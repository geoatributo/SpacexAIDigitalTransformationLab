from lab.compare import (
    evaluations_csv,
    list_questions,
    result_for,
    save_evaluation,
)
from lab.context import ContextPolicy, ContextStore


def _store() -> ContextStore:
    chunks = {
        "c1": {
            "chunk_id": "c1",
            "text": "Limite VPN 25 MB.",
            "metadata": {"document_id": "doc", "chunk_index": 0, "title": "VPN", "source_filename": "vpn.md"},
        }
    }
    return ContextStore(
        chunks=chunks,
        retrieval={"gold-01": {"case_id": "gold-01", "candidates": [{"rank": 1, "chunk_id": "c1", "dense_cosine": 0.9}]}},
        gold={"gold-01": {"id": "gold-01", "question": "Qual o limite?", "question_type": "factual", "expected_behavior": "answer", "reference_answer": "25 MB"}},
        policy=ContextPolicy(mode="top_n", top_n=1),
    )


def test_list_and_result_use_run_without_regenerating(tmp_path) -> None:
    store = _store()
    generations = {
        "gold-01": {
            "case_id": "gold-01",
            "question": "Qual o limite?",
            "chunk_ids": ["c1"],
            "chunk_count": 1,
            "empty_context": False,
            "expected_behavior": "answer",
            "reference_answer": "25 MB",
            "providers": [
                {
                    "provider": "xai",
                    "visible_text": "25 MB [1]",
                    "latency_ms": 10,
                    "usage": {"prompt_tokens": 8, "completion_tokens": 4, "total_tokens": 12},
                    "is_refusal": False,
                    "scratchpad_leaked": False,
                    "error": None,
                },
                {
                    "provider": "gemini",
                    "visible_text": "O limite é 25 MB.",
                    "latency_ms": 20,
                    "usage": {"prompt_tokens": 8, "completion_tokens": 7, "total_tokens": 15},
                    "is_refusal": False,
                    "scratchpad_leaked": False,
                    "error": None,
                },
            ],
        }
    }
    questions = list_questions(store, generations=generations, evaluations={})
    assert questions[0]["id"] == "gold-01"
    assert questions[0]["has_results"] is True
    payload = result_for(
        store,
        "gold-01",
        generations=generations,
        evaluations={},
        models={"xai": "grok-latest", "gemini": "g"},
    )
    assert payload["case_id"] == "gold-01"
    assert payload["chunk_ids"] == ["c1"]
    assert payload["chunk_count"] == 1
    assert payload["models"]["xai"] == "grok-latest"
    assert payload["xai"]["visible_text"] == "25 MB [1]"
    assert payload["xai"]["usage"]["prompt_tokens"] == 8
    assert payload["gemini"]["latency_ms"] == 20
    assert "text" not in payload["xai"]
    assert payload["sources"][0]["document"] == "VPN"


def test_evaluation_writes_json_and_csv(tmp_path) -> None:
    path = tmp_path / "evaluations.json"
    row = save_evaluation("gold-01", verdict="tie", notes="iguais", path=path)
    assert row["verdict"] == "tie"
    csv_text = evaluations_csv(path)
    assert "gold-01,tie,iguais" in csv_text.replace("\r\n", "\n")
