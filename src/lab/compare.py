from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lab.chat import sources_from_chunks
from lab.config import REPO_ROOT
from lab.context import ContextStore
from lab.providers.base import ChatProvider
from lab.runner import run_case

VERDICTS = ("xai_better", "gemini_better", "tie", "both_weak")
EVAL_PATH = REPO_ROOT / "data" / "evaluations.json"
OVERRIDE_PATH = REPO_ROOT / "data" / "runs" / "compare_overrides.json"


def _read_json(path: Path, default: Any) -> Any:
    if not path.is_file():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_evaluations(path: Path | None = None) -> dict[str, Any]:
    payload = _read_json(path or EVAL_PATH, {})
    return payload if isinstance(payload, dict) else {}


def save_evaluation(
    case_id: str,
    *,
    verdict: str,
    notes: str = "",
    path: Path | None = None,
) -> dict[str, Any]:
    if verdict not in VERDICTS:
        raise ValueError(f"Avaliação inválida: {verdict}")
    store = load_evaluations(path)
    row = {
        "case_id": case_id,
        "verdict": verdict,
        "notes": notes,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    store[case_id] = row
    _write_json(path or EVAL_PATH, store)
    return row


def evaluations_csv(path: Path | None = None) -> str:
    rows = load_evaluations(path)
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=["case_id", "verdict", "notes", "updated_at"])
    writer.writeheader()
    for case_id in sorted(rows):
        writer.writerow(rows[case_id])
    return buffer.getvalue()


def load_overrides(path: Path | None = None) -> dict[str, Any]:
    payload = _read_json(path or OVERRIDE_PATH, {})
    return payload if isinstance(payload, dict) else {}


def save_override(case: dict[str, Any], *, path: Path | None = None) -> None:
    store = load_overrides(path)
    store[str(case["case_id"])] = case
    _write_json(path or OVERRIDE_PATH, store)


def _is_generation_file(path: Path) -> bool:
    name = path.name.lower()
    if not name.endswith(".json") or name.endswith(".eval.json"):
        return False
    skip = ("dryrun", "compare_overrides", "context_sweep", "report.json", "metrics.json")
    return not any(token in name for token in skip)


def _generation_cases(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Ignore metrics packs whose ``cases`` are id strings, not generation objects."""
    records: list[dict[str, Any]] = []
    for case in payload.get("cases") or []:
        if isinstance(case, dict) and case.get("case_id") is not None:
            records.append(case)
    return records


def latest_run_payload(runs_dir: Path) -> dict[str, Any] | None:
    """Use the run JSON with the most cases (nested sweep folders included)."""
    if not runs_dir.is_dir():
        return None
    best: dict[str, Any] | None = None
    best_key = (-1, 0.0)
    for path in runs_dir.rglob("*.json"):
        if not _is_generation_file(path):
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(payload, dict):
            continue
        cases = _generation_cases(payload)
        if not cases:
            continue
        key = (len(cases), path.stat().st_mtime)
        if key > best_key:
            best_key = key
            best = payload
    return best


def generations_by_id(runs_dir: Path, override_path: Path | None = None) -> tuple[dict[str, Any], dict[str, str]]:
    found: dict[str, Any] = {}
    models: dict[str, str] = {}
    payload = latest_run_payload(runs_dir)
    if payload:
        models = dict(payload.get("models") or {})
        for case in _generation_cases(payload):
            found[str(case.get("case_id"))] = case
    found.update(load_overrides(override_path))
    return found, models


def _usage(row: dict[str, Any]) -> dict[str, Any]:
    usage = row.get("usage") if isinstance(row.get("usage"), dict) else {}
    return {
        "prompt_tokens": usage.get("prompt_tokens"),
        "completion_tokens": usage.get("completion_tokens"),
        "total_tokens": usage.get("total_tokens"),
    }


def _provider_row(case: dict[str, Any] | None, name: str) -> dict[str, Any] | None:
    if not case:
        return None
    for row in case.get("providers") or []:
        if str(row.get("provider")) != name:
            continue
        visible = row.get("visible_text")
        return {
            "provider": name,
            "visible_text": None if visible is None else str(visible),
            "latency_ms": row.get("latency_ms"),
            "usage": _usage(row),
            "is_refusal": row.get("is_refusal"),
            "scratchpad_leaked": row.get("scratchpad_leaked"),
            "error": row.get("error"),
        }
    return None


def list_questions(
    store: ContextStore,
    *,
    generations: dict[str, Any],
    evaluations: dict[str, Any],
) -> list[dict[str, Any]]:
    items = []
    for case_id in store.gold_ids():
        gold = store.gold_case(case_id) or {}
        case = generations.get(case_id)
        items.append(
            {
                "id": case_id,
                "text": str(gold.get("question") or ""),
                "category": gold.get("question_type"),
                "expected_behavior": gold.get("expected_behavior"),
                "has_results": bool(case and case.get("providers")),
                "evaluated": case_id in evaluations,
                "verdict": (evaluations.get(case_id) or {}).get("verdict"),
            }
        )
    return items


def result_for(
    store: ContextStore,
    case_id: str,
    *,
    generations: dict[str, Any],
    evaluations: dict[str, Any],
    models: dict[str, str],
) -> dict[str, Any]:
    gold = store.gold_case(case_id)
    if gold is None:
        raise KeyError(case_id)
    chunks = store.select_chunks(case_id)
    case = generations.get(case_id) or {}
    chunk_ids = [str(item) for item in (case.get("chunk_ids") or [chunk.chunk_id for chunk in chunks])]
    chunk_count = case.get("chunk_count")
    if chunk_count is None:
        chunk_count = len(chunk_ids)
    empty_context = case.get("empty_context")
    return {
        "case_id": case_id,
        "question": str(case.get("question") or gold.get("question") or ""),
        "chunk_ids": chunk_ids,
        "chunk_count": chunk_count,
        "empty_context": empty_context,
        "expected_behavior": case.get("expected_behavior", gold.get("expected_behavior")),
        "reference_answer": case.get("reference_answer", gold.get("reference_answer")),
        "models": {"xai": models.get("xai"), "gemini": models.get("gemini")},
        "sources": sources_from_chunks(chunks),
        "xai": _provider_row(case, "xai"),
        "gemini": _provider_row(case, "gemini"),
        "evaluation": evaluations.get(case_id),
    }


def generate_pair(
    *,
    store: ContextStore,
    providers: list[ChatProvider],
    case_id: str,
) -> dict[str, Any]:
    if store.gold_case(case_id) is None:
        raise KeyError(case_id)
    return run_case(store=store, providers=providers, case_id=case_id, empty_context=False)
