from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ContextChunk:
    index: int
    chunk_id: str
    title: str
    filename: str
    page: str
    section: str
    version: str
    text: str
    score: float


@dataclass(frozen=True)
class BuiltContext:
    case_id: str
    question: str
    chunks: list[ContextChunk]
    expected_behavior: str | None
    reference_answer: str | None


def _meta_get(metadata: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = metadata.get(key)
        if value not in (None, "", []):
            return str(value)
    frontmatter = metadata.get("frontmatter")
    if isinstance(frontmatter, dict):
        for key in keys:
            value = frontmatter.get(key)
            if value not in (None, "", []):
                return str(value)
    return ""


class ContextStore:
    def __init__(
        self,
        *,
        chunks_path: Path,
        retrieval_path: Path,
        gold_path: Path,
        max_chunks: int,
        similarity_floor: float,
        context_char_cap: int,
    ) -> None:
        self.max_chunks = max_chunks
        self.similarity_floor = similarity_floor
        self.context_char_cap = context_char_cap
        self._chunks = self._load_chunks(chunks_path)
        self._retrieval = self._load_retrieval(retrieval_path)
        self._gold = self._load_gold(gold_path)

    @staticmethod
    def _load_chunks(path: Path) -> dict[str, dict[str, Any]]:
        with path.open(encoding="utf-8") as handle:
            rows = json.load(handle)
        return {str(row["chunk_id"]): row for row in rows}

    @staticmethod
    def _load_retrieval(path: Path) -> dict[str, dict[str, Any]]:
        with path.open(encoding="utf-8") as handle:
            rows = json.load(handle)
        return {str(row["case_id"]): row for row in rows}

    @staticmethod
    def _load_gold(path: Path) -> dict[str, dict[str, Any]]:
        with path.open(encoding="utf-8") as handle:
            payload = json.load(handle)
        return {str(row["id"]): row for row in payload["cases"]}

    def gold_ids(self) -> list[str]:
        return list(self._gold.keys())

    def select_chunks(self, case_id: str) -> list[ContextChunk]:
        record = self._retrieval.get(case_id)
        if record is None:
            return []
        selected: list[ContextChunk] = []
        for candidate in record.get("candidates") or []:
            rank = int(candidate.get("rank") or 0)
            score = float(candidate.get("dense_cosine") or candidate.get("rrf_score") or 0.0)
            if rank != 1 and score < self.similarity_floor:
                continue
            chunk_id = str(candidate["chunk_id"])
            row = self._chunks.get(chunk_id)
            if row is None:
                continue
            metadata = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
            page_start = metadata.get("page_start")
            selected.append(
                ContextChunk(
                    index=len(selected) + 1,
                    chunk_id=chunk_id,
                    title=_meta_get(metadata, "title") or "sem título",
                    filename=_meta_get(metadata, "source_filename", "relative_path", "title"),
                    page="" if page_start in (None, "") else str(page_start),
                    section=_meta_get(metadata, "section_heading", "section_path"),
                    version=_meta_get(metadata, "document_version", "version"),
                    text=str(row.get("text") or ""),
                    score=score,
                )
            )
            if len(selected) >= self.max_chunks:
                break
        return self._fit_char_cap(selected)

    def _fit_char_cap(self, chunks: list[ContextChunk]) -> list[ContextChunk]:
        kept: list[ContextChunk] = []
        used = 0
        for chunk in chunks:
            extra = len(chunk.text)
            if kept and used + extra > self.context_char_cap:
                break
            if not kept and extra > self.context_char_cap:
                kept.append(chunk)
                break
            kept.append(chunk)
            used += extra
        return [
            ContextChunk(
                index=i,
                chunk_id=chunk.chunk_id,
                title=chunk.title,
                filename=chunk.filename,
                page=chunk.page,
                section=chunk.section,
                version=chunk.version,
                text=chunk.text,
                score=chunk.score,
            )
            for i, chunk in enumerate(kept, start=1)
        ]

    def build(self, case_id: str, *, empty_context: bool = False) -> BuiltContext:
        gold = self._gold.get(case_id)
        if gold is None:
            raise KeyError(f"Caso gold desconhecido: {case_id}")
        question = str(gold["question"])
        chunks = [] if empty_context else self.select_chunks(case_id)
        return BuiltContext(
            case_id=case_id,
            question=question,
            chunks=chunks,
            expected_behavior=gold.get("expected_behavior"),
            reference_answer=gold.get("reference_answer"),
        )
