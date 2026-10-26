from __future__ import annotations

import re
from dataclasses import dataclass

from lab.config import REFUSAL_SENTENCE

_OPEN = re.compile(r"<\s*scratchpad\s*>", re.IGNORECASE)
_CLOSE = re.compile(r"</\s*scratchpad\s*[>\]\)\}]?", re.IGNORECASE)
_BLOCK = re.compile(
    r"<\s*scratchpad\s*>.*?((</\s*scratchpad\s*[>\]\)\}]?)|$)",
    re.IGNORECASE | re.DOTALL,
)


@dataclass(frozen=True)
class ScratchpadResult:
    visible_text: str
    scratchpad_leaked: bool
    is_refusal: bool


def _collapse_space(text: str) -> str:
    collapsed = re.sub(r"[ \t]+\n", "\n", text)
    collapsed = re.sub(r"\n{3,}", "\n\n", collapsed)
    collapsed = re.sub(r" {2,}", " ", collapsed)
    return collapsed.strip()


def strip_scratchpad(raw_text: str) -> ScratchpadResult:
    raw = raw_text or ""
    stripped = _BLOCK.sub(" ", raw)
    if _OPEN.search(stripped):
        stripped = _OPEN.split(stripped, maxsplit=1)[0]
    if _CLOSE.search(stripped):
        stripped = _CLOSE.split(stripped, maxsplit=1)[-1]
    visible = _collapse_space(stripped)
    leaked = bool(
        _OPEN.search(visible)
        or _CLOSE.search(visible)
        or re.search(r"<\s*scratchpad", visible, re.IGNORECASE)
    )
    is_refusal = visible.strip() == REFUSAL_SENTENCE
    return ScratchpadResult(
        visible_text=visible,
        scratchpad_leaked=leaked,
        is_refusal=is_refusal,
    )
