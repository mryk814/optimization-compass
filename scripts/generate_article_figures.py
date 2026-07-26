from __future__ import annotations

import argparse
import heapq
import html
import math
import random
from pathlib import Path

from optimization_compass.constraint_geometry import generate_so3_traces
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
from optimization_compass.site_export import _generate_optimal_control_traces
from optimization_compass.surrogate_uncertainty import generate_surrogate_scenario
from optimization_compass.trace_models import AlgorithmTrace, TraceFrame
from optimization_compass.traces import generate_gradient_bundle

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
        "optimal-control-mesh-execution.svg": _optimal_control_mesh_svg(dataset_version).encode(
            "utf-8"
        ),
        "pareto-preference-execution.svg": _pareto_preference_svg(dataset_version).encode("utf-8"),
        "pbt-lineage-execution.svg": _pbt_lineage_svg(dataset_version).encode("utf-8"),
        "pdlp-residual-execution.svg": _pdlp_residual_svg(dataset_version).encode("utf-8"),
        "portfolio-risk-execution.svg": _portfolio_risk_svg(dataset_version).encode("utf-8"),
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
        "trf-probe-execution.svg": _trf_probe_svg(dataset_version).encode("utf-8"),
    }


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

    width, height = 640, 1080
    plot_left, plot_right = 82.0, 592.0
    plot_top, plot_bottom = 198.0, 612.0
    x_min, x_max = -0.15, 2.2
    y_min, y_max = -0.15, 2.15

    def screen(point: tuple[float, float]) -> tuple[float, float]:
        x1, x2 = point
        x = plot_left + (x1 - x_min) / (x_max - x_min) * (plot_right - plot_left)
        y = plot_bottom - (x2 - y_min) / (y_max - y_min) * (plot_bottom - plot_top)
        return x, y

    elements = [
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}" role="img" '
            'aria-labelledby="figure-title figure-description">'
        ),
        '<title id="figure-title">active-set QPで制約を外し、加える固定実行</title>',
        (
            '<desc id="figure-description">2変数の凸二次計画をfeasibleな原点から解く。'
            "原点では負のmultiplierを持つx1下限制約を外し、x2下限のface上を進む。"
            "x1上限制約を加え、同じ点でx2下限制約を外した後、"
            "斜めの制約へ進んで最適点に到達する。</desc>"
        ),
        '<rect width="640" height="1080" rx="24" fill="#fbfaf5"/>',
        (
            f'<defs><clipPath id="asq-plot"><rect x="{plot_left}" y="{plot_top}" '
            f'width="{plot_right - plot_left}" height="{plot_bottom - plot_top}"/>'
            "</clipPath></defs>"
        ),
        '<text x="32" y="48" class="asq-title">止まったら外す。動いたら加える。</text>',
        (
            '<text x="32" y="80" class="asq-subtitle">'
            "fixed convex QP · feasible start · deterministic working-set updates</text>"
        ),
        '<line x1="36" y1="116" x2="68" y2="116" stroke="#d67835" stroke-width="5"/>',
        '<text x="78" y="122" class="asq-legend">iterate path</text>',
        '<line x1="238" y1="116" x2="270" y2="116" stroke="#2c7564" stroke-width="6"/>',
        '<text x="280" y="122" class="asq-legend">final active constraints</text>',
        '<rect x="24" y="150" width="592" height="512" rx="18" fill="#ffffff" stroke="#cad8d2"/>',
        '<text x="44" y="184" class="asq-panel">feasible regionとiterate</text>',
    ]

    for tick in (0.0, 0.5, 1.0, 1.5, 2.0):
        x, _ = screen((tick, 0.0))
        _, y = screen((0.0, tick))
        elements.extend(
            [
                (
                    f'<line x1="{x:.2f}" y1="{plot_top}" x2="{x:.2f}" y2="{plot_bottom}" '
                    'stroke="#edf0ec" stroke-width="1"/>'
                ),
                (
                    f'<text x="{x:.2f}" y="638" text-anchor="middle" '
                    f'class="asq-axis">{tick:g}</text>'
                ),
                (
                    f'<line x1="{plot_left}" y1="{y:.2f}" x2="{plot_right}" y2="{y:.2f}" '
                    'stroke="#edf0ec" stroke-width="1"/>'
                ),
                (
                    f'<text x="68" y="{y + 5:.2f}" text-anchor="end" '
                    f'class="asq-axis">{tick:g}</text>'
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
    elements.append(
        f'<polygon points="{feasible_points}" fill="#dceee7" stroke="#45656a" stroke-width="2"/>'
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
        elements.append(
            f'<polyline points="{contour}" fill="none" stroke="#b9c7c2" '
            'stroke-width="1.5" stroke-dasharray="5 5" clip-path="url(#asq-plot)"/>'
        )

    final_active_segments = (
        ((1.5, 0.0), (1.5, 0.5)),
        ((0.0, 2.0), (1.5, 0.5)),
    )
    for start, end in final_active_segments:
        x1, y1 = screen(start)
        x2, y2 = screen(end)
        elements.append(
            f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" '
            'stroke="#2c7564" stroke-width="7" stroke-linecap="round"/>'
        )

    path_points = ((0.0, 0.0), (1.5, 0.0), (1.5, 0.5))
    path = " ".join(f"{x:.2f},{y:.2f}" for x, y in map(screen, path_points))
    elements.append(
        f'<polyline points="{path}" fill="none" stroke="#d67835" stroke-width="5" '
        'stroke-linecap="round" stroke-linejoin="round"/>'
    )
    point_labels = (
        ((0.0, 0.0), "A", "remove x₁ ≥ 0", -42.0),
        ((1.5, 0.0), "B", "add x₁ ≤ 1.5 / remove x₂ ≥ 0", 28.0),
        ((1.5, 0.5), "C", "add x₁ + x₂ ≤ 2", 28.0),
    )
    for point, marker, label, label_offset_y in point_labels:
        x, y = screen(point)
        label_anchor = "end" if marker != "A" else "start"
        label_x = x - 12 if marker != "A" else x + 12
        elements.extend(
            [
                (
                    f'<circle cx="{x:.2f}" cy="{y:.2f}" r="9" fill="#d67835" '
                    'stroke="#fff" stroke-width="3"/>'
                ),
                (
                    f'<text x="{x:.2f}" y="{y - 16:.2f}" text-anchor="middle" '
                    f'class="asq-marker">{marker}</text>'
                ),
                (
                    f'<text x="{label_x:.2f}" y="{y + label_offset_y:.2f}" '
                    f'text-anchor="{label_anchor}" '
                    f'class="asq-label">{html.escape(label)}</text>'
                ),
            ]
        )

    elements.extend(
        [
            '<text x="586" y="638" text-anchor="end" class="asq-axis">x₁</text>',
            '<text x="84" y="212" class="asq-axis">x₂</text>',
            (
                '<rect x="24" y="682" width="592" height="268" rx="18" '
                'fill="#ffffff" stroke="#cad8d2"/>'
            ),
            '<text x="44" y="718" class="asq-panel">working set event</text>',
        ]
    )

    constraint_labels = tuple(str(row[0]) for row in constraints)
    action_labels = {
        "remove": "remove",
        "add": "add",
        "step": "step",
        "optimal": "optimal",
    }
    action_colors = {
        "remove": "#102a2e",
        "add": "#d67835",
        "step": "#45656a",
        "optimal": "#2c7564",
    }
    for row_index, event in enumerate(events):
        action = str(event["action"])
        constraint_index = event["constraint_index"]
        point = event["point"]
        if not isinstance(point, tuple):
            raise TypeError("active-set QP event point must be a tuple")
        y = 758.0 + row_index * 40.0
        if constraint_index is None:
            detail = "KKT signs satisfied"
        else:
            constraint_label = constraint_labels[int(constraint_index)]
            if action == "remove":
                detail = f"{constraint_label} · λ={float(event['value']):.2f}"
            else:
                detail = f"{constraint_label} · α={float(event['value']):.2f}"
        elements.extend(
            [
                f'<circle cx="52" cy="{y - 5:.2f}" r="7" fill="{action_colors[action]}"/>',
                (
                    f'<text x="72" y="{y:.2f}" class="asq-action">'
                    f"{event['iteration']} · {action_labels[action]}</text>"
                ),
                f'<text x="210" y="{y:.2f}" class="asq-detail">{html.escape(detail)}</text>',
            ]
        )

    elements.extend(
        [
            (
                '<text x="32" y="988" class="asq-metric">'
                f"objective {float(probe['initial_objective']):.3f} → "
                f"{float(probe['final_objective']):.3f}</text>"
            ),
            '<text x="344" y="988" text-anchor="middle" class="asq-metric">add 2 · remove 2</text>',
            (
                '<text x="608" y="988" text-anchor="end" class="asq-metric">'
                f"max violation {max(0.0, float(probe['max_residual'])):.1f}</text>"
            ),
            (
                '<text x="32" y="1028" class="asq-meta">'
                "実行生成: scripts.generate_article_figures._active_set_qp_probe "
                f"· dataset {html.escape(dataset_version)}</text>"
            ),
            (
                '<text x="32" y="1056" class="asq-note">'
                "固定2変数convex QPです。degeneracy、cycling、factorization cost、"
                "solver一般の性能は示しません。</text>"
            ),
            """
<style>
  .asq-title { font: 700 24px system-ui, sans-serif; fill: #102a2e; }
  .asq-subtitle { font: 400 17px system-ui, sans-serif; fill: #45656a; }
  .asq-panel { font: 700 21px system-ui, sans-serif; fill: #102a2e; }
  .asq-legend { font: 400 17px system-ui, sans-serif; fill: #45656a; }
  .asq-axis { font: 400 16px system-ui, sans-serif; fill: #45656a; }
  .asq-marker { font: 700 16px system-ui, sans-serif; fill: #102a2e; }
  .asq-label { font: 600 15px system-ui, sans-serif; fill: #8b4c3d; }
  .asq-action { font: 700 18px system-ui, sans-serif; fill: #102a2e; }
  .asq-detail { font: 400 17px system-ui, sans-serif; fill: #45656a; }
  .asq-metric { font: 700 18px system-ui, sans-serif; fill: #102a2e; }
  .asq-meta { font: 400 13px system-ui, sans-serif; fill: #45656a; }
  .asq-note { font: 400 13px system-ui, sans-serif; fill: #8b4c3d; }
</style>
""",
            "</svg>\n",
        ]
    )
    return "".join(elements)


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

    width, height = 640, 1080
    plot_left, plot_right = 72.0, 592.0
    control_top, control_bottom = 214.0, 452.0
    state_top, state_bottom = 590.0, 828.0
    horizon = int(probe["horizon"])

    def time_x(index: int) -> float:
        return plot_left + index / horizon * (plot_right - plot_left)

    def control_y(value: float) -> float:
        return control_bottom - value / 1.05 * (control_bottom - control_top)

    def state_y(value: float) -> float:
        return state_bottom - value / 1.05 * (state_bottom - state_top)

    elements = [
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}" role="img" '
            'aria-labelledby="figure-title figure-description">'
        ),
        '<title id="figure-title">Direct Shootingのcontrol列とrollout結果</title>',
        (
            '<desc id="figure-description">20個のcontrolをprojected gradientで更新する'
            "固定Direct Shooting教材。上段では後半のcontrolが上限1へ達する。"
            "下段ではそのcontrol列を前進simulationしたstateが0から0.950へ進む。"
            "初期control列ではstateは0のままである。</desc>"
        ),
        '<rect width="640" height="1080" rx="24" fill="#fbfaf5"/>',
        '<text x="32" y="48" class="dsh-title">control列を変えると、trajectoryが決まる</text>',
        (
            '<text x="32" y="80" class="dsh-subtitle">'
            "fixed damped dynamics · 20 controls · 80 projected-gradient updates</text>"
        ),
        '<line x1="36" y1="116" x2="68" y2="116" stroke="#aebbb6" stroke-width="4"/>',
        '<text x="78" y="122" class="dsh-legend">initial</text>',
        '<line x1="190" y1="116" x2="222" y2="116" stroke="#d67835" stroke-width="5"/>',
        '<text x="232" y="122" class="dsh-legend">optimized control</text>',
        '<line x1="438" y1="116" x2="470" y2="116" stroke="#2c7564" stroke-width="5"/>',
        '<text x="480" y="122" class="dsh-legend">rollout state</text>',
        '<defs><marker id="dsh-arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" '
        'orient="auto"><path d="M0,0 L8,4 L0,8 Z" fill="#d67835"/></marker></defs>',
        '<rect x="24" y="150" width="592" height="338" rx="18" fill="#fff" stroke="#cad8d2"/>',
        '<text x="44" y="188" class="dsh-panel">decision variable: control sequence</text>',
        '<text x="590" y="188" text-anchor="end" class="dsh-status">−1 ≤ uₜ ≤ 1</text>',
    ]

    for value in (0.0, 0.5, 1.0):
        y = control_y(value)
        elements.extend(
            [
                (
                    f'<line x1="{plot_left}" y1="{y:.2f}" x2="{plot_right}" y2="{y:.2f}" '
                    'stroke="#e4e9e5" stroke-width="1"/>'
                ),
                (
                    f'<text x="60" y="{y + 5:.2f}" text-anchor="end" '
                    f'class="dsh-axis">{value:g}</text>'
                ),
            ]
        )

    bar_step = (plot_right - plot_left) / horizon
    bar_width = bar_step * 0.62
    baseline_y = control_y(0.0)
    for index, value in enumerate(optimized_controls):
        x = time_x(index) + (bar_step - bar_width) / 2
        y = control_y(float(value))
        elements.append(
            f'<rect x="{x:.2f}" y="{y:.2f}" width="{bar_width:.2f}" '
            f'height="{baseline_y - y:.2f}" rx="3" fill="#d67835"/>'
        )
    elements.append(
        f'<line x1="{plot_left}" y1="{baseline_y:.2f}" x2="{plot_right}" '
        f'y2="{baseline_y:.2f}" stroke="#aebbb6" stroke-width="4"/>'
    )
    for tick in (0, 5, 10, 15, 20):
        x = time_x(tick)
        elements.append(
            f'<text x="{x:.2f}" y="476" text-anchor="middle" class="dsh-axis">{tick}</text>'
        )
    elements.extend(
        [
            '<line x1="320" y1="498" x2="320" y2="536" stroke="#d67835" '
            'stroke-width="4" marker-end="url(#dsh-arrow)"/>',
            '<text x="336" y="522" class="dsh-flow">forward simulation</text>',
            '<rect x="24" y="548" width="592" height="338" rx="18" fill="#fff" stroke="#cad8d2"/>',
            '<text x="44" y="586" class="dsh-panel">rollout result: state trajectory</text>',
        ]
    )

    for value in (0.0, 0.5, 1.0):
        y = state_y(value)
        elements.extend(
            [
                (
                    f'<line x1="{plot_left}" y1="{y:.2f}" x2="{plot_right}" y2="{y:.2f}" '
                    'stroke="#e4e9e5" stroke-width="1"/>'
                ),
                (
                    f'<text x="60" y="{y + 5:.2f}" text-anchor="end" '
                    f'class="dsh-axis">{value:g}</text>'
                ),
            ]
        )

    target_y = state_y(float(probe["target"]))
    elements.extend(
        [
            (
                f'<line x1="{plot_left}" y1="{target_y:.2f}" x2="{plot_right}" '
                f'y2="{target_y:.2f}" stroke="#102a2e" stroke-width="2" '
                'stroke-dasharray="7 6"/>'
            ),
            (
                f'<text x="586" y="{target_y - 9:.2f}" text-anchor="end" '
                'class="dsh-target">target = 1</text>'
            ),
        ]
    )
    initial_path = " ".join(
        f"{time_x(index):.2f},{state_y(float(value)):.2f}"
        for index, value in enumerate(initial_states)
    )
    optimized_path = " ".join(
        f"{time_x(index):.2f},{state_y(float(value)):.2f}"
        for index, value in enumerate(optimized_states)
    )
    elements.extend(
        [
            (
                f'<polyline points="{initial_path}" fill="none" stroke="#aebbb6" '
                'stroke-width="4" stroke-dasharray="7 6"/>'
            ),
            (
                f'<polyline points="{optimized_path}" fill="none" stroke="#2c7564" '
                'stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>'
            ),
        ]
    )
    final_x = time_x(horizon)
    final_y = state_y(float(optimized_states[-1]))
    elements.extend(
        [
            f'<circle cx="{final_x:.2f}" cy="{final_y:.2f}" r="8" fill="#2c7564" '
            'stroke="#fff" stroke-width="3"/>',
            (
                f'<text x="{final_x - 12:.2f}" y="{final_y + 26:.2f}" text-anchor="end" '
                f'class="dsh-final">x₂₀ = {float(optimized_states[-1]):.3f}</text>'
            ),
        ]
    )
    for tick in (0, 5, 10, 15, 20):
        x = time_x(tick)
        elements.append(
            f'<text x="{x:.2f}" y="872" text-anchor="middle" class="dsh-axis">{tick}</text>'
        )

    elements.extend(
        [
            '<text x="32" y="928" class="dsh-metric-label">objective</text>',
            (
                '<text x="32" y="956" class="dsh-metric">'
                f"{float(probe['initial_objective']):.3f} → "
                f"{float(probe['final_objective']):.4f}</text>"
            ),
            '<text x="252" y="928" class="dsh-metric-label">terminal error</text>',
            (
                '<text x="252" y="956" class="dsh-metric">'
                f"{float(probe['terminal_error']):.4f}</text>"
            ),
            '<text x="446" y="928" class="dsh-metric-label">upper bound</text>',
            (
                '<text x="446" y="956" class="dsh-metric">'
                f"{int(probe['saturated_controls'])} / 20 controls</text>"
            ),
            (
                '<text x="32" y="992" class="dsh-meta">'
                "実行生成: scripts.generate_article_figures._direct_shooting_probe "
                f"· dataset {html.escape(dataset_version)}</text>"
            ),
            (
                '<text x="32" y="1024" class="dsh-note">'
                "固定1-state教材です。hard terminal constraintとpath constraintは"
                "示しません。</text>"
            ),
            (
                '<text x="32" y="1052" class="dsh-note">'
                "unstable dynamics、model mismatch、solver一般の性能も"
                "示しません。</text>"
            ),
            """
<style>
  .dsh-title { font: 700 24px system-ui, sans-serif; fill: #102a2e; }
  .dsh-subtitle { font: 400 17px system-ui, sans-serif; fill: #45656a; }
  .dsh-panel { font: 700 21px system-ui, sans-serif; fill: #102a2e; }
  .dsh-legend, .dsh-status { font: 400 16px system-ui, sans-serif; fill: #45656a; }
  .dsh-axis { font: 400 16px system-ui, sans-serif; fill: #45656a; }
  .dsh-flow { font: 700 15px system-ui, sans-serif; fill: #8b4c3d; }
  .dsh-target { font: 700 15px system-ui, sans-serif; fill: #102a2e; }
  .dsh-final { font: 700 16px system-ui, sans-serif; fill: #2c7564; }
  .dsh-metric-label { font: 400 14px system-ui, sans-serif; fill: #45656a; }
  .dsh-metric { font: 700 19px system-ui, sans-serif; fill: #102a2e; }
  .dsh-meta { font: 400 13px system-ui, sans-serif; fill: #45656a; }
  .dsh-note { font: 400 13px system-ui, sans-serif; fill: #8b4c3d; }
</style>
""",
            "</svg>\n",
        ]
    )
    return "".join(elements)


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

    width, height = 640, 1080
    plot_left, plot_right = 82.0, 592.0
    plot_top, plot_bottom = 632.0, 864.0
    log_floor = -8.0

    def iteration_x(iteration: int) -> float:
        return plot_left + iteration / 100.0 * (plot_right - plot_left)

    def residual_y(value: float) -> float:
        exponent = max(log_floor, min(0.0, math.log10(max(value, 10.0**log_floor))))
        return plot_top + (0.0 - exponent) / -log_floor * (plot_bottom - plot_top)

    elements = [
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}" role="img" '
            'aria-labelledby="figure-title figure-description">'
        ),
        '<title id="figure-title">PDHG反復で変数と三つの判定量が変わる様子</title>',
        (
            '<desc id="figure-description">三変数simplex線形計画を100回更新した固定教材。'
            "上段では初期に均等だった質量が最小costのx2へ移る。"
            "下段ではprimal residual、dual residual、primalとdualの目的値差を同時に示す。"
            "dual residualだけは初期にもゼロであり、一つの量だけでは停止できない。</desc>"
        ),
        '<rect width="640" height="1080" rx="24" fill="#fbfaf5"/>',
        '<text x="32" y="48" class="pdlp-title">一つの残差では、収束を判定できない</text>',
        (
            '<text x="32" y="80" class="pdlp-subtitle">'
            "fixed 3-variable LP · matrix-vector updates · 100 iterations</text>"
        ),
        '<rect x="24" y="112" width="592" height="406" rx="18" fill="#fff" stroke="#cad8d2"/>',
        '<text x="44" y="152" class="pdlp-panel">primal variable · target sum = 1</text>',
        '<rect x="44" y="174" width="18" height="18" rx="4" fill="#d67835"/>',
        '<text x="72" y="189" class="pdlp-legend">x₁ · cost 3</text>',
        '<rect x="210" y="174" width="18" height="18" rx="4" fill="#2c7564"/>',
        '<text x="238" y="189" class="pdlp-legend">x₂ · cost 1</text>',
        '<rect x="376" y="174" width="18" height="18" rx="4" fill="#8ba7a0"/>',
        '<text x="404" y="189" class="pdlp-legend">x₃ · cost 2</text>',
    ]

    colors = ("#d67835", "#2c7564", "#8ba7a0")
    for row_index, snapshot in enumerate(snapshots):
        if not isinstance(snapshot, dict):
            raise TypeError("PDLP teaching snapshot must be a dictionary")
        primal = snapshot["primal"]
        if not isinstance(primal, tuple):
            raise TypeError("PDLP teaching primal vector must be a tuple")
        y = 218.0 + row_index * 68.0
        elements.extend(
            [
                (
                    f'<text x="44" y="{y + 22:.2f}" class="pdlp-step">'
                    f"k = {int(snapshot['iteration'])}</text>"
                ),
                (f'<rect x="126" y="{y:.2f}" width="360" height="34" rx="8" fill="#edf2ef"/>'),
                (
                    f'<line x1="414" y1="{y - 4:.2f}" x2="414" y2="{y + 38:.2f}" '
                    'stroke="#102a2e" stroke-width="2" stroke-dasharray="4 4"/>'
                ),
            ]
        )
        cursor = 126.0
        for value, color in zip(primal, colors, strict=True):
            segment_width = 288.0 * max(0.0, float(value))
            if segment_width > 0.0:
                elements.append(
                    f'<rect x="{cursor:.2f}" y="{y:.2f}" width="{segment_width:.2f}" '
                    f'height="34" fill="{color}"/>'
                )
            cursor += segment_width
        elements.append(
            f'<text x="584" y="{y + 22:.2f}" text-anchor="end" class="pdlp-value">'
            f"cᵀx = {float(snapshot['primal_objective']):.3f}</text>"
        )

    elements.extend(
        [
            '<text x="44" y="494" class="pdlp-note">最小costの x₂ へ質量が集まる</text>',
            '<rect x="24" y="542" width="592" height="376" rx="18" fill="#fff" stroke="#cad8d2"/>',
            '<text x="44" y="582" class="pdlp-panel">three stopping quantities</text>',
        ]
    )

    for exponent in (0, -2, -4, -6, -8):
        y = residual_y(10.0**exponent)
        elements.extend(
            [
                (
                    f'<line x1="{plot_left}" y1="{y:.2f}" x2="{plot_right}" y2="{y:.2f}" '
                    'stroke="#e4e9e5" stroke-width="1"/>'
                ),
                (
                    f'<text x="68" y="{y + 5:.2f}" text-anchor="end" '
                    f'class="pdlp-axis">10^{exponent}</text>'
                ),
            ]
        )
    for iteration in (0, 20, 40, 60, 80, 100):
        x = iteration_x(iteration)
        elements.append(
            f'<text x="{x:.2f}" y="892" text-anchor="middle" class="pdlp-axis">{iteration}</text>'
        )

    series = (
        ("primal residual", "primal_residual", "#2c7564", ""),
        ("dual residual", "dual_residual", "#d67835", "7 5"),
        ("|cᵀx − bᵀy|", "objective_difference", "#102a2e", "3 5"),
    )
    for _, key, color, dash in series:
        points = " ".join(
            f"{iteration_x(int(item['iteration'])):.2f},{residual_y(float(item[key])):.2f}"
            for item in history
            if isinstance(item, dict)
        )
        dash_attribute = f' stroke-dasharray="{dash}"' if dash else ""
        elements.append(
            f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="4" '
            f'stroke-linecap="round" stroke-linejoin="round"{dash_attribute}/>'
        )
    legend_items = (
        (44, "primal residual", "#2c7564", ""),
        (232, "dual residual", "#d67835", "7 5"),
        (410, "|objective diff|", "#102a2e", "3 5"),
    )
    for x, label, color, dash in legend_items:
        dash_attribute = f' stroke-dasharray="{dash}"' if dash else ""
        elements.extend(
            [
                (
                    f'<line x1="{x}" y1="606" x2="{x + 28}" y2="606" '
                    f'stroke="{color}" stroke-width="4"{dash_attribute}/>'
                ),
                f'<text x="{x + 36}" y="612" class="pdlp-legend">{label}</text>',
            ]
        )
    final_primal = probe["final_primal"]
    if not isinstance(final_primal, tuple):
        raise TypeError("PDLP teaching final primal vector must be a tuple")
    elements.extend(
        [
            '<circle cx="82" cy="864" r="7" fill="#d67835" stroke="#fff" stroke-width="2"/>',
            '<text x="96" y="850" class="pdlp-callout">feasibility residuals = 0 at k = 0</text>',
            '<text x="96" y="874" class="pdlp-callout">but |objective diff| = 2</text>',
            '<text x="32" y="956" class="pdlp-metric-label">solution</text>',
            (
                '<text x="32" y="984" class="pdlp-metric">'
                f"x = ({', '.join(f'{float(value):.3f}' for value in final_primal)})"
                "</text>"
            ),
            '<text x="352" y="956" class="pdlp-metric-label">objective</text>',
            '<text x="352" y="984" class="pdlp-metric">2.000 → 1.000</text>',
            (
                '<text x="32" y="1024" class="pdlp-meta">'
                "実行生成: scripts.generate_article_figures._pdlp_probe "
                f"· dataset {html.escape(dataset_version)}</text>"
            ),
            (
                '<text x="32" y="1048" class="pdlp-limit">'
                "図のobjective differenceはraw absolute differenceです。infeasible iterateでは"
                "</text>"
            ),
            (
                '<text x="32" y="1070" class="pdlp-limit">'
                "dual bound／certificateを意味しません。scaling、restart、solver性能も"
                "示しません。</text>"
            ),
            """
<style>
  .pdlp-title { font: 700 24px system-ui, sans-serif; fill: #102a2e; }
  .pdlp-subtitle { font: 400 17px system-ui, sans-serif; fill: #45656a; }
  .pdlp-panel { font: 700 21px system-ui, sans-serif; fill: #102a2e; }
  .pdlp-legend { font: 400 15px system-ui, sans-serif; fill: #45656a; }
  .pdlp-step { font: 700 17px system-ui, sans-serif; fill: #102a2e; }
  .pdlp-value { font: 700 14px system-ui, sans-serif; fill: #102a2e; }
  .pdlp-note { font: 700 16px system-ui, sans-serif; fill: #2c7564; }
  .pdlp-axis { font: 400 14px system-ui, sans-serif; fill: #45656a; }
  .pdlp-callout { font: 700 14px system-ui, sans-serif; fill: #8b4c3d; }
  .pdlp-metric-label { font: 400 14px system-ui, sans-serif; fill: #45656a; }
  .pdlp-metric { font: 700 19px system-ui, sans-serif; fill: #102a2e; }
  .pdlp-meta { font: 400 13px system-ui, sans-serif; fill: #45656a; }
  .pdlp-limit { font: 400 13px system-ui, sans-serif; fill: #8b4c3d; }
</style>
""",
            "</svg>\n",
        ]
    )
    return "".join(elements)


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

    width, height = 640, 1080
    selected_indices = set(selected)
    item_card_width = 132.0
    item_gap = 10.0
    item_left = 36.0
    grid_cell_width = 50.0
    grid_cell_height = 50.0
    grid_left = 142.0
    grid_top = 340.0
    maximum_value = int(probe["optimal_value"])

    elements = [
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}" role="img" '
            'aria-labelledby="figure-title figure-description">'
        ),
        '<title id="figure-title">0/1 knapsackのDP tableとbacktracking実行結果</title>',
        (
            '<desc id="figure-description">capacity 8の0/1 knapsackに4 itemを順に追加し、'
            "5行9列のDP tableを埋める固定実行。最終value 13からbacktrackingすると、"
            "weight 4・value 8のitem Aとweight 3・value 5のitem Bを選び、"
            "合計weight 7、unused capacity 1となる。</desc>"
        ),
        '<rect width="640" height="1080" rx="24" fill="#fbfaf5"/>',
        '<text x="32" y="48" class="dp-title">小さな部分問題を再利用し、最後に選択を戻す</text>',
        (
            '<text x="32" y="80" class="dp-subtitle">'
            "0/1 knapsack · 4 items · capacity 8 · exact integer table</text>"
        ),
        '<text x="36" y="112" class="dp-section">items</text>',
    ]
    for index, (name, weight, value) in enumerate(items):
        x = item_left + index * (item_card_width + item_gap)
        chosen = index in selected_indices
        fill = "#e3f0ea" if chosen else "#fff"
        stroke = "#2c7564" if chosen else "#cad8d2"
        badge = "selected" if chosen else "available"
        elements.extend(
            [
                f'<rect x="{x:.2f}" y="126" width="{item_card_width:.2f}" height="86" '
                f'rx="14" fill="{fill}" stroke="{stroke}" stroke-width="2"/>',
                f'<text x="{x + 14:.2f}" y="156" class="dp-item">{name}</text>',
                (
                    f'<text x="{x + 14:.2f}" y="180" class="dp-item-detail">'
                    f"weight {weight} · value {value}</text>"
                ),
                (
                    f'<text x="{x + item_card_width - 12:.2f}" y="202" text-anchor="end" '
                    f'class="dp-item-status">{badge}</text>'
                ),
            ]
        )

    elements.extend(
        [
            '<rect x="24" y="238" width="592" height="452" rx="18" fill="#fff" stroke="#cad8d2"/>',
            (
                '<text x="44" y="276" class="dp-panel">'
                "best value by items considered × capacity</text>"
            ),
            '<rect x="44" y="298" width="18" height="18" rx="3" fill="#f2c8a3"/>',
            '<text x="72" y="312" class="dp-legend">larger value</text>',
            ('<line x1="214" y1="307" x2="240" y2="307" stroke="#2c7564" stroke-width="4"/>'),
            '<text x="250" y="312" class="dp-legend">backtrack</text>',
            '<text x="126" y="330" text-anchor="end" class="dp-axis">items</text>',
        ]
    )
    for capacity in range(int(probe["capacity"]) + 1):
        center_x = grid_left + capacity * grid_cell_width + grid_cell_width / 2
        elements.append(
            f'<text x="{center_x:.2f}" y="330" text-anchor="middle" '
            f'class="dp-axis">{capacity}</text>'
        )
    row_labels = ("none", "A", "A+B", "A..C", "A..D")
    for row_index, row in enumerate(table):
        center_y = grid_top + row_index * grid_cell_height + grid_cell_height / 2
        elements.append(
            f'<text x="126" y="{center_y + 5:.2f}" text-anchor="end" '
            f'class="dp-axis">{row_labels[row_index]}</text>'
        )
        for capacity, value in enumerate(row):
            x = grid_left + capacity * grid_cell_width
            y = grid_top + row_index * grid_cell_height
            intensity = int(value) / maximum_value if maximum_value else 0.0
            fill = "#fff" if value == 0 else ("#f7e2cf" if intensity < 0.7 else "#f0c8a6")
            elements.extend(
                [
                    f'<rect x="{x:.2f}" y="{y:.2f}" width="{grid_cell_width:.2f}" '
                    f'height="{grid_cell_height:.2f}" fill="{fill}" stroke="#d7e0dc"/>',
                    f'<text x="{x + grid_cell_width / 2:.2f}" '
                    f'y="{y + grid_cell_height / 2 + 6:.2f}" text-anchor="middle" '
                    f'class="dp-cell">{value}</text>',
                ]
            )

    backtrack_points = " ".join(
        (
            f"{grid_left + capacity * grid_cell_width + grid_cell_width / 2:.2f},"
            f"{grid_top + row * grid_cell_height + grid_cell_height / 2:.2f}"
        )
        for row, capacity in backtrack
    )
    elements.append(
        f'<polyline points="{backtrack_points}" fill="none" stroke="#2c7564" '
        'stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>'
    )
    for row, capacity in backtrack:
        center_x = grid_left + capacity * grid_cell_width + grid_cell_width / 2
        center_y = grid_top + row * grid_cell_height + grid_cell_height / 2
        elements.append(
            f'<circle cx="{center_x:.2f}" cy="{center_y:.2f}" r="7" '
            'fill="#fff" stroke="#2c7564" stroke-width="3"/>'
        )
    final_x = grid_left + int(probe["capacity"]) * grid_cell_width + grid_cell_width / 2
    final_y = grid_top + (len(table) - 1) * grid_cell_height + grid_cell_height / 2
    elements.extend(
        [
            f'<circle cx="{final_x:.2f}" cy="{final_y:.2f}" r="11" fill="#2c7564"/>',
            f'<text x="{final_x:.2f}" y="{final_y + 5:.2f}" text-anchor="middle" '
            'class="dp-final">13</text>',
            '<text x="32" y="750" class="dp-metric-label">selected items</text>',
            '<text x="32" y="782" class="dp-metric">A + B</text>',
            '<text x="250" y="750" class="dp-metric-label">total weight</text>',
            (
                '<text x="250" y="782" class="dp-metric">'
                f"{int(probe['selected_weight'])} / {int(probe['capacity'])}</text>"
            ),
            '<text x="458" y="750" class="dp-metric-label">optimal value</text>',
            (f'<text x="458" y="782" class="dp-metric">{int(probe["optimal_value"])}</text>'),
            '<rect x="24" y="824" width="592" height="114" rx="18" fill="#eaf3ef"/>',
            '<text x="44" y="858" class="dp-result-title">backtracking result</text>',
            (
                '<text x="44" y="888" class="dp-result">'
                "A (weight 4, value 8) + B (weight 3, value 5)</text>"
            ),
            (
                '<text x="44" y="918" class="dp-result">'
                f"used 7 / 8 · unused {int(probe['unused_capacity'])} · value 13</text>"
            ),
            (
                '<text x="32" y="982" class="dp-meta">'
                "実行生成: scripts.generate_article_figures._dynamic_programming_knapsack_probe "
                f"· dataset {html.escape(dataset_version)}</text>"
            ),
            (
                '<text x="32" y="1020" class="dp-limit">'
                "固定4-item整数knapsackです。別instance、連続量、近似、solver一般の"
                "性能は示しません。</text>"
            ),
            (
                '<text x="32" y="1046" class="dp-limit">'
                "tableはO(nC)でcapacity値に依存します。大規模state spaceの実用性は"
                "示しません。</text>"
            ),
            """
<style>
  .dp-title { font: 700 23px system-ui, sans-serif; fill: #102a2e; }
  .dp-subtitle { font: 400 16px system-ui, sans-serif; fill: #45656a; }
  .dp-section { font: 700 15px system-ui, sans-serif; fill: #45656a; }
  .dp-item { font: 700 20px system-ui, sans-serif; fill: #102a2e; }
  .dp-item-detail { font: 400 13px system-ui, sans-serif; fill: #45656a; }
  .dp-item-status { font: 700 12px system-ui, sans-serif; fill: #2c7564; }
  .dp-panel { font: 700 19px system-ui, sans-serif; fill: #102a2e; }
  .dp-legend { font: 400 13px system-ui, sans-serif; fill: #45656a; }
  .dp-axis { font: 400 13px system-ui, sans-serif; fill: #45656a; }
  .dp-cell { font: 700 15px system-ui, sans-serif; fill: #102a2e; }
  .dp-final { font: 700 13px system-ui, sans-serif; fill: #fff; }
  .dp-metric-label { font: 400 14px system-ui, sans-serif; fill: #45656a; }
  .dp-metric { font: 700 21px system-ui, sans-serif; fill: #102a2e; }
  .dp-result-title { font: 700 17px system-ui, sans-serif; fill: #102a2e; }
  .dp-result { font: 400 15px system-ui, sans-serif; fill: #245c42; }
  .dp-meta { font: 400 12px system-ui, sans-serif; fill: #45656a; }
  .dp-limit { font: 400 12px system-ui, sans-serif; fill: #8b4c3d; }
</style>
""",
            "</svg>\n",
        ]
    )
    return "".join(elements)


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

    width, height = 640, 1080
    plot_left, plot_right = 78.0, 590.0
    plot_top, plot_bottom = 212.0, 612.0
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
    elements = [
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}" role="img" '
            'aria-labelledby="figure-title figure-description">'
        ),
        '<title id="figure-title">ε-constraintで生産planのcostとemissionsを選ぶ固定実行</title>',
        (
            '<desc id="figure-description">需要18以上を満たす技術XとYの整数生産planを'
            "88個列挙し、cost最小化を主目的、emissionsを上限制約として解く。"
            "emissions上限36、30、24、18では異なる4つのPareto planを選ぶ。"
            "上限12では実行可能planがない。</desc>"
        ),
        '<rect width="640" height="1080" rx="24" fill="#fbfaf5"/>',
        '<text x="32" y="48" class="ec-title">許容上限を下げると、選ぶ生産planが移る</text>',
        (
            '<text x="32" y="80" class="ec-subtitle">'
            "integer plans · demand ≥ 18 · minimize cost · emissions ≤ ε</text>"
        ),
        '<circle cx="40" cy="116" r="6" fill="#d67835" opacity=".55"/>',
        '<text x="54" y="121" class="ec-legend">feasible plan</text>',
        '<line x1="174" y1="116" x2="200" y2="116" stroke="#2c7564" stroke-width="5"/>',
        '<text x="210" y="121" class="ec-legend">Pareto front</text>',
        '<circle cx="348" cy="116" r="8" fill="#2c7564"/>',
        '<text x="364" y="121" class="ec-legend">ε solution</text>',
        '<rect x="24" y="148" width="592" height="500" rx="18" fill="#fff" stroke="#cad8d2"/>',
        '<text x="44" y="184" class="ec-panel">objective space · lower-left is preferred</text>',
    ]
    for cost_tick in (50, 75, 100, 125, 150):
        x = cost_x(cost_tick)
        elements.extend(
            [
                f'<line x1="{x:.2f}" y1="{plot_top}" x2="{x:.2f}" y2="{plot_bottom}" '
                'stroke="#e4ebe7"/>',
                f'<text x="{x:.2f}" y="634" text-anchor="middle" '
                f'class="ec-axis">{cost_tick}</text>',
            ]
        )
    for emissions_tick in (20, 40, 60, 80):
        y = emissions_y(emissions_tick)
        elements.extend(
            [
                f'<line x1="{plot_left}" y1="{y:.2f}" x2="{plot_right}" y2="{y:.2f}" '
                'stroke="#e4ebe7"/>',
                f'<text x="{plot_left - 10}" y="{y + 5:.2f}" text-anchor="end" '
                f'class="ec-axis">{emissions_tick}</text>',
            ]
        )
    for plan in plans:
        if plan in selected_plans:
            continue
        elements.append(
            f'<circle cx="{cost_x(plan[3]):.2f}" cy="{emissions_y(plan[4]):.2f}" r="4" '
            'fill="#d67835" opacity=".34"/>'
        )
    elements.append(
        f'<polyline points="{pareto_points}" fill="none" stroke="#2c7564" '
        'stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>'
    )
    for epsilon, plan in solutions:
        if plan is None:
            continue
        x = cost_x(plan[3])
        y = emissions_y(plan[4])
        elements.extend(
            [
                f'<circle cx="{x:.2f}" cy="{y:.2f}" r="9" fill="#2c7564" '
                'stroke="#fff" stroke-width="3"/>',
                f'<text x="{x + 12:.2f}" y="{y - 10:.2f}" class="ec-label">ε {epsilon}</text>',
            ]
        )
    elements.extend(
        [
            '<text x="334" y="642" text-anchor="middle" class="ec-axis-title">cost →</text>',
            (
                '<text x="22" y="422" transform="rotate(-90 22 422)" '
                'text-anchor="middle" class="ec-axis-title">emissions →</text>'
            ),
            '<rect x="24" y="674" width="592" height="258" rx="18" fill="#fff" stroke="#cad8d2"/>',
            '<text x="44" y="710" class="ec-panel">one subproblem per emissions limit</text>',
            '<text x="52" y="740" class="ec-table-head">ε</text>',
            '<text x="126" y="740" class="ec-table-head">status</text>',
            '<text x="270" y="740" class="ec-table-head">plan (X, Y)</text>',
            '<text x="456" y="740" class="ec-table-head">cost</text>',
        ]
    )
    for row_index, (epsilon, plan) in enumerate(solutions):
        row_y = 772.0 + row_index * 34.0
        if plan is None:
            status = "infeasible"
            plan_label = "—"
            cost_label = "—"
            status_class = "ec-infeasible"
        else:
            status = "optimal"
            plan_label = f"({plan[0]}, {plan[1]})"
            cost_label = str(plan[3])
            status_class = "ec-optimal"
        elements.extend(
            [
                f'<line x1="44" y1="{row_y - 20:.2f}" x2="596" y2="{row_y - 20:.2f}" '
                'stroke="#edf1ef"/>',
                f'<text x="52" y="{row_y:.2f}" class="ec-table">{epsilon}</text>',
                f'<text x="126" y="{row_y:.2f}" class="{status_class}">{status}</text>',
                f'<text x="270" y="{row_y:.2f}" class="ec-table">{plan_label}</text>',
                f'<text x="456" y="{row_y:.2f}" class="ec-table">{cost_label}</text>',
            ]
        )
    elements.extend(
        [
            '<text x="32" y="972" class="ec-metric-label">feasible plans</text>',
            (f'<text x="32" y="1000" class="ec-metric">{int(probe["feasible_count"])}</text>'),
            '<text x="230" y="972" class="ec-metric-label">Pareto plans</text>',
            (f'<text x="230" y="1000" class="ec-metric">{int(probe["pareto_count"])}</text>'),
            '<text x="430" y="972" class="ec-metric-label">solved thresholds</text>',
            (
                '<text x="430" y="1000" class="ec-metric">'
                f"{int(probe['solved_count'])} / {len(solutions)}</text>"
            ),
            (
                '<text x="32" y="1032" class="ec-meta">'
                "実行生成: scripts.generate_article_figures._epsilon_constraint_production_probe "
                f"· dataset {html.escape(dataset_version)}</text>"
            ),
            (
                '<text x="32" y="1058" class="ec-limit">'
                "固定整数列挙です。別需要、連続変数、backend solver、threshold設計、"
                "一般性能は示しません。</text>"
            ),
            """
<style>
  .ec-title { font: 700 23px system-ui, sans-serif; fill: #102a2e; }
  .ec-subtitle { font: 400 16px system-ui, sans-serif; fill: #45656a; }
  .ec-legend { font: 400 14px system-ui, sans-serif; fill: #45656a; }
  .ec-panel { font: 700 19px system-ui, sans-serif; fill: #102a2e; }
  .ec-axis { font: 400 13px system-ui, sans-serif; fill: #45656a; }
  .ec-axis-title { font: 700 14px system-ui, sans-serif; fill: #45656a; }
  .ec-label { font: 700 13px system-ui, sans-serif; fill: #245c42; }
  .ec-table-head { font: 700 13px system-ui, sans-serif; fill: #45656a; }
  .ec-table { font: 400 15px system-ui, sans-serif; fill: #102a2e; }
  .ec-optimal { font: 700 14px system-ui, sans-serif; fill: #2c7564; }
  .ec-infeasible { font: 700 14px system-ui, sans-serif; fill: #a34f43; }
  .ec-metric-label { font: 400 14px system-ui, sans-serif; fill: #45656a; }
  .ec-metric { font: 700 20px system-ui, sans-serif; fill: #102a2e; }
  .ec-meta { font: 400 12px system-ui, sans-serif; fill: #45656a; }
  .ec-limit { font: 400 12px system-ui, sans-serif; fill: #8b4c3d; }
</style>
""",
            "</svg>\n",
        ]
    )
    return "".join(elements)


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

    width, height = 640, 1080
    grid_columns = int(probe["width"])
    grid_rows = int(probe["height"])
    cell_size = 25.0
    grid_left = (width - grid_columns * cell_size) / 2

    def grid_elements(
        result: dict[str, object],
        *,
        grid_top: float,
    ) -> list[str]:
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
            'stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>'
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
                    f'<circle cx="{center_x:.2f}" cy="{center_y:.2f}" r="10" fill="{fill}"/>',
                    f'<text x="{center_x:.2f}" y="{center_y + 4.5:.2f}" '
                    f'text-anchor="middle" class="da-node">{label}</text>',
                ]
            )
        return elements

    dijkstra_expanded = len(dijkstra["expanded"])
    astar_expanded = len(astar["expanded"])
    elements = [
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}" role="img" '
            'aria-labelledby="figure-title figure-description">'
        ),
        '<title id="figure-title">Dijkstra法とA*探索の展開範囲を比較する固定grid実行</title>',
        (
            '<desc id="figure-description">17列11行の4近傍gridで、同じ始点と終点を'
            "Dijkstra法とManhattan heuristicのA*で探索する。両者の最短路costは24。"
            f"Dijkstra法は{dijkstra_expanded} cell、A*は{astar_expanded} cellを展開し、"
            "A*はgoal方向へ探索範囲を絞る。</desc>"
        ),
        '<rect width="640" height="1080" rx="24" fill="#fbfaf5"/>',
        '<text x="32" y="48" class="da-title">同じcost 24でも、探した範囲は違う</text>',
        (
            '<text x="32" y="80" class="da-subtitle">'
            "17 × 11 grid · unit edge cost · 4-neighbor moves · Manhattan h</text>"
        ),
        '<rect x="32" y="106" width="18" height="18" rx="3" fill="#f0c8a6"/>',
        '<text x="60" y="120" class="da-legend">expanded</text>',
        '<rect x="174" y="106" width="18" height="18" rx="3" fill="#73b7a2"/>',
        '<text x="202" y="120" class="da-legend">shortest path</text>',
        '<rect x="352" y="106" width="18" height="18" rx="3" fill="#243f49"/>',
        '<text x="380" y="120" class="da-legend">obstacle</text>',
        '<rect x="24" y="148" width="592" height="350" rx="18" fill="#fff" stroke="#cad8d2"/>',
        '<text x="44" y="184" class="da-panel">Dijkstra · h(n) = 0</text>',
        (
            '<text x="596" y="184" text-anchor="end" class="da-count">'
            f"{dijkstra_expanded} expanded</text>"
        ),
        *grid_elements(dijkstra, grid_top=207.0),
        '<rect x="24" y="520" width="592" height="350" rx="18" fill="#fff" stroke="#cad8d2"/>',
        '<text x="44" y="556" class="da-panel">A* · Manhattan h(n)</text>',
        (
            '<text x="596" y="556" text-anchor="end" class="da-count">'
            f"{astar_expanded} expanded</text>"
        ),
        *grid_elements(astar, grid_top=579.0),
        '<text x="32" y="920" class="da-metric-label">shortest path cost</text>',
        (
            '<text x="32" y="950" class="da-metric">'
            f"{int(dijkstra['cost'])} = {int(astar['cost'])}</text>"
        ),
        '<text x="258" y="920" class="da-metric-label">expanded cells</text>',
        (f'<text x="258" y="950" class="da-metric">{dijkstra_expanded} → {astar_expanded}</text>'),
        '<text x="474" y="920" class="da-metric-label">reduction</text>',
        (
            '<text x="474" y="950" class="da-metric">'
            f"{float(probe['expansion_reduction']):.0%}</text>"
        ),
        (
            '<text x="32" y="1002" class="da-meta">'
            "実行生成: scripts.generate_article_figures._dijkstra_astar_grid_probe "
            f"· dataset {html.escape(dataset_version)}</text>"
        ),
        (
            '<text x="32" y="1034" class="da-limit">'
            "固定unit-cost gridです。別graph、重み、tie-break、heuristic一般の"
            "展開削減率は示しません。</text>"
        ),
        (
            '<text x="32" y="1058" class="da-limit">'
            "Manhattan hはこの4近傍設定でadmissibleです。side constraintは含みません。</text>"
        ),
        """
<style>
  .da-title { font: 700 24px system-ui, sans-serif; fill: #102a2e; }
  .da-subtitle { font: 400 16px system-ui, sans-serif; fill: #45656a; }
  .da-legend { font: 400 14px system-ui, sans-serif; fill: #45656a; }
  .da-panel { font: 700 20px system-ui, sans-serif; fill: #102a2e; }
  .da-count { font: 700 16px system-ui, sans-serif; fill: #2c7564; }
  .da-node { font: 700 12px system-ui, sans-serif; fill: #fff; }
  .da-metric-label { font: 400 14px system-ui, sans-serif; fill: #45656a; }
  .da-metric { font: 700 20px system-ui, sans-serif; fill: #102a2e; }
  .da-meta { font: 400 12px system-ui, sans-serif; fill: #45656a; }
  .da-limit { font: 400 12px system-ui, sans-serif; fill: #8b4c3d; }
</style>
""",
        "</svg>\n",
    ]
    return "".join(elements)


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

    width, height = 640, 1080
    plot_left, plot_right = 84.0, 556.0
    point_min_x, point_max_x = -0.5, 4.5
    point_min_y, point_max_y = 0.0, 4.5

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
            f'<polyline points="{polyline}" fill="none" stroke="{color}" stroke-width="5" '
            'stroke-linecap="round" stroke-linejoin="round"/>'
        ]
        for node, point in enumerate(points):
            x, y = point_position(point, plot_top=plot_top, plot_bottom=plot_bottom)
            fill = "#102a2e" if node == 0 else "#fff"
            text_color = "#fff" if node == 0 else "#102a2e"
            elements.extend(
                [
                    f'<circle cx="{x:.2f}" cy="{y:.2f}" r="16" fill="{fill}" '
                    f'stroke="{color}" stroke-width="4"/>',
                    f'<text x="{x:.2f}" y="{y + 5:.2f}" text-anchor="middle" '
                    f'style="font: 700 14px system-ui, sans-serif; fill: {text_color};">'
                    f"{node}</text>",
                ]
            )
        return elements

    elements = [
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}" role="img" '
            'aria-labelledby="figure-title figure-description">'
        ),
        '<title id="figure-title">2-opt local searchで交差routeを改善する実行結果</title>',
        (
            '<desc id="figure-description">8地点の固定巡回routeをbest-improvement 2-optで'
            "改善する教材。初期routeには5交差があり、距離は29.07。"
            "segment反転を4回受理すると、周囲を順に回る交差0のrouteとなる。"
            "最終距離は16.88で、2-opt近傍内に改善moveがなくなる。</desc>"
        ),
        '<rect width="640" height="1080" rx="24" fill="#fbfaf5"/>',
        '<text x="32" y="48" class="ls-title">edgeを2本つなぎ替え、交差をほどく</text>',
        (
            '<text x="32" y="80" class="ls-subtitle">'
            "fixed 8-stop route · best-improvement 2-opt · depot 0 fixed</text>"
        ),
        '<rect x="24" y="112" width="592" height="360" rx="18" fill="#fff" stroke="#cad8d2"/>',
        '<text x="44" y="150" class="ls-panel">before · input order</text>',
        (
            '<text x="596" y="150" text-anchor="end" class="ls-length">'
            f"length {float(probe['initial_length']):.2f}</text>"
        ),
        *route_elements(
            initial_tour,
            plot_top=184.0,
            plot_bottom=438.0,
            color="#d67835",
        ),
        '<line x1="320" y1="484" x2="320" y2="516" stroke="#d67835" stroke-width="4"/>',
        '<path d="M312 508 L320 520 L328 508" fill="none" stroke="#d67835" stroke-width="4"/>',
        (
            '<text x="338" y="507" class="ls-moves">'
            f"best-improvement · {int(probe['accepted_moves'])} accepted reversals</text>"
        ),
        '<rect x="24" y="534" width="592" height="360" rx="18" fill="#fff" stroke="#cad8d2"/>',
        '<text x="44" y="572" class="ls-panel">after · no improving 2-opt move</text>',
        (
            '<text x="596" y="572" text-anchor="end" class="ls-length">'
            f"length {float(probe['final_length']):.2f}</text>"
        ),
        *route_elements(
            final_tour,
            plot_top=606.0,
            plot_bottom=860.0,
            color="#2c7564",
        ),
        '<text x="32" y="940" class="ls-metric-label">route length</text>',
        (
            '<text x="32" y="970" class="ls-metric">'
            f"{float(probe['initial_length']):.2f} → {float(probe['final_length']):.2f}"
            "</text>"
        ),
        '<text x="286" y="940" class="ls-metric-label">crossings</text>',
        (
            '<text x="286" y="970" class="ls-metric">'
            f"{int(probe['initial_crossings'])} → {int(probe['final_crossings'])}</text>"
        ),
        '<text x="456" y="940" class="ls-metric-label">accepted</text>',
        (f'<text x="456" y="970" class="ls-metric">{int(probe["accepted_moves"])} moves</text>'),
        (
            '<text x="32" y="1014" class="ls-meta">'
            "実行生成: scripts.generate_article_figures._local_search_two_opt_probe "
            f"· dataset {html.escape(dataset_version)}</text>"
        ),
        (
            '<text x="32" y="1046" class="ls-limit">'
            "固定Euclidean 8地点教材です。time window、vehicle capacity、traffic、"
            "大域最適性は示しません。</text>"
        ),
        (
            '<text x="32" y="1068" class="ls-limit">'
            "別初期route、別近傍、実routing solver一般の性能も示しません。</text>"
        ),
        """
<style>
  .ls-title { font: 700 24px system-ui, sans-serif; fill: #102a2e; }
  .ls-subtitle { font: 400 17px system-ui, sans-serif; fill: #45656a; }
  .ls-panel { font: 700 21px system-ui, sans-serif; fill: #102a2e; }
  .ls-length { font: 700 17px system-ui, sans-serif; fill: #2c7564; }
  .ls-moves { font: 700 14px system-ui, sans-serif; fill: #8b4c3d; }
  .ls-metric-label { font: 400 14px system-ui, sans-serif; fill: #45656a; }
  .ls-metric { font: 700 19px system-ui, sans-serif; fill: #102a2e; }
  .ls-meta { font: 400 13px system-ui, sans-serif; fill: #45656a; }
  .ls-limit { font: 400 13px system-ui, sans-serif; fill: #8b4c3d; }
</style>
""",
        "</svg>\n",
    ]
    return "".join(elements)


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

    width, height = 640, 1080
    plot_left, plot_right = 74.0, 594.0
    landscape_top, landscape_bottom = 194.0, 470.0
    trace_top, trace_bottom = 628.0, 894.0
    lower_bound, upper_bound = (float(value) for value in bounds)
    objective_max = 42.0

    def position_x(value: float) -> float:
        return plot_left + (value - lower_bound) / (upper_bound - lower_bound) * (
            plot_right - plot_left
        )

    def landscape_y(value: float) -> float:
        return landscape_bottom - min(value, objective_max) / objective_max * (
            landscape_bottom - landscape_top
        )

    def iteration_x(iteration: int) -> float:
        return plot_left + iteration / int(probe["iterations"]) * (plot_right - plot_left)

    def trace_y(value: float) -> float:
        return trace_bottom - min(value, objective_max) / objective_max * (trace_bottom - trace_top)

    def temperature_y(value: float) -> float:
        ratio = value / float(probe["initial_temperature"])
        return trace_bottom - ratio * (trace_bottom - trace_top)

    landscape = " ".join(
        f"{position_x(x):.2f},{landscape_y(_simulated_annealing_objective(x)):.2f}"
        for x in (lower_bound + index / 320 * (upper_bound - lower_bound) for index in range(321))
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
    accepted_positions = [
        (float(item["x"]), float(item["objective"]), int(item["iteration"]))
        for item in history[1:]
        if bool(item["accepted"])
    ]
    worsening_positions = [
        (int(item["iteration"]), float(item["objective"]))
        for item in history[1:]
        if bool(item["accepted_worsening"])
    ]

    elements = [
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}" role="img" '
            'aria-labelledby="figure-title figure-description">'
        ),
        '<title id="figure-title">Simulated Annealingで悪化移動を受理する固定実行</title>',
        (
            '<desc id="figure-description">1次元Rastrigin関数を初期点3.5から400反復探索する'
            "固定seed実行。高温の序盤では悪化移動も受理して複数の谷を移動し、"
            "best-so-farは悪化させず保持する。目的値は32.25から0.00076まで改善する。</desc>"
        ),
        '<rect width="640" height="1080" rx="24" fill="#fbfaf5"/>',
        '<text x="32" y="48" class="sa-title">currentは悪化しても、bestは手放さない</text>',
        (
            '<text x="32" y="80" class="sa-subtitle">'
            "1D Rastrigin · seed 7 · 400 iterations · T₀ 5.0 · cooling 0.985</text>"
        ),
        '<line x1="32" y1="116" x2="58" y2="116" stroke="#d67835" stroke-width="5"/>',
        '<text x="68" y="122" class="sa-legend">current</text>',
        '<line x1="164" y1="116" x2="190" y2="116" stroke="#2c7564" stroke-width="6"/>',
        '<text x="200" y="122" class="sa-legend">best-so-far</text>',
        (
            '<line x1="342" y1="116" x2="368" y2="116" stroke="#345d6b" '
            'stroke-width="3" stroke-dasharray="8 6"/>'
        ),
        '<text x="378" y="122" class="sa-legend">temperature (scaled)</text>',
        '<circle cx="516" cy="116" r="7" fill="#fff" stroke="#9f552c" stroke-width="3"/>',
        '<text x="530" y="122" class="sa-legend">accepted worse</text>',
        '<rect x="24" y="150" width="592" height="354" rx="18" fill="#fff" stroke="#cad8d2"/>',
        '<text x="44" y="184" class="sa-panel">accepted states cross several basins</text>',
        (
            f'<polyline points="{landscape}" fill="none" stroke="#345d6b" '
            'stroke-width="3" stroke-linejoin="round"/>'
        ),
    ]
    for x, objective, iteration in accepted_positions:
        opacity = 0.28 + 0.52 * (1.0 - iteration / int(probe["iterations"]))
        elements.append(
            f'<circle cx="{position_x(x):.2f}" cy="{landscape_y(objective):.2f}" r="3.5" '
            f'fill="#d67835" opacity="{opacity:.2f}"/>'
        )
    start_x = position_x(float(probe["initial_x"]))
    start_y = landscape_y(float(probe["initial_objective"]))
    best_x = position_x(float(probe["best_x"]))
    best_y = landscape_y(float(probe["best_objective"]))
    elements.extend(
        [
            f'<circle cx="{start_x:.2f}" cy="{start_y:.2f}" r="8" fill="#102a2e"/>',
            f'<text x="{start_x - 10:.2f}" y="{start_y - 13:.2f}" text-anchor="end" '
            'class="sa-label">start</text>',
            f'<circle cx="{best_x:.2f}" cy="{best_y:.2f}" r="9" fill="#2c7564"/>',
            f'<text x="{best_x + 12:.2f}" y="{best_y - 10:.2f}" class="sa-label">best</text>',
        ]
    )
    for tick in (-5, -3, -1, 1, 3, 5):
        elements.append(
            f'<text x="{position_x(float(tick)):.2f}" y="490" text-anchor="middle" '
            f'class="sa-axis">{tick}</text>'
        )
    elements.extend(
        [
            '<rect x="24" y="538" width="592" height="390" rx="18" fill="#fff" stroke="#cad8d2"/>',
            (
                '<text x="44" y="576" class="sa-panel">'
                "temperature falls; current can still rise</text>"
            ),
        ]
    )
    for tick in (0, 10, 20, 30, 40):
        y = trace_y(float(tick))
        elements.extend(
            [
                f'<line x1="{plot_left}" y1="{y:.2f}" x2="{plot_right}" y2="{y:.2f}" '
                'stroke="#e4ebe7" stroke-width="1"/>',
                f'<text x="{plot_left - 10}" y="{y + 5:.2f}" text-anchor="end" '
                f'class="sa-axis">{tick}</text>',
            ]
        )
    elements.extend(
        [
            (
                f'<polyline points="{temperature_trace}" fill="none" stroke="#345d6b" '
                'stroke-width="3" stroke-dasharray="8 6"/>'
            ),
            (
                f'<polyline points="{current_trace}" fill="none" stroke="#d67835" '
                'stroke-width="3" stroke-linejoin="round"/>'
            ),
            (
                f'<polyline points="{best_trace}" fill="none" stroke="#2c7564" '
                'stroke-width="6" stroke-linejoin="round"/>'
            ),
        ]
    )
    for iteration, objective in worsening_positions:
        elements.append(
            f'<circle cx="{iteration_x(iteration):.2f}" cy="{trace_y(objective):.2f}" r="4.5" '
            'fill="#fff" stroke="#9f552c" stroke-width="2.5"/>'
        )
    for tick in (0, 100, 200, 300, 400):
        elements.append(
            f'<text x="{iteration_x(tick):.2f}" y="906" text-anchor="middle" '
            f'class="sa-axis">{tick}</text>'
        )
    elements.extend(
        [
            '<text x="334" y="922" text-anchor="middle" class="sa-axis">iteration</text>',
            '<text x="32" y="966" class="sa-metric-label">best objective</text>',
            (
                '<text x="32" y="994" class="sa-metric">'
                f"{float(probe['initial_objective']):.2f} → "
                f"{float(probe['best_objective']):.5f}</text>"
            ),
            '<text x="278" y="966" class="sa-metric-label">accepted worse</text>',
            (
                '<text x="278" y="994" class="sa-metric">'
                f"{int(probe['accepted_worsening'])} / "
                f"{int(probe['accepted_moves'])} moves</text>"
            ),
            '<text x="480" y="966" class="sa-metric-label">early / late</text>',
            (
                '<text x="480" y="994" class="sa-metric">'
                f"{int(probe['early_worsening'])} / {int(probe['late_worsening'])}</text>"
            ),
            (
                '<text x="32" y="1030" class="sa-meta">'
                "実行生成: scripts.generate_article_figures._simulated_annealing_probe "
                f"· dataset {html.escape(dataset_version)}</text>"
            ),
            (
                '<text x="32" y="1058" class="sa-limit">'
                "固定1次元・1 seedの教材です。別seed・高次元・schedule一般の性能や"
                "大域最適性は示しません。</text>"
            ),
            """
<style>
  .sa-title { font: 700 23px system-ui, sans-serif; fill: #102a2e; }
  .sa-subtitle { font: 400 16px system-ui, sans-serif; fill: #45656a; }
  .sa-panel { font: 700 19px system-ui, sans-serif; fill: #102a2e; }
  .sa-legend { font: 400 13px system-ui, sans-serif; fill: #45656a; }
  .sa-axis { font: 400 13px system-ui, sans-serif; fill: #45656a; }
  .sa-label { font: 700 14px system-ui, sans-serif; fill: #102a2e; }
  .sa-metric-label { font: 400 14px system-ui, sans-serif; fill: #45656a; }
  .sa-metric { font: 700 19px system-ui, sans-serif; fill: #102a2e; }
  .sa-meta { font: 400 12px system-ui, sans-serif; fill: #45656a; }
  .sa-limit { font: 400 12px system-ui, sans-serif; fill: #8b4c3d; }
</style>
""",
            "</svg>\n",
        ]
    )
    return "".join(elements)


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

    width, height = 640, 1080
    x_supply, x_demand = 104.0, 536.0
    x_supply_edge, x_demand_edge = 135.0, 501.0
    supply_y = {"A": 250.0, "B": 400.0}
    demand_y = {"X": 205.0, "Y": 325.0, "Z": 445.0}
    label_offsets = {
        ("A", "X"): -18.0,
        ("A", "Y"): -13.0,
        ("A", "Z"): -5.0,
        ("B", "X"): -14.0,
        ("B", "Y"): 28.0,
        ("B", "Z"): 19.0,
    }
    label_x = {
        ("A", "X"): 320.0,
        ("A", "Y"): 286.0,
        ("A", "Z"): 276.0,
        ("B", "X"): 364.0,
        ("B", "Y"): 372.0,
        ("B", "Z"): 320.0,
    }

    def panel_graph(
        flows: dict[tuple[str, str], float],
        *,
        y_offset: float,
        optimized: bool,
    ) -> list[str]:
        elements: list[str] = []
        active_color = "#2c7564" if optimized else "#102a2e"
        active_marker = "ns-arrow-active" if optimized else "ns-arrow-tree"
        for arc, cost in costs.items():
            tail, head = arc
            y1 = supply_y[tail] + y_offset
            y2 = demand_y[head] + y_offset
            flow = float(flows[arc])
            elements.append(
                f'<line x1="{x_supply_edge}" y1="{y1:.2f}" '
                f'x2="{x_demand_edge}" y2="{y2:.2f}" '
                'stroke="#dfe7e3" stroke-width="2"/>'
            )
            if flow > 1e-12:
                elements.append(
                    f'<line x1="{x_supply_edge}" y1="{y1:.2f}" '
                    f'x2="{x_demand_edge}" y2="{y2:.2f}" '
                    f'stroke="{active_color}" stroke-width="{3.0 + 1.5 * flow:.2f}" '
                    f'stroke-linecap="round" marker-end="url(#{active_marker})"/>'
                )
                midpoint_y = (y1 + y2) / 2.0 + label_offsets[arc]
                elements.append(
                    f'<text x="{label_x[arc]:.2f}" y="{midpoint_y:.2f}" text-anchor="middle" '
                    f'class="ns-flow">{flow:g} × cost {float(cost):g}</text>'
                )

        highlighted_arc = probe["leaving"] if optimized else probe["entering"]
        if not isinstance(highlighted_arc, tuple):
            raise TypeError("network-simplex highlighted arc must be a tuple")
        tail, head = highlighted_arc
        y1 = supply_y[tail] + y_offset
        y2 = demand_y[head] + y_offset
        if optimized:
            elements.append(
                f'<line x1="{x_supply_edge}" y1="{y1:.2f}" '
                f'x2="{x_demand_edge}" y2="{y2:.2f}" '
                'stroke="#aebbb6" stroke-width="4" stroke-dasharray="8 7" '
                'marker-end="url(#ns-arrow-muted)"/>'
            )
        else:
            elements.append(
                f'<line x1="{x_supply_edge}" y1="{y1:.2f}" '
                f'x2="{x_demand_edge}" y2="{y2:.2f}" '
                'stroke="#d67835" stroke-width="5" stroke-dasharray="9 7" '
                'marker-end="url(#ns-arrow-enter)"/>'
            )

        for node, amount in probe["supplies"].items():
            y = supply_y[node] + y_offset
            elements.extend(
                [
                    f'<circle cx="{x_supply}" cy="{y:.2f}" r="31" fill="#d67835"/>',
                    f'<text x="{x_supply}" y="{y + 6:.2f}" text-anchor="middle" '
                    f'class="ns-node">{node}</text>',
                    f'<text x="46" y="{y + 5:.2f}" class="ns-balance">+{float(amount):g}</text>',
                ]
            )
        for node, amount in probe["demands"].items():
            y = demand_y[node] + y_offset
            elements.extend(
                [
                    f'<circle cx="{x_demand}" cy="{y:.2f}" r="31" fill="#2c7564"/>',
                    f'<text x="{x_demand}" y="{y + 6:.2f}" text-anchor="middle" '
                    f'class="ns-node">{node}</text>',
                    f'<text x="582" y="{y + 5:.2f}" class="ns-balance">−{float(amount):g}</text>',
                ]
            )
        return elements

    elements = [
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}" role="img" '
            'aria-labelledby="figure-title figure-description">'
        ),
        '<title id="figure-title">Network Simplexの1回のpivotで輸送flowが変わる様子</title>',
        (
            '<desc id="figure-description">供給node AとBから需要node X、Y、Zへ9単位を'
            "輸送する固定最小費用流。初期treeへAからZのedgeを加える。"
            "できたcycleに1単位を流すとAからYのedgeがtreeを離れる。"
            "全nodeの需給を保ったまま総費用が20から18へ下がる。</desc>"
        ),
        '<rect width="640" height="1080" rx="24" fill="#fbfaf5"/>',
        '<text x="32" y="48" class="ns-title">1本加えると、cycleが1つできる</text>',
        (
            '<text x="32" y="80" class="ns-subtitle">'
            "fixed transportation flow · one tree pivot · integer supplies</text>"
        ),
        (
            "<defs>"
            '<marker id="ns-arrow-muted" markerWidth="6" markerHeight="6" refX="5" refY="3" '
            'orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#aebbb6"/></marker>'
            '<marker id="ns-arrow-tree" markerWidth="6" markerHeight="6" refX="5" refY="3" '
            'orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#102a2e"/></marker>'
            '<marker id="ns-arrow-active" markerWidth="6" markerHeight="6" refX="5" refY="3" '
            'orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#2c7564"/></marker>'
            '<marker id="ns-arrow-enter" markerWidth="6" markerHeight="6" refX="5" refY="3" '
            'orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#d67835"/></marker>'
            "</defs>"
        ),
        '<rect x="24" y="112" width="592" height="390" rx="18" fill="#fff" stroke="#cad8d2"/>',
        '<text x="44" y="150" class="ns-panel">before · feasible spanning tree</text>',
        '<text x="596" y="150" text-anchor="end" class="ns-cost">total cost 20</text>',
        (
            '<text x="44" y="184" class="ns-hint">'
            "orange dashed: entering A → Z · reduced cost −2</text>"
        ),
        *panel_graph(initial_flows, y_offset=0.0, optimized=False),
        '<rect x="24" y="526" width="592" height="390" rx="18" fill="#fff" stroke="#cad8d2"/>',
        '<text x="44" y="564" class="ns-panel">after · θ = 1 along the cycle</text>',
        '<text x="596" y="564" text-anchor="end" class="ns-cost">total cost 18</text>',
        '<text x="44" y="598" class="ns-hint">gray dashed: leaving A → Y · flow reaches 0</text>',
        *panel_graph(optimized_flows, y_offset=414.0, optimized=True),
        '<text x="32" y="956" class="ns-metric-label">pivot</text>',
        '<text x="32" y="984" class="ns-metric">A→Z enters · A→Y leaves</text>',
        '<text x="424" y="956" class="ns-metric-label">cost change</text>',
        '<text x="424" y="984" class="ns-metric">20 → 18</text>',
        (
            '<text x="32" y="1022" class="ns-meta">'
            "実行生成: scripts.generate_article_figures._network_simplex_transport_probe "
            f"· dataset {html.escape(dataset_version)}</text>"
        ),
        (
            '<text x="32" y="1052" class="ns-limit">'
            "固定2供給×3需要教材です。degeneracy、capacity upper bound、"
            "大規模networkの性能は示しません。</text>"
        ),
        """
<style>
  .ns-title { font: 700 24px system-ui, sans-serif; fill: #102a2e; }
  .ns-subtitle { font: 400 17px system-ui, sans-serif; fill: #45656a; }
  .ns-panel { font: 700 21px system-ui, sans-serif; fill: #102a2e; }
  .ns-cost { font: 700 17px system-ui, sans-serif; fill: #2c7564; }
  .ns-hint { font: 400 15px system-ui, sans-serif; fill: #8b4c3d; }
  .ns-node { font: 700 20px system-ui, sans-serif; fill: #fff; }
  .ns-balance { font: 700 16px system-ui, sans-serif; fill: #45656a; }
  .ns-flow {
    font: 700 14px system-ui, sans-serif;
    fill: #102a2e;
    paint-order: stroke;
    stroke: #fff;
    stroke-width: 5px;
  }
  .ns-metric-label { font: 400 14px system-ui, sans-serif; fill: #45656a; }
  .ns-metric { font: 700 18px system-ui, sans-serif; fill: #102a2e; }
  .ns-meta { font: 400 13px system-ui, sans-serif; fill: #45656a; }
  .ns-limit { font: 400 13px system-ui, sans-serif; fill: #8b4c3d; }
</style>
""",
        "</svg>\n",
    ]
    return "".join(elements)


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

    width, height = 640, 1080
    plot_left, plot_right = 78.0, 590.0
    worker_colors = ("#d67835", "#245c42", "#45656a", "#b08a3c", "#77647f", "#102a2e")
    score_top, score_bottom = 218.0, 482.0

    def round_x(round_index: int) -> float:
        return plot_left + round_index / 10 * (plot_right - plot_left)

    def score_y(score: float) -> float:
        return score_bottom - (score + 1.05) / 1.1 * (score_bottom - score_top)

    score_lines = []
    for worker_id in range(6):
        points = []
        for round_index, rows in enumerate(snapshots):
            row = rows[worker_id]
            points.append(f"{round_x(round_index):.2f},{score_y(float(row[4])):.2f}")
        score_lines.append(" ".join(points))

    elements = [
        _svg_open(
            "scoreの線とlineageの継承を同時に追う",
            (
                "6 workerを10 round進め、2 roundごとに最良workerから最下位workerへ"
                "stateをコピーし、learning rateを0.8倍または1.2倍した固定pure Python "
                "PBT教材です。worker scoreとlineage rootの継承を示します。実model、"
                "checkpoint cost、validation noise、並列実行、PBT一般の性能は示しません。"
            ),
            width=width,
            height=height,
        ),
        f'<rect width="{width}" height="{height}" rx="24" fill="#f7f6f1"/>',
        '<text x="32" y="50" class="pbt-title">scoreの線とlineageの継承を同時に追う</text>',
        (
            '<text x="32" y="82" class="pbt-subtitle">'
            "6 workers · 10 rounds · exploit every 2 rounds · deterministic toy training</text>"
        ),
        '<defs><marker id="pbt-arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" '
        'orient="auto"><path d="M0,0 L8,4 L0,8 Z" fill="#d67835"/></marker></defs>',
        '<line x1="36" y1="118" x2="62" y2="118" stroke="#45656a" stroke-width="5"/>',
        '<text x="72" y="124" class="pbt-legend">worker score</text>',
        '<path d="M218 126 C230 104, 246 104, 258 126" fill="none" stroke="#d67835" '
        'stroke-width="3" marker-end="url(#pbt-arrow)"/>',
        '<text x="270" y="124" class="pbt-legend">exploit copy</text>',
        '<text x="448" y="124" class="pbt-legend">line color = lineage root</text>',
        '<rect x="24" y="150" width="592" height="382" rx="18" fill="#fff" stroke="#cfd8d1"/>',
        '<text x="44" y="188" class="pbt-panel">同じworker IDでもcopy後は別lineageを継ぐ</text>',
        '<text x="596" y="188" text-anchor="end" class="pbt-status">score: higher is better</text>',
    ]
    for score in (-1.0, -0.75, -0.5, -0.25, 0.0):
        y = score_y(score)
        elements.extend(
            [
                (
                    f'<line x1="{plot_left}" y1="{y:.2f}" x2="{plot_right}" y2="{y:.2f}" '
                    'stroke="#ebe8e0"/>'
                ),
                (
                    f'<text x="{plot_left - 10}" y="{y + 5:.2f}" text-anchor="end" '
                    f'class="pbt-axis">{score:g}</text>'
                ),
            ]
        )
    for worker_id, points in enumerate(score_lines):
        elements.append(
            f'<polyline points="{points}" fill="none" stroke="{worker_colors[worker_id]}" '
            'stroke-width="3" stroke-linejoin="round"/>'
        )
        for round_index, rows in enumerate(snapshots):
            row = rows[worker_id]
            elements.append(
                f'<circle cx="{round_x(round_index):.2f}" cy="{score_y(float(row[4])):.2f}" '
                f'r="3.5" fill="{worker_colors[worker_id]}"/>'
            )
    for worker_id, color in enumerate(worker_colors):
        legend_x = 54 + worker_id * 94
        elements.extend(
            [
                f'<circle cx="{legend_x}" cy="508" r="5" fill="{color}"/>',
                f'<text x="{legend_x + 10}" y="513" class="pbt-axis">W{worker_id}</text>',
            ]
        )

    lineage_top = 620.0
    row_gap = 48.0
    elements.extend(
        [
            '<rect x="24" y="554" width="592" height="388" rx="18" fill="#fff" stroke="#cfd8d1"/>',
            '<text x="44" y="592" class="pbt-panel">copy元とlearning rate変更を残す</text>',
        ]
    )
    for round_index in range(11):
        x = round_x(round_index)
        elements.extend(
            [
                (
                    f'<line x1="{x:.2f}" y1="{lineage_top - 18}" x2="{x:.2f}" '
                    f'y2="{lineage_top + 5 * row_gap + 18}" stroke="#f0ede6"/>'
                ),
                (
                    f'<text x="{x:.2f}" y="918" text-anchor="middle" '
                    f'class="pbt-axis">{round_index}</text>'
                ),
            ]
        )
    for worker_id in range(6):
        y = lineage_top + worker_id * row_gap
        elements.extend(
            [
                (
                    f'<text x="58" y="{y + 5:.2f}" text-anchor="end" '
                    f'class="pbt-label">W{worker_id}</text>'
                ),
                (
                    f'<line x1="{plot_left}" y1="{y:.2f}" x2="{plot_right}" y2="{y:.2f}" '
                    'stroke="#ebe8e0" stroke-width="8" stroke-linecap="round"/>'
                ),
            ]
        )
        for round_index in range(10):
            root = int(snapshots[round_index][worker_id][3])
            elements.append(
                f'<line x1="{round_x(round_index):.2f}" y1="{y:.2f}" '
                f'x2="{round_x(round_index + 1):.2f}" y2="{y:.2f}" '
                f'stroke="{worker_colors[root]}" stroke-width="8" stroke-linecap="round"/>'
            )
    for event_index, event in enumerate(events):
        round_index, source_id, target_id, source_root, _, learning_rate, _, _ = event
        x = round_x(int(round_index))
        source_y = lineage_top + int(source_id) * row_gap
        target_y = lineage_top + int(target_id) * row_gap
        control_x = x + (12 if target_y >= source_y else -12)
        elements.extend(
            [
                (
                    f'<path d="M {x - 8:.2f} {source_y:.2f} Q {control_x:.2f} '
                    f'{(source_y + target_y) / 2:.2f} {x:.2f} {target_y:.2f}" '
                    'fill="none" stroke="#d67835" stroke-width="3" '
                    'marker-end="url(#pbt-arrow)"/>'
                ),
                (
                    f'<circle cx="{x:.2f}" cy="{target_y:.2f}" r="7" '
                    f'fill="{worker_colors[int(source_root)]}" stroke="#fff" stroke-width="2"/>'
                ),
            ]
        )
        label_y = target_y - 12 if event_index % 2 == 0 else target_y + 22
        anchor = "end" if round_index == 10 else "start"
        label_x = x - 8 if round_index == 10 else x + 8
        elements.append(
            f'<text x="{label_x:.2f}" y="{label_y:.2f}" text-anchor="{anchor}" '
            f'class="pbt-event">η={float(learning_rate):.3f}</text>'
        )
    elements.extend(
        [
            '<text x="78" y="934" class="pbt-axis">round</text>',
            (
                '<text x="32" y="982" class="pbt-metric">'
                f"best score {float(probe['initial_best']):.3f} → "
                f"{float(probe['final_best']):.3f}</text>"
            ),
            (
                '<text x="350" y="982" text-anchor="middle" class="pbt-metric">'
                f"exploit events {len(events)}</text>"
            ),
            (
                '<text x="608" y="982" text-anchor="end" class="pbt-metric">'
                f"final lineage roots {len(probe['final_roots'])}</text>"
            ),
            (
                '<text x="32" y="1026" class="pbt-meta">'
                f"実行生成: fixed toy training + deterministic exploit/explore "
                f"· dataset {html.escape(dataset_version)}</text>"
            ),
            '<text x="32" y="1054" class="pbt-note">'
            "固定score教材です。実model、checkpoint cost、validation noise、"
            "PBT一般の性能は示しません。</text>",
            """
<style>
  .pbt-title { font: 700 24px system-ui, sans-serif; fill: #102a2e; }
  .pbt-subtitle { font: 400 17px system-ui, sans-serif; fill: #45656a; }
  .pbt-panel { font: 700 21px system-ui, sans-serif; fill: #102a2e; }
  .pbt-status, .pbt-legend { font: 400 15px system-ui, sans-serif; fill: #45656a; }
  .pbt-axis { font: 400 16px system-ui, sans-serif; fill: #45656a; }
  .pbt-label { font: 700 17px system-ui, sans-serif; fill: #102a2e; }
  .pbt-event { font: 700 14px system-ui, sans-serif; fill: #8b4c3d; }
  .pbt-metric { font: 700 18px system-ui, sans-serif; fill: #102a2e; }
  .pbt-meta { font: 400 14px system-ui, sans-serif; fill: #45656a; }
  .pbt-note { font: 400 14px system-ui, sans-serif; fill: #8b4c3d; }
</style>
""",
            "</svg>\n",
        ]
    )
    return "".join(elements)


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

    width, height = 640, 1080
    plot_left, plot_right = 76.0, 590.0
    parameter_top, parameter_bottom = 220.0, 526.0
    parameter1_min, parameter1_max = -1.35, 2.15
    parameter2_min, parameter2_max = -1.2, 1.55

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

    contour_polylines = []
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
        contour_polylines.append(" ".join(points))

    path_points = " ".join(
        f"{parameter_x(float(point[0])):.2f},{parameter_y(float(point[1])):.2f}" for point in path
    )
    loss_top, loss_bottom = 705.0, 900.0
    max_update = int(history[-1][0])

    def update_x(update: int) -> float:
        return plot_left + update / max_update * (plot_right - plot_left)

    def loss_y(value: float) -> float:
        log_value = math.log10(max(value, 1e-4))
        return loss_bottom - (log_value + 4.0) / 4.5 * (loss_bottom - loss_top)

    batch_loss_points = " ".join(
        f"{update_x(int(row[0])):.2f},{loss_y(float(row[2])):.2f}" for row in history
    )
    full_loss_points = " ".join(
        f"{update_x(int(row[0])):.2f},{loss_y(float(row[3])):.2f}" for row in history
    )

    elements = [
        _svg_open(
            "mini-batchの揺れとfull-data lossを分けて読む",
            (
                "32 sample、2 parameterの固定線形回帰をbatch size 4、learning rate 0.3で"
                "8 epoch実行したpure Python SGD結果です。parameter path、mini-batch loss、"
                "full-data lossを同じrunから示します。validation、generalization、"
                "neural network、framework実装、SGD一般の性能は示しません。"
            ),
            width=width,
            height=height,
        ),
        f'<rect width="{width}" height="{height}" rx="24" fill="#f7f6f1"/>',
        '<text x="32" y="50" class="sgd-title">mini-batchの揺れとfull-data lossを分けて読む</text>',
        (
            '<text x="32" y="82" class="sgd-subtitle">'
            "32 samples · 2 parameters · batch 4 · η 0.3 · 8 epochs</text>"
        ),
        '<line x1="36" y1="118" x2="62" y2="118" stroke="#245c42" stroke-width="6"/>',
        '<text x="72" y="124" class="sgd-legend">full-data</text>',
        '<line x1="222" y1="118" x2="248" y2="118" stroke="#d67835" stroke-width="5"/>',
        '<text x="258" y="124" class="sgd-legend">mini-batch / update</text>',
        '<circle cx="500" cy="117" r="7" fill="#245c42"/>',
        '<text x="514" y="124" class="sgd-legend">full-data optimum</text>',
        '<rect x="24" y="150" width="592" height="424" rx="18" fill="#fff" stroke="#cfd8d1"/>',
        (
            '<text x="44" y="188" class="sgd-panel">'
            "同じfull-data loss面でもstepは小刻みに揺れる</text>"
        ),
        (
            f'<clipPath id="sgd-parameter-clip"><rect x="{plot_left}" y="{parameter_top}" '
            f'width="{plot_right - plot_left}" '
            f'height="{parameter_bottom - parameter_top}"/></clipPath>'
        ),
    ]
    for contour in contour_polylines:
        elements.append(
            f'<polyline points="{contour}" fill="none" stroke="#d9e2dd" stroke-width="2" '
            'clip-path="url(#sgd-parameter-clip)"/>'
        )
    for tick in (-1.0, 0.0, 1.0, 2.0):
        x = parameter_x(tick)
        elements.extend(
            [
                (
                    f'<line x1="{x:.2f}" y1="{parameter_top}" x2="{x:.2f}" '
                    f'y2="{parameter_bottom}" stroke="#f0ede6"/>'
                ),
                (
                    f'<text x="{x:.2f}" y="550" text-anchor="middle" '
                    f'class="sgd-axis">{tick:g}</text>'
                ),
            ]
        )
    for tick in (-1.0, 0.0, 1.0):
        y = parameter_y(tick)
        elements.extend(
            [
                (
                    f'<line x1="{plot_left}" y1="{y:.2f}" x2="{plot_right}" y2="{y:.2f}" '
                    'stroke="#f0ede6"/>'
                ),
                (
                    f'<text x="{plot_left - 10}" y="{y + 5:.2f}" text-anchor="end" '
                    f'class="sgd-axis">{tick:g}</text>'
                ),
            ]
        )
    elements.append(
        f'<polyline points="{path_points}" fill="none" stroke="#d67835" stroke-width="4" '
        'stroke-linejoin="round" stroke-linecap="round"/>'
    )
    start = path[0]
    elements.append(
        f'<text x="{parameter_x(float(start[0])) + 12:.2f}" '
        f'y="{parameter_y(float(start[1])) - 10:.2f}" class="sgd-label">start</text>'
    )
    for index, point in enumerate(path):
        if index % 8 == 0 or index == len(path) - 1:
            elements.append(
                f'<circle cx="{parameter_x(float(point[0])):.2f}" '
                f'cy="{parameter_y(float(point[1])):.2f}" r="5" '
                'fill="#d67835" stroke="#fff" stroke-width="2"/>'
            )
    elements.extend(
        [
            (
                f'<circle cx="{parameter_x(float(optimum[0])):.2f}" '
                f'cy="{parameter_y(float(optimum[1])):.2f}" r="8" '
                'fill="#245c42" stroke="#fff" stroke-width="3"/>'
            ),
            (
                f'<text x="{parameter_x(float(optimum[0])) - 12:.2f}" '
                f'y="{parameter_y(float(optimum[1])) - 14:.2f}" text-anchor="end" '
                'class="sgd-label">full-data optimum</text>'
            ),
            '<text x="76" y="566" class="sgd-axis">parameter 1</text>',
            '<rect x="24" y="600" width="592" height="348" rx="18" fill="#fff" stroke="#cfd8d1"/>',
            (
                '<text x="44" y="638" class="sgd-panel">'
                "batch lossは揺れ、full-data lossは傾向を示す</text>"
            ),
        ]
    )
    for tick, label in ((1.0, "1"), (0.1, "0.1"), (0.01, "0.01"), (0.001, "0.001")):
        y = loss_y(tick)
        elements.extend(
            [
                (
                    f'<line x1="{plot_left}" y1="{y:.2f}" x2="{plot_right}" y2="{y:.2f}" '
                    'stroke="#ebe8e0"/>'
                ),
                (
                    f'<text x="{plot_left - 10}" y="{y + 5:.2f}" text-anchor="end" '
                    f'class="sgd-axis">{label}</text>'
                ),
            ]
        )
    for epoch in range(1, int(probe["epochs"])):
        x = update_x(epoch * 8)
        elements.append(
            f'<line x1="{x:.2f}" y1="{loss_top}" x2="{x:.2f}" y2="{loss_bottom}" '
            'stroke="#d8d4ca" stroke-dasharray="4 6"/>'
        )
    elements.extend(
        [
            (
                f'<polyline points="{batch_loss_points}" fill="none" stroke="#d67835" '
                'stroke-width="3" stroke-linejoin="round" opacity="0.9"/>'
            ),
            (
                f'<polyline points="{full_loss_points}" fill="none" stroke="#245c42" '
                'stroke-width="6" stroke-linejoin="round"/>'
            ),
        ]
    )
    for update in (0, 16, 32, 48, 64):
        elements.append(
            f'<text x="{update_x(update):.2f}" y="928" text-anchor="middle" '
            f'class="sgd-axis">{update}</text>'
        )
    elements.extend(
        [
            '<text x="76" y="942" class="sgd-axis">update</text>',
            (
                '<text x="32" y="990" class="sgd-metric">'
                f"full loss {float(probe['initial_loss']):.3f} → "
                f"{float(probe['final_loss']):.4f}</text>"
            ),
            (
                '<text x="608" y="990" text-anchor="end" class="sgd-metric">'
                f"full-loss upward steps {int(probe['upward_full_loss_steps'])} / 63</text>"
            ),
            (
                '<text x="32" y="1032" class="sgd-meta">'
                f"実行生成: fixed LCG shuffle + pure Python mini-batch SGD "
                f"· dataset {html.escape(dataset_version)}</text>"
            ),
            (
                '<text x="32" y="1058" class="sgd-note">'
                "固定線形回帰です。validation、汎化性能、neural network、"
                "SGD一般の性能は示しません。</text>"
            ),
            """
<style>
  .sgd-title { font: 700 22px system-ui, sans-serif; fill: #102a2e; }
  .sgd-subtitle { font: 400 16px system-ui, sans-serif; fill: #45656a; }
  .sgd-panel { font: 700 19px system-ui, sans-serif; fill: #102a2e; }
  .sgd-legend { font: 400 14px system-ui, sans-serif; fill: #45656a; }
  .sgd-axis { font: 400 13px system-ui, sans-serif; fill: #45656a; }
  .sgd-label { font: 700 14px system-ui, sans-serif; fill: #102a2e; }
  .sgd-metric { font: 700 17px system-ui, sans-serif; fill: #102a2e; }
  .sgd-meta { font: 400 11px system-ui, sans-serif; fill: #45656a; }
  .sgd-note { font: 400 11px system-ui, sans-serif; fill: #8b4c3d; }
</style>
""",
            "</svg>\n",
        ]
    )
    return "".join(elements)


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

    width, height = 640, 1080
    plot_left, plot_right = 70.0, 594.0

    def x_project(value: float) -> float:
        return plot_left + (value - float(domain[0])) / (float(domain[1]) - float(domain[0])) * (
            plot_right - plot_left
        )

    curve_top, curve_bottom = 180.0, 430.0

    def curve_y(value: float) -> float:
        return curve_bottom - (value + 1.2) / 3.4 * (curve_bottom - curve_top)

    curve_points = []
    for index in range(161):
        value = float(domain[0]) + index / 160 * (float(domain[1]) - float(domain[0]))
        curve_points.append(f"{x_project(value):.2f},{curve_y(_spatial_objective(value)):.2f}")

    history_rows = [(int(row[0]), float(row[1]), float(row[2]), int(row[3])) for row in history]
    convergence_top, convergence_bottom = 706.0, 925.0
    max_node = max(row[0] for row in history_rows)

    def history_x(node: int) -> float:
        return plot_left + node / max_node * (plot_right - plot_left)

    def history_y(value: float) -> float:
        return convergence_bottom - (value + 4.2) / 4.4 * (convergence_bottom - convergence_top)

    bound_points = " ".join(
        f"{history_x(node):.2f},{history_y(bound):.2f}" for node, bound, _, _ in history_rows
    )
    incumbent_points = " ".join(
        f"{history_x(node):.2f},{history_y(incumbent):.2f}"
        for node, _, incumbent, _ in history_rows
    )

    elements = [
        _svg_open(
            "下界が上がると、捨てられる区間が増える",
            (
                "固定1変数多項式をpure Pythonのinterval arithmetic lower boundで"
                "空間branch-and-boundした実行結果です。目的関数、最終partition、"
                "incumbentとglobal lower boundの履歴を示します。McCormick relaxation、"
                "多変数MINLP、solver一般の性能や有限時間での厳密解を示す図ではありません。"
            ),
            width=width,
            height=height,
        ),
        f'<rect width="{width}" height="{height}" rx="24" fill="#f7f6f1"/>',
        ('<text x="32" y="50" class="sbb-title">下界が上がると、捨てられる区間が増える</text>'),
        (
            '<text x="32" y="82" class="sbb-subtitle">'
            "fixed polynomial · x ∈ [0, 2] · gap tolerance 0.01</text>"
        ),
        '<line x1="36" y1="118" x2="60" y2="118" stroke="#245c42" stroke-width="7"/>',
        '<text x="70" y="124" class="sbb-legend">objective / open region</text>',
        '<rect x="278" y="109" width="22" height="14" rx="3" fill="#bd6754"/>',
        '<text x="310" y="124" class="sbb-legend">boundでprune</text>',
        '<circle cx="468" cy="117" r="7" fill="#d67835"/>',
        '<text x="482" y="124" class="sbb-legend">incumbent</text>',
        '<rect x="24" y="150" width="592" height="330" rx="18" fill="#fff" stroke="#cfd8d1"/>',
        '<text x="44" y="185" class="sbb-panel">固定目的関数と得られたincumbent</text>',
    ]
    for value in (-1.0, 0.0, 1.0, 2.0):
        y = curve_y(value)
        elements.extend(
            [
                (
                    f'<line x1="{plot_left}" y1="{y:.2f}" x2="{plot_right}" y2="{y:.2f}" '
                    'stroke="#ebe8e0"/>'
                ),
                (
                    f'<text x="{plot_left - 10}" y="{y + 5:.2f}" text-anchor="end" '
                    f'class="sbb-axis">{value:g}</text>'
                ),
            ]
        )
    elements.append(
        f'<polyline points="{" ".join(curve_points)}" fill="none" stroke="#245c42" '
        'stroke-width="6" stroke-linejoin="round" stroke-linecap="round"/>'
    )
    best_point = float(probe["best_point"])
    best_value = float(probe["best_value"])
    elements.extend(
        [
            (
                f'<circle cx="{x_project(best_point):.2f}" cy="{curve_y(best_value):.2f}" '
                'r="9" fill="#d67835" stroke="#fff" stroke-width="3"/>'
            ),
            (
                f'<text x="{x_project(best_point) + 14:.2f}" '
                f'y="{curve_y(best_value) - 8:.2f}" class="sbb-label">'
                f"x*={best_point:.2f} · f={best_value:.2f}</text>"
            ),
        ]
    )
    for value in (0.0, 0.5, 1.0, 1.5, 2.0):
        elements.append(
            f'<text x="{x_project(value):.2f}" y="458" text-anchor="middle" '
            f'class="sbb-axis">{value:g}</text>'
        )

    elements.extend(
        [
            '<rect x="24" y="502" width="592" height="152" rx="18" fill="#fff" stroke="#cfd8d1"/>',
            '<text x="44" y="538" class="sbb-panel">停止時の区間partition</text>',
            '<text x="596" y="538" text-anchor="end" class="sbb-status">'
            f"open {len(pending)} · pruned {len(pruned)}</text>",
            '<rect x="70" y="566" width="524" height="38" rx="8" fill="#edf1ed"/>',
        ]
    )
    for lower, upper, _ in pruned:
        x = x_project(float(lower))
        region_width = max(1.0, x_project(float(upper)) - x)
        elements.append(
            f'<rect x="{x:.2f}" y="566" width="{region_width:.2f}" height="38" '
            'fill="#bd6754" opacity="0.82"/>'
        )
    for _, lower, upper in pending:
        x = x_project(float(lower))
        region_width = max(1.0, x_project(float(upper)) - x)
        elements.append(
            f'<rect x="{x:.2f}" y="566" width="{region_width:.2f}" height="38" '
            'fill="#245c42" opacity="0.9"/>'
        )
    elements.extend(
        [
            (
                f'<line x1="{x_project(best_point):.2f}" y1="558" '
                f'x2="{x_project(best_point):.2f}" y2="614" '
                'stroke="#d67835" stroke-width="5"/>'
            ),
            (
                f'<text x="{x_project(best_point):.2f}" y="636" text-anchor="middle" '
                'class="sbb-label">incumbent x=1</text>'
            ),
            '<rect x="24" y="676" width="592" height="302" rx="18" fill="#fff" stroke="#cfd8d1"/>',
            '<text x="44" y="712" class="sbb-panel">nodeを処理するほどglobal boundが上がる</text>',
        ]
    )
    for value in (-4.0, -3.0, -2.0, -1.0, 0.0):
        y = history_y(value)
        elements.extend(
            [
                (
                    f'<line x1="{plot_left}" y1="{y:.2f}" x2="{plot_right}" y2="{y:.2f}" '
                    'stroke="#ebe8e0"/>'
                ),
                (
                    f'<text x="{plot_left - 10}" y="{y + 5:.2f}" text-anchor="end" '
                    f'class="sbb-axis">{value:g}</text>'
                ),
            ]
        )
    elements.extend(
        [
            (
                f'<polyline points="{bound_points}" fill="none" stroke="#245c42" '
                'stroke-width="6" stroke-linejoin="round"/>'
            ),
            (
                f'<polyline points="{incumbent_points}" fill="none" stroke="#d67835" '
                'stroke-width="5" stroke-linejoin="round"/>'
            ),
        ]
    )
    for node in (0, 20, 40, 60, max_node):
        elements.append(
            f'<text x="{history_x(node):.2f}" y="952" text-anchor="middle" '
            f'class="sbb-axis">{node}</text>'
        )
    elements.extend(
        [
            '<text x="70" y="968" class="sbb-axis">processed nodes</text>',
            (f'<text x="32" y="1012" class="sbb-metric">incumbent {best_value:.3f}</text>'),
            (
                '<text x="320" y="1012" text-anchor="middle" class="sbb-metric">'
                f"global bound {float(probe['global_bound']):.3f}</text>"
            ),
            (
                '<text x="608" y="1012" text-anchor="end" class="sbb-metric">'
                f"gap {float(probe['absolute_gap']):.4f}</text>"
            ),
            (
                '<text x="32" y="1047" class="sbb-meta">'
                f"実行生成: interval arithmetic lower bound + deterministic best-bound search "
                f"· dataset {html.escape(dataset_version)}</text>"
            ),
            (
                '<text x="32" y="1070" class="sbb-note">'
                "固定1変数教材です。McCormick relaxation、多変数MINLP、"
                "solver一般の性能は示しません。</text>"
            ),
            """
<style>
  .sbb-title { font: 700 22px system-ui, sans-serif; fill: #102a2e; }
  .sbb-subtitle { font: 400 16px system-ui, sans-serif; fill: #45656a; }
  .sbb-panel { font: 700 19px system-ui, sans-serif; fill: #102a2e; }
  .sbb-status, .sbb-legend { font: 400 14px system-ui, sans-serif; fill: #45656a; }
  .sbb-axis { font: 400 13px system-ui, sans-serif; fill: #45656a; }
  .sbb-label { font: 700 14px system-ui, sans-serif; fill: #102a2e; }
  .sbb-metric { font: 700 17px system-ui, sans-serif; fill: #102a2e; }
  .sbb-meta { font: 400 11px system-ui, sans-serif; fill: #45656a; }
  .sbb-note { font: 400 11px system-ui, sans-serif; fill: #8b4c3d; }
</style>
""",
            "</svg>\n",
        ]
    )
    return "".join(elements)


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
    plot_x, plot_width, plot_height = 76.0, 500.0, 205.0
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
    ) -> list[str]:
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
        plot_y = panel_y + 58
        segment0 = (
            (project_x(0.0), project_y(float(probe["initial_state"]), plot_y)),
            (project_x(0.5), project_y(end0, plot_y)),
        )
        segment1 = (
            (project_x(0.5), project_y(state1, plot_y)),
            (project_x(1.0), project_y(end1, plot_y)),
        )
        result = [
            (
                f'<rect x="24" y="{panel_y}" width="592" height="338" rx="18" '
                'fill="#fff" stroke="#cfd8d1"/>'
            ),
            f'<text x="44" y="{panel_y + 35}" class="ms-panel">{html.escape(title)}</text>',
            (
                f'<text x="596" y="{panel_y + 35}" text-anchor="end" class="ms-status">'
                f"u=[{control0:.2f}, {control1:.2f}] · "
                f"‖defect‖={float(payload['defect_norm']):.3f}</text>"
            ),
            (
                f'<rect x="{plot_x}" y="{plot_y}" width="{plot_width}" '
                f'height="{plot_height}" rx="12" fill="#fbfcfa"/>'
            ),
        ]
        for value in (0.0, 0.5, 1.0, 1.25):
            y = project_y(value, plot_y)
            result.extend(
                [
                    (
                        f'<line x1="{plot_x}" y1="{y:.2f}" x2="{plot_x + plot_width}" '
                        f'y2="{y:.2f}" stroke="#ebe8e0"/>'
                    ),
                    (
                        f'<text x="{plot_x - 10}" y="{y + 6:.2f}" text-anchor="end" '
                        f'class="ms-axis">{value:g}</text>'
                    ),
                ]
            )
        for time, label in ((0.0, "t₀"), (0.5, "boundary"), (1.0, "target")):
            result.append(
                f'<text x="{project_x(time):.2f}" y="{plot_y + plot_height + 27}" '
                f'text-anchor="middle" class="ms-axis">{label}</text>'
            )
        for points in (segment0, segment1):
            result.append(
                f'<line x1="{points[0][0]:.2f}" y1="{points[0][1]:.2f}" '
                f'x2="{points[1][0]:.2f}" y2="{points[1][1]:.2f}" '
                'stroke="#245c42" stroke-width="7" stroke-linecap="round"/>'
            )
        for time, state, label in (
            (0.0, float(probe["initial_state"]), "x₀"),
            (0.5, state1, "decision x₁"),
            (1.0, float(probe["target_state"]), "target"),
        ):
            label_y = project_y(state, plot_y) - 15
            label_anchor = "middle"
            label_x = project_x(time)
            if show_defects and time == 1.0:
                label_y = project_y(state, plot_y) + 24
                label_anchor = "end"
                label_x += 20
            result.extend(
                [
                    (
                        f'<circle cx="{project_x(time):.2f}" cy="{project_y(state, plot_y):.2f}" '
                        'r="8" fill="#d67835" stroke="#fff" stroke-width="3"/>'
                    ),
                    (
                        f'<text x="{label_x:.2f}" y="{label_y:.2f}" '
                        f'text-anchor="{label_anchor}" class="ms-label">{label}</text>'
                    ),
                ]
            )
        if show_defects:
            for time, start, stop, label in (
                (0.5, end0, state1, f"δ₀={defect0:.2f}"),
                (1.0, end1, float(probe["target_state"]), f"δ₁={defect1:+.2f}"),
            ):
                x = project_x(time)
                y1, y2 = project_y(start, plot_y), project_y(stop, plot_y)
                result.extend(
                    [
                        (
                            f'<line x1="{x:.2f}" y1="{y1:.2f}" x2="{x:.2f}" y2="{y2:.2f}" '
                            'stroke="#bd6754" stroke-width="5" stroke-dasharray="7 5"/>'
                        ),
                        (
                            f'<text x="{x - 12:.2f}" y="{(y1 + y2) / 2 + 5:.2f}" '
                            f'text-anchor="end" class="ms-defect">{label}</text>'
                        ),
                    ]
                )
        return result

    elements = [
        _svg_open(
            "短いrolloutは、境界がつながって初めて一本の軌道になる",
            (
                "記事と同じ1 state、2 segment、segment duration 0.5の固定Multiple "
                "Shooting問題です。初期guessと、同じlinear continuity constraintsを"
                "exact equality KKTで解いた結果を比較します。segment rollout endpointと"
                "境界state decisionのずれ、terminal targetのずれ、defect norm、control "
                "costを示します。SciPy SLSQP自体の実行結果、非線形dynamics、path制約、"
                "一般的な収束性能は示しません。"
            ),
            width=640,
            height=1080,
        ),
        '<rect width="640" height="1080" rx="24" fill="#f7f6f1"/>',
        (
            '<text x="32" y="50" class="ms-title">'
            "短いrolloutは、境界がつながって初めて一本の軌道になる</text>"
        ),
        (
            '<text x="32" y="82" class="ms-subtitle">'
            "1 state · 2 segments · duration 0.5 · target 1.0"
            "</text>"
        ),
        '<line x1="36" y1="116" x2="76" y2="116" stroke="#245c42" stroke-width="7"/>',
        '<text x="86" y="122" class="ms-legend">segment rollout</text>',
        '<circle cx="266" cy="116" r="8" fill="#d67835"/>',
        '<text x="284" y="122" class="ms-legend">state decision</text>',
        (
            '<line x1="458" y1="102" x2="458" y2="128" stroke="#bd6754" '
            'stroke-width="5" stroke-dasharray="7 5"/>'
        ),
        '<text x="474" y="122" class="ms-legend">defect</text>',
    ]
    elements.extend(panel("初期guess", initial, 148.0, show_defects=True))
    elements.extend(panel("continuity solve後", solved, 510.0, show_defects=False))
    elements.extend(
        [
            (
                '<text x="32" y="904" class="ms-result">'
                f"objective {float(initial['objective']):.2f} → "
                f"{float(solved['objective']):.2f}</text>"
            ),
            (
                '<text x="608" y="904" text-anchor="end" class="ms-result">'
                f"defect norm {float(initial['defect_norm']):.3f} → "
                f"{float(solved['defect_norm']):.1f}</text>"
            ),
            (
                '<text x="32" y="958" class="ms-provenance">'
                "実行生成: fixed linear segment integration + exact equality KKT solve"
                f" · dataset {html.escape(dataset_version)}</text>"
            ),
            (
                '<text x="32" y="1002" class="ms-caveat">'
                "記事と同じ2-segment定式化です。SciPy SLSQP自体の実行結果ではありません。"
                "</text>"
            ),
            (
                '<text x="32" y="1032" class="ms-caveat">'
                "非線形dynamics、path制約、積分誤差、solverの一般性能を示しません。</text>"
            ),
            (
                '<text x="32" y="1060" class="ms-caveat">'
                "実務ではsegment分割と積分toleranceを変えて再検証します。</text>"
            ),
            (
                "<style>"
                "text{font-family:system-ui,-apple-system,'Segoe UI',sans-serif;fill:#26352d}"
                ".ms-title{font-size:25px;font-weight:760}"
                ".ms-subtitle{font-size:17px;fill:#617068}"
                ".ms-legend{font-size:16px;fill:#46554d}"
                ".ms-panel{font-size:22px;font-weight:750}"
                ".ms-status{font-size:16px;fill:#617068;font-variant-numeric:tabular-nums}"
                ".ms-axis{font-size:16px;fill:#617068;font-variant-numeric:tabular-nums}"
                ".ms-label{font-size:15px;font-weight:700}"
                ".ms-defect{font-size:15px;fill:#a33d30;font-weight:700}"
                ".ms-result{font-size:18px;font-weight:750;font-variant-numeric:tabular-nums}"
                ".ms-provenance{font-size:14px;fill:#617068}"
                ".ms-caveat{font-size:14px;fill:#7a4b38}"
                "</style>"
            ),
            "</svg>\n",
        ]
    )
    return "".join(elements)


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
    plot_x, plot_width = 68.0, 536.0
    state_y, state_height = 318.0, 285.0
    state_min, state_max = -2.8, 2.1
    control_y, control_height = 760.0, 145.0
    control_limit = max(abs(value) for value in controls)

    def project_x(step: int) -> float:
        return plot_x + step / 40 * plot_width

    def project_state(value: float) -> float:
        bounded = min(state_max, max(state_min, value))
        return (
            state_y + state_height - (bounded - state_min) / (state_max - state_min) * state_height
        )

    def project_control(value: float) -> float:
        return control_y + control_height / 2 - value / control_limit * control_height * 0.43

    position_points = [
        (project_x(index), project_state(state[0])) for index, state in enumerate(states)
    ]
    velocity_points = [
        (project_x(index), project_state(state[1])) for index, state in enumerate(states)
    ]
    uncontrolled_points = [(project_x(index), project_state(2.0)) for index in range(41)]
    control_points = [
        (project_x(index), project_control(value)) for index, value in enumerate(controls)
    ]

    def polyline(points: list[tuple[float, float]], color: str, dash: str = "") -> str:
        coordinates = " ".join(f"{x:.2f},{y:.2f}" for x, y in points)
        dash_attribute = f' stroke-dasharray="{dash}"' if dash else ""
        return (
            f'<polyline points="{coordinates}" fill="none" stroke="{color}" '
            'stroke-width="5" stroke-linecap="round" stroke-linejoin="round"'
            f"{dash_attribute}/>"
        )

    terminal_position, terminal_velocity = states[-1]
    first_gain, middle_gain, final_gain = gains[0], gains[20], gains[-1]
    elements = [
        _svg_open(
            "backward passのgainがforward rolloutを変える",
            (
                "記事のPython例と同じ2 state、1 control、40 stepの有限horizon linear LQR"
                "部分問題をpure Pythonで実行した結果です。backward passで時刻別feedback "
                "gainを求め、初期state [2, 0]からforward rolloutします。stateとcontrolの"
                "履歴、terminal state、maximum controlを示します。非線形iLQR/DDP反復、"
                "regularization、line search、一般制約、実時間性能は含みません。"
            ),
            width=640,
            height=1080,
        ),
        '<rect width="640" height="1080" rx="24" fill="#f7f6f1"/>',
        '<text x="32" y="50" class="lqr-title">backward passのgainがforward rolloutを変える</text>',
        (
            '<text x="32" y="82" class="lqr-subtitle">'
            "2 state · 1 control · horizon 40 · dt 0.1 · target [0, 0]"
            "</text>"
        ),
        '<text x="32" y="128" class="lqr-section">terminal costから時刻別gainへ</text>',
        '<rect x="24" y="150" width="592" height="118" rx="18" fill="#fff" stroke="#cfd8d1"/>',
        '<text x="48" y="183" class="lqr-small-label">backward</text>',
        '<text x="48" y="218" class="lqr-gain">K₃₉</text>',
        (
            '<text x="48" y="246" class="lqr-gain-value">'
            f"[{final_gain[0]:.3f}, {final_gain[1]:.3f}]</text>"
        ),
        '<text x="201" y="225" class="lqr-arrow">→</text>',
        '<text x="251" y="218" class="lqr-gain">K₂₀</text>',
        (
            '<text x="251" y="246" class="lqr-gain-value">'
            f"[{middle_gain[0]:.3f}, {middle_gain[1]:.3f}]</text>"
        ),
        '<text x="404" y="225" class="lqr-arrow">→</text>',
        '<text x="454" y="218" class="lqr-gain">K₀</text>',
        (
            '<text x="454" y="246" class="lqr-gain-value">'
            f"[{first_gain[0]:.3f}, {first_gain[1]:.3f}]</text>"
        ),
        '<text x="32" y="302" class="lqr-section">forward rolloutのstate</text>',
        (
            f'<rect x="{plot_x}" y="{state_y}" width="{plot_width}" height="{state_height}" '
            'rx="14" fill="#fff" stroke="#cfd8d1"/>'
        ),
    ]
    for value in (-2.0, -1.0, 0.0, 1.0, 2.0):
        y = project_state(value)
        elements.extend(
            [
                (
                    f'<line x1="{plot_x}" y1="{y:.2f}" x2="{plot_x + plot_width}" '
                    f'y2="{y:.2f}" stroke="#ebe8e0"/>'
                ),
                (
                    f'<text x="{plot_x - 10}" y="{y + 6:.2f}" text-anchor="end" '
                    f'class="lqr-axis">{value:g}</text>'
                ),
            ]
        )
    for step in (0, 10, 20, 30, 40):
        x = project_x(step)
        elements.append(
            f'<text x="{x:.2f}" y="{state_y + state_height + 27}" '
            f'text-anchor="middle" class="lqr-axis">{step}</text>'
        )
    elements.extend(
        [
            polyline(uncontrolled_points, "#9aa49e", "9 7"),
            polyline(position_points, "#245c42"),
            polyline(velocity_points, "#d67835"),
            '<line x1="36" y1="658" x2="76" y2="658" stroke="#245c42" stroke-width="5"/>',
            '<text x="84" y="664" class="lqr-legend">position</text>',
            '<line x1="190" y1="658" x2="230" y2="658" stroke="#d67835" stroke-width="5"/>',
            '<text x="238" y="664" class="lqr-legend">velocity</text>',
            (
                '<line x1="344" y1="658" x2="384" y2="658" stroke="#9aa49e" '
                'stroke-width="4" stroke-dasharray="9 7"/>'
            ),
            '<text x="392" y="664" class="lqr-legend">u=0 position</text>',
            (
                '<text x="32" y="708" class="lqr-result">'
                f"terminal state [{terminal_position:.5f}, {terminal_velocity:.5f}]"
                "</text>"
            ),
            (
                '<text x="608" y="708" text-anchor="end" class="lqr-result">'
                f"max |u| {control_limit:.3f}</text>"
            ),
            '<text x="32" y="746" class="lqr-section">forward rolloutのcontrol</text>',
            (
                f'<rect x="{plot_x}" y="{control_y}" width="{plot_width}" '
                f'height="{control_height}" rx="14" fill="#fff" stroke="#cfd8d1"/>'
            ),
            (
                f'<line x1="{plot_x}" y1="{project_control(0.0):.2f}" '
                f'x2="{plot_x + plot_width}" y2="{project_control(0.0):.2f}" '
                'stroke="#cfd8d1"/>'
            ),
            (
                f'<text x="{plot_x - 10}" y="{project_control(control_limit) + 6:.2f}" '
                'text-anchor="end" class="lqr-axis">+15</text>'
            ),
            (
                f'<text x="{plot_x - 10}" y="{project_control(0.0) + 6:.2f}" '
                'text-anchor="end" class="lqr-axis">0</text>'
            ),
            (
                f'<text x="{plot_x - 10}" y="{project_control(-control_limit) + 6:.2f}" '
                'text-anchor="end" class="lqr-axis">−15</text>'
            ),
            polyline(control_points, "#7e5f98"),
        ]
    )
    for step in (0, 10, 20, 30, 39):
        x = project_x(step)
        elements.append(
            f'<text x="{x:.2f}" y="{control_y + control_height + 27}" '
            f'text-anchor="middle" class="lqr-axis">{step}</text>'
        )
    elements.extend(
        [
            '<line x1="36" y1="954" x2="76" y2="954" stroke="#7e5f98" stroke-width="5"/>',
            '<text x="84" y="960" class="lqr-legend">feedback control uₖ</text>',
            (
                '<text x="32" y="1002" class="lqr-provenance">'
                "実行生成: finite-horizon Riccati backward pass + closed-loop forward rollout"
                f" · dataset {html.escape(dataset_version)}</text>"
            ),
            (
                '<text x="32" y="1032" class="lqr-caveat">'
                "記事のlinear LQR部分問題です。非線形iLQR/DDP反復や制約処理は含みません。"
                "</text>"
            ),
            (
                '<text x="32" y="1058" class="lqr-caveat">'
                "この1例から一般的な収束速度、安定性、real-time性能を判断できません。</text>"
            ),
            (
                "<style>"
                "text{font-family:system-ui,-apple-system,'Segoe UI',sans-serif;fill:#26352d}"
                ".lqr-title{font-size:26px;font-weight:760}"
                ".lqr-subtitle{font-size:17px;fill:#617068}"
                ".lqr-section{font-size:21px;font-weight:750}"
                ".lqr-small-label{font-size:14px;fill:#617068}"
                ".lqr-gain{font-size:20px;font-weight:750}"
                ".lqr-gain-value{font-size:16px;fill:#46554d;font-variant-numeric:tabular-nums}"
                ".lqr-arrow{font-size:24px;fill:#9a6b45}"
                ".lqr-axis{font-size:16px;fill:#617068;font-variant-numeric:tabular-nums}"
                ".lqr-legend{font-size:16px;fill:#46554d}"
                ".lqr-result{font-size:17px;font-weight:700;font-variant-numeric:tabular-nums}"
                ".lqr-provenance{font-size:14px;fill:#617068}"
                ".lqr-caveat{font-size:14px;fill:#7a4b38}"
                "</style>"
            ),
            "</svg>\n",
        ]
    )
    return "".join(elements)


