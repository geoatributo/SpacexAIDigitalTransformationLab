"""Pack a run folder into one portable Metrics report JSON.

The file contains everything the Metrics page needs (scores, deltas, cost,
pass/refusal disagreement). Metrics are not preloaded from data/runs — upload
the packed JSON via POST /metrics/runs/upload (stored under data/metrics/).

Example:
  python scripts/pack_metrics_report.py --run-dir data/runs/20261026T172740Z
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from lab.sweep_report import write_report_pack  # noqa: E402


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Empacota uma corrida num report.json portátil.")
    parser.add_argument(
        "--run-dir",
        type=Path,
        required=True,
        help="Pasta da corrida (com *.eval.json e, de preferência, os *.json irmãos).",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Destino do JSON. Por defeito: <run-dir>/report.json",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    run_dir = args.run_dir
    if not run_dir.is_dir():
        print(f"Pasta inexistente: {run_dir}", file=sys.stderr)
        return 1
    try:
        out = write_report_pack(run_dir, args.out, run_id=run_dir.name)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(f"Relatório: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
