from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lab.config import REPO_ROOT, Settings
from lab.context import ContextPolicy, ContextStore
from lab.judge import CrossJudgePanel, make_cross_panel, make_judge_provider
from lab.metrics import PASS_THRESHOLD, aggregate, as_payload, score_completion
from lab.rag_judge import aggregate_llm_cases, score_generated_answer
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
    return ContextStore.from_files(
        chunks_path=data_dir / "chunk_data" / "chunks.json",
        retrieval_path=data_dir / "chunk_data" / "retrieval.json",
        gold_path=data_dir / "geoatributo_base2_gold_questions_p4_merged.json",
        policy=ContextPolicy(mode="top_n", top_n=6, max_chars=9000),
    )


def resolve_context_chunks(
    case: dict[str, Any],
    chunk_texts: dict[str, str],
    *,
    store: ContextStore | None = None,
) -> tuple[list[str], str]:
    ids = [str(chunk_id) for chunk_id in case.get("chunk_ids") or []]
    found = [chunk_texts[chunk_id] for chunk_id in ids if chunk_texts.get(chunk_id)]
    if found:
        return found, "run"
    if case.get("empty_context") or not ids:
        return [], "empty"
    if store is None:
        return [], "missing"
    case_id = str(case.get("case_id") or "")
    if not case_id or case_id == "refuse-empty":
        return [], "empty"
    try:
        built = store.build(case_id, empty_context=False)
    except KeyError:
        return [], "missing"
    return [chunk.text for chunk in built.chunks], "store_fallback"


def resolve_context_text(
    case: dict[str, Any],
    chunk_texts: dict[str, str],
    *,
    store: ContextStore | None = None,
) -> tuple[str, str]:
    chunks, source = resolve_context_chunks(case, chunk_texts, store=store)
    return "\n".join(chunks), source


def evaluate_payload(
    payload: dict[str, Any],
    *,
    chunk_texts: dict[str, str],
    store: ContextStore | None = None,
    judge: ChatProvider | None = None,
    judge_model: str | None = None,
    judge_provider_name: str | None = None,
    cross_panel: CrossJudgePanel | None = None,
    pass_threshold: float = PASS_THRESHOLD,
) -> dict[str, Any]:
    by_provider: dict[str, list] = defaultdict(list)
    by_judge: dict[str, list] = defaultdict(list)
    by_cross: dict[str, list] = defaultdict(list)
    cases_out: list[dict[str, Any]] = []
    contestants = payload.get("models") or {}
    if judge and judge_model and judge_model in contestants.values():
        raise SystemExit(
            f"O modelo juiz ({judge_model}) coincide com um dos modelos em teste. "
            "Usa --cross-judge (Gemini↔Grok às cegas) ou um JUDGE_MODEL diferente."
        )
    for case in payload.get("cases") or []:
        context_chunks, context_source = resolve_context_chunks(case, chunk_texts, store=store)
        context_text = "\n".join(context_chunks)
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
            score_kwargs = {
                "question": str(case.get("question") or ""),
                "reference": case.get("reference_answer"),
                "generated": str(row.get("visible_text") or ""),
                "context_chunks": context_chunks,
                "expected_behavior": expected,
                "is_refusal": bool(row.get("is_refusal")),
                "error": row.get("error"),
                "pass_threshold": pass_threshold,
            }
            if judge and judge_model:
                judged = score_generated_answer(judge, model=judge_model, **score_kwargs)
                item["judge"] = judged
                by_judge[name].append(judged)
            if cross_panel:
                assignment = cross_panel.assignment_for(name)
                if assignment is None:
                    item["cross_judge"] = {"error": f"sem par cruzado para {name}", "passed": False, "bucket": "no_peer"}
                else:
                    judged = score_generated_answer(assignment.judge, model=assignment.model, **score_kwargs)
                    judged["blind"] = True
                    judged["scored_by"] = assignment.judge_name
                    judged["scored_by_model"] = assignment.model
                    item["cross_judge"] = judged
                    by_cross[name].append(judged)
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
    judge_method = (
        "LLM judge próprio (não ragas): uma chamada por métrica, nota 0–100, ask_score → 0–1. "
        f"temperature=0.2 top_p=0.95 max_output_tokens=8192 timeout=30s. pass_threshold={pass_threshold}."
    )
    if cross_panel:
        judge_method += " Cruzado às cegas: Grok pontua Gemini e Gemini pontua Grok."
    if judge:
        judge_method += f" Juiz terceiro: {judge_provider_name or judge.name} / {judge_model}."
    report: dict[str, Any] = {
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "method": {
            "correctness": "LLM: mesma key facts que a referência (0–100). Recusa esperada e sem contexto ficam fora.",
            "completeness": "LLM: cobertura de todos os pontos da referência; extra correcto não penaliza.",
            "grounded_rate": "LLM: fracção das afirmações suportadas pelos chunks juntos com \\n\\n---\\n\\n.",
            "pass_rate": f"% dos casos pontuados com correctness ≥ {pass_threshold} (só correctness).",
            "judge": judge_method,
        },
        "pass_threshold": pass_threshold,
        "models": payload.get("models"),
        "summary": summary,
        "cases": cases_out,
    }
    if judge:
        report["judge"] = {"provider": judge_provider_name or judge.name, "model": judge_model}
        report["summary_judge"] = {name: aggregate_llm_cases(items) for name, items in by_judge.items()}
    if cross_panel:
        report["cross_judge"] = {
            "blind": True,
            "pairs": {"gemini": "xai", "xai": "gemini"},
            "models": contestants,
        }
        report["summary_cross"] = {name: aggregate_llm_cases(items) for name, items in by_cross.items()}
    return report


