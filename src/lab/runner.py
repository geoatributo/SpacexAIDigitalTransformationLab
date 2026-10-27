from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from lab.config import Settings, load_settings
from lab.context import CONTEXT_MODES, ContextPolicy, ContextStore
from lab.prompts import SYSTEM_PROMPT, build_user_prompt
from lab.providers.base import ChatProvider, CompletionResult
from lab.retry import complete_with_retries
from lab.scratchpad import strip_scratchpad

log = logging.getLogger("lab")

REFUSE_CASE_ID = "refuse-empty"
# Set by scripts/run_context_configs.py so child jobs emit only step counters.
PROGRESS_ONLY = os.environ.get("LAB_PROGRESS_ONLY") == "1"
_PROGRESS_LOCK = threading.Lock()
_PROGRESS_DONE = 0


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
    # Windows consoles often use cp1252; force UTF-8 so arrows/accents don't crash logging.
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S"))
    # Sweep jobs only want step counters; keep warnings/errors visible.
    log.setLevel(logging.WARNING if PROGRESS_ONLY else logging.INFO)
    log.addHandler(handler)
    log.propagate = False


def _emit_progress(index: int, total: int) -> None:
    """Machine-readable step line for the config sweep relay."""
    if PROGRESS_ONLY:
        print(f"PROGRESS {index}/{total}", flush=True)


def _emit_progress_done(total: int) -> None:
    """Thread-safe completed-count progress for parallel case runs."""
    global _PROGRESS_DONE
    with _PROGRESS_LOCK:
        _PROGRESS_DONE += 1
        done = _PROGRESS_DONE
    _emit_progress(done, total)


def _preview(text: str, width: int = 80) -> str:
    compact = " ".join(text.split())
    if len(compact) <= width:
        return compact
    return compact[: width - 1] + "..."


def apply_generation(settings: Settings, *, temperature: float, top_p: float) -> Settings:
    if temperature < 0 or temperature > 2:
        raise ValueError("--temperature deve estar entre 0 e 2")
    if not 0 < top_p <= 1:
        raise ValueError("--top-p deve ser maior que 0 e no máximo 1")
    return replace(settings, temperature=temperature, top_p=top_p)


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
    emit_progress: bool = True,
) -> dict:
    if emit_progress:
        _emit_progress(index, total)
    log.info("[%s/%s] %s - a montar contexto", index, total, case_id)
    built = store.build(case_id if case_id != REFUSE_CASE_ID else "gold-01", empty_context=empty_context)
    log.info(
        "[%s/%s] %s - %s chunks | %s chars | %s",
        index,
        total,
        case_id,
        len(built.chunks),
        built.char_count,
        _preview(built.question),
    )
    if dry_run:
        log.info("[%s/%s] %s - chunk_ids=%s", index, total, case_id, [chunk.chunk_id for chunk in built.chunks])
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

    def _call_provider(provider: ChatProvider) -> dict:
        log.info("[%s/%s] %s -> %s ...", index, total, case_id, provider.name)
        completion = complete_with_retries(provider, system=SYSTEM_PROMPT, user=user_prompt)
        serialized = _serialize_completion(provider, completion)
        if serialized["error"]:
            log.warning(
                "[%s/%s] %s <- %s erro=%s (%sms)",
                index,
                total,
                case_id,
                provider.name,
                serialized["error"],
                serialized["latency_ms"],
            )
        else:
            usage = serialized.get("usage") or {}
            tokens = usage.get("total_tokens")
            token_bit = f" | tokens={tokens}" if tokens is not None else ""
            log.info(
                "[%s/%s] %s <- %s ok %sms | recusa=%s | fuga_scratchpad=%s%s",
                index,
                total,
                case_id,
                provider.name,
                serialized["latency_ms"],
                serialized["is_refusal"],
                serialized["scratchpad_leaked"],
                token_bit,
            )
        return serialized

    if len(providers) <= 1:
        results = [_call_provider(provider) for provider in providers]
    else:
        # Keep provider order stable (gemini, xai, …).
        with ThreadPoolExecutor(max_workers=len(providers)) as pool:
            futures = [pool.submit(_call_provider, provider) for provider in providers]
            results = [future.result() for future in futures]
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


