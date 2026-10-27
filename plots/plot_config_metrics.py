"""Plot average correctness, grounded_rate and completeness for one config."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from lab.sweep_report import METRICS, config_title, model_label  # noqa: E402

DEFAULT_RUNS = REPO_ROOT / "data" / "runs"
DEFAULT_OUT = Path(__file__).resolve().parent / "out"
COLORS = ("#3b6ea5", "#c47b2b", "#2f6f4e", "#6b4c9a")


def eval_path_for(config: str, *, runs_dir: Path) -> Path:
    raw = Path(config)
    if raw.suffix == ".json":
        return raw if raw.is_absolute() else REPO_ROOT / raw
    return runs_dir / f"{config}.eval.json"


def metric_table(summary: dict) -> tuple[list[str], dict[str, list[float]], dict[str, int]]:
    """Providers in file order, one value per metric, and the case count for each provider."""
    models = [str(name) for name in summary]
    series: dict[str, list[float]] = {}
    counts: dict[str, int] = {}
    for model in models:
        row = summary[model] if isinstance(summary[model], dict) else {}
        series[model] = [float(row.get(metric) or 0.0) for metric in METRICS]
        counts[model] = int(row.get("n") or 0)
    return models, series, counts


def default_plot_path(source: Path, config_name: str) -> Path:
    """Plots for a run folder land in plots/out/<that folder>."""
    if source.parent.name == "runs":
        return DEFAULT_OUT / f"{config_name}.png"
    return DEFAULT_OUT / source.parent.name / f"{config_name}.png"


def run_path_for(eval_path: Path) -> Path:
    if eval_path.name.endswith(".eval.json"):
        return eval_path.with_name(eval_path.name.removesuffix(".eval.json") + ".json")
    return eval_path


def plot_config(
    *,
    title: str,
    summary: dict,
    model_names: dict,
    out_path: Path,
) -> Path:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    models, series, counts = metric_table(summary)
    if not models:
        raise SystemExit(f"{title}: summary sem modelos")

    positions = list(range(len(METRICS)))
    width = 0.8 / len(models)
    figure, axis = plt.subplots(figsize=(8, 4.8))
    for index, model in enumerate(models):
        offset = (index - (len(models) - 1) / 2) * width
        bars = axis.bar(
            [pos + offset for pos in positions],
            series[model],
            width=width * 0.92,
            label=f"{model_label(model, model_names)} (n={counts[model]})",
            color=COLORS[index % len(COLORS)],
        )
        axis.bar_label(bars, fmt="%.2f", padding=2, fontsize=8)

    axis.set_xticks(positions, METRICS)
    axis.set_ylim(0, 1.12)
    axis.set_ylabel("média")
    axis.set_title(title)
    axis.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=1)
    axis.spines["top"].set_visible(False)
    axis.spines["right"].set_visible(False)
    figure.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(out_path, dpi=140, bbox_inches="tight")
    plt.close(figure)
    return out_path


def load_report(path: Path) -> dict:
    if not path.is_file():
        raise SystemExit(f"Ficheiro em falta: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Gráfico das médias de uma config: correctness, grounded_rate e completeness, por modelo."
    )
    parser.add_argument("config", help="Nome da config (data/runs/<nome>.eval.json) ou caminho do JSON.")
    parser.add_argument("--runs-dir", type=Path, default=DEFAULT_RUNS, help="Pasta das runs.")
    parser.add_argument("--out", type=Path, default=None, help="PNG de saída. Por defeito plots/out/<config>.png.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    source = eval_path_for(args.config, runs_dir=args.runs_dir)
    report = load_report(source)
    config_name = source.stem.removesuffix(".eval") if source.name.endswith(".eval.json") else source.stem
    run = load_report(run_path_for(source))
    title = config_title(
        run.get("context_policy") or {},
        temperature=run.get("temperature"),
        top_p=run.get("top_p"),
    )
    out_path = args.out or default_plot_path(source, config_name)
    written = plot_config(
        title=title,
        summary=report.get("summary") or {},
        model_names=report.get("models") or run.get("models") or {},
        out_path=out_path,
    )
    print(written)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
