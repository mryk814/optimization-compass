from __future__ import annotations

import math
from pathlib import Path

from scripts.lesson_figures.external_solver_objective import FIGURES

ROOT = Path(__file__).parents[2]


def test_external_solver_figure_uses_the_article_numbers() -> None:
    from scripts.lesson_figures.external_solver_objective import (
        EXT_RUNS,
        ext_equilibrium,
        ext_objective,
    )

    rows = [
        (0.1, "α", 0.0, 0.0),
        (0.35, "α+β", 0.3, 0.04),
        (0.5, "α+β", 0.6, 0.07),
        (0.8, "β", 1.0, 0.14),
    ]
    for x, phases, fraction, gibbs in rows:
        got = ext_equilibrium(x)
        assert got[0] == phases
        assert math.isclose(got[1], fraction, abs_tol=1e-12)
        assert math.isclose(got[2], gibbs, abs_tol=1e-12)
    assert [round(ext_objective(x), 6) for x in (-0.41, 0.0, 0.2, 0.35, 0.6, 0.8)] == [
        0.09,
        0.09,
        0.09,
        0.0,
        0.25,
        0.49,
    ]
    assert [(name, end, calls) for name, _, end, calls in EXT_RUNS] == [
        ("BFGS", -0.41, 4),
        ("L-BFGS-B", 0.0, 4),
        ("Nelder–Mead", 0.35, 30),
    ]
    figure = FIGURES["external-solver-flat-stop.svg"]()
    for text in ("x=−0.41、J=0.09", "x=0.00、J=0.09", "x=0.35、J=0、30回", "始点 x=0.60（J=0.25）"):
        assert text in figure


def test_external_solver_article_python_is_executable() -> None:
    article = (ROOT / "content/concepts/external-solver-objective.md").read_text(encoding="utf-8")
    code = article.split("```python\n", 1)[1].split("```", 1)[0]
    compile(code, "external-solver-objective.md", "exec")