def run_case(
    *,
    store: ContextStore,
    providers: list[ChatProvider],
    case_id: str,
    empty_context: bool = False,
) -> dict:
    """Gera xAI e Gemini no mesmo contexto congelado. Não altera o retrieval."""
    return _run_case(
        store=store,
        providers=providers,
        case_id=case_id,
        empty_context=empty_context,
        index=1,
        total=1,
        dry_run=False,
    )


def retry_failed_answers_path(
    run_path: Path,
    *,
    settings: Settings | None = None,
    workers: int = 4,
) -> dict:
    """Re-call providers for cells with ``error`` in a run JSON, writing in place."""
    import time
    from concurrent.futures import ThreadPoolExecutor, as_completed

    if settings is None:
        settings = load_settings(require_keys=True)

    payload = json.loads(run_path.read_text(encoding="utf-8"))
    if payload.get("dry_run"):
        return {"name": run_path.stem, "status": "dry_run", "retried": 0, "still_failed": 0}

    policy_raw = payload.get("context_policy") or {}
    mode = str(policy_raw.get("mode") or "top_n")
    top_n = policy_raw.get("top_n")
    policy = ContextPolicy(
        mode=mode,  # type: ignore[arg-type]
        top_n=int(top_n) if top_n is not None else 6,
        adjacent_m=policy_raw.get("adjacent_m"),
        max_chars=policy_raw.get("max_chars"),
    )
    policy.validate()
    store = ContextStore.from_files(
        chunks_path=settings.chunks_path,
        retrieval_path=settings.retrieval_path,
        gold_path=settings.gold_path,
        policy=policy,
    )

    run_settings = apply_generation(
        settings,
        temperature=float(payload.get("temperature") if payload.get("temperature") is not None else settings.temperature),
        top_p=float(payload.get("top_p") if payload.get("top_p") is not None else settings.top_p),
    )
    from lab.providers.gemini import GeminiProvider
    from lab.providers.xai import XaiProvider

    providers_by_name: dict[str, ChatProvider] = {
        "gemini": GeminiProvider(run_settings),
        "xai": XaiProvider(run_settings),
    }

    jobs: list[dict] = []
    for case_i, case in enumerate(payload.get("cases") or []):
        for prov_i, row in enumerate(case.get("providers") or []):
            if not row.get("error"):
                continue
            name = str(row.get("provider") or "")
            provider = providers_by_name.get(name)
            if provider is None:
                continue
            jobs.append({"case_i": case_i, "prov_i": prov_i, "provider": provider, "case": case})

    worker_count = max(1, int(workers))
    log.info(
        "[retry-answers] %s: %s células com erro · workers=%s",
        run_path.name,
        len(jobs),
        worker_count,
    )
    if not jobs:
        return {"name": run_path.stem, "status": "ok", "retried": 0, "still_failed": 0}

    def _work(job: dict) -> dict:
        case = job["case"]
        case_id = str(case.get("case_id") or "")
        empty_context = bool(case.get("empty_context"))
        question = str(case.get("question") or "")
        if empty_context or case_id == REFUSE_CASE_ID:
            chunks: list = []
        else:
            try:
                built = store.build(case_id if case_id != REFUSE_CASE_ID else "gold-01", empty_context=False)
                chunks = built.chunks
                if not question:
                    question = built.question
            except KeyError:
                chunks = []
        user_prompt = build_user_prompt(question, chunks)
        provider = job["provider"]
        completion = complete_with_retries(provider, system=SYSTEM_PROMPT, user=user_prompt)
        return {
            "case_i": job["case_i"],
            "prov_i": job["prov_i"],
            "serialized": _serialize_completion(provider, completion),
        }

    started = time.perf_counter()
    if worker_count == 1:
        results = [_work(job) for job in jobs]
    else:
        results = []
        with ThreadPoolExecutor(max_workers=worker_count) as pool:
            futures = [pool.submit(_work, job) for job in jobs]
            for future in as_completed(futures):
                results.append(future.result())

    still_failed = 0
    for result in results:
        row = payload["cases"][result["case_i"]]["providers"][result["prov_i"]]
        serialized = result["serialized"]
        row.clear()
        row.update(serialized)
        if serialized.get("error"):
            still_failed += 1

    run_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    elapsed = round(time.perf_counter() - started, 1)
    log.info(
        "[retry-answers] %s: %s/%s ok em %ss · ainda com erro=%s",
        run_path.name,
        len(jobs) - still_failed,
        len(jobs),
        elapsed,
        still_failed,
    )
    return {
        "name": run_path.stem,
        "status": "ok" if still_failed == 0 else "partial",
        "retried": len(jobs),
        "still_failed": still_failed,
        "elapsed_s": elapsed,
    }


