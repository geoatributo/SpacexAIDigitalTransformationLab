from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[2]
REFUSAL_SENTENCE = "O manual não especifica a resposta para essa questão."
PLACEHOLDER_KEYS = frozenset({"", "abcd", "changeme", "your-key", "xxx"})


def _load_env() -> None:
    load_dotenv(REPO_ROOT / ".env")


def _optional_int(name: str) -> int | None:
    raw = (os.getenv(name) or "").strip()
    if not raw:
        return None
    return int(raw)


def _require_key(name: str) -> str:
    value = (os.getenv(name) or "").strip()
    if value.lower() in PLACEHOLDER_KEYS or len(value) < 8:
        raise SystemExit(
            f"{name} está em falta ou é um placeholder. "
            "Pede a chave à Liliana e coloca-a no .env (nunca no repositório nem no chat)."
        )
    return value


@dataclass(frozen=True)
class Settings:
    gemini_api_key: str
    xai_api_key: str
    gemini_model: str
    xai_model: str
    xai_base_url: str
    max_output_tokens: int | None
    temperature: float
    top_p: float
    max_chunks: int
    similarity_floor: float
    context_char_cap: int
    data_dir: Path
    runs_dir: Path
    gold_path: Path
    retrieval_path: Path
    chunks_path: Path


def load_settings() -> Settings:
    _load_env()
    data_dir = REPO_ROOT / "data"
    return Settings(
        gemini_api_key=_require_key("GEMINI_API_KEY"),
        xai_api_key=_require_key("XAI_API_KEY"),
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest").strip(),
        xai_model=os.getenv("XAI_MODEL", "grok-latest").strip(),
        xai_base_url=os.getenv("XAI_BASE_URL", "https://api.x.ai/v1").rstrip("/"),
        max_output_tokens=_optional_int("MAX_OUTPUT_TOKENS"),
        temperature=0.1,
        top_p=0.9,
        max_chunks=6,
        similarity_floor=0.45,
        context_char_cap=9000,
        data_dir=data_dir,
        runs_dir=data_dir / "runs",
        gold_path=data_dir / "geoatributo_base2_gold_questions.json",
        retrieval_path=data_dir / "chunk_data" / "retrieval.json",
        chunks_path=data_dir / "chunk_data" / "chunks.json",
    )
