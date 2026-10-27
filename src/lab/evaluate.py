from __future__ import annotations

import argparse
import json
import re
import sys
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lab.config import REPO_ROOT, Settings
from lab.context import ContextPolicy, ContextStore
from lab.judge import CrossJudgePanel, make_cross_panel, make_judge_provider
from lab.metrics import PASS_THRESHOLD, aggregate, as_payload, score_completion
from lab.rag_judge import aggregate_llm_cases, score_generated_answer
from lab.providers.base import ChatProvider


def _log(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


def _run_llm_job(job: dict[str, Any]) -> dict[str, Any]:
    """Execute one third-judge or cross-judge scoring call."""
    kind = job["kind"]
    if kind == "judge":
        judged = score_generated_answer(job["provider"], model=job["model"], **job["score_kwargs"])
        return {"case_i": job["case_i"], "prov_i": job["prov_i"], "kind": kind, "judged": judged}
    judged = score_generated_answer(job["provider"], model=job["model"], **job["score_kwargs"])
    judged["blind"] = True
    judged["scored_by"] = job["scored_by"]
    judged["scored_by_model"] = job["model"]
    return {"case_i": job["case_i"], "prov_i": job["prov_i"], "kind": kind, "judged": judged}


def _chunks_path() -> Path:
    return REPO_ROOT / "data" / "chunk_data" / "chunks.json"


def _runs_dir() -> Path:
    return REPO_ROOT / "data" / "runs"


def load_chunk_texts(path: Path | None = None) -> dict[str, str]:
    with (path or _chunks_path()).open(encoding="utf-8") as handle:
        rows = json.load(handle)
    return {str(row["chunk_id"]): str(row.get("text") or "") for row in rows}


def _is_run_file(path: Path) -> bool:
    name = path.name
    if name.endswith(".eval.json"):
        return False
    if name.startswith("context_sweep") or name.startswith("metrics"):
        return False
    return True


def latest_run(runs_dir: Path | None = None) -> Path:
    folder = runs_dir or _runs_dir()
    files = [path for path in folder.rglob("*.json") if _is_run_file(path)]
    files.sort(key=lambda item: item.stat().st_mtime)
    if not files:
        raise SystemExit(f"Nenhuma run em {folder}")
    return files[-1]


def default_store() -> ContextStore:
    data_dir = REPO_ROOT / "data"
    return ContextStore.from_files(
        chunks_path=data_dir / "chunk_data" / "chunks.json",
        retrieval_path=data_dir / "chunk_data" / "retrieval.json",
        gold_path=data_dir / "geoatributo_base2_gold_questions_p4_merged.json",
        policy=ContextPolicy(mode="top_n", top_n=6, max_chars=9000),
    )


def resolve_context_chunks(
    case: dict[str, Any],
    chunk_texts: dict[str, str],
    *,
    store: ContextStore | None = None,
) -> tuple[list[str], str]:
    ids = [str(chunk_id) for chunk_id in case.get("chunk_ids") or []]
    found = [chunk_texts[chunk_id] for chunk_id in ids if chunk_texts.get(chunk_id)]
    if found:
        return found, "run"
    if case.get("empty_context") or not ids:
        return [], "empty"
    if store is None:
        return [], "missing"
    case_id = str(case.get("case_id") or "")
    if not case_id or case_id == "refuse-empty":
        return [], "empty"
    try:
        built = store.build(case_id, empty_context=False)
    except KeyError:
        return [], "missing"
    return [chunk.text for chunk in built.chunks], "store_fallback"


def resolve_context_text(
    case: dict[str, Any],
    chunk_texts: dict[str, str],
    *,
    store: ContextStore | None = None,
) -> tuple[str, str]:
    chunks, source = resolve_context_chunks(case, chunk_texts, store=store)
    return "\n".join(chunks), source


def _provider_pass_label(row: dict[str, Any]) -> str:
    for key in ("cross_judge", "judge"):
        block = row.get(key)
        if isinstance(block, dict):
            if block.get("unanswerable_ok") or block.get("bucket") == "unanswerable_ok":
                return "pass"
            return "pass" if block.get("passed") else "fail"
    if "passed" in row:
        return "pass" if row.get("passed") else "fail"
    return "?"


def evaluate_payload(
    payload: dict[str, Any],
    *,
    chunk_texts: dict[str, str],
    store: ContextStore | None = None,
    judge: ChatProvider | None = None,
    judge_model: str | None = None,
    judge_provider_name: str | None = None,
    cross_panel: CrossJudgePanel | None = None,
    pass_threshold: float = PASS_THRESHOLD,
    log: bool = False,
    lexical: bool = True,
    workers: int = 1,
) -> dict[str, Any]:
    if not lexical and not judge and not cross_panel:
        raise SystemExit("judge-only (--judge-only) exige --judge ou --cross-judge.")
    by_provider: dict[str, list] = defaultdict(list)
    by_judge: dict[str, list] = defaultdict(list)
    by_cross: dict[str, list] = defaultdict(list)
    cases_out: list[dict[str, Any]] = []
    contestants = payload.get("models") or {}
    if judge and judge_model and judge_model in contestants.values():
        raise SystemExit(
            f"O modelo juiz ({judge_model}) coincide com um dos modelos em teste. "
            "Usa --cross-judge (Gemini↔Grok às cegas) ou um JUDGE_MODEL diferente."
        )
    cases = payload.get("cases") or []
    modes: list[str] = []
    if lexical:
        modes.append("lexical")
    if judge and judge_model:
        modes.append(f"judge={judge_provider_name or getattr(judge, 'name', '?')}/{judge_model}")
    if cross_panel:
        modes.append("cross-judge")
    worker_count = max(1, int(workers))
    if log:
        _log(
            f"[eval] {len(cases)} casos · {' + '.join(modes)} · limiar={pass_threshold}"
            + (f" · workers={worker_count}" if (judge or cross_panel) else "")
        )
    started = time.perf_counter()
    llm_jobs: list[dict[str, Any]] = []
    case_meta: list[dict[str, Any]] = []

    for case_i, case in enumerate(cases):
        context_chunks, context_source = resolve_context_chunks(case, chunk_texts, store=store)
        context_text = "\n".join(context_chunks)
        expected = str(case.get("expected_behavior") or "answer")
        provider_scores: list[dict[str, Any]] = []
        for prov_i, row in enumerate(case.get("providers") or []):
            name = str(row.get("provider") or "unknown")
            item: dict[str, Any] = {"provider": row.get("provider")}
            if lexical:
                scores = score_completion(
                    expected_behavior=expected,
                    reference_answer=case.get("reference_answer"),
                    visible_text=str(row.get("visible_text") or ""),
                    is_refusal=bool(row.get("is_refusal")),
                    context_text=context_text,
                    error=row.get("error"),
                )
                by_provider[name].append(scores)
                item["lexical"] = as_payload(scores)
                item.update(as_payload(scores))
            score_kwargs = {
                "question": str(case.get("question") or ""),
                "reference": case.get("reference_answer"),
                "generated": str(row.get("visible_text") or ""),
                "context_chunks": context_chunks,
                "expected_behavior": expected,
                "is_refusal": bool(row.get("is_refusal")),
                "error": row.get("error"),
                "pass_threshold": pass_threshold,
            }
            if judge and judge_model:
                llm_jobs.append(
                    {
                        "case_i": case_i,
                        "prov_i": prov_i,
                        "kind": "judge",
                        "provider": judge,
                        "model": judge_model,
                        "score_kwargs": score_kwargs,
                        "provider_name": name,
                    }
                )
            if cross_panel:
                assignment = cross_panel.assignment_for(name)
                if assignment is None:
                    item["cross_judge"] = {
                        "error": f"sem par cruzado para {name}",
                        "passed": False,
                        "bucket": "no_peer",
                    }
                else:
                    llm_jobs.append(
                        {
                            "case_i": case_i,
                            "prov_i": prov_i,
                            "kind": "cross",
                            "provider": assignment.judge,
                            "model": assignment.model,
                            "scored_by": assignment.judge_name,
                            "score_kwargs": score_kwargs,
                            "provider_name": name,
                        }
                    )
            provider_scores.append(item)
        case_meta.append(
            {
                "case_id": case.get("case_id"),
                "expected_behavior": case.get("expected_behavior"),
                "context_source": context_source,
                "context_chars": len(context_text),
                "expected": expected,
                "providers": provider_scores,
            }
        )

    done_cases: set[int] = set()
    case_started = {i: time.perf_counter() for i in range(len(cases))}

    def _flush_case_log(case_i: int) -> None:
        if not log or case_i in done_cases:
            return
        meta = case_meta[case_i]
        providers = meta["providers"]
        if any(
            (judge and judge_model and "judge" not in row)
            or (cross_panel and "cross_judge" not in row)
            for row in providers
        ):
            return
        done_cases.add(case_i)
        labels = ", ".join(f"{row.get('provider')}={_provider_pass_label(row)}" for row in providers)
        _log(
            f"[eval] {len(done_cases)}/{len(cases)} {meta.get('case_id') or '?'} "
            f"expected={meta['expected']} ctx={meta['context_source']}:{meta['context_chars']}ch "
            f"{time.perf_counter() - case_started[case_i]:.2f}s · {labels}"
        )

    if llm_jobs:
        if worker_count == 1:
            results = [_run_llm_job(job) for job in llm_jobs]
        else:
            results = []
            with ThreadPoolExecutor(max_workers=worker_count) as pool:
                futures = [pool.submit(_run_llm_job, job) for job in llm_jobs]
                for future in as_completed(futures):
                    results.append(future.result())
        for result in results:
            case_i = result["case_i"]
            prov_i = result["prov_i"]
            item = case_meta[case_i]["providers"][prov_i]
            if result["kind"] == "judge":
                item["judge"] = result["judged"]
            else:
                item["cross_judge"] = result["judged"]
            _flush_case_log(case_i)

    by_judge = defaultdict(list)
    by_cross = defaultdict(list)
    for meta in case_meta:
        for item in meta["providers"]:
            name = str(item.get("provider") or "unknown")
            if "judge" in item:
                by_judge[name].append(item["judge"])
            cross = item.get("cross_judge")
            if isinstance(cross, dict) and cross.get("bucket") != "no_peer":
                by_cross[name].append(cross)
        cases_out.append(
            {
                "case_id": meta["case_id"],
                "expected_behavior": meta["expected_behavior"],
                "context_source": meta["context_source"],
                "providers": meta["providers"],
            }
        )
    for case_i in range(len(case_meta)):
        _flush_case_log(case_i)

    summary = {name: aggregate(items) for name, items in by_provider.items()} if lexical else {}
    if judge or cross_panel:
        judge_method = (
            "LLM judge próprio (não ragas): uma chamada JSON com correctness/grounded/completeness (0–100 → 0–1). "
            f"temperature=0.2 top_p=0.95 max_output_tokens=8192 timeout=120s retries=5 backoff=exp. pass_threshold={pass_threshold}."
        )
        if cross_panel:
            judge_method += " Cruzado às cegas: Grok pontua Gemini e Gemini pontua Grok."
        if judge:
            judge_method += f" Juiz terceiro: {judge_provider_name or judge.name} / {judge_model}."
        if not lexical:
            judge_method += " Sem métricas lexicais (judge-only)."
        scoring = "cross_judge" if cross_panel and not judge else ("judge" if judge and not cross_panel else "llm_judge")
        method = {
            "correctness": "LLM: mesma key facts que a referência (0–100). Recusa esperada e sem contexto ficam fora.",
            "completeness": "LLM: cobertura de todos os pontos da referência; extra correcto não penaliza.",
            "grounded_rate": "LLM: fracção das afirmações suportadas pelos chunks juntos com \\n\\n---\\n\\n.",
            "pass_rate": f"% dos casos pontuados com correctness ≥ {pass_threshold} (só correctness).",
            "judge": judge_method,
            "scoring": scoring,
            "lexical": False if not lexical else True,
        }
    else:
        method = {
            "correctness": "Lexical: number recall + unit coverage vs referência.",
            "completeness": "Lexical: cobertura de unidades da referência na resposta.",
            "grounded_rate": "Lexical: fracção de unidades da resposta cobertas pelo contexto.",
            "pass_rate": f"% dos casos com correctness ≥ {pass_threshold} (só correctness).",
            "judge": "desligado — só métricas lexicais locais (sem chamadas LLM).",
            "scoring": "lexical",
            "lexical": True,
        }
    log_summary = summary
    if not log_summary and by_cross:
        log_summary = {name: aggregate_llm_cases(items) for name, items in by_cross.items()}
    elif not log_summary and by_judge:
        log_summary = {name: aggregate_llm_cases(items) for name, items in by_judge.items()}
    if log:
        parts = [
            f"{name}=pass_rate={stats.get('pass_rate')}"
            for name, stats in log_summary.items()
        ]
        _log(f"[eval] concluído em {time.perf_counter() - started:.1f}s · {' '.join(parts)}")
    report: dict[str, Any] = {
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "method": method,
        "pass_threshold": pass_threshold,
        "models": payload.get("models"),
        "summary": summary,
        "cases": cases_out,
    }
    if judge:
        report["judge"] = {"provider": judge_provider_name or judge.name, "model": judge_model}
        report["summary_judge"] = {name: aggregate_llm_cases(items) for name, items in by_judge.items()}
    if cross_panel:
        report["cross_judge"] = {
            "blind": True,
            "pairs": {"gemini": "xai", "xai": "gemini"},
            "models": contestants,
        }
        report["summary_cross"] = {name: aggregate_llm_cases(items) for name, items in by_cross.items()}
    return report


def _judge_block_failed(block: Any) -> bool:
    if not isinstance(block, dict):
        return False
    if block.get("error"):
        return True
    if block.get("bucket") == "generation_error":
        return True
    if block.get("bucket") == "score" and block.get("correctness") is None:
        return True
    return False


def _recompute_llm_summaries(report: dict[str, Any]) -> None:
    by_judge: dict[str, list] = defaultdict(list)
    by_cross: dict[str, list] = defaultdict(list)
    for case in report.get("cases") or []:
        for item in case.get("providers") or []:
            name = str(item.get("provider") or "unknown")
            if "judge" in item:
                by_judge[name].append(item["judge"])
            cross = item.get("cross_judge")
            if isinstance(cross, dict) and cross.get("bucket") != "no_peer":
                by_cross[name].append(cross)
    if by_judge:
        report["summary_judge"] = {name: aggregate_llm_cases(items) for name, items in by_judge.items()}
    if by_cross:
        report["summary_cross"] = {name: aggregate_llm_cases(items) for name, items in by_cross.items()}


def retry_failed_judges_path(
    eval_path: Path,
    run_path: Path,
    *,
    chunks_path: Path | None = None,
    settings: Settings | None = None,
    pass_threshold: float = PASS_THRESHOLD,
    workers: int = 1,
) -> dict[str, Any]:
    """Re-score only judge/cross_judge cells that have an ``error``, writing the eval in place."""
    if settings is None:
        from lab.config import load_settings

        settings = load_settings(require_keys=True)

    report = json.loads(eval_path.read_text(encoding="utf-8"))
    run_payload = json.loads(run_path.read_text(encoding="utf-8"))
    run_by_id = {str(case.get("case_id")): case for case in (run_payload.get("cases") or [])}
    chunk_texts = load_chunk_texts(chunks_path)
    store = default_store()

    has_cross = any(
        isinstance((row.get("cross_judge") or None), dict)
        for case in (report.get("cases") or [])
        for row in (case.get("providers") or [])
    )
    has_third = any(
        isinstance((row.get("judge") or None), dict)
        for case in (report.get("cases") or [])
        for row in (case.get("providers") or [])
    )
    cross_panel = make_cross_panel(settings) if has_cross else None
    judge = make_judge_provider(settings) if has_third else None
    judge_model = settings.judge_model if has_third else None

    jobs: list[dict[str, Any]] = []
    for case_i, case in enumerate(report.get("cases") or []):
        case_id = str(case.get("case_id") or "")
        run_case = run_by_id.get(case_id)
        if run_case is None:
            continue
        context_chunks, _ = resolve_context_chunks(run_case, chunk_texts, store=store)
        expected = str(run_case.get("expected_behavior") or case.get("expected_behavior") or "answer")
        run_providers = {str(row.get("provider")): row for row in (run_case.get("providers") or [])}
        for prov_i, row in enumerate(case.get("providers") or []):
            name = str(row.get("provider") or "unknown")
            run_row = run_providers.get(name) or {}
            score_kwargs = {
                "question": str(run_case.get("question") or ""),
                "reference": run_case.get("reference_answer"),
                "generated": str(run_row.get("visible_text") or ""),
                "context_chunks": context_chunks,
                "expected_behavior": expected,
                "is_refusal": bool(run_row.get("is_refusal")),
                "error": run_row.get("error"),
                "pass_threshold": pass_threshold,
            }
            if _judge_block_failed(row.get("cross_judge")) and cross_panel is not None:
                assignment = cross_panel.assignment_for(name)
                if assignment is not None:
                    jobs.append(
                        {
                            "case_i": case_i,
                            "prov_i": prov_i,
                            "kind": "cross",
                            "provider": assignment.judge,
                            "model": assignment.model,
                            "scored_by": assignment.judge_name,
                            "score_kwargs": score_kwargs,
                        }
                    )
            if _judge_block_failed(row.get("judge")) and judge is not None and judge_model:
                jobs.append(
                    {
                        "case_i": case_i,
                        "prov_i": prov_i,
                        "kind": "judge",
                        "provider": judge,
                        "model": judge_model,
                        "score_kwargs": score_kwargs,
                    }
                )

    worker_count = max(1, int(workers))
    _log(f"[eval] retry-errors {eval_path.name}: {len(jobs)} células com erro · workers={worker_count}")
    if not jobs:
        return {"name": eval_path.stem, "status": "ok", "retried": 0, "still_failed": 0}

    started = time.perf_counter()
    if worker_count == 1:
        results = [_run_llm_job(job) for job in jobs]
    else:
        results = []
        with ThreadPoolExecutor(max_workers=worker_count) as pool:
            futures = [pool.submit(_run_llm_job, job) for job in jobs]
            for future in as_completed(futures):
                results.append(future.result())

    still_failed = 0
    for result in results:
        item = report["cases"][result["case_i"]]["providers"][result["prov_i"]]
        judged = result["judged"]
        if result["kind"] == "judge":
            item["judge"] = judged
        else:
            item["cross_judge"] = judged
        if judged.get("error"):
            still_failed += 1

    _recompute_llm_summaries(report)
    report["evaluated_at"] = datetime.now(timezone.utc).isoformat()
    method = report.get("method")
    if isinstance(method, dict) and "judge" in method:
        method["judge"] = re.sub(
            r"timeout=\d+s(?: retries=\d+)?(?: backoff=\w+)?",
            "timeout=120s retries=5 backoff=exp",
            str(method["judge"]),
        )
    eval_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    _log(
        f"[eval] retry-errors {eval_path.name}: {len(jobs) - still_failed}/{len(jobs)} ok "
        f"em {time.perf_counter() - started:.1f}s · ainda com erro={still_failed}"
    )
    return {
        "name": eval_path.stem,
        "status": "ok" if still_failed == 0 else "partial",
        "retried": len(jobs),
        "still_failed": still_failed,
        "elapsed_s": round(time.perf_counter() - started, 1),
    }


def evaluate_path(
    run_path: Path,
    *,
    chunks_path: Path | None = None,
    settings: Settings | None = None,
    use_judge: bool = False,
    use_cross_judge: bool = False,
    pass_threshold: float = PASS_THRESHOLD,
    lexical: bool = True,
    workers: int = 1,
) -> Path:
    payload = json.loads(run_path.read_text(encoding="utf-8"))
    judge = None
    judge_model = None
    judge_provider_name = None
    cross_panel = None
    if use_judge or use_cross_judge:
        if settings is None:
            from lab.config import load_settings

            settings = load_settings(require_keys=True)
        if use_judge:
            judge = make_judge_provider(settings)
            judge_model = settings.judge_model
            judge_provider_name = settings.judge_provider
        if use_cross_judge:
            cross_panel = make_cross_panel(settings)
    modes: list[str] = []
    if lexical:
        modes.append("lexical")
    if use_judge:
        modes.append("judge")
    if use_cross_judge:
        modes.append("cross-judge")
    _log(f"[eval] {run_path.name} → scoring={' + '.join(modes) or 'none'}")
    started = time.perf_counter()
    report = evaluate_payload(
        payload,
        chunk_texts=load_chunk_texts(chunks_path),
        store=default_store(),
        judge=judge,
        judge_model=judge_model,
        judge_provider_name=judge_provider_name,
        cross_panel=cross_panel,
        pass_threshold=pass_threshold,
        log=True,
        lexical=lexical,
        workers=workers,
    )
    out_path = run_path.with_name(run_path.stem + ".eval.json")
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    _log(f"[eval] {run_path.name} gravado em {out_path.name} ({time.perf_counter() - started:.1f}s)")
    return out_path


def _fmt(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.3f}"


def _format_provider_block(title: str, summary: dict[str, Any]) -> list[str]:
    lines = [title]
    for provider, stats in summary.items():
        extra = ""
        if "n_unanswerable_ok" in stats:
            extra = (
                f"  unanswerable_ok={stats.get('n_unanswerable_ok', 0)}"
                f"  false_refusal={stats.get('n_false_refusal', 0)}"
            )
        lines.append(
            f"{provider}: correctness={_fmt(stats.get('correctness'))}  "
            f"grounded_rate={_fmt(stats.get('grounded_rate'))}  "
            f"completeness={_fmt(stats.get('completeness'))}  "
            f"pass_rate={_fmt(stats.get('pass_rate'))}  n={stats.get('n', 0)}{extra}"
        )
    return lines


def format_summary(report: dict[str, Any]) -> str:
    lines = [f"limiar pass_rate: correctness ≥ {report.get('pass_threshold')}"]
    lines.extend(_format_provider_block("lexical:", report.get("summary") or {}))
    if report.get("summary_cross"):
        lines.extend(_format_provider_block("cruzado (cego: gemini←xai, xai←gemini):", report["summary_cross"]))
    if report.get("summary_judge"):
        judge_meta = report.get("judge") or {}
        lines.extend(
            _format_provider_block(
                f"juiz terceiro ({judge_meta.get('provider')}/{judge_meta.get('model')}):",
                report["summary_judge"],
            )
        )
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Avaliar uma run da Fase 1 (métricas determinísticas e juiz opcional).")
    parser.add_argument("run", nargs="?", help="Ficheiro data/runs/phase1_*.json. Sem argumento, usa a mais recente.")
    parser.add_argument("--judge", action="store_true", help="Pontuar com um terceiro modelo (JUDGE_PROVIDER / JUDGE_MODEL).")
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
    parser.add_argument("--pass-threshold", type=float, default=PASS_THRESHOLD, help="Limiar de correctness para pass_rate (default 0.8).")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    run_path = Path(args.run) if args.run else latest_run()
    out_path = evaluate_path(
        run_path,
        use_judge=args.judge,
        use_cross_judge=args.cross_judge,
        pass_threshold=args.pass_threshold,
        lexical=not args.judge_only,
        workers=args.workers,
    )
    print(f"Run: {run_path}")
    print(f"Eval: {out_path}")


if __name__ == "__main__":
    main()
