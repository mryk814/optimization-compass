from __future__ import annotations

import argparse
import heapq
import html
import math
import random
import re
from pathlib import Path

from optimization_compass.constraint_geometry import generate_so3_traces
from optimization_compass.derived_media import _best_trajectory, _plot_bounds
from optimization_compass.learning_slices import (
    generate_feasible_region_artifact,
    generate_pareto_front_artifact,
    generate_topology_field_artifact,
)
from optimization_compass.parameter_estimation import generate_parameter_estimation_traces
from optimization_compass.portfolio_uncertainty import generate_portfolio_uncertainty_traces
from optimization_compass.search_tree import (
    SearchTreeFramePayload,
    generate_search_tree_artifact,
)
from optimization_compass.site_export import (
    _generate_optimal_control_traces,
    _visualization_scenario,
)
from optimization_compass.surrogate_uncertainty import generate_surrogate_scenario
from optimization_compass.trace_models import AlgorithmTrace, TraceFrame
from optimization_compass.traces import generate_gradient_bundle, generate_nelder_mead_trace

ROOT = Path(__file__).parents[1]
DEFAULT_OUTPUT = ROOT / "site" / "public" / "media"
DATASET_VERSION_FILE = ROOT / "src" / "optimization_compass" / "resources" / "DATASET_VERSION"


def read_dataset_version() -> str:
    return DATASET_VERSION_FILE.read_text(encoding="utf-8").splitlines()[0].strip()


def generate_article_figures(dataset_version: str) -> dict[str, bytes]:
    return {
        "active-set-qp-execution.svg": _active_set_qp_svg(dataset_version).encode("utf-8"),
        "bayesian-optimization-execution.svg": _bayesian_optimization_svg(dataset_version).encode(
            "utf-8"
        ),
        "constrained-feasibility-execution.svg": _constrained_feasibility_svg(
            dataset_version
        ).encode("utf-8"),
        "cp-search-propagation-execution.svg": _cp_search_propagation_svg(dataset_version).encode(
            "utf-8"
        ),
        "direct-shooting-rollout-execution.svg": _direct_shooting_svg(dataset_version).encode(
            "utf-8"
        ),
        "dijkstra-astar-grid-execution.svg": _dijkstra_astar_grid_svg(dataset_version).encode(
            "utf-8"
        ),
        "dynamic-programming-knapsack-execution.svg": _dynamic_programming_knapsack_svg(
            dataset_version
        ).encode("utf-8"),
        "epsilon-constraint-production-execution.svg": _epsilon_constraint_production_svg(
            dataset_version
        ).encode("utf-8"),
        "gradient-family-execution.svg": _gradient_family_svg(dataset_version).encode("utf-8"),
        "lqr-backward-forward-execution.svg": _lqr_backward_forward_svg(dataset_version).encode(
            "utf-8"
        ),
        "local-search-two-opt-execution.svg": _local_search_two_opt_svg(dataset_version).encode(
            "utf-8"
        ),
        "least-squares-fit-diagnostic.svg": _least_squares_fit_svg(dataset_version).encode("utf-8"),
        "multiple-shooting-continuity-execution.svg": _multiple_shooting_svg(
            dataset_version
        ).encode("utf-8"),
        "network-simplex-pivot-execution.svg": _network_simplex_pivot_svg(dataset_version).encode(
            "utf-8"
        ),
        "nelder-mead-execution.svg": _nelder_mead_svg(dataset_version).encode("utf-8"),
        "optimal-control-mesh-execution.svg": _optimal_control_mesh_svg(dataset_version).encode(
            "utf-8"
        ),
        "pareto-preference-execution.svg": _pareto_preference_svg(dataset_version).encode("utf-8"),
        "particle-swarm-execution.svg": _particle_swarm_svg(dataset_version).encode("utf-8"),
        "pbt-lineage-execution.svg": _pbt_lineage_svg(dataset_version).encode("utf-8"),
        "pdlp-residual-execution.svg": _pdlp_residual_svg(dataset_version).encode("utf-8"),
        "portfolio-risk-execution.svg": _portfolio_risk_svg(dataset_version).encode("utf-8"),
        "random-search-coverage-execution.svg": _random_search_svg(dataset_version).encode("utf-8"),
        "search-tree-proof-execution.svg": _search_tree_proof_svg(dataset_version).encode("utf-8"),
        "sgd-mini-batch-execution.svg": _sgd_mini_batch_svg(dataset_version).encode("utf-8"),
        "simulated-annealing-execution.svg": _simulated_annealing_svg(dataset_version).encode(
            "utf-8"
        ),
        "so3-update-diagnostic.svg": _so3_update_svg(dataset_version).encode("utf-8"),
        "spatial-branch-bound-execution.svg": _spatial_branch_bound_svg(dataset_version).encode(
            "utf-8"
        ),
        "topology-field-execution.svg": _topology_field_svg(dataset_version).encode("utf-8"),
        "tpe-density-ratio-execution.svg": _tpe_density_ratio_svg(dataset_version).encode("utf-8"),
        "trf-probe-execution.svg": _trf_probe_svg(dataset_version).encode("utf-8"),
        "turbo-trust-region-execution.svg": _turbo_trust_region_svg(dataset_version).encode(
            "utf-8"
        ),
        "hyperband-rungs-execution.svg": _hyperband_rungs_svg(dataset_version).encode("utf-8"),
    }


def _nelder_mead_svg(dataset_version: str) -> str:
    trace = generate_nelder_mead_trace(
        problem_instance_id="OBJECTIVE_QUADRATIC_2D",
        trace_id="nelder-mead-quadratic",
        dataset_version=dataset_version,
    )
    scenario = _visualization_scenario(trace)
    if scenario.guided_story is None:
        raise ValueError("the Nelder-Mead article figure requires an authored guided story")
    terminal = trace.frames[scenario.guided_story.steps[-1].frame_index]
    simplex = [point.coordinates for point in terminal.points if point.role == "simplex-vertex"]
    if len(simplex) != 3:
        raise ValueError("Nelder-Mead article figure requires three terminal simplex vertices")
    x_min, x_max, y_min, y_max = _plot_bounds(trace)
    trajectory = _best_trajectory(trace.frames)

    initial_x, initial_y = (float(value) for value in trace.frames[0].points[0].coordinates)
    title = scenario.title_ja
    body, y = _figure_heading(
        title, f"f(x,y)=100x²+y²・初期点 ({initial_x:g}, {initial_y:g})・決定論的な実行"
    )
    legend_y = y + 14
    body.extend(
        [
            f'<line x1="{FIGURE_MARGIN}" y1="{legend_y - 5:g}" x2="{FIGURE_MARGIN + 26}" '
            f'y2="{legend_y - 5:g}" stroke="#9a462b" stroke-width="3.5"/>',
            f'<text x="{FIGURE_MARGIN + 34}" y="{legend_y:g}" class="note">最良点の軌跡</text>',
            f'<polygon points="{FIGURE_MARGIN + 150},{legend_y + 1:g} {FIGURE_MARGIN + 164},'
            f'{legend_y - 13:g} {FIGURE_MARGIN + 176},{legend_y + 1:g}" fill="#9fc2ad" '
            'stroke="#245c42" stroke-width="2"/>',
            f'<text x="{FIGURE_MARGIN + 184}" y="{legend_y:g}" class="note">終了時のsimplex</text>',
        ]
    )
    plot_size = 320.0
    panel, top, panel_bottom = _panel(legend_y + 14, "等高線の上で最良点が動く", plot_size + 30)
    body.extend(panel)
    plot_x, plot_y = (FIGURE_WIDTH - plot_size) / 2 + 10, top

    def project(point: list[float] | tuple[float, float]) -> tuple[float, float]:
        return (
            plot_x + (float(point[0]) - x_min) / (x_max - x_min) * plot_size,
            plot_y + plot_size - (float(point[1]) - y_min) / (y_max - y_min) * plot_size,
        )

    body.append(
        f'<rect x="{plot_x:g}" y="{plot_y:g}" width="{plot_size:g}" height="{plot_size:g}" '
        'fill="#f1f5f0" stroke="#d4ddd6"/>'
    )
    body.append(
        f'<clipPath id="nm-plot"><rect x="{plot_x:g}" y="{plot_y:g}" width="{plot_size:g}" '
        f'height="{plot_size:g}"/></clipPath>'
    )
    center_x, center_y = project((0.0, 0.0))
    contours = []
    for level in (1.0, 4.0, 16.0, 64.0, 256.0):
        radius_x = math.sqrt(level / 100.0) / (x_max - x_min) * plot_size
        radius_y = math.sqrt(level) / (y_max - y_min) * plot_size
        contours.append(
            f'<ellipse cx="{center_x:.2f}" cy="{center_y:.2f}" rx="{radius_x:.2f}" '
            f'ry="{radius_y:.2f}" fill="none" stroke="#b9c9bd" stroke-width="1.5"/>'
        )
    body.append(f'<g clip-path="url(#nm-plot)">{"".join(contours)}</g>')
    for tick in (-4, -2, 0, 2, 4):
        tick_x, _ = project((float(tick), 0.0))
        _, tick_y = project((0.0, float(tick)))
        body.extend(
            [
                f'<text x="{tick_x:.2f}" y="{plot_y + plot_size + 20:g}" text-anchor="middle" '
                f'class="axis">{tick}</text>',
                f'<text x="{plot_x - 8:g}" y="{tick_y + 5:.2f}" text-anchor="end" '
                f'class="axis">{tick}</text>',
            ]
        )
    path = " ".join("{:.2f},{:.2f}".format(*project(point)) for point in trajectory)
    vertices = " ".join("{:.2f},{:.2f}".format(*project(point)) for point in simplex)
    start_x, start_y = project(trajectory[0])
    body.extend(
        [
            f'<polyline points="{path}" fill="none" stroke="#9a462b" stroke-width="3.5" '
            'stroke-linejoin="round" stroke-linecap="round"/>',
            f'<polygon points="{vertices}" fill="#9fc2ad" fill-opacity="0.55" '
            'stroke="#245c42" stroke-width="3"/>',
            f'<circle cx="{start_x:.2f}" cy="{start_y:.2f}" r="5" fill="#fff" '
            'stroke="#9a462b" stroke-width="2.5"/>',
            f'<text x="{start_x:.2f}" y="{start_y - 12:.2f}" text-anchor="middle" '
            'class="method halo">最初の最良点</text>',
            f'<path d="M {center_x - 9:.2f} {center_y:.2f} H {center_x + 9:.2f} '
            f'M {center_x:.2f} {center_y - 9:.2f} V {center_y + 9:.2f}" stroke="#245c42" '
            'stroke-width="2.5"/>',
            f'<text x="{center_x + 14:.2f}" y="{center_y + 24:.2f}" class="method halo" '
            'fill="#245c42">最適解 (0, 0)</text>',
        ]
    )
    summary, y = _text_lines(
        FIGURE_MARGIN,
        panel_bottom + 30,
        "線は各反復の最良点をつないだものです。終了時のsimplexは最適解のすぐ近くにあり、"
        "この縮尺では点に見えます。",
        "note",
    )
    body.extend(summary)
    rows, y = _metric_rows(
        y + 12,
        (
            (
                "目的値",
                f"{_objective_value(trace.frames[0]):g} → "
                f"{_metric(_objective_value(trace.frames[-1]))}",
            ),
            (
                "評価回数",
                f"{trace.frames[-1].oracle_evaluations}回 · "
                f"{TERMINAL_STATUS_JA[trace.terminal_status]}",
            ),
        ),
    )
    body.extend(rows)
    footer, height = _figure_footer(
        y + 8,
        f"Scenario {scenario.scenario_id} · optimization_compass.traces."
        f"generate_nelder_mead_trace · dataset {dataset_version}",
        scenario.lesson.limitations_ja,
    )
    body.extend(footer)
    return _figure_document(title, scenario.lesson.text_alternative.ja, height, body)


def _active_set_qp_objective(point: tuple[float, float]) -> float:
    x1, x2 = point
    return x1 * x1 + 0.5 * x2 * x2 - 4.0 * x1 - x2


def _active_set_qp_probe() -> dict[str, object]:
    hessian = ((2.0, 0.0), (0.0, 1.0))
    linear = (-4.0, -1.0)
    constraints = (
        ("x₁ ≥ 0", (-1.0, 0.0), 0.0),
        ("x₂ ≥ 0", (0.0, -1.0), 0.0),
        ("x₁ ≤ 1.5", (1.0, 0.0), 1.5),
        ("x₁ + x₂ ≤ 2", (1.0, 1.0), 2.0),
    )
    point = [0.0, 0.0]
    working_set = [0, 1]
    events: list[dict[str, object]] = []

    for iteration in range(10):
        gradient = [
            hessian[row][0] * point[0] + hessian[row][1] * point[1] + linear[row]
            for row in range(2)
        ]
        system_size = 2 + len(working_set)
        kkt = [[0.0] * system_size for _ in range(system_size)]
        for row in range(2):
            for column in range(2):
                kkt[row][column] = hessian[row][column]
        for offset, constraint_index in enumerate(working_set):
            normal = constraints[constraint_index][1]
            for row in range(2):
                kkt[row][2 + offset] = normal[row]
                kkt[2 + offset][row] = normal[row]
        solution = _solve_dense_linear_system(
            kkt,
            [-gradient[0], -gradient[1], *([0.0] * len(working_set))],
        )
        direction = tuple(solution[:2])
        multipliers = tuple(solution[2:])

        if math.hypot(*direction) <= 1e-10:
            if min(multipliers, default=0.0) >= -1e-10:
                events.append(
                    {
                        "iteration": iteration,
                        "action": "optimal",
                        "constraint_index": None,
                        "point": tuple(point),
                        "working_set": tuple(working_set),
                        "value": min(multipliers, default=0.0),
                        "objective": _active_set_qp_objective(tuple(point)),
                    }
                )
                break
            removal_position = min(
                range(len(multipliers)),
                key=multipliers.__getitem__,
            )
            constraint_index = working_set.pop(removal_position)
            events.append(
                {
                    "iteration": iteration,
                    "action": "remove",
                    "constraint_index": constraint_index,
                    "point": tuple(point),
                    "working_set": tuple(working_set),
                    "value": multipliers[removal_position],
                    "objective": _active_set_qp_objective(tuple(point)),
                }
            )
            continue

        step_length = 1.0
        blocking_constraint = None
        for constraint_index, (_, normal, bound) in enumerate(constraints):
            if constraint_index in working_set:
                continue
            directional_change = normal[0] * direction[0] + normal[1] * direction[1]
            if directional_change <= 1e-10:
                continue
            candidate_length = (
                bound - normal[0] * point[0] - normal[1] * point[1]
            ) / directional_change
            if candidate_length < step_length - 1e-12:
                step_length = candidate_length
                blocking_constraint = constraint_index

        point = [point[index] + step_length * direction[index] for index in range(2)]
        if blocking_constraint is not None:
            working_set.append(blocking_constraint)
        events.append(
            {
                "iteration": iteration,
                "action": "add" if blocking_constraint is not None else "step",
                "constraint_index": blocking_constraint,
                "point": tuple(point),
                "working_set": tuple(working_set),
                "value": step_length,
                "objective": _active_set_qp_objective(tuple(point)),
            }
        )
    else:
        raise RuntimeError("fixed active-set QP probe did not terminate")

    final_point = tuple(point)
    residuals = tuple(
        normal[0] * point[0] + normal[1] * point[1] - bound for _, normal, bound in constraints
    )
    return {
        "constraints": constraints,
        "events": tuple(events),
        "initial_point": (0.0, 0.0),
        "final_point": final_point,
        "initial_objective": _active_set_qp_objective((0.0, 0.0)),
        "final_objective": _active_set_qp_objective(final_point),
        "max_residual": max(residuals),
    }


def _active_set_qp_svg(dataset_version: str) -> str:
    probe = _active_set_qp_probe()
    constraints = probe["constraints"]
    events = probe["events"]
    if not isinstance(constraints, tuple) or not isinstance(events, tuple):
        raise TypeError("active-set QP teaching probe collections must be tuples")

    title = "止まったら外す。動いたら加える。"
    body, y = _figure_heading(title, "固定した凸QP・実行可能な初期点・決定論的なworking set更新")
    legend_y = y + 14
    body.extend(
        [
            f'<line x1="{FIGURE_MARGIN}" y1="{legend_y - 5:g}" x2="{FIGURE_MARGIN + 26}" '
            f'y2="{legend_y - 5:g}" stroke="#d67835" stroke-width="4"/>',
            f'<text x="{FIGURE_MARGIN + 34}" y="{legend_y:g}" class="note">反復点の経路</text>',
            f'<line x1="{FIGURE_MARGIN + 160}" y1="{legend_y - 5:g}" x2="{FIGURE_MARGIN + 186}" '
            f'y2="{legend_y - 5:g}" stroke="#2c7564" stroke-width="5"/>',
            f'<text x="{FIGURE_MARGIN + 194}" y="{legend_y:g}" class="note">'
            "最後に有効な制約</text>",
        ]
    )
    panel, top, panel_bottom = _panel(legend_y + 14, "実行可能領域と反復点", 330)
    body.extend(panel)
    plot_left, plot_right = 64.0, 400.0
    plot_top = top + 14
    plot_bottom = plot_top + (plot_right - plot_left) * 414 / 510
    x_min, x_max = -0.15, 2.2
    y_min, y_max = -0.15, 2.15

    def screen(point: tuple[float, float]) -> tuple[float, float]:
        x1, x2 = point
        x = plot_left + (x1 - x_min) / (x_max - x_min) * (plot_right - plot_left)
        y = plot_bottom - (x2 - y_min) / (y_max - y_min) * (plot_bottom - plot_top)
        return x, y

    body.append(
        f'<defs><clipPath id="asq-plot"><rect x="{plot_left:g}" y="{plot_top:g}" '
        f'width="{plot_right - plot_left:g}" height="{plot_bottom - plot_top:g}"/>'
        "</clipPath></defs>"
    )
    for tick in (0.0, 0.5, 1.0, 1.5, 2.0):
        x, _ = screen((tick, 0.0))
        _, tick_y = screen((0.0, tick))
        body.extend(
            [
                (
                    f'<line x1="{x:.2f}" y1="{plot_top:g}" x2="{x:.2f}" y2="{plot_bottom:g}" '
                    'stroke="#edf0ec" stroke-width="1"/>'
                ),
                (
                    f'<text x="{x:.2f}" y="{plot_bottom + 20:g}" text-anchor="middle" '
                    f'class="axis">{tick:g}</text>'
                ),
                (
                    f'<line x1="{plot_left:g}" y1="{tick_y:.2f}" x2="{plot_right:g}" '
                    f'y2="{tick_y:.2f}" stroke="#edf0ec" stroke-width="1"/>'
                ),
                (
                    f'<text x="{plot_left - 10:g}" y="{tick_y + 5:.2f}" text-anchor="end" '
                    f'class="axis">{tick:g}</text>'
                ),
            ]
        )

    feasible_points = " ".join(
        f"{x:.2f},{y:.2f}"
        for x, y in (
            screen((0.0, 0.0)),
            screen((1.5, 0.0)),
            screen((1.5, 0.5)),
            screen((0.0, 2.0)),
        )
    )
    body.append(
        f'<polygon points="{feasible_points}" fill="#dceee7" stroke="#45656a" stroke-width="1.5"/>'
    )
    for objective_gap in (0.125, 0.5, 1.125, 2.0, 3.125):
        points = []
        for index in range(101):
            angle = 2.0 * math.pi * index / 100
            point = (
                2.0 + math.sqrt(objective_gap) * math.cos(angle),
                1.0 + math.sqrt(2.0 * objective_gap) * math.sin(angle),
            )
            points.append(screen(point))
        contour = " ".join(f"{x:.2f},{y:.2f}" for x, y in points)
        body.append(
            f'<polyline points="{contour}" fill="none" stroke="#b9c7c2" '
            'stroke-width="1.2" stroke-dasharray="4 4" clip-path="url(#asq-plot)"/>'
        )
    for start, end in (((1.5, 0.0), (1.5, 0.5)), ((0.0, 2.0), (1.5, 0.5))):
        x1, y1 = screen(start)
        x2, y2 = screen(end)
        body.append(
            f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" '
            'stroke="#2c7564" stroke-width="5" stroke-linecap="round"/>'
        )
    path_points = ((0.0, 0.0), (1.5, 0.0), (1.5, 0.5))
    path = " ".join(f"{x:.2f},{y:.2f}" for x, y in map(screen, path_points))
    body.append(
        f'<polyline points="{path}" fill="none" stroke="#d67835" stroke-width="3.5" '
        'stroke-linecap="round" stroke-linejoin="round"/>'
    )
    markers = dict(zip(path_points, ("A", "B", "C"), strict=True))
    for point, marker in markers.items():
        x, point_y = screen(point)
        label_x = x + 12 if marker == "A" else x - 12
        anchor = "start" if marker == "A" else "end"
        body.extend(
            [
                (
                    f'<circle cx="{x:.2f}" cy="{point_y:.2f}" r="6.5" fill="#d67835" '
                    'stroke="#fff" stroke-width="2"/>'
                ),
                (
                    f'<text x="{label_x:.2f}" y="{point_y - 10:.2f}" text-anchor="{anchor}" '
                    f'class="method halo">{marker}</text>'
                ),
            ]
        )
    body.extend(
        [
            f'<text x="{plot_right:g}" y="{plot_bottom + 42:g}" text-anchor="end" class="axis">'
            "横軸 x₁、縦軸 x₂</text>",
        ]
    )

    constraint_labels = tuple(str(row[0]) for row in constraints)
    action_labels = {"remove": "外す", "add": "加える", "step": "進む", "optimal": "最適"}
    action_colors = {
        "remove": "#102a2e",
        "add": "#d67835",
        "step": "#45656a",
        "optimal": "#2c7564",
    }
    panel, top, panel_bottom = _panel(panel_bottom + 12, "working setの変化", 12 + 30 * len(events))
    body.extend(panel)
    for row_index, event in enumerate(events):
        action = str(event["action"])
        constraint_index = event["constraint_index"]
        point = event["point"]
        if not isinstance(point, tuple):
            raise TypeError("active-set QP event point must be a tuple")
        marker = next(
            (
                letter
                for known, letter in markers.items()
                if math.dist(known, tuple(float(value) for value in point)) < 1e-9
            ),
            "",
        )
        row_y = top + 16 + row_index * 30
        if constraint_index is None:
            detail = "KKT条件の符号を満たす"
        else:
            constraint_label = constraint_labels[int(constraint_index)]
            symbol = "λ" if action == "remove" else "α"
            detail = f"{constraint_label} · {symbol}={float(event['value']):.2f}"
        where = f"（{marker}）" if marker else ""
        body.extend(
            [
                f'<circle cx="{FIGURE_MARGIN + 20}" cy="{row_y - 5:g}" r="5.5" '
                f'fill="{action_colors[action]}"/>',
                (
                    f'<text x="{FIGURE_MARGIN + 34}" y="{row_y:g}" class="method">'
                    f"{event['iteration']} · {action_labels[action]}{where}</text>"
                ),
                (
                    f'<text x="{FIGURE_MARGIN + 160}" y="{row_y:g}" class="status">'
                    f"{html.escape(detail)}</text>"
                ),
            ]
        )
    y = panel_bottom + 34
    right = FIGURE_WIDTH - FIGURE_MARGIN
    adds = sum(1 for event in events if event["action"] == "add")
    removes = sum(1 for event in events if event["action"] == "remove")
    for label, value in (
        (
            "目的値",
            f"{float(probe['initial_objective']):.3f} → {float(probe['final_objective']):.3f}",
        ),
        ("制約の追加と除外", f"加える {adds} · 外す {removes}"),
        ("最大の制約違反", f"{max(0.0, float(probe['max_residual'])):.1f}"),
    ):
        body.extend(
            [
                f'<text x="{FIGURE_MARGIN}" y="{y:g}" class="metric">{label}</text>',
                f'<text x="{right}" y="{y:g}" text-anchor="end" class="metric-value">'
                f"{value}</text>",
            ]
        )
        y += 26
    footer, height = _figure_footer(
        y + 8,
        f"scripts.generate_article_figures._active_set_qp_probe · dataset {dataset_version}",
        "固定した2変数の凸QPです。退化、巡回、分解のコスト、solver一般の性能は示しません。",
    )
    body.extend(footer)
    return _figure_document(
        "active-set QPで制約を外し、加える固定実行",
        (
            "2変数の凸二次計画を実行可能な原点から解く。"
            "原点では負のmultiplierを持つx1下限制約を外し、x2下限のface上を進む。"
            "x1上限制約を加え、同じ点でx2下限制約を外した後、"
            "斜めの制約へ進んで最適点に到達する。"
        ),
        height,
        body,
    )


def _direct_shooting_rollout(
    controls: tuple[float, ...],
    *,
    decay: float = 0.92,
    time_step: float = 0.1,
) -> tuple[float, ...]:
    states = [0.0]
    for control in controls:
        states.append(decay * states[-1] + time_step * control)
    return tuple(states)


def _direct_shooting_probe() -> dict[str, object]:
    horizon = 20
    decay = 0.92
    time_step = 0.1
    target = 1.0
    control_penalty = 0.002
    learning_rate = 4.0
    controls = [0.0] * horizon
    initial_controls = tuple(controls)
    initial_states = _direct_shooting_rollout(
        initial_controls,
        decay=decay,
        time_step=time_step,
    )
    terminal_weights = tuple(time_step * decay ** (horizon - 1 - index) for index in range(horizon))
    history: list[tuple[int, float, float, int]] = []

    for iteration in range(81):
        states = _direct_shooting_rollout(
            tuple(controls),
            decay=decay,
            time_step=time_step,
        )
        terminal_error = states[-1] - target
        objective = terminal_error * terminal_error + control_penalty * sum(
            control * control for control in controls
        )
        saturated = sum(control >= 1.0 - 1e-12 for control in controls)
        history.append((iteration, objective, states[-1], saturated))
        if iteration == 80:
            break

        gradient = [
            2.0 * terminal_error * weight + 2.0 * control_penalty * control
            for weight, control in zip(terminal_weights, controls, strict=True)
        ]
        controls = [
            max(-1.0, min(1.0, control - learning_rate * derivative))
            for control, derivative in zip(controls, gradient, strict=True)
        ]

    optimized_controls = tuple(controls)
    optimized_states = _direct_shooting_rollout(
        optimized_controls,
        decay=decay,
        time_step=time_step,
    )
    return {
        "horizon": horizon,
        "decay": decay,
        "time_step": time_step,
        "target": target,
        "control_penalty": control_penalty,
        "learning_rate": learning_rate,
        "initial_controls": initial_controls,
        "optimized_controls": optimized_controls,
        "initial_states": initial_states,
        "optimized_states": optimized_states,
        "history": tuple(history),
        "initial_objective": history[0][1],
        "final_objective": history[-1][1],
        "terminal_error": abs(optimized_states[-1] - target),
        "saturated_controls": history[-1][3],
    }


def _direct_shooting_svg(dataset_version: str) -> str:
    probe = _direct_shooting_probe()
    initial_controls = probe["initial_controls"]
    optimized_controls = probe["optimized_controls"]
    initial_states = probe["initial_states"]
    optimized_states = probe["optimized_states"]
    if not all(
        isinstance(values, tuple)
        for values in (
            initial_controls,
            optimized_controls,
            initial_states,
            optimized_states,
        )
    ):
        raise TypeError("direct-shooting teaching probe collections must be tuples")

    title = "制御の列を変えると、軌道が決まる"
    body, y = _figure_heading(title, "固定した減衰系・制御20個・射影勾配による更新80回")
    legend_y = y + 14
    for offset, (color, width, label) in zip(
        (0, 118, 260),
        (("#aebbb6", 3, "初期値"), ("#d67835", 4, "最適化後の制御"), ("#2c7564", 4, "状態")),
        strict=True,
    ):
        body.extend(
            [
                f'<line x1="{FIGURE_MARGIN + offset}" y1="{legend_y - 5:g}" '
                f'x2="{FIGURE_MARGIN + offset + 24}" y2="{legend_y - 5:g}" stroke="{color}" '
                f'stroke-width="{width}"/>',
                f'<text x="{FIGURE_MARGIN + offset + 32}" y="{legend_y:g}" class="note">'
                f"{label}</text>",
            ]
        )
    body.append(
        '<defs><marker id="dsh-arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" '
        'orient="auto"><path d="M0,0 L8,4 L0,8 Z" fill="#d67835"/></marker></defs>'
    )
    plot_left, plot_right = 52.0, 406.0
    horizon = int(probe["horizon"])
    plot_height = 160.0

    def time_x(index: int) -> float:
        return plot_left + index / horizon * (plot_right - plot_left)

    panel, control_top, panel_bottom = _panel(
        legend_y + 14, "決定変数: 制御の列（−1 ≤ uₜ ≤ 1）", plot_height + 40
    )
    body.extend(panel)
    control_top += 4
    control_bottom = control_top + plot_height

    def control_y(value: float) -> float:
        return control_bottom - value / 1.05 * (control_bottom - control_top)

    for value in (0.0, 0.5, 1.0):
        tick_y = control_y(value)
        body.extend(
            [
                f'<line x1="{plot_left:g}" y1="{tick_y:.2f}" x2="{plot_right:g}" '
                f'y2="{tick_y:.2f}" stroke="#e4e9e5" stroke-width="1"/>',
                f'<text x="{plot_left - 10:g}" y="{tick_y + 5:.2f}" text-anchor="end" '
                f'class="axis">{value:g}</text>',
            ]
        )
    bar_step = (plot_right - plot_left) / horizon
    bar_width = bar_step * 0.62
    baseline_y = control_y(0.0)
    for index, value in enumerate(optimized_controls):
        x = time_x(index) + (bar_step - bar_width) / 2
        bar_top = control_y(float(value))
        body.append(
            f'<rect x="{x:.2f}" y="{bar_top:.2f}" width="{bar_width:.2f}" '
            f'height="{baseline_y - bar_top:.2f}" rx="2" fill="#d67835"/>'
        )
    body.append(
        f'<line x1="{plot_left:g}" y1="{baseline_y:.2f}" x2="{plot_right:g}" '
        f'y2="{baseline_y:.2f}" stroke="#aebbb6" stroke-width="3"/>'
    )
    for tick in (0, 5, 10, 15, 20):
        body.append(
            f'<text x="{time_x(tick):.2f}" y="{control_bottom + 22:g}" text-anchor="middle" '
            f'class="axis">{tick}</text>'
        )
    arrow_top = panel_bottom + 6
    body.extend(
        [
            f'<line x1="{FIGURE_WIDTH / 2:g}" y1="{arrow_top:g}" x2="{FIGURE_WIDTH / 2:g}" '
            f'y2="{arrow_top + 30:g}" stroke="#d67835" stroke-width="3" '
            'marker-end="url(#dsh-arrow)"/>',
            f'<text x="{FIGURE_WIDTH / 2 + 14:g}" y="{arrow_top + 22:g}" class="method" '
            'fill="#8b4c3d">前進シミュレーション</text>',
        ]
    )
    panel, state_top, panel_bottom = _panel(arrow_top + 40, "結果: 状態の軌道", plot_height + 40)
    body.extend(panel)
    state_top += 4
    state_bottom = state_top + plot_height

    def state_y(value: float) -> float:
        return state_bottom - value / 1.05 * (state_bottom - state_top)

    for value in (0.0, 0.5, 1.0):
        tick_y = state_y(value)
        body.extend(
            [
                f'<line x1="{plot_left:g}" y1="{tick_y:.2f}" x2="{plot_right:g}" '
                f'y2="{tick_y:.2f}" stroke="#e4e9e5" stroke-width="1"/>',
                f'<text x="{plot_left - 10:g}" y="{tick_y + 5:.2f}" text-anchor="end" '
                f'class="axis">{value:g}</text>',
            ]
        )
    target_y = state_y(float(probe["target"]))
    initial_path = " ".join(
        f"{time_x(index):.2f},{state_y(float(value)):.2f}"
        for index, value in enumerate(initial_states)
    )
    optimized_path = " ".join(
        f"{time_x(index):.2f},{state_y(float(value)):.2f}"
        for index, value in enumerate(optimized_states)
    )
    final_x = time_x(horizon)
    final_y = state_y(float(optimized_states[-1]))
    body.extend(
        [
            f'<line x1="{plot_left:g}" y1="{target_y:.2f}" x2="{plot_right:g}" '
            f'y2="{target_y:.2f}" stroke="#102a2e" stroke-width="1.5" stroke-dasharray="6 5"/>',
            f'<text x="{plot_left + 6:g}" y="{target_y - 8:.2f}" class="method halo">'
            "目標 = 1</text>",
            f'<polyline points="{initial_path}" fill="none" stroke="#aebbb6" '
            'stroke-width="3" stroke-dasharray="6 5"/>',
            f'<polyline points="{optimized_path}" fill="none" stroke="#2c7564" '
            'stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>',
            f'<circle cx="{final_x:.2f}" cy="{final_y:.2f}" r="6" fill="#2c7564" '
            'stroke="#fff" stroke-width="2"/>',
            f'<text x="{final_x - 10:.2f}" y="{final_y + 24:.2f}" text-anchor="end" '
            f'class="method halo" fill="#2c7564">x₂₀ = {float(optimized_states[-1]):.3f}</text>',
        ]
    )
    for tick in (0, 5, 10, 15, 20):
        body.append(
            f'<text x="{time_x(tick):.2f}" y="{state_bottom + 22:g}" text-anchor="middle" '
            f'class="axis">{tick}</text>'
        )
    rows, y = _metric_rows(
        panel_bottom + 34,
        (
            (
                "目的値",
                f"{float(probe['initial_objective']):.3f} → {float(probe['final_objective']):.4f}",
            ),
            ("終端の誤差", f"{float(probe['terminal_error']):.4f}"),
            ("上限に達した制御", f"{int(probe['saturated_controls'])} / 20"),
        ),
    )
    body.extend(rows)
    footer, height = _figure_footer(
        y + 8,
        f"scripts.generate_article_figures._direct_shooting_probe · dataset {dataset_version}",
        "固定した1状態の教材です。終端の等式制約、経路制約、不安定な系、モデルのずれ、"
        "solver一般の性能は示しません。",
    )
    body.extend(footer)
    return _figure_document(
        "Direct Shootingの制御の列と前進シミュレーションの結果",
        (
            "20個の制御を射影勾配で更新する固定Direct Shooting教材。"
            "上段では後半の制御が上限1へ達する。"
            "下段ではその制御の列を前進シミュレーションした状態が0から0.950へ進む。"
            "初期の制御の列では状態は0のままである。"
        ),
        height,
        body,
    )


