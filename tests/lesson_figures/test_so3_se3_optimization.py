from __future__ import annotations

from scripts.lesson_figures.so3_se3_optimization import FIGURES, so3_paths, so3_rotation_minimum


def test_so3_figure_uses_the_article_numbers() -> None:
    rows = so3_paths()
    best = so3_rotation_minimum()
    assert round(best, 3) == 1.646
    # The nine-entry path flips to a mirror image on the first step, then undercuts the minimum.
    assert [row["k"] for row in rows if row["ambient_det"] < 0][0] == 1
    assert round(rows[1]["ambient_orth"], 3) == 1.084
    assert round(rows[1]["ambient_det"], 2) == -0.19
    assert next(row["k"] for row in rows if row["ambient_f"] < best) == 27
    assert round(rows[27]["ambient_f"], 3) == 1.612
    assert round(rows[-1]["ambient_f"], 3) == 0.077
    assert round(rows[-1]["ambient_orth"], 3) == 0.169
    # The rotation path never leaves SO(3) and stays at or above the rotation minimum.
    assert max(row["rotation_orth"] for row in rows) < 1e-14
    assert round(rows[20]["rotation_f"], 3) == 1.670
    assert min(row["rotation_f"] for row in rows) >= best - 1e-6
    figure = FIGURES["so3-rotation-paths.svg"]()
    for text in (
        "回転での最小 1.646",
        "k=1：行列式 −0.19（鏡像）",
        "k=27で回転での最小1.646を下回り",
    ):
        assert text in figure
