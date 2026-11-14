from __future__ import annotations

import math

from scripts.lesson_figures.written_and_real_constraints import FIGURES

from .article_python import article_code, article_setup, assert_article_prints_its_comments


def test_written_constraint_figure_uses_the_article_numbers() -> None:
    from scripts.lesson_figures.solver_evaluation_points import EVAL_NM_LAST_A, EVAL_NM_Q
    from scripts.lesson_figures.written_and_real_constraints import (
        CON_CLIPPED,
        CON_FMIN,
        CON_PENALTY_100,
        con_boundary_q,
        con_critical_area,
        con_dry_time,
    )

    # The points come from the same runs as the solver-evaluation figure.
    assert [q for _, q in CON_FMIN] == list(EVAL_NM_Q[12:15])
    assert CON_FMIN[2][0] == CON_CLIPPED[0] == EVAL_NM_LAST_A
    assert round(con_critical_area(), 6) == 0.000251
    assert round(con_dry_time(EVAL_NM_LAST_A, 0.0)) == 1700
    # fmin's 13th and 14th points survive the 30 minutes; the 15th runs dry after ~1370 s.
    assert con_dry_time(*CON_FMIN[0]) > 1800 and con_dry_time(*CON_FMIN[1]) > 1800
    assert round(con_dry_time(*CON_FMIN[2]), -1) == 1370
    # The answer with a penalty of 100 sits 1.5 s inside the boundary.
    assert round(con_dry_time(*CON_PENALTY_100), 1) == 1801.5
    assert round(con_boundary_q(0.0), 6) == -0.000556
    assert con_dry_time(1e-4, 1e-6) == math.inf
    plane = FIGURES["written-constraint-plane.svg"]()
    for text in ("ありうる値", "ツールが失敗", "失敗を100にした答え", "記録に合う答え"):
        assert text in plane


def test_written_constraint_runs_match_a_scipy_rerun() -> None:
    import warnings

    import pytest

    np = pytest.importorskip("numpy")
    optimize = pytest.importorskip("scipy.optimize")
    from scripts.lesson_figures.written_and_real_constraints import CON_PENALTY_100, con_dry_time

    space = article_setup("written-and-real-constraints", "x0 = [1e-4")
    tool, penalized = space["tool"], space["penalized"]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        res = optimize.minimize(penalized(100), [1e-4, 1e-4])
    assert not res.success
    assert np.allclose(res.x, CON_PENALTY_100, rtol=1e-5, atol=0)
    # At that answer the computable sum of squares still falls toward the boundary, and a step
    # of 1e-6 downhill runs the tank dry after about 1791 s.
    gradient = np.array([(tool(res.x + d) - tool(res.x - d)) / 2e-10 for d in np.eye(2) * 1e-10])
    assert (round(gradient[0], -2), round(gradient[1], -1)) == (-24600, 6340)
    step = res.x - 1e-6 * gradient / np.linalg.norm(gradient)
    assert round(con_dry_time(*step)) == 1791
    with pytest.raises(ValueError), warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        tool(step)
    # With q > 0 the equations never run dry, but the tool still fails where the balance level
    # (q/a)^2/(2g) is tiny; the empty-state tool returns a value on a 7 x 7 grid of the box.
    with pytest.raises(ValueError), warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        tool([0.01, 1e-6])
    assert round((1e-6 / 0.01) ** 2 / (2 * 9.81), 11) == 5.1e-10
    code = article_code("written-and-real-constraints")
    snippet = "def tool_empty" + code.split("def tool_empty", 1)[1].split("\nprint(", 1)[0]
    exec(compile(snippet, "written-and-real-constraints.md", "exec"), space)
    values = [0.0, 1e-7, 1e-6, 1e-5, 1e-4, 1e-3, 1e-2]
    assert all(np.isfinite(space["tool_empty"]([a, q])) for a in values for q in values)


def test_written_constraint_article_python_prints_its_comments() -> None:
    assert_article_prints_its_comments("written-and-real-constraints")
