from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lab.config import REPO_ROOT, Settings
from lab.context import ContextStore
from lab.judge import judge_completion, make_judge_provider
from lab.metrics import PASS_THRESHOLD, CaseScores, aggregate, as_payload, score_completion
from lab.providers.base import ChatProvider


def _chunks_path() -> Path:
    return REPO_ROOT / "data" / "chunk_data" / "chunks.json"


def _runs_dir() -> Path:
    return REPO_ROOT / "data" / "runs"


def load_chunk_texts(path: Path | None = None) -> dict[str, str]:
    with (path or _chunks_path()).open(encoding="utf-8") as handle:
        rows = json.load(handle)
    return {str(row["chunk_id"]): str(row.get("text") or "") for row in rows}


def latest_run(runs_dir: Path | None = None) -> Path:
    folder = runs_dir or _runs_dir()
    files = sorted(folder.glob("phase1_*.json"), key=lambda item: item.stat().st_mtime)
    files = [path for path in files if not path.name.endswith(".eval.json")]
    if not files:
        raise SystemExit(f"Nenhuma run em {folder}")
    return files[-1]


def default_store() -> ContextStore:
    data_dir = REPO_ROOT / "data"
    return ContextStore(
        chunks_path=data_dir / "chunk_data" / "chunks.json",
        retrieval_path=data_dir / "chunk_data" / "retrieval.json",
        gold_path=data_dir / "geoatributo_base2_gold_questions_p4_merged.json",
        max_chunks=6,
        similarity_floor=0.45,
        context_char_cap=9000,
    )


def resolve_context_text(
    case: dict[str, Any],
    chunk_texts: dict[str, str],
    *,
    store: ContextStore | None = None,
) -> tuple[str, str]:
    ids = [str(chunk_id) for chunk_id in case.get("chunk_ids") or []]
    found = [chunk_texts[chunk_id] for chunk_id in ids if chunk_texts.get(chunk_id)]
    if found:
        return "\n".join(found), "run"
    if case.get("empty_context") or not ids:
        return "", "empty"
    if store is None:
        return "", "missing"
    case_id = str(case.get("case_id") or "")
    if not case_id or case_id == "refuse-empty":
        return "", "empty"
    try:
        built = store.build(case_id, empty_context=False)
    except KeyError:
        return "", "missing"
    return "\n".join(chunk.text for chunk in built.chunks), "store_fallback"


def evaluate_payload(
    payload: dict[str, Any],
    *,
    chunk_texts: dict[str, str],
    store: ContextStore | None = None,
    judge: ChatProvider | None = None,
    judge_model: str | None = None,
    judge_provider_name: str | None = None,
) -> dict[str, Any]:
    by_provider: dict[str, list] = defaultdict(list)
    by_judge: dict[str, list] = defaultdict(list)
    cases_out: list[dict[str, Any]] = []
    contestants = payload.get("models") or {}
    if judge and judge_model and judge_model in contestants.values():
        raise SystemExit(
            f"O modelo juiz ({judge_model}) coincide com um dos modelos em teste. "
            "Define JUDGE_MODEL diferente de GEMINI_MODEL e XAI_MODEL."
        )
    for case in payload.get("cases") or []:
        context_text, context_source = resolve_context_text(case, chunk_texts, store=store)
        provider_scores = []
        expected = str(case.get("expected_behavior") or "answer")
        for row in case.get("providers") or []:
            scores = score_completion(
                expected_behavior=expected,
                reference_answer=case.get("reference_answer"),
                visible_text=str(row.get("visible_text") or ""),
                is_refusal=bool(row.get("is_refusal")),
                context_text=context_text,
                error=row.get("error"),
            )
            name = str(row.get("provider") or "unknown")
            by_provider[name].append(scores)
            item = {"provider": row.get("provider"), "lexical": as_payload(scores), **as_payload(scores)}
            if judge and judge_model and not row.get("error"):
                judged = judge_completion(
                    judge,
                    model=judge_model,
                    expected_behavior=expected,
                    question=str(case.get("question") or ""),
                    reference_answer=case.get("reference_answer"),
                    context_text=context_text,
                    visible_text=str(row.get("visible_text") or ""),
                    error=row.get("error"),
                )
                item["judge"] = judged
                if not judged.get("error"):
                    by_judge[name].append(
                        CaseScores(
                            correctness=float(judged["correctness"]),
                            grounded_rate=float(judged["grounded_rate"]),
                            completeness=float(judged["completeness"]),
                            passed=bool(judged["passed"]),
                            notes=str(judged.get("rationale") or ""),
                        )
                    )
            elif judge and row.get("error"):
                item["judge"] = {"error": "skipped: erro na chamada do modelo em teste", "passed": False}
            provider_scores.append(item)
        cases_out.append(
            {
                "case_id": case.get("case_id"),
                "expected_behavior": case.get("expected_behavior"),
                "context_source": context_source,
                "providers": provider_scores,
            }
        )
    summary = {name: aggregate(items) for name, items in by_provider.items()}
    judge_method = "determinístico (sobreposição de números e tokens). Sempre calculado."
    if judge:
        judge_method += (
            f" Juiz LLM opcional: {judge_provider_name or judge.name} / {judge_model} "
            "(JSON com as mesmas quatro notas). Não deve ser o mesmo modelo que Gemini ou Grok em teste."
        )
    report: dict[str, Any] = {
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "method": {
            "correctness": "lexical: 0.6 × recall dos números da referência + 0.4 × completeness. Juiz: nota 0–1 do terceiro modelo.",
            "completeness": "lexical: fração das unidades da gold cobertas. Juiz: cobertura dos pontos da referência.",
            "grounded_rate": "lexical: fração das frases da resposta suportadas pelo contexto. Juiz: afirmações inventadas vs contexto.",
            "pass_rate": f"% de casos com correctness ≥ {PASS_THRESHOLD} (summary = lexical; summary_judge = juiz se --judge)",
            "judge": judge_method,
        },
        "pass_threshold": PASS_THRESHOLD,
        "models": payload.get("models"),
        "summary": summary,
        "cases": cases_out,
    }
    if judge:
        report["judge"] = {"provider": judge_provider_name or judge.name, "model": judge_model}
        report["summary_judge"] = {name: aggregate(items) for name, items in by_judge.items()}
    return report


