from __future__ import annotations

from scripts.lesson_figures.shape_dependent_domain import (
    FIGURES,
    FIN_LENGTHS,
    fin_objective,
    fin_temperature,
)


def test_fin_length_figure_uses_the_article_numbers() -> None:
    lengths = [round(length, 3) for length in FIN_LENGTHS]
    assert lengths == [1.0, 1.317, 2.063]
    assert [round(fin_temperature(x, x), 3) for x in FIN_LENGTHS] == [0.648, 0.5, 0.25]
    assert [round(fin_temperature(x, 0.5), 3) for x in FIN_LENGTHS] == [0.731, 0.676, 0.623]
    assert [round(fin_objective(x), 3) for x in FIN_LENGTHS] == [-0.512, -0.537, -0.452]
    figure = FIGURES["shape-fin-length.svg"]()
    assert "L=1.317：先端 0.500、間隔 0.329" in figure
    assert "最小 J=−0.537（L=1.317）" in figure