def _so3_update_svg(dataset_version: str) -> str:
    traces = {
        str(trace.parameters["strategy"]): trace
        for trace in generate_so3_traces(dataset_version=dataset_version)
    }
    projected = traces["projected"]
    riemannian = traces["riemannian"]
    plot_x, plot_y, plot_width, plot_height = 70.0, 190.0, 520.0, 245.0
    angle_max = 2.8

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

    def metric_max(trace: AlgorithmTrace, metric_id: str) -> float:
        return max(_metric_value(frame, metric_id) for frame in trace.frames)

    def line(points: list[tuple[float, float]], color: str, dash: str = "") -> str:
        coordinates = " ".join(f"{x:.2f},{y:.2f}" for x, y in points)
        dash_attribute = f' stroke-dasharray="{dash}"' if dash else ""
        return (
            f'<polyline points="{coordinates}" fill="none" stroke="{color}" '
            'stroke-width="6" stroke-linecap="round" stroke-linejoin="round"'
            f"{dash_attribute}/>"
        )

    projected_history = history_points(projected)
    riemannian_history = history_points(riemannian)
    projected_first = projected.frames[1]
    riemannian_first = riemannian.frames[1]
    projected_final = projected.frames[-1]
    riemannian_final = riemannian.frames[-1]
    elements = [
        _svg_open(
            "SO(3)へ戻る二つの一歩は、同じではない",
            (
                "identityから同じnear-pi targetへ向かう固定Python実行です。"
                "Projected Gradientはambient step後にQR projectionし、Riemann勾配法は"
                "Lie algebra上の接空間stepをexponential mapで戻します。12 updateの"
                "geodesic residual、最初のmap correction、accepted rotationの直交性と"
                "determinant残差を比較します。固定3対応、noiseなし、固定stepの教材であり、"
                "一般性能rankingではありません。"
            ),
            width=640,
            height=1080,
        ),
        '<rect width="640" height="1080" rx="24" fill="#f7f6f1"/>',
        '<text x="32" y="50" class="so-title">SO(3)へ戻る二つの一歩は、同じではない</text>',
        (
            '<text x="32" y="82" class="so-subtitle">'
            "identity → near-π target · fixed step 0.35 · 12 updates"
            "</text>"
        ),
        '<line x1="36" y1="116" x2="78" y2="116" stroke="#d67835" stroke-width="6"/>',
        '<text x="88" y="122" class="so-legend">ambient + QR projection</text>',
        (
            '<line x1="336" y1="116" x2="378" y2="116" stroke="#245c42" '
            'stroke-width="6" stroke-dasharray="10 7"/>'
        ),
        '<text x="388" y="122" class="so-legend">tangent + exp map</text>',
        '<text x="32" y="162" class="so-section">targetまでのgeodesic residual</text>',
        (
            f'<rect x="{plot_x}" y="{plot_y}" width="{plot_width}" height="{plot_height}" '
            'rx="14" fill="#fff" stroke="#cfd8d1"/>'
        ),
    ]
    for angle in (0.0, 1.0, 2.0, 2.8):
        y = plot_y + plot_height - angle / angle_max * plot_height
        elements.extend(
            [
                (
                    f'<line x1="{plot_x}" y1="{y:.2f}" x2="{plot_x + plot_width}" '
                    f'y2="{y:.2f}" stroke="#ebe8e0"/>'
                ),
                (
                    f'<text x="{plot_x - 12}" y="{y + 6:.2f}" text-anchor="end" '
                    f'class="so-axis">{angle:g}</text>'
                ),
            ]
        )
    for evaluation in (0, 4, 8, 12):
        x = plot_x + evaluation / 12 * plot_width
        elements.extend(
            [
                (
                    f'<line x1="{x:.2f}" y1="{plot_y}" x2="{x:.2f}" '
                    f'y2="{plot_y + plot_height}" stroke="#f1efe9"/>'
                ),
                (
                    f'<text x="{x:.2f}" y="{plot_y + plot_height + 28}" '
                    f'text-anchor="middle" class="so-axis">{evaluation}</text>'
                ),
            ]
        )
    elements.extend(
        [
            line(projected_history, "#d67835"),
            line(riemannian_history, "#245c42", "10 7"),
        ]
    )
    for points, color in (
        (projected_history, "#d67835"),
        (riemannian_history, "#245c42"),
    ):
        for index in (0, 4, 12):
            x, y = points[index]
            elements.append(
                f'<circle cx="{x:.2f}" cy="{y:.2f}" r="6" fill="{color}" '
                'stroke="#fff" stroke-width="3"/>'
            )
    elements.extend(
        [
            (
                '<text x="70" y="485" class="so-result">'
                f"QR: 2.800 → {_metric_value(projected_final, 'geodesic_residual'):.3f} rad"
                "</text>"
            ),
            (
                '<text x="590" y="485" text-anchor="end" class="so-result">'
                f"Riemann: 2.800 → {_metric_value(riemannian_final, 'geodesic_residual'):.3f} rad"
                "</text>"
            ),
            '<text x="32" y="535" class="so-section">最初のupdateを分解する</text>',
            '<rect x="24" y="558" width="592" height="154" rx="18" fill="#fff" stroke="#cfd8d1"/>',
            '<circle cx="58" cy="600" r="13" fill="#d67835"/>',
            '<text x="82" y="607" class="so-card-title">Projected Gradient</text>',
            '<text x="82" y="638" class="so-card">ambient step ‖Δ‖ 0.976</text>',
            '<text x="278" y="638" class="so-arrow">→</text>',
            '<text x="312" y="638" class="so-card">QR correction 1.136</text>',
            '<text x="504" y="638" class="so-arrow">→</text>',
            '<text x="540" y="638" class="so-card">accepted R</text>',
            (
                '<text x="82" y="678" class="so-card-note">'
                f"accepted angle {_metric_value(projected_first, 'geodesic_residual'):.3f} rad"
                "</text>"
            ),
            '<rect x="24" y="730" width="592" height="154" rx="18" fill="#fff" stroke="#cfd8d1"/>',
            '<circle cx="58" cy="772" r="13" fill="#245c42"/>',
            '<text x="82" y="779" class="so-card-title">Riemannian Gradient</text>',
            '<text x="82" y="810" class="so-card">tangent step ‖ξ‖ 0.980</text>',
            '<text x="278" y="810" class="so-arrow">→</text>',
            '<text x="312" y="810" class="so-card">1次近似との差 0.661</text>',
            '<text x="504" y="810" class="so-arrow">→</text>',
            '<text x="540" y="810" class="so-card">accepted R</text>',
            (
                '<text x="82" y="850" class="so-card-note">'
                f"accepted angle {_metric_value(riemannian_first, 'geodesic_residual'):.3f} rad"
                "</text>"
            ),
            '<text x="32" y="928" class="so-section">accepted rotationの構造残差</text>',
            (
                '<text x="32" y="962" class="so-structure">'
                f"QR max: orthogonality {_metric(metric_max(projected, 'orthogonality_error'))}"
                f" · determinant {_metric(metric_max(projected, 'determinant_error'))}</text>"
            ),
            (
                '<text x="32" y="990" class="so-structure">'
                "Riemann max: orthogonality "
                f"{_metric(metric_max(riemannian, 'orthogonality_error'))}"
                f" · determinant {_metric(metric_max(riemannian, 'determinant_error'))}</text>"
            ),
            (
                '<text x="32" y="1026" class="so-provenance">'
                "実行生成: optimization_compass.constraint_geometry.generate_so3_traces"
                f" · dataset {html.escape(dataset_version)}</text>"
            ),
            (
                '<text x="32" y="1056" class="so-caveat">'
                "固定3対応・noiseなし・固定stepです。速度rankingや一般的な局所収束を示しません。"
                "</text>"
            ),
            (
                "<style>"
                "text{font-family:system-ui,-apple-system,'Segoe UI',sans-serif;fill:#26352d}"
                ".so-title{font-size:27px;font-weight:760}"
                ".so-subtitle{font-size:17px;fill:#617068}"
                ".so-legend{font-size:16px;fill:#46554d}"
                ".so-section{font-size:21px;font-weight:750}"
                ".so-axis{font-size:16px;fill:#617068;font-variant-numeric:tabular-nums}"
                ".so-result{font-size:17px;font-weight:700;font-variant-numeric:tabular-nums}"
                ".so-card-title{font-size:20px;font-weight:750}"
                ".so-card{font-size:17px;font-variant-numeric:tabular-nums}"
                ".so-card-note{font-size:16px;fill:#617068;font-variant-numeric:tabular-nums}"
                ".so-arrow{font-size:22px;fill:#9a6b45}"
                ".so-structure{font-size:16px;font-variant-numeric:tabular-nums}"
                ".so-provenance{font-size:14px;fill:#617068}"
                ".so-caveat{font-size:14px;fill:#7a4b38}"
                "</style>"
            ),
            "</svg>\n",
        ]
    )
    return "".join(elements)


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
        ("初期parameter", initial, "#d67835", ' stroke-dasharray="10 7"', 145.0),
        ("12評価後", final, "#245c42", "", 435.0),
    )
    plot_x, plot_width, plot_height = 64.0, 518.0, 190.0
    response_min, response_max = 0.0, 2.2

    def project_x(time: float) -> float:
        return plot_x + (time - time_start) / (time_stop - time_start) * plot_width

    def project_y(response: float, plot_y: float) -> float:
        return (
            plot_y
            + plot_height
            - (response - response_min) / (response_max - response_min) * plot_height
        )

    elements = [
        _svg_open(
            "曲線が重なっても、診断は終わらない",
            (
                "20点のnoiseless合成dataに3 parameter指数減衰modelを当てる固定Python診断"
                "probeです。初期parameterと12評価後の予測曲線、観測別residual、residual "
                "norm、既知truthからのparameter距離を比較します。12評価後のcurveは観測へ"
                "近づきますが、停止criterionには到達していません。LMやSciPy solverの実行"
                "結果ではありません。"
            ),
            width=640,
            height=1120,
        ),
        '<rect width="640" height="1120" rx="24" fill="#f7f6f1"/>',
        '<text x="32" y="48" class="ls-title">曲線が重なっても、診断は終わらない</text>',
        (
            '<text x="32" y="78" class="ls-subtitle">'
            "20 observations · noiseless · a exp(-k t)+c · 12 evaluation budget"
            "</text>"
        ),
        '<circle cx="42" cy="108" r="7" fill="#245c42" stroke="#fff" stroke-width="3"/>',
        '<text x="58" y="114" class="ls-legend">observations</text>',
        '<line x1="194" y1="108" x2="232" y2="108" stroke="#d67835" stroke-width="5"/>',
        '<text x="240" y="114" class="ls-legend">model curve</text>',
        '<line x1="382" y1="94" x2="382" y2="120" stroke="#bd6754" stroke-width="3"/>',
        '<text x="394" y="114" class="ls-legend">point residual</text>',
    ]

    for panel_title, frame, color, dash, panel_y in panel_specs:
        plot_y = panel_y + 57
        parameters = [float(value) for value in frame.points[0].coordinates]
        amplitude, rate, offset = parameters
        predictions = [amplitude * math.exp(-rate * time) + offset for time in times]
        curve_points = " ".join(
            f"{project_x(time):.2f},{project_y(prediction, plot_y):.2f}"
            for time, prediction in zip(times, predictions, strict=True)
        )
        metrics = {metric.metric_id: float(metric.value) for metric in frame.metrics}
        elements.extend(
            [
                (
                    f'<rect x="24" y="{panel_y}" width="592" height="272" rx="18" '
                    'fill="#fff" stroke="#cfd8d1"/>'
                ),
                (
                    f'<text x="44" y="{panel_y + 32}" class="ls-panel">'
                    f"{html.escape(panel_title)}</text>"
                ),
                (
                    f'<text x="596" y="{panel_y + 32}" text-anchor="end" class="ls-status">'
                    f"a={amplitude:.3f} · k={rate:.3f} · c={offset:.3f} · "
                    f"‖r‖={metrics['residual_norm']:.3f}</text>"
                ),
                (
                    f'<rect x="{plot_x}" y="{plot_y}" width="{plot_width}" '
                    f'height="{plot_height}" rx="12" fill="#fbfcfa"/>'
                ),
            ]
        )
        for response in (0.0, 1.0, 2.0):
            tick_y = project_y(response, plot_y)
            elements.extend(
                [
                    (
                        f'<line x1="{plot_x}" y1="{tick_y:.2f}" '
                        f'x2="{plot_x + plot_width}" y2="{tick_y:.2f}" '
                        'stroke="#ebe8e0"/>'
                    ),
                    (
                        f'<text x="{plot_x - 10}" y="{tick_y + 6:.2f}" '
                        f'text-anchor="end" class="ls-axis">{response:g}</text>'
                    ),
                ]
            )
        for time, observation, prediction in zip(times, observations, predictions, strict=True):
            x = project_x(time)
            observation_y = project_y(observation, plot_y)
            prediction_y = project_y(prediction, plot_y)
            elements.append(
                f'<line x1="{x:.2f}" y1="{observation_y:.2f}" '
                f'x2="{x:.2f}" y2="{prediction_y:.2f}" '
                'stroke="#bd6754" stroke-width="3" opacity="0.72"/>'
            )
        elements.append(
            f'<polyline points="{curve_points}" fill="none" stroke="{color}" '
            f'stroke-width="5" stroke-linecap="round" stroke-linejoin="round"{dash}/>'
        )
        for time, observation in zip(times, observations, strict=True):
            elements.append(
                f'<circle cx="{project_x(time):.2f}" '
                f'cy="{project_y(observation, plot_y):.2f}" r="6" '
                'fill="#245c42" stroke="#fff" stroke-width="2"/>'
            )
        for tick in (0.0, 2.5, 5.0):
            tick_x = project_x(tick)
            elements.append(
                f'<text x="{tick_x:.2f}" y="{plot_y + plot_height + 25}" '
                f'text-anchor="middle" class="ls-axis">{tick:g}</text>'
            )

    history_y, history_height = 790.0, 120.0
    history_x, history_width = 64.0, 518.0
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

    residual_history = [history_point(frame, "residual_norm") for frame in trace.frames]
    parameter_history = [history_point(frame, "parameter_error") for frame in trace.frames]
    elements.extend(
        [
            '<text x="32" y="754" class="ls-summary">curveの下で追う診断値</text>',
            (
                f'<rect x="{history_x}" y="{history_y}" width="{history_width}" '
                f'height="{history_height}" rx="12" fill="#fff" stroke="#cfd8d1"/>'
            ),
        ]
    )
    for exponent in (-2, -1, 0):
        y = history_y + history_height - (exponent - log_min) / (log_max - log_min) * history_height
        elements.extend(
            [
                (
                    f'<line x1="{history_x}" y1="{y:.2f}" '
                    f'x2="{history_x + history_width}" y2="{y:.2f}" '
                    'stroke="#ebe8e0"/>'
                ),
                (
                    f'<text x="{history_x - 10}" y="{y + 6:.2f}" '
                    f'text-anchor="end" class="ls-axis">1e{exponent}</text>'
                ),
            ]
        )
    for points, color in (
        (residual_history, "#245c42"),
        (parameter_history, "#d67835"),
    ):
        point_string = " ".join(f"{x:.2f},{y:.2f}" for x, y in points)
        elements.append(
            f'<polyline points="{point_string}" fill="none" stroke="{color}" '
            'stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>'
        )
        for x, y in points:
            elements.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="4" fill="{color}"/>')
    elements.extend(
        [
            '<line x1="64" y1="944" x2="102" y2="944" stroke="#245c42" stroke-width="5"/>',
            '<text x="112" y="950" class="ls-legend">residual norm 1.867 → 0.034</text>',
            '<line x1="344" y1="944" x2="382" y2="944" stroke="#d67835" stroke-width="5"/>',
            '<text x="392" y="950" class="ls-legend">parameter error 0.890 → 0.036</text>',
            (
                '<text x="32" y="990" class="ls-provenance">'
                "実行生成: generate_parameter_estimation_traces</text>"
            ),
            (
                '<text x="32" y="1018" class="ls-provenance">'
                "solver-independent damped Gauss–Newton probe · "
                f"dataset {html.escape(dataset_version)}</text>"
            ),
            (
                '<text x="32" y="1060" class="ls-caveat">'
                "20点・noiseなしの合成dataです。LM／SciPyの実行結果ではありません。</text>"
            ),
            (
                '<text x="32" y="1088" class="ls-caveat">'
                "識別性、統計的妥当性、実dataへの適合を保証しません。</text>"
            ),
            (
                "<style>"
                "text{font-family:system-ui,-apple-system,'Segoe UI',sans-serif;fill:#26352d}"
                ".ls-title{font-size:30px;font-weight:760}"
                ".ls-subtitle{font-size:17px;fill:#617068}"
                ".ls-legend{font-size:17px;fill:#46554d}"
                ".ls-panel{font-size:23px;font-weight:750}"
                ".ls-status{font-size:17px;fill:#617068;font-variant-numeric:tabular-nums}"
                ".ls-axis{font-size:18px;fill:#617068;font-variant-numeric:tabular-nums}"
                ".ls-summary{font-size:21px;font-weight:750}"
                ".ls-provenance{font-size:15px;fill:#617068}"
                ".ls-caveat{font-size:15px;fill:#7a4b38}"
                "</style>"
            ),
            "</svg>\n",
        ]
    )
    return "".join(elements)


