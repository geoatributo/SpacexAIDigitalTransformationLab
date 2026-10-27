from __future__ import annotations

import json
from pathlib import Path
from typing import Any

METRIC_LABELS = {
    "correctness": "Correção",
    "grounded_rate": "Fundamentação",
    "completeness": "Completude",
    "pass_rate": "Taxa de aprovação",
}


def latest_eval_path(runs_dir: Path) -> Path | None:
    files = sorted(runs_dir.glob("phase1_*.eval.json"), key=lambda item: item.stat().st_mtime)
    return files[-1] if files else None


def latest_run_path(runs_dir: Path) -> Path | None:
    files = sorted(
        [
            path
            for path in runs_dir.glob("phase1_*.json")
            if not path.name.endswith(".eval.json") and "dryrun" not in path.name
        ],
        key=lambda item: item.stat().st_mtime,
    )
    return files[-1] if files else None


def _delta(left: float | None, right: float | None) -> float | None:
    if left is None or right is None:
        return None
    return round(right - left, 4)


def metric_cards(runs_dir: Path) -> dict[str, Any]:
    eval_path = latest_eval_path(runs_dir)
    run_path = latest_run_path(runs_dir)
    run_payload = json.loads(run_path.read_text(encoding="utf-8")) if run_path else {}
    eval_payload = json.loads(eval_path.read_text(encoding="utf-8")) if eval_path else {}
    config = run_payload.get("context_policy") or eval_payload.get("context_policy") or {}
    models = run_payload.get("models") or eval_payload.get("models") or {}
    summary = eval_payload.get("summary_cross") or eval_payload.get("summary_judge") or eval_payload.get("summary") or {}
    method = eval_payload.get("method") or {}
    source = "summary_cross" if "summary_cross" in eval_payload else (
        "summary_judge" if "summary_judge" in eval_payload else "summary"
    )
    cards = []
    for key, label in METRIC_LABELS.items():
        gemini = (summary.get("gemini") or {}).get(key)
        xai = (summary.get("xai") or {}).get(key)
        n_gemini = (summary.get("gemini") or {}).get("n")
        n_xai = (summary.get("xai") or {}).get("n")
        cards.append(
            {
                "id": key,
                "label": label,
                "n": n_gemini if n_gemini == n_xai else {"gemini": n_gemini, "xai": n_xai},
                "gemini": gemini,
                "xai": xai,
                "delta": _delta(gemini, xai),
                "config": config,
                "source_file": eval_path.name if eval_path else None,
                "run_file": run_path.name if run_path else None,
                "method": method.get(key) or method.get("judge"),
                "summary_kind": source,
                "color_policy": "provisória — comparação relativa, sem limiar acordado",
            }
        )
    cases = eval_payload.get("cases") or run_payload.get("cases") or []
    n_answer = sum(1 for case in cases if str(case.get("expected_behavior") or "answer") != "refuse")
    n_refuse = sum(1 for case in cases if str(case.get("expected_behavior") or "") == "refuse")
    return {
        "models": models,
        "config": config,
        "source_file": eval_path.name if eval_path else None,
        "run_file": run_path.name if run_path else None,
        "pass_threshold": eval_payload.get("pass_threshold"),
        "cards": cards,
        "n_cases": len(cases),
        "n_answer": n_answer,
        "n_refuse": n_refuse,
        "note": (
            "Só se comparam as duas execuções desta run, na mesma configuração de contexto. "
            "As cores dos cartões marcam o valor maior/menor entre sistemas, não um juízo de qualidade "
            "(R2: sem limiar acordado)."
        ),
        "challenges": [
            {
                "id": "D1",
                "label": "Recusas",
                "text": f"{n_refuse} caso(s) com recusa esperada e {n_answer} com resposta esperada nesta run. Sequências de seguimento continuam fora do código.",
            },
            {
                "id": "D4",
                "label": "Tamanho da amostra",
                "text": f"n visível em cada cartão. Esta run tem {len(cases)} caso(s); diferenças pequenas podem dever-se a perguntas fáceis.",
            },
            {
                "id": "D6",
                "label": "Configuração",
                "text": "Os dois sistemas usam a mesma política de contexto; o detalhe está no cabeçalho e em cada cartão.",
            },
            {
                "id": "D7",
                "label": "Modelos",
                "text": (
                    f"Gemini {models.get('gemini') or '—'} vs xAI {models.get('xai') or '—'}. "
                    "A diferença mistura fornecedor e gama se um for lite e o outro de topo."
                ),
            },
        ],
    }
