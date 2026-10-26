"""Run a list of context configurations as parallel `python -m lab` jobs."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIGS = Path(__file__).with_name("context_configs.json")


def _lab_argv(entry: dict, *, limit: int, dry_run: bool) -> list[str]:
    argv = [sys.executable, "-m", "lab", "--limit", str(entry.get("limit", limit))]
    argv.extend(["--context-mode", str(entry["context_mode"])])
    if entry.get("top_n") is not None and entry["context_mode"] != "full_top1":
        argv.extend(["--top-n", str(entry["top_n"])])
    if entry.get("adjacent_m") is not None:
        argv.extend(["--adjacent-m", str(entry["adjacent_m"])])
    if entry.get("max_chars") is not None:
        argv.extend(["--max-chars", str(entry["max_chars"])])
    if dry_run:
        argv.append("--dry-run")
    return argv


def _run_one(payload: dict) -> dict:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT / "src")
    started = datetime.now(timezone.utc)
    proc = subprocess.run(
        payload["argv"],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    finished = datetime.now(timezone.utc)
    return {
        "name": payload["name"],
        "argv": payload["argv"][2:],
        "returncode": proc.returncode,
        "started_at": started.isoformat(),
        "finished_at": finished.isoformat(),
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


def load_config_file(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Corre várias configurações de contexto em paralelo (python -m lab)."
    )
    parser.add_argument("--configs", type=Path, default=DEFAULT_CONFIGS, help="JSON com a lista de configs.")
    parser.add_argument("--jobs", type=int, default=os.cpu_count() or 2, help="Processos em paralelo.")
    parser.add_argument("--limit", type=int, default=None, help="Override do limit global do JSON.")
    parser.add_argument("--live", action="store_true", help="Chama Gemini/xAI (por defeito é dry-run).")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    spec = load_config_file(args.configs)
    limit = args.limit if args.limit is not None else int(spec.get("limit", 5))
    dry_run = False if args.live else bool(spec.get("dry_run", True))
    entries = spec["configs"]
    jobs = max(1, min(args.jobs, len(entries)))
    payloads = [
        {
            "name": entry.get("name") or f"cfg_{i}",
            "argv": _lab_argv(entry, limit=limit, dry_run=dry_run),
        }
        for i, entry in enumerate(entries, start=1)
    ]
    print(f"A correr {len(payloads)} configs com {jobs} processos (dry_run={dry_run})…", flush=True)
    results: list[dict] = []
    with ThreadPoolExecutor(max_workers=jobs) as pool:
        futures = {pool.submit(_run_one, payload): payload["name"] for payload in payloads}
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            status = "ok" if result["returncode"] == 0 else f"fail={result['returncode']}"
            print(f"[{status}] {result['name']}", flush=True)
            if result["returncode"] != 0:
                err = (result["stderr"] or result["stdout"] or "").strip()
                if err:
                    print(err[-2000:], flush=True)

    results.sort(key=lambda row: row["name"])
    out_dir = REPO_ROOT / "data" / "runs"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    summary_path = out_dir / f"context_sweep_{stamp}.json"
    summary = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "dry_run": dry_run,
        "jobs": jobs,
        "results": [
            {k: v for k, v in row.items() if k not in {"stdout", "stderr"}}
            | {"log_tail": (row.get("stdout") or "")[-500:]}
            for row in results
        ],
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Resumo: {summary_path}")
    return 0 if all(row["returncode"] == 0 for row in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
