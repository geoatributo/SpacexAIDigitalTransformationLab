from __future__ import annotations

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

CORRECTNESS_PROMPT = """Question: {question}

Reference answer: {reference}

Generated answer: {generated}

Score how well the generated answer conveys the same key facts as the reference answer,
from 0 (completely wrong/unrelated) to 100 (fully matches all key facts).
Respond with ONLY the number, nothing else."""

GROUNDED_PROMPT = """Retrieved context:
{context}

Generated answer: {generated}

Score what fraction of the factual claims in the generated answer are directly supported
by the retrieved context above (0 = answer invents facts not in the context at all,
100 = every claim is explicitly supported by the context).
Respond with ONLY the number, nothing else."""

COMPLETENESS_PROMPT = """Question: {question}

Reference answer (the complete, correct answer): {reference}

Generated answer: {generated}

Score how completely the generated answer covers EVERY point present in the reference
answer (0 = covers none of the reference's points, 100 = covers all of them -- partial
credit for covering some but not all). Do not penalize extra correct detail beyond the
reference.
Respond with ONLY the number, nothing else."""


def ask_score(judge_response_text: str) -> float | None:
    match = re.search(r"(\d+(?:\.\d+)?)", judge_response_text)
    if not match:
        return None
    value = float(match.group(1))
    return value / 100.0 if value > 1.0 else value


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
    if expected == "refuse":
        return "unanswerable_ok" if is_refusal else "unanswerable_answered"
    if is_refusal:
        return "false_refusal"
    if error:
        return "generation_error"
    if not has_context:
        return "no_context"
    return "score"


def _ask_metric(
    provider: ChatProvider,
    *,
    model: str,
    user: str,
    metric: str,
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
    score = None if result.error else ask_score(result.text or "")
    return {
        "metric": metric,
        "score": score,
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

    context = join_retrieved_context(context_chunks)
    generated_text = generated or ""
    reference_text = reference or ""
    calls = [
        _ask_metric(
            provider,
            model=model,
            metric="correctness",
            user=CORRECTNESS_PROMPT.format(
                question=question,
                reference=reference_text,
                generated=generated_text,
            ),
        ),
        _ask_metric(
            provider,
            model=model,
            metric="grounded",
            user=GROUNDED_PROMPT.format(context=context, generated=generated_text),
        ),
        _ask_metric(
            provider,
            model=model,
            metric="completeness",
            user=COMPLETENESS_PROMPT.format(
                question=question,
                reference=reference_text,
                generated=generated_text,
            ),
        ),
    ]
    correctness = calls[0]["score"]
    grounded = calls[1]["score"]
    completeness = calls[2]["score"]
    passed = (correctness is not None) and (correctness >= pass_threshold)
    call_error = next((call["error"] for call in calls if call["error"]), None)
    return {
        "correctness": correctness,
        "grounded": grounded,
        "completeness": completeness,
        "passed": passed,
        "bucket": bucket,
        "unanswerable_ok": False,
        "false_refusal": False,
        "calls": calls,
        "error": call_error,
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