def _bayesian_optimization_svg(dataset_version: str) -> str:
    generated = generate_surrogate_scenario(
        dataset_version=dataset_version,
        strategy="explore",
        noise_preset="noiseless",
    )
    frames = (generated.payload.frames[0], generated.payload.frames[3])
    panel_specs = (
        ("初期観測の直後", frames[0], 145.0),
        ("3点を追加した後", frames[1], 545.0),
    )
    domain_min, domain_max = generated.payload.domain
    value_min, value_max = -1.3, 4.0
    plot_x, plot_width, plot_height = 58.0, 530.0, 200.0
    acquisition_height = 72.0

    def project_x(value: float) -> float:
        return plot_x + (value - domain_min) / (domain_max - domain_min) * plot_width

    def project_y(value: float, plot_y: float) -> float:
        bounded = min(value_max, max(value_min, value))
        return plot_y + plot_height - (bounded - value_min) / (value_max - value_min) * plot_height

    elements = [
        _svg_open(
            "観測が増えると、次の評価点も動く",
            (
                "固定seedの1次元black-boxをGaussian-process Bayesian Optimizationで実行し、"
                "3回評価後と6回評価後のsurrogate平均、不確実性、Expected Improvement、"
                "次の評価点を比較します。真の目的関数は教材用の答え合わせであり、"
                "optimizerは観測点以外の真値を参照しません。"
            ),
            width=640,
            height=1100,
        ),
        '<rect width="640" height="1100" rx="24" fill="#f7f6f1"/>',
        '<text x="32" y="48" class="bo-title">観測が増えると、次の評価点も動く</text>',
        (
            '<text x="32" y="78" class="bo-subtitle">'
            "fixed seed · 1D · noiseless · RBF kernel · 10 evaluation budget"
            "</text>"
        ),
        '<line x1="34" y1="108" x2="70" y2="108" stroke="#245c42" stroke-width="5"/>',
        '<text x="78" y="114" class="bo-legend">surrogate</text>',
        '<rect x="188" y="98" width="36" height="18" rx="5" fill="#cfe7dc"/>',
        '<text x="232" y="114" class="bo-legend">uncertainty</text>',
        (
            '<line x1="368" y1="108" x2="404" y2="108" stroke="#617068" '
            'stroke-width="3" stroke-dasharray="8 6"/>'
        ),
        '<text x="412" y="114" class="bo-legend">truth（教材のみ）</text>',
    ]

    for panel_title, frame, panel_y in panel_specs:
        plot_y = panel_y + 50
        acquisition_y = plot_y + plot_height + 35
        selected_x = float(frame.selected_point)
        selected_screen_x = project_x(selected_x)
        max_acquisition = max(point.acquisition for point in frame.predictive_summary)
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
        elements.extend(
            [
                (
                    f'<rect x="24" y="{panel_y}" width="592" height="382" rx="18" '
                    'fill="#fff" stroke="#cfd8d1"/>'
                ),
                (
                    f'<text x="44" y="{panel_y + 31}" class="bo-panel">'
                    f"{html.escape(panel_title)}</text>"
                ),
                (
                    f'<text x="596" y="{panel_y + 31}" text-anchor="end" class="bo-status">'
                    f"実評価 {frame.oracle_evaluations}回 · next x={selected_x:.2f}</text>"
                ),
                (
                    f'<rect x="{plot_x}" y="{plot_y}" width="{plot_width}" '
                    f'height="{plot_height}" rx="12" fill="#fbfcfa"/>'
                ),
            ]
        )
        for tick in (-1.0, 0.0, 2.0, 4.0):
            tick_y = project_y(tick, plot_y)
            elements.extend(
                [
                    (
                        f'<line x1="{plot_x}" y1="{tick_y:.2f}" '
                        f'x2="{plot_x + plot_width}" y2="{tick_y:.2f}" '
                        'stroke="#ebe8e0"/>'
                    ),
                    (
                        f'<text x="{plot_x - 10}" y="{tick_y + 6:.2f}" '
                        f'text-anchor="end" class="bo-axis">{tick:g}</text>'
                    ),
                ]
            )
        elements.extend(
            [
                f'<polygon points="{uncertainty_polygon}" fill="#cfe7dc" opacity="0.82"/>',
                (
                    f'<polyline points="{truth_points}" fill="none" stroke="#617068" '
                    'stroke-width="3" stroke-dasharray="8 6"/>'
                ),
                (
                    f'<polyline points="{mean_points}" fill="none" stroke="#245c42" '
                    'stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>'
                ),
                (
                    f'<line x1="{selected_screen_x:.2f}" y1="{plot_y}" '
                    f'x2="{selected_screen_x:.2f}" '
                    f'y2="{acquisition_y + acquisition_height}" stroke="#d67835" '
                    'stroke-width="4" stroke-dasharray="7 6"/>'
                ),
            ]
        )
        for observation in frame.observations:
            elements.append(
                f'<circle cx="{project_x(observation.x):.2f}" '
                f'cy="{project_y(observation.observed_value, plot_y):.2f}" r="8" '
                'fill="#245c42" stroke="#fff" stroke-width="3"/>'
            )
        elements.extend(
            [
                (
                    f'<text x="{plot_x}" y="{acquisition_y - 9}" class="bo-axis">'
                    "Expected Improvement</text>"
                ),
                (
                    f'<text x="{plot_x + plot_width}" y="{acquisition_y - 9}" '
                    'text-anchor="end" class="bo-axis">'
                    f"max {max_acquisition:.3f}</text>"
                ),
                (
                    f'<rect x="{plot_x}" y="{acquisition_y}" width="{plot_width}" '
                    f'height="{acquisition_height}" rx="10" fill="#fbf4ed"/>'
                ),
                f'<polygon points="{acquisition_path}" fill="#efc5a5" opacity="0.9"/>',
                (
                    f'<polyline points="{acquisition_point_string}" '
                    'fill="none" stroke="#d67835" stroke-width="4" '
                    'stroke-linecap="round" stroke-linejoin="round"/>'
                ),
                (
                    f'<circle cx="{selected_screen_x:.2f}" '
                    f'cy="{selected_acquisition_y:.2f}" '
                    'r="7" fill="#d67835" stroke="#fff" stroke-width="3"/>'
                ),
            ]
        )
        for tick in (-3.0, 0.0, 3.0):
            tick_x = project_x(tick)
            elements.append(
                f'<text x="{tick_x:.2f}" y="{acquisition_y + acquisition_height + 25}" '
                f'text-anchor="middle" class="bo-axis">{tick:g}</text>'
            )

    first_uncertainty = float(frames[0].selected_uncertainty)
    later_uncertainty = float(frames[1].selected_uncertainty)
    elements.extend(
        [
            '<text x="32" y="970" class="bo-summary">このrunで観測した変化</text>',
            (
                '<text x="32" y="1003" class="bo-metric">'
                f"実評価 3 → 6　　next x 1.73 → 2.10　　"
                f"next点の不確実性 {first_uncertainty:.2f} → {later_uncertainty:.2f}</text>"
            ),
            (
                '<text x="32" y="1044" class="bo-provenance">'
                "実行生成: generate_surrogate_scenario · explore / noiseless · "
                f"dataset {html.escape(dataset_version)}</text>"
            ),
            (
                '<text x="32" y="1077" class="bo-caveat">'
                "固定seed・1次元・RBF kernelの教材です。大域最適性や一般性能を保証しません。"
                "</text>"
            ),
            (
                "<style>"
                "text{font-family:system-ui,-apple-system,'Segoe UI',sans-serif;fill:#26352d}"
                ".bo-title{font-size:30px;font-weight:760}"
                ".bo-subtitle{font-size:17px;fill:#617068}"
                ".bo-legend{font-size:17px;fill:#46554d}"
                ".bo-panel{font-size:23px;font-weight:750}"
                ".bo-status{font-size:18px;fill:#617068;font-variant-numeric:tabular-nums}"
                ".bo-axis{font-size:18px;fill:#617068;font-variant-numeric:tabular-nums}"
                ".bo-summary{font-size:21px;font-weight:750}"
                ".bo-metric{font-size:19px;font-weight:650;font-variant-numeric:tabular-nums}"
                ".bo-provenance{font-size:15px;fill:#617068}"
                ".bo-caveat{font-size:15px;fill:#7a4b38}"
                "</style>"
            ),
            "</svg>\n",
        ]
    )
    return "".join(elements)


