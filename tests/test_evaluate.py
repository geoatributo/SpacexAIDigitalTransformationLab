from lab.config import REFUSAL_SENTENCE
from lab.evaluate import evaluate_payload


def test_evaluate_payload_aggregates_by_provider() -> None:
    chunk_id = "chunk-a"
    payload = {
        "models": {"gemini": "g", "xai": "x"},
        "cases": [
            {
                "case_id": "gold-01",
                "expected_behavior": "answer",
                "reference_answer": "O limite é 25 MB. Usar WeTransfer ou Google Drive.",
                "chunk_ids": [chunk_id],
                "providers": [
                    {
                        "provider": "gemini",
                        "visible_text": "O limite é 25 MB. Usar WeTransfer ou Google Drive.",
                        "is_refusal": False,
                        "error": None,
                    },
                    {
                        "provider": "xai",
                        "visible_text": "",
                        "is_refusal": False,
                        "error": "ClientError",
                    },
                ],
            },
            {
                "case_id": "refuse-empty",
                "expected_behavior": "refuse",
                "reference_answer": None,
                "chunk_ids": [],
                "providers": [
                    {
                        "provider": "gemini",
                        "visible_text": REFUSAL_SENTENCE,
                        "is_refusal": True,
                        "error": None,
                    },
                    {
                        "provider": "xai",
                        "visible_text": REFUSAL_SENTENCE,
                        "is_refusal": True,
                        "error": None,
                    },
                ],
            },
        ],
    }
    report = evaluate_payload(
        payload,
        chunk_texts={chunk_id: "O limite de VPN é 25 MB. Alternativas: WeTransfer ou Google Drive."},
    )
    gemini = report["summary"]["gemini"]
    xai = report["summary"]["xai"]
    assert gemini["n"] == 2
    assert gemini["pass_rate"] == 1.0
    assert xai["pass_rate"] == 0.5
    assert xai["correctness"] == 0.5
