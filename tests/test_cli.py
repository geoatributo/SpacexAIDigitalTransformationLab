import pytest

from lab.runner import parse_args, policy_from_args


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
