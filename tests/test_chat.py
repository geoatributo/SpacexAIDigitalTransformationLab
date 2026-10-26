from lab.chat import answer_question
from lab.context import ContextPolicy, ContextStore
from lab.prompts import SYSTEM_PROMPT
from lab.providers.base import CompletionResult


def _store() -> ContextStore:
    chunks = {
        "c1": {
            "chunk_id": "c1",
            "text": "O limite de envio por VPN é 25 MB. Usar WeTransfer ou Google Drive.",
            "metadata": {
                "document_id": "doc-a",
                "chunk_index": 0,
                "title": "VPN",
                "source_filename": "vpn.md",
                "page_start": 3,
            },
        },
        "c2": {
            "chunk_id": "c2",
            "text": "O plano de emergência define o ponto de encontro no parque.",
            "metadata": {
                "document_id": "doc-b",
                "chunk_index": 0,
                "title": "Emergência",
                "source_filename": "emergencia.md",
                "page_start": 1,
            },
        },
    }
    gold = {
        "gold-01": {
            "id": "gold-01",
            "question": "Qual o limite de envio por VPN?",
            "expected_behavior": "answer",
            "reference_answer": "25 MB",
        }
    }
    retrieval = {
        "gold-01": {
            "case_id": "gold-01",
            "candidates": [{"rank": 1, "chunk_id": "c1", "dense_cosine": 0.91}],
        }
    }
    return ContextStore(
        chunks=chunks,
        retrieval=retrieval,
        gold=gold,
        policy=ContextPolicy(mode="top_n", top_n=2),
    )


class FakeProvider:
    name = "xai"

    def __init__(self) -> None:
        self.calls: list[dict] = []

    def complete(self, **kwargs):
        self.calls.append(kwargs)
        return CompletionResult(text="O limite é 25 MB. [1]", latency_ms=9)


def test_gold_question_uses_frozen_retrieval() -> None:
    store = _store()
    chunks, retrieval = store.select_for_query("Qual o limite de envio por VPN?")
    assert retrieval.startswith("frozen_gold:")
    assert [chunk.chunk_id for chunk in chunks] == ["c1"]


def test_unrelated_question_uses_lexical_chunks() -> None:
    store = _store()
    chunks, retrieval = store.select_for_query("Onde é o ponto de encontro do plano de emergência?")
    assert retrieval == "lexical"
    assert chunks[0].chunk_id == "c2"


def test_answer_question_uses_existing_prompt_and_complete() -> None:
    provider = FakeProvider()
    result = answer_question(
        question="Qual o limite de envio por VPN?",
        history=[{"role": "user", "content": "Olá"}, {"role": "assistant", "content": "Em que posso ajudar?"}],
        store=_store(),
        provider=provider,
        model="grok-latest",
    )
    assert result.answer == "O limite é 25 MB. [1]"
    assert result.sources[0]["page"] == "3"
    assert result.sources[0]["document"] == "VPN"
    call = provider.calls[0]
    assert call["system"] == SYSTEM_PROMPT
    assert call["model"] == "grok-latest"
    assert "Histórico da conversa" in call["user"]
    assert "Pergunta:" in call["user"]
    assert "25 MB" in call["user"]