def _optimal_control_mesh_svg(dataset_version: str) -> str:
    traces = _generate_optimal_control_traces(dataset_version=dataset_version)
    trace_styles = {
        "pendulum-collocation-coarse": ("N=20", "#245c42", ""),
        "pendulum-collocation-refined": ("N=40", "#456b92", ""),
        "pendulum-model-rollout-failure": (
            "model mismatch",
            "#a53d3d",
            ' stroke-dasharray="14 9"',
        ),
    }
    panels = (
        ("mesh node上のpath violation", "node_path_violation", 130.0),
        ("区間再構成 / validation rolloutのpath violation", "reconstructed_path_violation", 430.0),
    )
    plot_x, plot_width, plot_height = 92.0, 620.0, 210.0
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

    elements = [
        _svg_open(
            "mesh上で収束しても、区間内の違反は別に残る",
            (
                "同じpendulum swing-up教材でN=20、N=40、gravityを10%変えたvalidation "
                "rolloutを比較します。mesh node上のpath violationは許容値内まで下がりますが、"
                "区間再構成とmodel mismatchでは別の違反が残ります。"
            ),
            height=920,
        ),
        '<rect width="800" height="920" rx="24" fill="#f7f6f1"/>',
        '<text x="42" y="54" class="title">mesh上で収束しても、区間内の違反は別に残る</text>',
        (
            '<text x="42" y="84" class="subtitle">'
            "same pendulum · 2 s horizon · same initial trajectory · 8 evaluation budget"
            "</text>"
        ),
    ]
    for panel_title, metric_key, plot_y in panels:
        elements.extend(
            [
                (
                    f'<text x="{plot_x}" y="{plot_y - 18}" class="panel-title">'
                    f"{html.escape(panel_title)}</text>"
                ),
                (
                    f'<rect x="{plot_x}" y="{plot_y}" width="{plot_width}" '
                    f'height="{plot_height}" rx="14" fill="#fff" stroke="#cfd8d1"/>'
                ),
            ]
        )
        for exponent in range(-5, 1):
            value = 10.0**exponent
            _, tick_y = project(
                iteration=0,
                value=value,
                plot_y=plot_y,
                max_iteration=8,
            )
            elements.extend(
                [
                    (
                        f'<line x1="{plot_x}" y1="{tick_y:.2f}" '
                        f'x2="{plot_x + plot_width}" y2="{tick_y:.2f}" '
                        'stroke="#ebe8e0"/>'
                    ),
                    (
                        f'<text x="{plot_x - 16}" y="{tick_y + 5:.2f}" '
                        f'text-anchor="end" class="axis">1e{exponent}</text>'
                    ),
                ]
            )
        _, tolerance_y = project(
            iteration=0,
            value=1e-4,
            plot_y=plot_y,
            max_iteration=8,
        )
        elements.extend(
            [
                (
                    f'<line x1="{plot_x}" y1="{tolerance_y:.2f}" '
                    f'x2="{plot_x + plot_width}" y2="{tolerance_y:.2f}" '
                    'stroke="#c56b32" stroke-width="2" stroke-dasharray="5 5"/>'
                ),
                (
                    f'<text x="{plot_x + 10}" y="{tolerance_y - 8:.2f}" '
                    'class="axis" fill="#9a4f24">path tolerance 1e-4</text>'
                ),
            ]
        )
        for trace in traces:
            _, color, dash = trace_styles[trace.trace_id]
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
            elements.append(
                f'<polyline points="{point_string}" fill="none" stroke="{color}" '
                f'stroke-width="5" stroke-linecap="round" stroke-linejoin="round"{dash}/>'
            )
            for x, y in points:
                elements.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="4" fill="{color}"/>')
        elements.append(
            f'<text x="{plot_x + plot_width / 2}" y="{plot_y + plot_height + 28}" '
            'text-anchor="middle" class="axis">iteration</text>'
        )
    for row, trace in enumerate(traces):
        label, color, dash = trace_styles[trace.trace_id]
        terminal = trace.frames[-1]
        node = float(terminal.payload["node_path_violation"])
        reconstructed = float(terminal.payload["reconstructed_path_violation"])
        row_y = 718 + row * 42
        elements.extend(
            [
                (
                    f'<line x1="92" y1="{row_y}" x2="132" y2="{row_y}" '
                    f'stroke="{color}" stroke-width="6"{dash}/>'
                ),
                (
                    f'<text x="148" y="{row_y + 6}" class="method" fill="{color}">'
                    f"{html.escape(label)}</text>"
                ),
                (
                    f'<text x="712" y="{row_y + 6}" text-anchor="end" class="metric-value">'
                    f"node {node:.1e} · rollout {reconstructed:.3g}</text>"
                ),
            ]
        )
    elements.extend(
        [
            (
                '<text x="42" y="858" class="caption">'
                "実行生成: optimization_compass.site_export._generate_optimal_control_traces"
                f" · dataset {html.escape(dataset_version)}</text>"
            ),
            (
                '<text x="42" y="892" class="caveat">'
                "固定pendulum教材の診断履歴です。連続時間可行性・実機安全性・一般性能を保証しません。"
                "</text>"
            ),
            _svg_style(),
            "</svg>\n",
        ]
    )
    return "".join(elements)


