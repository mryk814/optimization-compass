from __future__ import annotations

import math
import re
from pathlib import Path
from xml.etree import ElementTree

from scripts.generate_lesson_figures import (
    FIN_LENGTHS,
    MILP_NODES,
    OUTPUT,
    WIDTH,
    box_gradient,
    box_solution,
    box_unconstrained_minimum,
    box_value,
    composite_objective,
    composite_solution,
    composite_step,
    dryer_compass,
    dryer_value,
    fin_objective,
    fin_temperature,
    generate_lesson_figures,
    hpo_search_data,
    inverse_problem_curve,
    lasso_lambda_max,
    lasso_solution,
    lasso_zero_points,
    lcp_contact_data,
    least_squares_fit,
    least_squares_sse,
    milp_integer_points,
    milp_relaxation,
    minlp_interval_min,
    minlp_value,
    miqp_big_m_rows,
    miqp_enumerate,
    miqp_relaxation,
    mpc_wall_data,
    ncqp_basins,
    ncqp_projected_gradient,
    ncqp_starts,
    ncqp_value,
    pa007_runs,
    ridge_solution,
    so3_paths,
    so3_rotation_minimum,
    socp_center,
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


def test_fin_length_figure_uses_the_article_numbers() -> None:
    lengths = [round(length, 3) for length in FIN_LENGTHS]
    assert lengths == [1.0, 1.317, 2.063]
    assert [round(fin_temperature(x, x), 3) for x in FIN_LENGTHS] == [0.648, 0.5, 0.25]
    assert [round(fin_temperature(x, 0.5), 3) for x in FIN_LENGTHS] == [0.731, 0.676, 0.623]
    assert [round(fin_objective(x), 3) for x in FIN_LENGTHS] == [-0.512, -0.537, -0.452]
    figure = generate_lesson_figures()["shape-fin-length.svg"]
    assert "L=1.317：先端 0.500、間隔 0.329" in figure
    assert "最小 J=−0.537（L=1.317）" in figure


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


def test_robust_regression_figure_uses_the_article_numbers() -> None:
    from scripts.generate_lesson_figures import robust_fit

    squared_x, squared = robust_fit(None)
    huber_x, huber = robust_fit(1.0)
    assert round(squared_x, 9) == 2.5
    assert [round(value, 9) for value in squared] == [2.5, 2.5, 2.5, -7.5]
    assert round(huber_x, 9) == round(1 / 3, 9)
    assert [round(value, 9) for value in huber] == [round(1 / 3, 9)] * 3 + [-1.0]
    assert abs(sum(squared)) < 1e-9 and abs(sum(huber)) < 1e-9
    assert "Huberの解 x=1/3" in generate_lesson_figures()["robust-regression-huber.svg"]


def test_stochastic_erm_figure_uses_the_article_numbers() -> None:
    from scripts.generate_lesson_figures import erm_minibatch_data

    data = erm_minibatch_data()
    w0, w1 = data["minimiser"]
    assert (round(w0, 3), round(w1, 3)) == (-0.832, 1.678)
    start, minimum = data["start"], data["minimum"]
    assert [round(value, 4) for value in start["full"]] == [0.1446, -0.2802]
    assert (round(start["rms"], 3), start["same"]) == (0.114, 200)
    assert round(minimum["rms"], 3) == 0.083
    figure = generate_lesson_figures()["stochastic-erm-minibatch.svg"]
    assert "200本のうち200本が灰の線の同じ側" in figure
    assert "32件の勾配はRMS 0.083" in figure
    assert "stroke-dasharray" not in figure


def test_milp_tree_figure_uses_the_article_numbers() -> None:
    from fractions import Fraction

    points = milp_integer_points()
    assert len(points) == 13
    assert max(points, key=lambda p: 5 * p[0] + 4 * p[1]) == (4, 0)
    solved = {name: milp_relaxation(extra) for name, _, extra in MILP_NODES}
    expected = {
        "root": ((Fraction(3), Fraction(3, 2)), Fraction(21)),
        "left": ((Fraction(10, 3), Fraction(1)), Fraction(62, 3)),
        "left_left": ((Fraction(3), Fraction(1)), Fraction(19)),
        "left_right": ((Fraction(4), Fraction(0)), Fraction(20)),
        "right": ((Fraction(2), Fraction(2)), Fraction(18)),
    }
    assert solved == expected
    # Both leaves that give a final answer are integer points, and 19, 20, 18 never exceed 20.
    assert max(solved[n][1] for n in ("left_left", "left_right", "right")) == 20
    figure = generate_lesson_figures()["milp-relaxation-tree.svg"]
    for text in ("(10/3, 1)", "上界 62/3", "(3, 1.5)", "値 19", "値 20", "上界 18"):
        assert text in figure
    assert "stroke-dasharray" not in figure


def test_bound_constrained_box_figure_uses_the_article_numbers() -> None:
    free = box_unconstrained_minimum()
    assert (free, box_value(*free)) == ((2.0, 0.0), 2.0)
    assert box_value(1.0, 0.0) == 3.0
    x1, x2 = box_solution()
    assert (round(x1, 6), round(x2, 6), round(box_value(x1, x2), 6)) == (1.0, 0.5, 2.5)
    assert tuple(round(g, 6) for g in box_gradient(x1, x2)) == (-1.0, 0.0)
    figure = generate_lesson_figures()["bound-constrained-box.svg"]
    for text in ("(1, 0.5)", "f = 2.5", "f = 3", "f = 2"):
        assert text in figure


def test_socp_relay_figure_uses_the_article_numbers() -> None:
    from fractions import Fraction

    centre, weights = socp_center()
    assert centre == (Fraction(3), Fraction(1))
    assert weights == (Fraction(1, 3), Fraction(5, 12), Fraction(1, 4))
    # All three villages are at distance sqrt(10) from the centre, and the weights are positive.
    for vx, vy in ((0, 0), (6, 0), (2, 4)):
        assert (vx - 3) ** 2 + (vy - 1) ** 2 == 10
    figure = generate_lesson_figures()["socp-relay-station.svg"]
    for text in ("半径 3.6 km", "3.162 km", "Bまで 3.590 km", "(3, 1)", "5/12", "1/4", "1/3"):
        assert text in figure


def test_network_flow_figure_uses_the_article_numbers() -> None:
    from scripts.generate_lesson_figures import flow_cost, flow_successive_paths

    pushes = flow_successive_paths()
    assert [(path, cost, sent) for path, cost, sent, _ in pushes] == [
        ("S→A→B→T", 3, 3),
        ("S→B→A→T", 8, 1),
    ]
    final = pushes[-1][3]
    assert final == {("S", "A"): 3, ("S", "B"): 1, ("A", "B"): 2, ("A", "T"): 1, ("B", "T"): 3}
    assert flow_cost(pushes[0][3]) == 9 and flow_cost(final) == 17
    # Without reverse arcs the greedy run stops after three boxes.
    stuck = flow_successive_paths(use_reverse=False)
    assert sum(sent for _, _, sent, _ in stuck) == 3
    figure = generate_lesson_figures()["network-flow-paths.svg"]
    for text in ("費用 9", "費用 17", "4−1+5=8", "3/3（満杯）"):
        assert text in figure
    assert "stroke-dasharray" not in figure


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
    figure = generate_lesson_figures()["so3-rotation-paths.svg"]
    for text in (
        "回転での最小 1.646",
        "k=1：行列式 −0.19（鏡像）",
        "k=27で回転での最小1.646を下回り",
    ):
        assert text in figure


def test_neural_network_figure_uses_the_article_numbers() -> None:
    from scripts.generate_lesson_figures import (
        NN_START_A,
        NN_START_B,
        nn_gradient,
        nn_loss,
        nn_minimum,
        nn_path,
    )

    wu, wv = nn_minimum()
    assert (round(wu, 4), round(wv, 4)) == (0.7041, 1.0709)
    assert round(nn_loss(wu, wv), 6) == 0.0025
    assert round(nn_loss(0.0, 0.0), 6) == 0.665
    assert nn_gradient(0.0, 0.0) == (0.0, 0.0)
    assert round(nn_loss(*NN_START_A), 4) == 0.8124
    first = nn_path(NN_START_A, 1)[1]
    assert (round(first[0], 4), round(first[1], 4)) == (0.0847, 0.1871)
    assert nn_path(NN_START_A, 400)[-1][0] > 0 > nn_path(NN_START_B, 400)[-1][0]
    figure = generate_lesson_figures()["nn-training-two-valleys.svg"]
    for text in ("中点 0.665", "両端の損失 0.0025", "w*=(0.70, 1.07)"):
        assert text in figure


def test_composite_group_figure_uses_the_article_numbers() -> None:
    v, moved = composite_step([0.0] * 4)
    assert [round(value, 4) for value in v] == [0.85, 0.55, 0.3, 0.25]
    assert [round(value, 4) for value in moved] == [0.4722, 0.3055, 0.0, 0.0]
    assert round(math.hypot(v[0], v[1]), 3) == 1.012
    assert round(math.hypot(v[2], v[3]), 3) == 0.391
    x, count = composite_solution()
    assert count == 34
    assert [round(value, 4) for value in x] == [0.8145, 0.5026, 0.0, 0.0]
    assert round(composite_objective(x), 4) == 12.1193
    assert round(composite_objective([0.0] * 4), 1) == 17.5
    figure = generate_lesson_figures()["composite-group-shrink.svg"]
    for text in (
        "(0.85, 0.55)",
        "長さ 1.012 &gt; 0.45",
        "→ (0.472, 0.306)",
        "→ (0, 0)",
        "長さ 0.391 ≤ 0.45",
    ):
        assert text in figure


def test_discontinuous_dryer_figure_uses_the_article_numbers() -> None:
    assert dryer_value(0.55) == 0.325
    assert round(0.40 + 2.0 * (0.55 - 0.25) ** 2, 6) == 0.58
    assert (round(dryer_value(0.25), 6), round(dryer_value(0.80), 6)) == (0.4, 0.2)
    assert round(dryer_value(0.10), 6) == 0.445
    assert dryer_value(0.3) == dryer_value(0.3)
    left = dryer_compass(0.10, 0.4)
    right = dryer_compass(0.10, 0.5)
    assert (round(left[0], 3), round(left[1], 3), left[2]) == (0.25, 0.4, 27)
    assert (round(right[0], 3), round(right[1], 3), right[2]) == (0.8, 0.2, 35)
    figure = generate_lesson_figures()["discontinuous-dryer-cliff.svg"]
    for text in ("F(0.55) = 0.325", "0.58", "F = 0.445", "F = 0.4", "F = 0.2", "段差 −0.255"):
        assert text in figure


def test_noisy_black_box_figure_uses_the_article_numbers() -> None:
    from scripts.generate_lesson_figures import (
        oven_figure_data,
        oven_reversal,
        oven_spread,
        oven_true_score,
    )

    once, five = oven_figure_data()
    assert (once["k"], once["n"], five["k"], five["n"]) == (60, 1, 12, 5)
    assert round(once["xs"][once["best"]], 3) == 0.508
    assert round(once["means"][once["best"]], 3) == -0.38
    assert round(once["true_at_best"], 3) == 0.017
    assert round(five["xs"][five["best"]], 3) == 0.625
    assert round(five["means"][five["best"]], 3) == -0.077
    assert round(five["true_at_best"], 3) == 0.001
    # The true score is never negative, so a reported -0.380 cannot be real.
    assert min(oven_true_score(i / 100) for i in range(101)) == 0.0
    # Probability that n-bake means order two temperatures the wrong way round.
    assert [round(oven_reversal(n, 0.02), 3) for n in (1, 5)] == [0.472, 0.437]
    assert [round(oven_reversal(n, 0.08), 3) for n in (1, 5)] == [0.389, 0.264]
    assert [round(oven_reversal(n, 0.32), 3) for n in (1, 5)] == [0.129, 0.006]
    # Repeating the whole procedure 2000 times: the reported minimum is optimistic.
    for k, chosen, optimism in ((60, 0.041, -0.422), (12, 0.025, -0.109), (4, 0.010, -0.013)):
        got_chosen, got_optimism = oven_spread(k)
        assert (round(got_chosen, 3), round(got_optimism, 3)) == (chosen, optimism)
    figure = generate_lesson_figures()["noisy-black-box-budget.svg"]
    for text in ("① 60温度を1回ずつ", "② 12温度を5回ずつ", "最良の観測 −0.380、真の点数 0.017"):
        assert text in figure
    assert "最良の平均 −0.077、真の点数 0.001" in figure
    assert "stroke-dasharray" not in figure


def test_high_dimensional_black_box_figure_uses_the_article_numbers() -> None:
    from scripts.generate_lesson_figures import (
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
    figure = generate_lesson_figures()["high-dimensional-black-box-budget.svg"]
    for text in ("① 小箱に入る点の期待数（200点中）", "② ランダム200点の最良スコア（中央値）"):
        assert text in figure
    for text in ("0.0128", "0.0109", "0.0601", "ランダムな1点の平均 0.093"):
        assert text in figure


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
    figure = generate_lesson_figures()["nonconvex-qp-basins.svg"]
    for text in ("局所解 f=-2", "局所解 f=0", "鞍点 f=0.25", "緑の丸 316点", "橙の四角 45点"):
        assert text in figure


def test_minlp_figure_uses_the_article_numbers() -> None:
    values = {n: round(minlp_value(n), 2) for n in range(1, 7)}
    assert values == {1: -7.44, 2: -14.88, 3: -22.32, 4: -29.76, 5: -30.0, 6: -27.33}
    relaxed_n, relaxed_value = minlp_interval_min(1.0, 6.0)
    assert round(relaxed_n, 3) == 4.167 and round(relaxed_value, 6) == -31.0
    assert round(relaxed_n) == 4 and min(values, key=values.get) == 5
    left_n, left_value = minlp_interval_min(1.0, 4.0)
    right_n, right_value = minlp_interval_min(5.0, 6.0)
    assert (round(left_n, 6), round(left_value, 2)) == (4.0, -29.76)
    assert (round(right_n, 6), round(right_value, 2)) == (5.0, -30.0)
    figure = generate_lesson_figures()["minlp-relaxation-branch.svg"]
    for text in (
        "緩和の最小：n=4.17、値 −31.0",
        "丸めた n=4：値 −29.76",
        "n≤4 の節点：n=4、値 −29.76",
        "n≥5 の節点：n=5、値 −30.0",
    ):
        assert text in figure
    assert "stroke-dasharray" not in figure


def test_shortest_path_figure_uses_the_article_numbers() -> None:
    from scripts.generate_lesson_figures import path_distances, path_routes, path_rules, path_total

    totals = sorted((path_total(route), "→".join(route)) for route in path_routes())
    assert totals == [(7, "S→B→C→T"), (8, "S→A→T"), (10, "S→A→B→C→T"), (12, "S→T")]
    dist, best = path_distances()
    assert dist == {"S": 0, "A": 2, "B": 4, "C": 5, "T": 7}
    assert best == ("S", "B", "C", "T")
    assert [(name, path_total(route)) for name, route in path_rules()] == [
        ("道の数が最少", 12),
        ("次の道が最安", 10),
        ("合計が最小", 7),
    ]
    figure = generate_lesson_figures()["shortest-path-routes.svg"]
    for text in ("d=7", "S→A→B→C→T（道4本）", "S→B→C→T（道3本）", "12分", "10分", "7分"):
        assert text in figure
    assert "stroke-dasharray" not in figure


def test_bilevel_figure_uses_the_article_numbers() -> None:
    from scripts.generate_lesson_figures import _bilevel_data

    data = _bilevel_data()
    assert (data["best_x"], data["best_y"], data["best_revenue"]) == (2.0, 2.0, 4.0)
    assert (data["assumed_at_max"], data["actual_at_max"]) == (18.0, 0.0)
    xs = data["xs"]
    assert [data["revenue"][xs.index(x)] for x in (0.0, 1.0, 2.0, 3.0, 4.0)] == [
        0.0,
        3.0,
        4.0,
        3.0,
        0.0,
    ]
    figure = generate_lesson_figures()["bilevel-pricing-response.svg"]
    assert "x=2 で y=2" in figure and "最大 4" in figure
    assert "stroke-dasharray" not in figure


def test_lcp_active_set_figure_uses_the_article_numbers() -> None:
    from fractions import Fraction

    rows = lcp_contact_data()
    assert [row["active"] for row in rows] == [(), (0,), (1,), (0, 1)]
    assert [row["ok"] for row in rows] == [False, False, False, True]
    assert rows[1]["z"] == [Fraction(1, 2), 0] and rows[1]["w"] == [0, -1]
    assert rows[2]["z"] == [0, Fraction(3, 4)] and rows[2]["w"] == [Fraction(-1, 4), 0]
    assert rows[3]["z"] == [Fraction(1, 6), Fraction(2, 3)] and rows[3]["w"] == [0, 0]
    figure = generate_lesson_figures()["complementarity-active-sets.svg"]
    for text in ("接触なし（w&lt;0）", "Aだけ（w&lt;0）", "Bだけ（w&lt;0）", "AとB（解）"):
        assert text in figure
    assert figure.count('fill="#b3532d"') == 1  # only the solution is drawn filled


def test_high_dimensional_smooth_figure_uses_the_article_numbers() -> None:
    runs = pa007_runs()
    counts = {name: (run["iterations"], len(run["history"])) for name, run in runs.items()}
    assert counts == {"GD": (5883, 5884), "CG": (151, 310), "L-BFGS": (144, 151)}
    for run in runs.values():
        assert round(run["f"], 6) == 0.047872
        assert run["history"][-1] <= 1e-6 < run["history"][-2]
    figure = generate_lesson_figures()["large-smooth-deblur.svg"]
    for text in ("全体の誤差 5.8%", "全体の誤差 2.2%", "5884回", "310回", "151回", "位置 180〜240"):
        assert text in figure


def test_pa007_milestones_use_first_inclusive_crossing() -> None:
    from scripts.generate_lesson_figures import pa007_milestones

    # Rebounds do not replace the first crossing; a skipped level shares its evaluation.
    history = [2.0, 1.0, 1.2, 0.08, 0.2, 0.0005]
    assert pa007_milestones(history) == [(2, 0), (4, -1), (6, -2), (6, -3)]
    assert pa007_milestones([]) == []
    assert pa007_milestones([2.0]) == []


def test_pa007_milestones_match_computed_runs() -> None:
    from scripts.generate_lesson_figures import pa007_milestones

    expected = {
        "GD": [2, 4, 12, 139, 2630, 4517, 5884],
        "CG": [4, 12, 17, 35, 144, 230, 310],
        "L-BFGS": [4, 4, 6, 17, 76, 114, 151],
    }
    for name, run in pa007_runs().items():
        milestones = pa007_milestones(run["history"])
        assert [evaluation for evaluation, _ in milestones] == expected[name]
        assert [exponent for _, exponent in milestones] == list(range(0, -7, -1))
        assert milestones[-1] == (len(run["history"]), -6)
        # A relative perturbation changes raw coordinates, but not these crossing events.
        for scale in (1 - 1e-4, 1 + 1e-4):
            assert pa007_milestones([value * scale for value in run["history"]]) == milestones
        for evaluation, exponent in milestones:
            threshold = 10.0**exponent
            assert run["history"][evaluation - 1] <= threshold
            assert all(value > threshold for value in run["history"][: evaluation - 1])


def test_closed_form_order_cost_figure_uses_the_article_numbers() -> None:
    from scripts.generate_lesson_figures import (
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
    figure = generate_lesson_figures()["closed-form-order-cost.svg"]
    assert 'width="440"' in figure
    for text in (
        "Q=600",
        "最小の 6000 円",
        "発注費 KD/Q。Q=600 で 3000 円",
        "保管費 hQ/2。Q=600 で 3000 円",
    ):
        assert text in figure
    assert "stroke-dasharray" not in figure


def test_general_nonsmooth_figure_uses_the_article_numbers() -> None:
    from scripts.generate_lesson_figures import (
        PA011_START,
        _pa011_clarke_derivative,
        _pa011_clarke_minimum,
        _pa011_compass,
        _pa011_cost,
        _pa011_descent,
        _pa011_gradient_norm,
        _pa011_slope,
    )

    assert round(_pa011_cost(*PA011_START), 6) == 5.48
    assert tuple(round(v, 6) for v in _pa011_slope(1.5001, 1.4999)) == (3.6, -2.4)
    assert tuple(round(v, 6) for v in _pa011_slope(1.4999, 1.5001)) == (-2.4, 3.6)
    # The valley x1 = x2 holds two valley bottoms and a concave kink between them.
    assert [round(_pa011_cost(t, t), 6) for t in (1.0, 2.0, 3.0)] == [0.2, 1.4, 0.6]
    assert round(_pa011_cost(1.5, 1.5), 6) == 0.8
    # Fixed-step gradient descent crosses the valley 14 times in 16 steps and never sees a
    # small gradient.
    path = _pa011_descent(iterations=200)
    gaps = [a - b for a, b in path[:17]]
    assert sum(gaps[i] * gaps[i + 1] < 0 for i in range(16)) == 14
    assert round(min(_pa011_gradient_norm(p) for p in path), 3) == 4.28
    assert round(min(_pa011_cost(*p) for p in path), 3) == 0.8
    assert [round(g, 6) for g in gaps[:5]] == [1.4, 0.8, 0.2, -0.4, 0.2]
    axes = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    both = [*axes, (1, 1), (-1, -1), (1, -1), (-1, 1)]
    for start, directions, expected in (
        (PA011_START, axes, ((1.2, 1.2), 0.44, 68)),
        (PA011_START, both, ((1.0, 1.0), 0.2, 168)),
        ((2.0, 2.0), axes, ((2.0, 2.0), 1.4, 53)),
        ((2.0, 2.0), both, ((3.0, 3.0), 0.6, 115)),
    ):
        point, value, calls = _pa011_compass(start, 0.5, directions)
        assert ((round(point[0], 3), round(point[1], 3)), round(value, 3), calls) == expected
    # The Clarke minimum is negative at a point with a descent direction, positive at the kinks.
    assert round(_pa011_clarke_minimum((1.5, 1.5)), 3) == -0.849
    assert round(_pa011_clarke_minimum((2.0, 2.0)), 3) == 0.566
    # The exact generalized derivative includes slopes from both sides of the concave kink.
    assert _pa011_clarke_derivative((2.0, 2.0), (1.0, 1.0)) == 1.2
    assert _pa011_clarke_derivative((2.0, 2.0), (-1.0, -1.0)) == 0.8
    assert _pa011_clarke_derivative((1.5, 1.5), (-1.0, -1.0)) == -1.2
    figure = generate_lesson_figures()["general-nonsmooth-kink-valley.svg"]
    for text in ("谷底 0.2", "谷底 0.6", "山 1.4", "費用 5.48", "一歩 0.1"):
        assert text in figure


def test_general_nonsmooth_article_python_is_executable() -> None:
    article = (ROOT / "content/concepts/general-nonsmooth-local.md").read_text(encoding="utf-8")
    code = article.split("```python\n", 1)[1].split("```", 1)[0]
    compile(code, "general-nonsmooth-local.md", "exec")


def test_linear_system_figure_uses_the_article_numbers() -> None:
    from fractions import Fraction

    from scripts.generate_lesson_figures import _pa002_circuit_data

    data = _pa002_circuit_data()
    assert data["voltage"] == [Fraction(9, 4), Fraction(3, 2), Fraction(3, 4)]
    assert data["pivots"] == [Fraction(2), Fraction(3, 2), Fraction(4, 3)]
    # Kirchhoff's current law at every node: what leaves equals what is injected.
    assert (data["ground_1"], data["wire_12"]) == (Fraction(9, 4), Fraction(3, 4))
    assert data["ground_1"] + data["wire_12"] == 3
    assert data["wire_12"] == data["wire_23"] == data["ground_3"]
    figure = generate_lesson_figures()["linear-system-circuit.svg"]
    for text in (
        "v₁ = 2.25 V",
        "v₂ = 1.5 V",
        "v₃ = 0.75 V",
        "0.75 A",
        "2.25 A",
        "2.25 + 0.75 = 3 A",
    ):
        assert text in figure
    assert "stroke-dasharray" not in figure


def test_assignment_figures_use_the_article_numbers() -> None:
    from scripts.generate_lesson_figures import (
        ASSIGN_TIMES,
        ASSIGN_U,
        ASSIGN_V,
        assignment_all,
        assignment_greedy,
        assignment_reduced,
    )

    rows = assignment_all()
    assert [(total, longest) for total, longest, _ in rows] == [
        (15, 9),
        (16, 8),
        (20, 10),
        (21, 10),
        (22, 14),
        (24, 14),
    ]
    assert rows[0][2] == (0, 1, 2)
    assert assignment_greedy() == [(0, 1), (1, 2), (2, 0)]
    # The row and column values certify the minimum: never above a time, and summing to 15.
    reduced = assignment_reduced()
    assert all(value >= 0 for row in reduced for value in row)
    assert [reduced[i][i] for i in range(3)] == [0, 0, 0]
    assert sum(ASSIGN_U) + sum(ASSIGN_V) == 15
    assert sum(reduced[i][j] for i, j in assignment_greedy()) == 24 - 15
    assert ASSIGN_TIMES[2][2] == 9
    greedy = generate_lesson_figures()["assignment-greedy-optimal.svg"]
    for text in ("合計 24 分", "合計 15 分", "2 + 8 + 14 = 24", "3 + 3 + 9 = 15"):
        assert text in greedy
    dual = generate_lesson_figures()["assignment-dual-bound.svg"]
    for text in ("u の合計 9 ＋ v の合計 6 = 15", "救急車3 u=5", "C v=4"):
        assert text in dual


def test_eigenvalue_figures_use_the_article_numbers() -> None:
    from scripts.generate_lesson_figures import (
        eig_best_angle,
        eig_centre,
        eig_perpendicular_sum,
        eig_scatter,
        eig_values,
    )

    assert eig_centre() == (4.0, 3.0)
    assert eig_scatter() == (4.0, 4.0, 10.0)
    assert eig_values() == (2.0, 12.0)
    assert math.isclose(math.tan(math.radians(eig_best_angle())), 2.0)
    assert math.isclose(eig_perpendicular_sum(eig_best_angle()), 2.0)
    assert math.isclose(eig_perpendicular_sum(45.0), 3.0)
    assert math.isclose(eig_perpendicular_sum(0.0), 10.0)
    # 7 + 3 cos 2φ − 4 sin 2φ, the article's closed form
    for angle in range(0, 180, 15):
        phi = math.radians(angle)
        closed = 7 + 3 * math.cos(2 * phi) - 4 * math.sin(2 * phi)
        assert math.isclose(eig_perpendicular_sum(angle), closed)
    fence = generate_lesson_figures()["eigenvalue-fence-direction.svg"]
    for text in ("63.4° で最小 2", "153.4° で最大 12", "45°（縦のずれで当てはめた直線）で 3"):
        assert text in fence
    parallel = generate_lesson_figures()["eigenvalue-parallel-condition.svg"]
    for text in ("M n=(4, 4)", "M n=2 n", "n=(2, −1)/√5"):
        assert text in parallel


def test_stochastic_programming_figures_use_the_article_numbers() -> None:
    from scripts.generate_lesson_figures import sp_best, sp_cost, sp_expected, sp_mean_demand

    assert sp_best() == (40, 7000.0)
    assert sp_mean_demand() == 46.0
    assert [sp_expected(x) for x in (0, 20, 40, 46, 80)] == [11500, 8500, 7000, 7150, 8000]
    assert [sp_cost(40, d) for d in (20, 40, 80)] == [4000, 4000, 14000]
    cost = generate_lesson_figures()["stochastic-programming-expected-cost.svg"]
    for text in ("x=40：7000", "x=46：7150", "x=80：8000", "晴れ 80個"):
        assert text in cost
    tree = generate_lesson_figures()["stochastic-programming-two-stage.svg"]
    for text in ("x=40", "取り寄せ y=0", "取り寄せ y=40"):
        assert text in tree
