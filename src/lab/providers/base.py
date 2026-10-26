from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


def format_provider_error(exc: BaseException, *, secrets: tuple[str, ...] = ()) -> str:
    text = f"{type(exc).__name__}: {exc}"
    for secret in secrets:
        if secret:
            text = text.replace(secret, "[REDACTED]")
    return text[:800]


@dataclass
class CompletionResult:
    text: str
    latency_ms: int
    usage: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


class ChatProvider(Protocol):
    name: str

    def complete(
        self,
        *,
        system: str,
        user: str,
        model: str | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        max_output_tokens: int | None = None,
        timeout: float | None = None,
    ) -> CompletionResult: ...
