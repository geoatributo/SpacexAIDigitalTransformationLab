import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import run_context_configs as sweep


def test_lab_argv_adjacent_dry_run() -> None:
    argv = sweep._lab_argv(
        {"context_mode": "top_n_adjacent", "top_n": 3, "adjacent_m": 1},
        limit=2,
        dry_run=True,
    )
    assert argv[2:] == [
        "lab",
        "--limit",
        "2",
        "--context-mode",
        "top_n_adjacent",
        "--top-n",
        "3",
        "--adjacent-m",
        "1",
        "--dry-run",
    ]


def test_lab_argv_full_top1_omits_top_n() -> None:
    argv = sweep._lab_argv({"context_mode": "full_top1", "top_n": 6}, limit=5, dry_run=False)
    assert "--top-n" not in argv
    assert "--dry-run" not in argv
    assert "full_top1" in argv
