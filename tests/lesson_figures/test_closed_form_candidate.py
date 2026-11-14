from __future__ import annotations

from scripts.lesson_figures.closed_form_candidate import FIGURES


def test_closed_form_order_cost_figure_uses_the_article_numbers() -> None:
    from scripts.lesson_figures.closed_form_candidate import (
        _pa001_best_quantity,
        _pa001_cost,
        _pa001_holding,
        _pa001_ordering,
        _pa001_slope,
    )

    best = _pa001_best_quantity()
    assert (round(best, 6), round(_pa001_cost(best), 6)) == (600.0, 6000.0)
    assert (round(_pa001_ordering(best), 6), round(_pa001_holding(best), 6)) == (3000.0, 3000.0)
    assert abs(_pa001_slope(best)) < 1e-9
    assert [round(_pa001_cost(q), 6) for q in (300.0, 500.0, 800.0, 1200.0)] == [
        7500.0,
        6100.0,
        6250.0,
        7500.0,
    ]
    figure = FIGURES["closed-form-order-cost.svg"]()
    assert 'width="440"' in figure
    for text in (
        "Q=600",
        "最小の 6000 円",
        "発注費 KD/Q。Q=600 で 3000 円",
        "保管費 hQ/2。Q=600 で 3000 円",
    ):
        assert text in figure
    assert "stroke-dasharray" not in figure
