"""Where a solver evaluates (content/concepts/solver-evaluation-points.md): water levels of a
draining tank, fitted by the outlet area a [m^2] and the inflow q [m^3/s]. The tool solves the ODE A
dh/dt = q - a sqrt(2 g h) with solve_ivp and fails when the tank runs dry.
"""

from __future__ import annotations

import math
from collections.abc import Callable

from ._svg import (
    GRID,
    INK,
    LINE,
    MUTED,
    POINT,
    RING,
    UPDATE,
    VIOLATION,
    _open,
    _polyline,
    _scale,
    _signed,
    _text,
)

EVAL_START = (1e-4, 1e-4)
# Points SciPy 1.18.1 passed to the tool, as recorded by the article's Python block. The test
# tests/lesson_figures/test_solver_evaluation_points.py reruns SciPy and checks that these
# sequences still hold.
EVAL_NM_Q = (
    1e-4,
    1e-4,
    1.05e-4,
    9.5e-5,
    9e-5,
    9e-5,
    8.5e-5,
    7.5e-5,
    6.25e-5,
    5.75e-5,
    4.125e-5,
    1.875e-5,
    -1.4375e-5,
    -3.5625e-5,
    -8.46875e-5,
)
EVAL_NM_LAST_A = 0.000265547
EVAL_BFGS_TRIAL = (0.979185, -0.247878)
# L-BFGS-B with 1e-5 <= a, q <= 1e-3, one letter per point whose gradient it computed:
# s start, a accepted iterate, t line-search point, r a point it had already evaluated.
EVAL_LBFGSB_ROLES = "sattttttattaaaaaaa"


def eval_dry_time(a: float, q: float = 0.0) -> float:
    """Seconds until a 1 m tank of area 1 m^2 runs dry with no inflow (q = 0)."""
    assert q == 0.0
    return 2 * math.sqrt(1.0) / (a * math.sqrt(2 * 9.81))


def eval_role_counts() -> dict[str, int]:
    return {role: EVAL_LBFGSB_ROLES.count(role) for role in "satr"}