def _constrained_feasibility_svg(dataset_version: str) -> str:
    artifact = generate_feasible_region_artifact(dataset_version)
    plot_x, plot_y, plot_width, plot_height = 88.0, 126.0, 624.0, 500.0
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
    elements = [
        _svg_open(
            "目的値が下がっても、制約違反なら解ではない",
            artifact.text_alternative_ja,
            height=850,
        ),
        '<rect width="800" height="850" rx="24" fill="#f7f6f1"/>',
        '<text x="42" y="54" class="title">目的値が下がっても、制約違反なら解ではない</text>',
        (
            '<text x="42" y="84" class="subtitle">'
            "min x²+y² · (x−1)²+(y−1)² ≤ 1 · deterministic teaching trace"
            "</text>"
        ),
        (
            f'<rect x="{plot_x}" y="{plot_y}" width="{plot_width}" height="{plot_height}" '
            'rx="16" fill="#fff" stroke="#cfd8d1"/>'
        ),
        (
            f'<clipPath id="feasible-plot"><rect x="{plot_x}" y="{plot_y}" '
            f'width="{plot_width}" height="{plot_height}" rx="16"/></clipPath>'
        ),
        '<g clip-path="url(#feasible-plot)">',
    ]
    for level in artifact.contour_values:
        contour_radius = math.sqrt(level) / (x_max - x_min) * plot_width
        origin_x, origin_y = project((0.0, 0.0))
        elements.append(
            f'<circle cx="{origin_x:.2f}" cy="{origin_y:.2f}" r="{contour_radius:.2f}" '
            'fill="none" stroke="#dedbd2" stroke-width="2"/>'
        )
    elements.extend(
        [
            (
                f'<circle cx="{center_x:.2f}" cy="{center_y:.2f}" r="{radius:.2f}" '
                'fill="#dcefe4" fill-opacity="0.88" stroke="#245c42" stroke-width="4"/>'
            ),
            "</g>",
            (
                f'<text x="{center_x:.2f}" y="{center_y - radius + 30:.2f}" '
                'text-anchor="middle" class="panel-title" fill="#245c42">実行可能領域</text>'
            ),
        ]
    )
    path_styles = {
        "constraint_aware": ("制約を評価", "#245c42"),
        "unconstrained_failure": ("制約を無視", "#c56b32"),
    }
    summaries: list[tuple[str, str, float, float]] = []
    for path in artifact.paths:
        label, color = path_styles[path.role]
        points = [project(step.point) for step in path.steps]
        point_string = " ".join(f"{x:.2f},{y:.2f}" for x, y in points)
        dash = ' stroke-dasharray="14 9"' if path.role == "unconstrained_failure" else ""
        elements.append(
            f'<polyline points="{point_string}" fill="none" stroke="{color}" '
            f'stroke-width="6" stroke-linecap="round" stroke-linejoin="round"{dash}/>'
        )
        for index, (x, y) in enumerate(points):
            radius_value = 7 if index in {0, len(points) - 1} else 4
            fill = "#fff" if index == 0 else color
            elements.append(
                f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{radius_value}" '
                f'fill="{fill}" stroke="{color}" stroke-width="3"/>'
            )
        terminal = path.steps[-1]
        summaries.append((label, color, terminal.objective, terminal.violation))
    elements.extend(
        [
            (
                '<text x="88" y="654" class="note">'
                "○ 共通初期点　● 終了点　実線: 制約を評価　破線: 制約を無視</text>"
            ),
        ]
    )
    for row, (label, color, objective, violation) in enumerate(summaries):
        row_y = 690 + row * 42
        elements.extend(
            [
                (
                    f'<line x1="88" y1="{row_y}" x2="124" y2="{row_y}" '
                    f'stroke="{color}" stroke-width="6"/>'
                ),
                (
                    f'<text x="140" y="{row_y + 6}" class="method" fill="{color}">'
                    f"{html.escape(label)}</text>"
                ),
                (
                    f'<text x="712" y="{row_y + 6}" text-anchor="end" class="metric-value">'
                    f"f={objective:.3f} · violation={violation:.3f}</text>"
                ),
            ]
        )
    elements.extend(
        [
            (
                '<text x="42" y="790" class="caption">'
                "実行生成: optimization_compass.learning_slices.generate_feasible_region_artifact"
                f" · dataset {html.escape(dataset_version)}</text>"
            ),
            (
                '<text x="42" y="824" class="caveat">'
                "固定2次元教材です。SLSQPやBFGSの実装性能・一般的な収束性は示しません。"
                "</text>"
            ),
            _svg_style(),
            "</svg>\n",
        ]
    )
    return "".join(elements)


