from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

ContextMode = Literal["top_n", "top_n_adjacent", "full_top1"]
CONTEXT_MODES: tuple[str, ...] = ("top_n", "top_n_adjacent", "full_top1")


@dataclass(frozen=True)
class ContextPolicy:
    mode: ContextMode = "top_n"
    top_n: int = 6
    adjacent_m: int | None = None
    max_chars: int | None = None

    def validate(self) -> None:
        if self.mode not in CONTEXT_MODES:
            raise ValueError(f"context-mode inválido: {self.mode}")
        if self.mode != "full_top1" and not 1 <= self.top_n <= 50:
            raise ValueError("--top-n deve estar entre 1 e 50")
        if self.mode == "top_n_adjacent" and (self.adjacent_m is None or self.adjacent_m < 1):
            raise ValueError("--adjacent-m é obrigatório (>= 1) no modo top_n_adjacent")
        if self.max_chars is not None and self.max_chars < 1:
            raise ValueError("--max-chars deve ser >= 1")

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "top_n": None if self.mode == "full_top1" else self.top_n,
            "adjacent_m": self.adjacent_m if self.mode == "top_n_adjacent" else None,
            "max_chars": self.max_chars,
        }


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
    document_id: str = ""
    chunk_index: int = 0


@dataclass(frozen=True)
class BuiltContext:
    case_id: str
    question: str
    chunks: list[ContextChunk]
    expected_behavior: str | None
    reference_answer: str | None

    @property
    def char_count(self) -> int:
        return sum(len(chunk.text) for chunk in self.chunks)


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


def _row_metadata(row: dict[str, Any]) -> dict[str, Any]:
    metadata = row.get("metadata")
    return metadata if isinstance(metadata, dict) else {}


def _document_id(row: dict[str, Any]) -> str:
    metadata = _row_metadata(row)
    return _meta_get(metadata, "document_id", "source_document_id")


def _chunk_index(row: dict[str, Any]) -> int:
    metadata = _row_metadata(row)
    raw = metadata.get("chunk_index")
    try:
        return int(raw)
    except (TypeError, ValueError):
        return 0


