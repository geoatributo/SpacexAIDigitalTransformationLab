from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from lab.config import Settings, load_settings
from lab.context import CONTEXT_MODES, ContextPolicy, ContextStore
from lab.prompts import SYSTEM_PROMPT, build_user_prompt
from lab.providers.base import ChatProvider, CompletionResult
from lab.scratchpad import strip_scratchpad

log = logging.getLogger("lab")

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


def configure_logging() -> None:
    if log.handlers:
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S"))
    log.setLevel(logging.INFO)
    log.addHandler(handler)
    log.propagate = False


def _preview(text: str, width: int = 80) -> str:
    compact = " ".join(text.split())
    if len(compact) <= width:
        return compact
    return compact[: width - 1] + "…"


def policy_from_args(args: argparse.Namespace) -> ContextPolicy:
    policy = ContextPolicy(
        mode=args.context_mode,
        top_n=args.top_n,
        adjacent_m=args.adjacent_m,
        max_chars=args.max_chars,
    )
    try:
        policy.validate()
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    return policy


def _run_case(
    *,
    store: ContextStore,
    providers: list[ChatProvider],
    case_id: str,
    empty_context: bool,
    index: int,
    total: int,
    dry_run: bool,
) -> dict:
    log.info("[%s/%s] %s — a montar contexto", index, total, case_id)
    built = store.build(case_id if case_id != REFUSE_CASE_ID else "gold-01", empty_context=empty_context)
    log.info(
        "[%s/%s] %s — %s chunks | %s chars | %s",
        index,
        total,
        case_id,
        len(built.chunks),
        built.char_count,
        _preview(built.question),
    )
    if dry_run:
        log.info("[%s/%s] %s — chunk_ids=%s", index, total, case_id, [chunk.chunk_id for chunk in built.chunks])
        return {
            "case_id": case_id,
            "question": built.question,
            "empty_context": empty_context,
            "chunk_ids": [chunk.chunk_id for chunk in built.chunks],
            "chunk_count": len(built.chunks),
            "char_count": built.char_count,
            "expected_behavior": "refuse" if empty_context else built.expected_behavior,
            "reference_answer": None if empty_context else built.reference_answer,
            "providers": [],
        }
    user_prompt = build_user_prompt(built.question, built.chunks)
    results = []
    for provider in providers:
        log.info("[%s/%s] %s → %s …", index, total, case_id, provider.name)
        completion = provider.complete(system=SYSTEM_PROMPT, user=user_prompt)
        serialized = _serialize_completion(provider, completion)
        results.append(serialized)
        if serialized["error"]:
            log.warning(
                "[%s/%s] %s ← %s erro=%s (%sms)",
                index,
                total,
                case_id,
                provider.name,
                serialized["error"],
                serialized["latency_ms"],
            )
            continue
        usage = serialized.get("usage") or {}
        tokens = usage.get("total_tokens")
        token_bit = f" | tokens={tokens}" if tokens is not None else ""
        log.info(
            "[%s/%s] %s ← %s ok %sms | recusa=%s | fuga_scratchpad=%s%s",
            index,
            total,
            case_id,
            provider.name,
            serialized["latency_ms"],
            serialized["is_refusal"],
            serialized["scratchpad_leaked"],
            token_bit,
        )
    return {
        "case_id": case_id,
        "question": built.question,
        "empty_context": empty_context,
        "chunk_ids": [chunk.chunk_id for chunk in built.chunks],
        "chunk_count": len(built.chunks),
        "char_count": built.char_count,
        "expected_behavior": "refuse" if empty_context else built.expected_behavior,
        "reference_answer": None if empty_context else built.reference_answer,
        "providers": results,
    }


