"""Comparison plots for every config named in a context_sweep.json file.

The sweep lists the configs. Scores come from each ``<name>.eval.json`` and
latency and tokens come from the matching ``<name>.json`` in the same folder.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from lab.sweep_report import (  # noqa: E402
    METRICS,
    ConfigView,
    axis_label,
    case_matrix,
    cost_stats,
    deltas,
    load_sweep,
    median,
    model_label as model_caption,
    pass_code,
    provider_order,
    sampling_note,
    sort_key,
    _summary_value,
)
from plot_config_metrics import COLORS  # noqa: E402

DEFAULT_RUNS = REPO_ROOT / "data" / "runs"
DEFAULT_OUT = Path(__file__).resolve().parent / "out"
PASS_COLORS = ("#d9d9d9", "#3b6ea5", "#c47b2b", "#7a2e2e")
PASS_LABELS = ("both pass", "only Gemini passes", "only Grok passes", "both fail")
REFUSAL_LABELS = ("both answer", "only Gemini refuses", "only Grok refuses", "both refuse")


def _style(axis) -> None:
    axis.spines["top"].set_visible(False)
    axis.spines["right"].set_visible(False)


def _grouped_bars(axis, labels: list[str], series: dict[str, list[float]], *, model_names: dict) -> None:
    import matplotlib.pyplot as plt

    positions = list(range(len(labels)))
    providers = provider_order(list(series))
    width = 0.8 / max(len(providers), 1)
    for index, provider in enumerate(providers):
        offset = (index - (len(providers) - 1) / 2) * width
        bars = axis.bar(
            [pos + offset for pos in positions],
            series[provider],
            width=width * 0.92,
            label=model_caption(provider, model_names),
            color=COLORS[index % len(COLORS)],
        )
        axis.bar_label(bars, fmt="%.2f", padding=2, fontsize=7)
    axis.set_xticks(positions, labels, rotation=25, ha="right")
    _style(axis)
    axis.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.32), ncol=1)
    plt.setp(axis.get_xticklabels(), fontsize=8)


def _save(figure, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=140, bbox_inches="tight")
    import matplotlib.pyplot as plt

    plt.close(figure)
    return path


def plot_metric_across(views: list[ConfigView], metric: str, out_path: Path) -> Path:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    labels = [view.label for view in views]
    providers = provider_order(list(views[0].summary))
    series = {
        provider: [_summary_value(view.summary, provider, metric) or 0.0 for view in views] for provider in providers
    }
    figure, axis = plt.subplots(figsize=(max(8, 1.35 * len(views)), 5.2))
    _grouped_bars(axis, labels, series, model_names=views[0].model_names)
    axis.set_ylim(0, 1.15)
    axis.set_ylabel(metric)
    note = sampling_note(views)
    axis.set_title(f"{metric} across configs" + (f"\n{note}" if note else ""))
    return _save(figure, out_path)


def plot_deltas(views: list[ConfigView], out_path: Path) -> Path:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    labels = [view.label for view in views]
    positions = list(range(len(labels)))
    width = 0.8 / len(METRICS)
    figure, axis = plt.subplots(figsize=(max(8, 1.35 * len(views)), 5.2))
    metric_colors = ("#3b6ea5", "#c47b2b", "#2f6f4e")
    for index, metric in enumerate(METRICS):
        offset = (index - (len(METRICS) - 1) / 2) * width
        values = [deltas(view)[metric] or 0.0 for view in views]
        bars = axis.bar(
            [pos + offset for pos in positions],
            values,
            width=width * 0.92,
            label=metric,
            color=metric_colors[index],
        )
        axis.bar_label(bars, fmt="%+.2f", padding=2, fontsize=7)
    axis.axhline(0, color="#666666", linewidth=0.8)
    axis.set_xticks(positions, labels, rotation=25, ha="right")
    gemini = model_caption("gemini", views[0].model_names)
    xai = model_caption("xai", views[0].model_names)
    note = sampling_note(views)
    axis.set_ylabel(f"{xai} − {gemini}")
    axis.set_title("Score difference" + (f"\n{note}" if note else ""))
    _style(axis)
    axis.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.32), ncol=3)
    return _save(figure, out_path)


def plot_cost(views: list[ConfigView], out_path: Path) -> Path:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    labels = [view.label for view in views]
    stats = [cost_stats(view) for view in views]
    providers = provider_order([provider for row in stats for provider in row])
    figure, axes = plt.subplots(1, 2, figsize=(max(10, 1.6 * len(views)), 5.2))
    latency = {provider: [row.get(provider, {}).get("median_s", 0.0) for row in stats] for provider in providers}
    tokens = {provider: [row.get(provider, {}).get("mean_tokens", 0.0) for row in stats] for provider in providers}
    _grouped_bars(axes[0], labels, latency, model_names=views[0].model_names)
    _grouped_bars(axes[1], labels, tokens, model_names=views[0].model_names)
    axes[0].set_ylabel("median latency (s)")
    axes[1].set_ylabel("mean tokens")
    note = sampling_note(views)
    figure.suptitle("Cost by context size" + (f" — {note}" if note else ""))
    return _save(figure, out_path)


def _heatmap(views: list[ConfigView], *, kind: str, title: str, labels: tuple[str, ...], out_path: Path) -> Path:
    import matplotlib

    matplotlib.use("Agg")
    from matplotlib import pyplot as plt
    from matplotlib.colors import BoundaryNorm, ListedColormap

    case_ids, rows = case_matrix(views, kind=kind)
    grid = [[-1 if value is None else value for value in row] for row in rows]
    figure, axis = plt.subplots(figsize=(max(10, 0.32 * len(case_ids)), max(3.5, 0.55 * len(views) + 1.5)))
    cmap = ListedColormap(["#f2f2f2", *PASS_COLORS])
    norm = BoundaryNorm([-1.5, -0.5, 0.5, 1.5, 2.5, 3.5], cmap.N)
    axis.imshow(grid, aspect="auto", cmap=cmap, norm=norm, interpolation="nearest")
    axis.set_yticks(range(len(views)), [view.label for view in views])
    axis.set_xticks(range(len(case_ids)), case_ids, rotation=90, fontsize=7)
    axis.set_title(title)
    handles = [
        plt.Line2D([0], [0], marker="s", color="none", markerfacecolor=color, markersize=10, label=label)
        for color, label in zip(PASS_COLORS, labels, strict=True)
    ]
    axis.legend(handles=handles, frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.28), ncol=2)
    return _save(figure, out_path)


def write_plots(views: list[ConfigView], out_dir: Path) -> list[Path]:
    written = [plot_metric_across(views, metric, out_dir / f"across_{metric}.png") for metric in METRICS]
    written.append(plot_deltas(views, out_dir / "delta.png"))
    written.append(plot_cost(views, out_dir / "latency_tokens.png"))
    note = sampling_note(views)
    suffix = f" ({note})" if note else ""
    written.append(
        _heatmap(
            views,
            kind="pass",
            title=f"Pass / fail by question{suffix}",
            labels=PASS_LABELS,
            out_path=out_dir / "disagreement_pass.png",
        )
    )
    written.append(
        _heatmap(
            views,
            kind="refusal",
            title=f"Refusals by question{suffix}",
            labels=REFUSAL_LABELS,
            out_path=out_dir / "disagreement_refusal.png",
        )
    )
    return written


def default_sweep_out(sweep_path: Path) -> Path:
    """Match the run folder name so plots stay with that sweep."""
    parent = sweep_path.parent
    if parent.name == "runs":
        stamp = sweep_path.stem.removeprefix("context_sweep").strip("_") or "sweep"
        return DEFAULT_OUT / stamp
    return DEFAULT_OUT / parent.name


def latest_sweep(runs_dir: Path) -> Path:
    files = sorted(runs_dir.rglob("context_sweep*.json"), key=lambda item: item.stat().st_mtime)
    if not files:
        raise SystemExit(f"Nenhum context_sweep*.json em {runs_dir}")
    return files[-1]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Gráficos de comparação a partir de um context_sweep.json e dos eval de cada config."
    )
    parser.add_argument("sweep", nargs="?", help="context_sweep.json. Sem argumento, usa o mais recente em data/runs.")
    parser.add_argument("--out", type=Path, default=None, help="Pasta dos PNG. Por defeito plots/out/<pasta da corrida>/.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    sweep_path = Path(args.sweep) if args.sweep else latest_sweep(DEFAULT_RUNS)
    if not sweep_path.is_file():
        raise SystemExit(f"Sweep em falta: {sweep_path}")
    try:
        views = load_sweep(sweep_path)
    except FileNotFoundError as exc:
        raise SystemExit(str(exc)) from exc
    for path in write_plots(views, args.out or default_sweep_out(sweep_path)):
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