def evaluate_path(
    run_path: Path,
    *,
    chunks_path: Path | None = None,
    settings: Settings | None = None,
    use_judge: bool = False,
    use_cross_judge: bool = False,
    pass_threshold: float = PASS_THRESHOLD,
) -> Path:
    payload = json.loads(run_path.read_text(encoding="utf-8"))
    judge = None
    judge_model = None
    judge_provider_name = None
    cross_panel = None
    if use_judge or use_cross_judge:
        if settings is None:
            from lab.config import load_settings

            settings = load_settings(require_keys=True)
        if use_judge:
            judge = make_judge_provider(settings)
            judge_model = settings.judge_model
            judge_provider_name = settings.judge_provider
        if use_cross_judge:
            cross_panel = make_cross_panel(settings)
    report = evaluate_payload(
        payload,
        chunk_texts=load_chunk_texts(chunks_path),
        store=default_store(),
        judge=judge,
        judge_model=judge_model,
        judge_provider_name=judge_provider_name,
        cross_panel=cross_panel,
        pass_threshold=pass_threshold,
    )
    out_path = run_path.with_name(run_path.stem + ".eval.json")
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path


def _fmt(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.3f}"


def _format_provider_block(title: str, summary: dict[str, Any]) -> list[str]:
    lines = [title]
    for provider, stats in summary.items():
        extra = ""
        if "n_unanswerable_ok" in stats:
            extra = (
                f"  unanswerable_ok={stats.get('n_unanswerable_ok', 0)}"
                f"  false_refusal={stats.get('n_false_refusal', 0)}"
            )
        lines.append(
            f"{provider}: correctness={_fmt(stats.get('correctness'))}  "
            f"grounded_rate={_fmt(stats.get('grounded_rate'))}  "
            f"completeness={_fmt(stats.get('completeness'))}  "
            f"pass_rate={_fmt(stats.get('pass_rate'))}  n={stats.get('n', 0)}{extra}"
        )
    return lines


def format_summary(report: dict[str, Any]) -> str:
    lines = [f"limiar pass_rate: correctness ≥ {report.get('pass_threshold')}"]
    lines.extend(_format_provider_block("lexical:", report.get("summary") or {}))
    if report.get("summary_cross"):
        lines.extend(_format_provider_block("cruzado (cego: gemini←xai, xai←gemini):", report["summary_cross"]))
    if report.get("summary_judge"):
        judge_meta = report.get("judge") or {}
        lines.extend(
            _format_provider_block(
                f"juiz terceiro ({judge_meta.get('provider')}/{judge_meta.get('model')}):",
                report["summary_judge"],
            )
        )
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Avaliar uma run da Fase 1 (métricas determinísticas e juiz opcional).")
    parser.add_argument("run", nargs="?", help="Ficheiro data/runs/phase1_*.json. Sem argumento, usa a mais recente.")
    parser.add_argument("--judge", action="store_true", help="Pontuar com um terceiro modelo (JUDGE_PROVIDER / JUDGE_MODEL).")
    parser.add_argument(
        "--cross-judge",
        action="store_true",
        help="Grok avalia Gemini e Gemini avalia Grok, sem identificar o autor no prompt.",
    )
    parser.add_argument("--pass-threshold", type=float, default=PASS_THRESHOLD, help="Limiar de correctness para pass_rate (default 0.8).")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    run_path = Path(args.run) if args.run else latest_run()
    out_path = evaluate_path(
        run_path,
        use_judge=args.judge,
        use_cross_judge=args.cross_judge,
        pass_threshold=args.pass_threshold,
    )
    report = json.loads(out_path.read_text(encoding="utf-8"))
    print(f"Run: {run_path}")
    print(f"Eval: {out_path}")
    print(format_summary(report))


if __name__ == "__main__":
    main()
