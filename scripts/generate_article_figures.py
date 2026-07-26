from __future__ import annotations

import argparse
import html
import math
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
        "bayesian-optimization-execution.svg": _bayesian_optimization_svg(dataset_version).encode(
            "utf-8"
        ),
        "constrained-feasibility-execution.svg": _constrained_feasibility_svg(
            dataset_version
        ).encode("utf-8"),
        "gradient-family-execution.svg": _gradient_family_svg(dataset_version).encode("utf-8"),
        "lqr-backward-forward-execution.svg": _lqr_backward_forward_svg(dataset_version).encode(
            "utf-8"
        ),
        "least-squares-fit-diagnostic.svg": _least_squares_fit_svg(dataset_version).encode("utf-8"),
        "multiple-shooting-continuity-execution.svg": _multiple_shooting_svg(
            dataset_version
        ).encode("utf-8"),
        "optimal-control-mesh-execution.svg": _optimal_control_mesh_svg(dataset_version).encode(
            "utf-8"
        ),
        "pareto-preference-execution.svg": _pareto_preference_svg(dataset_version).encode("utf-8"),
        "portfolio-risk-execution.svg": _portfolio_risk_svg(dataset_version).encode("utf-8"),
        "search-tree-proof-execution.svg": _search_tree_proof_svg(dataset_version).encode("utf-8"),
        "so3-update-diagnostic.svg": _so3_update_svg(dataset_version).encode("utf-8"),
        "spatial-branch-bound-execution.svg": _spatial_branch_bound_svg(dataset_version).encode(
            "utf-8"
        ),
        "topology-field-execution.svg": _topology_field_svg(dataset_version).encode("utf-8"),
        "trf-probe-execution.svg": _trf_probe_svg(dataset_version).encode("utf-8"),
    }


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
