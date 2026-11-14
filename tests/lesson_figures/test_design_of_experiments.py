from __future__ import annotations

from scripts.lesson_figures.design_of_experiments import FIGURES


def test_design_of_experiments_figures_use_the_article_numbers() -> None:
    from scripts.lesson_figures._numeric import _det3
    from scripts.lesson_figures.design_of_experiments import (
        DOE_DESIGNS,
        DOE_ENDS,
        doe_frank_wolfe,
        doe_information,
        doe_variance,
    )

    dets = [round(_det3(doe_information(xs)), 3) for _, xs, _ in DOE_DESIGNS]
    assert dets == [16.056, 0.131, 32.0]
    assert abs(_det3(doe_information(DOE_ENDS))) < 1e-9
    grid = [i / 100 for i in range(-100, 101)]
    worst = [
        round(max(doe_variance(doe_information(xs), x) for x in grid), 2)
        for _, xs, _ in DOE_DESIGNS
    ]
    assert worst == [0.82, 25.11, 0.5]
    history = doe_frank_wolfe()
    assert [round(history[k][1], 4) for k in (10, 100, 1000)] == [0.4068, 0.0558, 0.0059]
    assert round(sum(history[1000][0][i] for i in (0, 10, 20)), 3) == 0.996
    designs = FIGURES["doe-designs-variance.svg"]()
    for text in ("等間隔：最大 0.82", "中央付近：両端で 25", "最大 0.50"):
        assert text in designs
    weights = FIGURES["doe-weights-gap.svg"]()
    for text in ("1000回", "0.996", "0.407"):
        assert text in weights
