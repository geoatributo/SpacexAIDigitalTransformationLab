from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from lab.context import ContextChunk, ContextStore
from lab.prompts import SYSTEM_PROMPT, build_user_prompt
from lab.providers.base import ChatProvider
from lab.scratchpad import strip_scratchpad

HistoryTurn = dict[str, str]


@dataclass(frozen=True)
class ChatAnswer:
    answer: str
    is_refusal: bool
    scratchpad_leaked: bool
    latency_ms: int
    provider: str
    model: str
    retrieval: str
    sources: list[dict[str, Any]]
    error: str | None = None


def _history_block(history: list[HistoryTurn] | None) -> str:
    turns: list[str] = []
    for item in (history or [])[-8:]:
        role = str(item.get("role") or "").strip().lower()
        content = str(item.get("content") or "").strip()
        if not content:
            continue
        label = "Utilizador" if role == "user" else "Assistente"
        turns.append(f"{label}: {content}")
    if not turns:
        return ""
    return "Histórico da conversa (só para pronomes; não cites):\n" + "\n".join(turns) + "\n\n"


def sources_from_chunks(chunks: list[ContextChunk]) -> list[dict[str, Any]]:
    return [
        {
            "index": chunk.index,
            "chunk_id": chunk.chunk_id,
            "document": chunk.title,
            "filename": chunk.filename,
            "page": chunk.page or None,
            "section": chunk.section or None,
            "score": round(chunk.score, 4),
            "excerpt": chunk.text[:400],
        }
        for chunk in chunks
    ]


def answer_question(
    *,
    question: str,
    history: list[HistoryTurn] | None,
    store: ContextStore,
    provider: ChatProvider,
    model: str,
) -> ChatAnswer:
    chunks, retrieval = store.select_for_query(question)
    user_prompt = _history_block(history) + build_user_prompt(question, chunks)
    result = provider.complete(system=SYSTEM_PROMPT, user=user_prompt, model=model)
    cleaned = strip_scratchpad(result.text)
    return ChatAnswer(
        answer=cleaned.visible_text,
        is_refusal=cleaned.is_refusal,
        scratchpad_leaked=cleaned.scratchpad_leaked,
        latency_ms=result.latency_ms,
        provider=provider.name,
        model=model,
        retrieval=retrieval,
        sources=sources_from_chunks(chunks),
        error=result.error,
    )