_RUN_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,80}")


def select_gold_ids(gold_ids: list[str], *, limit: int) -> list[str]:
    """First `limit` questions, in the order of the merged gold file."""
    if limit < 1:
        raise ValueError("--limit deve ser >= 1")
    return list(gold_ids[:limit])


def run_output_path(runs_dir: Path, *, dry_run: bool, run_name: str | None, stamp: str) -> Path:
    """Config runs use the config name. A plain `python -m lab` keeps the timestamped name."""
    if run_name is not None and run_name.strip():
        cleaned = run_name.strip()
        if _RUN_NAME.fullmatch(cleaned) is None:
            raise ValueError(f"--run-name inválido: {run_name}")
        return runs_dir / f"{cleaned}.json"
    prefix = "phase1_dryrun" if dry_run else "phase1"
    return runs_dir / f"{prefix}_{stamp}.json"


def run_phase1(
    settings: Settings,
    *,
    limit: int,
    policy: ContextPolicy,
    dry_run: bool = False,
    run_name: str | None = None,
    case_workers: int = 1,
) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    try:
        out_path = run_output_path(settings.runs_dir, dry_run=dry_run, run_name=run_name, stamp=stamp)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    log.info("A carregar chunks, retrieval e gold...")
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
        log.info("A testar API Responses da xAI...")
        responses_api_supported = xai.probe_responses_api()
        log.info("API Responses xAI: %s", "sim" if responses_api_supported else "nao (chat completions)")
        providers = [gemini, xai]
    else:
        log.info("Dry-run: sem chamadas a Gemini/xAI")

    available = store.gold_ids()
    try:
        gold_ids = select_gold_ids(available, limit=limit)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    planned = [*gold_ids, REFUSE_CASE_ID]
    total = len(planned)
    worker_count = max(1, int(case_workers))
    log.info(
        "Fase 1: %s casos (%s de %s gold + recusa vazia) · case_workers=%s",
        total,
        len(gold_ids),
        len(available),
        worker_count,
    )
    jobs = [
        {
            "case_id": case_id,
            "empty_context": False,
            "index": index,
        }
        for index, case_id in enumerate(gold_ids, start=1)
    ]
    jobs.append({"case_id": REFUSE_CASE_ID, "empty_context": True, "index": total})

    global _PROGRESS_DONE
    _PROGRESS_DONE = 0

    def _work(job: dict) -> tuple[int, dict]:
        row = _run_case(
            store=store,
            providers=providers,
            case_id=job["case_id"],
            empty_context=job["empty_context"],
            index=job["index"],
            total=total,
            dry_run=dry_run,
            emit_progress=worker_count == 1,
        )
        if worker_count > 1:
            _emit_progress_done(total)
        return job["index"], row

    if worker_count == 1:
        cases = [_work(job)[1] for job in jobs]
    else:
        by_index: dict[int, dict] = {}
        with ThreadPoolExecutor(max_workers=worker_count) as pool:
            futures = [pool.submit(_work, job) for job in jobs]
            for future in as_completed(futures):
                index, row = future.result()
                by_index[index] = row
        cases = [by_index[index] for index in sorted(by_index)]

    settings.runs_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "phase": 1,
        "dry_run": dry_run,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "config_name": run_name.strip() if run_name and run_name.strip() else None,
        "models": {"gemini": settings.gemini_model, "xai": settings.xai_model},
        "temperature": settings.temperature,
        "top_p": settings.top_p,
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
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Quantas perguntas do gold fundido, pela ordem do ficheiro (default 5).",
    )
    parser.add_argument(
        "--run-name",
        default=None,
        help="Nome do ficheiro dentro da pasta da corrida. Usado quando a corrida vem de uma config.",
    )
    parser.add_argument(
        "--runs-dir",
        type=Path,
        default=None,
        help="Pasta desta corrida. Por defeito data/runs/<timestamp>/.",
    )
    parser.add_argument(
        "--context-mode",
        choices=CONTEXT_MODES,
        default="top_n",
        help="Como montar o contexto a partir do retrieval congelado.",
    )
    parser.add_argument(
        "--top-n",
        "--top-k",
        dest="top_n",
        type=int,
        default=6,
        help="Número de chunks de topo, o k (1–50). --top-k é o mesmo parâmetro. Ignorado em full_top1.",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.1,
        help="Temperatura igual nos dois modelos (0–2, default 0.1).",
    )
    parser.add_argument(
        "--top-p",
        type=float,
        default=0.9,
        help="top_p igual nos dois modelos (maior que 0 e no máximo 1, default 0.9).",
    )
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
        "--case-workers",
        type=int,
        default=int(os.environ.get("LAB_CASE_WORKERS") or "32"),
        help="Perguntas em paralelo dentro desta config (default 32, ou LAB_CASE_WORKERS).",
    )
    parser.add_argument(
        "--eval",
        nargs="?",
        const="",
        default=None,
        help="Avaliar uma run já gravada (sem chamar as APIs, salvo --judge/--cross-judge). Sem caminho, usa a mais recente.",
    )
    parser.add_argument(
        "--judge",
        action="store_true",
        help="Avaliar com um terceiro modelo (JUDGE_PROVIDER/JUDGE_MODEL).",
    )
    parser.add_argument(
        "--cross-judge",
        action="store_true",
        help="Grok avalia Gemini e Gemini avalia Grok, sem identificar o autor no prompt.",
    )
    parser.add_argument(
        "--judge-only",
        action="store_true",
        help="Só juiz LLM — não corre métricas lexicais. Exige --judge ou --cross-judge.",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Chamadas de juiz em paralelo dentro de uma config (default 1).",
    )
    parser.add_argument(
        "--pass-threshold",
        type=float,
        default=0.8,
        help="Limiar de correctness para pass_rate (default 0.8).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    configure_logging()
    args = parse_args(argv)
    from lab.evaluate import evaluate_path, latest_run

    if args.eval is not None:
        run_path = Path(args.eval) if args.eval else latest_run()
        need_keys = args.judge or args.cross_judge
        settings = load_settings(require_keys=True) if need_keys else None
        out_path = evaluate_path(
            run_path,
            settings=settings,
            use_judge=args.judge,
            use_cross_judge=args.cross_judge,
            pass_threshold=args.pass_threshold,
            lexical=not args.judge_only,
            workers=args.workers,
        )
        log.info("Run: %s", run_path)
        log.info("Eval: %s", out_path)
        return

    policy = policy_from_args(args)
    log.info("A validar configuracao...")
    settings = load_settings(require_keys=not args.dry_run)
    if args.runs_dir is not None:
        settings = replace(settings, runs_dir=args.runs_dir)
    else:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        settings = replace(settings, runs_dir=settings.runs_dir / stamp)
    try:
        settings = apply_generation(settings, temperature=args.temperature, top_p=args.top_p)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    path = run_phase1(
        settings,
        limit=args.limit,
        policy=policy,
        dry_run=args.dry_run,
        run_name=args.run_name,
        case_workers=args.case_workers,
    )
    if not args.dry_run:
        out_path = evaluate_path(
            path,
            settings=settings,
            use_judge=args.judge,
            use_cross_judge=args.cross_judge,
            pass_threshold=args.pass_threshold,
            lexical=not args.judge_only,
            workers=args.workers,
        )
        log.info("Metricas: %s", out_path)
    log.info("Concluido: %s", path)



if __name__ == "__main__":
    main()
