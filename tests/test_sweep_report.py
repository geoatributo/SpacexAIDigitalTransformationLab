import json
import os
from pathlib import Path

import pytest

from lab.sweep_report import (
    build_report,
    list_runs,
    load_or_build_report,
    resolve_run_dir,
    save_uploaded_report,
    validate_report_pack,
    write_report_pack,
)


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _eval(gemini: float, xai: float, cases: list[dict]) -> dict:
    def row(score: float) -> dict:
        return {"correctness": score, "grounded_rate": score, "completeness": score, "n": 2}

    return {
        "models": {"gemini": "gemini-3.8-flash", "xai": "grok-4.20-0309-non-reasoning"},
        "summary": {"gemini": row(gemini), "xai": row(xai)},
        "cases": cases,
    }


def _case(case_id: str, providers: list[dict]) -> dict:
    return {"case_id": case_id, "providers": providers}


def _passed(gemini: bool, xai: bool) -> list[dict]:
    return [{"provider": "gemini", "passed": gemini}, {"provider": "xai", "passed": xai}]


def _cross_passed(gemini: bool, xai: bool, *, gemini_ok_refusal: bool = False, xai_ok_refusal: bool = False) -> list[dict]:
    def block(passed: bool, ok_refusal: bool) -> dict:
        if ok_refusal:
            return {"passed": False, "bucket": "unanswerable_ok", "unanswerable_ok": True}
        return {"passed": passed, "bucket": "score"}

    return [
        {
            "provider": "gemini",
            "passed": False,
            "cross_judge": block(gemini, gemini_ok_refusal),
        },
        {
            "provider": "xai",
            "passed": False,
            "cross_judge": block(xai, xai_ok_refusal),
        },
    ]


def _called(gemini_refusal: bool, xai_refusal: bool, gemini_ms: int, xai_ms: int) -> list[dict]:
    return [
        {"provider": "gemini", "is_refusal": gemini_refusal, "latency_ms": gemini_ms, "usage": {"total_tokens": 100}},
        {"provider": "xai", "is_refusal": xai_refusal, "latency_ms": xai_ms, "usage": {"total_tokens": 40}},
    ]


def _fill(folder: Path) -> None:
    _write(
        folder / "context_sweep.json",
        {
            "created_at": "2026-01-02T00:00:00+00:00",
            "results": [
                {"name": "adjacent", "returncode": 0},
                {"name": "top1", "returncode": 0},
            ],
        },
    )
    _write(
        folder / "top1.eval.json",
        _eval(
            0.9,
            0.7,
            [
                _case("gold-01", _passed(True, True)),
                _case("gold-02", _passed(True, False)),
            ],
        ),
    )
    _write(
        folder / "top1.json",
        {
            "temperature": 0.1,
            "top_p": 0.9,
            "context_policy": {"mode": "top_n", "top_n": 1},
            "cases": [
                _case("gold-01", _called(False, False, 1000, 3000)),
                _case("gold-02", _called(False, True, 3000, 1000)),
            ],
        },
    )
    _write(
        folder / "adjacent.eval.json",
        _eval(
            0.4,
            0.6,
            [
                _case("gold-01", _passed(False, True)),
                _case("gold-02", _passed(False, False)),
            ],
        ),
    )
    _write(
        folder / "adjacent.json",
        {
            "temperature": 0.1,
            "top_p": 0.9,
            "context_policy": {"mode": "top_n_adjacent", "top_n": 3, "adjacent_m": 1},
            "cases": [
                _case("gold-01", _called(False, False, 2000, 2000)),
                _case("gold-02", _called(True, True, 2000, 2000)),
            ],
        },
    )


def test_report_orders_configs_and_scores_disagreement(tmp_path: Path) -> None:
    root = tmp_path / "runs"
    older = root / "20260101T000000Z"
    newer = root / "20260102T000000Z"
    _fill(older)
    _fill(newer)
    _write(root / "flat.eval.json", _eval(1, 1, [_case("gold-01", _passed(True, True))]))
    _write(root / "flat.json", {"temperature": 0.2, "top_p": 0.5, "context_policy": {"mode": "top_n", "top_n": 6}, "cases": []})
    for path in older.iterdir():
        os.utime(path, (1_500_000_000, 1_500_000_000))
    for path in newer.iterdir():
        os.utime(path, (2_000_000_000, 2_000_000_000))
    os.utime(root / "flat.eval.json", (1_400_000_000, 1_400_000_000))

    listed = list_runs(root)
    assert [row["id"] for row in listed] == ["20260102T000000Z", "20260101T000000Z", "runs"]
    assert listed[0]["config_count"] == 2
    assert listed[0]["created_at"] == "2026-01-02T00:00:00+00:00"

    report = build_report(resolve_run_dir(root, "20260102T000000Z"), run_id="20260102T000000Z")
    assert [row["name"] for row in report["configs"]] == ["top1", "adjacent"]
    assert report["configs"][0]["label"] == "Top 1"
    assert report["configs"][1]["title"] == "Top 3 chunks with 1 adjacent, T=0.1, top_p=0.9"
    assert report["sampling_note"] == "T=0.1, top_p=0.9"
    assert report["models"]["gemini"] == "gemini-3.8-flash"
    assert report["models"]["xai"] == "grok-4.20-0309-non-reasoning"
    assert abs(report["configs"][0]["delta"]["correctness"] - -0.2) < 1e-9
    assert abs(report["configs"][1]["delta"]["correctness"] - 0.2) < 1e-9
    assert report["cases"] == ["gold-01", "gold-02"]
    assert report["disagreement"]["pass"] == [[0, 1], [2, 3]]
    assert report["disagreement"]["refusal"] == [[0, 2], [0, 3]]
    assert report["configs"][0]["cost"]["gemini"]["median_s"] == 2
    assert "pass_rate" not in report["configs"][0]