def _pdlp_probe() -> dict[str, object]:
    costs = (3.0, 1.0, 2.0)
    right_hand_side = 1.0
    spectral_norm = math.sqrt(3.0)
    primal_step = 0.9 / spectral_norm
    dual_step = 0.9 / spectral_norm
    primal = [1.0 / 3.0] * 3
    dual = 0.0
    history: list[dict[str, object]] = []

    for iteration in range(101):
        primal_residual = abs(sum(primal) - right_hand_side)
        reduced_costs = tuple(cost - dual for cost in costs)
        dual_residual = math.sqrt(
            sum(min(reduced_cost, 0.0) ** 2 for reduced_cost in reduced_costs)
        )
        primal_objective = sum(cost * value for cost, value in zip(costs, primal, strict=True))
        dual_objective = right_hand_side * dual
        history.append(
            {
                "iteration": iteration,
                "primal": tuple(primal),
                "dual": dual,
                "primal_residual": primal_residual,
                "dual_residual": dual_residual,
                "objective_difference": abs(primal_objective - dual_objective),
                "primal_objective": primal_objective,
                "dual_objective": dual_objective,
            }
        )
        if iteration == 100:
            break

        primal_next = [
            max(0.0, value - primal_step * (cost - dual))
            for value, cost in zip(primal, costs, strict=True)
        ]
        extrapolated_sum = sum(
            2.0 * next_value - value for next_value, value in zip(primal_next, primal, strict=True)
        )
        dual += dual_step * (right_hand_side - extrapolated_sum)
        primal = primal_next

    return {
        "costs": costs,
        "right_hand_side": right_hand_side,
        "spectral_norm": spectral_norm,
        "primal_step": primal_step,
        "dual_step": dual_step,
        "history": tuple(history),
        "snapshots": tuple(history[index] for index in (0, 5, 20, 100)),
        "final_primal": history[-1]["primal"],
        "final_dual": history[-1]["dual"],
        "final_primal_residual": history[-1]["primal_residual"],
        "final_dual_residual": history[-1]["dual_residual"],
        "final_objective_difference": history[-1]["objective_difference"],
    }


def _pdlp_residual_svg(dataset_version: str) -> str:
    probe = _pdlp_probe()
    history = probe["history"]
    snapshots = probe["snapshots"]
    if not isinstance(history, tuple) or not isinstance(snapshots, tuple):
        raise TypeError("PDLP teaching probe history and snapshots must be tuples")

    title = "一つの残差では、収束を判定できない"
    body, y = _figure_heading(title, "固定した3変数のLP・行列とベクトルの積による更新・100反復")
    colors = ("#d67835", "#2c7564", "#8ba7a0")
    panel, top, panel_bottom = _panel(
        y + 8, "primal変数（合計 = 1）", 34 + 52 * len(snapshots) + 26
    )
    body.extend(panel)
    for index, (color, label) in enumerate(
        zip(colors, ("x₁ · cost 3", "x₂ · cost 1", "x₃ · cost 2"), strict=True)
    ):
        key_x = FIGURE_MARGIN + 14 + index * 126
        body.extend(
            [
                f'<rect x="{key_x}" y="{top - 6:g}" width="15" height="15" rx="3" fill="{color}"/>',
                f'<text x="{key_x + 22}" y="{top + 7:g}" class="note">{label}</text>',
            ]
        )
    bar_left, bar_full = FIGURE_MARGIN + 80.0, 240.0
    for row_index, snapshot in enumerate(snapshots):
        if not isinstance(snapshot, dict):
            raise TypeError("PDLP teaching snapshot must be a dictionary")
        primal = snapshot["primal"]
        if not isinstance(primal, tuple):
            raise TypeError("PDLP teaching primal vector must be a tuple")
        bar_y = top + 26 + row_index * 52.0
        body.extend(
            [
                f'<text x="{FIGURE_MARGIN + 14}" y="{bar_y + 19:.2f}" class="method">'
                f"k = {int(snapshot['iteration'])}</text>",
                f'<rect x="{bar_left:g}" y="{bar_y:.2f}" width="{bar_full * 1.2:g}" '
                'height="28" rx="6" fill="#edf2ef"/>',
                f'<line x1="{bar_left + bar_full:g}" y1="{bar_y - 4:.2f}" '
                f'x2="{bar_left + bar_full:g}" y2="{bar_y + 32:.2f}" stroke="#102a2e" '
                'stroke-width="1.5" stroke-dasharray="4 4"/>',
            ]
        )
        cursor = bar_left
        for value, color in zip(primal, colors, strict=True):
            segment_width = bar_full * max(0.0, float(value))
            if segment_width > 0.0:
                body.append(
                    f'<rect x="{cursor:.2f}" y="{bar_y:.2f}" width="{segment_width:.2f}" '
                    f'height="28" fill="{color}"/>'
                )
            cursor += segment_width
        body.append(
            f'<text x="{bar_left:g}" y="{bar_y + 46:.2f}" class="status">'
            f"cᵀx = {float(snapshot['primal_objective']):.3f}</text>"
        )
    body.append(
        f'<text x="{FIGURE_MARGIN + 14}" y="{panel_bottom - 12:g}" class="method" '
        'fill="#2c7564">costが最小の x₂ へ質量が集まる</text>'
    )

    series = (
        ("primal残差", "primal_residual", "#2c7564", ""),
        ("dual残差", "dual_residual", "#d67835", "7 5"),
        ("目的値の差 |cᵀx − bᵀy|", "objective_difference", "#102a2e", "3 5"),
    )
    panel, top, panel_bottom = _panel(panel_bottom + 12, "停止判定に使う3つの量", 76 + 200)
    body.extend(panel)
    for index, (label, _, color, dash) in enumerate(series):
        dash_attribute = f' stroke-dasharray="{dash}"' if dash else ""
        key_y = top + 4 + index * 22
        body.extend(
            [
                f'<line x1="{FIGURE_MARGIN + 14}" y1="{key_y - 5:g}" x2="{FIGURE_MARGIN + 40}" '
                f'y2="{key_y - 5:g}" stroke="{color}" stroke-width="3"{dash_attribute}/>',
                f'<text x="{FIGURE_MARGIN + 48}" y="{key_y:g}" class="note">{label}</text>',
            ]
        )
    plot_left, plot_right = 72.0, 404.0
    plot_top = top + 76
    plot_bottom = plot_top + 160
    log_floor = -8.0

    def iteration_x(iteration: int) -> float:
        return plot_left + iteration / 100.0 * (plot_right - plot_left)

    def residual_y(value: float) -> float:
        exponent = max(log_floor, min(0.0, math.log10(max(value, 10.0**log_floor))))
        return plot_top + (0.0 - exponent) / -log_floor * (plot_bottom - plot_top)

    for exponent in (0, -2, -4, -6, -8):
        tick_y = residual_y(10.0**exponent)
        body.extend(
            [
                f'<line x1="{plot_left:g}" y1="{tick_y:.2f}" x2="{plot_right:g}" '
                f'y2="{tick_y:.2f}" stroke="#e4e9e5" stroke-width="1"/>',
                f'<text x="{plot_left - 8:g}" y="{tick_y + 5:.2f}" text-anchor="end" '
                f'class="axis">1e{exponent}</text>',
            ]
        )
    for iteration in (0, 20, 40, 60, 80, 100):
        body.append(
            f'<text x="{iteration_x(iteration):.2f}" y="{plot_bottom + 22:g}" '
            f'text-anchor="middle" class="axis">{iteration}</text>'
        )
    for _, key, color, dash in series:
        points = " ".join(
            f"{iteration_x(int(item['iteration'])):.2f},{residual_y(float(item[key])):.2f}"
            for item in history
            if isinstance(item, dict)
        )
        dash_attribute = f' stroke-dasharray="{dash}"' if dash else ""
        body.append(
            f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="3" '
            f'stroke-linecap="round" stroke-linejoin="round"{dash_attribute}/>'
        )
    body.append(
        f'<circle cx="{plot_left:g}" cy="{plot_bottom:g}" r="5.5" fill="#d67835" '
        'stroke="#fff" stroke-width="2"/>'
    )
    final_primal = probe["final_primal"]
    if not isinstance(final_primal, tuple):
        raise TypeError("PDLP teaching final primal vector must be a tuple")
    callout, y = _text_lines(
        FIGURE_MARGIN,
        panel_bottom + 30,
        "k = 0 では実行可能性の残差が 0 でも、目的値の差は 2 ある（橙の点）",
        "method",
        size=TEXT_SIZE["method"],
    )
    body.extend(line.replace('class="method"', 'class="method" fill="#8b4c3d"') for line in callout)
    rows, y = _metric_rows(
        y + 8,
        (
            ("解", f"x = ({', '.join(f'{float(value):.3f}' for value in final_primal)})"),
            ("目的値", "2.000 → 1.000"),
        ),
    )
    body.extend(rows)
    footer, height = _figure_footer(
        y + 8,
        f"scripts.generate_article_figures._pdlp_probe · dataset {dataset_version}",
        "図の目的値の差は生の絶対差です。実行不能な反復点ではdualの下界や証明書を意味しません。"
        "scaling、restart、solverの性能も示しません。",
    )
    body.extend(footer)
    return _figure_document(
        "PDHG反復で変数と三つの判定量が変わる様子",
        (
            "三変数simplex線形計画を100回更新した固定教材。"
            "上段では初期に均等だった質量が最小costのx2へ移る。"
            "下段ではprimal残差、dual残差、primalとdualの目的値差を同時に示す。"
            "dual残差だけは初期にもゼロであり、一つの量だけでは停止できない。"
        ),
        height,
        body,
    )


def _dijkstra_astar_grid_probe() -> dict[str, object]:
    width, height = 17, 11
    start = (1, 5)
    goal = (15, 5)
    obstacles = tuple(
        sorted({(6, y) for y in range(1, 10) if y != 2} | {(11, y) for y in range(1, 10) if y != 8})
    )
    blocked = set(obstacles)

    def search(*, use_heuristic: bool) -> dict[str, object]:
        def heuristic(node: tuple[int, int]) -> int:
            if not use_heuristic:
                return 0
            return abs(goal[0] - node[0]) + abs(goal[1] - node[1])

        distance = {start: 0}
        predecessor: dict[tuple[int, int], tuple[int, int]] = {}
        queue = [(heuristic(start), heuristic(start), start)]
        closed: set[tuple[int, int]] = set()
        expanded: list[tuple[int, int]] = []
        relaxed_edges = 0

        while queue:
            _, _, node = heapq.heappop(queue)
            if node in closed:
                continue
            closed.add(node)
            expanded.append(node)
            if node == goal:
                break

            for delta_x, delta_y in ((1, 0), (0, 1), (-1, 0), (0, -1)):
                neighbor = (node[0] + delta_x, node[1] + delta_y)
                if not (0 <= neighbor[0] < width and 0 <= neighbor[1] < height):
                    continue
                if neighbor in blocked:
                    continue
                candidate = distance[node] + 1
                if candidate >= distance.get(neighbor, width * height + 1):
                    continue
                distance[neighbor] = candidate
                predecessor[neighbor] = node
                priority = candidate + heuristic(neighbor)
                heapq.heappush(queue, (priority, heuristic(neighbor), neighbor))
                relaxed_edges += 1

        path = [goal]
        while path[-1] != start:
            path.append(predecessor[path[-1]])
        path.reverse()
        return {
            "cost": distance[goal],
            "path": tuple(path),
            "expanded": tuple(expanded),
            "relaxed_edges": relaxed_edges,
        }

    dijkstra = search(use_heuristic=False)
    astar = search(use_heuristic=True)
    return {
        "width": width,
        "height": height,
        "start": start,
        "goal": goal,
        "obstacles": obstacles,
        "dijkstra": dijkstra,
        "astar": astar,
        "expansion_reduction": (len(dijkstra["expanded"]) - len(astar["expanded"]))
        / len(dijkstra["expanded"]),
    }


def _cp_search_probe() -> dict[str, object]:
    size = 4
    initial_domains = tuple(tuple(range(size)) for _ in range(size))
    events: list[dict[str, object]] = []
    nodes = 0
    pruned_values = 0
    conflicts = 0
    backtracks = 0

    def search(
        domains: tuple[tuple[int, ...], ...],
        assignments: tuple[tuple[int, int], ...],
    ) -> tuple[tuple[int, int], ...] | None:
        nonlocal nodes, pruned_values, conflicts, backtracks
        assigned = dict(assignments)
        if len(assigned) == size:
            events.append(
                {
                    "action": "solution",
                    "assignments": assignments,
                    "domains": domains,
                }
            )
            return assignments

        row = min(
            (candidate for candidate in range(size) if candidate not in assigned),
            key=lambda candidate: (len(domains[candidate]), candidate),
        )
        for column in domains[row]:
            nodes += 1
            next_domains = [tuple(values) for values in domains]
            pruned_values += len(next_domains[row]) - 1
            next_domains[row] = (column,)
            next_assignments = tuple(sorted((*assignments, (row, column))))
            next_assigned = dict(next_assignments)
            removed: list[tuple[int, int]] = []
            conflict_row: int | None = None

            for other_row in range(size):
                if other_row in next_assigned:
                    continue
                previous = next_domains[other_row]
                filtered = tuple(
                    candidate
                    for candidate in previous
                    if candidate != column and abs(candidate - column) != abs(other_row - row)
                )
                removed.extend(
                    (other_row, candidate) for candidate in previous if candidate not in filtered
                )
                pruned_values += len(previous) - len(filtered)
                next_domains[other_row] = filtered
                if not filtered and conflict_row is None:
                    conflict_row = other_row

            next_domain_tuple = tuple(next_domains)
            events.append(
                {
                    "action": "assign",
                    "row": row,
                    "column": column,
                    "assignments": next_assignments,
                    "domains": next_domain_tuple,
                    "removed": tuple(removed),
                    "conflict_row": conflict_row,
                }
            )
            if conflict_row is not None:
                conflicts += 1
                events.append(
                    {
                        "action": "conflict",
                        "row": conflict_row,
                        "assignments": next_assignments,
                        "domains": next_domain_tuple,
                    }
                )
                continue

            solution = search(next_domain_tuple, next_assignments)
            if solution is not None:
                return solution

        backtracks += 1
        events.append(
            {
                "action": "backtrack",
                "row": row,
                "assignments": assignments,
                "domains": domains,
            }
        )
        return None

    solution = search(initial_domains, ())
    assert solution is not None
    return {
        "size": size,
        "initial_domains": initial_domains,
        "events": tuple(events),
        "solution": solution,
        "nodes": nodes,
        "pruned_values": pruned_values,
        "conflicts": conflicts,
        "backtracks": backtracks,
    }


