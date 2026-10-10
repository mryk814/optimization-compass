from __future__ import annotations

import math
import re
from pathlib import Path
from xml.etree import ElementTree

from scripts.generate_lesson_figures import (
    OUTPUT,
    WIDTH,
    generate_lesson_figures,
    hpo_search_data,
    inverse_problem_curve,
    lasso_lambda_max,
    lasso_solution,
    lasso_zero_points,
    least_squares_fit,
    least_squares_sse,
    miqp_big_m_rows,
    miqp_enumerate,
    miqp_relaxation,
    mpc_wall_data,
    ridge_solution,
    vrp_data,
)

ROOT = Path(__file__).parents[1]
SVG = "{http://www.w3.org/2000/svg}"


def test_least_squares_figures_use_the_article_numbers() -> None:
    x1, x2, sse = least_squares_fit()
    assert (round(x1, 6), round(x2, 6), round(sse, 6)) == (0.9, 0.9, 0.7)
    assert round(least_squares_sse(0.5, 1.3), 6) == 1.66
    figures = generate_lesson_figures()
    assert "この直線では合計 0.70" in figures["least-squares-residuals.svg"]
    assert "二乗和 1.66" in figures["least-squares-contours.svg"]
    assert figures["least-squares-minimum.svg"].count("0.9 で最小 0.70") == 2


def test_inverse_problem_figure_uses_the_article_numbers() -> None:
    alpha, error, curve = inverse_problem_curve()
    assert f"{alpha:.2e}" == "7.25e-04"
    assert round(error, 4) == 0.0199
    by_exponent = dict(curve)
    assert round(by_exponent[-10.0], 1) == 43.9
    assert round(by_exponent[-3.0], 4) == 0.0182
    assert round(by_exponent[0.0], 2) == 0.61
    assert "α=7.25e-04" in generate_lesson_figures()["inverse-problem-alpha.svg"]


def test_l1_path_figure_uses_the_article_numbers() -> None:
    assert round(lasso_lambda_max(), 2) == 18.96
    assert [round(value, 1) for value in lasso_zero_points()] == [19.0, 12.6, 7.2, 4.8]
    assert [round(value, 2) for value in lasso_solution(10.0)] == [0.74, -0.21, 0.0, 0.0]
    assert [round(value, 2) for value in lasso_solution(0.0)] == [1.77, -1.18, -0.9, 0.21]
    assert [round(value, 2) for value in ridge_solution(10.0)] == [0.88, -0.61, -0.29, 0.25]
    assert all(value != 0.0 for value in ridge_solution(20.0))
    figure = generate_lesson_figures()["l1-sparse-regularization-path.svg"]
    assert "階数は4.8、徒歩は7.2、築年数は12.6、面積は19.0で0になります" in figure
    assert "stroke-dasharray" not in figure


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
    figure = generate_lesson_figures()["mpc-wall-receding.svg"]
    assert "位置が-0.90まで進んで壁を越えます" in figure
    assert "最小の位置は0.019で、壁を越えません" in figure
    assert "stroke-dasharray" not in figure


def test_vrp_figures_use_the_article_numbers() -> None:
    data = vrp_data()
    assert data["split_count"] == 22
    assert round(data["optimum"], 3) == 35.527  # type: ignore[arg-type]
    assert data["optimum_routes"] == [[3, 1, 4, 6], [2, 7, 5]]
    assert round(data["nearest"], 3) == 39.616  # type: ignore[arg-type]
    assert data["nearest_routes"] == [[4, 6, 7, 5], [3, 1, 2]]
    assert round(data["heuristic"], 3) == 38.508  # type: ignore[arg-type]
    assert data["heuristic_routes"] == [[4, 5, 7, 6], [1, 3, 2]]
    assert round(data["degree_cost"], 3) == 28.389  # type: ignore[arg-type]
    assert data["degree_routes"] == [[4], [6]]
    assert data["degree_loops"] == [[1, 3], [2, 5, 7]]
    figures = generate_lesson_figures()
    assert "最近傍法と2-optの結果は38.508、全探索の最適は35.527" in figures["vrp-routes.svg"]
    assert "費用28.389の解が選ばれます" in figures["vrp-subtour.svg"]
    assert "輪が2つ残り" in figures["vrp-subtour.svg"]
    assert "stroke-dasharray" not in figures["vrp-routes.svg"] + figures["vrp-subtour.svg"]


