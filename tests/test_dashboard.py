import json

from lab.dashboard import metric_cards


def test_metric_cards_include_n_delta_and_challenge_notes(tmp_path) -> None:
    eval_payload = {
        "pass_threshold": 0.8,
        "models": {"gemini": "gemini-3.5-flash-lite", "xai": "grok-4"},
        "context_policy": {"mode": "top_n", "top_n": 6},
        "method": {"judge": "cruzado às cegas"},
        "summary_cross": {
            "gemini": {"correctness": 0.9, "grounded_rate": 0.8, "completeness": 0.7, "pass_rate": 1.0, "n": 5},
            "xai": {"correctness": 1.0, "grounded_rate": 0.9, "completeness": 0.8, "pass_rate": 1.0, "n": 5},
        },
        "cases": [
            {"expected_behavior": "answer"},
            {"expected_behavior": "refuse"},
        ],
    }
    (tmp_path / "phase1_test.eval.json").write_text(json.dumps(eval_payload), encoding="utf-8")
    payload = metric_cards(tmp_path)
    assert payload["n_refuse"] == 1
    assert payload["n_answer"] == 1
    card = next(item for item in payload["cards"] if item["id"] == "correctness")
    assert card["n"] == 5
    assert card["delta"] == 0.1
    assert "provisória" in card["color_policy"]
    assert {item["id"] for item in payload["challenges"]} >= {"D1", "D4", "D6", "D7"}
