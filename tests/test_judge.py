from lab.evaluate import evaluate_payload
from lab.providers.base import CompletionResult
from lab.rag_judge import JUDGE_SYSTEM_PROMPT


class FakeJudge:
    name = "gemini"

    def complete(self, **kwargs):
        assert kwargs["model"] == "gemini-3.5-flash"
        assert kwargs["system"] == JUDGE_SYSTEM_PROMPT
        user = kwargs["user"].lower()
        assert "gemini" not in user
        assert "grok" not in user
        assert "three metrics" in kwargs["user"]
        return CompletionResult(
            text='{"correctness": 90, "grounded": 100, "completeness": 80}',
            latency_ms=12,
        )


def test_evaluate_payload_records_judge_scores() -> None:
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
                    {"provider": "gemini", "visible_text": "25 MB", "is_refusal": False, "error": None},
                ],
            }
        ],
    }
    report = evaluate_payload(
        payload,
        chunk_texts={"c1": "O limite é 25 MB."},
        judge=FakeJudge(),
        judge_model="gemini-3.5-flash",
        judge_provider_name="gemini",
    )
    judged = report["cases"][0]["providers"][0]["judge"]
    assert judged["correctness"] == 0.9
    assert judged["grounded"] == 1.0
    assert judged["completeness"] == 0.8
    assert judged["error"] is None
    assert len(judged["calls"]) == 1
    assert report["summary_judge"]["gemini"]["pass_rate"] == 1.0
    assert report["judge"]["model"] == "gemini-3.5-flash"