def _eval_inflow_svg() -> str:
    count = len(EVAL_NM_Q)
    first_negative = next(i for i, q in enumerate(EVAL_NM_Q) if q < 0) + 1
    parts = _open(
        "評価の番号と、渡された流入量 q",
        (
            "初期点 a=0.0001、q=0.0001 から、SciPy の三通りの使い方で"
            "水位の二乗和を最小化したときに、"
            "ツールへ渡された流入量 q を評価の番号ごとに描く。"
            f"fmin（Nelder–Mead）は {first_negative} 回目から負の q を渡し、"
            f"{first_negative} 回目と {first_negative + 1} 回目はエラーにならずに計算された。"
            f"{count} 回目は流入量 {_signed(EVAL_NM_Q[-1] * 1e4, 2)}×10⁻⁴ でタンクが空になり、"
            "ツールが失敗した。q の下限を0にした Nelder–Mead は12回目まで同じ点を通り、"
            f"13回目からは q=0 を渡し、{count} 回目に同じく失敗した。"
            "minimize の既定（BFGS）は4回目に "
            f"q={_signed(EVAL_BFGS_TRIAL[1], 2)} を渡して失敗した。"
            "BFGS の◆は、重ならないように少し上にずらして描く。"
        ),
        386,
    )
    px = _scale(1.0, float(count), 76, 410)
    py = _scale(-1.0, 1.25, 300, 128)
    parts.append(f'<path d="M76 128V300H410" fill="none" stroke="{GRID}"/>')
    for tick in (-1.0, 0.0, 0.5, 1.0):
        parts.append(_text(68, py(tick) + 5, f"{tick:g}".replace("-", "−"), "tick", "end"))
    for tick in (1, 4, 8, 12, 15):
        parts.append(_text(px(tick), 322, str(tick), "tick", "middle"))
    parts.append(f'<path d="M76 {py(0):.1f}H410" stroke="{GRID}" stroke-width="1.5"/>')
    fmin = [(px(i + 1), py(q * 1e4)) for i, q in enumerate(EVAL_NM_Q)]
    parts.append(_polyline(fmin, RING, 2))
    for index, (x, y) in enumerate(fmin[:-1]):
        fill = "#ffffff" if EVAL_NM_Q[index] < 0 else POINT
        parts.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.5" fill="{fill}" '
            f'stroke="{POINT}" stroke-width="2"/>'
        )
    last_x, last_y = fmin[-1]
    parts.append(
        f'<circle cx="{last_x:.1f}" cy="{last_y:.1f}" r="6" fill="{VIOLATION}" '
        f'stroke="{INK}" stroke-width="1.5"/>'
    )
    for index in range(first_negative - 1, count):
        x = px(index + 1)
        color = VIOLATION if index == count - 1 else UPDATE
        parts.append(
            f'<rect x="{x - 5:.1f}" y="{py(0) - 5:.1f}" width="10" height="10" '
            f'fill="#ffffff" stroke="{color}" stroke-width="2.5"/>'
        )
    for index in range(3):
        x, y = px(index + 1), py(1.0) - 14
        parts.append(
            f'<path d="M{x:.1f} {y - 6:.1f}L{x + 6:.1f} {y:.1f}L{x:.1f} {y + 6:.1f}'
            f'L{x - 6:.1f} {y:.1f}Z" fill="{UPDATE}"/>'
        )
    arrow_x = px(4)
    parts.append(
        f'<path d="M{arrow_x:.1f} {py(0.2):.1f}V298" stroke="{VIOLATION}" stroke-width="2.5"/>'
    )
    parts.append(
        f'<path d="M{arrow_x - 6:.1f} 290L{arrow_x:.1f} 300L{arrow_x + 6:.1f} 290" '
        f'fill="none" stroke="{VIOLATION}" stroke-width="2.5"/>'
    )
    parts.append(
        _text(
            arrow_x + 10,
            py(-0.55),
            f"4回目 q={_signed(EVAL_BFGS_TRIAL[1], 2)} m³/s（図の外）",
            "tick",
        )
    )
    parts.append(f'<circle cx="28" cy="55" r="5" fill="{POINT}"/>')
    parts.append(_text(42, 60, "fmin（白抜きは負の q）", "tick"))
    parts.append(
        f'<rect x="22" y="71" width="12" height="12" fill="#ffffff" '
        f'stroke="{UPDATE}" stroke-width="2.5"/>'
    )
    parts.append(_text(42, 82, "下限0つき Nelder–Mead", "tick"))
    parts.append(f'<path d="M28 93L34 99L28 105L22 99Z" fill="{UPDATE}"/>')
    parts.append(_text(42, 104, "minimize の既定（BFGS）", "tick"))
    parts.append(f'<circle cx="276" cy="55" r="6" fill="{VIOLATION}"/>')
    parts.append(_text(290, 60, "ツールが失敗", "tick"))
    parts.append(_text(20, 344, "縦軸 q（×10⁻⁴ m³/s）、横軸 評価の番号", "tick"))
    parts.append(_text(20, 368, "初期点 a=q=0.0001。SciPy 1.18.1", "tick"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


def _eval_breakdown_svg() -> str:
    counts = eval_role_counts()
    points = len(EVAL_LBFGSB_ROLES)
    parts = _open(
        f"反復{counts['a']}回の裏の評価{3 * points}回",
        (
            "a と q の上下限を 0.00001 から 0.001 にした L-BFGS-B が、"
            "ツールを呼んだ順に四角を並べる。"
            f"列は勾配を求めた点 {points} 個で、評価の順に左から並ぶ。"
            f"一段目は初期点 {counts['s']} 個、受け入れた反復点 {counts['a']} 個、"
            f"直線探索の途中の点 {counts['t']} 個"
            + (f"、前に呼んだ点の呼び直し {counts['r']} 個" if counts["r"] else "")
            + "。"
            f"二段目と三段目は、勾配を差分で作るために a と q を 1e-8 ずらした点 {2 * points} 個。"
        ),
        334,
    )
    fills = {"s": MUTED, "a": LINE, "t": RING, "r": UPDATE, "d": "#ffffff"}
    size, gap, left, top = 9, 2.5, 25, 92
    for column, role in enumerate(EVAL_LBFGSB_ROLES):
        for row, cell in enumerate((role, "d", "d")):
            x, y = left + column * (size + gap), top + row * (size + gap)
            parts.append(
                f'<rect x="{x:.1f}" y="{y:.1f}" width="{size}" height="{size}" rx="2" '
                f'fill="{fills[cell]}" stroke="{INK if cell != "d" else GRID}" '
                f'stroke-width="1"/>'
            )
    parts.append(_text(20, 64, "1列が勾配を求めた1点。左から評価の順", "tick"))
    rows_bottom = top + 3 * (size + gap)
    legend = (
        ("s", f"初期点 {counts['s']}"),
        ("a", f"受け入れた反復点 {counts['a']}"),
        ("t", f"直線探索の途中の点 {counts['t']}"),
        *((("r", f"前に呼んだ点の呼び直し {counts['r']}"),) if counts["r"] else ()),
        ("d", f"差分のための点 {2 * points}（各列の2段目と3段目）"),
    )
    for index, (role, label) in enumerate(legend):
        y = rows_bottom + 30 + index * 26
        parts.append(
            f'<rect x="20" y="{y - 14}" width="16" height="16" rx="3" fill="{fills[role]}" '
            f'stroke="{INK if role != "d" else GRID}" stroke-width="1.5"/>'
        )
        parts.append(_text(44, y, label, "tick"))
    parts.append(_text(20, 318, "SciPy 1.18.1、初期点 a=q=0.0001", "tick"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


FIGURES: dict[str, Callable[[], str]] = {
    "solver-evaluation-inflow.svg": _eval_inflow_svg,
    "solver-evaluation-breakdown.svg": _eval_breakdown_svg,
}