def _pareto_preference_svg(dataset_version: str) -> str:
    artifact = generate_pareto_front_artifact(dataset_version)
    plot_x, plot_y, plot_width, plot_height = 96.0, 126.0, 600.0, 500.0
    lower, upper = -0.4, 8.4

    def project(objectives: tuple[float, float]) -> tuple[float, float]:
        first, second = objectives
        return (
            plot_x + (first - lower) / (upper - lower) * plot_width,
            plot_y + plot_height - (second - lower) / (upper - lower) * plot_height,
        )

    elements = [
        _svg_open(
            "同じfrontでも、weightで選ぶ点が動く",
            artifact.text_alternative_ja,
            height=850,
        ),
        '<rect width="800" height="850" rx="24" fill="#f7f6f1"/>',
        '<text x="42" y="54" class="title">同じfrontでも、weightで選ぶ点が動く</text>',
        (
            '<text x="42" y="84" class="subtitle">'
            "2-objective quadratic · 81 sampled points · exact teaching front"
            "</text>"
        ),
        (
            f'<rect x="{plot_x}" y="{plot_y}" width="{plot_width}" height="{plot_height}" '
            'rx="16" fill="#fff" stroke="#cfd8d1"/>'
        ),
    ]
    for tick in (0, 2, 4, 6, 8):
        tick_x, _ = project((float(tick), 0.0))
        _, tick_y = project((0.0, float(tick)))
        elements.extend(
            [
                (
                    f'<line x1="{tick_x:.2f}" y1="{plot_y}" x2="{tick_x:.2f}" '
                    f'y2="{plot_y + plot_height}" stroke="#ebe8e0"/>'
                ),
                (
                    f'<line x1="{plot_x}" y1="{tick_y:.2f}" x2="{plot_x + plot_width}" '
                    f'y2="{tick_y:.2f}" stroke="#ebe8e0"/>'
                ),
                (
                    f'<text x="{tick_x:.2f}" y="{plot_y + plot_height + 28}" '
                    f'text-anchor="middle" class="axis">{tick}</text>'
                ),
                (
                    f'<text x="{plot_x - 18}" y="{tick_y + 5:.2f}" '
                    f'text-anchor="end" class="axis">{tick}</text>'
                ),
            ]
        )
    for point in artifact.points:
        x, y = project(point.objectives)
        fill = "#b8b5ad" if point.dominated else "#7ca993"
        opacity = "0.55" if point.dominated else "0.8"
        elements.append(
            f'<circle cx="{x:.2f}" cy="{y:.2f}" r="4.5" fill="{fill}" opacity="{opacity}"/>'
        )
    front_points = " ".join(
        f"{x:.2f},{y:.2f}"
        for x, y in (project(point.objectives) for point in artifact.pareto_front)
    )
    elements.append(
        f'<polyline points="{front_points}" fill="none" stroke="#245c42" '
        'stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>'
    )
    for selection in artifact.preference_selections:
        x, y = project(selection.objectives)
        label_x = x + (16 if selection.weight_f1 < 0.5 else -16)
        anchor = "start" if selection.weight_f1 < 0.5 else "end"
        label_y = y - 14 if selection.weight_f1 != 0.8 else y + 30
        elements.extend(
            [
                (
                    f'<circle cx="{x:.2f}" cy="{y:.2f}" r="10" fill="#c56b32" '
                    'stroke="#fff" stroke-width="4"/>'
                ),
                (
                    f'<text x="{label_x:.2f}" y="{label_y:.2f}" text-anchor="{anchor}" '
                    f'class="method" fill="#9a4f24">w₁={selection.weight_f1:.1f}</text>'
                ),
            ]
        )
    ideal_x, ideal_y = project(artifact.reference.ideal)
    elements.extend(
        [
            (
                f'<path d="M {ideal_x - 8:.2f} {ideal_y:.2f} H {ideal_x + 8:.2f} '
                f'M {ideal_x:.2f} {ideal_y - 8:.2f} V {ideal_y + 8:.2f}" '
                'stroke="#a53d3d" stroke-width="3"/>'
            ),
            (
                f'<text x="{ideal_x + 16:.2f}" y="{ideal_y - 12:.2f}" '
                'class="status" fill="#a53d3d">ideal（同時には到達不能）</text>'
            ),
            (
                '<text x="396" y="682" text-anchor="middle" class="axis">'
                "f₁: originからの距離²（小さいほど良い）</text>"
            ),
            (
                '<text x="28" y="376" text-anchor="middle" class="axis" '
                'transform="rotate(-90 28 376)">f₂: (2,2)からの距離²（小さいほど良い）</text>'
            ),
            (
                '<text x="96" y="722" class="note">'
                "灰: dominated　青緑: Pareto front　橙: weightで選んだ点</text>"
            ),
            (
                '<text x="42" y="780" class="caption">'
                "実行生成: optimization_compass.learning_slices.generate_pareto_front_artifact"
                f" · dataset {html.escape(dataset_version)}</text>"
            ),
            (
                '<text x="42" y="814" class="caveat">'
                "凸な2目的固定教材です。weightは客観的な優先度や一般性能rankingではありません。"
                "</text>"
            ),
            _svg_style(),
            "</svg>\n",
        ]
    )
    return "".join(elements)


