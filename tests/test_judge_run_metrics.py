import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import judge_run_metrics as judge_script


def test_list_run_files_skips_aux(tmp_path: Path) -> None:
    (tmp_path / "top_n_1.json").write_text("{}", encoding="utf-8")
    (tmp_path / "top_n_1.eval.json").write_text("{}", encoding="utf-8")
    (tmp_path / "metrics.json").write_text("[]", encoding="utf-8")
    (tmp_path / "report.json").write_text("{}", encoding="utf-8")
    (tmp_path / "context_sweep.json").write_text("{}", encoding="utf-8")
    files = judge_script.list_run_files(tmp_path)
    assert [path.name for path in files] == ["top_n_1.json"]


def test_main_pack_only(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "top1.json").write_text(
        json.dumps(
            {
                "temperature": 0.1,
                "top_p": 0.9,
                "context_policy": {"mode": "top_n", "top_n": 1},
                "cases": [],
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "top1.eval.json").write_text(
        json.dumps(
            {
                "models": {"gemini": "g", "xai": "x"},
                "summary": {
                    "gemini": {"correctness": 1, "grounded_rate": 1, "completeness": 1, "n": 1},
                    "xai": {"correctness": 1, "grounded_rate": 1, "completeness": 1, "n": 1},
                },
                "cases": [{"case_id": "gold-01", "providers": [{"provider": "gemini", "passed": True}, {"provider": "xai", "passed": True}]}],
            }
        ),
        encoding="utf-8",
    )
    called: list[str] = []

    def fake_score(*_args, **_kwargs):
        called.append("score")
        return []

    monkeypatch.setattr(judge_script, "score_runs", fake_score)
    code = judge_script.main(["--run-dir", str(tmp_path), "--pack-only"])
    assert code == 0
    assert called == []
    assert (tmp_path / "report.json").is_file()


def test_main_scores_then_packs(tmp_path: Path, monkeypatch) -> None:
    run = tmp_path / "cfg.json"
    run.write_text(
        json.dumps({"dry_run": False, "cases": [{"providers": [{"provider": "gemini"}]}]}),
        encoding="utf-8",
    )
    (tmp_path / "cfg.eval.json").write_text(
        json.dumps(
            {
                "models": {"gemini": "g", "xai": "x"},
                "summary": {
                    "gemini": {"correctness": 1, "grounded_rate": 1, "completeness": 1, "n": 1},
                    "xai": {"correctness": 1, "grounded_rate": 1, "completeness": 1, "n": 1},
                },
                "summary_cross": {
                    "gemini": {"correctness": 0.9, "grounded_rate": 0.9, "completeness": 0.9, "n": 1},
                    "xai": {"correctness": 0.9, "grounded_rate": 0.9, "completeness": 0.9, "n": 1},
                },
                "cases": [
                    {
                        "case_id": "gold-01",
                        "providers": [
                            {"provider": "gemini", "passed": True, "cross_judge": {"passed": True, "bucket": "score"}},
                            {"provider": "xai", "passed": True, "cross_judge": {"passed": True, "bucket": "score"}},
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    def fake_score(run_files, **_kwargs):
        assert [path.name for path in run_files] == ["cfg.json"]
        return [
            {
                "name": "cfg",
                "status": "ok",
                "eval_path": str(tmp_path / "cfg.eval.json"),
                "summary_cross": {"gemini": {"n": 1}},
            }
        ]

    monkeypatch.setattr(judge_script, "score_runs", fake_score)
    code = judge_script.main(["--run-dir", str(tmp_path)])
    assert code == 0
    metrics = json.loads((tmp_path / "metrics.json").read_text(encoding="utf-8"))
    assert metrics[0]["status"] == "ok"
    report = json.loads((tmp_path / "report.json").read_text(encoding="utf-8"))
    assert report["scoring"] == "cross_judge"