def test_miqp_figure_uses_the_article_numbers() -> None:
    found = miqp_enumerate()
    assert len(found) == 10
    total, subset, weights = found[0]
    assert (round(total, 2), subset) == (120.75, (0, 3, 4))
    assert [round(value, 3) for value in weights] == [0.55, 0.252, 0.198]
    assert [
        (round(value, 2), "".join("ABCDE"[i] for i in sub)) for value, sub, _ in found[1:3]
    ] == [
        (125.73, "ACE"),
        (129.75, "ACD"),
    ]
    by_subset = {sub: round(value, 2) for value, sub, _ in found}
    assert by_subset[(0, 4)] == 146.0  # A=0.6, E=0.4: 36 + 100 + 2 * 5
    bounds = {label: round(bound, 2) for label, bound, _, _ in miqp_big_m_rows()}
    assert list(bounds.values()) == [102.41, 97.09, 92.59, 92.14, 104.59]
    value, weights = miqp_relaxation((1.0,) * 5)
    assert round(value, 2) == 97.09 and round(sum(weights), 6) == 1.0
    assert round(miqp_big_m_rows()[-1][2], 2) == 125.78
    figure = generate_lesson_figures()["miqp-big-m-bound.svg"]
    assert "M ＝ 100では下界92.14、最適値120.75" in figure
    assert "stroke-dasharray" not in figure


def test_hpo_search_figure_uses_the_article_numbers() -> None:
    data = hpo_search_data()
    grid, rand = data["grid"], data["random"]
    assert (grid["distinct_lam"], grid["distinct_degree"]) == (4, 4)
    assert (rand["distinct_lam"], rand["distinct_degree"]) == (16, 11)
    grid_d, grid_lam = grid["configs"][grid["best"]]
    rand_d, rand_lam = rand["configs"][rand["best"]]
    assert round(grid["values"][grid["best"]], 3) == 0.192
    assert (grid_d, round(math.log10(grid_lam), 2)) == (6, -3.67)
    assert round(rand["values"][rand["best"]], 3) == 0.144
    assert (rand_d, round(math.log10(rand_lam), 2)) == (3, -1.67)
    assert round(data["terrain"][(3, 2)], 3) == 0.137  # degree 3 at log10 lambda = -4.75
    figure = generate_lesson_figures()["hpo-search-points.svg"]
    assert "格子ではlog10 λの値が4種類、ランダムでは16種類" in figure
    assert "格子が0.192、ランダムが0.144" in figure
    assert "stroke-dasharray" not in figure


def test_lesson_figures_are_current_and_drawn_at_their_display_width() -> None:
    for name, body in generate_lesson_figures().items():
        assert body == generate_lesson_figures()[name]
        assert (OUTPUT / name).read_text(encoding="utf-8") == body, f"regenerate {name}"
        root = ElementTree.fromstring(body)
        assert root.attrib["width"] == str(WIDTH)
        assert root.attrib["viewBox"].split()[2] == str(WIDTH)
        assert root.find(f"{SVG}title").text and root.find(f"{SVG}desc").text
        # One SVG unit is one CSS pixel on a PC: text stays between tick and body size.
        sizes = [float(size) for size in re.findall(r"font-size:(\d+(?:\.\d+)?)px", body)]
        assert sizes and min(sizes) >= 15 and max(sizes) <= 17


def test_lesson_figures_are_referenced_by_content() -> None:
    corpus = "".join(path.read_text(encoding="utf-8") for path in ROOT.glob("content/**/*.md"))
    for name in generate_lesson_figures():
        assert f"./figures/{name}" in corpus
