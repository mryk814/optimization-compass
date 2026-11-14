from __future__ import annotations

from scripts.lesson_figures.high_dimensional_smooth_unconstrained import FIGURES, pa007_runs


def test_high_dimensional_smooth_figure_uses_the_article_numbers() -> None:
    runs = pa007_runs()
    counts = {name: (run["iterations"], len(run["history"])) for name, run in runs.items()}
    assert counts == {"GD": (5883, 5884), "CG": (151, 310), "L-BFGS": (144, 151)}
    for run in runs.values():
        assert round(run["f"], 6) == 0.047872
        assert run["history"][-1] <= 1e-6 < run["history"][-2]
    figure = FIGURES["large-smooth-deblur.svg"]()
    for text in ("全体の誤差 5.8%", "全体の誤差 2.2%", "5884回", "310回", "151回", "位置 180〜240"):
        assert text in figure


def test_pa007_milestones_use_first_inclusive_crossing() -> None:
    from scripts.lesson_figures.high_dimensional_smooth_unconstrained import pa007_milestones

    # Rebounds do not replace the first crossing; a skipped level shares its evaluation.
    history = [2.0, 1.0, 1.2, 0.08, 0.2, 0.0005]
    assert pa007_milestones(history) == [(2, 0), (4, -1), (6, -2), (6, -3)]
    assert pa007_milestones([]) == []
    assert pa007_milestones([2.0]) == []


def test_pa007_milestones_match_computed_runs() -> None:
    from scripts.lesson_figures.high_dimensional_smooth_unconstrained import pa007_milestones

    expected = {
        "GD": [2, 4, 12, 139, 2630, 4517, 5884],
        "CG": [4, 12, 17, 35, 144, 230, 310],
        "L-BFGS": [4, 4, 6, 17, 76, 114, 151],
    }
    for name, run in pa007_runs().items():
        milestones = pa007_milestones(run["history"])
        assert [evaluation for evaluation, _ in milestones] == expected[name]
        assert [exponent for _, exponent in milestones] == list(range(0, -7, -1))
        assert milestones[-1] == (len(run["history"]), -6)
        # A relative perturbation changes raw coordinates, but not these crossing events.
        for scale in (1 - 1e-4, 1 + 1e-4):
            assert pa007_milestones([value * scale for value in run["history"]]) == milestones
        for evaluation, exponent in milestones:
            threshold = 10.0**exponent
            assert run["history"][evaluation - 1] <= threshold
            assert all(value > threshold for value in run["history"][: evaluation - 1])
