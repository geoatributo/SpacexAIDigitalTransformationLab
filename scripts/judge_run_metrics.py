"""Re-score an existing sweep run with an LLM judge and pack report.json.

Uses the already-generated answers in ``data/runs/<stamp>/<config>.json``.
Does not call the contestant models again — only the judge(s),
except ``--retry-errors`` which also re-calls contestants for answer cells with ``error``.

By default: blind cross-judge, **judge-only** (no lexical metrics).
Then rewrites ``*.eval.json``, ``metrics.json``, and ``report.json``.
The Metrics page prefers ``summary_cross`` / ``cross_judge.passed`` when present.

Examples:
  python scripts/judge_run_metrics.py --run-dir data/runs/20261026T172740Z
  python scripts/judge_run_metrics.py --run-dir data/runs/20261026T172740Z --only top_n_1_t01_p09
  python scripts/judge_run_metrics.py --run-dir data/runs/20261026T172740Z --with-lexical
  python scripts/judge_run_metrics.py --run-dir data/runs/20261026T172740Z --judge
  python scripts/judge_run_metrics.py --run-dir data/runs/20261026T172740Z --pack-only
  python scripts/judge_run_metrics.py --run-dir data/runs/20261026T172740Z_llm --retry-errors
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

SKIP_STEMS = frozenset({"metrics", "context_sweep", "report"})


def _log(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


def list_run_files(run_dir: Path) -> list[Path]:
    """Config answer files: ``*.json`` that are not eval/metrics/sweep/report."""
    files: list[Path] = []
    for path in sorted(run_dir.glob("*.json")):
        name = path.name
        if name.endswith(".eval.json"):
            continue
        if path.stem in SKIP_STEMS or name.startswith("context_sweep"):
            continue
        files.append(path)
    return files


def _has_answers(payload: dict) -> bool:
    return any(case.get("providers") for case in payload.get("cases") or [])


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Pontua uma corrida existente com juiz LLM e gera report.json."
    )
    parser.add_argument(
        "--run-dir",
        type=Path,
        required=True,
        help="Pasta da corrida (ex.: data/runs/20261026T172740Z).",
    )
    parser.add_argument(
        "--only",
        action="append",
        default=[],
        help="Só esta config (stem, ex. top_n_1_t01_p09). Pode repetir.",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--cross-judge",
        dest="judge_mode",
        action="store_const",
        const="cross",
        help="Grok↔Gemini às cegas (defeito).",
    )
    mode.add_argument(
        "--judge",
        dest="judge_mode",
        action="store_const",
        const="third",
        help="Terceiro juiz (JUDGE_PROVIDER / JUDGE_MODEL no .env).",
    )
    parser.set_defaults(judge_mode="cross")
    lexical = parser.add_mutually_exclusive_group()
    lexical.add_argument(
        "--judge-only",
        dest="lexical",
        action="store_false",
        help="Só juiz LLM, sem métricas lexicais (defeito).",
    )
    lexical.add_argument(
        "--with-lexical",
        dest="lexical",
        action="store_true",
        help="Também corre métricas lexicais locais.",
    )
    parser.set_defaults(lexical=False)
    parser.add_argument(
        "--pack-only",
        action="store_true",
        help="Não chama o juiz; só reempacota report.json a partir dos *.eval.json.",
    )
    parser.add_argument(
        "--retry-errors",
        action="store_true",
        help=(
            "Re-tenta respostas com error nos *.json (backoff exp.), "
            "depois re-pontua judge/cross_judge falhados nos *.eval.json, e reempacota."
        ),
    )
    parser.add_argument(
        "--pass-threshold",
        type=float,
        default=0.8,
        help="Limiar de correctness para pass (default 0.8).",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=64,
        help="Chamadas de juiz em paralelo por config (default 64).",
    )
    parser.add_argument(
        "--jobs",
        type=int,
        default=7,
        help="Configs em paralelo (default 7). Cuidado com rate limits.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Destino do report.json (default: <run-dir>/report.json).",
    )
    return parser.parse_args(argv)


def _score_one(
    run_path: Path,
    *,
    settings,
    use_cross_judge: bool,
    use_judge: bool,
    pass_threshold: float,
    lexical: bool,
    workers: int,
) -> dict:
    from lab.evaluate import evaluate_path

    payload = json.loads(run_path.read_text(encoding="utf-8"))
    if payload.get("dry_run") or not _has_answers(payload):
        return {"name": run_path.stem, "status": "no_answers"}
    started = time.perf_counter()
    out = evaluate_path(
        run_path,
        settings=settings,
        use_judge=use_judge,
        use_cross_judge=use_cross_judge,
        pass_threshold=pass_threshold,
        lexical=lexical,
        workers=workers,
    )
    report = json.loads(out.read_text(encoding="utf-8"))
    summary_key = "summary_cross" if report.get("summary_cross") else (
        "summary_judge" if report.get("summary_judge") else "summary"
    )
    row = {
        "name": run_path.stem,
        "status": "ok",
        "eval_path": str(out),
        "scoring": (report.get("method") or {}).get("scoring", summary_key),
        "summary": report.get("summary"),
        "elapsed_s": round(time.perf_counter() - started, 1),
    }
    for key in ("summary_judge", "summary_cross"):
        if report.get(key):
            row[key] = report[key]
    return row


def score_runs(
    run_files: list[Path],
    *,
    use_cross_judge: bool,
    use_judge: bool,
    pass_threshold: float,
    lexical: bool = False,
    workers: int = 8,
    jobs: int = 2,
) -> list[dict]:
    from lab.config import load_settings

    settings = load_settings(require_keys=True)
    total = len(run_files)
    mode = "cross-judge" if use_cross_judge else "judge"
    lexical_note = " + lexical" if lexical else " (judge-only)"
    job_count = max(1, min(int(jobs), total or 1))
    worker_count = max(1, int(workers))
    _log(
        f"[judge] {total} configs · mode={mode}{lexical_note} · limiar={pass_threshold} "
        f"· jobs={job_count} · workers={worker_count}"
    )
    batch_started = time.perf_counter()
    rows: list[dict] = []

    def _work(run_path: Path) -> dict:
        n_cases = len(json.loads(run_path.read_text(encoding="utf-8")).get("cases") or [])
        _log(f"[judge] {run_path.stem}: a pontuar {n_cases} casos ({mode}{lexical_note})…")
        try:
            return _score_one(
                run_path,
                settings=settings,
                use_cross_judge=use_cross_judge,
                use_judge=use_judge,
                pass_threshold=pass_threshold,
                lexical=lexical,
                workers=worker_count,
            )
        except (Exception, SystemExit) as exc:
            return {"name": run_path.stem, "status": "error", "error": str(exc)}

    if job_count == 1:
        ordered = [_work(path) for path in run_files]
    else:
        by_name: dict[str, dict] = {}
        with ThreadPoolExecutor(max_workers=job_count) as pool:
            futures = {pool.submit(_work, path): path for path in run_files}
            for future in as_completed(futures):
                row = future.result()
                by_name[str(row.get("name"))] = row
                if row.get("status") == "ok":
                    summary = row.get("summary_cross") or row.get("summary_judge") or row.get("summary") or {}
                    rates = " ".join(
                        f"{provider}=pass_rate={stats.get('pass_rate')}"
                        for provider, stats in summary.items()
                        if isinstance(stats, dict)
                    )
                    _log(
                        f"[judge] {row['name']}: ok em {row.get('elapsed_s', '?')}s"
                        + (f" · {rates}" if rates else "")
                    )
                elif row.get("status") == "error":
                    _log(f"[judge] {row['name']}: ERRO {row.get('error')}")
                else:
                    _log(f"[judge] {row['name']}: {row.get('status')}")
        ordered = [by_name[path.stem] for path in run_files if path.stem in by_name]
        for path in run_files:
            if path.stem not in by_name:
                ordered.append({"name": path.stem, "status": "missing"})

    for row in ordered:
        if job_count == 1:
            if row.get("status") == "ok":
                summary = row.get("summary_cross") or row.get("summary_judge") or row.get("summary") or {}
                rates = " ".join(
                    f"{provider}=pass_rate={stats.get('pass_rate')}"
                    for provider, stats in summary.items()
                    if isinstance(stats, dict)
                )
                _log(
                    f"[judge] {row['name']}: ok em {row.get('elapsed_s', '?')}s"
                    + (f" · {rates}" if rates else "")
                )
            elif row.get("status") == "error":
                _log(f"[judge] {row['name']}: ERRO {row.get('error')}")
            elif row.get("status") == "no_answers":
                _log(f"[judge] {row['name']}: sem respostas — a saltar")
        rows.append(row)

    _log(
        f"[judge] lote concluído em {time.perf_counter() - batch_started:.1f}s "
        f"({sum(1 for row in rows if row.get('status') == 'ok')}/{total} ok)"
    )
    return rows


def pack_report(run_dir: Path, out: Path | None = None) -> Path:
    from lab.sweep_report import write_report_pack

    return write_report_pack(run_dir, out, run_id=run_dir.name)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    run_dir = args.run_dir
    if not run_dir.is_dir():
        _log(f"Pasta inexistente: {run_dir}")
        return 1

    run_files = list_run_files(run_dir)
    if args.only:
        wanted = set(args.only)
        run_files = [path for path in run_files if path.stem in wanted]
        missing = wanted - {path.stem for path in run_files}
        if missing:
            _log(f"Configs em falta: {', '.join(sorted(missing))}")
            return 1
    if not run_files and not args.pack_only:
        _log(f"Nenhum ficheiro de config em {run_dir}")
        return 1

    metrics_rows = None
    if args.retry_errors and args.pack_only:
        _log("Usa --retry-errors ou --pack-only, não os dois.")
        return 1
    if args.retry_errors:
        from lab.config import load_settings
        from lab.evaluate import retry_failed_judges_path
        from lab.runner import configure_logging, retry_failed_answers_path

        configure_logging()
        settings = load_settings(require_keys=True)
        worker_count = max(1, int(args.workers))
        metrics_rows = []
        for run_path in run_files:
            answer_row: dict = {"name": run_path.stem, "answers": None}
            try:
                answer_row["answers"] = retry_failed_answers_path(
                    run_path,
                    settings=settings,
                    workers=worker_count,
                )
            except (Exception, SystemExit) as exc:
                answer_row["answers"] = {"status": "error", "error": str(exc)}
                _log(f"[retry-answers] {run_path.stem}: ERRO {exc}")

            eval_path = run_path.with_name(run_path.stem + ".eval.json")
            if not eval_path.is_file():
                _log(f"[judge] {run_path.stem}: sem {eval_path.name} — a saltar juiz")
                metrics_rows.append({**answer_row, "status": "no_eval"})
                continue
            try:
                judge_row = retry_failed_judges_path(
                    eval_path,
                    run_path,
                    settings=settings,
                    pass_threshold=args.pass_threshold,
                    workers=worker_count,
                )
            except (Exception, SystemExit) as exc:
                judge_row = {"name": run_path.stem, "status": "error", "error": str(exc)}
                _log(f"[judge] {run_path.stem}: ERRO {exc}")
            metrics_rows.append({**judge_row, "answers": answer_row.get("answers")})
        metrics_path = run_dir / "metrics.json"
        metrics_path.write_text(json.dumps(metrics_rows, ensure_ascii=False, indent=2), encoding="utf-8")
        _log(f"[judge] Métricas (retry): {metrics_path}")
    elif not args.pack_only:
        use_cross_judge = args.judge_mode == "cross"
        use_judge = args.judge_mode == "third"
        metrics_rows = score_runs(
            run_files,
            use_cross_judge=use_cross_judge,
            use_judge=use_judge,
            pass_threshold=args.pass_threshold,
            lexical=args.lexical,
            workers=args.workers,
            jobs=args.jobs,
        )
        metrics_path = run_dir / "metrics.json"
        metrics_path.write_text(json.dumps(metrics_rows, ensure_ascii=False, indent=2), encoding="utf-8")
        _log(f"[judge] Métricas: {metrics_path}")
        if any(row.get("status") == "error" for row in metrics_rows):
            _log("[judge] houve erros — a empacotar na mesma com o que existir")

    try:
        report_path = pack_report(run_dir, args.out)
    except FileNotFoundError as exc:
        _log(str(exc))
        return 1
    _log(f"[judge] Relatório: {report_path}")

    if metrics_rows is not None and any(
        row.get("status") == "error" or int(row.get("still_failed") or 0) > 0 for row in metrics_rows
    ):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
