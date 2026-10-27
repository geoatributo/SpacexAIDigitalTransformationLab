import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "plots"))
import plot_sweep as sweep


def _view(name: str, mode: str, top_n: int | None, adjacent: int | None, gemini: float, xai: float) -> sweep.ConfigView:
    return sweep.ConfigView(
        name=name,
        policy={"mode": mode, "top_n": top_n, "adjacent_m": adjacent},
        temperature=0.1,
        top_p=0.9,
        model_names={"gemini": "gemini-3.8-flash", "xai": "grok-4"},
        summary={
            "gemini": {"correctness": gemini, "grounded_rate": gemini, "completeness": gemini},
            "xai": {"correctness": xai, "grounded_rate": xai, "completeness": xai},
        },
    )


def test_configs_sort_by_context_shape() -> None:
    views = [
        _view("full", "full_top1", None, None, 1, 1),
        _view("top10", "top_n", 10, None, 1, 1),
        _view("adj", "top_n_adjacent", 3, 1, 1, 1),
        _view("top1", "top_n", 1, None, 1, 1),
    ]
    ordered = [view.name for view in sorted(views, key=sweep.sort_key)]
    assert ordered == ["top1", "top10", "adj", "full"]
    assert sweep.axis_label({"mode": "top_n_adjacent", "top_n": 3, "adjacent_m": 1}) == "Top 3 + 1 adjacent"


def test_delta_is_grok_minus_gemini() -> None:
    gap = sweep.deltas(_view("top6", "top_n", 6, None, 0.9, 0.7))
    assert abs(gap["correctness"] - -0.2) < 1e-9


def test_pass_code_marks_who_passed() -> None:
    assert sweep.pass_code(True, True) == 0
    assert sweep.pass_code(True, False) == 1
    assert sweep.pass_code(False, True) == 2
    assert sweep.pass_code(False, False) == 3
    assert sweep.pass_code(None, True) is None


def test_sweep_plots_use_the_run_folder_name() -> None:
    nested = Path("data/runs/20261026T160000Z/context_sweep.json")
    flat = Path("data/runs/context_sweep_20261026T160000Z.json")
    assert sweep.default_sweep_out(nested) == sweep.DEFAULT_OUT / "20261026T160000Z"
    assert sweep.default_sweep_out(flat) == sweep.DEFAULT_OUT / "20261026T160000Z"


def test_median_latency_uses_the_middle_call() -> None:
    assert sweep.median([1000, 3000, 2000]) == 2000