def test_unknown_run_is_rejected(tmp_path: Path) -> None:
    root = tmp_path / "runs"
    root.mkdir()
    with pytest.raises(FileNotFoundError):
        resolve_run_dir(root, "../secret")
    with pytest.raises(FileNotFoundError):
        resolve_run_dir(root, "missing")


def test_write_and_load_report_pack(tmp_path: Path) -> None:
    folder = tmp_path / "20260102T000000Z"
    _fill(folder)
    path = write_report_pack(folder)
    assert path.name == "report.json"
    packed = load_or_build_report(folder, run_id="20260102T000000Z")
    built = build_report(folder, run_id="20260102T000000Z")
    assert packed["configs"] == built["configs"]
    assert packed["disagreement"] == built["disagreement"]
    assert packed["configs"][0]["cost"]["gemini"]["median_s"] == 2
    assert packed["disagreement"]["refusal"] == [[0, 2], [0, 3]]


def test_list_runs_includes_pack_only_folder(tmp_path: Path) -> None:
    root = tmp_path / "runs"
    source = tmp_path / "source"
    _fill(source)
    report = build_report(source, run_id="source")
    saved = save_uploaded_report(root, report)
    listed = list_runs(root)
    assert listed[0]["id"] == saved["id"]
    assert listed[0]["config_count"] == 2
    loaded = load_or_build_report(resolve_run_dir(root, saved["id"]), run_id=saved["id"])
    assert loaded["id"] == saved["id"]
    assert loaded["disagreement"]["pass"] == report["disagreement"]["pass"]


def test_validate_report_pack_rejects_incomplete(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="configs"):
        validate_report_pack({"cases": [], "disagreement": {"pass": [], "refusal": []}})
    with pytest.raises(ValueError, match="disagreement"):
        validate_report_pack({"configs": [{"name": "x"}], "cases": []})


def test_report_prefers_cross_judge_summary_and_pass(tmp_path: Path) -> None:
    folder = tmp_path / "20260103T000000Z"
    _write(
        folder / "context_sweep.json",
        {"created_at": "2026-01-03T00:00:00+00:00", "results": [{"name": "top1", "returncode": 0}]},
    )
    _write(
        folder / "top1.eval.json",
        {
            "models": {"gemini": "g", "xai": "x"},
            "summary": {
                "gemini": {"correctness": 0.1, "grounded_rate": 0.1, "completeness": 0.1, "n": 2},
                "xai": {"correctness": 0.1, "grounded_rate": 0.1, "completeness": 0.1, "n": 2},
            },
            "summary_cross": {
                "gemini": {"correctness": 0.9, "grounded_rate": 0.8, "completeness": 0.7, "n": 1},
                "xai": {"correctness": 0.85, "grounded_rate": 0.75, "completeness": 0.65, "n": 1},
            },
            "cases": [
                _case("gold-01", _cross_passed(True, True)),
                _case("gold-02", _cross_passed(False, False, gemini_ok_refusal=True, xai_ok_refusal=True)),
            ],
        },
    )
    _write(
        folder / "top1.json",
        {
            "temperature": 0.1,
            "top_p": 0.9,
            "context_policy": {"mode": "top_n", "top_n": 1},
            "cases": [
                _case("gold-01", _called(False, False, 1000, 1000)),
                _case("gold-02", _called(True, True, 1000, 1000)),
            ],
        },
    )
    report = build_report(folder, run_id=folder.name)
    assert report["scoring"] == "cross_judge"
    assert report["configs"][0]["scoring"] == "cross_judge"
    assert abs(report["configs"][0]["metrics"]["gemini"]["correctness"] - 0.9) < 1e-9
    # lexical passed was False for both; cross_judge says both pass (incl. unanswerable_ok)
    assert report["disagreement"]["pass"] == [[0, 0]]
