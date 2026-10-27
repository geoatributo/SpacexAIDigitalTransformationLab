import pytest

from lab.human_eval import (
    MemoryStore,
    assignment_for,
    blind_answers,
    create_session,
    export_rows,
    rater_id,
    save_rating,
    summary,
)


@pytest.fixture
def store() -> MemoryStore:
    return MemoryStore()


def test_same_name_same_rater_id() -> None:
    assert rater_id("Ana") == rater_id(" ana ")


def test_default_store_memory_backend(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HUMAN_EVAL_STORE", "memory")
    from lab.human_eval import default_store as make_store

    assert isinstance(make_store(), MemoryStore)


def test_assignment_is_stable_and_blind_payload_hides_providers(store: MemoryStore) -> None:
    session = create_session("Ana", "rate", store=store)
    first = assignment_for(session["id"], "gold-01", store=store)
    second = assignment_for(session["id"], "gold-01", store=store)
    assert first == second
    assert set(first) == {"xai", "gemini"}
    result = {
        "case_id": "gold-01",
        "question": "Qual o limite?",
        "chunk_count": 6,
        "expected_behavior": "answer",
        "xai": {"visible_text": "25 MB", "error": None},
        "gemini": {"visible_text": "O limite é 25 MB.", "error": None},
    }
    payload = blind_answers(result, first[0], first[1])
    assert "xai" not in payload
    assert "gemini" not in str(payload).lower()
    assert payload["answer_a"]["text"] in {"25 MB", "O limite é 25 MB."}


def test_metrics_only_session_is_not_a_rating(store: MemoryStore) -> None:
    session = create_session("Ana", "metrics_only", store=store)
    try:
        save_rating(
            session_id=session["id"],
            case_id="gold-01",
            score_a=8,
            score_b=7,
            store=store,
            run_file="run.json",
            context={},
        )
    except ValueError:
        pass
    else:
        raise AssertionError("metrics_only should not save ratings")
    stats = summary(store=store, case_ids=["gold-01"])
    assert stats["distinct_raters"] == 0


def test_export_uses_rater_id_not_name(store: MemoryStore) -> None:
    session = create_session("Ana Silva", "rate", store=store)
    save_rating(
        session_id=session["id"],
        case_id="gold-01",
        score_a=9,
        score_b=6,
        store=store,
        run_file="run.json",
        context={"policy": {"top_n": 6}},
    )
    rows = export_rows(store=store)
    assert "name" not in rows[0]
    assert rows[0]["rater_id"] == rater_id("Ana Silva")
    assert {rows[0]["slot_a"], rows[0]["slot_b"]} == {"xai", "gemini"}
    assert rows[0]["context"]["policy"]["top_n"] == 6
