from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lab.compare import load_evaluations
from lab.config import REPO_ROOT

METRICS_NOTES_PATH = REPO_ROOT / "data" / "metrics_notes.json"

VERDICT_LABELS = {
    "xai_better": "xAI melhor",
    "gemini_better": "Gemini melhor",
    "tie": "Empate",
    "both_weak": "Ambas fracas",
}


def _read_json(path: Path, default: Any) -> Any:
    if not path.is_file():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_metrics_notes(path: Path | None = None) -> dict[str, Any]:
    payload = _read_json(path or METRICS_NOTES_PATH, {})
    return payload if isinstance(payload, dict) else {}


def get_metrics_note(run_id: str, *, path: Path | None = None) -> dict[str, Any] | None:
    row = load_metrics_notes(path).get(run_id)
    return dict(row) if isinstance(row, dict) else None


def save_metrics_note(run_id: str, notes: str, *, path: Path | None = None) -> dict[str, Any]:
    run_id = run_id.strip()
    if not run_id:
        raise ValueError("Corrida em falta.")
    store = load_metrics_notes(path)
    row = {
        "run_id": run_id,
        "notes": notes,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    store[run_id] = row
    _write_json(path or METRICS_NOTES_PATH, store)
    return row


def format_evaluation_report(
    *,
    compare_path: Path | None = None,
    metrics_path: Path | None = None,
    blind_rows: list[dict[str, Any]] | None = None,
) -> str:
    """Plain-text report of human notes from Compare, Metrics and Blind eval."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines = [
        "Relatório de avaliações humanas — Goldilocks RAG",
        f"Gerado em: {now}",
        "",
        "=" * 60,
        "1. Comparar (por pergunta)",
        "=" * 60,
        "",
    ]
    compare = load_evaluations(compare_path)
    if not compare:
        lines.append("(sem notas nesta secção)")
        lines.append("")
    else:
        for case_id in sorted(compare):
            row = compare[case_id] or {}
            verdict = row.get("verdict")
            label = VERDICT_LABELS.get(str(verdict), str(verdict) if verdict else "sem veredicto")
            notes = str(row.get("notes") or "").strip() or "(sem texto)"
            lines.append(f"[{case_id}] {label}")
            if row.get("updated_at"):
                lines.append(f"Atualizado: {row['updated_at']}")
            lines.append(notes)
            lines.append("")

    lines.extend(
        [
            "=" * 60,
            "2. Métricas (por corrida)",
            "=" * 60,
            "",
        ]
    )
    metrics = load_metrics_notes(metrics_path)
    if not metrics:
        lines.append("(sem notas nesta secção)")
        lines.append("")
    else:
        for run_id in sorted(metrics):
            row = metrics[run_id] or {}
            notes = str(row.get("notes") or "").strip() or "(sem texto)"
            lines.append(f"[{run_id}]")
            if row.get("updated_at"):
                lines.append(f"Atualizado: {row['updated_at']}")
            lines.append(notes)
            lines.append("")

    lines.extend(
        [
            "=" * 60,
            "3. Avaliar às cegas (0–10)",
            "=" * 60,
            "",
        ]
    )
    blind = blind_rows or []
    if not blind:
        lines.append("(sem notas nesta secção)")
        lines.append("")
    else:
        for row in sorted(blind, key=lambda item: (str(item.get("case_id") or ""), str(item.get("created_at") or ""))):
            case_id = row.get("case_id") or "?"
            rater = row.get("rater_id") or "?"
            score_a = row.get("score_a")
            score_b = row.get("score_b")
            notes = str(row.get("notes") or "").strip() or "(sem texto)"
            lines.append(f"[{case_id}] avaliador={rater} · A={score_a} · B={score_b}")
            if row.get("created_at"):
                lines.append(f"Criado: {row['created_at']}")
            lines.append(notes)
            lines.append("")

    lines.append("Fim do relatório.")
    return "\n".join(lines) + "\n"
