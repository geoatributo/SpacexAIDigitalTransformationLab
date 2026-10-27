"""Run a list of context configurations as parallel `python -m lab` jobs.

``temperature`` and ``top_p`` are read from each config entry only. Both
models in that job share the entry's values. There is no file-level or
CLI override for them. ``top_k`` on an entry is the chunk count, the same
setting as ``top_n``.

``--metrics`` scores every config run in ``data/runs/<name>.json``. Without
``--live`` it only scores files already saved.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIGS = Path(__file__).with_name("context_configs.json")


def _entry_name(entry: dict) -> str:
    return str(entry.get("name") or "?")


def _resolve_top_k(entry: dict) -> int | None:
    """Chunk count for this entry. ``top_k`` and ``top_n`` are the same setting."""
    top_k = entry.get("top_k")
    top_n = entry.get("top_n")
    if top_k is not None and top_n is not None and int(top_k) != int(top_n):
        raise ValueError(f"{_entry_name(entry)}: top_k={top_k} e top_n={top_n} têm de ser iguais")
    if top_k is not None:
        return int(top_k)
    if top_n is not None:
        return int(top_n)
    return None


def _entry_unit_float(entry: dict, key: str, *, low: float, high: float, low_exclusive: bool) -> float | None:
    if entry.get(key) is None:
        return None
    value = float(entry[key])
    ok = low < value <= high if low_exclusive else low <= value <= high
    if not ok:
        bound = f"maior que {low} e no máximo {high}" if low_exclusive else f"entre {low} e {high}"
        raise ValueError(f"{_entry_name(entry)}: {key} deve estar {bound} (recebido {value})")
    return value


def _lab_argv(entry: dict, *, limit: int, dry_run: bool, runs_dir: Path | None = None) -> list[str]:
    argv = [sys.executable, "-m", "lab", "--limit", str(entry.get("limit", limit))]
    argv.extend(["--context-mode", str(entry["context_mode"])])
    resolved_k = _resolve_top_k(entry)
    if resolved_k is not None and entry["context_mode"] != "full_top1":
        argv.extend(["--top-n", str(resolved_k)])
    if entry.get("adjacent_m") is not None:
        argv.extend(["--adjacent-m", str(entry["adjacent_m"])])
    if entry.get("max_chars") is not None:
        argv.extend(["--max-chars", str(entry["max_chars"])])
    temperature = _entry_unit_float(entry, "temperature", low=0, high=2, low_exclusive=False)
    top_p = _entry_unit_float(entry, "top_p", low=0, high=1, low_exclusive=True)
    if temperature is not None:
        argv.extend(["--temperature", str(temperature)])
    if top_p is not None:
        argv.extend(["--top-p", str(top_p)])
    if entry.get("name"):
        argv.extend(["--run-name", str(entry["name"])])
    if runs_dir is not None:
        argv.extend(["--runs-dir", str(runs_dir)])
    if dry_run:
        argv.append("--dry-run")
    return argv


_print_lock = threading.Lock()
_PROGRESS_LINE = re.compile(r"^PROGRESS\s+(\d+)/(\d+)\s*$")


def _relay_stream(stream, *, name: str, sink: list[str], show_progress: bool) -> None:
    """Capture child output; optionally print only step counters to stdout."""
    for raw in iter(stream.readline, ""):
        sink.append(raw)
        if not show_progress:
            continue
        match = _PROGRESS_LINE.match(raw.rstrip("\n\r"))
        if match is None:
            continue
        with _print_lock:
            print(f"[{name}] {match.group(1)}/{match.group(2)}", flush=True)
    stream.close()


def _run_one(payload: dict) -> dict:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT / "src")
    env["PYTHONUNBUFFERED"] = "1"
    env.setdefault("PYTHONIOENCODING", "utf-8")
    env["LAB_PROGRESS_ONLY"] = "1"
    name = payload["name"]
    started = datetime.now(timezone.utc)
    proc = subprocess.Popen(
        payload["argv"],
        cwd=REPO_ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )
    stdout_chunks: list[str] = []
    stderr_chunks: list[str] = []
    readers = [
        threading.Thread(
            target=_relay_stream,
            args=(proc.stdout,),
            kwargs={"name": name, "sink": stdout_chunks, "show_progress": True},
            daemon=True,
        ),
        threading.Thread(
            target=_relay_stream,
            args=(proc.stderr,),
            kwargs={"name": name, "sink": stderr_chunks, "show_progress": False},
            daemon=True,
        ),
    ]
    for thread in readers:
        thread.start()
    returncode = proc.wait()
    for thread in readers:
        thread.join()
    finished = datetime.now(timezone.utc)
    return {
        "name": name,
        "argv": payload["argv"][2:],
        "returncode": returncode,
        "started_at": started.isoformat(),
        "finished_at": finished.isoformat(),
        "stdout": "".join(stdout_chunks),
        "stderr": "".join(stderr_chunks),
    }


def load_config_file(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def config_names(entries: list[dict]) -> list[str]:
    return [str(entry.get("name") or f"cfg_{i}") for i, entry in enumerate(entries, start=1)]


def latest_run_dir(root: Path) -> Path:
    """Most recently written run folder. Flat files in ``root`` are the fallback."""
    folders = [path for path in root.iterdir() if path.is_dir()] if root.is_dir() else []
    if not folders:
        return root
    folders.sort(key=lambda path: path.stat().st_mtime)
    return folders[-1]


def should_launch_jobs(*, metrics: bool, live: bool) -> bool:
    """``--metrics`` alone scores saved runs. ``--live`` still launches the models."""
    return live or not metrics


def _has_answers(payload: dict) -> bool:
    return any(case.get("providers") for case in payload.get("cases") or [])


def _score_saved_run(run_path: Path, *, pass_threshold: float) -> dict:
    src = str(REPO_ROOT / "src")
    if src not in sys.path:
        sys.path.insert(0, src)
    from lab.evaluate import evaluate_path

    out = evaluate_path(run_path, pass_threshold=pass_threshold)
    report = json.loads(out.read_text(encoding="utf-8"))
    scored = {"eval_path": str(out), "summary": report.get("summary")}
    for key in ("summary_judge", "summary_cross"):
        if report.get(key):
            scored[key] = report[key]
    return scored


def evaluate_config_runs(
    names: list[str],
    *,
    runs_dir: Path,
    pass_threshold: float = 0.8,
    evaluate_run=None,
) -> list[dict]:
    scorer = evaluate_run or (lambda path: _score_saved_run(path, pass_threshold=pass_threshold))
    rows: list[dict] = []
    for name in names:
        run_path = runs_dir / f"{name}.json"
        if not run_path.is_file():
            rows.append({"name": name, "status": "missing"})
            print(f"[metrics] {name}: ficheiro em falta ({run_path.name})", file=sys.stderr, flush=True)
            continue
        payload = json.loads(run_path.read_text(encoding="utf-8"))
        if payload.get("dry_run") or not _has_answers(payload):
            rows.append({"name": name, "status": "no_answers"})
            print(f"[metrics] {name}: sem respostas de modelo", file=sys.stderr, flush=True)
            continue
        try:
            scored = scorer(run_path)
        except (Exception, SystemExit) as exc:
            rows.append({"name": name, "status": "error", "error": str(exc)})
            print(f"[metrics] {name}: {exc}", file=sys.stderr, flush=True)
            continue
        rows.append({"name": name, "status": "ok", **scored})
    return rows


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Corre várias configurações de contexto em paralelo (python -m lab)."
    )
    parser.add_argument("--configs", type=Path, default=DEFAULT_CONFIGS, help="JSON com a lista de configs.")
    parser.add_argument("--jobs", type=int, default=os.cpu_count() or 2, help="Processos em paralelo.")
    parser.add_argument("--limit", type=int, default=None, help="Override do limit global do JSON.")
    parser.add_argument("--live", action="store_true", help="Chama Gemini/xAI (por defeito é dry-run).")
    parser.add_argument(
        "--run-dir",
        type=Path,
        default=None,
        help="Pasta da corrida. Sem isto, uma corrida nova cria data/runs/<timestamp>/; --metrics sozinho usa a mais recente.",
    )
    parser.add_argument(
        "--metrics",
        action="store_true",
        help="Calcula as métricas de cada config na pasta da corrida. Sem --live, não chama os modelos.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    spec = load_config_file(args.configs)
    limit = args.limit if args.limit is not None else int(spec.get("limit", 5))
    dry_run = False if args.live else bool(spec.get("dry_run", True))
    entries = spec["configs"]
    names = config_names(entries)
    launch = should_launch_jobs(metrics=args.metrics, live=args.live)
    runs_root = REPO_ROOT / "data" / "runs"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    if args.run_dir is not None:
        run_dir = args.run_dir
    elif launch:
        run_dir = runs_root / stamp
    else:
        run_dir = latest_run_dir(runs_root)
    run_dir.mkdir(parents=True, exist_ok=True)
    results: list[dict] = []
    jobs = 0
    if launch:
        jobs = max(1, min(args.jobs, len(entries) or 1))
        try:
            payloads = [
                {"name": name, "argv": _lab_argv(entry, limit=limit, dry_run=dry_run, runs_dir=run_dir)}
                for name, entry in zip(names, entries, strict=True)
            ]
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        total = len(payloads)
        print(f"A correr {total} configs com {jobs} processos (dry_run={dry_run})…", flush=True)
        with ThreadPoolExecutor(max_workers=jobs) as pool:
            futures = {pool.submit(_run_one, payload): payload["name"] for payload in payloads}
            done = 0
            for future in as_completed(futures):
                result = future.result()
                results.append(result)
                done += 1
                status = "ok" if result["returncode"] == 0 else f"fail={result['returncode']}"
                print(f"[{status}] {result['name']} ({done}/{total})", flush=True)
                if result["returncode"] != 0:
                    err = (result["stderr"] or result["stdout"] or "").strip()
                    if err:
                        print(err[-2000:], flush=True)
        results.sort(key=lambda row: row["name"])

    metrics_rows = None
    if args.metrics:
        metrics_rows = evaluate_config_runs(names, runs_dir=run_dir)

    summary_path = run_dir / "context_sweep.json"
    summary = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "run_dir": str(run_dir),
        "dry_run": dry_run,
        "launched": launch,
        "jobs": jobs if launch else 0,
        "results": [
            {k: v for k, v in row.items() if k not in {"stdout", "stderr"}}
            | {"log_tail": (row.get("stdout") or "")[-500:]}
            for row in results
        ],
    }
    if metrics_rows is not None:
        summary["metrics"] = metrics_rows
        metrics_path = run_dir / "metrics.json"
        metrics_path.write_text(json.dumps(metrics_rows, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Métricas: {metrics_path}")
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Resumo: {summary_path}")
    jobs_failed = any(row["returncode"] != 0 for row in results)
    metrics_failed = metrics_rows is not None and any(row["status"] != "ok" for row in metrics_rows)
    return 1 if jobs_failed or metrics_failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
