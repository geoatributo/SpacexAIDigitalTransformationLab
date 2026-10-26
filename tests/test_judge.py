from lab.evaluate import evaluate_payload
from lab.judge import parse_judge_json, scores_from_judge_payload
from lab.providers.base import CompletionResult


class FakeJudge:
    name = "gemini"

    def complete(self, *, system: str, user: str, model: str | None = None, temperature=None, max_output_tokens=None):
        assert model == "gemini-3.5-flash"
        assert "Resposta visível" in user
        return CompletionResult(
            text='{"correctness": 0.9, "completeness": 0.8, "grounded_rate": 1, "rationale": "Cobre o limite de 25 MB."}',
            latency_ms=12,
        )


def test_parse_judge_json_strips_fences() -> None:
    raw = '```json\n{"correctness": 1, "completeness": 0.5, "grounded_rate": 0.2, "rationale": "ok"}\n```'
    parsed = parse_judge_json(raw)
    assert parsed["correctness"] == 1.0
    assert parsed["completeness"] == 0.5
    scores = scores_from_judge_payload(parsed)
    assert scores.passed is True
    assert scores.completeness == 0.5


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
    assert judged["error"] is None
    assert report["summary_judge"]["gemini"]["pass_rate"] == 1.0
    assert report["judge"]["model"] == "gemini-3.5-flash"
