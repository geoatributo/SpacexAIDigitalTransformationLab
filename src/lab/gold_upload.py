from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

def _is_metrics_pack(payload: dict[str, Any]) -> bool:
    if payload.get("configs") is not None and payload.get("disagreement") is not None:
        return True
    cases = payload.get("cases")
    if isinstance(cases, list) and cases and all(isinstance(item, str) for item in cases):
        return bool(payload.get("configs") or payload.get("scoring") or payload.get("disagreement") is not None)
    return False


def _rows_from_payload(payload: Any) -> list[Any]:
    if isinstance(payload, list):
        return payload
    if not isinstance(payload, dict):
        raise ValueError("JSON inválido: esperado um objeto ou uma lista de perguntas.")
    if _is_metrics_pack(payload):
        raise ValueError("Este JSON é um relatório de métricas. Use «Carregar relatório de métricas».")
    if isinstance(payload.get("question"), str) and (payload.get("id") or payload.get("case_id")):
        return [payload]
    rows = payload.get("cases") or payload.get("questions") or payload.get("gold")
    if not isinstance(rows, list):
        raise ValueError("O ficheiro não tem uma lista de perguntas (cases, questions ou gold).")
    return rows


def parse_gold_payload(payload: Any) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    """Return (gold_by_id, generation_cases_by_id). Does not call models."""
    gold: dict[str, dict[str, Any]] = {}
    generations: dict[str, Any] = {}
    for index, raw in enumerate(_rows_from_payload(payload), start=1):
        if isinstance(raw, str):
            question = raw.strip()
            if not question:
                continue
            case_id = f"upload-{index:03d}"
            gold[case_id] = {
                "id": case_id,
                "question": question,
                "question_type": None,
                "expected_behavior": "answer",
            }
            continue
        if not isinstance(raw, dict):
            continue
        question = str(raw.get("question") or raw.get("text") or "").strip()
        if not question:
            continue
        case_id = str(raw.get("id") or raw.get("case_id") or f"upload-{index:03d}")
        row = dict(raw)
        row["id"] = case_id
        row["question"] = question
        gold[case_id] = row
        if raw.get("providers"):
            generations[case_id] = raw
    if not gold:
        raise ValueError("O ficheiro não contém perguntas (campo question).")
    return gold, generations


def save_uploaded_gold(dest_dir: Path, gold: dict[str, dict[str, Any]]) -> dict[str, Any]:
    dest_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = dest_dir / f"gold_{stamp}.json"
    body = {"cases": list(gold.values())}
    path.write_text(json.dumps(body, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"id": path.stem, "n": len(gold), "file": path.name}


def questions_dir(data_dir: Path) -> Path:
    return data_dir / "uploads" / "questions"
