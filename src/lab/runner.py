from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from lab.config import Settings, load_settings
from lab.context import ContextStore
from lab.prompts import SYSTEM_PROMPT, build_user_prompt
from lab.providers.base import ChatProvider, CompletionResult
from lab.scratchpad import strip_scratchpad

PHASE1_GOLD_IDS = ["gold-01", "gold-02", "gold-03", "gold-04", "gold-05"]
REFUSE_CASE_ID = "refuse-empty"


def _serialize_completion(provider: ChatProvider, result: CompletionResult) -> dict:
    cleaned = strip_scratchpad(result.text)
    payload = {
        "provider": provider.name,
        "raw_text": result.text,
        "visible_text": cleaned.visible_text,
        "scratchpad_leaked": cleaned.scratchpad_leaked,
        "is_refusal": cleaned.is_refusal,
        "latency_ms": result.latency_ms,
        "usage": result.usage,
        "error": result.error,
    }
    if result.extra:
        payload["extra"] = result.extra
    return payload


def _run_case(
    *,
    store: ContextStore,
    providers: list[ChatProvider],
    case_id: str,
    empty_context: bool,
) -> dict:
    built = store.build(case_id if case_id != REFUSE_CASE_ID else "gold-01", empty_context=empty_context)
    user_prompt = build_user_prompt(built.question, built.chunks)
    return {
        "case_id": case_id,
        "question": built.question,
        "empty_context": empty_context,
        "chunk_ids": [chunk.chunk_id for chunk in built.chunks],
        "chunk_count": len(built.chunks),
        "expected_behavior": "refuse" if empty_context else built.expected_behavior,
        "reference_answer": None if empty_context else built.reference_answer,
        "providers": [_serialize_completion(provider, provider.complete(system=SYSTEM_PROMPT, user=user_prompt)) for provider in providers],
    }


def run_phase1(settings: Settings, *, limit: int) -> Path:
    store = ContextStore(
        chunks_path=settings.chunks_path,
        retrieval_path=settings.retrieval_path,
        gold_path=settings.gold_path,
        max_chunks=settings.max_chunks,
        similarity_floor=settings.similarity_floor,
        context_char_cap=settings.context_char_cap,
    )
    from lab.providers.gemini import GeminiProvider
    from lab.providers.xai import XaiProvider

    gemini = GeminiProvider(settings)
    xai = XaiProvider(settings)
    responses_api_supported = xai.probe_responses_api()
    providers: list[ChatProvider] = [gemini, xai]

    gold_ids = [case_id for case_id in PHASE1_GOLD_IDS if case_id in store.gold_ids()][:limit]
    cases = [_run_case(store=store, providers=providers, case_id=case_id, empty_context=False) for case_id in gold_ids]
    cases.append(_run_case(store=store, providers=providers, case_id=REFUSE_CASE_ID, empty_context=True))

    settings.runs_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = settings.runs_dir / f"phase1_{stamp}.json"
    payload = {
        "phase": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "models": {"gemini": settings.gemini_model, "xai": settings.xai_model},
        "max_output_tokens": settings.max_output_tokens,
        "responses_api_supported": responses_api_supported,
        "cases": cases,
    }
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fase 1: Gemini vs Grok no mesmo contexto congelado.")
    parser.add_argument("--limit", type=int, default=5, help="Número de perguntas gold (default 5).")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    settings = load_settings()
    path = run_phase1(settings, limit=args.limit)
    print(f"Resultados: {path}")


if __name__ == "__main__":
    main()