def _gradient_family_svg(dataset_version: str) -> str:
    bundle = generate_gradient_bundle(dataset_version=dataset_version)
    traces = bundle.member_traces
    styles = {
        "gradient_descent": ("Gradient Descent", "#245c42"),
        "momentum": ("Momentum", "#c56b32"),
        "adam": ("Adam", "#456b92"),
    }
    plot_x, plot_y, plot_width, plot_height = 60.0, 120.0, 680.0, 420.0
    x_bounds, y_bounds = (-1.8, 1.6), (-0.2, 1.8)

    def project(point: tuple[float, float] | list[float]) -> tuple[float, float]:
        x, y = point
        return (
            plot_x + (x - x_bounds[0]) / (x_bounds[1] - x_bounds[0]) * plot_width,
            plot_y + plot_height - (y - y_bounds[0]) / (y_bounds[1] - y_bounds[0]) * plot_height,
        )

    elements = [
        _svg_open(
            "同じ谷でも、更新則で軌跡が変わる",
            (
                "f(x,y)=100x²+y²を同じ初期点と40回の評価予算で実行した結果です。"
                "Gradient Descent、Momentum、Adamの軌跡と最終目的値を示します。"
            ),
            height=900,
        ),
        '<rect width="800" height="900" rx="24" fill="#f7f6f1"/>',
        '<text x="60" y="54" class="title">同じ谷でも、更新則で軌跡が変わる</text>',
        (
            '<text x="60" y="84" class="subtitle">'
            "f(x,y)=100x²+y² · 同じ初期点 · 40 oracle evaluations · fixed preset"
            "</text>"
        ),
        (
            f'<rect x="{plot_x}" y="{plot_y}" width="{plot_width}" height="{plot_height}" '
            'rx="14" fill="#fff" stroke="#cfd8d1"/>'
        ),
    ]
    for level in (1.0, 4.0, 16.0, 64.0, 256.0):
        radius_x, radius_y = math.sqrt(level / 100.0), math.sqrt(level)
        center = project((0.0, 0.0))
        rx = radius_x / (x_bounds[1] - x_bounds[0]) * plot_width
        ry = radius_y / (y_bounds[1] - y_bounds[0]) * plot_height
        elements.append(
            f'<ellipse cx="{center[0]:.2f}" cy="{center[1]:.2f}" rx="{rx:.2f}" '
            f'ry="{ry:.2f}" fill="none" stroke="#d9dfda" stroke-width="1.5"/>'
        )
    optimum = project((0.0, 0.0))
    elements.extend(
        [
            (
                f'<line x1="{optimum[0]:.2f}" y1="{plot_y}" x2="{optimum[0]:.2f}" '
                f'y2="{plot_y + plot_height}" stroke="#e4e8e4"/>'
            ),
            (
                f'<line x1="{plot_x}" y1="{optimum[1]:.2f}" x2="{plot_x + plot_width}" '
                f'y2="{optimum[1]:.2f}" stroke="#e4e8e4"/>'
            ),
            (
                f'<circle cx="{optimum[0]:.2f}" cy="{optimum[1]:.2f}" r="6" '
                'fill="#fff" stroke="#1f2924" stroke-width="2"/>'
            ),
            (
                f'<text x="{optimum[0] + 12:.2f}" y="{optimum[1] - 10:.2f}" '
                'class="axis">optimum</text>'
            ),
        ]
    )
    for trace in traces:
        method = str(trace.frames[0].payload["method"])
        label, color = styles[method]
        points = [
            project(tuple(frame.points[0].coordinates)) for frame in trace.frames if frame.points
        ]
        point_string = " ".join(f"{x:.2f},{y:.2f}" for x, y in points)
        start_x, start_y = points[0]
        end_x, end_y = points[-1]
        elements.extend(
            [
                (
                    f'<polyline points="{point_string}" fill="none" stroke="{color}" '
                    'stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>'
                ),
                (
                    f'<circle cx="{start_x:.2f}" cy="{start_y:.2f}" r="6" fill="#fff" '
                    f'stroke="{color}" stroke-width="3"/>'
                ),
                f'<circle cx="{end_x:.2f}" cy="{end_y:.2f}" r="7" fill="{color}"/>',
            ]
        )
        terminal_value = _objective_value(trace.frames[-1])
        row_y = 612 + list(styles).index(method) * 72
        elements.extend(
            [
                (
                    f'<line x1="60" y1="{row_y}" x2="100" y2="{row_y}" '
                    f'stroke="{color}" stroke-width="5"/>'
                ),
                f'<text x="116" y="{row_y + 6}" class="method">{html.escape(label)}</text>',
                (
                    f'<text x="414" y="{row_y + 6}" class="metric">'
                    f"final f = {_metric(terminal_value)}</text>"
                ),
                (
                    f'<text x="740" y="{row_y + 6}" text-anchor="end" class="status">'
                    f"{html.escape(trace.terminal_status)} · "
                    f"{trace.frames[-1].oracle_evaluations} evals"
                    "</text>"
                ),
            ]
        )
    elements.extend(
        [
            '<text x="60" y="570" class="note">○ start　● terminal　等高線は目的関数値</text>',
            (
                '<text x="60" y="838" class="caption">'
                "実行生成: optimization_compass.traces.generate_gradient_bundle"
                f" · dataset {html.escape(dataset_version)}</text>"
            ),
            (
                '<text x="60" y="870" class="caveat">'
                "この固定presetの軌跡であり、一般的な性能rankingではありません。"
                "</text>"
            ),
            _svg_style(),
            "</svg>\n",
        ]
    )
    return "".join(elements)


