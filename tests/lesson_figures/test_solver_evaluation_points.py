from __future__ import annotations

import math
from pathlib import Path

from scripts.lesson_figures.solver_evaluation_points import FIGURES

ROOT = Path(__file__).parents[2]


def _solver_evaluation_article_code() -> str:
    article = (ROOT / "content/concepts/solver-evaluation-points.md").read_text(encoding="utf-8")
    return article.split("```python\n", 1)[1].split("```", 1)[0]


def _solver_evaluation_tool() -> dict[str, object]:
    """Run the article's definitions (simulate, observed, tool) without its solver calls."""
    namespace: dict[str, object] = {}
    setup = _solver_evaluation_article_code().split("x0 = [1e-4", 1)[0]
    exec(compile(setup, "solver-evaluation-points.md", "exec"), namespace)
    return namespace


def test_solver_evaluation_figures_use_the_article_numbers() -> None:
    from scripts.lesson_figures.solver_evaluation_points import (
        EVAL_BFGS_TRIAL,
        EVAL_NM_LAST_A,
        EVAL_NM_Q,
        EVAL_START,
        eval_dry_time,
        eval_role_counts,
    )

    # With q = 0 (the clipped Nelder-Mead) the 14th point survives the 30 minutes and the 15th
    # runs dry; the L-BFGS-B corner runs dry in about 45 s.
    assert round(eval_dry_time(0.000220156)) == 2051
    assert round(eval_dry_time(EVAL_NM_LAST_A)) == 1700
    assert round(eval_dry_time(0.01)) == 45
    assert len(EVAL_NM_Q) == 15
    assert [i + 1 for i, q in enumerate(EVAL_NM_Q) if q < 0] == [13, 14, 15]
    step = math.hypot(EVAL_BFGS_TRIAL[0] - EVAL_START[0], EVAL_BFGS_TRIAL[1] - EVAL_START[1])
    assert round(step, 2) == 1.01
    assert eval_role_counts() == {"s": 1, "a": 9, "t": 8, "r": 0}
    inflow = FIGURES["solver-evaluation-inflow.svg"]()
    for text in ("4回目 q=−0.25 m³/s（図の外）", "fmin（白抜きは負の q）", "ツールが失敗"):
        assert text in inflow
    breakdown = FIGURES["solver-evaluation-breakdown.svg"]()
    for text in (
        "反復9回の裏の評価54回",
        "直線探索の途中の点 8",
        "差分のための点 36",
    ):
        assert text in breakdown
    assert "呼び直し" not in breakdown