def run_phase1(
    settings: Settings,
    *,
    limit: int,
    policy: ContextPolicy,
    dry_run: bool = False,
) -> Path:
    log.info("A carregar chunks, retrieval e gold…")
    store = ContextStore.from_files(
        chunks_path=settings.chunks_path,
        retrieval_path=settings.retrieval_path,
        gold_path=settings.gold_path,
        policy=policy,
    )
    log.info("Dados carregados (%s perguntas gold)", len(store.gold_ids()))
    log.info("Contexto: %s", policy.to_dict())

    providers: list[ChatProvider] = []
    responses_api_supported: bool | None = None
    if not dry_run:
        from lab.providers.gemini import GeminiProvider
        from lab.providers.xai import XaiProvider

        gemini = GeminiProvider(settings)
        xai = XaiProvider(settings)
        log.info("Modelos: gemini=%s | xai=%s", settings.gemini_model, settings.xai_model)
        log.info("A testar API Responses da xAI…")
        responses_api_supported = xai.probe_responses_api()
        log.info("API Responses xAI: %s", "sim" if responses_api_supported else "não (a usar chat completions)")
        providers = [gemini, xai]
    else:
        log.info("Dry-run: sem chamadas a Gemini/xAI")

    gold_ids = [case_id for case_id in PHASE1_GOLD_IDS if case_id in store.gold_ids()][:limit]
    planned = [*gold_ids, REFUSE_CASE_ID]
    total = len(planned)
    log.info("Fase 1: %s casos (%s gold + recusa vazia)", total, len(gold_ids))
    cases = []
    for index, case_id in enumerate(gold_ids, start=1):
        cases.append(
            _run_case(
                store=store,
                providers=providers,
                case_id=case_id,
                empty_context=False,
                index=index,
                total=total,
                dry_run=dry_run,
            )
        )
    cases.append(
        _run_case(
            store=store,
            providers=providers,
            case_id=REFUSE_CASE_ID,
            empty_context=True,
            index=total,
            total=total,
            dry_run=dry_run,
        )
    )

    settings.runs_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    prefix = "phase1_dryrun" if dry_run else "phase1"
    out_path = settings.runs_dir / f"{prefix}_{stamp}.json"
    payload = {
        "phase": 1,
        "dry_run": dry_run,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "models": {"gemini": settings.gemini_model, "xai": settings.xai_model},
        "max_output_tokens": settings.max_output_tokens,
        "responses_api_supported": responses_api_supported,
        "context_policy": policy.to_dict(),
        "cases": cases,
    }
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info("Resultados gravados em %s", out_path)
    return out_path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fase 1: Gemini vs Grok no mesmo contexto congelado.")
    parser.add_argument("--limit", type=int, default=5, help="Número de perguntas gold (default 5).")
    parser.add_argument(
        "--context-mode",
        choices=CONTEXT_MODES,
        default="top_n",
        help="Como montar o contexto a partir do retrieval congelado.",
    )
    parser.add_argument("--top-n", type=int, default=6, help="Número de chunks de topo (1–50). Ignorado em full_top1.")
    parser.add_argument(
        "--adjacent-m",
        type=int,
        default=None,
        help="Vizinhos ±M por chunk_index no mesmo documento (obrigatório em top_n_adjacent).",
    )
    parser.add_argument(
        "--max-chars",
        type=int,
        default=None,
        help="Teto opcional de caracteres; chunks não são cortados a meio.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Monta o contexto e grava um JSON, sem chamar os modelos.",
    )
    parser.add_argument(
        "--eval",
        nargs="?",
        const="",
        default=None,
        help="Avaliar uma run já gravada (sem chamar as APIs, salvo --judge). Sem caminho, usa a mais recente.",
    )
    parser.add_argument(
        "--judge",
        action="store_true",
        help="Avaliar com um terceiro modelo (JUDGE_PROVIDER/JUDGE_MODEL). Por omissão só corre a métrica lexical.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    configure_logging()
    args = parse_args(argv)
    from lab.evaluate import evaluate_path, format_summary, latest_run

    if args.eval is not None:
        run_path = Path(args.eval) if args.eval else latest_run()
        settings = load_settings(require_keys=True) if args.judge else None
        out_path = evaluate_path(run_path, settings=settings, use_judge=args.judge)
        report = json.loads(out_path.read_text(encoding="utf-8"))
        log.info("Run: %s", run_path)
        log.info("Eval: %s", out_path)
        for line in format_summary(report).splitlines():
            log.info("%s", line)
        return

    policy = policy_from_args(args)
    log.info("A validar configuração…")
    settings = load_settings(require_keys=not args.dry_run)
    path = run_phase1(settings, limit=args.limit, policy=policy, dry_run=args.dry_run)
    if not args.dry_run:
        out_path = evaluate_path(path, settings=settings, use_judge=args.judge)
        report = json.loads(out_path.read_text(encoding="utf-8"))
        log.info("Métricas: %s", out_path)
        for line in format_summary(report).splitlines():
            log.info("%s", line)
    log.info("Concluído: %s", path)


if __name__ == "__main__":
    main()