def _portfolio_risk_svg(dataset_version: str) -> str:
    traces = generate_portfolio_uncertainty_traces(dataset_version=dataset_version)
    panels = (
        ("nominal目的", traces[0], "#245c42"),
        ("CVaRを含む目的", traces[1], "#c56b32"),
    )
    asset_colors = ("#245c42", "#c56b32", "#456b92", "#8b7d58")
    elements = [
        _svg_open(
            "同じ12 scenarioでも、riskの置き方で配分が変わる",
            (
                "4資産の配分を、同じtraining 8件とheld-out 4件で評価した固定教材です。"
                "nominal目的とCVaRを含む目的について、配分とmean loss、CVaR 75%、"
                "worst lossをtrainingとheld-outに分けて示します。"
            ),
            height=920,
        ),
        '<rect width="800" height="920" rx="24" fill="#f7f6f1"/>',
        '<text x="42" y="54" class="title">同じsampleでも、riskの置き方で配分が変わる</text>',
        (
            '<text x="42" y="84" class="subtitle">'
            "4 assets · training 8 + held-out 4 · same capped simplex · α = 0.75"
            "</text>"
        ),
    ]
    for panel_index, (label, trace, accent) in enumerate(panels):
        panel_y = 116 + panel_index * 344
        weights = trace.frames[0].points[0].coordinates
        training = trace.frames[1]
        held_out = trace.frames[2]
        elements.extend(
            [
                (
                    f'<rect x="42" y="{panel_y}" width="716" height="316" rx="16" '
                    'fill="#fff" stroke="#cfd8d1"/>'
                ),
                (
                    f'<text x="64" y="{panel_y + 38}" class="panel-title" '
                    f'fill="{accent}">{html.escape(label)}</text>'
                ),
                (
                    f'<text x="736" y="{panel_y + 38}" text-anchor="end" class="status">'
                    f"{html.escape(str(trace.objective['definition']))}</text>"
                ),
                f'<text x="64" y="{panel_y + 72}" class="metric">配分</text>',
            ]
        )
        bar_x, bar_y, bar_width, bar_height = 126.0, panel_y + 52.0, 610.0, 34.0
        cursor = bar_x
        for asset_index, (weight, color) in enumerate(zip(weights, asset_colors, strict=True)):
            width = float(weight) * bar_width
            if width > 0:
                elements.append(
                    f'<rect x="{cursor:.2f}" y="{bar_y:.2f}" width="{width:.2f}" '
                    f'height="{bar_height}" fill="{color}"/>'
                )
            cursor += width
            elements.append(
                f'<text x="{126 + asset_index * 150}" y="{panel_y + 112}" class="status">'
                f'<tspan fill="{color}" font-weight="750">●</tspan> '
                f"Asset {asset_index + 1}: {float(weight):.2f}</text>"
            )
        elements.extend(
            [
                f'<text x="64" y="{panel_y + 158}" class="method">評価split</text>',
                f'<text x="310" y="{panel_y + 158}" class="method">mean loss</text>',
                f'<text x="494" y="{panel_y + 158}" class="method">CVaR 75%</text>',
                f'<text x="668" y="{panel_y + 158}" class="method">worst loss</text>',
            ]
        )
        for row_index, (split_label, frame) in enumerate(
            (("training 8", training), ("held-out 4", held_out))
        ):
            row_y = panel_y + 202 + row_index * 54
            elements.extend(
                [
                    f'<text x="64" y="{row_y}" class="metric">{split_label}</text>',
                    (
                        f'<text x="310" y="{row_y}" class="metric-value">'
                        f"{_metric(_metric_value(frame, 'mean_loss'))}</text>"
                    ),
                    (
                        f'<text x="494" y="{row_y}" class="metric-value">'
                        f"{_metric(_metric_value(frame, 'cvar_75'))}</text>"
                    ),
                    (
                        f'<text x="668" y="{row_y}" class="metric-value">'
                        f"{_metric(_metric_value(frame, 'worst_loss'))}</text>"
                    ),
                ]
            )
        elements.append(
            f'<line x1="64" y1="{panel_y + 294}" x2="736" y2="{panel_y + 294}" '
            f'stroke="{accent}" stroke-width="3"/>'
        )
    elements.extend(
        [
            (
                '<text x="42" y="826" class="caption">'
                "実行生成: optimization_compass.portfolio_uncertainty."
                f"generate_portfolio_uncertainty_traces · dataset {html.escape(dataset_version)}"
                "</text>"
            ),
            (
                '<text x="42" y="860" class="caveat">'
                "固定8/4 scenarioのempirical summaryであり、母集団riskや将来returnを保証しません。"
                "</text>"
            ),
            (
                '<text x="42" y="892" class="note">'
                "lossは小さい側が良い。trainingとheld-outは別々に読みます。</text>"
            ),
            _svg_style(),
            "</svg>\n",
        ]
    )
    return "".join(elements)


def _trf_probe_svg(dataset_version: str) -> str:
    traces = {
        trace.trace_id: trace
        for trace in generate_parameter_estimation_traces(dataset_version=dataset_version)
    }
    series = (
        ("通常初期値", traces["exponential-fit-trf"], "#245c42", 486.0),
        ("悪い初期値", traces["exponential-fit-trf-poor-init"], "#c56b32", 420.0),
    )
    plot_x, plot_y, plot_width, plot_height = 76.0, 136.0, 648.0, 390.0
    log_min, log_max = math.log10(0.03), math.log10(4.0)

    def project(evaluation: int, residual: float) -> tuple[float, float]:
        x = plot_x + (evaluation - 1) / 11 * plot_width
        y = plot_y + (log_max - math.log10(residual)) / (log_max - log_min) * plot_height
        return x, y

    elements = [
        _svg_open(
            "同じ診断probeでも、初期値で残差履歴が変わる",
            (
                "20観測の指数減衰fitに対するsolver-independent damped Gauss–Newton"
                "診断probeの実行結果です。通常初期値と悪い初期値について、"
                "12 evaluationまでのresidual normを対数目盛で示します。"
                "TRF本体の実行ではありません。"
            ),
            height=720,
        ),
        '<rect width="800" height="720" rx="24" fill="#f7f6f1"/>',
        '<text x="42" y="54" class="title">同じ診断probeでも、初期値で残差履歴が変わる</text>',
        (
            '<text x="42" y="84" class="subtitle">'
            "exponential fit · 20 observations · 12 evaluations · log residual scale"
            "</text>"
        ),
        (
            f'<rect x="{plot_x}" y="{plot_y}" width="{plot_width}" height="{plot_height}" '
            'rx="14" fill="#fff" stroke="#cfd8d1"/>'
        ),
    ]
    for tick in (3.0, 1.0, 0.3, 0.1, 0.03):
        _, y = project(1, tick)
        elements.extend(
            [
                (
                    f'<line x1="{plot_x}" y1="{y:.2f}" x2="{plot_x + plot_width}" '
                    f'y2="{y:.2f}" stroke="#e2e7e2"/>'
                ),
                (
                    f'<text x="{plot_x - 12}" y="{y + 5:.2f}" text-anchor="end" '
                    f'class="axis">{tick:g}</text>'
                ),
            ]
        )
    for evaluation in (1, 4, 8, 12):
        x, _ = project(evaluation, 1.0)
        elements.extend(
            [
                (
                    f'<line x1="{x:.2f}" y1="{plot_y}" x2="{x:.2f}" '
                    f'y2="{plot_y + plot_height}" stroke="#eef1ee"/>'
                ),
                (
                    f'<text x="{x:.2f}" y="{plot_y + plot_height + 26}" '
                    f'text-anchor="middle" class="axis">{evaluation}</text>'
                ),
            ]
        )
    for label, trace, color, label_y in series:
        points = [
            project(frame.oracle_evaluations, _metric_value(frame, "residual_norm"))
            for frame in trace.frames
        ]
        point_string = " ".join(f"{x:.2f},{y:.2f}" for x, y in points)
        start_value = _metric_value(trace.frames[0], "residual_norm")
        final_value = _metric_value(trace.frames[-1], "residual_norm")
        end_x, end_y = points[-1]
        elements.extend(
            [
                (
                    f'<polyline points="{point_string}" fill="none" stroke="{color}" '
                    'stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>'
                ),
                (
                    f'<circle cx="{points[0][0]:.2f}" cy="{points[0][1]:.2f}" r="6" '
                    f'fill="#fff" stroke="{color}" stroke-width="3"/>'
                ),
                f'<circle cx="{end_x:.2f}" cy="{end_y:.2f}" r="7" fill="{color}"/>',
                (
                    f'<line x1="604" y1="{label_y - 5:.2f}" x2="{end_x - 10:.2f}" '
                    f'y2="{end_y:.2f}" stroke="{color}" stroke-width="2"/>'
                ),
                (
                    f'<text x="594" y="{label_y:.2f}" text-anchor="end" '
                    f'class="method" fill="{color}">{html.escape(label)}</text>'
                ),
                (
                    f'<text x="594" y="{label_y + 22:.2f}" text-anchor="end" '
                    f'class="status">residual {_metric(start_value)}'
                    f" → {_metric(final_value)}</text>"
                ),
            ]
        )
    elements.extend(
        [
            '<text x="400" y="584" text-anchor="middle" class="metric">oracle evaluations</text>',
            (
                '<text x="42" y="640" class="caption">'
                "実行生成: optimization_compass.parameter_estimation."
                f"generate_parameter_estimation_traces · dataset {html.escape(dataset_version)}"
                "</text>"
            ),
            (
                '<text x="42" y="674" class="caveat">'
                "solver条件を読む固定診断probeです。"
                "SciPy TRFの内部iterationや性能差ではありません。"
                "</text>"
            ),
            _svg_style(),
            "</svg>\n",
        ]
    )
    return "".join(elements)


def _search_tree_proof_svg(dataset_version: str) -> str:
    artifact = generate_search_tree_artifact(dataset_version=dataset_version)
    payload = SearchTreeFramePayload.model_validate(artifact.trace.frames[-1].payload)
    positions = {
        "root": (400.0, 146.0),
        "root-0": (190.0, 272.0),
        "root-1": (610.0, 272.0),
        "root-1-0": (190.0, 398.0),
        "root-1-1": (610.0, 398.0),
        "root-1-1-0": (190.0, 524.0),
        "root-1-1-1": (610.0, 524.0),
        "root-1-1-0-0": (190.0, 650.0),
        "root-1-1-0-1": (610.0, 650.0),
    }
    state_labels = {
        "branched": "分岐",
        "bound_pruned": "bound枝刈り",
        "infeasible_pruned": "実行不能",
        "optimal": "最適解",
        "open": "未探索",
        "active": "評価中",
        "feasible": "実行可能",
    }
    elements = [
        _svg_open(
            "9 nodeの探索で、bestとboundが一致する",
            (
                "4変数0-1 knapsackの決定論的Branch-and-Boundを最後まで実行した探索木です。"
                "各nodeの部分割当、value、bound、枝刈り理由を示し、最終的にbest feasible 15と"
                "global bound 15が一致してgap 0になる過程を表します。cut生成は含みません。"
            ),
            height=850,
        ),
        '<rect width="800" height="850" rx="24" fill="#f7f6f1"/>',
        '<text x="42" y="54" class="title">9 nodeの探索で、bestとboundが一致する</text>',
        (
            '<text x="42" y="84" class="subtitle">'
            "0-1 knapsack · depth-first include-first · deterministic teaching run"
            "</text>"
        ),
        (
            '<text x="42" y="112" class="metric">'
            f"best {payload.best_feasible_value} · bound {payload.global_bound:.2f} · "
            f"gap {payload.absolute_gap}</text>"
        ),
    ]
    for node in payload.nodes:
        if node.parent_id is None:
            continue
        parent_x, parent_y = positions[node.parent_id]
        child_x, child_y = positions[node.node_id]
        elements.append(
            f'<line x1="{parent_x:.2f}" y1="{parent_y + 40:.2f}" '
            f'x2="{child_x:.2f}" y2="{child_y - 40:.2f}" '
            'stroke="#9a968d" stroke-width="3"/>'
        )
    for node in payload.nodes:
        x, y = positions[node.node_id]
        fill, stroke = {
            "optimal": ("#d9f2df", "#2d7a46"),
            "infeasible_pruned": ("#f9dddd", "#a53d3d"),
            "bound_pruned": ("#e6e3dc", "#746f65"),
        }.get(node.state, ("#ffffff", "#49463f"))
        bound = "—" if node.bound is None else f"{node.bound:.2f}"
        elements.extend(
            [
                (
                    f'<rect x="{x - 94:.2f}" y="{y - 40:.2f}" width="188" height="80" '
                    f'rx="12" fill="{fill}" stroke="{stroke}" stroke-width="3"/>'
                ),
                (
                    f'<text x="{x:.2f}" y="{y - 13:.2f}" text-anchor="middle" '
                    f'class="method">{html.escape(node.branch_label_ja)}</text>'
                ),
                (
                    f'<text x="{x:.2f}" y="{y + 10:.2f}" text-anchor="middle" '
                    f'class="status">value {node.objective_value} · bound {bound}</text>'
                ),
                (
                    f'<text x="{x:.2f}" y="{y + 30:.2f}" text-anchor="middle" '
                    f'fill="{stroke}" font-size="14" font-weight="750">'
                    f"{state_labels[node.state]}</text>"
                ),
            ]
        )
    elements.extend(
        [
            (
                '<text x="42" y="780" class="caption">'
                "実行生成: optimization_compass.search_tree.generate_search_tree_artifact"
                f" · dataset {html.escape(dataset_version)}</text>"
            ),
            (
                '<text x="42" y="814" class="caveat">'
                "Branch-and-Boundの固定教材です。cut separationやMILP solver性能は示しません。"
                "</text>"
            ),
            _svg_style(),
            "</svg>\n",
        ]
    )
    return "".join(elements)


def _topology_field_svg(dataset_version: str) -> str:
    artifact = generate_topology_field_artifact(dataset_version)
    primary = next(run for run in artifact.runs if run.role == "primary")
    failure = next(run for run in artifact.runs if run.role == "failure_contrast")
    panels = (
        ("初期field", primary.steps[0]),
        ("filterあり · 反復6", primary.steps[6]),
        ("filterあり · 反復12", primary.steps[12]),
        ("filterなし · 反復12", failure.steps[12]),
    )
    elements = [
        _svg_open(
            "同じ12反復でも、filterの有無でfieldが変わる",
            (
                "8×4要素のトポロジー最適化教育generatorの実行結果です。"
                "初期field、filterありの中間と終端、filterなしの終端を、"
                "compliance、gray fraction、checkerboard scoreとともに示します。"
            ),
            height=1000,
        ),
        '<rect width="800" height="1000" rx="24" fill="#f7f6f1"/>',
        '<text x="36" y="54" class="title">同じ12反復でも、filterの有無でfieldが変わる</text>',
        (
            '<text x="36" y="84" class="subtitle">'
            "8×4 density field · volume target 0.50 · deterministic teaching run"
            "</text>"
        ),
    ]
    panel_width = 350
    panel_height = 360
    cell_size = 36
    grid_width = artifact.grid.columns * cell_size
    for index, (label, step) in enumerate(panels):
        panel_x = 36 + (index % 2) * 378
        panel_y = 116 + (index // 2) * 386
        grid_x = panel_x + (panel_width - grid_width) / 2
        grid_y = panel_y + 54
        accent = "#a33d30" if "filterなし" in label else "#245c42"
        elements.extend(
            [
                (
                    f'<rect x="{panel_x}" y="{panel_y}" width="{panel_width}" '
                    f'height="{panel_height}" rx="16" '
                    'fill="#fff" stroke="#cfd8d1"/>'
                ),
                (
                    f'<text x="{panel_x + 18}" y="{panel_y + 34}" class="panel-title" '
                    f'fill="{accent}">{html.escape(label)}</text>'
                ),
            ]
        )
        for cell_index, density in enumerate(step.density):
            x = grid_x + (cell_index % artifact.grid.columns) * cell_size
            y = grid_y + (cell_index // artifact.grid.columns) * cell_size
            fill = _density_color(density)
            elements.append(
                f'<rect x="{x:.2f}" y="{y:.2f}" width="{cell_size}" height="{cell_size}" '
                f'fill="{fill}" stroke="#eef1ed" stroke-width="1"/>'
            )
        elements.extend(
            [
                (f'<text x="{panel_x + 18}" y="{panel_y + 230}" class="metric">compliance</text>'),
                (
                    f'<text x="{panel_x + 332}" y="{panel_y + 230}" text-anchor="end" '
                    f'class="metric-value">{step.compliance:.2f}</text>'
                ),
                (
                    f'<text x="{panel_x + 18}" y="{panel_y + 268}" '
                    'class="metric">gray fraction</text>'
                ),
                (
                    f'<text x="{panel_x + 332}" y="{panel_y + 268}" text-anchor="end" '
                    f'class="metric-value">{step.gray_fraction:.3f}</text>'
                ),
                (
                    f'<text x="{panel_x + 18}" y="{panel_y + 306}" '
                    'class="metric">checkerboard</text>'
                ),
                (
                    f'<text x="{panel_x + 332}" y="{panel_y + 306}" text-anchor="end" '
                    f'class="metric-value">{step.checkerboard_score:.3f}</text>'
                ),
                (
                    f'<text x="{panel_x + 18}" y="{panel_y + 340}" class="status">'
                    f"iteration {step.iteration} · volume {step.volume_fraction:.3f}</text>"
                ),
                (
                    f'<line x1="{panel_x + 18}" y1="{panel_y + 350}" '
                    f'x2="{panel_x + 332}" y2="{panel_y + 350}" '
                    f'stroke="{accent}" stroke-width="3"/>'
                ),
            ]
        )
    elements.extend(
        [
            (
                '<text x="36" y="912" class="caption">'
                "濃いセルほどdensityが高い。指標はfieldと同じ反復から取得。</text>"
            ),
            (
                '<text x="36" y="944" class="caption">'
                "実行生成: optimization_compass.learning_slices.generate_topology_field_artifact"
                f" · dataset {html.escape(dataset_version)}</text>"
            ),
            (
                '<text x="36" y="976" class="caveat">'
                "8×4の教育用referenceであり、実FEM・強度・座屈・製造性を保証しません。"
                "</text>"
            ),
            _svg_style(),
            "</svg>\n",
        ]
    )
    return "".join(elements)


def _svg_open(title: str, description: str, *, width: int = 800, height: int) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        'role="img" aria-labelledby="figure-title figure-description">'
        f'<title id="figure-title">{html.escape(title)}</title>'
        f'<desc id="figure-description">{html.escape(description)}</desc>'
    )


def _svg_style() -> str:
    return (
        "<style>"
        "text{font-family:system-ui,-apple-system,'Segoe UI',sans-serif;fill:#26352d}"
        ".title{font-size:28px;font-weight:750}"
        ".subtitle{font-size:16px;fill:#617068}"
        ".panel-title,.method{font-size:19px;font-weight:750}"
        ".metric,.metric-value{font-size:16px;font-variant-numeric:tabular-nums}"
        ".metric-value{font-weight:750}"
        ".status,.axis,.note{font-size:14px;fill:#617068}"
        ".caption{font-size:15px;fill:#46554d}"
        ".caveat{font-size:14px;fill:#7a4b38}"
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
