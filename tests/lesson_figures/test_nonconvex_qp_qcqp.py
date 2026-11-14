from __future__ import annotations

from scripts.lesson_figures.nonconvex_qp_qcqp import (
    FIGURES,
    ncqp_basins,
    ncqp_projected_gradient,
    ncqp_starts,
    ncqp_value,
)


def test_nonconvex_qp_figure_uses_the_article_numbers() -> None:
    # Local minima at the corners (-1, -1) and (1, 1); (0.5, 0.5) is a saddle.
    assert (ncqp_value(-1, -1), ncqp_value(1, 1), ncqp_value(1, -1), ncqp_value(-1, 1)) == (
        -2,
        0,
        5,
        5,
    )
    assert round(ncqp_value(0.5, 0.5), 6) == 0.25
    assert ncqp_projected_gradient((0.9, 0.2)) == (1.0, 1.0)
    assert ncqp_projected_gradient((0.3, 0.3)) == (-1.0, -1.0)
    basins = ncqp_basins()
    assert (len(basins["low"]), len(basins["high"]), basins["other"]) == (316, 45, 0)
    # The basin boundary is the straight line x1 + x2 = 1, which passes through the saddle.
    assert all((a + b > 1) == ((a, b) in basins["high"]) for a, b in ncqp_starts())
    figure = FIGURES["nonconvex-qp-basins.svg"]()
    for text in ("局所解 f=-2", "局所解 f=0", "鞍点 f=0.25", "緑の丸 316点", "橙の四角 45点"):
        assert text in figure
