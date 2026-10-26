"""Read a sweep folder into the JSON the metrics page draws.

The plot scripts use the same loader, so a bar on the page matches the PNG.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

METRICS = ("correctness", "grounded_rate", "completeness")
ROOT_RUN_ID = "runs"
_RUN_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,80}")


def format_num(value: float) -> str:
    return format(value, "g")


def config_title(policy: dict, *, temperature: float | None, top_p: float | None) -> str:
    mode = policy.get("mode")
    top_n = policy.get("top_n")
    adjacent = policy.get("adjacent_m")
    if mode == "full_top1":
        head = "Full document of the top chunk"
    elif mode == "top_n_adjacent":
        head = f"Top {top_n} chunks with {adjacent} adjacent"
    else:
        head = f"Top {top_n} chunks"
    parts = [head]
    if temperature is not None:
        parts.append(f"T={format_num(float(temperature))}")
    if top_p is not None:
        parts.append(f"top_p={format_num(float(top_p))}")
    return ", ".join(parts)


def model_label(provider: str, models: dict) -> str:
    exact = models.get(provider)
    return str(exact) if exact else provider


@dataclass
class ConfigView:
    name: str
    policy: dict
    temperature: float | None
    top_p: float | None
    model_names: dict
    summary: dict
    eval_cases: list = field(default_factory=list)
    run_cases: list = field(default_factory=list)

    @property
    def label(self) -> str:
        return axis_label(self.policy)


def axis_label(policy: dict) -> str:
    mode = policy.get("mode")
    if mode == "full_top1":
        return "Full document"
    if mode == "top_n_adjacent":
        return f"Top {policy.get('top_n')} + {policy.get('adjacent_m')} adjacent"
    return f"Top {policy.get('top_n')}"


def sort_key(view: ConfigView) -> tuple:
    mode = view.policy.get("mode")
    rank = {"top_n": 0, "top_n_adjacent": 1, "full_top1": 2}.get(mode, 9)
    return (rank, view.policy.get("top_n") or 0, view.policy.get("adjacent_m") or 0, view.name)


def provider_order(names: list[str]) -> list[str]:
    preferred = ("gemini", "xai")
    ordered = [name for name in preferred if name in names]
    ordered.extend(name for name in names if name not in ordered)
    return ordered


def sampling_note(views: list[ConfigView]) -> str:
    temps = {view.temperature for view in views}
    tops = {view.top_p for view in views}
    if len(temps) == 1 and len(tops) == 1 and None not in temps and None not in tops:
        return f"T={format_num(float(next(iter(temps))))}, top_p={format_num(float(next(iter(tops))))}"
    return ""


def _load_json(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _view_from_files(name: str, eval_path: Path, metric: dict | None = None) -> ConfigView | None:
    if not eval_path.is_file():
        print(f"A saltar {name}: eval em falta ({eval_path})", file=sys.stderr)
        return None
    report = _load_json(eval_path)
    run_path = eval_path.with_name(eval_path.name.removesuffix(".eval.json") + ".json")
    run = _load_json(run_path) if run_path.is_file() else {}
    return ConfigView(
        name=name,
        policy=run.get("context_policy") or {},
        temperature=run.get("temperature"),
        top_p=run.get("top_p"),
        model_names=report.get("models") or run.get("models") or {},
        summary=report.get("summary") or (metric or {}).get("summary") or {},
        eval_cases=report.get("cases") or [],
        run_cases=run.get("cases") or [],
    )


def load_sweep(path: Path) -> list[ConfigView]:
    """Configs referenced by the sweep, in context order, skipping missing eval files."""
    sweep = _load_json(path)
    runs_dir = path.parent
    by_name: dict[str, dict] = {}
    for row in sweep.get("metrics") or []:
        if row.get("name"):
            by_name[str(row["name"])] = row
    names: list[str] = []
    for row in sweep.get("results") or []:
        name = str(row.get("name") or "")
        if name and row.get("returncode", 0) == 0 and name not in names:
            names.append(name)
    for name in by_name:
        if name not in names and by_name[name].get("status", "ok") == "ok":
            names.append(name)

    views: list[ConfigView] = []
    for name in names:
        metric = by_name.get(name) or {}
        eval_path = Path(str(metric["eval_path"])) if metric.get("eval_path") else runs_dir / f"{name}.eval.json"
        view = _view_from_files(name, eval_path, metric)
        if view is not None:
            views.append(view)
    views.sort(key=sort_key)
    if not views:
        raise FileNotFoundError(f"Nenhuma config com eval em {path}")
    return views


def load_run_dir(runs_dir: Path) -> list[ConfigView]:
    """Prefer the newest context_sweep in the folder. Otherwise every eval file there."""
    sweeps = sorted(runs_dir.glob("context_sweep*.json"), key=lambda item: item.stat().st_mtime)
    if sweeps:
        return load_sweep(sweeps[-1])
    views: list[ConfigView] = []
    for eval_path in sorted(runs_dir.glob("*.eval.json")):
        name = eval_path.name.removesuffix(".eval.json")
        view = _view_from_files(name, eval_path)
        if view is not None:
            views.append(view)
    views.sort(key=sort_key)
    if not views:
        raise FileNotFoundError(f"Nenhuma config com eval em {runs_dir}")
    return views


def _summary_value(summary: dict, provider: str, metric: str) -> float | None:
    row = summary.get(provider)
    if not isinstance(row, dict) or row.get(metric) is None:
        return None
    return float(row[metric])


def deltas(view: ConfigView) -> dict[str, float | None]:
    """Grok minus Gemini. Missing scores stay None."""
    out: dict[str, float | None] = {}
    for metric in METRICS:
        gemini = _summary_value(view.summary, "gemini", metric)
        xai = _summary_value(view.summary, "xai", metric)
        out[metric] = None if gemini is None or xai is None else xai - gemini
    return out


def _providers(case: dict) -> dict[str, dict]:
    return {str(row.get("provider")): row for row in case.get("providers") or []}


def pass_code(gemini_passed: bool | None, xai_passed: bool | None) -> int | None:
    if gemini_passed is None or xai_passed is None:
        return None
    if gemini_passed and xai_passed:
        return 0
    if gemini_passed:
        return 1
    if xai_passed:
        return 2
    return 3


def refusal_code(gemini_refused: bool | None, xai_refused: bool | None) -> int | None:
    """0 both answer, 1 only Gemini, 2 only Grok, 3 both refuse."""
    if gemini_refused is None or xai_refused is None:
        return None
    if not gemini_refused and not xai_refused:
        return 0
    if gemini_refused and not xai_refused:
        return 1
    if not gemini_refused and xai_refused:
        return 2
    return 3


def case_matrix(views: list[ConfigView], *, kind: str) -> tuple[list[str], list[list[int | None]]]:
    case_ids: list[str] = []
    seen: set[str] = set()
    for view in views:
        source = view.eval_cases if kind == "pass" else view.run_cases
        for case in source:
            case_id = str(case.get("case_id"))
            if case_id not in seen:
                seen.add(case_id)
                case_ids.append(case_id)
    rows: list[list[int | None]] = []
    for view in views:
        by_id = {str(case.get("case_id")): case for case in (view.eval_cases if kind == "pass" else view.run_cases)}
        row: list[int | None] = []
        for case_id in case_ids:
            providers = _providers(by_id.get(case_id) or {})
            if kind == "pass":
                gemini = providers.get("gemini", {}).get("passed")
                xai = providers.get("xai", {}).get("passed")
                row.append(pass_code(None if gemini is None else bool(gemini), None if xai is None else bool(xai)))
            else:
                gemini = providers.get("gemini", {}).get("is_refusal")
                xai = providers.get("xai", {}).get("is_refusal")
                row.append(
                    refusal_code(None if gemini is None else bool(gemini), None if xai is None else bool(xai))
                )
        rows.append(row)
    return case_ids, rows


def median(values: list[float]) -> float:
    ordered = sorted(values)
    count = len(ordered)
    if count == 0:
        return 0.0
    middle = count // 2
    if count % 2:
        return float(ordered[middle])
    return (ordered[middle - 1] + ordered[middle]) / 2


def cost_stats(view: ConfigView) -> dict[str, dict[str, float]]:
    buckets: dict[str, dict[str, list[float]]] = {}
    for case in view.run_cases:
        for row in case.get("providers") or []:
            if row.get("error"):
                continue
            provider = str(row.get("provider"))
            bucket = buckets.setdefault(provider, {"latency_ms": [], "tokens": []})
            if row.get("latency_ms") is not None:
                bucket["latency_ms"].append(float(row["latency_ms"]))
            total = (row.get("usage") or {}).get("total_tokens")
            if total is not None:
                bucket["tokens"].append(float(total))
    return {
        provider: {
            "median_s": median(bucket["latency_ms"]) / 1000,
            "mean_tokens": (sum(bucket["tokens"]) / len(bucket["tokens"])) if bucket["tokens"] else 0.0,
        }
        for provider, bucket in buckets.items()
    }


def _provider_metrics(summary: dict, provider: str) -> dict | None:
    row = summary.get(provider)
    if not isinstance(row, dict):
        return None
    payload: dict = {metric: _summary_value(summary, provider, metric) for metric in METRICS}
    if row.get("n") is not None:
        payload["n"] = int(row["n"])
    return payload


def _case_count(summary: dict) -> int:
    for provider in provider_order([str(name) for name in summary]):
        row = summary.get(provider)
        if isinstance(row, dict) and row.get("n") is not None:
            return int(row["n"])
    return 0


def _align(case_ids: list[str], source_ids: list[str], rows: list[list[int | None]]) -> list[list[int | None]]:
    index = {case_id: position for position, case_id in enumerate(source_ids)}
    aligned: list[list[int | None]] = []
    for row in rows:
        aligned.append([row[index[case_id]] if case_id in index else None for case_id in case_ids])
    return aligned


def _shared_cases(views: list[ConfigView]) -> tuple[list[str], list[list[int | None]], list[list[int | None]]]:
    pass_ids, pass_rows = case_matrix(views, kind="pass")
    refusal_ids, refusal_rows = case_matrix(views, kind="refusal")
    cases = list(pass_ids)
    for case_id in refusal_ids:
        if case_id not in cases:
            cases.append(case_id)
    return cases, _align(cases, pass_ids, pass_rows), _align(cases, refusal_ids, refusal_rows)


def _created_at(folder: Path) -> str:
    sweeps = sorted(folder.glob("context_sweep*.json"), key=lambda item: item.stat().st_mtime)
    if sweeps:
        created = _load_json(sweeps[-1]).get("created_at")
        if created:
            return str(created)
        stamp = sweeps[-1].stat().st_mtime
    else:
        files = list(folder.glob("*.eval.json"))
        stamp = max((path.stat().st_mtime for path in files), default=folder.stat().st_mtime)
    return datetime.fromtimestamp(stamp, timezone.utc).isoformat()


def _activity(folder: Path) -> float:
    files = list(folder.glob("context_sweep*.json")) + list(folder.glob("*.eval.json"))
    if not files:
        return folder.stat().st_mtime
    return max(path.stat().st_mtime for path in files)


def _has_metrics(folder: Path) -> bool:
    return any(folder.glob("context_sweep*.json")) or any(folder.glob("*.eval.json"))


def list_runs(runs_root: Path) -> list[dict]:
    """Subfolders with a sweep or an eval file, newest first. The flat runs folder is included too."""
    if not runs_root.is_dir():
        return []
    folders: list[tuple[str, Path]] = []
    if _has_metrics(runs_root):
        folders.append((ROOT_RUN_ID, runs_root))
    for child in runs_root.iterdir():
        if child.is_dir() and _RUN_ID.fullmatch(child.name) and _has_metrics(child):
            if child.name == ROOT_RUN_ID and any(run_id == ROOT_RUN_ID for run_id, _path in folders):
                continue
            folders.append((child.name, child))
    folders.sort(key=lambda item: _activity(item[1]), reverse=True)
    return [
        {
            "id": run_id,
            "created_at": _created_at(folder),
            "config_count": len(list(folder.glob("*.eval.json"))),
        }
        for run_id, folder in folders
    ]


def resolve_run_dir(runs_root: Path, run_id: str) -> Path:
    if not _RUN_ID.fullmatch(run_id):
        raise FileNotFoundError(run_id)
    root = runs_root.resolve()
    child = (runs_root / run_id).resolve()
    try:
        child.relative_to(root)
    except ValueError as exc:
        raise FileNotFoundError(run_id) from exc
    if child.parent == root and child.is_dir() and _has_metrics(child):
        return child
    if run_id == ROOT_RUN_ID and _has_metrics(root):
        return root
    raise FileNotFoundError(run_id)


def build_report(runs_dir: Path, *, run_id: str) -> dict:
    views = load_run_dir(runs_dir)
    models: dict[str, str] = {}
    for view in views:
        for provider, name in view.model_names.items():
            models.setdefault(str(provider), str(name))
    cases, pass_rows, refusal_rows = _shared_cases(views)
    configs = []
    for view in views:
        metrics = {}
        for provider in provider_order([str(name) for name in view.summary]):
            row = _provider_metrics(view.summary, provider)
            if row is not None:
                metrics[provider] = row
        configs.append(
            {
                "name": view.name,
                "label": view.label,
                "title": config_title(view.policy, temperature=view.temperature, top_p=view.top_p),
                "temperature": view.temperature,
                "top_p": view.top_p,
                "policy": view.policy,
                "n": _case_count(view.summary),
                "metrics": metrics,
                "delta": deltas(view),
                "cost": cost_stats(view),
            }
        )
    return {
        "id": run_id,
        "created_at": _created_at(runs_dir),
        "sampling_note": sampling_note(views),
        "models": models,
        "configs": configs,
        "cases": cases,
        "disagreement": {"pass": pass_rows, "refusal": refusal_rows},
    }
