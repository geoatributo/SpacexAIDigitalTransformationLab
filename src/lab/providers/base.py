from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass
class CompletionResult:
    text: str
    latency_ms: int
    usage: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


class ChatProvider(Protocol):
    name: str

    def complete(self, *, system: str, user: str) -> CompletionResult: ...
