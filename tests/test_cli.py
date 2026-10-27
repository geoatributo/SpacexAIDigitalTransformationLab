import pytest

from pathlib import Path

from lab.runner import parse_args, policy_from_args, run_output_path, select_gold_ids


def test_select_gold_ids_uses_file_order() -> None:
    ids = [f"gold-{index:02d}" for index in range(1, 51)] + ["p4-F8", "p4-R1"]
    assert select_gold_ids(ids, limit=5) == ["gold-01", "gold-02", "gold-03", "gold-04", "gold-05"]
    assert select_gold_ids(ids, limit=30) == ids[:30]
    assert select_gold_ids(ids, limit=100) == ids
    with pytest.raises(ValueError):
        select_gold_ids(ids, limit=0)


def test_run_output_path_uses_config_name() -> None:
    folder = Path("data/runs")
    named = run_output_path(folder, dry_run=True, run_name="top_n_6", stamp="20260101T000000Z")
    plain = run_output_path(folder, dry_run=False, run_name=None, stamp="20260101T000000Z")
    assert named == folder / "top_n_6.json"
    assert plain == folder / "phase1_20260101T000000Z.json"
    with pytest.raises(ValueError):
        run_output_path(folder, dry_run=False, run_name="../top_n_6", stamp="20260101T000000Z")


def test_cli_rejects_top_n_out_of_range() -> None:
    with pytest.raises(SystemExit):
        policy_from_args(parse_args(["--top-n", "0"]))
    with pytest.raises(SystemExit):
        policy_from_args(parse_args(["--top-n", "51"]))


def test_cli_adjacent_requires_m() -> None:
    with pytest.raises(SystemExit):
        policy_from_args(parse_args(["--context-mode", "top_n_adjacent", "--top-n", "3"]))


def test_cli_adjacent_ok() -> None:
    policy = policy_from_args(parse_args(["--context-mode", "top_n_adjacent", "--top-n", "3", "--adjacent-m", "2"]))
    assert policy.mode == "top_n_adjacent"
    assert policy.top_n == 3
    assert policy.adjacent_m == 2


def test_cli_full_top1() -> None:
    policy = policy_from_args(parse_args(["--context-mode", "full_top1"]))
    assert policy.to_dict()["top_n"] is None
    assert policy.mode == "full_top1"


def test_cli_top_k_alias_and_generation() -> None:
    args = parse_args(["--top-k", "4", "--temperature", "0.0", "--top-p", "1"])
    policy = policy_from_args(args)
    assert policy.top_n == 4
    assert args.temperature == 0.0
    assert args.top_p == 1.0


def test_cli_rejects_generation_out_of_range() -> None:
    from lab.config import load_settings
    from lab.runner import apply_generation

    settings = load_settings(require_keys=False)
    with pytest.raises(ValueError):
        apply_generation(settings, temperature=2.5, top_p=0.9)
    with pytest.raises(ValueError):
        apply_generation(settings, temperature=0.1, top_p=0)
    updated = apply_generation(settings, temperature=0.0, top_p=1.0)
    assert updated.temperature == 0.0
    assert updated.top_p == 1.0
