import json

import pytest

from lab.gold_upload import parse_gold_payload, save_uploaded_gold


def test_parse_gold_cases() -> None:
    gold, generations = parse_gold_payload(
        {
            "cases": [
                {"id": "n-01", "question": "Qual o limite VPN?", "expected_behavior": "answer"},
                {"case_id": "n-02", "text": "Quem aprova férias?"},
            ]
        }
    )
    assert gold["n-01"]["question"] == "Qual o limite VPN?"
    assert gold["n-02"]["question"] == "Quem aprova férias?"
    assert generations == {}


def test_parse_generation_run_keeps_answers_without_calling_models() -> None:
    gold, generations = parse_gold_payload(
        {
            "cases": [
                {
                    "case_id": "gold-01",
                    "question": "Qual o limite?",
                    "providers": [{"provider": "xai", "visible_text": "25 MB"}],
                }
            ]
        }
    )
    assert "gold-01" in gold
    assert generations["gold-01"]["providers"][0]["provider"] == "xai"


def test_reject_metrics_report_pack() -> None:
    with pytest.raises(ValueError, match="métricas"):
        parse_gold_payload({"cases": ["gold-01", "gold-02"], "configs": [{}], "disagreement": {"pass": []}})


def test_save_uploaded_gold(tmp_path) -> None:
    gold, _ = parse_gold_payload({"questions": [{"id": "q1", "question": "Teste?"}]})
    saved = save_uploaded_gold(tmp_path, gold)
    payload = json.loads((tmp_path / saved["file"]).read_text(encoding="utf-8"))
    assert payload["cases"][0]["id"] == "q1"
    assert saved["n"] == 1
