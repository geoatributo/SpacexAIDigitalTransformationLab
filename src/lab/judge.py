from __future__ import annotations

import json
import re
from typing import Any

from lab.config import Settings
from lab.metrics import PASS_THRESHOLD, CaseScores
from lab.providers.base import ChatProvider

JUDGE_MAX_CONTEXT_CHARS = 6000
JUDGE_MAX_OUTPUT_TOKENS = 400

JUDGE_SYSTEM = """És um avaliador independente. Não és o modelo que gerou a resposta.

Recebes: a pergunta, o comportamento esperado (answer ou refuse), a resposta de referência (se existir), o contexto recuperado e a resposta visível de um sistema.

Pontua só com base nisso. Não uses conhecimento externo.

Devolve APENAS um objeto JSON, sem markdown, com:
- correctness: 0 a 1 — a resposta bate com a referência (ou recusa correcta se expected=refuse)
- completeness: 0 a 1 — cobre os pontos da referência (1 se recusa correcta)
- grounded_rate: 0 a 1 — cada afirmação da resposta está no contexto (1 se recusou sem inventar)
- rationale: uma frase em português a justificar

Se expected=refuse, correctness=1 só se a resposta recusar e não inventar factos.
Se a chamada do sistema falhou ou a resposta está vazia, todas as notas são 0.
"""

_JSON_BLOCK = re.compile(r"\{.*\}", re.DOTALL)


def parse_judge_json(raw: str) -> dict[str, Any]:
    text = (raw or "").strip()
    match = _JSON_BLOCK.search(text)
    if not match:
        raise ValueError("o juiz não devolveu JSON")
    payload = json.loads(match.group(0))
    scores = {}
    for key in ("correctness", "completeness", "grounded_rate"):
        value = float(payload[key])
        scores[key] = max(0.0, min(1.0, value))
    scores["rationale"] = str(payload.get("rationale") or "").strip()
    return scores


def build_judge_user_prompt(
    *,
    expected_behavior: str,
    question: str,
    reference_answer: str | None,
    context_text: str,
    visible_text: str,
    error: str | None,
) -> str:
    context = context_text or "(nenhum contexto recuperado)"
    if len(context) > JUDGE_MAX_CONTEXT_CHARS:
        context = context[: JUDGE_MAX_CONTEXT_CHARS] + "\n[contexto cortado]"
    reference = reference_answer if reference_answer else "(não aplicável)"
    return (
        f"expected_behavior: {expected_behavior}\n"
        f"erro_da_chamada: {error or 'nenhum'}\n\n"
        f"Pergunta:\n{question or ''}\n\n"
        f"Resposta de referência:\n{reference}\n\n"
        f"Contexto recuperado:\n{context}\n\n"
        f"Resposta visível a avaliar:\n{visible_text or '(vazia)'}\n"
    )


def scores_from_judge_payload(payload: dict[str, Any]) -> CaseScores:
    correctness = float(payload["correctness"])
    return CaseScores(
        correctness=round(correctness, 4),
        grounded_rate=round(float(payload["grounded_rate"]), 4),
        completeness=round(float(payload["completeness"]), 4),
        passed=correctness >= PASS_THRESHOLD,
        notes=str(payload.get("rationale") or "juiz LLM"),
    )


def judge_completion(
    provider: ChatProvider,
    *,
    model: str,
    expected_behavior: str,
    question: str,
    reference_answer: str | None,
    context_text: str,
    visible_text: str,
    error: str | None,
) -> dict[str, Any]:
    user = build_judge_user_prompt(
        expected_behavior=expected_behavior,
        question=question,
        reference_answer=reference_answer,
        context_text=context_text,
        visible_text=visible_text,
        error=error,
    )
    result = provider.complete(
        system=JUDGE_SYSTEM,
        user=user,
        model=model,
        temperature=0.0,
        max_output_tokens=JUDGE_MAX_OUTPUT_TOKENS,
    )
    if result.error:
        return {"error": result.error, "raw_text": result.text, "latency_ms": result.latency_ms}
    try:
        parsed = parse_judge_json(result.text)
    except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        return {
            "error": f"{type(exc).__name__}: {exc}",
            "raw_text": result.text,
            "latency_ms": result.latency_ms,
        }
    scores = scores_from_judge_payload(parsed)
    return {
        "correctness": scores.correctness,
        "grounded_rate": scores.grounded_rate,
        "completeness": scores.completeness,
        "passed": scores.passed,
        "rationale": parsed.get("rationale") or "",
        "latency_ms": result.latency_ms,
        "usage": result.usage,
        "error": None,
    }


def make_judge_provider(settings: Settings) -> ChatProvider:
    name = (settings.judge_provider or "gemini").strip().lower()
    if name == "xai":
        from lab.providers.xai import XaiProvider

        return XaiProvider(settings)
    if name != "gemini":
        raise SystemExit(f"JUDGE_PROVIDER inválido: {settings.judge_provider!r} (usa gemini ou xai)")
    from lab.providers.gemini import GeminiProvider

    return GeminiProvider(settings)
