from __future__ import annotations

import math

from scripts.lesson_figures.trajectory_optimization import FIGURES


def test_trajectory_figures_use_the_article_numbers() -> None:
    from scripts.lesson_figures.trajectory_optimization import (
        TRAJ_RADIUS,
        traj_clearance,
        traj_path,
        traj_solve,
        traj_states,
    )

    assert [round(traj_solve(n)[0], 2) for n in (5, 10, 20, 40)] == [3.34, 3.81, 3.77, 3.75]
    assert round(traj_solve(20, -1.0)[0], 2) == 6.67
    top = max(y for _, y, _, _ in traj_states(20))
    assert math.isclose(top, 0.5, abs_tol=1e-6)
    # Every grid point of the 5-interval answer is outside the pillar, the path between is not.
    assert min(math.hypot(x - 2.0, y + 0.3) for x, y, _, _ in traj_states(5)) > TRAJ_RADIUS - 1e-6
    assert round(traj_clearance(traj_path(5, samples=400)), 3) == 0.536
    assert traj_clearance(traj_path(20, samples=400)) > TRAJ_RADIUS - 1e-6
    paths = FIGURES["trajectory-pillar-paths.svg"]()
    for text in ("上を回る：3.77", "下を回る：6.67"):
        assert text in paths
    grid = FIGURES["trajectory-grid-check.svg"]()
    for text in ("最大26cm", "3.34", "3.81", "3.77", "3.75"):
        assert text in grid
