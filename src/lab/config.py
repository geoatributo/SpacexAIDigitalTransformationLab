from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[2]
REFUSAL_SENTENCE = "O manual não especifica a resposta para essa questão."
PLACEHOLDER_KEYS = frozenset({"", "abcd", "changeme", "your-key", "xxx"})


KEY_FILE = REPO_ROOT / "CHAVE-API.md"


def _read_key_file(path: Path) -> str:
    """Devolve a chave do primeiro bloco de código de CHAVE-API.md (decisão em DECISAO-CHAVE-API.md)."""
    if not path.is_file():
        return ""
    inside = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("```"):
            if inside:
                break
            inside = True
            continue
        if inside and line.strip():
            return line.strip()
    return ""


def _load_env() -> None:
    # Ordem: variável de ambiente, depois .env, depois CHAVE-API.md (só para a chave xAI).
    load_dotenv(REPO_ROOT / ".env")
    if (os.getenv("XAI_API_KEY") or "").strip().lower() in PLACEHOLDER_KEYS:
        key = _read_key_file(KEY_FILE)
        if key:
            os.environ["XAI_API_KEY"] = key


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
            "A chave xAI está em CHAVE-API.md (decisão em DECISAO-CHAVE-API.md); a do Gemini pede-se e põe-se no .env. Não a partilhar fora do repositório (chat, email)."
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
        gold_path=data_dir / "geoatributo_base2_gold_questions_p4_merged.json",
        retrieval_path=data_dir / "chunk_data" / "retrieval.json",
        chunks_path=data_dir / "chunk_data" / "chunks.json",
    )
