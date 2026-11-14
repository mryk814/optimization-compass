from __future__ import annotations

from scripts.lesson_figures.high_dimensional_black_box import FIGURES


def test_high_dimensional_black_box_figure_uses_the_article_numbers() -> None:
    from scripts.lesson_figures.high_dimensional_black_box import (
        _pa015_expected_hits,
        _pa015_search_data,
        _pa015_typical_score,
    )

    # Expected number of the 200 points inside the small box 0.5 <= every knob <= 0.7.
    assert [round(_pa015_expected_hits(n), 4) for n in (1, 2, 3, 4, 5, 6)] == [
        40.0,
        8.0,
        1.6,
        0.32,
        0.064,
        0.0128,
    ]
    assert round(_pa015_typical_score(), 4) == 0.0933
    # Median over 200 repetitions (seed 0) of the best score among 200 random points.
    search = _pa015_search_data()
    assert [round(search[n]["all"], 4) for n in (2, 5, 10, 20, 50)] == [
        0.0005,
        0.0109,
        0.0269,
        0.0429,
        0.0601,
    ]
    assert [round(search[n]["two"], 4) for n in (2, 5, 10, 20, 50)] == [
        0.0005,
        0.0006,
        0.0005,
        0.0005,
        0.0006,
    ]
    figure = FIGURES["high-dimensional-black-box-budget.svg"]()
    for text in ("① 小箱に入る点の期待数（200点中）", "② ランダム200点の最良スコア（中央値）"):
        assert text in figure
    for text in ("0.0128", "0.0109", "0.0601", "ランダムな1点の平均 0.093"):
        assert text in figure
