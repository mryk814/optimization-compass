from __future__ import annotations

from scripts.lesson_figures.model_predictive_control import FIGURES, mpc_wall_data


def test_mpc_wall_figure_uses_the_article_numbers() -> None:
    data = mpc_wall_data()
    assert [round(value, 3) for value in data["model"][:5]] == [3.0, 2.5, 1.229, 0.187, 0.0]
    assert round(data["open_loop"][-1], 2) == -0.9
    assert round(min(data["open_loop"]), 2) == -0.9
    assert round(min(data["receding"]), 3) == 0.019
    assert [
        round(value, 3) for value in (data["receding"][-1], *data["receding_velocity_end"])
    ] == [
        0.023,
        -0.115,
    ]
    figure = FIGURES["mpc-wall-receding.svg"]()
    assert "位置が-0.90まで進んで壁を越えます" in figure
    assert "最小の位置は0.019で、壁を越えません" in figure
    assert "stroke-dasharray" not in figure
