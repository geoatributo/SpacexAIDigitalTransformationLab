import json
import sys
from pathlib import Path

import pytest

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


def test_lab_argv_writes_into_the_run_folder() -> None:
    argv = sweep._lab_argv(
        {"name": "top_n_6", "context_mode": "top_n", "top_n": 6},
        limit=1,
        dry_run=True,
        runs_dir=Path("data/runs/20261026T160000Z"),
    )
    assert argv[argv.index("--runs-dir") + 1] == str(Path("data/runs/20261026T160000Z"))


def test_lab_argv_uses_config_name() -> None:
    argv = sweep._lab_argv(
        {"name": "top_n_6", "context_mode": "top_n", "top_n": 6, "temperature": 0.1, "top_p": 0.9},
        limit=5,
        dry_run=True,
    )
    assert argv[argv.index("--run-name") + 1] == "top_n_6"


def test_lab_argv_full_top1_omits_top_n() -> None:
    argv = sweep._lab_argv({"context_mode": "full_top1", "top_n": 6}, limit=5, dry_run=False)
    assert "--top-n" not in argv
    assert "--dry-run" not in argv
    assert "full_top1" in argv


def test_lab_argv_generation_comes_from_the_entry() -> None:
    argv = sweep._lab_argv(
        {"context_mode": "top_n", "top_k": 8, "temperature": 0.0, "top_p": 1.0},
        limit=1,
        dry_run=True,
    )
    assert argv[2:] == [
        "lab",
        "--limit",
        "1",
        "--context-mode",
        "top_n",
        "--top-n",
        "8",
        "--temperature",
        "0.0",
        "--top-p",
        "1.0",
        "--dry-run",
    ]


def test_omitted_generation_is_not_filled_from_elsewhere() -> None:
    argv = sweep._lab_argv({"context_mode": "top_n", "top_n": 3}, limit=1, dry_run=True)
    assert "--temperature" not in argv
    assert "--top-p" not in argv


def test_metrics_alone_does_not_launch_jobs() -> None:
    assert sweep.should_launch_jobs(metrics=True, live=False) is False
    assert sweep.should_launch_jobs(metrics=True, live=True) is True
    assert sweep.should_launch_jobs(metrics=False, live=False) is True


def test_evaluate_config_runs_skips_missing_and_dry(tmp_path: Path) -> None:
    (tmp_path / "top_n_1.json").write_text(
        json.dumps({"dry_run": True, "cases": [{"providers": []}]}),
        encoding="utf-8",
    )
    (tmp_path / "top_n_6.json").write_text(
        json.dumps({"dry_run": False, "cases": [{"providers": [{"provider": "gemini"}]}]}),
        encoding="utf-8",
    )
    seen: list[Path] = []

    def fake_score(path: Path) -> dict:
        seen.append(path)
        return {"eval_path": str(path.with_suffix(".eval.json")), "summary": {"gemini": {"n": 1}}, "text": "lexical:"}

    rows = sweep.evaluate_config_runs(
        ["top_n_1", "top_n_3", "top_n_6"],
        runs_dir=tmp_path,
        evaluate_run=fake_score,
    )
    assert [row["status"] for row in rows] == ["no_answers", "missing", "ok"]
    assert seen == [tmp_path / "top_n_6.json"]
    assert rows[2]["summary"]["gemini"]["n"] == 1


def test_top_k_and_top_n_must_match() -> None:
    with pytest.raises(ValueError, match="clash"):
        sweep._lab_argv(
            {"name": "clash", "context_mode": "top_n", "top_k": 2, "top_n": 4},
            limit=1,
            dry_run=True,
        )
