from __future__ import annotations

from pathlib import Path

from scripts.lesson_figures.general_nonsmooth_local import FIGURES

ROOT = Path(__file__).parents[2]


def test_general_nonsmooth_figure_uses_the_article_numbers() -> None:
    from scripts.lesson_figures.general_nonsmooth_local import (
        PA011_START,
        _pa011_clarke_derivative,
        _pa011_clarke_minimum,
        _pa011_compass,
        _pa011_cost,
        _pa011_descent,
        _pa011_gradient_norm,
        _pa011_slope,
    )

    assert round(_pa011_cost(*PA011_START), 6) == 5.48
    assert tuple(round(v, 6) for v in _pa011_slope(1.5001, 1.4999)) == (3.6, -2.4)
    assert tuple(round(v, 6) for v in _pa011_slope(1.4999, 1.5001)) == (-2.4, 3.6)
    # The valley x1 = x2 holds two valley bottoms and a concave kink between them.
    assert [round(_pa011_cost(t, t), 6) for t in (1.0, 2.0, 3.0)] == [0.2, 1.4, 0.6]
    assert round(_pa011_cost(1.5, 1.5), 6) == 0.8
    # Fixed-step gradient descent crosses the valley 14 times in 16 steps and never sees a
    # small gradient.
    path = _pa011_descent(iterations=200)
    gaps = [a - b for a, b in path[:17]]
    assert sum(gaps[i] * gaps[i + 1] < 0 for i in range(16)) == 14
    assert round(min(_pa011_gradient_norm(p) for p in path), 3) == 4.28
    assert round(min(_pa011_cost(*p) for p in path), 3) == 0.8
    assert [round(g, 6) for g in gaps[:5]] == [1.4, 0.8, 0.2, -0.4, 0.2]
    axes = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    both = [*axes, (1, 1), (-1, -1), (1, -1), (-1, 1)]
    for start, directions, expected in (
        (PA011_START, axes, ((1.2, 1.2), 0.44, 68)),
        (PA011_START, both, ((1.0, 1.0), 0.2, 168)),
        ((2.0, 2.0), axes, ((2.0, 2.0), 1.4, 53)),
        ((2.0, 2.0), both, ((3.0, 3.0), 0.6, 115)),
    ):
        point, value, calls = _pa011_compass(start, 0.5, directions)
        assert ((round(point[0], 3), round(point[1], 3)), round(value, 3), calls) == expected
    # The Clarke minimum is negative at a point with a descent direction, positive at the kinks.
    assert round(_pa011_clarke_minimum((1.5, 1.5)), 3) == -0.849
    assert round(_pa011_clarke_minimum((2.0, 2.0)), 3) == 0.566
    # The exact generalized derivative includes slopes from both sides of the concave kink.
    assert _pa011_clarke_derivative((2.0, 2.0), (1.0, 1.0)) == 1.2
    assert _pa011_clarke_derivative((2.0, 2.0), (-1.0, -1.0)) == 0.8
    assert _pa011_clarke_derivative((1.5, 1.5), (-1.0, -1.0)) == -1.2
    figure = FIGURES["general-nonsmooth-kink-valley.svg"]()
    for text in ("谷底 0.2", "谷底 0.6", "山 1.4", "費用 5.48", "一歩 0.1"):
        assert text in figure


def test_general_nonsmooth_article_python_is_executable() -> None:
    article = (ROOT / "content/concepts/general-nonsmooth-local.md").read_text(encoding="utf-8")
    code = article.split("```python\n", 1)[1].split("```", 1)[0]
    compile(code, "general-nonsmooth-local.md", "exec")
