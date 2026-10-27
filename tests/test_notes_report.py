from lab.compare import save_evaluation
from lab.notes_report import format_evaluation_report, get_metrics_note, save_metrics_note


def test_save_evaluation_notes_only(tmp_path) -> None:
    path = tmp_path / "evaluations.json"
    row = save_evaluation("gold-01", notes="Parece empate.", path=path)
    assert row["verdict"] is None
    assert row["notes"] == "Parece empate."
    again = save_evaluation("gold-01", verdict="tie", notes="Confirmado.", path=path)
    assert again["verdict"] == "tie"
    kept = save_evaluation("gold-01", notes="Só texto.", path=path)
    assert kept["verdict"] == "tie"
    assert kept["notes"] == "Só texto."


def test_metrics_notes_and_text_report(tmp_path) -> None:
    compare = tmp_path / "evaluations.json"
    metrics = tmp_path / "metrics_notes.json"
    save_evaluation("gold-02", verdict="xai_better", notes="xAI mais completo", path=compare)
    saved = save_metrics_note("20261027T100000Z", "Grok ganha em grounded.", path=metrics)
    assert saved["run_id"] == "20261027T100000Z"
    assert get_metrics_note("20261027T100000Z", path=metrics)["notes"] == "Grok ganha em grounded."
    text = format_evaluation_report(
        compare_path=compare,
        metrics_path=metrics,
        blind_rows=[
            {
                "case_id": "gold-03",
                "rater_id": "abc",
                "score_a": 8,
                "score_b": 6,
                "notes": "A melhor",
                "created_at": "2026-10-27T12:00:00+00:00",
            }
        ],
    )
    assert "Relatório de avaliações humanas" in text
    assert "[gold-02] xAI melhor" in text
    assert "xAI mais completo" in text
    assert "[20261027T100000Z]" in text
    assert "Grok ganha em grounded." in text
    assert "[gold-03] avaliador=abc · A=8 · B=6" in text
    assert "A melhor" in text
