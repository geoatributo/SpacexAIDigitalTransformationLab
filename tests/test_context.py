from lab.context import ContextPolicy, ContextStore


def _chunk(chunk_id: str, *, doc: str, index: int, text: str) -> dict:
    return {
        "chunk_id": chunk_id,
        "text": text,
        "metadata": {
            "document_id": doc,
            "chunk_index": index,
            "title": doc,
            "source_filename": f"{doc}.md",
        },
    }


def _store(policy: ContextPolicy) -> ContextStore:
    chunks = [
        _chunk("a0", doc="doc-a", index=0, text="A0"),
        _chunk("a1", doc="doc-a", index=1, text="A1"),
        _chunk("a2", doc="doc-a", index=2, text="A2"),
        _chunk("a3", doc="doc-a", index=3, text="A3"),
        _chunk("b0", doc="doc-b", index=0, text="B0"),
        _chunk("b1", doc="doc-b", index=1, text="B1"),
    ]
    retrieval = [
        {
            "case_id": "gold-01",
            "candidates": [
                {"rank": 1, "chunk_id": "a1", "dense_cosine": 0.9},
                {"rank": 2, "chunk_id": "a2", "dense_cosine": 0.8},
                {"rank": 3, "chunk_id": "b0", "dense_cosine": 0.2},
            ],
        }
    ]
    gold = [{"id": "gold-01", "question": "Pergunta?", "expected_behavior": "answer", "reference_answer": "A"}]
    return ContextStore(
        chunks={row["chunk_id"]: row for row in chunks},
        retrieval={row["case_id"]: row for row in retrieval},
        gold={row["id"]: row for row in gold},
        policy=policy,
    )


def test_top_n_returns_exact_ranks() -> None:
    store = _store(ContextPolicy(mode="top_n", top_n=2))
    chunks = store.select_chunks("gold-01")
    assert [chunk.chunk_id for chunk in chunks] == ["a1", "a2"]
    assert [chunk.index for chunk in chunks] == [1, 2]


def test_adjacent_includes_neighbors_and_dedupes() -> None:
    store = _store(ContextPolicy(mode="top_n_adjacent", top_n=2, adjacent_m=1))
    chunks = store.select_chunks("gold-01")
    # seeds a1,a2 → a0,a1,a2,a3 (a1±1 and a2±1 overlap)
    assert [chunk.chunk_id for chunk in chunks] == ["a0", "a1", "a2", "a3"]


def test_full_top1_uses_whole_document_not_just_topk() -> None:
    store = _store(ContextPolicy(mode="full_top1"))
    chunks = store.select_chunks("gold-01")
    assert [chunk.chunk_id for chunk in chunks] == ["a0", "a1", "a2", "a3"]
    assert "b0" not in [chunk.chunk_id for chunk in chunks]


def test_empty_context_for_refusal_case() -> None:
    store = _store(ContextPolicy(mode="top_n", top_n=2))
    built = store.build("gold-01", empty_context=True)
    assert built.chunks == []
    assert built.question == "Pergunta?"


def test_policy_rejects_bad_top_n() -> None:
    try:
        ContextPolicy(mode="top_n", top_n=0).validate()
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")
    try:
        ContextPolicy(mode="top_n", top_n=51).validate()
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")


def test_adjacent_requires_m() -> None:
    try:
        ContextPolicy(mode="top_n_adjacent", top_n=2, adjacent_m=None).validate()
    except ValueError:
        return
    raise AssertionError("expected ValueError")
