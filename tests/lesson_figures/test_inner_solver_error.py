from __future__ import annotations

from scripts.lesson_figures.inner_solver_error import FIGURES

from .article_python import article_setup, assert_article_prints_its_comments


def test_inner_solver_figure_uses_the_article_numbers() -> None:
    from scripts.lesson_figures.inner_solver_error import (
        INNER_E,
        INNER_JUMPS,
        INNER_RUNS,
        inner_samples,
    )

    samples = inner_samples()
    assert len(samples) == len(INNER_E) == 181
    assert round(samples[-1][0], 9) == 0.00049
    assert [count for count, _ in INNER_RUNS] == [50, 62, 68, 74, 80, 86]
    assert (round(min(INNER_E) * 1e-5, 5), round(max(INNER_E) * 1e-5, 5)) == (-0.00024, 0.00009)
    # The answer a = 0.000401 lies inside the 68-evaluation range, and near it the offset
    # grows by about 1.6e-6 for each 1e-6 of a.
    answer = next(s for s in samples if round(s[0], 9) == 0.000401)
    assert answer[2] == 68
    assert round((INNER_E[92] - INNER_E[90]) / 2, 2) == 0.16  # 0.16e-5 per 1e-6 of a
    for jump_a, _ in INNER_JUMPS:
        before = max(s for s in samples if s[0] < jump_a)
        after = min(s for s in samples if s[0] > jump_a)
        assert before[2] != after[2]
    steps = FIGURES["inner-solver-steps.svg"]()
    for text in ("段差 −6.79", "段差 −1.23", "答え"):
        assert text in steps


def test_inner_solver_steps_match_a_scipy_rerun() -> None:
    import pytest

    np = pytest.importorskip("numpy")
    pytest.importorskip("scipy.integrate")
    from scripts.lesson_figures.inner_solver_error import INNER_JUMPS, INNER_Q, inner_samples

    space = article_setup("inner-solver-error", "x0 = [1e-4")
    simulate, tool, model = space["simulate"], space["tool"], space["model"]
    for a, error, count in inner_samples():
        sol = simulate(a, INNER_Q, "RK45")
        assert sol.nfev == count
        assert abs((tool([a, INNER_Q], "RK45") - model([a, INNER_Q])) * 1e5 - error) < 0.01
    for jump_a, jump in INNER_JUMPS:
        low, high = jump_a - 5e-13, jump_a + 5e-13
        assert simulate(low, INNER_Q, "RK45").nfev < simulate(high, INNER_Q, "RK45").nfev
        change = tool([high, INNER_Q], "RK45") - tool([low, INNER_Q], "RK45")
        assert round(change, 7) == jump
    # At the other three count changes the result bends but does not jump.
    for a in (0.0003524915843, 0.0004169641882, 0.0004618028082):
        low, high = a - 5e-13, a + 5e-13
        assert simulate(low, INNER_Q, "RK45").nfev != simulate(high, INNER_Q, "RK45").nfev
        assert abs(tool([high, INNER_Q], "RK45") - tool([low, INNER_Q], "RK45")) < 1e-7
    # The initial point's value differs between BLAS kernels only from about the 14th digit.
    assert np.isclose(tool([1e-4, 1e-4], "RK45"), 4.66189639906857, rtol=1e-13, atol=0)


def test_inner_solver_article_python_prints_its_comments() -> None:
    assert_article_prints_its_comments("inner-solver-error")