def _cp_search_propagation_svg(dataset_version: str) -> str:
    probe = _cp_search_probe()
    events = probe["events"]
    assert isinstance(events, tuple)
    stages = (
        {
            "title": "1. まだ決めていない",
            "subtitle": "各queenのdomainは0–3",
            "domains": probe["initial_domains"],
            "assignments": (),
            "conflict_row": None,
            "accent": "#102a2e",
        },
        {
            "title": "2. Q1 = 0 を仮決定",
            "subtitle": "攻撃される6値を除く",
            "domains": events[0]["domains"],
            "assignments": events[0]["assignments"],
            "conflict_row": None,
            "accent": "#d77b42",
        },
        {
            "title": "3. domainが空になる",
            "subtitle": "Q4に置けず、この枝を戻る",
            "domains": events[4]["domains"],
            "assignments": events[4]["assignments"],
            "conflict_row": events[4]["conflict_row"],
            "accent": "#a24c3d",
        },
        {
            "title": "4. Q1 = 1 から解へ",
            "subtitle": "全domainが単一値になる",
            "domains": events[-1]["domains"],
            "assignments": events[-1]["assignments"],
            "conflict_row": None,
            "accent": "#2c7564",
        },
    )
    title = "値を消してから、残った枝だけを探す"
    body, y = _figure_heading(title, "4-Queens・forward checking・残りの候補が最少の変数から")
    legend_y = y + 14
    for index, (fill, stroke, label) in enumerate(
        (
            ("#2c7564", "#2c7564", "確定した値"),
            ("#f5e4d7", "#d77b42", "残っている候補"),
            ("#f4ded9", "#a24c3d", "空のdomain／矛盾"),
        )
    ):
        key_x = FIGURE_MARGIN + (index % 2) * 190
        key_y = legend_y + (index // 2) * 26
        body.extend(
            [
                f'<rect x="{key_x}" y="{key_y - 14:g}" width="18" height="18" rx="5" '
                f'fill="{fill}" stroke="{stroke}"/>',
                f'<text x="{key_x + 26}" y="{key_y:g}" class="axis">{label}</text>',
            ]
        )
    y = legend_y + 26 + 6
    text_x = FIGURE_MARGIN + 14
    grid_label_x, chip_x0, chip_step, chip_width, row_step = 226, 252, 38, 32, 30
    for stage in stages:
        domains = stage["domains"]
        assignments = dict(stage["assignments"])
        conflict_row = stage["conflict_row"]
        assert isinstance(domains, tuple)
        panel_y = y + 10
        panel_height = 24 + len(domains) * row_step
        body.append(
            f'<rect x="{FIGURE_MARGIN}" y="{panel_y:g}" width="{CONTENT_WIDTH}" '
            f'height="{panel_height:g}" rx="12" fill="#fff" stroke="#d8ded9"/>'
        )
        heading, heading_y = _text_lines(
            text_x,
            panel_y + 30,
            str(stage["title"]),
            "panel-title",
            size=TEXT_SIZE["panel-title"],
            width=grid_label_x - text_x - 12,
            line_height=22,
        )
        for line in heading:
            body.append(
                line.replace('class="panel-title"', f'class="panel-title" fill="{stage["accent"]}"')
            )
        subtitle, _ = _text_lines(
            text_x,
            heading_y + 2,
            str(stage["subtitle"]),
            "status",
            width=grid_label_x - text_x - 12,
            line_height=20,
        )
        body.extend(subtitle)
        for row, domain in enumerate(domains):
            row_y = panel_y + 12 + row * row_step
            body.append(
                f'<text x="{grid_label_x}" y="{row_y + 17:g}" class="metric">Q{row + 1}</text>'
            )
            if row == conflict_row:
                span = 3 * chip_step + chip_width
                body.extend(
                    [
                        (
                            f'<rect x="{chip_x0}" y="{row_y:g}" width="{span}" height="24" '
                            'rx="7" fill="#f4ded9" stroke="#a24c3d"/>'
                        ),
                        (
                            f'<text x="{chip_x0 + span / 2:g}" y="{row_y + 17:g}" '
                            'text-anchor="middle" class="metric-value" fill="#a24c3d">∅</text>'
                        ),
                    ]
                )
                continue
            for column in range(4):
                chip_x = chip_x0 + column * chip_step
                available = column in domain
                assigned = assignments.get(row) == column
                fill = "#2c7564" if assigned else "#f5e4d7" if available else "#f0f1ed"
                stroke = "#2c7564" if assigned else "#d77b42" if available else "#d8ded9"
                text_fill = "#fff" if assigned else "#26352d" if available else "#a8afa9"
                body.extend(
                    [
                        (
                            f'<rect x="{chip_x}" y="{row_y:g}" width="{chip_width}" height="24" '
                            f'rx="7" fill="{fill}" stroke="{stroke}"/>'
                        ),
                        (
                            f'<text x="{chip_x + chip_width / 2:g}" y="{row_y + 17:g}" '
                            f'text-anchor="middle" class="metric-value" fill="{text_fill}">'
                            f"{column}</text>"
                        ),
                    ]
                )
        y = panel_y + panel_height
    heading, y = _text_lines(
        FIGURE_MARGIN,
        y + 36,
        "探索木は、空domainの枝をその場で捨てる",
        "panel-title",
        size=TEXT_SIZE["panel-title"],
    )
    body.extend(heading)

    def node(
        center_x: float,
        top: float,
        width: float,
        lines: tuple[tuple[str, str, str], ...],
        fill: str,
        stroke: str,
    ) -> list[str]:
        height = 12 + 21 * len(lines)
        parts = [
            f'<rect x="{center_x - width / 2:g}" y="{top:g}" width="{width:g}" '
            f'height="{height:g}" rx="12" fill="{fill}" stroke="{stroke}"/>'
        ]
        for index, (text, css_class, color) in enumerate(lines):
            color_attribute = f' fill="{color}"' if color else ""
            parts.append(
                f'<text x="{center_x:g}" y="{top + 22 + 21 * index:g}" text-anchor="middle" '
                f'class="{css_class}"{color_attribute}>{text}</text>'
            )
        return parts

    root_top = y + 2
    branch_top = root_top + 70
    leaf_top = branch_top + 74
    root_x, left_x, right_x = 220.0, 142.0, 340.0
    leaf_left, leaf_middle = 80.0, 207.0
    body.extend(
        [
            f'<line x1="{root_x:g}" y1="{root_top + 33:g}" x2="{left_x:g}" y2="{branch_top:g}" '
            'stroke="#d77b42" stroke-width="2.5"/>',
            f'<line x1="{root_x:g}" y1="{root_top + 33:g}" x2="{right_x:g}" y2="{branch_top:g}" '
            'stroke="#2c7564" stroke-width="2.5"/>',
            f'<line x1="{left_x:g}" y1="{branch_top + 33:g}" x2="{leaf_left:g}" '
            f'y2="{leaf_top:g}" stroke="#a24c3d" stroke-width="2"/>',
            f'<line x1="{left_x:g}" y1="{branch_top + 33:g}" x2="{leaf_middle:g}" '
            f'y2="{leaf_top:g}" stroke="#a24c3d" stroke-width="2"/>',
            f'<line x1="{right_x:g}" y1="{branch_top + 33:g}" x2="{right_x:g}" '
            f'y2="{leaf_top:g}" stroke="#2c7564" stroke-width="2.5"/>',
            *node(root_x, root_top, 88, (("Q1", "metric-value", ""),), "#fff", "#102a2e"),
            *node(left_x, branch_top, 104, (("Q1 = 0", "metric-value", ""),), "#f5e4d7", "#d77b42"),
            *node(
                right_x, branch_top, 104, (("Q1 = 1", "metric-value", ""),), "#d8e5df", "#2c7564"
            ),
            *node(
                leaf_left,
                leaf_top,
                120,
                (("Q2 = 2", "status", ""), ("Q3 = ∅", "metric-value", "#a24c3d")),
                "#f4ded9",
                "#a24c3d",
            ),
            *node(
                leaf_middle,
                leaf_top,
                128,
                (("Q2 = 3, Q3 = 1", "status", ""), ("Q4 = ∅", "metric-value", "#a24c3d")),
                "#f4ded9",
                "#a24c3d",
            ),
            *node(
                right_x,
                leaf_top,
                140,
                (("Q2 = 3 → Q3 = 0", "status", ""), ("Q4 = 2 · 解", "metric-value", "#2c7564")),
                "#d8e5df",
                "#2c7564",
            ),
        ]
    )
    stats, y = _text_lines(
        FIGURE_MARGIN,
        leaf_top + 54 + 34,
        f"試したノード {probe['nodes']} · 削った値 {probe['pruned_values']} · "
        f"矛盾 {probe['conflicts']} · 後戻り {probe['backtracks']}",
        "metric",
        size=TEXT_SIZE["metric"],
    )
    body.extend(stats)
    footer, height = _figure_footer(
        y + 4,
        f"scripts/generate_article_figures.py::_cp_search_probe · dataset {dataset_version}",
        "固定した4-Queensのforward checkingです。実際のsolverのglobal constraint、学習、"
        "restartの性能は示しません。",
    )
    body.extend(footer)
    return _figure_document(
        "制約プログラミング探索の固定実行",
        (
            "4-Queensをforward checkingと、残りの候補が最少の変数から選ぶbranchingで解く。"
            "全行が0から3の列候補を持つ初期状態から、Q1イコール0の枝で値を削り、"
            "Q4のdomainが空になってbacktrackする。その後Q1イコール1の枝で"
            "解1、3、0、2へ到達する。"
        ),
        height,
        body,
    )


def _dynamic_programming_knapsack_probe() -> dict[str, object]:
    items = (
        ("A", 4, 8),
        ("B", 3, 5),
        ("C", 5, 6),
        ("D", 2, 4),
    )
    capacity = 8
    table = [[0] * (capacity + 1) for _ in range(len(items) + 1)]
    take = [[False] * (capacity + 1) for _ in range(len(items) + 1)]

    for item_count, (_, weight, value) in enumerate(items, start=1):
        for available_capacity in range(capacity + 1):
            skip_value = table[item_count - 1][available_capacity]
            take_value = (
                table[item_count - 1][available_capacity - weight] + value
                if weight <= available_capacity
                else -1
            )
            if take_value > skip_value:
                table[item_count][available_capacity] = take_value
                take[item_count][available_capacity] = True
            else:
                table[item_count][available_capacity] = skip_value

    remaining_capacity = capacity
    selected: list[int] = []
    backtrack = [(len(items), remaining_capacity)]
    for item_count in range(len(items), 0, -1):
        if take[item_count][remaining_capacity]:
            selected.append(item_count - 1)
            remaining_capacity -= items[item_count - 1][1]
        backtrack.append((item_count - 1, remaining_capacity))
    selected.reverse()

    return {
        "items": items,
        "capacity": capacity,
        "table": tuple(tuple(row) for row in table),
        "take": tuple(tuple(row) for row in take),
        "selected": tuple(selected),
        "backtrack": tuple(backtrack),
        "optimal_value": table[-1][-1],
        "selected_weight": sum(items[index][1] for index in selected),
        "unused_capacity": remaining_capacity,
    }


def _dynamic_programming_knapsack_svg(dataset_version: str) -> str:
    probe = _dynamic_programming_knapsack_probe()
    items = probe["items"]
    table = probe["table"]
    selected = probe["selected"]
    backtrack = probe["backtrack"]
    if not all(isinstance(value, tuple) for value in (items, table, selected, backtrack)):
        raise TypeError("dynamic-programming teaching probe collections must be tuples")

    selected_indices = set(selected)
    maximum_value = int(probe["optimal_value"])
    capacity_limit = int(probe["capacity"])
    title = "小さな部分問題を再利用し、最後に選択を戻す"
    body, y = _figure_heading(title, "0/1 knapsack・品物4個・容量8・整数の厳密な表")
    card_width, card_height, gap = (CONTENT_WIDTH - 10) / 2, 62.0, 10.0
    cards_top = y + 8
    for index, (name, weight, value) in enumerate(items):
        x = FIGURE_MARGIN + (index % 2) * (card_width + gap)
        card_y = cards_top + (index // 2) * (card_height + gap)
        chosen = index in selected_indices
        body.extend(
            [
                f'<rect x="{x:g}" y="{card_y:g}" width="{card_width:g}" height="{card_height:g}" '
                f'rx="12" fill="{"#e3f0ea" if chosen else "#fff"}" '
                f'stroke="{"#2c7564" if chosen else "#cad8d2"}" stroke-width="2"/>',
                f'<text x="{x + 14:g}" y="{card_y + 26:g}" class="panel-title">{name}</text>',
                f'<text x="{x + card_width - 12:g}" y="{card_y + 26:g}" text-anchor="end" '
                f'class="method" fill="{"#2c7564" if chosen else "#8a958f"}">'
                f"{'選択' if chosen else '未選択'}</text>",
                f'<text x="{x + 14:g}" y="{card_y + 50:g}" class="status">'
                f"重さ {weight} · 価値 {value}</text>",
            ]
        )
    cell_width, cell_height = 36.0, 36.0
    grid_left = FIGURE_WIDTH - FIGURE_MARGIN - 14 - cell_width * (capacity_limit + 1)
    panel, top, panel_bottom = _panel(
        cards_top + 2 * card_height + gap + 12,
        "考えた品物 × 容量ごとの最大価値",
        30 + 28 + cell_height * len(table) + 12,
    )
    body.extend(panel)
    key_y = top + 4
    body.extend(
        [
            f'<rect x="{FIGURE_MARGIN + 14}" y="{key_y - 13:g}" width="16" height="16" rx="3" '
            'fill="#f0c8a6"/>',
            f'<text x="{FIGURE_MARGIN + 38}" y="{key_y:g}" class="note">大きい価値</text>',
            f'<line x1="{FIGURE_MARGIN + 150}" y1="{key_y - 5:g}" x2="{FIGURE_MARGIN + 176}" '
            f'y2="{key_y - 5:g}" stroke="#2c7564" stroke-width="3"/>',
            f'<text x="{FIGURE_MARGIN + 184}" y="{key_y:g}" class="note">選択を戻る道筋</text>',
        ]
    )
    grid_top = top + 30 + 28
    body.append(
        f'<text x="{grid_left - 8:g}" y="{grid_top - 10:g}" text-anchor="end" class="axis">'
        "容量</text>"
    )
    for capacity in range(capacity_limit + 1):
        center_x = grid_left + capacity * cell_width + cell_width / 2
        body.append(
            f'<text x="{center_x:.2f}" y="{grid_top - 10:g}" text-anchor="middle" '
            f'class="axis">{capacity}</text>'
        )
    row_labels = ("なし", "A", "A+B", "A〜C", "A〜D")
    path_cells = set(backtrack)
    final_cell = (len(table) - 1, capacity_limit)

    def cell_center(row: int, capacity: int) -> tuple[float, float]:
        return (
            grid_left + capacity * cell_width + cell_width / 2,
            grid_top + row * cell_height + cell_height / 2,
        )

    numbers = []
    for row_index, row in enumerate(table):
        _, center_y = cell_center(row_index, 0)
        body.append(
            f'<text x="{grid_left - 8:g}" y="{center_y + 5:.2f}" text-anchor="end" '
            f'class="axis">{row_labels[row_index]}</text>'
        )
        for capacity, value in enumerate(row):
            x = grid_left + capacity * cell_width
            cell_y = grid_top + row_index * cell_height
            intensity = int(value) / maximum_value if maximum_value else 0.0
            fill = "#fff" if value == 0 else ("#f7e2cf" if intensity < 0.7 else "#f0c8a6")
            if (row_index, capacity) == final_cell:
                fill = "#2c7564"
            body.append(
                f'<rect x="{x:.2f}" y="{cell_y:.2f}" width="{cell_width:g}" '
                f'height="{cell_height:g}" fill="{fill}" stroke="#d7e0dc"/>'
            )
            final = (row_index, capacity) == final_cell
            if final:
                number_style = 'class="metric-value" fill="#fff"'
            elif (row_index, capacity) in path_cells:
                number_style = 'class="metric-value halo"'
            else:
                number_style = 'class="metric-value"'
            numbers.append(
                f'<text x="{x + cell_width / 2:.2f}" y="{cell_y + cell_height / 2 + 6:.2f}" '
                f'text-anchor="middle" {number_style}>{value}</text>'
            )
    backtrack_points = " ".join(
        "{:.2f},{:.2f}".format(*cell_center(row, capacity)) for row, capacity in backtrack
    )
    body.append(
        f'<polyline points="{backtrack_points}" fill="none" stroke="#2c7564" '
        'stroke-width="3" stroke-linecap="round" stroke-linejoin="round" opacity="0.7"/>'
    )
    for row, capacity in sorted(path_cells):
        x = grid_left + capacity * cell_width
        cell_y = grid_top + row * cell_height
        body.append(
            f'<rect x="{x + 2:.2f}" y="{cell_y + 2:.2f}" width="{cell_width - 4:g}" '
            f'height="{cell_height - 4:g}" rx="4" fill="none" stroke="#2c7564" '
            'stroke-width="2.5"/>'
        )
    body.extend(numbers)
    chosen_items = [items[index] for index in sorted(selected_indices)]
    rows, y = _metric_rows(
        panel_bottom + 34,
        (
            ("選んだ品物", " + ".join(str(name) for name, _, _ in chosen_items)),
            ("重さの合計", f"{int(probe['selected_weight'])} / {capacity_limit}"),
            ("最適な価値", f"{maximum_value}"),
        ),
    )
    body.extend(rows)
    result, y = _text_lines(
        FIGURE_MARGIN,
        y + 6,
        "戻った結果: "
        + " + ".join(
            f"{name}（重さ {weight}、価値 {value}）" for name, weight, value in chosen_items
        )
        + f" · 未使用の容量 {int(probe['unused_capacity'])}",
        "status",
    )
    body.extend(result)
    footer, height = _figure_footer(
        y + 6,
        "scripts.generate_article_figures._dynamic_programming_knapsack_probe"
        f" · dataset {dataset_version}",
        "固定した品物4個の整数knapsackです。別のinstance、連続量、近似、solver一般の性能は"
        "示しません。表の大きさはO(nC)で容量の値に依存し、大規模な状態空間での実用性は示しません。",
    )
    body.extend(footer)
    return _figure_document(
        "0/1 knapsackのDP表と選択の戻り",
        (
            "容量8の0/1 knapsackに4つの品物を順に加え、"
            "5行9列のDP表を埋める固定実行。最終の価値13から戻ると、"
            "重さ4・価値8の品物Aと重さ3・価値5の品物Bを選び、"
            "重さの合計7、未使用の容量1となる。"
        ),
        height,
        body,
    )


def _epsilon_constraint_production_probe() -> dict[str, object]:
    demand = 18
    technology_x = ("X", 3, 8, 6)
    technology_y = ("Y", 2, 7, 2)
    plans: list[tuple[int, int, int, int, int]] = []
    for x_count in range(11):
        for y_count in range(11):
            output = technology_x[1] * x_count + technology_y[1] * y_count
            if output < demand:
                continue
            cost = technology_x[2] * x_count + technology_y[2] * y_count
            emissions = technology_x[3] * x_count + technology_y[3] * y_count
            plans.append((x_count, y_count, output, cost, emissions))

    pareto = tuple(
        sorted(
            (
                plan
                for plan in plans
                if not any(
                    candidate[3] <= plan[3]
                    and candidate[4] <= plan[4]
                    and candidate[3:5] != plan[3:5]
                    for candidate in plans
                )
            ),
            key=lambda plan: plan[4],
            reverse=True,
        )
    )
    thresholds = (36, 30, 24, 18, 12)
    solutions: list[tuple[int, tuple[int, int, int, int, int] | None]] = []
    for epsilon in thresholds:
        eligible = [plan for plan in plans if plan[4] <= epsilon]
        solution = (
            min(eligible, key=lambda plan: (plan[3], plan[4], plan[0], plan[1]))
            if eligible
            else None
        )
        solutions.append((epsilon, solution))

    return {
        "demand": demand,
        "technology_x": technology_x,
        "technology_y": technology_y,
        "plans": tuple(plans),
        "pareto": pareto,
        "solutions": tuple(solutions),
        "thresholds": thresholds,
        "feasible_count": len(plans),
        "pareto_count": len(pareto),
        "solved_count": sum(solution is not None for _, solution in solutions),
    }


def _epsilon_constraint_production_svg(dataset_version: str) -> str:
    probe = _epsilon_constraint_production_probe()
    plans = probe["plans"]
    pareto = probe["pareto"]
    solutions = probe["solutions"]
    if not all(isinstance(value, tuple) for value in (plans, pareto, solutions)):
        raise TypeError("epsilon-constraint teaching probe collections must be tuples")

    title = "排出の上限を下げると、選ぶ生産計画が移る"
    body, y = _figure_heading(title, "整数の生産計画・需要 ≥ 18・costを最小化・排出 ≤ ε")
    legend_y = y + 14
    body.extend(
        [
            f'<circle cx="{FIGURE_MARGIN + 6}" cy="{legend_y - 5:g}" r="5" fill="#d67835" '
            'opacity=".55"/>',
            f'<text x="{FIGURE_MARGIN + 18}" y="{legend_y:g}" class="note">実行可能な計画</text>',
            f'<line x1="{FIGURE_MARGIN + 138}" y1="{legend_y - 5:g}" x2="{FIGURE_MARGIN + 162}" '
            f'y2="{legend_y - 5:g}" stroke="#2c7564" stroke-width="4"/>',
            f'<text x="{FIGURE_MARGIN + 170}" y="{legend_y:g}" class="note">Pareto front</text>',
            f'<circle cx="{FIGURE_MARGIN + 284}" cy="{legend_y - 5:g}" r="6.5" fill="#2c7564"/>',
            f'<text x="{FIGURE_MARGIN + 296}" y="{legend_y:g}" class="note">εごとの解</text>',
        ]
    )
    panel, top, panel_bottom = _panel(legend_y + 14, "目的空間（左下ほど良い）", 300)
    body.extend(panel)
    plot_left, plot_right = 64.0, 404.0
    plot_top, plot_bottom = top + 10, top + 250
    cost_min, cost_max = 45.0, 152.0
    emissions_min, emissions_max = 15.0, 82.0

    def cost_x(cost: int) -> float:
        return plot_left + (cost - cost_min) / (cost_max - cost_min) * (plot_right - plot_left)

    def emissions_y(emissions: int) -> float:
        return plot_bottom - (emissions - emissions_min) / (emissions_max - emissions_min) * (
            plot_bottom - plot_top
        )

    selected_plans = {solution for _, solution in solutions if solution is not None}
    pareto_points = " ".join(f"{cost_x(plan[3]):.2f},{emissions_y(plan[4]):.2f}" for plan in pareto)
    for cost_tick in (50, 75, 100, 125, 150):
        x = cost_x(cost_tick)
        body.extend(
            [
                f'<line x1="{x:.2f}" y1="{plot_top:g}" x2="{x:.2f}" y2="{plot_bottom:g}" '
                'stroke="#e4ebe7"/>',
                f'<text x="{x:.2f}" y="{plot_bottom + 20:g}" text-anchor="middle" '
                f'class="axis">{cost_tick}</text>',
            ]
        )
    for emissions_tick in (20, 40, 60, 80):
        tick_y = emissions_y(emissions_tick)
        body.extend(
            [
                f'<line x1="{plot_left:g}" y1="{tick_y:.2f}" x2="{plot_right:g}" '
                f'y2="{tick_y:.2f}" stroke="#e4ebe7"/>',
                f'<text x="{plot_left - 8:g}" y="{tick_y + 5:.2f}" text-anchor="end" '
                f'class="axis">{emissions_tick}</text>',
            ]
        )
    for plan in plans:
        if plan in selected_plans:
            continue
        body.append(
            f'<circle cx="{cost_x(plan[3]):.2f}" cy="{emissions_y(plan[4]):.2f}" r="3" '
            'fill="#d67835" opacity=".34"/>'
        )
    body.append(
        f'<polyline points="{pareto_points}" fill="none" stroke="#2c7564" '
        'stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>'
    )
    for epsilon, plan in solutions:
        if plan is None:
            continue
        x = cost_x(plan[3])
        point_y = emissions_y(plan[4])
        body.extend(
            [
                f'<circle cx="{x:.2f}" cy="{point_y:.2f}" r="6.5" fill="#2c7564" '
                'stroke="#fff" stroke-width="2"/>',
                f'<text x="{x + 10:.2f}" y="{point_y - 8:.2f}" class="method halo" '
                f'fill="#245c42">ε {epsilon}</text>',
            ]
        )
    body.append(
        f'<text x="{plot_right:g}" y="{plot_bottom + 42:g}" text-anchor="end" class="axis">'
        "横軸 cost →、縦軸 排出 →</text>"
    )
    columns = (FIGURE_MARGIN + 14, FIGURE_MARGIN + 64, FIGURE_MARGIN + 190, FIGURE_MARGIN + 380)
    panel, top, panel_bottom = _panel(
        panel_bottom + 12, "排出の上限ごとに1つの部分問題", 34 + 30 * len(solutions)
    )
    body.extend(panel)
    for column_x, heading, anchor in zip(
        columns,
        ("ε", "状態", "計画 (X, Y)", "cost"),
        ("start", "start", "start", "end"),
        strict=True,
    ):
        body.append(
            f'<text x="{column_x}" y="{top + 6:g}" text-anchor="{anchor}" class="method">'
            f"{heading}</text>"
        )
    for row_index, (epsilon, plan) in enumerate(solutions):
        row_y = top + 36 + row_index * 30.0
        if plan is None:
            status, plan_label, cost_label, color = "実行不能", "—", "—", "#a34f43"
        else:
            status, plan_label, cost_label, color = (
                "最適",
                f"({plan[0]}, {plan[1]})",
                str(plan[3]),
                "#2c7564",
            )
        body.extend(
            [
                f'<line x1="{FIGURE_MARGIN + 14}" y1="{row_y - 20:g}" '
                f'x2="{FIGURE_WIDTH - FIGURE_MARGIN - 14}" y2="{row_y - 20:g}" stroke="#edf1ef"/>',
                f'<text x="{columns[0]}" y="{row_y:g}" class="metric">{epsilon}</text>',
                f'<text x="{columns[1]}" y="{row_y:g}" class="metric-value" fill="{color}">'
                f"{status}</text>",
                f'<text x="{columns[2]}" y="{row_y:g}" class="metric">{plan_label}</text>',
                f'<text x="{columns[3]}" y="{row_y:g}" text-anchor="end" class="metric">'
                f"{cost_label}</text>",
            ]
        )
    rows, y = _metric_rows(
        panel_bottom + 34,
        (
            ("実行可能な計画", f"{int(probe['feasible_count'])}"),
            ("Pareto最適な計画", f"{int(probe['pareto_count'])}"),
            ("解けた上限", f"{int(probe['solved_count'])} / {len(solutions)}"),
        ),
    )
    body.extend(rows)
    footer, height = _figure_footer(
        y + 8,
        "scripts.generate_article_figures._epsilon_constraint_production_probe"
        f" · dataset {dataset_version}",
        "固定した整数の列挙です。別の需要、連続変数、backend solver、上限の決め方、"
        "一般的な性能は示しません。",
    )
    body.extend(footer)
    return _figure_document(
        "ε-constraintで生産計画のcostと排出を選ぶ固定実行",
        (
            "需要18以上を満たす技術XとYの整数の生産計画を"
            "88個列挙し、cost最小化を主目的、排出を上限制約として解く。"
            "排出の上限36、30、24、18では異なる4つのPareto最適な計画を選ぶ。"
            "上限12では実行可能な計画がない。"
        ),
        height,
        body,
    )


def _dijkstra_astar_grid_svg(dataset_version: str) -> str:
    probe = _dijkstra_astar_grid_probe()
    obstacles = probe["obstacles"]
    dijkstra = probe["dijkstra"]
    astar = probe["astar"]
    if (
        not isinstance(obstacles, tuple)
        or not isinstance(dijkstra, dict)
        or not isinstance(astar, dict)
    ):
        raise TypeError("Dijkstra/A* teaching probe has invalid collections")

    grid_columns = int(probe["width"])
    grid_rows = int(probe["height"])
    cell_size = 22.0
    grid_left = (FIGURE_WIDTH - grid_columns * cell_size) / 2

    def grid_elements(result: dict[str, object], *, grid_top: float) -> list[str]:
        expanded = result["expanded"]
        path = result["path"]
        if not isinstance(expanded, tuple) or not isinstance(path, tuple):
            raise TypeError("Dijkstra/A* result collections must be tuples")
        expanded_order = {node: index for index, node in enumerate(expanded)}
        path_nodes = set(path)
        obstacle_nodes = set(obstacles)
        elements: list[str] = []
        for row in range(grid_rows):
            for column in range(grid_columns):
                node = (column, row)
                x = grid_left + column * cell_size
                y = grid_top + row * cell_size
                fill = "#ffffff"
                if node in obstacle_nodes:
                    fill = "#243f49"
                elif node in expanded_order:
                    progress = expanded_order[node] / max(1, len(expanded) - 1)
                    fill = "#f0c8a6" if progress < 0.5 else "#f7e2cf"
                if node in path_nodes:
                    fill = "#73b7a2"
                elements.append(
                    f'<rect x="{x:.2f}" y="{y:.2f}" width="{cell_size:.2f}" '
                    f'height="{cell_size:.2f}" fill="{fill}" stroke="#d7e0dc" '
                    'stroke-width="1"/>'
                )
        path_points = " ".join(
            (
                f"{grid_left + node[0] * cell_size + cell_size / 2:.2f},"
                f"{grid_top + node[1] * cell_size + cell_size / 2:.2f}"
            )
            for node in path
        )
        elements.append(
            f'<polyline points="{path_points}" fill="none" stroke="#236956" '
            'stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>'
        )
        for node, label, fill in (
            (probe["start"], "S", "#102a2e"),
            (probe["goal"], "G", "#2c7564"),
        ):
            node_x, node_y = node
            center_x = grid_left + int(node_x) * cell_size + cell_size / 2
            center_y = grid_top + int(node_y) * cell_size + cell_size / 2
            elements.extend(
                [
                    f'<circle cx="{center_x:.2f}" cy="{center_y:.2f}" r="10.5" fill="{fill}"/>',
                    f'<text x="{center_x:.2f}" y="{center_y + 5:.2f}" text-anchor="middle" '
                    f'class="method" fill="#fff">{label}</text>',
                ]
            )
        return elements

    dijkstra_expanded = len(dijkstra["expanded"])
    astar_expanded = len(astar["expanded"])
    title = "同じcost 24でも、探した範囲は違う"
    body, y = _figure_heading(title, "17 × 11の格子・辺のcostは1・4近傍の移動・Manhattan距離のh")
    legend_y = y + 14
    for offset, (fill, label) in zip(
        (0, 120, 266),
        (("#f0c8a6", "展開したセル"), ("#73b7a2", "最短路"), ("#243f49", "障害物")),
        strict=True,
    ):
        body.extend(
            [
                f'<rect x="{FIGURE_MARGIN + offset}" y="{legend_y - 13:g}" width="16" height="16" '
                f'rx="3" fill="{fill}"/>',
                f'<text x="{FIGURE_MARGIN + offset + 24}" y="{legend_y:g}" class="note">'
                f"{label}</text>",
            ]
        )
    y = legend_y + 2
    for name, result, count in (
        ("Dijkstra · h(n) = 0", dijkstra, dijkstra_expanded),
        ("A* · Manhattan h(n)", astar, astar_expanded),
    ):
        panel, top, panel_bottom = _panel(y + 12, name, grid_rows * cell_size + 18)
        body.extend(panel)
        body.append(
            f'<text x="{FIGURE_WIDTH - FIGURE_MARGIN - 14}" y="{top - 18:g}" text-anchor="end" '
            f'class="metric-value" fill="#2c7564">{count}セルを展開</text>'
        )
        body.extend(grid_elements(result, grid_top=top + 2))
        y = panel_bottom
    rows, y = _metric_rows(
        y + 34,
        (
            ("最短路のcost", f"{int(dijkstra['cost'])} = {int(astar['cost'])}"),
            ("展開したセル", f"{dijkstra_expanded} → {astar_expanded}"),
            ("減少率", f"{float(probe['expansion_reduction']):.0%}"),
        ),
    )
    body.extend(rows)
    footer, height = _figure_footer(
        y + 8,
        f"scripts.generate_article_figures._dijkstra_astar_grid_probe · dataset {dataset_version}",
        "辺のcostが1の固定した格子です。別のgraph、重み、同点の扱い、heuristic一般での展開の"
        "減り方は示しません。Manhattan距離のhはこの4近傍の設定でadmissibleです。"
        "追加の制約は含みません。",
    )
    body.extend(footer)
    return _figure_document(
        "Dijkstra法とA*探索の展開範囲を比較する固定格子の実行",
        (
            "17列11行の4近傍の格子で、同じ始点と終点を"
            "Dijkstra法とManhattan距離のheuristicを使うA*で探索する。両者の最短路のcostは24。"
            f"Dijkstra法は{dijkstra_expanded}セル、A*は{astar_expanded}セルを展開し、"
            "A*は終点の方向へ探索範囲を絞る。"
        ),
        height,
        body,
    )


def _tour_length(
    tour: tuple[int, ...],
    points: tuple[tuple[float, float], ...],
) -> float:
    return sum(
        math.hypot(
            points[tour[(index + 1) % len(tour)]][0] - points[tour[index]][0],
            points[tour[(index + 1) % len(tour)]][1] - points[tour[index]][1],
        )
        for index in range(len(tour))
    )


def _tour_crossings(
    tour: tuple[int, ...],
    points: tuple[tuple[float, float], ...],
) -> int:
    def orientation(
        first: tuple[float, float],
        second: tuple[float, float],
        third: tuple[float, float],
    ) -> float:
        return (second[0] - first[0]) * (third[1] - first[1]) - (second[1] - first[1]) * (
            third[0] - first[0]
        )

    crossings = 0
    size = len(tour)
    for first_index in range(size):
        first_start = points[tour[first_index]]
        first_end = points[tour[(first_index + 1) % size]]
        for second_index in range(first_index + 1, size):
            if (second_index + 1) % size == first_index or (first_index + 1) % size == second_index:
                continue
            second_start = points[tour[second_index]]
            second_end = points[tour[(second_index + 1) % size]]
            if (
                orientation(first_start, first_end, second_start)
                * orientation(first_start, first_end, second_end)
                < 0.0
                and orientation(second_start, second_end, first_start)
                * orientation(second_start, second_end, first_end)
                < 0.0
            ):
                crossings += 1
    return crossings


def _local_search_two_opt_probe() -> dict[str, object]:
    points = (
        (0.0, 0.0),
        (2.0, 0.3),
        (4.2, 0.0),
        (4.5, 2.0),
        (4.0, 4.2),
        (2.1, 4.5),
        (-0.2, 4.0),
        (-0.5, 2.0),
    )
    initial_tour = (0, 2, 4, 6, 1, 3, 5, 7)
    tour = initial_tour
    history: list[dict[str, object]] = [
        {
            "iteration": 0,
            "tour": tour,
            "length": _tour_length(tour, points),
            "move": None,
            "crossings": _tour_crossings(tour, points),
        }
    ]
    evaluated_candidates = 0

    while True:
        best_tour = tour
        best_length = _tour_length(tour, points)
        best_move: tuple[int, int] | None = None
        for start in range(1, len(tour) - 1):
            for stop in range(start + 1, len(tour)):
                evaluated_candidates += 1
                candidate = (
                    tour[:start] + tuple(reversed(tour[start : stop + 1])) + tour[stop + 1 :]
                )
                candidate_length = _tour_length(candidate, points)
                if candidate_length < best_length - 1e-12:
                    best_tour = candidate
                    best_length = candidate_length
                    best_move = (start, stop)
        if best_move is None:
            break
        tour = best_tour
        history.append(
            {
                "iteration": len(history),
                "tour": tour,
                "length": best_length,
                "move": best_move,
                "crossings": _tour_crossings(tour, points),
            }
        )

    initial_length = float(history[0]["length"])
    final_length = float(history[-1]["length"])
    return {
        "points": points,
        "initial_tour": initial_tour,
        "final_tour": tour,
        "history": tuple(history),
        "initial_length": initial_length,
        "final_length": final_length,
        "relative_improvement": (initial_length - final_length) / initial_length,
        "accepted_moves": len(history) - 1,
        "evaluated_candidates": evaluated_candidates,
        "initial_crossings": history[0]["crossings"],
        "final_crossings": history[-1]["crossings"],
    }


def _local_search_two_opt_svg(dataset_version: str) -> str:
    probe = _local_search_two_opt_probe()
    points = probe["points"]
    initial_tour = probe["initial_tour"]
    final_tour = probe["final_tour"]
    history = probe["history"]
    if not all(
        isinstance(values, tuple)
        for values in (
            points,
            initial_tour,
            final_tour,
            history,
        )
    ):
        raise TypeError("local-search teaching probe collections must be tuples")

    plot_left, plot_right = 70.0, 370.0
    point_min_x, point_max_x = -0.5, 4.5
    point_min_y, point_max_y = 0.0, 4.5
    plot_height = (plot_right - plot_left) * 254 / 472

    def point_position(
        point: tuple[float, float],
        *,
        plot_top: float,
        plot_bottom: float,
    ) -> tuple[float, float]:
        x = plot_left + (point[0] - point_min_x) / (point_max_x - point_min_x) * (
            plot_right - plot_left
        )
        y = plot_bottom - (point[1] - point_min_y) / (point_max_y - point_min_y) * (
            plot_bottom - plot_top
        )
        return x, y

    def route_elements(
        tour: tuple[int, ...],
        *,
        plot_top: float,
        plot_bottom: float,
        color: str,
    ) -> list[str]:
        route_points = [
            point_position(points[node], plot_top=plot_top, plot_bottom=plot_bottom)
            for node in (*tour, tour[0])
        ]
        polyline = " ".join(f"{x:.2f},{y:.2f}" for x, y in route_points)
        elements = [
            f'<polyline points="{polyline}" fill="none" stroke="{color}" stroke-width="3.5" '
            'stroke-linecap="round" stroke-linejoin="round"/>'
        ]
        for node, point in enumerate(points):
            x, y = point_position(point, plot_top=plot_top, plot_bottom=plot_bottom)
            fill = "#102a2e" if node == 0 else "#fff"
            text_color = "#fff" if node == 0 else "#102a2e"
            elements.extend(
                [
                    f'<circle cx="{x:.2f}" cy="{y:.2f}" r="12" fill="{fill}" '
                    f'stroke="{color}" stroke-width="3"/>',
                    f'<text x="{x:.2f}" y="{y + 5:.2f}" text-anchor="middle" '
                    f'class="metric-value" fill="{text_color}">{node}</text>',
                ]
            )
        return elements

    title = "辺を2本つなぎ替え、交差をほどく"
    body, y = _figure_heading(title, "固定した8地点の巡回路・最良改善の2-opt・地点0は固定")
    panel, top, panel_bottom = _panel(y + 8, "前: 入力の順番", plot_height + 40)
    body.extend(panel)
    body.append(
        f'<text x="{FIGURE_WIDTH - FIGURE_MARGIN - 14}" y="{top - 18:g}" text-anchor="end" '
        f'class="metric-value" fill="#8b4c3d">長さ {float(probe["initial_length"]):.2f}</text>'
    )
    body.extend(
        route_elements(
            initial_tour, plot_top=top + 14, plot_bottom=top + 14 + plot_height, color="#d67835"
        )
    )
    arrow_top = panel_bottom + 6
    body.extend(
        [
            f'<line x1="{FIGURE_WIDTH / 2:g}" y1="{arrow_top:g}" x2="{FIGURE_WIDTH / 2:g}" '
            f'y2="{arrow_top + 28:g}" stroke="#d67835" stroke-width="3"/>',
            f'<path d="M{FIGURE_WIDTH / 2 - 7:g} {arrow_top + 21:g} L{FIGURE_WIDTH / 2:g} '
            f'{arrow_top + 31:g} L{FIGURE_WIDTH / 2 + 7:g} {arrow_top + 21:g}" fill="none" '
            'stroke="#d67835" stroke-width="3"/>',
            f'<text x="{FIGURE_WIDTH / 2 + 16:g}" y="{arrow_top + 22:g}" class="method" '
            f'fill="#8b4c3d">区間の反転を{int(probe["accepted_moves"])}回受理</text>',
        ]
    )
    panel, top, panel_bottom = _panel(
        arrow_top + 40, "後: 改善する2-optの手がない", plot_height + 40
    )
    body.extend(panel)
    body.append(
        f'<text x="{FIGURE_WIDTH - FIGURE_MARGIN - 14}" y="{top - 18:g}" text-anchor="end" '
        f'class="metric-value" fill="#2c7564">長さ {float(probe["final_length"]):.2f}</text>'
    )
    body.extend(
        route_elements(
            final_tour, plot_top=top + 14, plot_bottom=top + 14 + plot_height, color="#2c7564"
        )
    )
    rows, y = _metric_rows(
        panel_bottom + 34,
        (
            (
                "巡回路の長さ",
                f"{float(probe['initial_length']):.2f} → {float(probe['final_length']):.2f}",
            ),
            ("辺の交差", f"{int(probe['initial_crossings'])} → {int(probe['final_crossings'])}"),
            ("受理した手", f"{int(probe['accepted_moves'])}回"),
        ),
    )
    body.extend(rows)
    footer, height = _figure_footer(
        y + 8,
        f"scripts.generate_article_figures._local_search_two_opt_probe · dataset {dataset_version}",
        "固定したユークリッド平面の8地点の教材です。時間枠、車両の容量、交通、大域最適性、"
        "別の初期巡回路や近傍、実際のrouting solver一般の性能は示しません。",
    )
    body.extend(footer)
    return _figure_document(
        "2-opt局所探索で交差のある巡回路を改善する実行結果",
        (
            "8地点の固定した巡回路を最良改善の2-optで改善する教材。"
            "初期の巡回路には5つの交差があり、距離は29.07。"
            "区間の反転を4回受理すると、周囲を順に回る交差0の巡回路となる。"
            "最終距離は16.88で、2-optの近傍内に改善する手がなくなる。"
        ),
        height,
        body,
    )


def _simulated_annealing_objective(x: float) -> float:
    return 10.0 + x * x - 10.0 * math.cos(2.0 * math.pi * x)


def _simulated_annealing_probe() -> dict[str, object]:
    seed = 7
    iterations = 400
    initial_temperature = 5.0
    cooling_rate = 0.985
    step_scale = 0.5
    lower_bound, upper_bound = -5.12, 5.12
    generator = random.Random(seed)

    x = 3.5
    objective = _simulated_annealing_objective(x)
    best_x, best_objective = x, objective
    temperature = initial_temperature
    history: list[dict[str, object]] = [
        {
            "iteration": 0,
            "x": x,
            "objective": objective,
            "best_x": best_x,
            "best_objective": best_objective,
            "temperature": temperature,
            "accepted": True,
            "accepted_worsening": False,
        }
    ]

    for iteration in range(1, iterations + 1):
        candidate = min(
            upper_bound,
            max(lower_bound, x + generator.gauss(0.0, step_scale)),
        )
        candidate_objective = _simulated_annealing_objective(candidate)
        delta = candidate_objective - objective
        accepted = delta <= 0.0 or generator.random() < math.exp(-delta / temperature)
        accepted_worsening = accepted and delta > 0.0
        if accepted:
            x, objective = candidate, candidate_objective
            if objective < best_objective:
                best_x, best_objective = x, objective
        history.append(
            {
                "iteration": iteration,
                "x": x,
                "objective": objective,
                "best_x": best_x,
                "best_objective": best_objective,
                "temperature": temperature,
                "accepted": accepted,
                "accepted_worsening": accepted_worsening,
            }
        )
        temperature *= cooling_rate

    accepted_moves = sum(bool(item["accepted"]) for item in history[1:])
    accepted_worsening = sum(bool(item["accepted_worsening"]) for item in history[1:])
    early_worsening = sum(bool(item["accepted_worsening"]) for item in history[1:101])
    late_worsening = sum(bool(item["accepted_worsening"]) for item in history[301:])
    return {
        "seed": seed,
        "iterations": iterations,
        "initial_x": float(history[0]["x"]),
        "initial_objective": float(history[0]["objective"]),
        "initial_temperature": initial_temperature,
        "final_temperature": temperature,
        "cooling_rate": cooling_rate,
        "step_scale": step_scale,
        "bounds": (lower_bound, upper_bound),
        "history": tuple(history),
        "best_x": best_x,
        "best_objective": best_objective,
        "accepted_moves": accepted_moves,
        "accepted_worsening": accepted_worsening,
        "early_worsening": early_worsening,
        "late_worsening": late_worsening,
    }


def _simulated_annealing_svg(dataset_version: str) -> str:
    probe = _simulated_annealing_probe()
    history = probe["history"]
    bounds = probe["bounds"]
    if not isinstance(history, tuple) or not isinstance(bounds, tuple):
        raise TypeError("simulated-annealing teaching probe collections must be tuples")

    title = "現在の点は悪化しても、最良点は手放さない"
    body, y = _figure_heading(title, "1次元Rastrigin・seed 7・400反復・初期温度 5.0・冷却率 0.985")
    legend_y = y + 14
    legend = (
        (
            '<line x1="{x}" y1="{y}" x2="{x2}" y2="{y}" stroke="#d67835" stroke-width="3"/>',
            "現在の点",
        ),
        (
            '<line x1="{x}" y1="{y}" x2="{x2}" y2="{y}" stroke="#2c7564" stroke-width="4.5"/>',
            "それまでの最良",
        ),
        (
            '<line x1="{x}" y1="{y}" x2="{x2}" y2="{y}" stroke="#345d6b" stroke-width="2.5" '
            'stroke-dasharray="6 5"/>',
            "温度（初期値で正規化）",
        ),
        (
            '<circle cx="{cx}" cy="{y}" r="5" fill="#fff" stroke="#9f552c" stroke-width="2"/>',
            "受理した悪化",
        ),
    )
    for index, (shape, label) in enumerate(legend):
        key_x = FIGURE_MARGIN + (index % 2) * 190
        key_y = legend_y + (index // 2) * 24
        body.append(shape.format(x=key_x, x2=key_x + 24, cx=key_x + 12, y=f"{key_y - 5:g}"))
        body.append(f'<text x="{key_x + 32}" y="{key_y:g}" class="note">{label}</text>')
    plot_left, plot_right = 56.0, 404.0
    lower_bound, upper_bound = (float(value) for value in bounds)
    objective_max = 42.0
    panel, top, panel_bottom = _panel(
        legend_y + 24 + 14, "受理された状態は、いくつもの谷をまたぐ", 216
    )
    body.extend(panel)
    landscape_top, landscape_bottom = top + 14, top + 184

    def position_x(value: float) -> float:
        return plot_left + (value - lower_bound) / (upper_bound - lower_bound) * (
            plot_right - plot_left
        )

    def landscape_y(value: float) -> float:
        return landscape_bottom - min(value, objective_max) / objective_max * (
            landscape_bottom - landscape_top
        )

    landscape = " ".join(
        f"{position_x(x):.2f},{landscape_y(_simulated_annealing_objective(x)):.2f}"
        for x in (lower_bound + index / 320 * (upper_bound - lower_bound) for index in range(321))
    )
    body.append(
        f'<polyline points="{landscape}" fill="none" stroke="#345d6b" '
        'stroke-width="2" stroke-linejoin="round"/>'
    )
    for item in history[1:]:
        if not bool(item["accepted"]):
            continue
        iteration = int(item["iteration"])
        opacity = 0.28 + 0.52 * (1.0 - iteration / int(probe["iterations"]))
        body.append(
            f'<circle cx="{position_x(float(item["x"])):.2f}" '
            f'cy="{landscape_y(float(item["objective"])):.2f}" r="3" '
            f'fill="#d67835" opacity="{opacity:.2f}"/>'
        )
    start_x = position_x(float(probe["initial_x"]))
    start_y = landscape_y(float(probe["initial_objective"]))
    best_x = position_x(float(probe["best_x"]))
    best_y = landscape_y(float(probe["best_objective"]))
    body.extend(
        [
            f'<circle cx="{start_x:.2f}" cy="{start_y:.2f}" r="6" fill="#102a2e"/>',
            f'<text x="{start_x - 9:.2f}" y="{start_y - 9:.2f}" text-anchor="end" '
            'class="method halo">開始点</text>',
            f'<circle cx="{best_x:.2f}" cy="{best_y:.2f}" r="6.5" fill="#2c7564"/>',
            f'<text x="{best_x + 10:.2f}" y="{best_y - 8:.2f}" class="method halo" '
            'fill="#2c7564">最良点</text>',
        ]
    )
    for tick in (-5, -3, -1, 1, 3, 5):
        body.append(
            f'<text x="{position_x(float(tick)):.2f}" y="{landscape_bottom + 22:g}" '
            f'text-anchor="middle" class="axis">{tick}</text>'
        )
    panel, top, panel_bottom = _panel(
        panel_bottom + 12, "温度は下がる。それでも現在の点は上がりうる", 230
    )
    body.extend(panel)
    trace_top, trace_bottom = top + 10, top + 190

    def iteration_x(iteration: int) -> float:
        return plot_left + iteration / int(probe["iterations"]) * (plot_right - plot_left)

    def trace_y(value: float) -> float:
        return trace_bottom - min(value, objective_max) / objective_max * (trace_bottom - trace_top)

    def temperature_y(value: float) -> float:
        ratio = value / float(probe["initial_temperature"])
        return trace_bottom - ratio * (trace_bottom - trace_top)

    for tick in (0, 10, 20, 30, 40):
        tick_y = trace_y(float(tick))
        body.extend(
            [
                f'<line x1="{plot_left:g}" y1="{tick_y:.2f}" x2="{plot_right:g}" '
                f'y2="{tick_y:.2f}" stroke="#e4ebe7" stroke-width="1"/>',
                f'<text x="{plot_left - 8:g}" y="{tick_y + 5:.2f}" text-anchor="end" '
                f'class="axis">{tick}</text>',
            ]
        )
    current_trace = " ".join(
        f"{iteration_x(int(item['iteration'])):.2f},{trace_y(float(item['objective'])):.2f}"
        for item in history
    )
    best_trace = " ".join(
        f"{iteration_x(int(item['iteration'])):.2f},{trace_y(float(item['best_objective'])):.2f}"
        for item in history
    )
    temperature_trace = " ".join(
        f"{iteration_x(int(item['iteration'])):.2f},{temperature_y(float(item['temperature'])):.2f}"
        for item in history
    )
    body.extend(
        [
            f'<polyline points="{temperature_trace}" fill="none" stroke="#345d6b" '
            'stroke-width="2.5" stroke-dasharray="6 5"/>',
            f'<polyline points="{current_trace}" fill="none" stroke="#d67835" '
            'stroke-width="2" stroke-linejoin="round"/>',
            f'<polyline points="{best_trace}" fill="none" stroke="#2c7564" '
            'stroke-width="4.5" stroke-linejoin="round"/>',
        ]
    )
    for item in history[1:]:
        if bool(item["accepted_worsening"]):
            body.append(
                f'<circle cx="{iteration_x(int(item["iteration"])):.2f}" '
                f'cy="{trace_y(float(item["objective"])):.2f}" r="3.5" '
                'fill="#fff" stroke="#9f552c" stroke-width="2"/>'
            )
    for tick in (0, 100, 200, 300, 400):
        body.append(
            f'<text x="{iteration_x(tick):.2f}" y="{trace_bottom + 22:g}" '
            f'text-anchor="middle" class="axis">{tick}</text>'
        )
    body.append(
        f'<text x="{plot_right:g}" y="{panel_bottom + 22:g}" text-anchor="end" class="axis">'
        "横軸: 反復</text>"
    )
    rows, y = _metric_rows(
        panel_bottom + 54,
        (
            (
                "最良の目的値",
                f"{float(probe['initial_objective']):.2f} → {float(probe['best_objective']):.5f}",
            ),
            (
                "受理した悪化 / 受理した移動",
                f"{int(probe['accepted_worsening'])} / {int(probe['accepted_moves'])}",
            ),
            (
                "悪化の受理（序盤 / 終盤）",
                f"{int(probe['early_worsening'])} / {int(probe['late_worsening'])}",
            ),
        ),
    )
    body.extend(rows)
    footer, height = _figure_footer(
        y + 8,
        f"scripts.generate_article_figures._simulated_annealing_probe · dataset {dataset_version}",
        "固定した1次元・1 seedの教材です。別のseed、高次元、温度スケジュール一般での性能や、"
        "大域最適性は示しません。",
    )
    body.extend(footer)
    return _figure_document(
        "Simulated Annealingで悪化する移動を受理する固定実行",
        (
            "1次元Rastrigin関数を初期点3.5から400反復探索する"
            "固定seedの実行。高温の序盤では悪化する移動も受理して複数の谷を移動し、"
            "それまでの最良値は悪化させずに保持する。目的値は32.25から0.00076まで改善する。"
        ),
        height,
        body,
    )


def _network_simplex_transport_probe() -> dict[str, object]:
    supplies = {"A": 4.0, "B": 5.0}
    demands = {"X": 3.0, "Y": 2.0, "Z": 4.0}
    costs = {
        ("A", "X"): 2.0,
        ("A", "Y"): 5.0,
        ("A", "Z"): 4.0,
        ("B", "X"): 3.0,
        ("B", "Y"): 1.0,
        ("B", "Z"): 2.0,
    }
    initial_flows = {
        ("A", "X"): 3.0,
        ("A", "Y"): 1.0,
        ("A", "Z"): 0.0,
        ("B", "X"): 0.0,
        ("B", "Y"): 1.0,
        ("B", "Z"): 4.0,
    }
    entering = ("A", "Z")
    cycle = (
        (("A", "Z"), 1.0),
        (("B", "Z"), -1.0),
        (("B", "Y"), 1.0),
        (("A", "Y"), -1.0),
    )

    def total_cost(flows: dict[tuple[str, str], float]) -> float:
        return sum(flows[arc] * cost for arc, cost in costs.items())

    def node_potentials(
        flows: dict[tuple[str, str], float],
    ) -> dict[str, float]:
        tree_arcs = [arc for arc, flow in flows.items() if flow > 1e-12]
        potentials = {"A": 0.0}
        while len(potentials) < len(supplies) + len(demands):
            progress = False
            for tail, head in tree_arcs:
                cost = costs[(tail, head)]
                if tail in potentials and head not in potentials:
                    potentials[head] = potentials[tail] - cost
                    progress = True
                elif head in potentials and tail not in potentials:
                    potentials[tail] = potentials[head] + cost
                    progress = True
            if not progress:
                raise ValueError("positive-flow arcs must form a spanning tree")
        return potentials

    def reduced_costs(
        flows: dict[tuple[str, str], float],
    ) -> dict[tuple[str, str], float]:
        potentials = node_potentials(flows)
        return {arc: cost - potentials[arc[0]] + potentials[arc[1]] for arc, cost in costs.items()}

    def max_balance_error(flows: dict[tuple[str, str], float]) -> float:
        supply_errors = [
            abs(sum(flow for (tail, _), flow in flows.items() if tail == node) - amount)
            for node, amount in supplies.items()
        ]
        demand_errors = [
            abs(sum(flow for (_, head), flow in flows.items() if head == node) - amount)
            for node, amount in demands.items()
        ]
        return max((*supply_errors, *demand_errors))

    initial_reduced_costs = reduced_costs(initial_flows)
    theta = min(initial_flows[arc] for arc, direction in cycle if direction < 0.0)
    optimized_flows = dict(initial_flows)
    for arc, direction in cycle:
        optimized_flows[arc] += direction * theta
    optimized_reduced_costs = reduced_costs(optimized_flows)
    leaving = next(
        arc for arc, direction in cycle if direction < 0.0 and optimized_flows[arc] <= 1e-12
    )

    return {
        "supplies": supplies,
        "demands": demands,
        "costs": costs,
        "initial_flows": initial_flows,
        "optimized_flows": optimized_flows,
        "initial_cost": total_cost(initial_flows),
        "optimized_cost": total_cost(optimized_flows),
        "initial_reduced_costs": initial_reduced_costs,
        "optimized_reduced_costs": optimized_reduced_costs,
        "entering": entering,
        "leaving": leaving,
        "cycle": cycle,
        "theta": theta,
        "initial_balance_error": max_balance_error(initial_flows),
        "optimized_balance_error": max_balance_error(optimized_flows),
    }


def _network_simplex_pivot_svg(dataset_version: str) -> str:
    probe = _network_simplex_transport_probe()
    costs = probe["costs"]
    initial_flows = probe["initial_flows"]
    optimized_flows = probe["optimized_flows"]
    if not all(
        isinstance(values, dict)
        for values in (
            costs,
            initial_flows,
            optimized_flows,
        )
    ):
        raise TypeError("network-simplex teaching probe mappings must be dictionaries")
    entering = probe["entering"]
    leaving = probe["leaving"]
    if not isinstance(entering, tuple) or not isinstance(leaving, tuple):
        raise TypeError("network-simplex entering and leaving arcs must be tuples")

    x_supply, x_demand = 76.0, 364.0
    x_supply_edge, x_demand_edge = 98.0, 342.0
    supply_y = {"A": 36.0, "B": 156.0}
    demand_y = {"X": 0.0, "Y": 96.0, "Z": 192.0}
    label_offsets = {
        ("A", "X"): -14.0,
        ("A", "Y"): -10.0,
        ("A", "Z"): -4.0,
        ("B", "X"): -11.0,
        ("B", "Y"): 22.0,
        ("B", "Z"): 15.0,
    }
    label_x = {
        ("A", "X"): 220.0,
        ("A", "Y"): 196.0,
        ("A", "Z"): 190.0,
        ("B", "X"): 251.0,
        ("B", "Y"): 256.0,
        ("B", "Z"): 220.0,
    }

    def arrow(start: str, end: str) -> str:
        return f"{start} → {end}"

    def panel_graph(
        flows: dict[tuple[str, str], float],
        *,
        y_offset: float,
        optimized: bool,
    ) -> list[str]:
        elements: list[str] = []
        labels: list[str] = []
        active_color = "#2c7564" if optimized else "#102a2e"
        active_marker = "ns-arrow-active" if optimized else "ns-arrow-tree"
        for arc, cost in costs.items():
            tail, head = arc
            y1 = supply_y[tail] + y_offset
            y2 = demand_y[head] + y_offset
            flow = float(flows[arc])
            elements.append(
                f'<line x1="{x_supply_edge:g}" y1="{y1:.2f}" x2="{x_demand_edge:g}" '
                f'y2="{y2:.2f}" stroke="#dfe7e3" stroke-width="1.5"/>'
            )
            if flow > 1e-12:
                elements.append(
                    f'<line x1="{x_supply_edge:g}" y1="{y1:.2f}" x2="{x_demand_edge:g}" '
                    f'y2="{y2:.2f}" stroke="{active_color}" '
                    f'stroke-width="{2.0 + 1.2 * flow:.2f}" stroke-linecap="round" '
                    f'marker-end="url(#{active_marker})"/>'
                )
                midpoint_y = (y1 + y2) / 2.0 + label_offsets[arc]
                labels.append(
                    f'<text x="{label_x[arc]:.2f}" y="{midpoint_y:.2f}" text-anchor="middle" '
                    f'class="metric-value halo">{flow:g} × {float(cost):g}</text>'
                )
        tail, head = leaving if optimized else entering
        y1 = supply_y[tail] + y_offset
        y2 = demand_y[head] + y_offset
        if optimized:
            elements.append(
                f'<line x1="{x_supply_edge:g}" y1="{y1:.2f}" x2="{x_demand_edge:g}" '
                f'y2="{y2:.2f}" stroke="#aebbb6" stroke-width="3" stroke-dasharray="7 6" '
                'marker-end="url(#ns-arrow-muted)"/>'
            )
        else:
            elements.append(
                f'<line x1="{x_supply_edge:g}" y1="{y1:.2f}" x2="{x_demand_edge:g}" '
                f'y2="{y2:.2f}" stroke="#d67835" stroke-width="3.5" stroke-dasharray="8 6" '
                'marker-end="url(#ns-arrow-enter)"/>'
            )
        elements.extend(labels)
        for node, amount in probe["supplies"].items():
            y = supply_y[node] + y_offset
            elements.extend(
                [
                    f'<circle cx="{x_supply:g}" cy="{y:.2f}" r="20" fill="#d67835"/>',
                    f'<text x="{x_supply:g}" y="{y + 6:.2f}" text-anchor="middle" '
                    f'class="panel-title" fill="#fff">{node}</text>',
                    f'<text x="{FIGURE_MARGIN + 12}" y="{y + 5:.2f}" class="metric-value">'
                    f"+{float(amount):g}</text>",
                ]
            )
        for node, amount in probe["demands"].items():
            y = demand_y[node] + y_offset
            elements.extend(
                [
                    f'<circle cx="{x_demand:g}" cy="{y:.2f}" r="20" fill="#2c7564"/>',
                    f'<text x="{x_demand:g}" y="{y + 6:.2f}" text-anchor="middle" '
                    f'class="panel-title" fill="#fff">{node}</text>',
                    f'<text x="{x_demand + 26:g}" y="{y + 5:.2f}" class="metric-value">'
                    f"−{float(amount):g}</text>",
                ]
            )
        return elements

    title = "1本加えると、閉路が1つできる"
    body, y = _figure_heading(title, "固定した輸送問題の流れ・全域木のpivot 1回・整数の供給量")
    body.append(
        "<defs>"
        '<marker id="ns-arrow-muted" markerWidth="4" markerHeight="4" refX="3.4" refY="2" '
        'orient="auto"><path d="M0,0 L4,2 L0,4 Z" fill="#aebbb6"/></marker>'
        '<marker id="ns-arrow-tree" markerWidth="4" markerHeight="4" refX="3.4" refY="2" '
        'orient="auto"><path d="M0,0 L4,2 L0,4 Z" fill="#102a2e"/></marker>'
        '<marker id="ns-arrow-active" markerWidth="4" markerHeight="4" refX="3.4" refY="2" '
        'orient="auto"><path d="M0,0 L4,2 L0,4 Z" fill="#2c7564"/></marker>'
        '<marker id="ns-arrow-enter" markerWidth="4" markerHeight="4" refX="3.4" refY="2" '
        'orient="auto"><path d="M0,0 L4,2 L0,4 Z" fill="#d67835"/></marker>'
        "</defs>"
    )
    key, y = _text_lines(
        FIGURE_MARGIN,
        y + 14,
        "辺のラベルは 流量 × 単位費用。左の数は供給量、右の数は需要量です。",
        "note",
    )
    body.extend(key)
    initial_cost = float(probe["initial_cost"])
    optimized_cost = float(probe["optimized_cost"])
    entering_reduced = float(probe["initial_reduced_costs"][entering])
    for name, cost, hint, flows, optimized in (
        (
            "前: 実行可能な全域木",
            initial_cost,
            f"橙の破線: 入る辺 {arrow(*entering)}（被約費用 {entering_reduced:g}）",
            initial_flows,
            False,
        ),
        (
            f"後: 閉路に沿って θ = {float(probe['theta']):g}",
            optimized_cost,
            f"灰色の破線: 出る辺 {arrow(*leaving)}（流量が0になる）",
            optimized_flows,
            True,
        ),
    ):
        panel, top, panel_bottom = _panel(y + 2, name, 22 + 52 + 192 + 28)
        body.extend(panel)
        body.append(
            f'<text x="{FIGURE_WIDTH - FIGURE_MARGIN - 14}" y="{top - 18:g}" text-anchor="end" '
            f'class="metric-value" fill="#2c7564">総費用 {cost:g}</text>'
        )
        hint_color = "#8b4c3d" if not optimized else "#617068"
        body.append(
            f'<text x="{FIGURE_MARGIN + 14}" y="{top + 4:g}" class="status" '
            f'fill="{hint_color}">{hint}</text>'
        )
        body.extend(panel_graph(flows, y_offset=top + 48, optimized=optimized))
        y = panel_bottom + 10
    rows, y = _metric_rows(
        y + 24,
        (
            ("pivot", f"{arrow(*entering)} が入り、{arrow(*leaving)} が出る"),
            ("総費用の変化", f"{initial_cost:g} → {optimized_cost:g}"),
        ),
    )
    body.extend(rows)
    footer, height = _figure_footer(
        y + 8,
        "scripts.generate_article_figures._network_simplex_transport_probe"
        f" · dataset {dataset_version}",
        "供給2点と需要3点の固定教材です。退化、容量の上限、大規模なnetworkでの性能は示しません。",
    )
    body.extend(footer)
    return _figure_document(
        "Network Simplexの1回のpivotで輸送の流れが変わる様子",
        (
            "供給ノードAとBから需要ノードX、Y、Zへ9単位を"
            "輸送する固定した最小費用流。初期の全域木へAからZの辺を加える。"
            "できた閉路に1単位を流すとAからYの辺が木を離れる。"
            "全ノードの需給を保ったまま総費用が20から18へ下がる。"
        ),
        height,
        body,
    )


def _particle_swarm_objective(point: list[float] | tuple[float, ...]) -> float:
    return 20.0 + sum(
        coordinate * coordinate - 10.0 * math.cos(2.0 * math.pi * coordinate)
        for coordinate in point
    )


def _particle_swarm_probe() -> dict[str, object]:
    rng = random.Random(5)
    particle_count = 30
    lower, upper = -5.12, 5.12
    inertia = 0.65
    cognitive = social = 1.4
    velocity_limit = 1.5
    snapshot_iterations = {0, 5, 15, 40}

    positions = [
        [rng.uniform(lower, upper), rng.uniform(lower, upper)] for _ in range(particle_count)
    ]
    velocities = [[0.0, 0.0] for _ in range(particle_count)]
    personal_bests = [position.copy() for position in positions]
    personal_values = [_particle_swarm_objective(position) for position in personal_bests]

    def diversity() -> float:
        centroid = [
            sum(position[dimension] for position in positions) / particle_count
            for dimension in range(2)
        ]
        return math.sqrt(
            sum(
                sum((position[dimension] - centroid[dimension]) ** 2 for dimension in range(2))
                for position in positions
            )
            / particle_count
        )

    def current_median() -> float:
        values = sorted(_particle_swarm_objective(position) for position in positions)
        midpoint = len(values) // 2
        return (values[midpoint - 1] + values[midpoint]) / 2.0

    def snapshot(iteration: int) -> dict[str, object]:
        best_index = min(range(particle_count), key=personal_values.__getitem__)
        return {
            "iteration": iteration,
            "positions": tuple(tuple(position) for position in positions),
            "global_best": tuple(personal_bests[best_index]),
            "global_best_value": personal_values[best_index],
            "diversity": diversity(),
        }

    snapshots = [snapshot(0)]
    history = [
        {
            "iteration": 0,
            "global_best_value": min(personal_values),
            "median_value": current_median(),
            "diversity": diversity(),
        }
    ]
    personal_updates = 0
    boundary_hits = 0

    for iteration in range(1, 41):
        best_index = min(range(particle_count), key=personal_values.__getitem__)
        global_best = personal_bests[best_index].copy()
        for particle in range(particle_count):
            for dimension in range(2):
                velocity = (
                    inertia * velocities[particle][dimension]
                    + cognitive
                    * rng.random()
                    * (personal_bests[particle][dimension] - positions[particle][dimension])
                    + social
                    * rng.random()
                    * (global_best[dimension] - positions[particle][dimension])
                )
                velocities[particle][dimension] = max(
                    -velocity_limit, min(velocity_limit, velocity)
                )
                proposed = positions[particle][dimension] + velocities[particle][dimension]
                if proposed < lower or proposed > upper:
                    boundary_hits += 1
                positions[particle][dimension] = max(lower, min(upper, proposed))

            value = _particle_swarm_objective(positions[particle])
            if value < personal_values[particle]:
                personal_bests[particle] = positions[particle].copy()
                personal_values[particle] = value
                personal_updates += 1

        history.append(
            {
                "iteration": iteration,
                "global_best_value": min(personal_values),
                "median_value": current_median(),
                "diversity": diversity(),
            }
        )
        if iteration in snapshot_iterations:
            snapshots.append(snapshot(iteration))

    best_index = min(range(particle_count), key=personal_values.__getitem__)
    return {
        "snapshots": tuple(snapshots),
        "history": tuple(history),
        "initial_best_value": history[0]["global_best_value"],
        "final_best": tuple(personal_bests[best_index]),
        "final_best_value": personal_values[best_index],
        "initial_diversity": history[0]["diversity"],
        "final_diversity": history[-1]["diversity"],
        "personal_updates": personal_updates,
        "boundary_hits": boundary_hits,
    }


def _particle_swarm_svg(dataset_version: str) -> str:
    probe = _particle_swarm_probe()
    snapshots = probe["snapshots"]
    history = probe["history"]
    assert isinstance(snapshots, tuple)
    assert isinstance(history, tuple)

    title = "群は散らばりながら、最良の経験へ引かれる"
    body, y = _figure_heading(title, "2次元Rastrigin・30粒子・seed 5・global-best型")
    key_y = y + 16
    body.extend(
        [
            f'<circle cx="{FIGURE_MARGIN + 7}" cy="{key_y - 5:g}" r="5.5" fill="#d77b42"/>',
            f'<text x="{FIGURE_MARGIN + 20}" y="{key_y:g}" class="axis">現在の位置</text>',
            f'<path d="M{FIGURE_MARGIN + 137} {key_y - 14:g} l4 8 9 1 -6.5 6 2 9 -8.5 -5 '
            '-8 5 2 -9 -6.5 -6 9 -1z" fill="#2c7564"/>',
            f'<text x="{FIGURE_MARGIN + 154}" y="{key_y:g}" class="axis">全体の最良点</text>',
            f'<circle cx="{FIGURE_MARGIN + 7}" cy="{key_y + 21:g}" r="4" fill="#d8e5df" '
            'stroke="#6e8f83"/>',
            f'<text x="{FIGURE_MARGIN + 20}" y="{key_y + 26:g}" class="axis">'
            "周期的な谷の目安（厳密な極小点ではない）</text>",
        ]
    )
    panel_width, gap = (CONTENT_WIDTH - 12) / 2, 12.0
    plot_left, plot_top, plot_size = 14.0, 34.0, panel_width - 28
    panel_height = plot_top + plot_size + 52
    domain = 5.12
    grid_top = key_y + 42

    def project(point: tuple[float, ...], panel_x: float, panel_y: float) -> tuple[float, float]:
        return (
            panel_x + plot_left + (point[0] + domain) / (2.0 * domain) * plot_size,
            panel_y + plot_top + (domain - point[1]) / (2.0 * domain) * plot_size,
        )

    for index, snapshot_data in enumerate(snapshots):
        assert isinstance(snapshot_data, dict)
        panel_x = FIGURE_MARGIN + (index % 2) * (panel_width + gap)
        panel_y = grid_top + (index // 2) * (panel_height + gap)
        iteration = int(snapshot_data["iteration"])
        best_value = float(snapshot_data["global_best_value"])
        diversity = float(snapshot_data["diversity"])
        body.extend(
            [
                (
                    f'<rect x="{panel_x:g}" y="{panel_y:g}" width="{panel_width:g}" '
                    f'height="{panel_height:g}" rx="12" fill="#fff" stroke="#d8ded9"/>'
                ),
                (
                    f'<text x="{panel_x + plot_left:g}" y="{panel_y + 24:g}" '
                    f'class="panel-title">反復 {iteration}</text>'
                ),
                (
                    f'<rect x="{panel_x + plot_left:g}" y="{panel_y + plot_top:g}" '
                    f'width="{plot_size:g}" height="{plot_size:g}" fill="#f6f3eb" '
                    'stroke="#d8ded9"/>'
                ),
            ]
        )
        for guide in range(-4, 5):
            guide_x, _ = project((float(guide), 0.0), panel_x, panel_y)
            _, guide_y = project((0.0, float(guide)), panel_x, panel_y)
            body.append(
                f'<line x1="{guide_x:.2f}" y1="{panel_y + plot_top:g}" '
                f'x2="{guide_x:.2f}" y2="{panel_y + plot_top + plot_size:g}" '
                'stroke="#e8e5dd" stroke-width="1"/>'
            )
            body.append(
                f'<line x1="{panel_x + plot_left:g}" y1="{guide_y:.2f}" '
                f'x2="{panel_x + plot_left + plot_size:g}" y2="{guide_y:.2f}" '
                'stroke="#e8e5dd" stroke-width="1"/>'
            )
            for other in range(-4, 5):
                if guide == 0 and other == 0:
                    continue
                local_x, local_y = project((float(guide), float(other)), panel_x, panel_y)
                body.append(
                    f'<circle cx="{local_x:.2f}" cy="{local_y:.2f}" r="1.6" fill="#d8e5df"/>'
                )

        optimum_x, optimum_y = project((0.0, 0.0), panel_x, panel_y)
        body.append(
            f'<circle cx="{optimum_x:.2f}" cy="{optimum_y:.2f}" r="4" '
            'fill="#fff" stroke="#2c7564" stroke-width="1.5"/>'
        )
        positions = snapshot_data["positions"]
        assert isinstance(positions, tuple)
        for position in positions:
            particle_x, particle_y = project(position, panel_x, panel_y)
            body.append(
                f'<circle cx="{particle_x:.2f}" cy="{particle_y:.2f}" r="3.2" '
                'fill="#d77b42" fill-opacity=".82" stroke="#fff" stroke-width="0.8"/>'
            )
        best_x, best_y = project(snapshot_data["global_best"], panel_x, panel_y)
        body.append(
            f'<path d="M{best_x:.2f} {best_y - 7:.2f} l2.6 5.2 6 0.9 -4.3 4.3 1.7 6 '
            f'-6 -3.4 -5.2 3.4 1.7 -6 -4.3 -4.3 6 -0.9z" fill="#2c7564" stroke="#fff"/>'
        )
        stats_y = panel_y + plot_top + plot_size + 22
        body.extend(
            [
                f'<text x="{panel_x + plot_left:g}" y="{stats_y:g}" class="status">'
                f"最良 {_metric(best_value)}</text>",
                f'<text x="{panel_x + plot_left:g}" y="{stats_y + 20:g}" class="status">'
                f"広がり {diversity:.2f}</text>",
            ]
        )

    y = grid_top + 2 * panel_height + gap
    heading, y = _text_lines(
        FIGURE_MARGIN,
        y + 32,
        "最良値は下がる。同時に、群の広がりも失われる",
        "panel-title",
        size=TEXT_SIZE["panel-title"],
    )
    body.extend(heading)
    chart_x, chart_y, chart_width, chart_height = float(FIGURE_MARGIN), y - 6, 400.0, 150.0
    body.append(
        f'<rect x="{chart_x:g}" y="{chart_y:g}" width="{chart_width:g}" '
        f'height="{chart_height:g}" rx="12" fill="#fff" stroke="#d8ded9"/>'
    )
    best_logs = [math.log10(max(float(item["global_best_value"]), 1.0e-8)) for item in history]
    diversities = [float(item["diversity"]) for item in history]
    best_min, best_max = min(best_logs), max(best_logs)
    diversity_max = max(diversities)

    def chart_point(index: int, value: float, lower: float, upper: float) -> tuple[float, float]:
        x = chart_x + 16.0 + index / 40.0 * (chart_width - 32.0)
        ratio = (value - lower) / (upper - lower) if upper > lower else 0.0
        y = chart_y + chart_height - 18.0 - ratio * (chart_height - 36.0)
        return x, y

    best_points = [
        chart_point(index, value, best_min, best_max) for index, value in enumerate(best_logs)
    ]
    diversity_points = [
        chart_point(index, value, 0.0, diversity_max) for index, value in enumerate(diversities)
    ]
    body.extend(
        [
            (
                '<polyline points="'
                + " ".join(f"{x:.2f},{y:.2f}" for x, y in best_points)
                + '" fill="none" stroke="#2c7564" stroke-width="3"/>'
            ),
            (
                '<polyline points="'
                + " ".join(f"{x:.2f},{y:.2f}" for x, y in diversity_points)
                + '" fill="none" stroke="#d77b42" stroke-width="2.5" stroke-dasharray="7 5"/>'
            ),
            f'<text x="{chart_x:g}" y="{chart_y + chart_height + 20:g}" class="axis">0</text>',
            f'<text x="{chart_x + chart_width:g}" y="{chart_y + chart_height + 20:g}" '
            'text-anchor="end" class="axis">反復 40</text>',
        ]
    )
    y = chart_y + chart_height + 52
    for color, label, value, dashed in (
        (
            "#2c7564",
            "それまでの最良値（log10）",
            f"{_metric(float(probe['initial_best_value']))} → "
            f"{_metric(float(probe['final_best_value']))}",
            False,
        ),
        (
            "#d77b42",
            "位置の広がり",
            f"{float(probe['initial_diversity']):.2f} → {float(probe['final_diversity']):.2f}",
            True,
        ),
    ):
        row, y = _legend_row(y, color, label, value, dash=dashed)
        body.extend(row)
    note, y = _text_lines(FIGURE_MARGIN, y + 2, "2本の線の縦軸は別々の目盛です。", "note")
    body.extend(note)
    footer, height = _figure_footer(
        y + 4,
        f"scripts/generate_article_figures.py::_particle_swarm_probe · dataset {dataset_version}",
        "固定した2次元・1 seedのglobal-best PSOです。大域最適性や、他のseedでの再現は"
        "保証しません。",
    )
    body.extend(footer)
    return _figure_document(
        "Particle Swarm Optimizationの固定実行",
        (
            "2次元Rastrigin関数上の30粒子を反復0、5、15、40で示す。"
            "粒子は広い初期配置から全体の最良点付近へ集中し、下段では"
            "それまでの最良値が下がる一方で、位置の広がりも縮小する。"
            "淡い整数格子は周期的な谷の配置の目安であり、厳密な極小点ではない。"
        ),
        height,
        body,
    )


def _pbt_validation_score(weight: float, learning_rate: float) -> float:
    return -((weight - 1.0) ** 2) - 0.08 * learning_rate


def _pbt_population_probe() -> dict[str, object]:
    learning_rates = (0.04, 0.07, 0.11, 0.16, 0.24, 0.34)
    workers = [
        {
            "worker_id": worker_id,
            "weight": 0.0,
            "learning_rate": learning_rate,
            "lineage_root": worker_id,
            "score": _pbt_validation_score(0.0, learning_rate),
        }
        for worker_id, learning_rate in enumerate(learning_rates)
    ]

    def snapshot() -> tuple[tuple[int, float, float, int, float], ...]:
        return tuple(
            (
                int(worker["worker_id"]),
                float(worker["weight"]),
                float(worker["learning_rate"]),
                int(worker["lineage_root"]),
                float(worker["score"]),
            )
            for worker in workers
        )

    snapshots = [snapshot()]
    events: list[tuple[int, int, int, int, int, float, float, float]] = []
    for round_index in range(1, 11):
        for worker in workers:
            learning_rate = float(worker["learning_rate"])
            weight = float(worker["weight"])
            weight += 1.8 * learning_rate * (1.0 - weight)
            worker["weight"] = weight
            worker["score"] = _pbt_validation_score(weight, learning_rate)

        if round_index % 2 == 0:
            ranked = sorted(
                workers,
                key=lambda worker: (float(worker["score"]), -int(worker["worker_id"])),
                reverse=True,
            )
            source = ranked[0]
            target = ranked[-1]
            previous_root = int(target["lineage_root"])
            previous_score = float(target["score"])
            factor = 1.2 if round_index % 4 == 2 else 0.8
            new_learning_rate = min(
                0.4,
                max(0.02, float(source["learning_rate"]) * factor),
            )
            target["weight"] = float(source["weight"])
            target["learning_rate"] = new_learning_rate
            target["lineage_root"] = int(source["lineage_root"])
            target["score"] = _pbt_validation_score(
                float(target["weight"]),
                new_learning_rate,
            )
            events.append(
                (
                    round_index,
                    int(source["worker_id"]),
                    int(target["worker_id"]),
                    int(source["lineage_root"]),
                    previous_root,
                    new_learning_rate,
                    previous_score,
                    float(target["score"]),
                )
            )
        snapshots.append(snapshot())

    initial_best = max(row[4] for row in snapshots[0])
    final_best = max(row[4] for row in snapshots[-1])
    final_roots = tuple(sorted({row[3] for row in snapshots[-1]}))
    return {
        "snapshots": tuple(snapshots),
        "events": tuple(events),
        "initial_best": initial_best,
        "final_best": final_best,
        "final_roots": final_roots,
    }


def _pbt_lineage_svg(dataset_version: str) -> str:
    probe = _pbt_population_probe()
    snapshots = probe["snapshots"]
    events = probe["events"]
    if not isinstance(snapshots, tuple) or not isinstance(events, tuple):
        raise TypeError("PBT teaching probe collections must be tuples")

    plot_left, plot_right = 62.0, 400.0
    worker_colors = ("#d67835", "#245c42", "#45656a", "#b08a3c", "#77647f", "#102a2e")

    def round_x(round_index: int) -> float:
        return plot_left + round_index / 10 * (plot_right - plot_left)

    title = "scoreの線と系譜の継承を同時に追う"
    body, y = _figure_heading(
        title, "worker 6個・10ラウンド・2ラウンドごとにexploit・決定論的なtoy学習"
    )
    legend_y = y + 14
    body.extend(
        [
            '<defs><marker id="pbt-arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" '
            'orient="auto"><path d="M0,0 L8,4 L0,8 Z" fill="#d67835"/></marker></defs>',
            f'<path d="M{FIGURE_MARGIN} {legend_y + 2:g} C{FIGURE_MARGIN + 10} {legend_y - 18:g}, '
            f'{FIGURE_MARGIN + 24} {legend_y - 18:g}, {FIGURE_MARGIN + 32} {legend_y + 2:g}" '
            'fill="none" stroke="#d67835" stroke-width="2.5" marker-end="url(#pbt-arrow)"/>',
            f'<text x="{FIGURE_MARGIN + 42}" y="{legend_y:g}" class="note">exploitのコピー</text>',
            f'<text x="{FIGURE_MARGIN + 180}" y="{legend_y:g}" class="note">'
            "線の色 = 系譜の根</text>",
        ]
    )
    panel, top, panel_bottom = _panel(
        legend_y + 14, "同じworker IDでも、コピー後は別の系譜を継ぐ", 250
    )
    body.extend(panel)
    body.append(
        f'<text x="{FIGURE_WIDTH - FIGURE_MARGIN - 14}" y="{top + 4:g}" text-anchor="end" '
        'class="status">scoreは高いほど良い</text>'
    )
    score_top, score_bottom = top + 22, top + 192

    def score_y(score: float) -> float:
        return score_bottom - (score + 1.05) / 1.1 * (score_bottom - score_top)

    for score in (-1.0, -0.5, 0.0):
        tick_y = score_y(score)
        body.extend(
            [
                f'<line x1="{plot_left:g}" y1="{tick_y:.2f}" x2="{plot_right:g}" '
                f'y2="{tick_y:.2f}" stroke="#ebe8e0"/>',
                f'<text x="{plot_left - 8:g}" y="{tick_y + 5:.2f}" text-anchor="end" '
                f'class="axis">{score:g}</text>',
            ]
        )
    for worker_id in range(6):
        points = " ".join(
            f"{round_x(round_index):.2f},{score_y(float(rows[worker_id][4])):.2f}"
            for round_index, rows in enumerate(snapshots)
        )
        body.append(
            f'<polyline points="{points}" fill="none" stroke="{worker_colors[worker_id]}" '
            'stroke-width="2.5" stroke-linejoin="round"/>'
        )
        for round_index, rows in enumerate(snapshots):
            body.append(
                f'<circle cx="{round_x(round_index):.2f}" '
                f'cy="{score_y(float(rows[worker_id][4])):.2f}" r="2.8" '
                f'fill="{worker_colors[worker_id]}"/>'
            )
    for worker_id, color in enumerate(worker_colors):
        legend_x = FIGURE_MARGIN + 20 + worker_id * 64
        body.extend(
            [
                f'<circle cx="{legend_x}" cy="{score_bottom + 25:g}" r="5" fill="{color}"/>',
                f'<text x="{legend_x + 9}" y="{score_bottom + 30:g}" class="axis">'
                f"W{worker_id}</text>",
            ]
        )
    row_gap = 36.0
    panel, top, panel_bottom = _panel(
        panel_bottom + 12, "コピー元と学習率の変更を残す", 18 + 5 * row_gap + 62
    )
    body.extend(panel)
    lineage_top = top + 18
    for round_index in range(11):
        x = round_x(round_index)
        body.extend(
            [
                f'<line x1="{x:.2f}" y1="{lineage_top - 14:g}" x2="{x:.2f}" '
                f'y2="{lineage_top + 5 * row_gap + 14:g}" stroke="#f0ede6"/>',
                f'<text x="{x:.2f}" y="{lineage_top + 5 * row_gap + 36:g}" '
                f'text-anchor="middle" class="axis">{round_index}</text>',
            ]
        )
    for worker_id in range(6):
        row_y = lineage_top + worker_id * row_gap
        body.extend(
            [
                f'<text x="{plot_left - 12:g}" y="{row_y + 5:.2f}" text-anchor="end" '
                f'class="method">W{worker_id}</text>',
                f'<line x1="{plot_left:g}" y1="{row_y:.2f}" x2="{plot_right:g}" '
                f'y2="{row_y:.2f}" stroke="#ebe8e0" stroke-width="6" stroke-linecap="round"/>',
            ]
        )
        for round_index in range(10):
            root = int(snapshots[round_index][worker_id][3])
            body.append(
                f'<line x1="{round_x(round_index):.2f}" y1="{row_y:.2f}" '
                f'x2="{round_x(round_index + 1):.2f}" y2="{row_y:.2f}" '
                f'stroke="{worker_colors[root]}" stroke-width="6" stroke-linecap="round"/>'
            )
    labels = []
    for event_index, event in enumerate(events):
        round_index, source_id, target_id, source_root, _, learning_rate, _, _ = event
        x = round_x(int(round_index))
        source_y = lineage_top + int(source_id) * row_gap
        target_y = lineage_top + int(target_id) * row_gap
        control_x = x + (10 if target_y >= source_y else -10)
        body.extend(
            [
                f'<path d="M {x - 6:.2f} {source_y:.2f} Q {control_x:.2f} '
                f'{(source_y + target_y) / 2:.2f} {x:.2f} {target_y:.2f}" '
                'fill="none" stroke="#d67835" stroke-width="2.5" marker-end="url(#pbt-arrow)"/>',
                f'<circle cx="{x:.2f}" cy="{target_y:.2f}" r="5.5" '
                f'fill="{worker_colors[int(source_root)]}" stroke="#fff" stroke-width="2"/>',
            ]
        )
        label_y = target_y - 10 if event_index % 2 == 0 else target_y + 20
        anchor = "end" if round_index == 10 else "start"
        label_x = x - 8 if round_index == 10 else x + 8
        labels.append(
            f'<text x="{label_x:.2f}" y="{label_y:.2f}" text-anchor="{anchor}" '
            f'class="method halo" fill="#8b4c3d">η={float(learning_rate):.3f}</text>'
        )
    body.extend(labels)
    body.append(
        f'<text x="{plot_right:g}" y="{panel_bottom + 22:g}" text-anchor="end" class="axis">'
        "横軸: ラウンド</text>"
    )
    rows, y = _metric_rows(
        panel_bottom + 54,
        (
            (
                "最良のscore",
                f"{float(probe['initial_best']):.3f} → {float(probe['final_best']):.3f}",
            ),
            ("exploitの回数", f"{len(events)}"),
            ("最後に残った系譜の根", f"{len(probe['final_roots'])}"),
        ),
    )
    body.extend(rows)
    footer, height = _figure_footer(
        y + 8,
        f"固定したtoy学習 + 決定論的なexploit/explore · dataset {dataset_version}",
        "固定したscoreの教材です。実際のmodel、checkpointのコスト、検証のノイズ、"
        "PBT一般の性能は示しません。",
    )
    body.extend(footer)
    return _figure_document(
        "scoreの線と系譜の継承を同時に追う",
        (
            "6個のworkerを10ラウンド進め、2ラウンドごとに最良のworkerから最下位のworkerへ"
            "状態をコピーし、学習率を0.8倍または1.2倍した固定pure Python "
            "PBT教材です。workerのscoreと系譜の根の継承を示します。実際のmodel、"
            "checkpointのコスト、検証のノイズ、並列実行、PBT一般の性能は示しません。"
        ),
        height,
        body,
    )


def _sgd_samples() -> tuple[tuple[float, float, float], ...]:
    rows = []
    for index in range(32):
        feature1 = -1.0 + 2.0 * index / 31.0
        feature2 = -1.0 + 2.0 * ((index * 7) % 32) / 31.0
        noise = 0.08 * math.sin(1.7 * index)
        target = 1.8 * feature1 - 0.9 * feature2 + noise
        rows.append((feature1, feature2, target))
    return tuple(rows)


def _sgd_loss(
    parameters: tuple[float, float],
    rows: tuple[tuple[float, float, float], ...],
) -> float:
    return sum(
        0.5 * (feature1 * parameters[0] + feature2 * parameters[1] - target) ** 2
        for feature1, feature2, target in rows
    ) / len(rows)


def _sgd_gradient(
    parameters: tuple[float, float],
    rows: tuple[tuple[float, float, float], ...],
) -> tuple[float, float]:
    gradient1 = 0.0
    gradient2 = 0.0
    for feature1, feature2, target in rows:
        residual = feature1 * parameters[0] + feature2 * parameters[1] - target
        gradient1 += feature1 * residual
        gradient2 += feature2 * residual
    return gradient1 / len(rows), gradient2 / len(rows)


def _sgd_mini_batch_probe() -> dict[str, object]:
    rows = _sgd_samples()
    hessian11 = sum(row[0] * row[0] for row in rows) / len(rows)
    hessian12 = sum(row[0] * row[1] for row in rows) / len(rows)
    hessian22 = sum(row[1] * row[1] for row in rows) / len(rows)
    right1 = sum(row[0] * row[2] for row in rows) / len(rows)
    right2 = sum(row[1] * row[2] for row in rows) / len(rows)
    determinant = hessian11 * hessian22 - hessian12 * hessian12
    optimum = (
        (right1 * hessian22 - right2 * hessian12) / determinant,
        (hessian11 * right2 - hessian12 * right1) / determinant,
    )

    learning_rate = 0.3
    batch_size = 4
    epochs = 8
    parameters = (-1.2, 1.4)
    initial_loss = _sgd_loss(parameters, rows)
    path = [parameters]
    history: list[tuple[int, int, float, float, float, float]] = []
    generator_state = 17
    update = 0

    for epoch in range(epochs):
        order = list(range(len(rows)))
        for index in range(len(order) - 1, 0, -1):
            generator_state = (1664525 * generator_state + 1013904223) & 0xFFFFFFFF
            swap_index = generator_state % (index + 1)
            order[index], order[swap_index] = order[swap_index], order[index]
        for start in range(0, len(order), batch_size):
            batch = tuple(rows[index] for index in order[start : start + batch_size])
            gradient = _sgd_gradient(parameters, batch)
            parameters = (
                parameters[0] - learning_rate * gradient[0],
                parameters[1] - learning_rate * gradient[1],
            )
            update += 1
            path.append(parameters)
            history.append(
                (
                    update,
                    epoch + 1,
                    _sgd_loss(parameters, batch),
                    _sgd_loss(parameters, rows),
                    parameters[0],
                    parameters[1],
                )
            )

    upward_full_loss_steps = sum(
        history[index][3] > history[index - 1][3] for index in range(1, len(history))
    )
    return {
        "rows": rows,
        "learning_rate": learning_rate,
        "batch_size": batch_size,
        "epochs": epochs,
        "initial_parameters": path[0],
        "initial_loss": initial_loss,
        "optimum": optimum,
        "optimum_loss": _sgd_loss(optimum, rows),
        "path": tuple(path),
        "history": tuple(history),
        "final_parameters": parameters,
        "final_loss": _sgd_loss(parameters, rows),
        "upward_full_loss_steps": upward_full_loss_steps,
        "hessian": (hessian11, hessian12, hessian22),
    }


def _sgd_mini_batch_svg(dataset_version: str) -> str:
    probe = _sgd_mini_batch_probe()
    path = probe["path"]
    history = probe["history"]
    optimum = probe["optimum"]
    hessian = probe["hessian"]
    if not (
        isinstance(path, tuple)
        and isinstance(history, tuple)
        and isinstance(optimum, tuple)
        and isinstance(hessian, tuple)
    ):
        raise TypeError("SGD teaching probe collections must be tuples")

    title = "mini-batchの揺れと全データの損失を分けて読む"
    body, y = _figure_heading(title, "標本32個・パラメータ2個・batch 4・η 0.3・8 epoch")
    legend_y = y + 14
    body.extend(
        [
            f'<line x1="{FIGURE_MARGIN}" y1="{legend_y - 5:g}" x2="{FIGURE_MARGIN + 24}" '
            f'y2="{legend_y - 5:g}" stroke="#245c42" stroke-width="4.5"/>',
            f'<text x="{FIGURE_MARGIN + 32}" y="{legend_y:g}" class="note">全データ</text>',
            f'<line x1="{FIGURE_MARGIN + 116}" y1="{legend_y - 5:g}" x2="{FIGURE_MARGIN + 140}" '
            f'y2="{legend_y - 5:g}" stroke="#d67835" stroke-width="3.5"/>',
            f'<text x="{FIGURE_MARGIN + 148}" y="{legend_y:g}" class="note">'
            "mini-batch／更新</text>",
            f'<circle cx="{FIGURE_MARGIN + 6}" cy="{legend_y + 19:g}" r="6" fill="#245c42"/>',
            f'<text x="{FIGURE_MARGIN + 18}" y="{legend_y + 24:g}" class="note">'
            "全データでの最適解</text>",
        ]
    )
    plot_left, plot_right = 56.0, 404.0
    parameter1_min, parameter1_max = -1.35, 2.15
    parameter2_min, parameter2_max = -1.2, 1.55
    panel, top, panel_bottom = _panel(
        legend_y + 24 + 14, "同じ損失の面でも、stepは小刻みに揺れる", 252
    )
    body.extend(panel)
    parameter_top, parameter_bottom = top + 6, top + 196

    def parameter_x(value: float) -> float:
        return plot_left + (value - parameter1_min) / (parameter1_max - parameter1_min) * (
            plot_right - plot_left
        )

    def parameter_y(value: float) -> float:
        return parameter_bottom - (value - parameter2_min) / (parameter2_max - parameter2_min) * (
            parameter_bottom - parameter_top
        )

    hessian11, hessian12, hessian22 = (float(value) for value in hessian)
    trace = hessian11 + hessian22
    spread = math.sqrt((hessian11 - hessian22) ** 2 + 4.0 * hessian12**2)
    eigenvalue1 = 0.5 * (trace + spread)
    eigenvalue2 = 0.5 * (trace - spread)
    angle = 0.5 * math.atan2(2.0 * hessian12, hessian11 - hessian22)
    cosine = math.cos(angle)
    sine = math.sin(angle)
    body.append(
        f'<clipPath id="sgd-parameter-clip"><rect x="{plot_left:g}" y="{parameter_top:g}" '
        f'width="{plot_right - plot_left:g}" height="{parameter_bottom - parameter_top:g}"/>'
        "</clipPath>"
    )
    for level in (0.03, 0.12, 0.4, 1.2, 2.4):
        radius1 = math.sqrt(2.0 * level / eigenvalue1)
        radius2 = math.sqrt(2.0 * level / eigenvalue2)
        points = []
        for index in range(121):
            phase = 2.0 * math.pi * index / 120
            local1 = radius1 * math.cos(phase)
            local2 = radius2 * math.sin(phase)
            parameter1 = float(optimum[0]) + cosine * local1 - sine * local2
            parameter2 = float(optimum[1]) + sine * local1 + cosine * local2
            points.append(f"{parameter_x(parameter1):.2f},{parameter_y(parameter2):.2f}")
        body.append(
            f'<polyline points="{" ".join(points)}" fill="none" stroke="#d9e2dd" '
            'stroke-width="1.5" clip-path="url(#sgd-parameter-clip)"/>'
        )
    for tick in (-1.0, 0.0, 1.0, 2.0):
        x = parameter_x(tick)
        body.extend(
            [
                f'<line x1="{x:.2f}" y1="{parameter_top:g}" x2="{x:.2f}" '
                f'y2="{parameter_bottom:g}" stroke="#f0ede6"/>',
                f'<text x="{x:.2f}" y="{parameter_bottom + 20:g}" text-anchor="middle" '
                f'class="axis">{tick:g}</text>',
            ]
        )
    for tick in (-1.0, 0.0, 1.0):
        tick_y = parameter_y(tick)
        body.extend(
            [
                f'<line x1="{plot_left:g}" y1="{tick_y:.2f}" x2="{plot_right:g}" '
                f'y2="{tick_y:.2f}" stroke="#f0ede6"/>',
                f'<text x="{plot_left - 8:g}" y="{tick_y + 5:.2f}" text-anchor="end" '
                f'class="axis">{tick:g}</text>',
            ]
        )
    path_points = " ".join(
        f"{parameter_x(float(point[0])):.2f},{parameter_y(float(point[1])):.2f}" for point in path
    )
    body.append(
        f'<polyline points="{path_points}" fill="none" stroke="#d67835" stroke-width="2.5" '
        'stroke-linejoin="round" stroke-linecap="round"/>'
    )
    for index, point in enumerate(path):
        if index % 8 == 0 or index == len(path) - 1:
            body.append(
                f'<circle cx="{parameter_x(float(point[0])):.2f}" '
                f'cy="{parameter_y(float(point[1])):.2f}" r="3.5" '
                'fill="#d67835" stroke="#fff" stroke-width="1.5"/>'
            )
    start = path[0]
    optimum_x = parameter_x(float(optimum[0]))
    optimum_y = parameter_y(float(optimum[1]))
    body.extend(
        [
            f'<text x="{parameter_x(float(start[0])) + 10:.2f}" '
            f'y="{parameter_y(float(start[1])) - 8:.2f}" class="method halo">開始点</text>',
            f'<circle cx="{optimum_x:.2f}" cy="{optimum_y:.2f}" r="6" '
            'fill="#245c42" stroke="#fff" stroke-width="2"/>',
            f'<text x="{optimum_x - 10:.2f}" y="{optimum_y - 10:.2f}" text-anchor="end" '
            'class="method halo" fill="#245c42">最適解</text>',
            f'<text x="{plot_right:g}" y="{parameter_bottom + 40:g}" text-anchor="end" '
            'class="axis">横軸 パラメータ1、縦軸 パラメータ2</text>',
        ]
    )
    max_update = int(history[-1][0])
    panel, top, panel_bottom = _panel(
        panel_bottom + 12, "batchの損失は揺れ、全データの損失が傾向を示す", 196
    )
    body.extend(panel)
    loss_top, loss_bottom = top + 6, top + 156

    def update_x(update: int) -> float:
        return plot_left + update / max_update * (plot_right - plot_left)

    def loss_y(value: float) -> float:
        log_value = math.log10(max(value, 1e-4))
        return loss_bottom - (log_value + 4.0) / 4.5 * (loss_bottom - loss_top)

    for tick, label in ((1.0, "1"), (0.1, "0.1"), (0.01, "0.01"), (0.001, "0.001")):
        tick_y = loss_y(tick)
        body.extend(
            [
                f'<line x1="{plot_left:g}" y1="{tick_y:.2f}" x2="{plot_right:g}" '
                f'y2="{tick_y:.2f}" stroke="#ebe8e0"/>',
                f'<text x="{plot_left - 6:g}" y="{tick_y + 5:.2f}" text-anchor="end" '
                f'class="axis">{label}</text>',
            ]
        )
    for epoch in range(1, int(probe["epochs"])):
        x = update_x(epoch * 8)
        body.append(
            f'<line x1="{x:.2f}" y1="{loss_top:g}" x2="{x:.2f}" y2="{loss_bottom:g}" '
            'stroke="#d8d4ca" stroke-dasharray="4 6"/>'
        )
    batch_loss_points = " ".join(
        f"{update_x(int(row[0])):.2f},{loss_y(float(row[2])):.2f}" for row in history
    )
    full_loss_points = " ".join(
        f"{update_x(int(row[0])):.2f},{loss_y(float(row[3])):.2f}" for row in history
    )
    body.extend(
        [
            f'<polyline points="{batch_loss_points}" fill="none" stroke="#d67835" '
            'stroke-width="2" stroke-linejoin="round" opacity="0.9"/>',
            f'<polyline points="{full_loss_points}" fill="none" stroke="#245c42" '
            'stroke-width="4" stroke-linejoin="round"/>',
        ]
    )
    for update in (0, 16, 32, 48, 64):
        body.append(
            f'<text x="{update_x(update):.2f}" y="{loss_bottom + 20:g}" text-anchor="middle" '
            f'class="axis">{update}</text>'
        )
    body.append(
        f'<text x="{plot_right:g}" y="{panel_bottom + 22:g}" text-anchor="end" class="axis">'
        "横軸: 更新の回数（破線はepochの区切り）</text>"
    )
    rows, y = _metric_rows(
        panel_bottom + 54,
        (
            (
                "全データの損失",
                f"{float(probe['initial_loss']):.3f} → {float(probe['final_loss']):.4f}",
            ),
            (
                "全データの損失が増えた更新",
                f"{int(probe['upward_full_loss_steps'])} / {len(history) - 1}",
            ),
        ),
    )
    body.extend(rows)
    footer, height = _figure_footer(
        y + 8,
        f"固定したLCGによるshuffle + pure Pythonのmini-batch SGD · dataset {dataset_version}",
        "固定した線形回帰です。検証、汎化性能、neural network、SGD一般の性能は示しません。",
    )
    body.extend(footer)
    return _figure_document(
        "mini-batchの揺れと全データの損失を分けて読む",
        (
            "標本32個、パラメータ2個の固定線形回帰をbatch size 4、学習率0.3で"
            "8 epoch実行したpure PythonのSGDの結果です。パラメータの経路、mini-batchの損失、"
            "全データの損失を同じ実行から示します。検証、汎化、"
            "neural network、frameworkの実装、SGD一般の性能は示しません。"
        ),
        height,
        body,
    )


def _spatial_objective(value: float) -> float:
    return value * value * (1.0 + 0.5 * (value - 1.0) ** 2) - 2.0 * value


def _interval_square(lower: float, upper: float) -> tuple[float, float]:
    minimum = 0.0 if lower <= 0.0 <= upper else min(lower * lower, upper * upper)
    return minimum, max(lower * lower, upper * upper)


def _spatial_interval_lower_bound(lower: float, upper: float) -> float:
    squared = _interval_square(lower, upper)
    shifted_squared = _interval_square(lower - 1.0, upper - 1.0)
    product_lower = squared[0] * shifted_squared[0]
    return squared[0] + 0.5 * product_lower - 2.0 * upper


def _spatial_branch_bound_probe(
    *,
    gap_tolerance: float = 0.01,
    max_nodes: int = 256,
) -> dict[str, object]:
    domain = (0.0, 2.0)
    initial_candidates = (domain[0], domain[1])
    best_point = min(initial_candidates, key=_spatial_objective)
    best_value = _spatial_objective(best_point)
    pending = [(_spatial_interval_lower_bound(*domain), *domain)]
    pruned: list[tuple[float, float, float]] = []
    history = [(0, pending[0][0], best_value, len(pending))]
    explored = 0

    while pending and explored < max_nodes:
        pending.sort(key=lambda region: (region[0], region[1], region[2]))
        bound, lower, upper = pending.pop(0)
        if bound >= best_value:
            pruned.append((lower, upper, bound))
            continue
        if best_value - bound <= gap_tolerance:
            pending.append((bound, lower, upper))
            break

        midpoint = 0.5 * (lower + upper)
        for candidate in (lower, midpoint, upper):
            candidate_value = _spatial_objective(candidate)
            if candidate_value < best_value:
                best_point = candidate
                best_value = candidate_value
        explored += 1

        for child_lower, child_upper in ((lower, midpoint), (midpoint, upper)):
            child_bound = _spatial_interval_lower_bound(child_lower, child_upper)
            if child_bound >= best_value:
                pruned.append((child_lower, child_upper, child_bound))
            else:
                pending.append((child_bound, child_lower, child_upper))

        global_bound = min((region[0] for region in pending), default=best_value)
        history.append((explored, global_bound, best_value, len(pending)))

    pending.sort(key=lambda region: (region[1], region[2]))
    global_bound = min((region[0] for region in pending), default=best_value)
    return {
        "domain": domain,
        "gap_tolerance": gap_tolerance,
        "best_point": best_point,
        "best_value": best_value,
        "global_bound": global_bound,
        "absolute_gap": best_value - global_bound,
        "explored": explored,
        "pruned": tuple(pruned),
        "pending": tuple(pending),
        "history": tuple(history),
    }


def _spatial_branch_bound_svg(dataset_version: str) -> str:
    probe = _spatial_branch_bound_probe()
    domain = probe["domain"]
    history = probe["history"]
    pruned = probe["pruned"]
    pending = probe["pending"]
    if not (
        isinstance(domain, tuple)
        and isinstance(history, tuple)
        and isinstance(pruned, tuple)
        and isinstance(pending, tuple)
    ):
        raise TypeError("spatial branch-and-bound probe collections must be tuples")

    plot_left, plot_right = 56.0, 404.0

    def x_project(value: float) -> float:
        return plot_left + (value - float(domain[0])) / (float(domain[1]) - float(domain[0])) * (
            plot_right - plot_left
        )

    title = "下界が上がると、捨てられる区間が増える"
    body, y = _figure_heading(title, "固定した多項式・x ∈ [0, 2]・gapの許容値 0.01")
    legend_y = y + 14
    body.extend(
        [
            f'<line x1="{FIGURE_MARGIN}" y1="{legend_y - 5:g}" x2="{FIGURE_MARGIN + 22}" '
            f'y2="{legend_y - 5:g}" stroke="#245c42" stroke-width="5"/>',
            f'<text x="{FIGURE_MARGIN + 30}" y="{legend_y:g}" class="note">'
            "目的関数／未処理の区間</text>",
            f'<rect x="{FIGURE_MARGIN + 210}" y="{legend_y - 12:g}" width="18" height="12" '
            'rx="3" fill="#bd6754"/>',
            f'<text x="{FIGURE_MARGIN + 236}" y="{legend_y:g}" class="note">下界で枝刈り</text>',
            f'<circle cx="{FIGURE_MARGIN + 6}" cy="{legend_y + 19:g}" r="6" fill="#d67835"/>',
            f'<text x="{FIGURE_MARGIN + 18}" y="{legend_y + 24:g}" class="note">'
            "暫定解（incumbent）</text>",
        ]
    )
    panel, top, panel_bottom = _panel(legend_y + 24 + 14, "固定した目的関数と、得られた暫定解", 196)
    body.extend(panel)
    curve_top, curve_bottom = top + 6, top + 166

    def curve_y(value: float) -> float:
        return curve_bottom - (value + 1.2) / 3.4 * (curve_bottom - curve_top)

    for value in (-1.0, 0.0, 1.0, 2.0):
        tick_y = curve_y(value)
        body.extend(
            [
                f'<line x1="{plot_left:g}" y1="{tick_y:.2f}" x2="{plot_right:g}" '
                f'y2="{tick_y:.2f}" stroke="#ebe8e0"/>',
                f'<text x="{plot_left - 8:g}" y="{tick_y + 5:.2f}" text-anchor="end" '
                f'class="axis">{value:g}</text>',
            ]
        )
    curve_points = []
    for index in range(161):
        value = float(domain[0]) + index / 160 * (float(domain[1]) - float(domain[0]))
        curve_points.append(f"{x_project(value):.2f},{curve_y(_spatial_objective(value)):.2f}")
    body.append(
        f'<polyline points="{" ".join(curve_points)}" fill="none" stroke="#245c42" '
        'stroke-width="4" stroke-linejoin="round" stroke-linecap="round"/>'
    )
    best_point = float(probe["best_point"])
    best_value = float(probe["best_value"])
    body.extend(
        [
            f'<circle cx="{x_project(best_point):.2f}" cy="{curve_y(best_value):.2f}" '
            'r="6.5" fill="#d67835" stroke="#fff" stroke-width="2"/>',
            f'<text x="{x_project(best_point):.2f}" y="{curve_y(best_value) - 22:.2f}" '
            'text-anchor="middle" '
            f'class="method halo">x*={best_point:.2f} · f={best_value:.2f}</text>',
        ]
    )
    for value in (0.0, 0.5, 1.0, 1.5, 2.0):
        body.append(
            f'<text x="{x_project(value):.2f}" y="{curve_bottom + 22:g}" text-anchor="middle" '
            f'class="axis">{value:g}</text>'
        )
    panel, top, panel_bottom = _panel(panel_bottom + 12, "停止したときの区間の分割", 96)
    body.extend(panel)
    body.append(
        f'<text x="{FIGURE_WIDTH - FIGURE_MARGIN - 14}" y="{top - 18:g}" text-anchor="end" '
        f'class="status">未処理 {len(pending)} · 枝刈り {len(pruned)}</text>'
    )
    strip_y, strip_height = top + 8, 30.0
    body.append(
        f'<rect x="{plot_left:g}" y="{strip_y:g}" width="{plot_right - plot_left:g}" '
        f'height="{strip_height:g}" rx="6" fill="#edf1ed"/>'
    )
    for lower, upper, _ in pruned:
        x = x_project(float(lower))
        region_width = max(1.0, x_project(float(upper)) - x)
        body.append(
            f'<rect x="{x:.2f}" y="{strip_y:g}" width="{region_width:.2f}" '
            f'height="{strip_height:g}" fill="#bd6754" opacity="0.82"/>'
        )
    for _, lower, upper in pending:
        x = x_project(float(lower))
        region_width = max(1.0, x_project(float(upper)) - x)
        body.append(
            f'<rect x="{x:.2f}" y="{strip_y:g}" width="{region_width:.2f}" '
            f'height="{strip_height:g}" fill="#245c42" opacity="0.9"/>'
        )
    body.extend(
        [
            f'<line x1="{x_project(best_point):.2f}" y1="{strip_y - 6:g}" '
            f'x2="{x_project(best_point):.2f}" y2="{strip_y + strip_height + 6:g}" '
            'stroke="#d67835" stroke-width="3.5"/>',
            f'<text x="{x_project(best_point):.2f}" y="{strip_y + strip_height + 28:g}" '
            f'text-anchor="middle" class="method">暫定解 x={best_point:g}</text>',
        ]
    )
    history_rows = [(int(row[0]), float(row[1]), float(row[2]), int(row[3])) for row in history]
    max_node = max(row[0] for row in history_rows)
    panel, top, panel_bottom = _panel(
        panel_bottom + 12, "ノードを処理するほど、全体の下界が上がる", 196
    )
    body.extend(panel)
    convergence_top, convergence_bottom = top + 6, top + 156

    def history_x(node: int) -> float:
        return plot_left + node / max_node * (plot_right - plot_left)

    def history_y(value: float) -> float:
        return convergence_bottom - (value + 4.2) / 4.4 * (convergence_bottom - convergence_top)

    for value in (-4.0, -3.0, -2.0, -1.0, 0.0):
        tick_y = history_y(value)
        body.extend(
            [
                f'<line x1="{plot_left:g}" y1="{tick_y:.2f}" x2="{plot_right:g}" '
                f'y2="{tick_y:.2f}" stroke="#ebe8e0"/>',
                f'<text x="{plot_left - 8:g}" y="{tick_y + 5:.2f}" text-anchor="end" '
                f'class="axis">{value:g}</text>',
            ]
        )
    bound_points = " ".join(
        f"{history_x(node):.2f},{history_y(bound):.2f}" for node, bound, _, _ in history_rows
    )
    incumbent_points = " ".join(
        f"{history_x(node):.2f},{history_y(incumbent):.2f}"
        for node, _, incumbent, _ in history_rows
    )
    body.extend(
        [
            f'<polyline points="{bound_points}" fill="none" stroke="#245c42" '
            'stroke-width="4" stroke-linejoin="round"/>',
            f'<polyline points="{incumbent_points}" fill="none" stroke="#d67835" '
            'stroke-width="3.5" stroke-linejoin="round"/>',
        ]
    )
    for node in (0, 20, 40, 60, max_node):
        body.append(
            f'<text x="{history_x(node):.2f}" y="{convergence_bottom + 22:g}" '
            f'text-anchor="middle" class="axis">{node}</text>'
        )
    body.append(
        f'<text x="{plot_right:g}" y="{panel_bottom + 22:g}" text-anchor="end" class="axis">'
        "横軸: 処理したノード数　緑: 全体の下界　橙: 暫定解</text>"
    )
    rows, y = _metric_rows(
        panel_bottom + 54,
        (
            ("暫定解の値", f"{best_value:.3f}"),
            ("全体の下界", f"{float(probe['global_bound']):.3f}"),
            ("gap", f"{float(probe['absolute_gap']):.4f}"),
        ),
    )
    body.extend(rows)
    footer, height = _figure_footer(
        y + 8,
        f"区間演算による下界 + 決定論的なbest-bound探索 · dataset {dataset_version}",
        "固定した1変数の教材です。McCormick relaxation、多変数のMINLP、solver一般の性能は"
        "示しません。",
    )
    body.extend(footer)
    return _figure_document(
        "下界が上がると、捨てられる区間が増える",
        (
            "固定した1変数の多項式を、pure Pythonの区間演算による下界で"
            "空間branch-and-boundした実行結果です。目的関数、最終的な区間の分割、"
            "暫定解と全体の下界の履歴を示します。McCormick relaxation、"
            "多変数のMINLP、solver一般の性能や有限時間での厳密解を示す図ではありません。"
        ),
        height,
        body,
    )


def _solve_dense_linear_system(
    matrix: list[list[float]], right_hand_side: list[float]
) -> list[float]:
    size = len(right_hand_side)
    augmented = [[*row, right_hand_side[index]] for index, row in enumerate(matrix)]
    for column in range(size):
        pivot = max(range(column, size), key=lambda row: abs(augmented[row][column]))
        if abs(augmented[pivot][column]) <= 1e-12:
            raise ValueError("multiple-shooting teaching KKT system is singular")
        augmented[column], augmented[pivot] = augmented[pivot], augmented[column]
        scale = augmented[column][column]
        augmented[column] = [value / scale for value in augmented[column]]
        for row in range(size):
            if row == column:
                continue
            factor = augmented[row][column]
            augmented[row] = [
                value - factor * pivot_value
                for value, pivot_value in zip(augmented[row], augmented[column], strict=True)
            ]
    return [augmented[index][-1] for index in range(size)]


def _multiple_shooting_probe() -> dict[str, object]:
    duration = 0.5
    initial_state = 0.0
    target_state = 1.0
    initial_guess = (0.5, 0.5, 1.5)
    hessian = [
        [0.0, 0.0, 0.0],
        [0.0, 2.0 * duration, 0.0],
        [0.0, 0.0, 2.0 * duration],
    ]
    constraints = [
        [-1.0, duration, 0.0],
        [1.0, 0.0, duration],
    ]
    kkt = [[*hessian[row], constraints[0][row], constraints[1][row]] for row in range(3)]
    kkt.extend(
        [
            [*constraints[0], 0.0, 0.0],
            [*constraints[1], 0.0, 0.0],
        ]
    )
    solution = _solve_dense_linear_system(kkt, [0.0, 0.0, 0.0, 0.0, target_state])
    solved = tuple(solution[:3])

    def evaluate(vector: tuple[float, ...]) -> dict[str, object]:
        state1, control0, control1 = vector
        end0 = initial_state + duration * control0
        end1 = state1 + duration * control1
        defects = (end0 - state1, end1 - target_state)
        return {
            "vector": vector,
            "endpoints": (end0, end1),
            "defects": defects,
            "defect_norm": math.sqrt(sum(value * value for value in defects)),
            "objective": duration * (control0 * control0 + control1 * control1),
        }

    return {
        "duration": duration,
        "initial_state": initial_state,
        "target_state": target_state,
        "initial": evaluate(initial_guess),
        "solved": evaluate(solved),
    }


def _multiple_shooting_svg(dataset_version: str) -> str:
    probe = _multiple_shooting_probe()
    initial = probe["initial"]
    solved = probe["solved"]
    if not isinstance(initial, dict) or not isinstance(solved, dict):
        raise TypeError("multiple-shooting probe panels must be dictionaries")
    plot_x, plot_width, plot_height = 74.0, 290.0, 170.0
    state_min, state_max = -0.1, 1.35

    def project_x(time: float) -> float:
        return plot_x + time * plot_width

    def project_y(state: float, plot_y: float) -> float:
        return plot_y + plot_height - (state - state_min) / (state_max - state_min) * plot_height

    def panel(
        title: str,
        payload: dict[str, object],
        panel_y: float,
        *,
        show_defects: bool,
    ) -> tuple[list[str], float]:
        vector = payload["vector"]
        endpoints = payload["endpoints"]
        defects = payload["defects"]
        if not (
            isinstance(vector, tuple)
            and isinstance(endpoints, tuple)
            and isinstance(defects, tuple)
        ):
            raise TypeError("multiple-shooting probe values must be tuples")
        state1, control0, control1 = (float(value) for value in vector)
        end0, end1 = (float(value) for value in endpoints)
        defect0, defect1 = (float(value) for value in defects)
        result, top, bottom = _panel(panel_y, title, 22 + 18 + plot_height + 34)
        result.append(
            f'<text x="{FIGURE_MARGIN + 14}" y="{top + 4:g}" class="status">'
            f"u=[{control0:.2f}, {control1:.2f}] · "
            f"‖defect‖={float(payload['defect_norm']):.3f}</text>"
        )
        plot_y = top + 28
        segment0 = (
            (project_x(0.0), project_y(float(probe["initial_state"]), plot_y)),
            (project_x(0.5), project_y(end0, plot_y)),
        )
        segment1 = (
            (project_x(0.5), project_y(state1, plot_y)),
            (project_x(1.0), project_y(end1, plot_y)),
        )
        result.append(
            f'<rect x="{plot_x - 14:g}" y="{plot_y:g}" width="{plot_width + 28:g}" '
            f'height="{plot_height:g}" rx="10" fill="#fbfcfa"/>'
        )
        for value in (0.0, 0.5, 1.0, 1.25):
            tick_y = project_y(value, plot_y)
            result.extend(
                [
                    f'<line x1="{plot_x - 14:g}" y1="{tick_y:.2f}" '
                    f'x2="{plot_x + plot_width + 14:g}" y2="{tick_y:.2f}" stroke="#ebe8e0"/>',
                    f'<text x="{plot_x - 20:g}" y="{tick_y + 5:.2f}" text-anchor="end" '
                    f'class="axis">{value:g}</text>',
                ]
            )
        for time, label in ((0.0, "t₀"), (0.5, "境界"), (1.0, "終端")):
            result.append(
                f'<text x="{project_x(time):.2f}" y="{plot_y + plot_height + 22:g}" '
                f'text-anchor="middle" class="axis">{label}</text>'
            )
        for points in (segment0, segment1):
            result.append(
                f'<line x1="{points[0][0]:.2f}" y1="{points[0][1]:.2f}" '
                f'x2="{points[1][0]:.2f}" y2="{points[1][1]:.2f}" '
                'stroke="#245c42" stroke-width="5" stroke-linecap="round"/>'
            )
        labels = []
        for time, state, label in (
            (0.0, float(probe["initial_state"]), "x₀"),
            (0.5, state1, "決定変数 x₁"),
            (1.0, float(probe["target_state"]), "目標"),
        ):
            label_y = project_y(state, plot_y) - 12
            label_anchor = "middle"
            label_x = project_x(time)
            if show_defects and time == 1.0:
                label_y = project_y(state, plot_y) + 22
                label_anchor = "end"
                label_x += 16
            result.append(
                f'<circle cx="{project_x(time):.2f}" cy="{project_y(state, plot_y):.2f}" '
                'r="6" fill="#d67835" stroke="#fff" stroke-width="2"/>'
            )
            labels.append(
                f'<text x="{label_x:.2f}" y="{label_y:.2f}" text-anchor="{label_anchor}" '
                f'class="method halo">{label}</text>'
            )
        if show_defects:
            for time, start, stop, label in (
                (0.5, end0, state1, f"δ₀={defect0:.2f}"),
                (1.0, end1, float(probe["target_state"]), f"δ₁={defect1:+.2f}"),
            ):
                x = project_x(time)
                y1, y2 = project_y(start, plot_y), project_y(stop, plot_y)
                result.append(
                    f'<line x1="{x:.2f}" y1="{y1:.2f}" x2="{x:.2f}" y2="{y2:.2f}" '
                    'stroke="#bd6754" stroke-width="3.5" stroke-dasharray="6 4"/>'
                )
                labels.append(
                    f'<text x="{x - 10:.2f}" y="{(y1 + y2) / 2 + 5:.2f}" text-anchor="end" '
                    f'class="method halo" fill="#a33d30">{label}</text>'
                )
        return result + labels, bottom

    title = "短い区間の前進計算は、境界がつながって初めて一本の軌道になる"
    body, y = _figure_heading(title, "状態1個・区間2個・区間の長さ 0.5・目標 1.0")
    legend_y = y + 14
    body.extend(
        [
            f'<line x1="{FIGURE_MARGIN}" y1="{legend_y - 5:g}" x2="{FIGURE_MARGIN + 26}" '
            f'y2="{legend_y - 5:g}" stroke="#245c42" stroke-width="5"/>',
            f'<text x="{FIGURE_MARGIN + 34}" y="{legend_y:g}" class="note">区間の前進計算</text>',
            f'<circle cx="{FIGURE_MARGIN + 162}" cy="{legend_y - 5:g}" r="6" fill="#d67835"/>',
            f'<text x="{FIGURE_MARGIN + 174}" y="{legend_y:g}" class="note">状態の決定変数</text>',
            f'<line x1="{FIGURE_MARGIN + 300}" y1="{legend_y - 15:g}" x2="{FIGURE_MARGIN + 300}" '
            f'y2="{legend_y + 3:g}" stroke="#bd6754" stroke-width="3.5" '
            'stroke-dasharray="6 4"/>',
            f'<text x="{FIGURE_MARGIN + 310}" y="{legend_y:g}" class="note">defect</text>',
        ]
    )
    first, bottom = panel("初期の推定値", initial, legend_y + 14, show_defects=True)
    body.extend(first)
    second, bottom = panel("連続性の制約を解いた後", solved, bottom + 12, show_defects=False)
    body.extend(second)
    rows, y = _metric_rows(
        bottom + 34,
        (
            (
                "目的値",
                f"{float(initial['objective']):.2f} → {float(solved['objective']):.2f}",
            ),
            (
                "defectのノルム",
                f"{float(initial['defect_norm']):.3f} → {float(solved['defect_norm']):.1f}",
            ),
        ),
    )
    body.extend(rows)
    footer, height = _figure_footer(
        y + 8,
        f"固定した線形の区間積分 + 等式制約のKKTを厳密に解く · dataset {dataset_version}",
        "記事と同じ2区間の定式化です。SciPy SLSQP自体の実行結果ではありません。"
        "非線形のdynamics、経路制約、積分誤差、solverの一般的な性能は示しません。"
        "実務では区間の分け方と積分のtoleranceを変えて再検証します。",
    )
    body.extend(footer)
    return _figure_document(
        "短い区間の前進計算は、境界がつながって初めて一本の軌道になる",
        (
            "記事と同じ状態1個、区間2個、区間の長さ0.5の固定Multiple "
            "Shooting問題です。初期の推定値と、同じ線形の連続性制約を"
            "等式制約のKKTで厳密に解いた結果を比較します。区間の前進計算の終点と"
            "境界の状態の決定変数のずれ、終端の目標とのずれ、defectのノルム、制御の"
            "costを示します。SciPy SLSQP自体の実行結果、非線形のdynamics、経路制約、"
            "一般的な収束性能は示しません。"
        ),
        height,
        body,
    )


def _finite_horizon_lqr_probe() -> tuple[
    list[tuple[float, float]], list[float], list[tuple[float, float]]
]:
    dt = 0.1
    control_scale = 0.1
    control_cost = 0.01
    position_cost = 1.0
    velocity_cost = 0.1
    p00, p01, p10, p11 = 10.0, 0.0, 0.0, 1.0
    reversed_gains: list[tuple[float, float]] = []
    for _ in range(40):
        control_hessian = control_cost + control_scale * control_scale * p11
        gain_position = control_scale * p10 / control_hessian
        gain_velocity = control_scale * (dt * p10 + p11) / control_hessian
        reversed_gains.append((gain_position, gain_velocity))

        a_minus_bk00 = 1.0
        a_minus_bk01 = dt
        a_minus_bk10 = -control_scale * gain_position
        a_minus_bk11 = 1.0 - control_scale * gain_velocity
        product00 = p00 * a_minus_bk00 + p01 * a_minus_bk10
        product01 = p00 * a_minus_bk01 + p01 * a_minus_bk11
        product10 = p10 * a_minus_bk00 + p11 * a_minus_bk10
        product11 = p10 * a_minus_bk01 + p11 * a_minus_bk11
        next00 = position_cost + product00
        next01 = product01
        next10 = dt * product00 + product10
        next11 = velocity_cost + dt * product01 + product11
        off_diagonal = 0.5 * (next01 + next10)
        p00, p01, p10, p11 = next00, off_diagonal, off_diagonal, next11

    gains = list(reversed(reversed_gains))
    position, velocity = 2.0, 0.0
    states = [(position, velocity)]
    controls: list[float] = []
    for gain_position, gain_velocity in gains:
        control = -(gain_position * position + gain_velocity * velocity)
        position, velocity = (
            position + dt * velocity,
            velocity + control_scale * control,
        )
        controls.append(control)
        states.append((position, velocity))
    return states, controls, gains


def _lqr_backward_forward_svg(dataset_version: str) -> str:
    states, controls, gains = _finite_horizon_lqr_probe()
    plot_x, plot_width = 58.0, 346.0
    state_min, state_max = -2.8, 2.1
    control_limit = max(abs(value) for value in controls)

    def project_x(step: int) -> float:
        return plot_x + step / 40 * plot_width

    def polyline(points: list[tuple[float, float]], color: str, dash: str = "") -> str:
        coordinates = " ".join(f"{x:.2f},{y:.2f}" for x, y in points)
        dash_attribute = f' stroke-dasharray="{dash}"' if dash else ""
        return (
            f'<polyline points="{coordinates}" fill="none" stroke="{color}" '
            'stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"'
            f"{dash_attribute}/>"
        )

    terminal_position, terminal_velocity = states[-1]
    first_gain, middle_gain, final_gain = gains[0], gains[20], gains[-1]
    title = "backward passのgainが、forwardの前進計算を変える"
    body, y = _figure_heading(title, "状態2個・制御1個・horizon 40・dt 0.1・目標 [0, 0]")
    panel, top, panel_bottom = _panel(y + 8, "終端のcostから、時刻ごとのgainへ", 3 * 26 + 2)
    body.extend(panel)
    for index, (name, gain) in enumerate(
        (("K₃₉（終端側）", final_gain), ("K₂₀", middle_gain), ("K₀（初期側）", first_gain))
    ):
        row_y = top + 6 + index * 26
        body.extend(
            [
                f'<text x="{FIGURE_MARGIN + 14}" y="{row_y:g}" class="method">{name}</text>',
                f'<text x="{FIGURE_WIDTH - FIGURE_MARGIN - 14}" y="{row_y:g}" '
                f'text-anchor="end" class="metric">[{gain[0]:.3f}, {gain[1]:.3f}]</text>',
            ]
        )
    body.append(
        f'<text x="{FIGURE_MARGIN + 150}" y="{top + 6 + 26:g}" class="status">'
        "↑ backwardに計算</text>"
    )
    state_height = 190.0
    panel, top, panel_bottom = _panel(
        panel_bottom + 12, "forwardの前進計算: 状態", state_height + 28 + 30
    )
    body.extend(panel)
    state_y = top

    def project_state(value: float) -> float:
        bounded = min(state_max, max(state_min, value))
        return (
            state_y + state_height - (bounded - state_min) / (state_max - state_min) * state_height
        )

    for value in (-2.0, -1.0, 0.0, 1.0, 2.0):
        tick_y = project_state(value)
        body.extend(
            [
                f'<line x1="{plot_x:g}" y1="{tick_y:.2f}" x2="{plot_x + plot_width:g}" '
                f'y2="{tick_y:.2f}" stroke="#ebe8e0"/>',
                f'<text x="{plot_x - 8:g}" y="{tick_y + 5:.2f}" text-anchor="end" '
                f'class="axis">{value:g}</text>',
            ]
        )
    for step in (0, 10, 20, 30, 40):
        body.append(
            f'<text x="{project_x(step):.2f}" y="{state_y + state_height + 22:g}" '
            f'text-anchor="middle" class="axis">{step}</text>'
        )
    body.extend(
        [
            polyline(
                [(project_x(index), project_state(2.0)) for index in range(41)], "#9aa49e", "7 6"
            ),
            polyline(
                [(project_x(index), project_state(state[0])) for index, state in enumerate(states)],
                "#245c42",
            ),
            polyline(
                [(project_x(index), project_state(state[1])) for index, state in enumerate(states)],
                "#d67835",
            ),
        ]
    )
    key_y = state_y + state_height + 48
    for offset, (color, label, dash) in zip(
        (0, 100, 200),
        (("#245c42", "位置", ""), ("#d67835", "速度", ""), ("#9aa49e", "u=0 の位置", "7 6")),
        strict=True,
    ):
        dash_attribute = f' stroke-dasharray="{dash}"' if dash else ""
        body.extend(
            [
                f'<line x1="{FIGURE_MARGIN + 14 + offset}" y1="{key_y - 5:g}" '
                f'x2="{FIGURE_MARGIN + 38 + offset}" y2="{key_y - 5:g}" stroke="{color}" '
                f'stroke-width="3.5"{dash_attribute}/>',
                f'<text x="{FIGURE_MARGIN + 46 + offset}" y="{key_y:g}" class="note">'
                f"{label}</text>",
            ]
        )
    control_height = 120.0
    panel, top, panel_bottom = _panel(
        panel_bottom + 12, "forwardの前進計算: feedback制御 uₖ", control_height + 32
    )
    body.extend(panel)
    control_y = top

    def project_control(value: float) -> float:
        return control_y + control_height / 2 - value / control_limit * control_height * 0.43

    body.extend(
        [
            f'<line x1="{plot_x:g}" y1="{project_control(0.0):.2f}" '
            f'x2="{plot_x + plot_width:g}" y2="{project_control(0.0):.2f}" stroke="#cfd8d1"/>',
            f'<text x="{plot_x - 8:g}" y="{project_control(control_limit) + 5:.2f}" '
            f'text-anchor="end" class="axis">+{control_limit:.0f}</text>',
            f'<text x="{plot_x - 8:g}" y="{project_control(0.0) + 5:.2f}" text-anchor="end" '
            'class="axis">0</text>',
            f'<text x="{plot_x - 8:g}" y="{project_control(-control_limit) + 5:.2f}" '
            f'text-anchor="end" class="axis">−{control_limit:.0f}</text>',
            polyline(
                [
                    (project_x(index), project_control(value))
                    for index, value in enumerate(controls)
                ],
                "#7e5f98",
            ),
        ]
    )
    for step in (0, 10, 20, 30, 39):
        body.append(
            f'<text x="{project_x(step):.2f}" y="{control_y + control_height + 22:g}" '
            f'text-anchor="middle" class="axis">{step}</text>'
        )
    rows, y = _metric_rows(
        panel_bottom + 34,
        (
            ("終端の状態", f"[{terminal_position:.5f}, {terminal_velocity:.5f}]"),
            ("最大の |u|", f"{control_limit:.3f}"),
        ),
    )
    body.extend(rows)
    footer, height = _figure_footer(
        y + 8,
        "有限horizonのRiccati backward pass + 閉ループのforward前進計算"
        f" · dataset {dataset_version}",
        "記事の線形LQR部分問題です。非線形のiLQR/DDP反復や制約の処理は含みません。"
        "この1例から一般的な収束速度、安定性、実時間での性能は判断できません。",
    )
    body.extend(footer)
    return _figure_document(
        "backward passのgainが、forwardの前進計算を変える",
        (
            "記事のPython例と同じ状態2個、制御1個、40 stepの有限horizonの線形LQR"
            "部分問題をpure Pythonで実行した結果です。backward passで時刻ごとのfeedback "
            "gainを求め、初期状態 [2, 0] からforwardに前進計算します。状態と制御の"
            "履歴、終端の状態、制御の最大値を示します。非線形のiLQR/DDP反復、"
            "regularization、line search、一般の制約、実時間での性能は含みません。"
        ),
        height,
        body,
    )


def _so3_update_svg(dataset_version: str) -> str:
    traces = {
        str(trace.parameters["strategy"]): trace
        for trace in generate_so3_traces(dataset_version=dataset_version)
    }
    projected = traces["projected"]
    riemannian = traces["riemannian"]
    angle_max = 2.8

    def metric_max(trace: AlgorithmTrace, metric_id: str) -> float:
        return max(_metric_value(frame, metric_id) for frame in trace.frames)

    def line(points: list[tuple[float, float]], color: str, dash: str = "") -> str:
        coordinates = " ".join(f"{x:.2f},{y:.2f}" for x, y in points)
        dash_attribute = f' stroke-dasharray="{dash}"' if dash else ""
        return (
            f'<polyline points="{coordinates}" fill="none" stroke="{color}" '
            'stroke-width="4" stroke-linecap="round" stroke-linejoin="round"'
            f"{dash_attribute}/>"
        )

    projected_first = projected.frames[1]
    riemannian_first = riemannian.frames[1]
    projected_final = projected.frames[-1]
    riemannian_final = riemannian.frames[-1]
    title = "SO(3)へ戻る二つの一歩は、同じではない"
    body, y = _figure_heading(title, "単位行列 → πに近い目標・固定step 0.35・更新12回")
    legend_y = y + 14
    body.extend(
        [
            f'<line x1="{FIGURE_MARGIN}" y1="{legend_y - 5:g}" x2="{FIGURE_MARGIN + 28}" '
            f'y2="{legend_y - 5:g}" stroke="#d67835" stroke-width="4"/>',
            f'<text x="{FIGURE_MARGIN + 36}" y="{legend_y:g}" class="note">'
            "外側の空間 + QRで射影</text>",
            f'<line x1="{FIGURE_MARGIN + 210}" y1="{legend_y - 5:g}" x2="{FIGURE_MARGIN + 238}" '
            f'y2="{legend_y - 5:g}" stroke="#245c42" stroke-width="4" stroke-dasharray="8 6"/>',
            f'<text x="{FIGURE_MARGIN + 246}" y="{legend_y:g}" class="note">'
            "接空間 + exp map</text>",
        ]
    )
    plot_x, plot_width, plot_height = 52.0, 352.0, 180.0
    panel, top, panel_bottom = _panel(
        legend_y + 14, "目標までのgeodesic残差（rad）", plot_height + 34
    )
    body.extend(panel)
    plot_y = top

    def history_points(trace: AlgorithmTrace) -> list[tuple[float, float]]:
        return [
            (
                plot_x + frame.oracle_evaluations / 12 * plot_width,
                plot_y
                + plot_height
                - _metric_value(frame, "geodesic_residual") / angle_max * plot_height,
            )
            for frame in trace.frames
        ]

    for angle in (0.0, 1.0, 2.0, 2.8):
        tick_y = plot_y + plot_height - angle / angle_max * plot_height
        body.extend(
            [
                f'<line x1="{plot_x:g}" y1="{tick_y:.2f}" x2="{plot_x + plot_width:g}" '
                f'y2="{tick_y:.2f}" stroke="#ebe8e0"/>',
                f'<text x="{plot_x - 8:g}" y="{tick_y + 5:.2f}" text-anchor="end" '
                f'class="axis">{angle:g}</text>',
            ]
        )
    for evaluation in (0, 4, 8, 12):
        x = plot_x + evaluation / 12 * plot_width
        body.extend(
            [
                f'<line x1="{x:.2f}" y1="{plot_y:g}" x2="{x:.2f}" y2="{plot_y + plot_height:g}" '
                'stroke="#f1efe9"/>',
                f'<text x="{x:.2f}" y="{plot_y + plot_height + 22:g}" text-anchor="middle" '
                f'class="axis">{evaluation}</text>',
            ]
        )
    projected_history = history_points(projected)
    riemannian_history = history_points(riemannian)
    body.extend([line(projected_history, "#d67835"), line(riemannian_history, "#245c42", "8 6")])
    for points, color in ((projected_history, "#d67835"), (riemannian_history, "#245c42")):
        for index in (0, 4, 12):
            x, point_y = points[index]
            body.append(
                f'<circle cx="{x:.2f}" cy="{point_y:.2f}" r="4.5" fill="{color}" '
                'stroke="#fff" stroke-width="2"/>'
            )
    rows, y = _metric_rows(
        panel_bottom + 30,
        (
            ("QR", f"2.800 → {_metric_value(projected_final, 'geodesic_residual'):.3f} rad"),
            (
                "Riemann",
                f"2.800 → {_metric_value(riemannian_final, 'geodesic_residual'):.3f} rad",
            ),
        ),
    )
    body.extend(rows)
    heading, y = _text_lines(
        FIGURE_MARGIN, y + 16, "最初の更新を分解する", "panel-title", size=TEXT_SIZE["panel-title"]
    )
    body.extend(heading)
    right = FIGURE_WIDTH - FIGURE_MARGIN - 14
    for name, color, steps in (
        (
            "Projected Gradient",
            "#d67835",
            (
                ("外側の空間でのstep ‖Δ‖", "0.976"),
                ("→ QRで戻す補正", "1.136"),
                (
                    "→ 受理した回転の角度",
                    f"{_metric_value(projected_first, 'geodesic_residual'):.3f} rad",
                ),
            ),
        ),
        (
            "Riemannian Gradient",
            "#245c42",
            (
                ("接空間でのstep ‖ξ‖", "0.980"),
                ("→ 1次近似との差", "0.661"),
                (
                    "→ 受理した回転の角度",
                    f"{_metric_value(riemannian_first, 'geodesic_residual'):.3f} rad",
                ),
            ),
        ),
    ):
        card_y = y - 6
        card_height = 40 + 26 * len(steps)
        body.extend(
            [
                f'<rect x="{FIGURE_MARGIN}" y="{card_y:g}" width="{CONTENT_WIDTH}" '
                f'height="{card_height:g}" rx="12" fill="#fff" stroke="#cfd8d1"/>',
                f'<circle cx="{FIGURE_MARGIN + 24}" cy="{card_y + 22:g}" r="8" fill="{color}"/>',
                f'<text x="{FIGURE_MARGIN + 40}" y="{card_y + 28:g}" class="method">{name}</text>',
            ]
        )
        for index, (label, value) in enumerate(steps):
            row_y = card_y + 56 + index * 26
            body.extend(
                [
                    f'<text x="{FIGURE_MARGIN + 14}" y="{row_y:g}" class="metric">{label}</text>',
                    f'<text x="{right}" y="{row_y:g}" text-anchor="end" class="metric-value">'
                    f"{value}</text>",
                ]
            )
        y = card_y + card_height + 18
    heading, y = _text_lines(
        FIGURE_MARGIN,
        y + 16,
        "受理した回転の構造の残差（最大値）",
        "panel-title",
        size=TEXT_SIZE["panel-title"],
    )
    body.extend(heading)
    for name, trace in (("QR", projected), ("Riemann", riemannian)):
        detail, y = _text_lines(
            FIGURE_MARGIN,
            y,
            f"{name}: 直交性 {_metric(metric_max(trace, 'orthogonality_error'))}"
            f" · 行列式 {_metric(metric_max(trace, 'determinant_error'))}",
            "metric",
            size=TEXT_SIZE["metric"],
        )
        body.extend(detail)
    footer, height = _figure_footer(
        y + 8,
        f"optimization_compass.constraint_geometry.generate_so3_traces · dataset {dataset_version}",
        "固定した3対応・ノイズなし・固定stepです。速さの順位や、一般的な局所収束は示しません。",
    )
    body.extend(footer)
    return _figure_document(
        "SO(3)へ戻る二つの一歩は、同じではない",
        (
            "単位行列から同じπに近い目標へ向かう固定Python実行です。"
            "Projected Gradientは外側の空間でstepを取った後にQRで射影し、Riemann勾配法は"
            "Lie代数上の接空間でのstepをexponential mapで戻します。12回の更新の"
            "geodesic残差、最初の更新での写像による補正、受理した回転の直交性と"
            "行列式の残差を比較します。固定3対応、ノイズなし、固定stepの教材であり、"
            "一般的な性能の順位ではありません。"
        ),
        height,
        body,
    )


def _least_squares_fit_svg(dataset_version: str) -> str:
    trace = next(
        trace
        for trace in generate_parameter_estimation_traces(dataset_version=dataset_version)
        if trace.trace_id == "exponential-fit-lm"
    )
    initial, final = trace.frames[0], trace.frames[-1]
    time_start, time_stop, observation_count = 0.0, 5.0, 20
    times = [
        time_start + index * (time_stop - time_start) / (observation_count - 1)
        for index in range(observation_count)
    ]
    truth_a, truth_k, truth_c = (float(value) for value in trace.parameters["truth"])
    observations = [truth_a * math.exp(-truth_k * time) + truth_c for time in times]
    panel_specs = (
        ("初期のパラメータ", initial, "#d67835", ' stroke-dasharray="8 6"'),
        ("12回の評価の後", final, "#245c42", ""),
    )
    plot_x, plot_width, plot_height = 52.0, 352.0, 150.0
    response_min, response_max = 0.0, 2.2

    def project_x(time: float) -> float:
        return plot_x + (time - time_start) / (time_stop - time_start) * plot_width

    def project_y(response: float, plot_y: float) -> float:
        return (
            plot_y
            + plot_height
            - (response - response_min) / (response_max - response_min) * plot_height
        )

    title = "曲線が重なっても、診断は終わらない"
    body, y = _figure_heading(title, "観測20点・ノイズなし・a exp(-k t)+c・評価予算12回")
    legend_y = y + 14
    body.extend(
        [
            f'<circle cx="{FIGURE_MARGIN + 6}" cy="{legend_y - 5:g}" r="5.5" fill="#245c42" '
            'stroke="#fff" stroke-width="2"/>',
            f'<text x="{FIGURE_MARGIN + 18}" y="{legend_y:g}" class="note">観測</text>',
            f'<line x1="{FIGURE_MARGIN + 74}" y1="{legend_y - 5:g}" x2="{FIGURE_MARGIN + 100}" '
            f'y2="{legend_y - 5:g}" stroke="#d67835" stroke-width="3.5"/>',
            f'<text x="{FIGURE_MARGIN + 108}" y="{legend_y:g}" class="note">modelの曲線</text>',
            f'<line x1="{FIGURE_MARGIN + 226}" y1="{legend_y - 15:g}" x2="{FIGURE_MARGIN + 226}" '
            f'y2="{legend_y + 3:g}" stroke="#bd6754" stroke-width="2.5"/>',
            f'<text x="{FIGURE_MARGIN + 236}" y="{legend_y:g}" class="note">点ごとの残差</text>',
        ]
    )
    y = legend_y + 2
    for panel_title, frame, color, dash in panel_specs:
        parameters = [float(value) for value in frame.points[0].coordinates]
        amplitude, rate, offset = parameters
        metrics = {metric.metric_id: float(metric.value) for metric in frame.metrics}
        panel, top, panel_bottom = _panel(y + 12, panel_title, 22 + 14 + plot_height + 30)
        body.extend(panel)
        body.append(
            f'<text x="{FIGURE_MARGIN + 14}" y="{top + 4:g}" class="status">'
            f"a={amplitude:.3f} · k={rate:.3f} · c={offset:.3f} · "
            f"‖r‖={metrics['residual_norm']:.3f}</text>"
        )
        plot_y = top + 22
        predictions = [amplitude * math.exp(-rate * time) + offset for time in times]
        curve_points = " ".join(
            f"{project_x(time):.2f},{project_y(prediction, plot_y):.2f}"
            for time, prediction in zip(times, predictions, strict=True)
        )
        body.append(
            f'<rect x="{plot_x - 10:g}" y="{plot_y:g}" width="{plot_width + 20:g}" '
            f'height="{plot_height:g}" rx="10" fill="#fbfcfa"/>'
        )
        for response in (0.0, 1.0, 2.0):
            tick_y = project_y(response, plot_y)
            body.extend(
                [
                    f'<line x1="{plot_x - 10:g}" y1="{tick_y:.2f}" '
                    f'x2="{plot_x + plot_width + 10:g}" y2="{tick_y:.2f}" stroke="#ebe8e0"/>',
                    f'<text x="{plot_x - 16:g}" y="{tick_y + 5:.2f}" text-anchor="end" '
                    f'class="axis">{response:g}</text>',
                ]
            )
        for time, observation, prediction in zip(times, observations, predictions, strict=True):
            x = project_x(time)
            body.append(
                f'<line x1="{x:.2f}" y1="{project_y(observation, plot_y):.2f}" '
                f'x2="{x:.2f}" y2="{project_y(prediction, plot_y):.2f}" '
                'stroke="#bd6754" stroke-width="2" opacity="0.72"/>'
            )
        body.append(
            f'<polyline points="{curve_points}" fill="none" stroke="{color}" '
            f'stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"{dash}/>'
        )
        for time, observation in zip(times, observations, strict=True):
            body.append(
                f'<circle cx="{project_x(time):.2f}" cy="{project_y(observation, plot_y):.2f}" '
                'r="4" fill="#245c42" stroke="#fff" stroke-width="1.5"/>'
            )
        for tick in (0.0, 2.5, 5.0):
            body.append(
                f'<text x="{project_x(tick):.2f}" y="{plot_y + plot_height + 20:g}" '
                f'text-anchor="middle" class="axis">{tick:g}</text>'
            )
        y = panel_bottom
    history_height = 120.0
    panel, top, panel_bottom = _panel(y + 12, "曲線の下で追う診断値", history_height + 22)
    body.extend(panel)
    history_x, history_width, history_y = plot_x, plot_width, top + 4
    log_min, log_max = -2.0, 0.4

    def history_point(frame: TraceFrame, metric_id: str) -> tuple[float, float]:
        value = _metric_value(frame, metric_id)
        bounded = min(10**log_max, max(10**log_min, value))
        return (
            history_x
            + (frame.oracle_evaluations - 1) / (trace.evaluation_budget - 1) * history_width,
            history_y
            + history_height
            - (math.log10(bounded) - log_min) / (log_max - log_min) * history_height,
        )

    for exponent in (-2, -1, 0):
        tick_y = (
            history_y + history_height - (exponent - log_min) / (log_max - log_min) * history_height
        )
        body.extend(
            [
                f'<line x1="{history_x:g}" y1="{tick_y:.2f}" x2="{history_x + history_width:g}" '
                f'y2="{tick_y:.2f}" stroke="#ebe8e0"/>',
                f'<text x="{history_x - 8:g}" y="{tick_y + 5:.2f}" text-anchor="end" '
                f'class="axis">1e{exponent}</text>',
            ]
        )
    for metric_id, color in (("residual_norm", "#245c42"), ("parameter_error", "#d67835")):
        points = [history_point(frame, metric_id) for frame in trace.frames]
        point_string = " ".join(f"{x:.2f},{y:.2f}" for x, y in points)
        body.append(
            f'<polyline points="{point_string}" fill="none" stroke="{color}" '
            'stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>'
        )
        for x, point_y in points:
            body.append(f'<circle cx="{x:.2f}" cy="{point_y:.2f}" r="3" fill="{color}"/>')
    y = panel_bottom + 34
    for color, label, value in (
        ("#245c42", "残差ノルム", "1.867 → 0.034"),
        ("#d67835", "真値からのパラメータ距離", "0.890 → 0.036"),
    ):
        row, y = _legend_row(y, color, label, value)
        body.extend(row)
    footer, height = _figure_footer(
        y + 4,
        "generate_parameter_estimation_traces · solverに依存しないdamped Gauss–Newton probe"
        f" · dataset {dataset_version}",
        "20点・ノイズなしの合成データです。LMやSciPyの実行結果ではありません。"
        "識別性、統計的な妥当性、実データへの適合は保証しません。",
    )
    body.extend(footer)
    return _figure_document(
        "曲線が重なっても、診断は終わらない",
        (
            "20点のノイズなし合成データに3パラメータの指数減衰modelを当てる固定Python診断"
            "probeです。初期のパラメータと12回の評価の後の予測曲線、観測ごとの残差、残差"
            "ノルム、既知の真値からのパラメータ距離を比較します。12回の評価の後の曲線は観測へ"
            "近づきますが、停止条件には到達していません。LMやSciPy solverの実行"
            "結果ではありません。"
        ),
        height,
        body,
    )


def _bayesian_optimization_svg(dataset_version: str) -> str:
    generated = generate_surrogate_scenario(
        dataset_version=dataset_version,
        strategy="explore",
        noise_preset="noiseless",
    )
    frames = (generated.payload.frames[0], generated.payload.frames[3])
    panel_specs = (
        ("初期観測の直後", frames[0]),
        ("3点を追加した後", frames[1]),
    )
    domain_min, domain_max = generated.payload.domain
    value_min, value_max = -1.3, 4.0
    plot_x, plot_width, plot_height = 52.0, 352.0, 160.0
    acquisition_height = 56.0

    def project_x(value: float) -> float:
        return plot_x + (value - domain_min) / (domain_max - domain_min) * plot_width

    def project_y(value: float, plot_y: float) -> float:
        bounded = min(value_max, max(value_min, value))
        return plot_y + plot_height - (bounded - value_min) / (value_max - value_min) * plot_height

    title = "観測が増えると、次の評価点も動く"
    body, y = _figure_heading(title, "固定seed・1次元・ノイズなし・RBF kernel・評価予算10回")
    legend_y = y + 14
    body.extend(
        [
            f'<line x1="{FIGURE_MARGIN}" y1="{legend_y - 5:g}" x2="{FIGURE_MARGIN + 26}" '
            f'y2="{legend_y - 5:g}" stroke="#245c42" stroke-width="3.5"/>',
            f'<text x="{FIGURE_MARGIN + 34}" y="{legend_y:g}" class="note">surrogateの平均</text>',
            f'<rect x="{FIGURE_MARGIN + 160}" y="{legend_y - 13:g}" width="26" height="15" '
            'rx="4" fill="#cfe7dc"/>',
            f'<text x="{FIGURE_MARGIN + 194}" y="{legend_y:g}" class="note">不確実性</text>',
            f'<line x1="{FIGURE_MARGIN}" y1="{legend_y + 19:g}" x2="{FIGURE_MARGIN + 26}" '
            f'y2="{legend_y + 19:g}" stroke="#617068" stroke-width="2.5" '
            'stroke-dasharray="6 5"/>',
            f'<text x="{FIGURE_MARGIN + 34}" y="{legend_y + 24:g}" class="note">'
            "真の関数（教材の答え合わせ用）</text>",
        ]
    )
    y = legend_y + 26
    for panel_title, frame in panel_specs:
        selected_x = float(frame.selected_point)
        max_acquisition = max(point.acquisition for point in frame.predictive_summary)
        panel, top, panel_bottom = _panel(
            y + 12, panel_title, 22 + plot_height + 32 + acquisition_height + 30
        )
        body.extend(panel)
        body.append(
            f'<text x="{FIGURE_MARGIN + 14}" y="{top + 4:g}" class="status">'
            f"実際の評価 {frame.oracle_evaluations}回 · 次の x={selected_x:.2f}</text>"
        )
        plot_y = top + 18
        acquisition_y = plot_y + plot_height + 32
        selected_screen_x = project_x(selected_x)
        uncertainty_points = [
            (project_x(point.x), project_y(point.upper, plot_y))
            for point in frame.predictive_summary
        ] + [
            (project_x(point.x), project_y(point.lower, plot_y))
            for point in reversed(frame.predictive_summary)
        ]
        uncertainty_polygon = " ".join(f"{x:.2f},{y:.2f}" for x, y in uncertainty_points)
        mean_points = " ".join(
            f"{project_x(point.x):.2f},{project_y(point.mean, plot_y):.2f}"
            for point in frame.predictive_summary
        )
        truth_points = " ".join(
            f"{project_x(point.x):.2f},{project_y(point.true_value, plot_y):.2f}"
            for point in frame.predictive_summary
        )
        acquisition_points = [
            (
                project_x(point.x),
                acquisition_y
                + acquisition_height
                - (
                    point.acquisition / max_acquisition * acquisition_height
                    if max_acquisition
                    else 0.0
                ),
            )
            for point in frame.predictive_summary
        ]
        acquisition_point_string = " ".join(f"{x:.2f},{y:.2f}" for x, y in acquisition_points)
        _, selected_acquisition_y = min(
            acquisition_points,
            key=lambda point: abs(point[0] - selected_screen_x),
        )
        acquisition_path = " ".join(
            [
                f"{plot_x:.2f},{acquisition_y + acquisition_height:.2f}",
                *(f"{x:.2f},{y:.2f}" for x, y in acquisition_points),
                f"{plot_x + plot_width:.2f},{acquisition_y + acquisition_height:.2f}",
            ]
        )
        body.append(
            f'<rect x="{plot_x:g}" y="{plot_y:g}" width="{plot_width:g}" '
            f'height="{plot_height:g}" rx="10" fill="#fbfcfa"/>'
        )
        for tick in (-1.0, 0.0, 2.0, 4.0):
            tick_y = project_y(tick, plot_y)
            body.extend(
                [
                    f'<line x1="{plot_x:g}" y1="{tick_y:.2f}" x2="{plot_x + plot_width:g}" '
                    f'y2="{tick_y:.2f}" stroke="#ebe8e0"/>',
                    f'<text x="{plot_x - 8:g}" y="{tick_y + 5:.2f}" text-anchor="end" '
                    f'class="axis">{tick:g}</text>',
                ]
            )
        body.extend(
            [
                f'<polygon points="{uncertainty_polygon}" fill="#cfe7dc" opacity="0.82"/>',
                f'<polyline points="{truth_points}" fill="none" stroke="#617068" '
                'stroke-width="2" stroke-dasharray="6 5"/>',
                f'<polyline points="{mean_points}" fill="none" stroke="#245c42" '
                'stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>',
                f'<line x1="{selected_screen_x:.2f}" y1="{plot_y:g}" '
                f'x2="{selected_screen_x:.2f}" y2="{acquisition_y + acquisition_height:g}" '
                'stroke="#d67835" stroke-width="2.5" stroke-dasharray="6 5"/>',
            ]
        )
        for observation in frame.observations:
            body.append(
                f'<circle cx="{project_x(observation.x):.2f}" '
                f'cy="{project_y(observation.observed_value, plot_y):.2f}" r="5.5" '
                'fill="#245c42" stroke="#fff" stroke-width="2"/>'
            )
        body.extend(
            [
                f'<text x="{plot_x:g}" y="{acquisition_y - 8:g}" class="axis">'
                "Expected Improvement</text>",
                f'<text x="{plot_x + plot_width:g}" y="{acquisition_y - 8:g}" '
                f'text-anchor="end" class="axis">最大 {max_acquisition:.3f}</text>',
                f'<rect x="{plot_x:g}" y="{acquisition_y:g}" width="{plot_width:g}" '
                f'height="{acquisition_height:g}" rx="8" fill="#fbf4ed"/>',
                f'<polygon points="{acquisition_path}" fill="#efc5a5" opacity="0.9"/>',
                f'<polyline points="{acquisition_point_string}" fill="none" stroke="#d67835" '
                'stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>',
                f'<circle cx="{selected_screen_x:.2f}" cy="{selected_acquisition_y:.2f}" '
                'r="5" fill="#d67835" stroke="#fff" stroke-width="2"/>',
            ]
        )
        for tick in (-3.0, 0.0, 3.0):
            body.append(
                f'<text x="{project_x(tick):.2f}" y="{acquisition_y + acquisition_height + 20:g}" '
                f'text-anchor="middle" class="axis">{tick:g}</text>'
            )
        y = panel_bottom
    first_uncertainty = float(frames[0].selected_uncertainty)
    later_uncertainty = float(frames[1].selected_uncertainty)
    heading, y = _text_lines(
        FIGURE_MARGIN,
        y + 34,
        "この実行で観測した変化",
        "panel-title",
        size=TEXT_SIZE["panel-title"],
    )
    body.extend(heading)
    rows, y = _metric_rows(
        y,
        (
            ("実際の評価", f"{frames[0].oracle_evaluations} → {frames[1].oracle_evaluations}回"),
            (
                "次の x",
                f"{float(frames[0].selected_point):.2f} → {float(frames[1].selected_point):.2f}",
            ),
            ("次の点の不確実性", f"{first_uncertainty:.2f} → {later_uncertainty:.2f}"),
        ),
    )
    body.extend(rows)
    footer, height = _figure_footer(
        y + 8,
        f"generate_surrogate_scenario · explore / noiseless · dataset {dataset_version}",
        "固定seed・1次元・RBF kernelの教材です。大域最適性や一般的な性能は保証しません。",
    )
    body.extend(footer)
    return _figure_document(
        "観測が増えると、次の評価点も動く",
        (
            "固定seedの1次元black-boxをGaussian-process Bayesian Optimizationで実行し、"
            "3回の評価後と6回の評価後のsurrogateの平均、不確実性、Expected Improvement、"
            "次の評価点を比較します。真の目的関数は教材用の答え合わせであり、"
            "optimizerは観測点以外の真値を参照しません。"
        ),
        height,
        body,
    )


def _optimal_control_mesh_svg(dataset_version: str) -> str:
    traces = _generate_optimal_control_traces(dataset_version=dataset_version)
    trace_styles = {
        "pendulum-collocation-coarse": ("N=20", "#245c42", False),
        "pendulum-collocation-refined": ("N=40", "#456b92", False),
        "pendulum-model-rollout-failure": ("モデル不一致（重力 +10%）", "#a53d3d", True),
    }
    panels = (
        ("mesh nodeでのpath制約違反", "node_path_violation"),
        ("区間内の再構成と検証rolloutでの違反", "reconstructed_path_violation"),
    )
    title = "mesh上で収束しても、区間内の違反は別に残る"
    body, y = _figure_heading(title, "同じ振り子・時間幅2 s・同じ初期軌道・評価予算8回")
    plot_x = FIGURE_MARGIN + 42.0
    plot_width = FIGURE_WIDTH - FIGURE_MARGIN - 8 - plot_x
    plot_height = 170.0
    log_min, log_max = -5.0, 0.0

    def project(
        *,
        iteration: int,
        value: float,
        plot_y: float,
        max_iteration: int,
    ) -> tuple[float, float]:
        bounded = min(10**log_max, max(10**log_min, value))
        return (
            plot_x + iteration / max_iteration * plot_width,
            plot_y
            + plot_height
            - (math.log10(bounded) - log_min) / (log_max - log_min) * plot_height,
        )

    for panel_index, (panel_title, metric_key) in enumerate(panels):
        heading, y = _text_lines(
            FIGURE_MARGIN, y + 22, panel_title, "panel-title", size=TEXT_SIZE["panel-title"]
        )
        body.extend(heading)
        plot_y = y - 6
        body.extend(
            _plot_frame(
                plot_x - 8, plot_y, plot_width + 16, plot_height, f"mesh-plot-{panel_index}"
            )
        )
        for exponent in range(-5, 1):
            _, tick_y = project(iteration=0, value=10.0**exponent, plot_y=plot_y, max_iteration=8)
            body.extend(
                [
                    (
                        f'<line x1="{plot_x - 8:g}" y1="{tick_y:.2f}" '
                        f'x2="{plot_x + plot_width + 8:g}" y2="{tick_y:.2f}" stroke="#ebe8e0"/>'
                    ),
                    (
                        f'<text x="{plot_x - 14:g}" y="{tick_y + 5:.2f}" '
                        f'text-anchor="end" class="axis">1e{exponent}</text>'
                    ),
                ]
            )
        _, tolerance_y = project(iteration=0, value=1e-4, plot_y=plot_y, max_iteration=8)
        body.extend(
            [
                (
                    f'<line x1="{plot_x - 8:g}" y1="{tolerance_y:.2f}" '
                    f'x2="{plot_x + plot_width + 8:g}" y2="{tolerance_y:.2f}" '
                    'stroke="#c56b32" stroke-width="2" stroke-dasharray="5 5"/>'
                ),
                (
                    f'<text x="{plot_x + 4:g}" y="{tolerance_y + 20:.2f}" '
                    'class="axis halo" fill="#9a4f24">許容値 1e-4</text>'
                ),
            ]
        )
        for trace in traces:
            _, color, dashed = trace_styles[trace.trace_id]
            dash = ' stroke-dasharray="10 6"' if dashed else ""
            points = [
                project(
                    iteration=frame.iteration,
                    value=float(frame.payload[metric_key]),
                    plot_y=plot_y,
                    max_iteration=trace.frames[-1].iteration,
                )
                for frame in trace.frames
            ]
            point_string = " ".join(f"{x:.2f},{y:.2f}" for x, y in points)
            body.append(
                f'<polyline points="{point_string}" fill="none" stroke="{color}" '
                f'stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"{dash}/>'
            )
            for x, point_y in points:
                body.append(f'<circle cx="{x:.2f}" cy="{point_y:.2f}" r="3" fill="{color}"/>')
        body.append(
            f'<text x="{plot_x + plot_width / 2:g}" y="{plot_y + plot_height + 22:g}" '
            'text-anchor="middle" class="axis">反復 →</text>'
        )
        y = plot_y + plot_height + 26
    y += 30
    for trace in traces:
        label, color, dashed = trace_styles[trace.trace_id]
        terminal = trace.frames[-1]
        node = float(terminal.payload["node_path_violation"])
        reconstructed = float(terminal.payload["reconstructed_path_violation"])
        row, y = _legend_row(
            y,
            color,
            label,
            detail=f"終了時 node上 {node:.1e} · 区間内 {reconstructed:.3g}",
            dash=dashed,
        )
        body.extend(row)
    footer, height = _figure_footer(
        y + 4,
        f"optimization_compass.site_export._generate_optimal_control_traces"
        f" · dataset {dataset_version}",
        "固定した振り子教材の診断履歴です。連続時間での実行可能性、実機の安全性、"
        "一般的な性能は保証しません。",
    )
    body.extend(footer)
    return _figure_document(
        title,
        (
            "同じpendulum swing-up教材でN=20、N=40、重力を10%変えた検証rolloutを"
            "比較します。mesh node上のpath制約違反は許容値内まで下がりますが、"
            "区間内の再構成とモデル不一致では別の違反が残ります。"
        ),
        height,
        body,
    )


def _constrained_feasibility_svg(dataset_version: str) -> str:
    artifact = generate_feasible_region_artifact(dataset_version)
    title = "目的値が下がっても、制約違反なら解ではない"
    body, y = _figure_heading(title, "min x²+y²・(x−1)²+(y−1)² ≤ 1・固定の教材用実行記録")
    plot_x, plot_y, plot_width = float(FIGURE_MARGIN), y + 8, float(CONTENT_WIDTH)
    plot_height = round(plot_width * 500 / 624)
    x_min, x_max = artifact.bounds.x
    y_min, y_max = artifact.bounds.y

    def project(point: tuple[float, float]) -> tuple[float, float]:
        x, y = point
        return (
            plot_x + (x - x_min) / (x_max - x_min) * plot_width,
            plot_y + plot_height - (y - y_min) / (y_max - y_min) * plot_height,
        )

    center_x, center_y = project(artifact.constraint.center)
    radius = artifact.constraint.radius / (x_max - x_min) * plot_width
    body.extend(_plot_frame(plot_x, plot_y, plot_width, plot_height, "feasible-plot"))
    body.append('<g clip-path="url(#feasible-plot)">')
    origin_x, origin_y = project((0.0, 0.0))
    for level in artifact.contour_values:
        contour_radius = math.sqrt(level) / (x_max - x_min) * plot_width
        body.append(
            f'<circle cx="{origin_x:.2f}" cy="{origin_y:.2f}" r="{contour_radius:.2f}" '
            'fill="none" stroke="#dedbd2" stroke-width="1.5"/>'
        )
    body.extend(
        [
            (
                f'<circle cx="{center_x:.2f}" cy="{center_y:.2f}" r="{radius:.2f}" '
                'fill="#dcefe4" fill-opacity="0.88" stroke="#245c42" stroke-width="3"/>'
            ),
            "</g>",
            (
                f'<text x="{center_x:.2f}" y="{center_y - radius + 26:.2f}" '
                'text-anchor="middle" class="panel-title" fill="#245c42">実行可能領域</text>'
            ),
        ]
    )
    path_styles = {
        "constraint_aware": ("制約を評価", "#245c42"),
        "unconstrained_failure": ("制約を無視", "#c56b32"),
    }
    summaries: list[tuple[str, str, float, float, bool]] = []
    for path in artifact.paths:
        label, color = path_styles[path.role]
        points = [project(step.point) for step in path.steps]
        point_string = " ".join(f"{x:.2f},{y:.2f}" for x, y in points)
        dashed = path.role == "unconstrained_failure"
        dash = ' stroke-dasharray="10 6"' if dashed else ""
        body.append(
            f'<polyline points="{point_string}" fill="none" stroke="{color}" '
            f'stroke-width="4" stroke-linecap="round" stroke-linejoin="round"{dash}/>'
        )
        for index, (x, y) in enumerate(points):
            radius_value = 5.5 if index in {0, len(points) - 1} else 3
            fill = "#fff" if index == 0 else color
            body.append(
                f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{radius_value}" '
                f'fill="{fill}" stroke="{color}" stroke-width="2.5"/>'
            )
        terminal = path.steps[-1]
        summaries.append((label, color, terminal.objective, terminal.violation, dashed))
    note, y = _text_lines(
        FIGURE_MARGIN,
        plot_y + plot_height + 28,
        "○ 共通の初期点　● 終了点　実線: 制約を評価　破線: 制約を無視",
        "note",
    )
    body.extend(note)
    y += 10
    for label, color, objective, violation, dashed in summaries:
        row, y = _legend_row(
            y, color, label, f"f={objective:.3f} · 違反量={violation:.3f}", dash=dashed
        )
        body.extend(row)
    footer, height = _figure_footer(
        y + 4,
        "optimization_compass.learning_slices.generate_feasible_region_artifact"
        f" · dataset {dataset_version}",
        "固定した2次元の教材です。SLSQPやBFGSの実装性能や、一般的な収束性は示しません。",
    )
    body.extend(footer)
    return _figure_document(title, artifact.text_alternative_ja, height, body)


def _pareto_preference_svg(dataset_version: str) -> str:
    artifact = generate_pareto_front_artifact(dataset_version)
    title = "同じPareto frontでも、重みで選ぶ点が動く"
    body, y = _figure_heading(title, "2目的の二次関数・81点を標本化・教材用の厳密なfront")
    axis_y, y = _text_lines(
        FIGURE_MARGIN, y + 6, "縦軸 f₂: 点(2,2)からの距離²（小さいほど良い）", "axis"
    )
    body.extend(axis_y)
    plot_x, plot_y = FIGURE_MARGIN + 26.0, y - 6
    plot_width = FIGURE_WIDTH - FIGURE_MARGIN - plot_x
    plot_height = round(plot_width * 500 / 600)
    lower, upper = -0.4, 8.4

    def project(objectives: tuple[float, float]) -> tuple[float, float]:
        first, second = objectives
        return (
            plot_x + (first - lower) / (upper - lower) * plot_width,
            plot_y + plot_height - (second - lower) / (upper - lower) * plot_height,
        )

    body.extend(_plot_frame(plot_x, plot_y, plot_width, plot_height, "pareto-plot"))
    for tick in (0, 2, 4, 6, 8):
        tick_x, _ = project((float(tick), 0.0))
        _, tick_y = project((0.0, float(tick)))
        body.extend(
            [
                (
                    f'<line x1="{tick_x:.2f}" y1="{plot_y:g}" x2="{tick_x:.2f}" '
                    f'y2="{plot_y + plot_height:g}" stroke="#ebe8e0"/>'
                ),
                (
                    f'<line x1="{plot_x:g}" y1="{tick_y:.2f}" x2="{plot_x + plot_width:g}" '
                    f'y2="{tick_y:.2f}" stroke="#ebe8e0"/>'
                ),
                (
                    f'<text x="{tick_x:.2f}" y="{plot_y + plot_height + 20:g}" '
                    f'text-anchor="middle" class="axis">{tick}</text>'
                ),
                (
                    f'<text x="{plot_x - 8:g}" y="{tick_y + 5:.2f}" '
                    f'text-anchor="end" class="axis">{tick}</text>'
                ),
            ]
        )
    for point in artifact.points:
        x, y = project(point.objectives)
        fill = "#b8b5ad" if point.dominated else "#7ca993"
        opacity = "0.55" if point.dominated else "0.8"
        body.append(
            f'<circle cx="{x:.2f}" cy="{y:.2f}" r="3.5" fill="{fill}" opacity="{opacity}"/>'
        )
    front_points = " ".join(
        f"{x:.2f},{y:.2f}"
        for x, y in (project(point.objectives) for point in artifact.pareto_front)
    )
    body.append(
        f'<polyline points="{front_points}" fill="none" stroke="#245c42" '
        'stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>'
    )
    for selection in artifact.preference_selections:
        x, y = project(selection.objectives)
        body.extend(
            [
                (
                    f'<circle cx="{x:.2f}" cy="{y:.2f}" r="7" fill="#c56b32" '
                    'stroke="#fff" stroke-width="3"/>'
                ),
                (
                    f'<text x="{x + 12:.2f}" y="{y - 10:.2f}" class="method halo" '
                    f'fill="#9a4f24">w₁={selection.weight_f1:.1f}</text>'
                ),
            ]
        )
    ideal_x, ideal_y = project(artifact.reference.ideal)
    body.extend(
        [
            (
                f'<path d="M {ideal_x - 6:.2f} {ideal_y:.2f} H {ideal_x + 6:.2f} '
                f'M {ideal_x:.2f} {ideal_y - 6:.2f} V {ideal_y + 6:.2f}" '
                'stroke="#a53d3d" stroke-width="2.5"/>'
            ),
            (
                f'<text x="{ideal_x + 12:.2f}" y="{ideal_y + 5:.2f}" '
                'class="status halo" fill="#a53d3d">理想点（同時には到達不能）</text>'
            ),
        ]
    )
    axis_x, y = _text_lines(
        FIGURE_MARGIN,
        plot_y + plot_height + 44,
        "横軸 f₁: 原点からの距離²（小さいほど良い）",
        "axis",
    )
    body.extend(axis_x)
    note, y = _text_lines(
        FIGURE_MARGIN, y + 6, "灰: 支配される点　青緑: Pareto front　橙: 重みで選んだ点", "note"
    )
    body.extend(note)
    footer, height = _figure_footer(
        y + 8,
        "optimization_compass.learning_slices.generate_pareto_front_artifact"
        f" · dataset {dataset_version}",
        "凸な2目的の固定教材です。重みは客観的な優先度でも、一般的な性能の順位でもありません。",
    )
    body.extend(footer)
    return _figure_document(title, artifact.text_alternative_ja, height, body)


def _gradient_family_svg(dataset_version: str) -> str:
    bundle = generate_gradient_bundle(dataset_version=dataset_version)
    traces = bundle.member_traces
    styles = {
        "gradient_descent": ("Gradient Descent", "#245c42"),
        "momentum": ("Momentum", "#c56b32"),
        "adam": ("Adam", "#456b92"),
    }
    title = "同じ谷でも、更新則で軌跡が変わる"
    body, y = _figure_heading(title, "f(x,y)=100x²+y²・同じ初期点・評価40回・固定設定")
    x_bounds, y_bounds = (-1.8, 1.6), (-0.2, 1.8)
    plot_x, plot_y, plot_width = float(FIGURE_MARGIN), y + 8, float(CONTENT_WIDTH)
    plot_height = round(plot_width * 0.62)

    def project(point: tuple[float, float] | list[float]) -> tuple[float, float]:
        x, y = point
        return (
            plot_x + (x - x_bounds[0]) / (x_bounds[1] - x_bounds[0]) * plot_width,
            plot_y + plot_height - (y - y_bounds[0]) / (y_bounds[1] - y_bounds[0]) * plot_height,
        )

    body.append(
        f'<rect x="{plot_x:g}" y="{plot_y:g}" width="{plot_width:g}" height="{plot_height:g}" '
        'rx="12" fill="#fff" stroke="#cfd8d1"/>'
    )
    body.append(
        f'<clipPath id="gradient-plot"><rect x="{plot_x:g}" y="{plot_y:g}" '
        f'width="{plot_width:g}" height="{plot_height:g}" rx="12"/></clipPath>'
    )
    contours = []
    center = project((0.0, 0.0))
    for level in (1.0, 4.0, 16.0, 64.0, 256.0):
        radius_x, radius_y = math.sqrt(level / 100.0), math.sqrt(level)
        rx = radius_x / (x_bounds[1] - x_bounds[0]) * plot_width
        ry = radius_y / (y_bounds[1] - y_bounds[0]) * plot_height
        contours.append(
            f'<ellipse cx="{center[0]:.2f}" cy="{center[1]:.2f}" rx="{rx:.2f}" '
            f'ry="{ry:.2f}" fill="none" stroke="#d9dfda" stroke-width="1.5"/>'
        )
    body.append(f'<g clip-path="url(#gradient-plot)">{"".join(contours)}</g>')
    optimum = project((0.0, 0.0))
    body.extend(
        [
            (
                f'<line x1="{optimum[0]:.2f}" y1="{plot_y:g}" x2="{optimum[0]:.2f}" '
                f'y2="{plot_y + plot_height:g}" stroke="#e4e8e4"/>'
            ),
            (
                f'<line x1="{plot_x:g}" y1="{optimum[1]:.2f}" x2="{plot_x + plot_width:g}" '
                f'y2="{optimum[1]:.2f}" stroke="#e4e8e4"/>'
            ),
            (
                f'<circle cx="{optimum[0]:.2f}" cy="{optimum[1]:.2f}" r="5" '
                'fill="#fff" stroke="#1f2924" stroke-width="2"/>'
            ),
            (
                f'<text x="{optimum[0] + 10:.2f}" y="{optimum[1] + 20:.2f}" '
                'class="axis halo">最適解</text>'
            ),
        ]
    )
    rows: list[str] = []
    row_y = plot_y + plot_height + 30
    legend, row_y = _text_lines(
        FIGURE_MARGIN, row_y, "○ 開始点　● 終了点　楕円は目的関数の等高線", "note"
    )
    rows.extend(legend)
    row_y += 10
    for trace in traces:
        method = str(trace.frames[0].payload["method"])
        label, color = styles[method]
        points = [
            project(tuple(frame.points[0].coordinates)) for frame in trace.frames if frame.points
        ]
        point_string = " ".join(f"{x:.2f},{y:.2f}" for x, y in points)
        start_x, start_y = points[0]
        end_x, end_y = points[-1]
        body.extend(
            [
                (
                    f'<polyline points="{point_string}" fill="none" stroke="{color}" '
                    'stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>'
                ),
                (
                    f'<circle cx="{start_x:.2f}" cy="{start_y:.2f}" r="5" fill="#fff" '
                    f'stroke="{color}" stroke-width="2.5"/>'
                ),
                f'<circle cx="{end_x:.2f}" cy="{end_y:.2f}" r="6" fill="{color}"/>',
            ]
        )
        terminal_value = _objective_value(trace.frames[-1])
        status = TERMINAL_STATUS_JA[trace.terminal_status]
        rows.extend(
            [
                (
                    f'<line x1="{FIGURE_MARGIN}" y1="{row_y - 5}" x2="{FIGURE_MARGIN + 28}" '
                    f'y2="{row_y - 5}" stroke="{color}" stroke-width="4"/>'
                ),
                (
                    f'<text x="{FIGURE_MARGIN + 38}" y="{row_y}" class="method">'
                    f"{html.escape(label)}</text>"
                ),
                (
                    f'<text x="{FIGURE_WIDTH - FIGURE_MARGIN}" y="{row_y}" text-anchor="end" '
                    f'class="metric">最終 f = {_metric(terminal_value)}</text>'
                ),
                (
                    f'<text x="{FIGURE_MARGIN + 38}" y="{row_y + 22}" class="status">'
                    f"評価{trace.frames[-1].oracle_evaluations}回 · {status}</text>"
                ),
            ]
        )
        row_y += 54
    body.extend(rows)
    footer, height = _figure_footer(
        row_y + 4,
        f"optimization_compass.traces.generate_gradient_bundle · dataset {dataset_version}",
        "この固定設定での軌跡で、一般的な性能の順位ではありません。",
    )
    body.extend(footer)
    return _figure_document(
        title,
        (
            "f(x,y)=100x²+y²を同じ初期点と40回の評価予算で実行した結果です。"
            "Gradient Descent、Momentum、Adamの軌跡と最終目的値を示します。"
        ),
        height,
        body,
    )


def _portfolio_risk_svg(dataset_version: str) -> str:
    traces = generate_portfolio_uncertainty_traces(dataset_version=dataset_version)
    panels = (
        ("公称目的", traces[0], "#245c42"),
        ("CVaRを含む目的", traces[1], "#c56b32"),
    )
    objective_labels = {
        "training mean loss": "学習用データの平均損失",
        "training mean loss + 0.5 CVaR_0.75": "学習用データの平均損失 + 0.5·CVaR 75%",
    }
    asset_colors = ("#245c42", "#c56b32", "#456b92", "#8b7d58")
    title = "同じ標本でも、リスクの置き方で配分が変わる"
    body, y = _figure_heading(
        title, "4資産・学習用データ8件と評価用データ4件・同じ上限付き単体・α = 0.75"
    )
    inner_x = FIGURE_MARGIN + 14
    inner_right = FIGURE_WIDTH - FIGURE_MARGIN - 14
    columns = (inner_right - 172, inner_right - 86, inner_right)
    for label, trace, accent in panels:
        panel_y = y + 8
        weights = trace.frames[0].points[0].coordinates
        training = trace.frames[1]
        held_out = trace.frames[2]
        content = [
            (
                f'<text x="{inner_x}" y="{panel_y + 30:g}" class="panel-title" '
                f'fill="{accent}">{html.escape(label)}</text>'
            ),
        ]
        definition, row_y = _text_lines(
            inner_x,
            panel_y + 52,
            objective_labels[str(trace.objective["definition"])],
            "status",
            width=inner_right - inner_x,
        )
        content.extend(definition)
        bar_y, bar_width, bar_height = row_y - 4, inner_right - inner_x, 26.0
        content.append(
            f'<text x="{inner_x}" y="{bar_y + bar_height + 22:g}" class="metric">配分</text>'
        )
        cursor = float(inner_x)
        for asset_index, (weight, color) in enumerate(zip(weights, asset_colors, strict=True)):
            width = float(weight) * bar_width
            if width > 0:
                content.append(
                    f'<rect x="{cursor:.2f}" y="{bar_y:.2f}" width="{width:.2f}" '
                    f'height="{bar_height}" fill="{color}"/>'
                )
            cursor += width
            label_x = inner_x + 48 + (asset_index % 2) * 170
            label_y = bar_y + bar_height + 22 + (asset_index // 2) * 22
            content.append(
                f'<text x="{label_x}" y="{label_y:g}" class="status">'
                f'<tspan fill="{color}" font-weight="750">●</tspan> '
                f"資産{asset_index + 1}: {float(weight):.2f}</text>"
            )
        header_y = bar_y + bar_height + 84
        content.append(f'<text x="{inner_x}" y="{header_y:g}" class="method">データ</text>')
        for column_x, heading in zip(columns, ("平均損失", "CVaR 75%", "最悪損失"), strict=True):
            content.append(
                f'<text x="{column_x}" y="{header_y:g}" text-anchor="end" class="method">'
                f"{heading}</text>"
            )
        for row_index, (split_label, frame) in enumerate(
            (("学習用 8件", training), ("評価用 4件", held_out))
        ):
            row_y = header_y + 30 + row_index * 28
            content.append(f'<text x="{inner_x}" y="{row_y:g}" class="metric">{split_label}</text>')
            for column_x, metric_id in zip(
                columns, ("mean_loss", "cvar_75", "worst_loss"), strict=True
            ):
                content.append(
                    f'<text x="{column_x}" y="{row_y:g}" text-anchor="end" class="metric-value">'
                    f"{_metric(_metric_value(frame, metric_id))}</text>"
                )
        panel_bottom = header_y + 30 + 28 + 20
        body.append(
            f'<rect x="{FIGURE_MARGIN}" y="{panel_y:g}" width="{CONTENT_WIDTH}" '
            f'height="{panel_bottom - panel_y:g}" rx="12" fill="#fff" stroke="#cfd8d1"/>'
        )
        body.append(
            f'<rect x="{FIGURE_MARGIN}" y="{panel_y + 12:g}" width="4" height="26" '
            f'fill="{accent}"/>'
        )
        body.extend(content)
        y = panel_bottom + 6
    note, y = _text_lines(
        FIGURE_MARGIN,
        y + 22,
        "損失は小さいほど良い。学習用データと評価用データは別々に読みます。",
        "note",
    )
    body.extend(note)
    footer, height = _figure_footer(
        y + 4,
        "optimization_compass.portfolio_uncertainty.generate_portfolio_uncertainty_traces"
        f" · dataset {dataset_version}",
        "固定した8件と4件のシナリオの経験的な要約です。母集団のリスクや将来のリターンは"
        "保証しません。",
    )
    body.extend(footer)
    return _figure_document(
        title,
        (
            "4資産の配分を、同じ学習用データ8件と評価用データ4件で評価した固定教材です。"
            "公称目的とCVaRを含む目的について、配分と平均損失、CVaR 75%、"
            "最悪損失を学習用データと評価用データに分けて示します。"
        ),
        height,
        body,
    )


def _trf_probe_svg(dataset_version: str) -> str:
    traces = {
        trace.trace_id: trace
        for trace in generate_parameter_estimation_traces(dataset_version=dataset_version)
    }
    series = (
        ("通常の初期値", traces["exponential-fit-trf"], "#245c42"),
        ("悪い初期値", traces["exponential-fit-trf-poor-init"], "#c56b32"),
    )
    title = "同じ診断probeでも、初期値で残差の履歴が変わる"
    body, y = _figure_heading(title, "指数減衰のfit・観測20点・評価12回")
    axis_y, y = _text_lines(FIGURE_MARGIN, y + 6, "縦軸: 残差ノルム（対数目盛）", "axis")
    body.extend(axis_y)
    plot_x, plot_y = FIGURE_MARGIN + 34.0, y - 6
    plot_width = FIGURE_WIDTH - FIGURE_MARGIN - 8 - plot_x
    plot_height = 250.0
    log_min, log_max = math.log10(0.03), math.log10(4.0)

    def project(evaluation: int, residual: float) -> tuple[float, float]:
        x = plot_x + (evaluation - 1) / 11 * plot_width
        y = plot_y + (log_max - math.log10(residual)) / (log_max - log_min) * plot_height
        return x, y

    body.extend(_plot_frame(plot_x - 8, plot_y, plot_width + 16, plot_height, "trf-plot"))
    for tick in (3.0, 1.0, 0.3, 0.1, 0.03):
        _, tick_y = project(1, tick)
        body.extend(
            [
                (
                    f'<line x1="{plot_x - 8:g}" y1="{tick_y:.2f}" x2="{plot_x + plot_width + 8:g}" '
                    f'y2="{tick_y:.2f}" stroke="#e2e7e2"/>'
                ),
                (
                    f'<text x="{plot_x - 14:g}" y="{tick_y + 5:.2f}" text-anchor="end" '
                    f'class="axis">{tick:g}</text>'
                ),
            ]
        )
    for evaluation in (1, 4, 8, 12):
        tick_x, _ = project(evaluation, 1.0)
        body.extend(
            [
                (
                    f'<line x1="{tick_x:.2f}" y1="{plot_y:g}" x2="{tick_x:.2f}" '
                    f'y2="{plot_y + plot_height:g}" stroke="#eef1ee"/>'
                ),
                (
                    f'<text x="{tick_x:.2f}" y="{plot_y + plot_height + 20:g}" '
                    f'text-anchor="middle" class="axis">{evaluation}</text>'
                ),
            ]
        )
    rows: list[str] = []
    axis_x, row_y = _text_lines(
        FIGURE_MARGIN, plot_y + plot_height + 44, "横軸: 評価回数　○ 開始　● 12回目", "axis"
    )
    rows.extend(axis_x)
    row_y += 10
    for label, trace, color in series:
        points = [
            project(frame.oracle_evaluations, _metric_value(frame, "residual_norm"))
            for frame in trace.frames
        ]
        point_string = " ".join(f"{x:.2f},{y:.2f}" for x, y in points)
        start_value = _metric_value(trace.frames[0], "residual_norm")
        final_value = _metric_value(trace.frames[-1], "residual_norm")
        end_x, end_y = points[-1]
        body.extend(
            [
                (
                    f'<polyline points="{point_string}" fill="none" stroke="{color}" '
                    'stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>'
                ),
                (
                    f'<circle cx="{points[0][0]:.2f}" cy="{points[0][1]:.2f}" r="5" '
                    f'fill="#fff" stroke="{color}" stroke-width="2.5"/>'
                ),
                f'<circle cx="{end_x:.2f}" cy="{end_y:.2f}" r="5.5" fill="{color}"/>',
            ]
        )
        row, row_y = _legend_row(
            row_y, color, label, f"残差 {_metric(start_value)} → {_metric(final_value)}"
        )
        rows.extend(row)
    body.extend(rows)
    footer, height = _figure_footer(
        row_y + 4,
        "optimization_compass.parameter_estimation.generate_parameter_estimation_traces"
        f" · dataset {dataset_version}",
        "solverの条件を読むための固定した診断probeです。"
        "SciPy TRFの内部反復や性能差ではありません。",
    )
    body.extend(footer)
    return _figure_document(
        title,
        (
            "20観測の指数減衰fitに対する、solverに依存しないdamped Gauss–Newton"
            "診断probeの実行結果です。通常の初期値と悪い初期値について、"
            "評価12回までの残差ノルムを対数目盛で示します。"
            "TRF本体の実行ではありません。"
        ),
        height,
        body,
    )


def _search_tree_proof_svg(dataset_version: str) -> str:
    artifact = generate_search_tree_artifact(dataset_version=dataset_version)
    payload = SearchTreeFramePayload.model_validate(artifact.trace.frames[-1].payload)
    title = "9ノードの探索で、最良値と上界が一致する"
    body, y = _figure_heading(title, "0-1 knapsack・深さ優先で「入れる」側から・固定の教材用実行")
    summary, y = _text_lines(
        FIGURE_MARGIN,
        y + 4,
        f"最良の実行可能値 {payload.best_feasible_value} · 上界 {payload.global_bound:.2f} · "
        f"差 {payload.absolute_gap}",
        "metric",
        size=TEXT_SIZE["metric"],
    )
    body.extend(summary)
    left, right, centre = 115.0, 325.0, FIGURE_WIDTH / 2
    top, step = y + 34, 104.0
    positions = {
        "root": (centre, top),
        "root-0": (left, top + step),
        "root-1": (right, top + step),
        "root-1-0": (left, top + 2 * step),
        "root-1-1": (right, top + 2 * step),
        "root-1-1-0": (left, top + 3 * step),
        "root-1-1-1": (right, top + 3 * step),
        "root-1-1-0-0": (left, top + 4 * step),
        "root-1-1-0-1": (right, top + 4 * step),
    }
    state_labels = {
        "branched": "分岐",
        "bound_pruned": "上界で枝刈り",
        "infeasible_pruned": "実行不能",
        "optimal": "最適解",
        "open": "未探索",
        "active": "評価中",
        "feasible": "実行可能",
    }
    half_width, half_height = 96.0, 38.0
    for node in payload.nodes:
        if node.parent_id is None:
            continue
        parent_x, parent_y = positions[node.parent_id]
        child_x, child_y = positions[node.node_id]
        body.append(
            f'<line x1="{parent_x:.2f}" y1="{parent_y + half_height:.2f}" '
            f'x2="{child_x:.2f}" y2="{child_y - half_height:.2f}" '
            'stroke="#9a968d" stroke-width="2.5"/>'
        )
    for node in payload.nodes:
        x, y = positions[node.node_id]
        fill, stroke = {
            "optimal": ("#d9f2df", "#2d7a46"),
            "infeasible_pruned": ("#f9dddd", "#a53d3d"),
            "bound_pruned": ("#e6e3dc", "#746f65"),
        }.get(node.state, ("#ffffff", "#49463f"))
        bound = "—" if node.bound is None else f"{node.bound:.2f}"
        body.extend(
            [
                (
                    f'<rect x="{x - half_width:.2f}" y="{y - half_height:.2f}" '
                    f'width="{2 * half_width:g}" height="{2 * half_height:g}" '
                    f'rx="10" fill="{fill}" stroke="{stroke}" stroke-width="2.5"/>'
                ),
                (
                    f'<text x="{x:.2f}" y="{y - 13:.2f}" text-anchor="middle" '
                    f'class="method">{html.escape(node.branch_label_ja)}</text>'
                ),
                (
                    f'<text x="{x:.2f}" y="{y + 7:.2f}" text-anchor="middle" '
                    f'class="status">値 {node.objective_value} · 上界 {bound}</text>'
                ),
                (
                    f'<text x="{x:.2f}" y="{y + 27:.2f}" text-anchor="middle" '
                    f'fill="{stroke}" font-weight="750">'
                    f"{state_labels[node.state]}</text>"
                ),
            ]
        )
    footer, height = _figure_footer(
        top + 4 * step + half_height + 32,
        "optimization_compass.search_tree.generate_search_tree_artifact"
        f" · dataset {dataset_version}",
        "Branch-and-Boundの固定教材です。cut separationやMILP solverの性能は示しません。",
    )
    body.extend(footer)
    return _figure_document(
        title,
        (
            "4変数の0-1 knapsackに対する決定論的なBranch-and-Boundを最後まで実行した探索木です。"
            "各ノードの部分割当、値、上界、枝刈りの理由を示し、最良の実行可能値15と"
            "全体の上界15が一致して差が0になる過程を表します。cut生成は含みません。"
        ),
        height,
        body,
    )


def _topology_field_svg(dataset_version: str) -> str:
    artifact = generate_topology_field_artifact(dataset_version)
    primary = next(run for run in artifact.runs if run.role == "primary")
    failure = next(run for run in artifact.runs if run.role == "failure_contrast")
    panels = (
        ("初期の密度場", primary.steps[0], False),
        ("filterあり · 反復6", primary.steps[6], False),
        ("filterあり · 反復12", primary.steps[12], False),
        ("filterなし · 反復12", failure.steps[12], True),
    )
    title = "同じ12反復でも、filterの有無で密度場が変わる"
    body, y = _figure_heading(title, "8×4要素の密度場・体積の目標 0.50・固定の教材用実行")
    cell_size = 28
    grid_width = artifact.grid.columns * cell_size
    grid_height = artifact.grid.rows * cell_size
    inner_x = FIGURE_MARGIN + 14
    metrics_x = inner_x + grid_width + 18
    metrics_right = FIGURE_WIDTH - FIGURE_MARGIN - 14
    for label, step, is_failure in panels:
        panel_y = y + 8
        accent = "#a33d30" if is_failure else "#245c42"
        grid_y = panel_y + 46
        panel_height = 46 + grid_height + 44
        body.extend(
            [
                (
                    f'<rect x="{FIGURE_MARGIN}" y="{panel_y:g}" width="{CONTENT_WIDTH}" '
                    f'height="{panel_height:g}" rx="12" fill="#fff" stroke="#cfd8d1"/>'
                ),
                (
                    f'<rect x="{FIGURE_MARGIN}" y="{panel_y + 12:g}" width="4" height="24" '
                    f'fill="{accent}"/>'
                ),
                (
                    f'<text x="{inner_x}" y="{panel_y + 30:g}" class="panel-title" '
                    f'fill="{accent}">{html.escape(label)}</text>'
                ),
            ]
        )
        for cell_index, density in enumerate(step.density):
            x = inner_x + (cell_index % artifact.grid.columns) * cell_size
            cell_y = grid_y + (cell_index // artifact.grid.columns) * cell_size
            body.append(
                f'<rect x="{x:.2f}" y="{cell_y:.2f}" width="{cell_size}" height="{cell_size}" '
                f'fill="{_density_color(density)}" stroke="#eef1ed" stroke-width="1"/>'
            )
        for row, (metric_label, value) in enumerate(
            (
                ("compliance", f"{step.compliance:.2f}"),
                ("中間密度の割合", f"{step.gray_fraction:.3f}"),
                ("市松模様の度合い", f"{step.checkerboard_score:.3f}"),
            )
        ):
            label_y = grid_y + 14 + row * 40
            body.extend(
                [
                    f'<text x="{metrics_x}" y="{label_y:g}" class="status">{metric_label}</text>',
                    (
                        f'<text x="{metrics_right}" y="{label_y + 19:g}" text-anchor="end" '
                        f'class="metric-value">{value}</text>'
                    ),
                ]
            )
        body.append(
            f'<text x="{inner_x}" y="{grid_y + grid_height + 28:g}" class="status">'
            f"反復{step.iteration} · 体積率 {step.volume_fraction:.3f}</text>"
        )
        y = panel_y + panel_height + 4
    note, y = _text_lines(
        FIGURE_MARGIN,
        y + 24,
        "濃いセルほど密度が高い。指標は密度場と同じ反復から取得しています。",
        "note",
    )
    body.extend(note)
    footer, height = _figure_footer(
        y + 4,
        "optimization_compass.learning_slices.generate_topology_field_artifact"
        f" · dataset {dataset_version}",
        "8×4の教育用referenceです。実際のFEM、強度、座屈、製造性は保証しません。",
    )
    body.extend(footer)
    return _figure_document(
        title,
        (
            "8×4要素のトポロジー最適化の教育用generatorの実行結果です。"
            "初期の密度場、filterありの中間と終端、filterなしの終端を、"
            "compliance、中間密度の割合（gray fraction）、市松模様の度合い"
            "（checkerboard score）とともに示します。"
        ),
        height,
        body,
    )


def _random_search_probe() -> dict[str, object]:
    rng = random.Random(7)
    points: list[tuple[float, float, float]] = []
    best_history: list[float] = []
    best = math.inf
    for _ in range(48):
        x, y = rng.random(), rng.random()
        value = (
            (x - 0.24) ** 2 + 0.8 * (y - 0.72) ** 2 + 0.025 * (1.0 - math.cos(6.0 * math.pi * x))
        )
        points.append((x, y, value))
        best = min(best, value)
        best_history.append(best)
    occupied = len({(min(3, int(x * 4)), min(3, int(y * 4))) for x, y, _ in points})
    best_index = min(range(len(points)), key=lambda index: points[index][2])
    return {
        "points": tuple(points),
        "best_history": tuple(best_history),
        "occupied_cells": occupied,
        "best_index": best_index,
    }


def _random_search_svg(dataset_version: str) -> str:
    probe = _random_search_probe()
    points = probe["points"]
    history = probe["best_history"]
    title = "Random Searchの48回をそのまま見る"
    body, y = _figure_heading(title, "2次元の探索空間・48試行・seed 7")
    panel, top, bottom = _panel(y + 8, "どこを試したか", 262)
    body.extend(panel)
    box_x, box_y, box_width, box_height = 64.0, top, 330.0, 220.0
    body.append(
        f'<rect x="{box_x:g}" y="{box_y:g}" width="{box_width:g}" height="{box_height:g}" '
        'fill="#f5f8f4" stroke="#c7d2ca"/>'
    )
    for index in range(1, 4):
        grid_x = box_x + index * box_width / 4
        grid_y = box_y + index * box_height / 4
        body.extend(
            [
                f'<line x1="{grid_x:g}" y1="{box_y:g}" x2="{grid_x:g}" '
                f'y2="{box_y + box_height:g}" stroke="#e1e7e2"/>',
                f'<line x1="{box_x:g}" y1="{grid_y:g}" x2="{box_x + box_width:g}" '
                f'y2="{grid_y:g}" stroke="#e1e7e2"/>',
            ]
        )
    for index, (x_value, y_value, _) in enumerate(points):
        x = box_x + box_width * x_value
        point_y = box_y + box_height - box_height * y_value
        best = index == probe["best_index"]
        body.append(
            f'<circle cx="{x:.2f}" cy="{point_y:.2f}" r="{5 if best else 3.5}" '
            f'fill="{"#dc6b3f" if best else "#3a8062"}" '
            f'opacity="{1 if best else 0.72}"/>'
        )
    body.extend(
        [
            f'<text x="{box_x:g}" y="{box_y + box_height + 20:g}" class="axis">0</text>',
            f'<text x="{box_x + box_width:g}" y="{box_y + box_height + 20:g}" '
            'text-anchor="end" class="axis">1 · x</text>',
            f'<text x="{box_x - 10:g}" y="{box_y + 12:g}" text-anchor="end" class="axis">y</text>',
        ]
    )
    panel, top, bottom = _panel(bottom + 12, "それまでの最良値はどう下がったか", 196)
    body.extend(panel)
    chart_x, chart_y, chart_width, chart_height = 64.0, top + 6, 330.0, 150.0
    body.extend(
        [
            f'<line x1="{chart_x:g}" y1="{chart_y + chart_height:g}" '
            f'x2="{chart_x + chart_width:g}" y2="{chart_y + chart_height:g}" stroke="#9caaa1"/>',
            f'<line x1="{chart_x:g}" y1="{chart_y:g}" x2="{chart_x:g}" '
            f'y2="{chart_y + chart_height:g}" stroke="#9caaa1"/>',
        ]
    )
    maximum = max(history)
    path = []
    for index, value in enumerate(history):
        x = chart_x + chart_width * index / (len(history) - 1)
        point_y = chart_y + chart_height * (maximum - value) / maximum
        path.append(f"{x:.2f},{point_y:.2f}")
    body.extend(
        [
            f'<polyline points="{" ".join(path)}" fill="none" stroke="#dc6b3f" '
            'stroke-width="3" stroke-linejoin="round"/>',
            f'<text x="{chart_x:g}" y="{chart_y + chart_height + 20:g}" class="axis">1回目</text>',
            f'<text x="{chart_x + chart_width:g}" y="{chart_y + chart_height + 20:g}" '
            'text-anchor="end" class="axis">48回目</text>',
        ]
    )
    y = bottom + 34
    right = FIGURE_WIDTH - FIGURE_MARGIN
    body.extend(
        [
            f'<text x="{FIGURE_MARGIN}" y="{y:g}" class="metric">16分割のうち訪れたセル</text>',
            f'<text x="{right}" y="{y:g}" text-anchor="end" class="metric-value">'
            f"{probe['occupied_cells']} / 16</text>",
            f'<text x="{FIGURE_MARGIN}" y="{y + 28:g}" class="metric">最終の最良目的値</text>',
            f'<text x="{right}" y="{y + 28:g}" text-anchor="end" class="metric-value">'
            f"{history[-1]:.4f}</text>",
        ]
    )
    note, y = _text_lines(
        FIGURE_MARGIN, y + 62, "点の散らばりと改善の停滞を、同じ48回の評価から読みます。", "note"
    )
    body.extend(note)
    footer, height = _figure_footer(
        y + 4,
        f"scripts/generate_article_figures.py::_random_search_probe · dataset {dataset_version}",
        "固定した2次元の目的関数と単一seedの教材です。高次元での被覆や手法の順位は示しません。",
    )
    body.extend(footer)
    return _figure_document(
        title,
        "固定seedで2次元の探索空間を48回サンプリングした点と、それまでの最良値の推移。",
        height,
        body,
    )


def _tpe_density_ratio_probe() -> dict[str, object]:
    observations = (
        (0.05, 0.62),
        (0.13, 0.44),
        (0.20, 0.26),
        (0.28, 0.12),
        (0.34, 0.08),
        (0.42, 0.11),
        (0.51, 0.23),
        (0.62, 0.39),
        (0.74, 0.55),
        (0.86, 0.72),
        (0.93, 0.82),
        (0.98, 0.91),
    )
    ranked = sorted(observations, key=lambda item: item[1])
    good = tuple(ranked[:4])
    bad = tuple(ranked[4:])
    bandwidth = 0.09

    def density(x: float, group: tuple[tuple[float, float], ...]) -> float:
        return sum(
            math.exp(-0.5 * ((x - observed_x) / bandwidth) ** 2) for observed_x, _ in group
        ) / len(group)

    grid = tuple(index / 100 for index in range(101))
    curves = tuple((x, density(x, good), density(x, bad)) for x in grid)
    candidate = max(curves, key=lambda item: item[1] / max(item[2], 1e-9))
    return {
        "observations": observations,
        "good": good,
        "bad": bad,
        "curves": curves,
        "candidate": candidate[0],
        "candidate_ratio": candidate[1] / candidate[2],
    }


def _tpe_density_ratio_svg(dataset_version: str) -> str:
    probe = _tpe_density_ratio_probe()
    curves = probe["curves"]
    maximum = max(max(good, bad) for _, good, bad in curves)
    title = "TPEは「良い群／悪い群」の差を見る"
    body, y = _figure_heading(title, "観測済み12試行・良い4件／悪い8件・固定bandwidth 0.09")
    panel, top, bottom = _panel(y + 8, "パラメータ x の密度モデル", 250)
    body.extend(panel)
    chart_x, chart_width = 44.0, 360.0
    baseline, chart_height = top + 170, 160.0

    def curve_path(offset: int) -> str:
        return " ".join(
            f"{chart_x + x * chart_width:.2f},"
            f"{baseline - chart_height * values[offset] / maximum:.2f}"
            for x, *values in curves
        )

    body.extend(
        [
            f'<line x1="{chart_x:g}" y1="{baseline:g}" x2="{chart_x + chart_width:g}" '
            f'y2="{baseline:g}" stroke="#9caaa1"/>',
            f'<line x1="{chart_x:g}" y1="{baseline - chart_height - 6:g}" x2="{chart_x:g}" '
            f'y2="{baseline:g}" stroke="#9caaa1"/>',
            f'<polyline points="{curve_path(0)}" fill="none" stroke="#28795b" stroke-width="3"/>',
            f'<polyline points="{curve_path(1)}" fill="none" stroke="#a8a39b" stroke-width="3"/>',
        ]
    )
    for x, _ in probe["good"]:
        body.append(
            f'<circle cx="{chart_x + x * chart_width:.2f}" cy="{baseline + 16:g}" r="4.5" '
            'fill="#28795b"/>'
        )
    for x, _ in probe["bad"]:
        body.append(
            f'<circle cx="{chart_x + x * chart_width:.2f}" cy="{baseline + 34:g}" r="3.5" '
            'fill="#a8a39b"/>'
        )
    candidate_x = chart_x + probe["candidate"] * chart_width
    body.extend(
        [
            f'<line x1="{candidate_x:.2f}" y1="{baseline - chart_height - 6:g}" '
            f'x2="{candidate_x:.2f}" y2="{baseline + 42:g}" '
            'stroke="#dc6b3f" stroke-width="2.5" stroke-dasharray="6 5"/>',
            f'<text x="{candidate_x + 8:.2f}" y="{baseline - chart_height + 10:g}" '
            f'class="metric-value halo" fill="#dc6b3f">次の x ≈ {probe["candidate"]:.2f}</text>',
            f'<text x="{chart_x:g}" y="{baseline + 62:g}" class="axis">0</text>',
            f'<text x="{chart_x + chart_width:g}" y="{baseline + 62:g}" text-anchor="end" '
            'class="axis">1 · パラメータ x</text>',
        ]
    )
    y = bottom + 34
    for color, label, detail in (
        ("#28795b", "良い群の密度 l(x)", "下の濃い点: 良い4件の x"),
        ("#a8a39b", "悪い群の密度 g(x)", "下の薄い点: 悪い8件の x"),
    ):
        row, y = _legend_row(y, color, label, detail=detail)
        body.extend(row)
    note, y = _text_lines(
        FIGURE_MARGIN,
        y + 6,
        "同じ履歴を、目的関数の曲面ではなくパラメータの密度の差として使います。\n"
        "緑の山が高く、灰色の山が低い場所を次の候補として優先します。",
        "note",
    )
    body.extend(note)
    footer, height = _figure_footer(
        y + 4,
        "scripts/generate_article_figures.py::_tpe_density_ratio_probe"
        f" · dataset {dataset_version}",
        "1次元のGaussian KDEによる概念図です。Optunaの内部実装や、条件付きの探索空間全体は"
        "再現しません。",
    )
    body.extend(footer)
    return _figure_document(
        title,
        "固定した12試行を良い4件と悪い8件に分け、Gaussian KDEの密度比から次の候補を選ぶ教材。",
        height,
        body,
    )


def _hyperband_rungs_probe() -> dict[str, object]:
    trials = tuple(
        tuple(
            0.30
            + 0.045 * trial
            - (0.06 + 0.008 * ((trial * 5) % 7)) * math.log1p(resource)
            + 0.018 * math.sin(trial * 1.7 + resource)
            for resource in range(1, 10)
        )
        for trial in range(12)
    )
    first = tuple(sorted(range(12), key=lambda trial: trials[trial][0])[:4])
    second = tuple(sorted(first, key=lambda trial: trials[trial][2])[:1])
    used_resource = 12 * 1 + 4 * (3 - 1) + (9 - 3)
    return {
        "trials": trials,
        "rungs": (1, 3, 9),
        "promoted_at_one": first,
        "promoted_at_three": second,
        "used_resource": used_resource,
        "full_resource": 12 * 9,
    }


def _hyperband_rungs_svg(dataset_version: str) -> str:
    probe = _hyperband_rungs_probe()
    trials = probe["trials"]
    promoted_one = set(probe["promoted_at_one"])
    promoted_three = set(probe["promoted_at_three"])
    title = "全試行を最後まで育てない"
    body, y = _figure_heading(title, "Successive Halving・12 → 4 → 1試行・資源 1 → 3 → 9")
    panel, top, bottom = _panel(y + 8, "試行ごとの指標と昇格", 300)
    body.extend(panel)
    x_positions = {1: 70, 3: 220, 9: 370}
    lowest_y, span = top + 250, 236.0
    for resource, x in x_positions.items():
        body.extend(
            [
                f'<line x1="{x}" y1="{top:g}" x2="{x}" y2="{lowest_y + 12:g}" '
                'stroke="#dfe5e0" stroke-width="2"/>',
                (
                    f'<text x="{x}" y="{lowest_y + 34:g}" text-anchor="middle" class="axis">'
                    f"資源 {resource}</text>"
                ),
            ]
        )
    all_values = [value for trial in trials for value in trial]
    low, high = min(all_values), max(all_values)

    def project_y(value: float) -> float:
        return lowest_y - span * (value - low) / (high - low)

    for trial_index, trial in enumerate(trials):
        points = [(x_positions[1], project_y(trial[0]))]
        if trial_index in promoted_one:
            points.append((x_positions[3], project_y(trial[2])))
        if trial_index in promoted_three:
            points.append((x_positions[9], project_y(trial[8])))
        color = (
            "#dc6b3f"
            if trial_index in promoted_three
            else ("#367e61" if trial_index in promoted_one else "#b8beb9")
        )
        stroke_width = "3.5" if trial_index in promoted_three else "2"
        body.append(
            f'<polyline points="{" ".join(f"{x},{y:.2f}" for x, y in points)}" '
            f'fill="none" stroke="{color}" stroke-width="{stroke_width}"/>'
        )
        for x, point_y in points:
            body.append(f'<circle cx="{x}" cy="{point_y:.2f}" r="3.5" fill="{color}"/>')
    saved = 1 - probe["used_resource"] / probe["full_resource"]
    y = bottom + 34
    right = FIGURE_WIDTH - FIGURE_MARGIN
    body.extend(
        [
            f'<text x="{FIGURE_MARGIN}" y="{y:g}" class="metric">消費した資源</text>',
            f'<text x="{right}" y="{y:g}" text-anchor="end" class="metric-value">'
            f"{probe['used_resource']} / {probe['full_resource']}</text>",
            f'<text x="{FIGURE_MARGIN}" y="{y + 22:g}" class="status">'
            "分母は全試行を資源9まで進めた場合</text>",
            f'<text x="{FIGURE_MARGIN}" y="{y + 52:g}" class="metric">'
            "この固定例で省いた資源</text>",
            f'<text x="{right}" y="{y + 52:g}" text-anchor="end" class="metric-value">'
            f"{saved:.0%}</text>",
        ]
    )
    note, y = _text_lines(
        FIGURE_MARGIN,
        y + 86,
        "灰色は資源1、緑は資源3、橙は資源9まで進んだ試行。割り当ての判断だけを描いています。",
        "note",
    )
    body.extend(note)
    footer, height = _figure_footer(
        y + 4,
        f"scripts/generate_article_figures.py::_hyperband_rungs_probe · dataset {dataset_version}",
        "固定した滑らかな学習曲線です。遅咲きの試行、ノイズ、非同期の待ちは省略しています。",
    )
    body.extend(footer)
    return _figure_document(
        "Successive Halvingの資源配分",
        "12試行を資源1で評価して4試行、さらに1試行へ絞る固定実行。",
        height,
        body,
    )


def _turbo_trust_region_probe() -> dict[str, object]:
    rng = random.Random(7)

    def objective(x: float, y: float) -> float:
        return (x - 0.72) ** 2 + 1.3 * (y - 0.28) ** 2 + 0.025 * math.sin(12 * x)

    center = [0.5, 0.5]
    length = 0.6
    best = objective(*center)
    steps = []
    failures = 0
    for iteration in range(12):
        candidate = [
            min(1.0, max(0.0, center[axis] + rng.uniform(-length / 2, length / 2)))
            for axis in range(2)
        ]
        value = objective(*candidate)
        improved = value < best
        if improved:
            center, best, failures = candidate, value, 0
            length = min(0.8, length * 1.15)
        else:
            failures += 1
            if failures == 2:
                length, failures = max(0.08, length / 2), 0
        steps.append((iteration + 1, tuple(center), length, best, improved))
    return {"steps": tuple(steps), "initial_best": objective(0.5, 0.5)}


def _turbo_trust_region_svg(dataset_version: str) -> str:
    probe = _turbo_trust_region_probe()
    steps = probe["steps"]
    selected = (0, 3, 7, 11)
    title = "探索範囲を局所boxへ絞る"
    body, y = _figure_heading(title, "TuRBO型の制御・2次元の目的関数・評価12回・seed 7")
    panel, top, bottom = _panel(y + 8, "trust regionと暫定最良点", 314)
    body.extend(panel)
    box_x, box_y, box_width, box_height = 60.0, top, 320.0, 304.0
    body.append(
        f'<rect x="{box_x:g}" y="{box_y:g}" width="{box_width:g}" height="{box_height:g}" '
        'fill="#f5f8f4" stroke="#c7d2ca"/>'
    )
    palette = ("#b7c7be", "#79a58f", "#367e61", "#dc6b3f")
    path = []
    for color_index, step_index in enumerate(selected):
        _, center, length, _, _ = steps[step_index]
        x = box_x + center[0] * box_width
        point_y = box_y + box_height - center[1] * box_height
        lower = tuple(max(0.0, value - length / 2) for value in center)
        upper = tuple(min(1.0, value + length / 2) for value in center)
        left = box_x + lower[0] * box_width
        top_edge = box_y + box_height - upper[1] * box_height
        width = (upper[0] - lower[0]) * box_width
        height = (upper[1] - lower[1]) * box_height
        body.extend(
            [
                f'<rect x="{left:.2f}" y="{top_edge:.2f}" '
                f'width="{width:.2f}" height="{height:.2f}" fill="none" '
                f'stroke="{palette[color_index]}" stroke-width="2.5"/>',
                f'<circle cx="{x:.2f}" cy="{point_y:.2f}" r="4.5" fill="{palette[color_index]}"/>',
            ]
        )
        path.append(f"{x:.2f},{point_y:.2f}")
    body.append(
        f'<polyline points="{" ".join(path)}" fill="none" stroke="#6a756e" '
        'stroke-width="2" stroke-dasharray="5 5"/>'
    )
    panel, top, bottom = _panel(bottom + 12, "12回の制御履歴", 200)
    body.extend(panel)
    chart_x, chart_y, chart_width, chart_height = 64.0, top + 6, 330.0, 150.0
    body.extend(
        [
            f'<line x1="{chart_x:g}" y1="{chart_y + chart_height:g}" '
            f'x2="{chart_x + chart_width:g}" y2="{chart_y + chart_height:g}" stroke="#9caaa1"/>',
            f'<line x1="{chart_x:g}" y1="{chart_y:g}" x2="{chart_x:g}" '
            f'y2="{chart_y + chart_height:g}" stroke="#9caaa1"/>',
        ]
    )
    max_best = probe["initial_best"]
    usable = chart_height - 12
    lengths = " ".join(
        f"{chart_x + chart_width * (index - 1) / 11:.2f},"
        f"{chart_y + chart_height - usable * length / 0.8:.2f}"
        for index, _, length, _, _ in steps
    )
    bests = " ".join(
        f"{chart_x + chart_width * (index - 1) / 11:.2f},"
        f"{chart_y + chart_height - usable * (max_best - best) / max_best:.2f}"
        for index, _, _, best, _ in steps
    )
    body.extend(
        [
            f'<polyline points="{lengths}" fill="none" stroke="#367e61" stroke-width="3"/>',
            f'<polyline points="{bests}" fill="none" stroke="#dc6b3f" stroke-width="3"/>',
            f'<text x="{chart_x:g}" y="{chart_y + chart_height + 20:g}" class="axis">1</text>',
            f'<text x="{chart_x + chart_width:g}" y="{chart_y + chart_height + 20:g}" '
            'text-anchor="end" class="axis">評価 12回目</text>',
        ]
    )
    y = bottom + 34
    for color, label, detail in (
        ("#367e61", "boxの一辺の長さ", "上の図の枠の大きさ（最大0.8で正規化）"),
        ("#dc6b3f", "最良値の改善量", "初期点からの改善（初期値で正規化）"),
    ):
        row, y = _legend_row(y, color, label, detail=detail)
        body.extend(row)
    note, y = _text_lines(
        FIGURE_MARGIN,
        y + 6,
        "改善した点へ中心を移し、2回停滞するとboxを縮めます。\n上の図の枠は薄い色ほど早い時点、"
        "橙が最後です。\nSAASBOは別の発想で、少数の有効な次元を事前分布として表します。",
        "note",
    )
    body.extend(note)
    footer, height = _figure_footer(
        y + 4,
        "scripts/generate_article_figures.py::_turbo_trust_region_probe"
        f" · dataset {dataset_version}",
        "trust regionの制御だけの教材です。GP、獲得関数、SAAS priorは実装していません。",
    )
    body.extend(footer)
    return _figure_document(
        "TuRBO型trust regionの拡大と縮小",
        "固定seedの局所box探索で、改善時の中心の移動と、停滞時のboxの縮小を示す。",
        height,
        body,
    )


# Execution figures are drawn FIGURE_WIDTH units wide with width/height attributes equal to the
# viewBox, so a PC shows them 1:1 and a 375 px phone (353 px of article width) at about 0.8.
# Text is drawn at 15-18 units: >= 12 px on the phone and <= 18 px on a PC
# (docs/teaching-article-playbook.md §5.4). Side-by-side panels are stacked instead of shrunk.
FIGURE_WIDTH = 440
FIGURE_MARGIN = 20
CONTENT_WIDTH = FIGURE_WIDTH - 2 * FIGURE_MARGIN
TEXT_SIZE = {"title": 18, "panel-title": 17, "method": 16, "metric": 16, "body": 15}
TERMINAL_STATUS_JA = {
    "completed": "完了",
    "converged": "収束",
    "budget_exhausted": "評価予算を使い切り",
    "diverged": "発散",
    "stopped": "停止",
    "failed": "失敗",
}
# Line-break opportunities, best first (see _break_level): 0 after list separators and sentence
# punctuation; 1 at spaces, "." and "/" in identifiers and Latin/Japanese changes; 2 after
# hiragana before kanji or katakana; 3 between any two Japanese characters or after "_".
_BREAK_AFTER = set("　、。，,・·")
_NO_BREAK_BEFORE = set(":;,.)）]」、。・·=≤≥<>+−-²")
_NO_BREAK_AFTER = set("(（[「=≤≥<>+−-")


def _is_wide(character: str) -> bool:
    return bool(character) and (ord(character) >= 0x2E80 or character in "○●□■△▲◇◆→←↑↓")


def _text_width(text: str, size: float) -> float:
    """Conservative width estimate for system-ui text, used only to wrap and place labels."""
    return sum(size * (1.0 if _is_wide(character) else 0.52) for character in text)


def _wrap(text: str, size: float, width: float = CONTENT_WIDTH) -> list[str]:
    """Wrap into as few lines as fit ``width`` and even out their lengths.

    Uses the best break level (see ``_BREAK_AFTER``) at which every line fits; ``\\n`` forces a
    break.
    """
    lines: list[str] = []
    for part in text.split("\n"):
        for level in (0, 1, 2, 3):
            segments = _wrap_segments(part, level)
            greedy = _pack_segments(segments, size, width)
            if all(_text_width(line, size) <= width for line in greedy):
                break
        low, high = width / max(1, len(greedy)), width
        while len(greedy) > 1 and high - low > 1:
            middle = (low + high) / 2
            if len(_pack_segments(segments, size, middle)) == len(greedy):
                high = middle
            else:
                low = middle
        lines.extend(_pack_segments(segments, size, high) if len(greedy) > 1 else greedy)
    return lines


def _break_level(character: str, rest: str) -> int:
    following = rest[:1]
    if not following or following in _NO_BREAK_BEFORE or character in _NO_BREAK_AFTER:
        return 4
    if character in _BREAK_AFTER:
        return 0
    if character == "." and rest.startswith(("py", "svg", "json")):
        return 4
    if character in " ./" or (character == ":" and following != ":"):
        return 1
    if _is_wide(character) != _is_wide(following):
        return 1
    kinds = (_kana_kind(character), _kana_kind(following))
    if kinds in {("hiragana", "kanji"), ("hiragana", "katakana"), ("kanji", "katakana")} or (
        kinds == ("katakana", "kanji")
    ):
        return 2
    if character == "_" or (_is_wide(character) and _is_wide(following)):
        return 3
    return 4


def _kana_kind(character: str) -> str:
    code = ord(character) if character else 0
    if 0x3040 <= code <= 0x309F:
        return "hiragana"
    if 0x30A0 <= code <= 0x30FF:
        return "katakana"
    if 0x4E00 <= code <= 0x9FFF or character == "々":
        return "kanji"
    return "other"


def _wrap_segments(text: str, level: int) -> list[str]:
    segments: list[str] = []
    current = ""
    for index, character in enumerate(text):
        current += character
        if _break_level(character, text[index + 1 :]) <= level:
            segments.append(current)
            current = ""
    if current:
        segments.append(current)
    return segments


def _pack_segments(segments: list[str], size: float, width: float) -> list[str]:
    lines: list[str] = []
    line = ""
    for segment in segments:
        if line and _text_width((line + segment).rstrip(), size) > width:
            lines.append(line.rstrip())
            line = segment.lstrip()
        else:
            line += segment
    if line.strip():
        lines.append(line.rstrip())
    return lines


def _text_lines(
    x: float,
    y: float,
    text: str,
    css_class: str,
    *,
    size: float = TEXT_SIZE["body"],
    width: float = CONTENT_WIDTH,
    line_height: float | None = None,
    anchor: str | None = None,
) -> tuple[list[str], float]:
    """Wrapped text whose first baseline is ``y``; returns the elements and the next baseline."""
    step = line_height if line_height is not None else round(size * 1.4)
    anchor_attribute = f' text-anchor="{anchor}"' if anchor else ""
    elements = []
    for line in _wrap(text, size, width):
        elements.append(
            f'<text x="{x:g}" y="{y:g}"{anchor_attribute} class="{css_class}">'
            f"{html.escape(line)}</text>"
        )
        y += step
    return elements, y


def _figure_heading(title: str, subtitle: str) -> tuple[list[str], float]:
    """Title and subtitle at the top of a figure; returns the elements and the next free y."""
    elements, y = _text_lines(FIGURE_MARGIN, 34, title, "title", size=TEXT_SIZE["title"])
    subtitle_elements, y = _text_lines(FIGURE_MARGIN, y, subtitle, "subtitle")
    return elements + subtitle_elements, y - 4


def _figure_footer(y: float, provenance: str, caveat: str) -> tuple[list[str], float]:
    """Provenance (``実行生成: ...``) and caveat lines; returns the elements and figure height."""
    elements, y = _text_lines(FIGURE_MARGIN, y, f"実行生成: {provenance}", "caption")
    caveat_elements, y = _text_lines(FIGURE_MARGIN, y + 4, caveat, "caveat")
    return elements + caveat_elements, y - 2


def _plot_frame(x: float, y: float, width: float, height: float, clip_id: str) -> list[str]:
    """White plot panel plus a clip path of the same shape (use ``clip-path="url(#id)"``)."""
    return [
        f'<rect x="{x:g}" y="{y:g}" width="{width:g}" height="{height:g}" rx="12" '
        'fill="#fff" stroke="#cfd8d1"/>',
        f'<clipPath id="{clip_id}"><rect x="{x:g}" y="{y:g}" width="{width:g}" '
        f'height="{height:g}" rx="12"/></clipPath>',
    ]


def _panel(y: float, title: str, content_height: float) -> tuple[list[str], float, float]:
    """Full-width white panel with a title; returns the elements, the y where content starts and
    the y just below the panel."""
    elements, content_y = _text_lines(
        FIGURE_MARGIN + 14,
        y + 28,
        title,
        "panel-title",
        size=TEXT_SIZE["panel-title"],
        width=CONTENT_WIDTH - 28,
    )
    bottom = content_y + content_height
    return (
        [
            f'<rect x="{FIGURE_MARGIN}" y="{y:g}" width="{CONTENT_WIDTH}" '
            f'height="{bottom - y:g}" rx="12" fill="#fff" stroke="#d6ddd7"/>',
            *elements,
        ],
        content_y,
        bottom,
    )


def _metric_rows(y: float, rows: tuple[tuple[str, str], ...]) -> tuple[list[str], float]:
    """Label on the left, bold value on the right, one row each; returns elements and next y."""
    right = FIGURE_WIDTH - FIGURE_MARGIN
    elements = []
    for label, value in rows:
        elements.extend(
            [
                f'<text x="{FIGURE_MARGIN}" y="{y:g}" class="metric">{html.escape(label)}</text>',
                f'<text x="{right}" y="{y:g}" text-anchor="end" class="metric-value">'
                f"{html.escape(value)}</text>",
            ]
        )
        y += 26
    return elements, y


def _legend_row(
    y: float,
    color: str,
    label: str,
    value: str = "",
    detail: str = "",
    *,
    dash: bool = False,
    marker: str = "line",
) -> tuple[list[str], float]:
    """Colored key, bold label and right-aligned value; the value drops to its own line when the
    two do not fit side by side. ``detail`` is a muted wrapped line underneath. Returns the
    elements and the next row's baseline."""
    text_x = FIGURE_MARGIN + 38
    right = FIGURE_WIDTH - FIGURE_MARGIN
    if marker == "line":
        dash_attribute = ' stroke-dasharray="8 5"' if dash else ""
        key = (
            f'<line x1="{FIGURE_MARGIN}" y1="{y - 5:g}" x2="{FIGURE_MARGIN + 28}" '
            f'y2="{y - 5:g}" stroke="{color}" stroke-width="4"{dash_attribute}/>'
        )
    else:
        key = (
            f'<rect x="{FIGURE_MARGIN + 6}" y="{y - 13:g}" width="16" height="16" rx="3" '
            f'fill="{color}"/>'
        )
    elements = [
        key,
        f'<text x="{text_x}" y="{y:g}" class="method">{html.escape(label)}</text>',
    ]
    side_by_side = (
        _text_width(label, TEXT_SIZE["method"]) + _text_width(value, TEXT_SIZE["metric"]) + 16
        <= right - text_x
    )
    next_y = y + 22
    if value:
        if side_by_side:
            elements.append(
                f'<text x="{right}" y="{y:g}" text-anchor="end" class="metric">'
                f"{html.escape(value)}</text>"
            )
        else:
            value_lines, next_y = _text_lines(
                text_x,
                next_y,
                value,
                "metric",
                size=TEXT_SIZE["metric"],
                width=right - text_x,
                line_height=21,
            )
            elements.extend(value_lines)
    if detail:
        detail_lines, next_y = _text_lines(
            text_x, next_y, detail, "status", width=right - text_x, line_height=20
        )
        elements.extend(detail_lines)
    return elements, next_y + 12


# The stylesheet's ``text{fill:...}`` outranks a presentation ``fill`` attribute, so a colored
# label must carry its color as an inline style.
_TEXT_FILL = re.compile(r'(<text\b[^>]*?) fill="(#[0-9a-fA-F]{3,6})"')


def _figure_document(title: str, description: str, height: float, body: list[str]) -> str:
    height = math.ceil(height)
    body = [_TEXT_FILL.sub(r'\1 style="fill:\2"', part) for part in body]
    return "".join(
        [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {FIGURE_WIDTH} {height}" '
            f'width="{FIGURE_WIDTH}" height="{height}" '
            'role="img" aria-labelledby="figure-title figure-description">'
            f'<title id="figure-title">{html.escape(title)}</title>'
            f'<desc id="figure-description">{html.escape(description)}</desc>',
            f'<rect width="{FIGURE_WIDTH}" height="{height}" rx="16" fill="#f7f6f1"/>',
            *body,
            _figure_style(),
            "</svg>\n",
        ]
    )


def _figure_style() -> str:
    return (
        "<style>"
        "text{font-family:system-ui,-apple-system,'Segoe UI',sans-serif;fill:#26352d;"
        f"font-size:{TEXT_SIZE['body']}px}}"
        f".title{{font-size:{TEXT_SIZE['title']}px;font-weight:750}}"
        ".subtitle{fill:#617068}"
        f".panel-title{{font-size:{TEXT_SIZE['panel-title']}px;font-weight:750}}"
        f".method{{font-size:{TEXT_SIZE['method']}px;font-weight:750}}"
        f".metric,.metric-value{{font-size:{TEXT_SIZE['metric']}px;"
        "font-variant-numeric:tabular-nums}"
        ".metric-value{font-weight:750}"
        ".status,.axis,.note{fill:#617068}"
        ".caption{fill:#46554d}"
        ".caveat{fill:#7a4b38}"
        ".halo{paint-order:stroke;stroke:#fff;stroke-width:4px;stroke-linejoin:round}"
        "</style>"
    )


def _objective_value(frame: TraceFrame) -> float:
    return _metric_value(frame, "objective")


def _metric_value(frame: TraceFrame, metric_id: str) -> float:
    return next(float(metric.value) for metric in frame.metrics if metric.metric_id == metric_id)


def _metric(value: float) -> str:
    if value == 0:
        return "0"
    if abs(value) < 0.001 or abs(value) >= 10_000:
        return f"{value:.2e}"
    return f"{value:.4g}"


def _density_color(value: float) -> str:
    low = (243, 242, 236)
    high = (36, 92, 66)
    ratio = min(1.0, max(0.0, value))
    red, green, blue = (
        round(low[index] + (high[index] - low[index]) * ratio) for index in range(3)
    )
    return f"#{red:02x}{green:02x}{blue:02x}"


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Generate deterministic executable-result figures embedded in learning articles."
        )
    )
    parser.add_argument("--check", action="store_true", help="Fail when tracked figures are stale.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    dataset_version = read_dataset_version()
    figures = generate_article_figures(dataset_version)
    stale: list[str] = []
    for name, payload in figures.items():
        destination = args.output / name
        if args.check:
            if not destination.is_file() or destination.read_bytes() != payload:
                stale.append(str(destination.relative_to(ROOT)))
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(payload)
    if stale:
        raise SystemExit("stale article figures: " + ", ".join(stale))
    if not args.check:
        print(f"generated {len(figures)} article figures for dataset {dataset_version}")


if __name__ == "__main__":
    main()
