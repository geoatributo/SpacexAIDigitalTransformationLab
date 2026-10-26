from __future__ import annotations

import re
from dataclasses import dataclass

from lab.config import Settings
from lab.providers.base import ChatProvider

CROSS_PEER = {"gemini": "xai", "xai": "gemini"}

_IDENTITY_LEAK = re.compile(
    r"\b(gemini|grok|xai|openai|flash-lite|flash lite)\b",
    re.IGNORECASE,
)


def identity_leaks(text: str) -> list[str]:
    return sorted({match.group(0).lower() for match in _IDENTITY_LEAK.finditer(text or "")})


@dataclass(frozen=True)
class JudgeAssignment:
    subject: str
    judge_name: str
    judge: ChatProvider
    model: str


class CrossJudgePanel:
    """Gemini avalia Grok e Grok avalia Gemini. O prompt do RAG judge não nomeia o autor."""

    def __init__(self, *, judges: dict[str, tuple[ChatProvider, str]]) -> None:
        self._judges = judges

    def assignment_for(self, subject: str) -> JudgeAssignment | None:
        peer = CROSS_PEER.get(subject)
        if peer is None or peer not in self._judges:
            return None
        judge, model = self._judges[peer]
        return JudgeAssignment(subject=subject, judge_name=peer, judge=judge, model=model)


def make_judge_provider(settings: Settings) -> ChatProvider:
    name = (settings.judge_provider or "gemini").strip().lower()
    if name == "xai":
        from lab.providers.xai import XaiProvider

        return XaiProvider(settings)
    if name != "gemini":
        raise SystemExit(f"JUDGE_PROVIDER inválido: {settings.judge_provider!r} (usa gemini ou xai)")
    from lab.providers.gemini import GeminiProvider

    return GeminiProvider(settings)


def make_cross_panel(settings: Settings) -> CrossJudgePanel:
    from lab.providers.gemini import GeminiProvider
    from lab.providers.xai import XaiProvider

    return CrossJudgePanel(
        judges={
            "gemini": (GeminiProvider(settings), settings.gemini_model),
            "xai": (XaiProvider(settings), settings.xai_model),
        }
    )
