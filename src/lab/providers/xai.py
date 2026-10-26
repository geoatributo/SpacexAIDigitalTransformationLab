from __future__ import annotations

import time
from typing import Any

from openai import OpenAI

from lab.config import Settings
from lab.providers.base import CompletionResult


class XaiProvider:
    name = "xai"

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = OpenAI(api_key=settings.xai_api_key, base_url=settings.xai_base_url)
        self.responses_api_supported: bool | None = None

    def probe_responses_api(self) -> bool:
        if self.responses_api_supported is not None:
            return self.responses_api_supported
        try:
            self._client.responses.create(
                model=self._settings.xai_model,
                input="ping",
                max_output_tokens=16,
            )
            self.responses_api_supported = True
        except Exception:
            self.responses_api_supported = False
        return self.responses_api_supported

    def complete(self, *, system: str, user: str) -> CompletionResult:
        started = time.perf_counter()
        try:
            kwargs: dict[str, Any] = {
                "model": self._settings.xai_model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "temperature": self._settings.temperature,
                "top_p": self._settings.top_p,
            }
            if self._settings.max_output_tokens is not None:
                kwargs["max_tokens"] = self._settings.max_output_tokens
            response = self._client.chat.completions.create(**kwargs)
            latency_ms = int((time.perf_counter() - started) * 1000)
            choice = response.choices[0].message.content if response.choices else ""
            return CompletionResult(
                text=choice or "",
                latency_ms=latency_ms,
                usage=_usage_from_openai(response.usage),
                extra={"responses_api_supported": self.responses_api_supported},
            )
        except Exception as exc:
            latency_ms = int((time.perf_counter() - started) * 1000)
            return CompletionResult(
                text="",
                latency_ms=latency_ms,
                error=type(exc).__name__,
                extra={"responses_api_supported": self.responses_api_supported},
            )


def _usage_from_openai(usage: Any) -> dict[str, Any]:
    if usage is None:
        return {}
    return {
        "prompt_tokens": getattr(usage, "prompt_tokens", None),
        "completion_tokens": getattr(usage, "completion_tokens", None),
        "total_tokens": getattr(usage, "total_tokens", None),
    }
