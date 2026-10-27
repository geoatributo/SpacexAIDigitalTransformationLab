"""Re-score an existing sweep run with an LLM judge and pack report.json.

Uses the already-generated answers in ``data/runs/<stamp>/<config>.json``.
Does not call the contestant models again — only the judge(s).

By default runs blind cross-judge (Grok scores Gemini, Gemini scores Grok).
Then rewrites ``*.eval.json``, ``metrics.json``, and ``report.json``.
The Metrics page prefers ``summary_cross`` / ``cross_judge.passed`` when present.

Examples:
  python scripts/judge_run_metrics.py --run-dir data/runs/20261026T172740Z
  python scripts/judge_run_metrics.py --run-dir data/runs/20261026T172740Z --only top_n_1_t01_p09
  python scripts/judge_run_metrics.py --run-dir data/runs/20261026T172740Z --judge
  python scripts/judge_run_metrics.py --run-dir data/runs/20261026T172740Z --pack-only
"""

from __future__ import annotations

import argparse
import json
import sys
import time
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
    parser.add_argument(
        "--pack-only",
        action="store_true",
        help="Não chama o juiz; só reempacota report.json a partir dos *.eval.json.",
    )
    parser.add_argument(
        "--pass-threshold",
        type=float,
        default=0.8,
        help="Limiar de correctness para pass (default 0.8).",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Destino do report.json (default: <run-dir>/report.json).",
    )
    return parser.parse_args(argv)


def score_runs(
    run_files: list[Path],
    *,
    use_cross_judge: bool,
    use_judge: bool,
    pass_threshold: float,
) -> list[dict]:
    from lab.config import load_settings
    from lab.evaluate import evaluate_path

    settings = load_settings(require_keys=True)
    rows: list[dict] = []
    total = len(run_files)
    mode = "cross-judge" if use_cross_judge else "judge"
    _log(f"[judge] {total} configs · mode={mode} · limiar={pass_threshold}")
    batch_started = time.perf_counter()
    for index, run_path in enumerate(run_files, start=1):
        payload = json.loads(run_path.read_text(encoding="utf-8"))
        n_cases = len(payload.get("cases") or [])
        if payload.get("dry_run") or not _has_answers(payload):
            rows.append({"name": run_path.stem, "status": "no_answers"})
            _log(f"[judge] {index}/{total} {run_path.stem}: sem respostas — a saltar")
            continue
        _log(f"[judge] {index}/{total} {run_path.stem}: a pontuar {n_cases} casos ({mode})…")
        started = time.perf_counter()
        try:
            out = evaluate_path(
                run_path,
                settings=settings,
                use_judge=use_judge,
                use_cross_judge=use_cross_judge,
                pass_threshold=pass_threshold,
            )
        except (Exception, SystemExit) as exc:
            rows.append({"name": run_path.stem, "status": "error", "error": str(exc)})
            _log(f"[judge] {index}/{total} {run_path.stem}: ERRO {exc}")
            continue
        report = json.loads(out.read_text(encoding="utf-8"))
        elapsed = time.perf_counter() - started
        summary_key = "summary_cross" if report.get("summary_cross") else (
            "summary_judge" if report.get("summary_judge") else "summary"
        )
        summary = report.get(summary_key) or {}
        rates = " ".join(
            f"{provider}=pass_rate={stats.get('pass_rate')}"
            for provider, stats in summary.items()
            if isinstance(stats, dict)
        )
        _log(
            f"[judge] {index}/{total} {run_path.stem}: ok em {elapsed:.1f}s"
            + (f" · {rates}" if rates else "")
        )
        row = {
            "name": run_path.stem,
            "status": "ok",
            "eval_path": str(out),
            "scoring": (report.get("method") or {}).get("scoring", summary_key),
            "summary": report.get("summary"),
        }
        for key in ("summary_judge", "summary_cross"):
            if report.get(key):
                row[key] = report[key]
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
    if not args.pack_only:
        use_cross_judge = args.judge_mode == "cross"
        use_judge = args.judge_mode == "third"
        metrics_rows = score_runs(
            run_files,
            use_cross_judge=use_cross_judge,
            use_judge=use_judge,
            pass_threshold=args.pass_threshold,
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

    if metrics_rows is not None and any(row.get("status") == "error" for row in metrics_rows):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
