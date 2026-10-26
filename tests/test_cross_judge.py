from lab.config import REFUSAL_SENTENCE
from lab.evaluate import evaluate_payload
from lab.judge import CROSS_PEER, CrossJudgePanel, identity_leaks
from lab.providers.base import CompletionResult
from lab.rag_judge import JUDGE_SYSTEM_PROMPT


class RecordingJudge:
    def __init__(self, name: str) -> None:
        self.name = name
        self.calls: list[dict] = []

    def complete(self, **kwargs):
        self.calls.append(kwargs)
        assert kwargs["system"] == JUDGE_SYSTEM_PROMPT
        assert identity_leaks(kwargs["system"]) == []
        assert identity_leaks(kwargs["user"]) == []
        assert "gemini" not in kwargs["user"].lower()
        assert "grok" not in kwargs["user"].lower()
        assert "xai" not in kwargs["user"].lower()
        return CompletionResult(text="85", latency_ms=5)


def test_cross_panel_routes_gemini_to_xai() -> None:
    gemini = RecordingJudge("gemini")
    xai = RecordingJudge("xai")
    panel = CrossJudgePanel(
        judges={
            "gemini": (gemini, "gemini-flash-lite-latest"),
            "xai": (xai, "grok-latest"),
        }
    )
    assert CROSS_PEER["gemini"] == "xai"
    assigned = panel.assignment_for("gemini")
    assert assigned is not None
    assert assigned.judge_name == "xai"
    assert assigned.model == "grok-latest"
    assert assigned.judge is xai


def test_evaluate_payload_cross_judge_is_blind_and_swapped() -> None:
    gemini = RecordingJudge("gemini")
    xai = RecordingJudge("xai")
    panel = CrossJudgePanel(
        judges={
            "gemini": (gemini, "gemini-flash-lite-latest"),
            "xai": (xai, "grok-latest"),
        }
    )
    payload = {
        "models": {"gemini": "gemini-flash-lite-latest", "xai": "grok-latest"},
        "cases": [
            {
                "case_id": "gold-01",
                "question": "Qual o limite?",
                "expected_behavior": "answer",
                "reference_answer": "25 MB",
                "chunk_ids": ["c1"],
                "providers": [
                    {"provider": "gemini", "visible_text": "O limite é 25 MB.", "is_refusal": False, "error": None},
                    {"provider": "xai", "visible_text": "Limite de 25 MB.", "is_refusal": False, "error": None},
                ],
            },
            {
                "case_id": "refuse-empty",
                "question": "Pergunta sem corpus",
                "expected_behavior": "refuse",
                "reference_answer": None,
                "chunk_ids": [],
                "providers": [
                    {"provider": "gemini", "visible_text": REFUSAL_SENTENCE, "is_refusal": True, "error": None},
                    {"provider": "xai", "visible_text": REFUSAL_SENTENCE, "is_refusal": True, "error": None},
                ],
            },
        ],
    }
    report = evaluate_payload(payload, chunk_texts={"c1": "O limite é 25 MB."}, cross_panel=panel)
    gemini_row = report["cases"][0]["providers"][0]["cross_judge"]
    xai_row = report["cases"][0]["providers"][1]["cross_judge"]
    assert gemini_row["blind"] is True
    assert gemini_row["scored_by"] == "xai"
    assert gemini_row["scored_by_model"] == "grok-latest"
    assert xai_row["scored_by"] == "gemini"
    assert len(xai.calls) == 3
    assert len(gemini.calls) == 3
    assert xai.calls[0]["model"] == "grok-latest"
    assert "O limite é 25 MB." in xai.calls[0]["user"]
    assert "Limite de 25 MB." in gemini.calls[0]["user"]
    assert report["summary_cross"]["gemini"]["n"] == 1
    assert report["summary_cross"]["gemini"]["n_unanswerable_ok"] == 1
    assert report["cases"][1]["providers"][0]["cross_judge"]["bucket"] == "unanswerable_ok"