def evaluate_path(
    run_path: Path,
    *,
    chunks_path: Path | None = None,
    settings: Settings | None = None,
    use_judge: bool = False,
) -> Path:
    payload = json.loads(run_path.read_text(encoding="utf-8"))
    judge = None
    judge_model = None
    judge_provider_name = None
    if use_judge:
        if settings is None:
            from lab.config import load_settings

            settings = load_settings(require_keys=True)
        judge = make_judge_provider(settings)
        judge_model = settings.judge_model
        judge_provider_name = settings.judge_provider
    report = evaluate_payload(
        payload,
        chunk_texts=load_chunk_texts(chunks_path),
        store=default_store(),
        judge=judge,
        judge_model=judge_model,
        judge_provider_name=judge_provider_name,
    )
    out_path = run_path.with_name(run_path.stem + ".eval.json")
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path


def _format_provider_block(title: str, summary: dict[str, Any]) -> list[str]:
    lines = [title]
    for provider, stats in summary.items():
        lines.append(
            f"{provider}: correctness={stats['correctness']:.3f}  "
            f"grounded_rate={stats['grounded_rate']:.3f}  "
            f"completeness={stats['completeness']:.3f}  "
            f"pass_rate={stats['pass_rate']:.3f}  n={stats['n']}"
        )
    return lines


def format_summary(report: dict[str, Any]) -> str:
    lines = [f"limiar pass_rate: correctness ≥ {report.get('pass_threshold')}"]
    lines.extend(_format_provider_block("lexical:", report.get("summary") or {}))
    if report.get("summary_judge"):
        judge_meta = report.get("judge") or {}
        lines.extend(
            _format_provider_block(
                f"juiz ({judge_meta.get('provider')}/{judge_meta.get('model')}):",
                report["summary_judge"],
            )
        )
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Avaliar uma run da Fase 1 (métricas determinísticas e juiz opcional).")
    parser.add_argument("run", nargs="?", help="Ficheiro data/runs/phase1_*.json. Sem argumento, usa a mais recente.")
    parser.add_argument("--judge", action="store_true", help="Pontuar também com um terceiro modelo (JUDGE_PROVIDER / JUDGE_MODEL).")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    run_path = Path(args.run) if args.run else latest_run()
    out_path = evaluate_path(run_path, use_judge=args.judge)
    report = json.loads(out_path.read_text(encoding="utf-8"))
    print(f"Run: {run_path}")
    print(f"Eval: {out_path}")
    print(format_summary(report))


if __name__ == "__main__":
    main()
