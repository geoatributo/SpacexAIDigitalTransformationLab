from lab.config import REPO_ROOT
from lab.context import ContextStore


def _store() -> ContextStore:
    data = REPO_ROOT / "data"
    return ContextStore(
        chunks_path=data / "chunk_data" / "chunks.json",
        retrieval_path=data / "chunk_data" / "retrieval.json",
        gold_path=data / "geoatributo_base2_gold_questions.json",
        max_chunks=6,
        similarity_floor=0.45,
        context_char_cap=9000,
    )


def test_selects_top_chunks_and_keeps_first_below_floor() -> None:
    store = _store()
    chunks = store.select_chunks("gold-01")
    assert 1 <= len(chunks) <= 6
    assert chunks[0].index == 1
    assert chunks[0].text
    for later in chunks[1:]:
        assert later.score >= 0.45


def test_empty_context_for_refusal_case() -> None:
    store = _store()
    built = store.build("gold-01", empty_context=True)
    assert built.chunks == []
    assert built.question
