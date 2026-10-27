from __future__ import annotations

import json
import re
from typing import Any

from lab.providers.base import ChatProvider

JUDGE_SYSTEM_PROMPT = (
    "You are a meticulous QA grader for a RAG system's answers. Follow the instructions exactly."
)
JUDGE_TEMPERATURE = 0.2
JUDGE_TOP_P = 0.95
JUDGE_MAX_OUTPUT_TOKENS = 8192
JUDGE_TIMEOUT_S = 30.0
PASS_THRESHOLD = 0.8
CONTEXT_JOIN = "\n\n---\n\n"

SCORES_PROMPT = """Question: {question}

Reference answer: {reference}

Retrieved context:
{context}

Generated answer: {generated}

Score the generated answer on three metrics from 0 to 100:
1. correctness — how well it conveys the same key facts as the reference (0 = wrong/unrelated, 100 = all key facts).
2. grounded — what fraction of its factual claims are directly supported by the retrieved context (0 = invents facts, 100 = every claim supported).
3. completeness — how completely it covers every point in the reference; do not penalize extra correct detail (0 = none, 100 = all).

Respond with ONLY a JSON object, no markdown, no other text:
{{"correctness": <number>, "grounded": <number>, "completeness": <number>}}"""

_SCORE_KEYS = ("correctness", "grounded", "completeness")
_JSON_OBJECT = re.compile(r"\{[^{}]*\}", re.DOTALL)


def ask_score(judge_response_text: str) -> float | None:
    match = re.search(r"(\d+(?:\.\d+)?)", judge_response_text)
    if not match:
        return None
    value = float(match.group(1))
    return value / 100.0 if value > 1.0 else value


def _normalize_score(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        number = float(value)
    elif isinstance(value, str):
        return ask_score(value)
    else:
        return None
    if number > 1.0:
        number = number / 100.0
    if number < 0.0 or number > 1.0:
        return None
    return number


def parse_scores(judge_response_text: str) -> dict[str, float | None]:
    """Parse one judge reply into correctness / grounded / completeness in 0–1."""
    text = (judge_response_text or "").strip()
    empty = {key: None for key in _SCORE_KEYS}
    if not text:
        return empty
    candidates: list[str] = []
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL | re.IGNORECASE)
    if fenced:
        candidates.append(fenced.group(1))
    match = _JSON_OBJECT.search(text)
    if match:
        candidates.append(match.group(0))
    candidates.append(text)
    for candidate in candidates:
        try:
            payload = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if not isinstance(payload, dict):
            continue
        return {key: _normalize_score(payload.get(key)) for key in _SCORE_KEYS}
    return empty


def join_retrieved_context(chunks: list[str]) -> str:
    return CONTEXT_JOIN.join(chunk for chunk in chunks if (chunk or "").strip())


def media(chave: str, casos: list[dict[str, Any]]) -> float | None:
    valores = [caso[chave] for caso in casos if caso.get(chave) is not None]
    return round(sum(valores) / len(valores), 4) if valores else None


def pass_rate(casos: list[dict[str, Any]]) -> float | None:
    if not casos:
        return None
    return round(sum(1 for caso in casos if caso.get("passed")) / len(casos), 4)


def classify_case(
    *,
    expected_behavior: str,
    is_refusal: bool,
    context_chunks: list[str],
    error: str | None,
) -> str:
    expected = (expected_behavior or "answer").strip().lower()
    has_context = any((chunk or "").strip() for chunk in context_chunks)
    if expected in {"refuse", "refusal"}:
        return "unanswerable_ok" if is_refusal else "unanswerable_answered"
    if is_refusal:
        return "false_refusal"
    if error:
        return "generation_error"
    if not has_context:
        return "no_context"
    return "score"


def empty_scores() -> dict[str, float | None]:
    return {key: None for key in _SCORE_KEYS}


def _ask_scores(
    provider: ChatProvider,
    *,
    model: str,
    user: str,
) -> dict[str, Any]:
    result = provider.complete(
        system=JUDGE_SYSTEM_PROMPT,
        user=user,
        model=model,
        temperature=JUDGE_TEMPERATURE,
        top_p=JUDGE_TOP_P,
        max_output_tokens=JUDGE_MAX_OUTPUT_TOKENS,
        timeout=JUDGE_TIMEOUT_S,
    )
    scores = empty_scores() if result.error else parse_scores(result.text or "")
    return {
        "metric": "all",
        "scores": scores,
        "score": scores.get("correctness"),
        "raw_text": result.text,
        "error": result.error,
        "latency_ms": result.latency_ms,
        "usage": result.usage,
    }


def score_generated_answer(
    provider: ChatProvider,
    *,
    model: str,
    question: str,
    reference: str | None,
    generated: str,
    context_chunks: list[str],
    expected_behavior: str,
    is_refusal: bool,
    error: str | None,
    pass_threshold: float = PASS_THRESHOLD,
) -> dict[str, Any]:
    bucket = classify_case(
        expected_behavior=expected_behavior,
        is_refusal=is_refusal,
        context_chunks=context_chunks,
        error=error,
    )
    base = {
        "correctness": None,
        "grounded": None,
        "completeness": None,
        "passed": False,
        "bucket": bucket,
        "unanswerable_ok": bucket == "unanswerable_ok",
        "false_refusal": bucket == "false_refusal",
        "calls": [],
        "error": None,
    }
    if bucket != "score":
        return base

    call = _ask_scores(
        provider,
        model=model,
        user=SCORES_PROMPT.format(
            question=question,
            reference=reference or "",
            context=join_retrieved_context(context_chunks),
            generated=generated or "",
        ),
    )
    scores = call["scores"]
    correctness = scores.get("correctness")
    grounded = scores.get("grounded")
    completeness = scores.get("completeness")
    passed = (correctness is not None) and (correctness >= pass_threshold)
    return {
        "correctness": correctness,
        "grounded": grounded,
        "completeness": completeness,
        "passed": passed,
        "bucket": bucket,
        "unanswerable_ok": False,
        "false_refusal": False,
        "calls": [call],
        "error": call["error"],
    }


def aggregate_llm_cases(casos: list[dict[str, Any]]) -> dict[str, Any]:
    scored = [caso for caso in casos if caso.get("bucket") == "score"]
    return {
        "correctness": media("correctness", scored),
        "grounded_rate": media("grounded", scored),
        "completeness": media("completeness", scored),
        "pass_rate": pass_rate(scored),
        "n": len(scored),
        "n_unanswerable_ok": sum(1 for caso in casos if caso.get("unanswerable_ok")),
        "n_false_refusal": sum(1 for caso in casos if caso.get("false_refusal")),
        "n_excluded": sum(1 for caso in casos if caso.get("bucket") not in {"score", None}),
    }
