"""Shared exponential backoff for provider / judge API calls."""

from __future__ import annotations

import random
import time
from typing import Callable

from lab.providers.base import ChatProvider, CompletionResult

DEFAULT_RETRIES = 5
DEFAULT_BACKOFF_S = 2.0
DEFAULT_BACKOFF_CAP_S = 60.0


def backoff_delay(attempt: int, *, base_s: float = DEFAULT_BACKOFF_S, cap_s: float = DEFAULT_BACKOFF_CAP_S) -> float:
    """Exponential delay for the *next* retry after ``attempt`` (0-based) failed."""
    delay = min(cap_s, base_s * (2**attempt))
    return delay * (0.5 + random.random())


def sleep_backoff(attempt: int, *, base_s: float = DEFAULT_BACKOFF_S, cap_s: float = DEFAULT_BACKOFF_CAP_S) -> float:
    delay = backoff_delay(attempt, base_s=base_s, cap_s=cap_s)
    time.sleep(delay)
    return delay


def complete_with_retries(
    provider: ChatProvider,
    *,
    system: str,
    user: str,
    model: str | None = None,
    temperature: float | None = None,
    top_p: float | None = None,
    max_output_tokens: int | None = None,
    timeout: float | None = None,
    retries: int = DEFAULT_RETRIES,
    backoff_s: float = DEFAULT_BACKOFF_S,
    backoff_cap_s: float = DEFAULT_BACKOFF_CAP_S,
    should_retry: Callable[[CompletionResult], bool] | None = None,
) -> CompletionResult:
    """Call ``provider.complete`` with exponential backoff on retryable failures."""
    attempts = max(1, int(retries))
    last = CompletionResult(text="", latency_ms=0, error="no attempt")
    for attempt in range(attempts):
        last = provider.complete(
            system=system,
            user=user,
            model=model,
            temperature=temperature,
            top_p=top_p,
            max_output_tokens=max_output_tokens,
            timeout=timeout,
        )
        retryable = should_retry(last) if should_retry is not None else bool(last.error)
        if not retryable:
            last.extra = {**(last.extra or {}), "attempts": attempt + 1}
            return last
        if attempt + 1 < attempts:
            delay = sleep_backoff(attempt, base_s=backoff_s, cap_s=backoff_cap_s)
            last.extra = {**(last.extra or {}), "attempts": attempt + 1, "next_backoff_s": round(delay, 2)}
    last.extra = {**(last.extra or {}), "attempts": attempts}
    return last