class ContextStore:
    def __init__(
        self,
        *,
        chunks: dict[str, dict[str, Any]],
        retrieval: dict[str, dict[str, Any]],
        gold: dict[str, dict[str, Any]],
        policy: ContextPolicy,
    ) -> None:
        policy.validate()
        self.policy = policy
        self._chunks = chunks
        self._retrieval = retrieval
        self._gold = gold
        self._by_document = self._index_documents()

    @classmethod
    def from_files(
        cls,
        *,
        chunks_path: Path,
        retrieval_path: Path,
        gold_path: Path,
        policy: ContextPolicy,
    ) -> ContextStore:
        return cls(
            chunks=cls._load_chunks(chunks_path),
            retrieval=cls._load_retrieval(retrieval_path),
            gold=cls._load_gold(gold_path),
            policy=policy,
        )

    def _index_documents(self) -> dict[str, list[str]]:
        grouped: dict[str, list[tuple[int, str]]] = {}
        for chunk_id, row in self._chunks.items():
            doc_id = _document_id(row)
            if not doc_id:
                continue
            grouped.setdefault(doc_id, []).append((_chunk_index(row), chunk_id))
        return {
            doc_id: [chunk_id for _, chunk_id in sorted(entries, key=lambda item: (item[0], item[1]))]
            for doc_id, entries in grouped.items()
        }

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

    def gold_case(self, case_id: str) -> dict[str, Any] | None:
        return self._gold.get(case_id)

    def gold_question(self, case_id: str) -> str:
        row = self._gold.get(case_id) or {}
        return str(row.get("question") or "")

    def _ranked_candidates(self, case_id: str) -> list[tuple[str, float]]:
        record = self._retrieval.get(case_id)
        if record is None:
            return []
        ranked: list[tuple[int, str, float]] = []
        for candidate in record.get("candidates") or []:
            chunk_id = str(candidate["chunk_id"])
            if chunk_id not in self._chunks:
                continue
            rank = int(candidate.get("rank") or len(ranked) + 1)
            score = float(candidate.get("dense_cosine") or candidate.get("rrf_score") or 0.0)
            ranked.append((rank, chunk_id, score))
        ranked.sort(key=lambda item: item[0])
        return [(chunk_id, score) for _, chunk_id, score in ranked]

    def _to_context_chunk(self, chunk_id: str, *, score: float, index: int) -> ContextChunk:
        row = self._chunks[chunk_id]
        metadata = _row_metadata(row)
        page_start = metadata.get("page_start")
        return ContextChunk(
            index=index,
            chunk_id=chunk_id,
            title=_meta_get(metadata, "title") or "sem título",
            filename=_meta_get(metadata, "source_filename", "relative_path", "title"),
            page="" if page_start in (None, "") else str(page_start),
            section=_meta_get(metadata, "section_heading", "section_path"),
            version=_meta_get(metadata, "document_version", "version"),
            text=str(row.get("text") or ""),
            score=score,
            document_id=_document_id(row),
            chunk_index=_chunk_index(row),
        )

    def _scores_for(self, case_id: str) -> dict[str, float]:
        return {chunk_id: score for chunk_id, score in self._ranked_candidates(case_id)}

    def _ordered_ids(self, chunk_ids: list[str]) -> list[str]:
        unique: list[str] = []
        seen: set[str] = set()
        for chunk_id in chunk_ids:
            if chunk_id in seen or chunk_id not in self._chunks:
                continue
            seen.add(chunk_id)
            unique.append(chunk_id)
        unique.sort(key=lambda cid: (_document_id(self._chunks[cid]), _chunk_index(self._chunks[cid]), cid))
        return unique

    def _expand_adjacent(self, seed_ids: list[str], *, adjacent_m: int) -> list[str]:
        expanded: list[str] = []
        for seed_id in seed_ids:
            row = self._chunks[seed_id]
            doc_id = _document_id(row)
            sequence = self._by_document.get(doc_id) or [seed_id]
            try:
                position = sequence.index(seed_id)
            except ValueError:
                expanded.append(seed_id)
                continue
            start = max(0, position - adjacent_m)
            end = min(len(sequence), position + adjacent_m + 1)
            expanded.extend(sequence[start:end])
        return expanded

    def select_chunks(self, case_id: str) -> list[ContextChunk]:
        ranked = self._ranked_candidates(case_id)
        if not ranked:
            return []
        policy = self.policy
        if policy.mode == "full_top1":
            top_id = ranked[0][0]
            doc_id = _document_id(self._chunks[top_id])
            chosen_ids = list(self._by_document.get(doc_id) or [top_id])
        else:
            seeds = [chunk_id for chunk_id, _ in ranked[: policy.top_n]]
            if policy.mode == "top_n_adjacent":
                chosen_ids = self._expand_adjacent(seeds, adjacent_m=policy.adjacent_m or 1)
            else:
                chosen_ids = seeds
            if policy.mode == "top_n":
                # Keep retrieval rank order for plain top-N.
                chunks = [
                    self._to_context_chunk(chunk_id, score=score, index=i)
                    for i, (chunk_id, score) in enumerate(ranked[: policy.top_n], start=1)
                ]
                return self._fit_char_cap(chunks)
        scores = self._scores_for(case_id)
        ordered = self._ordered_ids(chosen_ids)
        chunks = [
            self._to_context_chunk(chunk_id, score=scores.get(chunk_id, 0.0), index=i)
            for i, chunk_id in enumerate(ordered, start=1)
        ]
        return self._fit_char_cap(chunks)

    def _fit_char_cap(self, chunks: list[ContextChunk]) -> list[ContextChunk]:
        cap = self.policy.max_chars
        if cap is None:
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
                    document_id=chunk.document_id,
                    chunk_index=chunk.chunk_index,
                )
                for i, chunk in enumerate(chunks, start=1)
            ]
        kept: list[ContextChunk] = []
        used = 0
        for chunk in chunks:
            extra = len(chunk.text)
            if kept and used + extra > cap:
                break
            if not kept and extra > cap:
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
                document_id=chunk.document_id,
                chunk_index=chunk.chunk_index,
            )
            for i, chunk in enumerate(kept, start=1)
        ]

    def select_for_query(self, question: str, *, gold_match_floor: float = 0.55) -> tuple[list[ContextChunk], str]:
        """Frozen retrieval when the question matches gold; otherwise lexical ranking over chunks."""
        matched = self._match_gold_case(question, floor=gold_match_floor)
        if matched:
            return self.select_chunks(matched), f"frozen_gold:{matched}"
        return self._select_lexical(question), "lexical"

    def _match_gold_case(self, question: str, *, floor: float) -> str | None:
        from lab.metrics import _content_tokens

        query_tokens = set(_content_tokens(question))
        if not query_tokens:
            return None
        best_id = None
        best = 0.0
        for case_id, row in self._gold.items():
            gold_tokens = set(_content_tokens(str(row.get("question") or "")))
            if not gold_tokens:
                continue
            score = len(query_tokens & gold_tokens) / len(query_tokens | gold_tokens)
            if score > best:
                best = score
                best_id = case_id
        return best_id if best_id is not None and best >= floor else None

    def _select_lexical(self, question: str) -> list[ContextChunk]:
        from lab.metrics import _content_tokens

        query_tokens = set(_content_tokens(question))
        if not query_tokens:
            return []
        ranked: list[tuple[float, str]] = []
        for chunk_id, row in self._chunks.items():
            chunk_tokens = set(_content_tokens(str(row.get("text") or "")))
            if not chunk_tokens:
                continue
            overlap = len(query_tokens & chunk_tokens)
            if overlap == 0:
                continue
            ranked.append((overlap / len(query_tokens), chunk_id))
        ranked.sort(key=lambda item: item[0], reverse=True)
        top_n = self.policy.top_n if self.policy.mode != "full_top1" else 1
        chosen = ranked[:top_n]
        chunks = [
            self._to_context_chunk(chunk_id, score=score, index=index)
            for index, (score, chunk_id) in enumerate(chosen, start=1)
        ]
        return self._fit_char_cap(chunks)

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