def test_solver_evaluation_points_match_a_scipy_rerun() -> None:
    import contextlib
    import warnings

    import pytest

    np = pytest.importorskip("numpy")
    optimize = pytest.importorskip("scipy.optimize")
    from scripts.lesson_figures.solver_evaluation_points import (
        EVAL_BFGS_TRIAL,
        EVAL_LBFGSB_ROLES,
        EVAL_NM_LAST_A,
        EVAL_NM_Q,
        EVAL_START,
    )

    space = _solver_evaluation_tool()
    tool, simulate, observed = space["tool"], space["simulate"], space["observed"]

    def sse(x, rtol):
        return float(np.sum((simulate(*x, rtol=rtol).y[0] - observed) ** 2))

    def record(solve):
        points = []

        def wrapped(x):
            points.append(np.array(x, dtype=float))
            return tool(points[-1])

        with warnings.catch_warnings(), contextlib.suppress(ValueError):
            warnings.simplefilter("ignore", RuntimeWarning)
            solve(wrapped)
        return points

    start = list(EVAL_START)
    zero_box = [(0, 0.01), (0, 0.01)]
    box = [(1e-5, 1e-3), (1e-5, 1e-3)]
    # Gradient at the start, by central differences through a tight ODE solve.
    gradient = [
        (sse(np.add(start, step), 1e-10) - sse(np.subtract(start, step), 1e-10)) / 2e-7
        for step in ([1e-7, 0.0], [0.0, 1e-7])
    ]
    assert (round(gradient[0], -2), round(gradient[1], -2)) == (-80300, 20300)
    assert round(sse(start, 1e-3), 2) == 4.66

    # fmin's 14th and 15th points have negative inflow: the 14th runs dry 0.3 s after the
    # 30 minutes, the 15th after about 1370 s.
    def dry_time(a, q):
        def empty(_, h):
            return h[0] - 1e-12

        empty.terminal, empty.direction = True, -1
        sol = space["solve_ivp"](
            lambda _, h: [q - a * np.sqrt(2 * 9.81 * max(h[0], 0.0))],
            (0, 5000),
            [1.0],
            events=empty,
            rtol=1e-12,
            atol=1e-14,
        )
        return float(sol.t_events[0][0])

    assert round(dry_time(0.000220156, -3.5625e-5), 1) == 1800.3
    assert round(dry_time(EVAL_NM_LAST_A, EVAL_NM_Q[-1]), -1) == 1370
    bfgs = record(lambda f: optimize.minimize(f, start))
    assert len(bfgs) == 4
    assert [round(v, 6) for v in bfgs[-1]] == list(EVAL_BFGS_TRIAL)
    nelder = record(lambda f: optimize.fmin(f, start, disp=False))
    assert [round(p[1], 12) for p in nelder] == [round(q, 12) for q in EVAL_NM_Q]
    assert round(nelder[-1][0], 9) == EVAL_NM_LAST_A
    clipped = record(lambda f: optimize.minimize(f, start, method="Nelder-Mead", bounds=zero_box))
    assert len(clipped) == 15
    assert all(np.array_equal(a, b) for a, b in zip(clipped[:12], nelder[:12], strict=True))
    assert [p[1] for p in clipped[12:]] == [0.0, 0.0, 0.0]
    corner = record(lambda f: optimize.minimize(f, start, method="L-BFGS-B", bounds=zero_box))
    assert len(corner) == 4 and list(corner[-1]) == [0.01, 0.0]
    iterates = [np.array(start)]
    lbfgsb = record(
        lambda f: optimize.minimize(
            f,
            start,
            method="L-BFGS-B",
            bounds=box,
            callback=lambda xk: iterates.append(np.array(xk)),
        )
    )
    assert len(lbfgsb) == 54 and len(iterates) == 10
    roles, seen, accepted = [], [], 1
    for index, point in enumerate(lbfgsb):
        if index % 3:
            shift = point - lbfgsb[index - index % 3]
            assert np.count_nonzero(shift) == 1 and np.max(np.abs(shift)) <= 1.0001e-8
            continue
        if not roles:
            roles.append("s")
        elif any(np.array_equal(point, x) for x in seen):
            roles.append("r")
        elif accepted < len(iterates) and np.array_equal(point, iterates[accepted]):
            roles.append("a")
            accepted += 1
        else:
            roles.append("t")
        seen.append(point)
    assert "".join(roles) == EVAL_LBFGSB_ROLES
    assert list(lbfgsb[3]) == [1e-3, 1e-5]
    # Points 17 and 18 agree to 3 digits; point 16 does not.
    assert {(round(p[0], 6), round(p[1], 6)) for p in lbfgsb[48::3]} == {(0.000401, 0.000501)}
    assert round(lbfgsb[45][1], 6) != 0.000501
    # The clipped simplex collapses onto q = 1e-5 although increasing q still lowers the fit.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        collapsed = optimize.minimize(tool, start, method="Nelder-Mead", bounds=box)
    assert collapsed.success and (collapsed.nit, collapsed.nfev) == (16, 31)
    assert np.allclose(collapsed.final_simplex[0][:, 1], 1e-5, rtol=0, atol=1e-15)
    corner_q = collapsed.x + [0.0, 1e-8]
    slope_q = (sse(corner_q, 1e-10) - sse(collapsed.x - [0.0, 1e-8], 1e-10)) / 2e-8
    assert round(slope_q, -1) == -350
    assert round(collapsed.fun / sse(lbfgsb[-3], 1e-3)) == 149
    # With Radau, a tighter ODE tolerance leaves the L-BFGS-B counts unchanged.
    tight = optimize.minimize(lambda x: sse(x, 1e-8), start, method="L-BFGS-B", bounds=box)
    assert (tight.nit, tight.nfev) == (9, 54)
    # Rescaled to 1e4 a and 1e4 q, BFGS never passes a negative value and reaches the fit.
    scaled = record(lambda f: optimize.minimize(lambda z: f(np.asarray(z) * 1e-4), [1.0, 1.0]))
    # The evaluation count depends on the BLAS kernel (57 or 66); the path and answer do not.
    assert min(min(p) for p in scaled) > 0
    assert np.allclose(scaled[-1], [0.000401, 0.000501], rtol=0, atol=1e-6)
    assert [round(v, 6) for v in scaled[3]] == [0.000198, 0.000075]


def test_solver_evaluation_article_python_prints_its_comments() -> None:
    import contextlib
    import io
    import warnings

    import pytest

    pytest.importorskip("scipy.optimize")
    code = _solver_evaluation_article_code()
    expected = [line[len("# → ") :] for line in code.splitlines() if line.startswith("# → ")]
    output = io.StringIO()
    with warnings.catch_warnings(), contextlib.redirect_stdout(output):
        warnings.simplefilter("ignore", RuntimeWarning)
        exec(compile(code, "solver-evaluation-points.md", "exec"), {})
    assert output.getvalue().splitlines() == expected
