import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "plots"))
import plot_config_metrics as plots


def test_metric_table_keeps_model_order() -> None:
    models, series, counts = plots.metric_table(
        {
            "gemini": {"correctness": 0.9, "grounded_rate": 0.8, "completeness": 0.7, "n": 31},
            "xai": {"correctness": 0.5, "grounded_rate": 0.4, "completeness": 0.3, "n": 31},
        }
    )
    assert models == ["gemini", "xai"]
    assert series["gemini"] == [0.9, 0.8, 0.7]
    assert series["xai"] == [0.5, 0.4, 0.3]
    assert counts["xai"] == 31


def test_config_title_describes_context_and_sampling() -> None:
    assert plots.config_title(
        {"mode": "top_n_adjacent", "top_n": 3, "adjacent_m": 1},
        temperature=0.1,
        top_p=0.9,
    ) == "Top 3 chunks with 1 adjacent, T=0.1, top_p=0.9"
    assert plots.config_title(
        {"mode": "top_n", "top_n": 6},
        temperature=0.1,
        top_p=0.9,
    ) == "Top 6 chunks, T=0.1, top_p=0.9"
    assert plots.model_label("xai", {"xai": "grok-4.20-0309-non-reasoning"}) == "grok-4.20-0309-non-reasoning"


def test_plot_path_follows_the_run_folder() -> None:
    nested = Path("data/runs/20261026T160000Z/top_n_6.eval.json")
    flat = Path("data/runs/top_n_6.eval.json")
    assert plots.default_plot_path(nested, "top_n_6") == plots.DEFAULT_OUT / "20261026T160000Z" / "top_n_6.png"
    assert plots.default_plot_path(flat, "top_n_6") == plots.DEFAULT_OUT / "top_n_6.png"


def test_eval_path_for_config_name() -> None:
    path = plots.eval_path_for("top_n_6", runs_dir=Path("data/runs"))
    assert path == Path("data/runs") / "top_n_6.eval.json"
