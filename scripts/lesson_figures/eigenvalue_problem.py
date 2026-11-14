"""Eigenvalue problem (content/concepts/eigenvalue-problem.md): five stakes along a straight fence,
read off a map with errors in both coordinates. The fence's unit normal n minimises the sum of
squared perpendicular distances n^T M n, M = sum of (p - mean)(p - mean)^T.
"""

from __future__ import annotations

import math
from collections.abc import Callable

from ._svg import GRID, INK, LINE, MUTED, POINT, UPDATE, _open, _polyline, _scale, _text

EIG_POINTS = ((3.0, 2.0), (3.0, 3.0), (4.0, 1.0), (5.0, 4.0), (5.0, 5.0))


def eig_centre() -> tuple[float, float]:
    count = len(EIG_POINTS)
    return (sum(p[0] for p in EIG_POINTS) / count, sum(p[1] for p in EIG_POINTS) / count)


def eig_scatter() -> tuple[float, float, float]:
    """(a, b, c) of the centred scatter matrix [[a, b], [b, c]]."""
    cx, cy = eig_centre()
    a = sum((x - cx) ** 2 for x, _ in EIG_POINTS)
    b = sum((x - cx) * (y - cy) for x, y in EIG_POINTS)
    c = sum((y - cy) ** 2 for _, y in EIG_POINTS)
    return a, b, c


def eig_values() -> tuple[float, float]:
    a, b, c = eig_scatter()
    mean, radius = (a + c) / 2, math.hypot((a - c) / 2, b)
    return mean - radius, mean + radius


def eig_perpendicular_sum(angle_deg: float) -> float:
    """Sum of squared perpendicular distances to the line through the centre at this angle."""
    a, b, c = eig_scatter()
    theta = math.radians(angle_deg)
    nx, ny = -math.sin(theta), math.cos(theta)  # unit normal of the line
    return a * nx * nx + 2 * b * nx * ny + c * ny * ny


def eig_best_angle() -> float:
    """Direction of the fitted line in degrees in [0, 180): the eigenvector of the larger value."""
    a, b, _ = eig_scatter()
    _, upper = eig_values()
    return math.degrees(math.atan2(upper - a, b)) % 180


def _eig_fence_svg() -> str:
    lower, upper = eig_values()
    best = eig_best_angle()
    cx, cy = eig_centre()
    a, b, _ = eig_scatter()
    vertical_angle = math.degrees(math.atan(b / a))  # the y-on-x least-squares line
    vertical_sum = eig_perpendicular_sum(vertical_angle)
    parts = _open(
        "塀の向きを変えると、距離の二乗和が波打つ",
        (
            f"5本の杭と、重心 ({cx:g}, {cy:g}) を通る直線。"
            f"傾き{math.tan(math.radians(best)):g}の直線（向き {best:.1f}°）で、"
            f"杭から直線への垂直な距離の二乗和が最小の {lower:g} になる。"
            f"二乗和は向きとともに {lower:g} と {upper:g} の間を波打ち、"
            f"縦のずれで当てはめた傾き1の直線（45°）では {vertical_sum:g}。"
        ),
        652,
    )
    unit = 34
    px = _scale(1.0, 7.0, 220 - 3 * unit, 220 + 3 * unit)
    py = _scale(0.0, 6.0, 288, 288 - 6 * unit)
    parts.append(_text(20, 64, "① 杭の位置と塀の線"))
    parts.append(
        f'<rect x="{px(1):.1f}" y="{py(6):.1f}" width="{6 * unit}" height="{6 * unit}" '
        f'fill="#ffffff" stroke="{GRID}"/>'
    )
    for tick in range(1, 8):
        parts.append(_text(px(tick), py(0) + 20, str(tick), "tick", "middle"))
    for tick in range(0, 7, 2):
        parts.append(_text(px(1) - 8, py(tick) + 5, str(tick), "tick", "end"))
    dx, dy = math.cos(math.radians(best)), math.sin(math.radians(best))
    span = 3.0 / dy
    parts.append(
        _polyline(
            [(px(cx - span * dx), py(cy - span * dy)), (px(cx + span * dx), py(cy + span * dy))],
            LINE,
            3,
        )
    )
    for x, y in EIG_POINTS:
        along = (x - cx) * dx + (y - cy) * dy
        fx, fy = cx + along * dx, cy + along * dy
        parts.append(
            f'<path d="M{px(x):.1f} {py(y):.1f}L{px(fx):.1f} {py(fy):.1f}" '
            f'stroke="{UPDATE}" stroke-width="3"/>'
        )
        parts.append(f'<circle cx="{px(x):.1f}" cy="{py(y):.1f}" r="6" fill="{POINT}"/>')
    parts.append(
        f'<circle cx="{px(cx):.1f}" cy="{py(cy):.1f}" r="5" fill="#ffffff" stroke="{INK}" '
        'stroke-width="2"/>'
    )
    parts.append(_text(330, 120, f"傾き {math.tan(math.radians(best)):g}", "note"))
    parts.append(_text(330, 144, f"二乗和 {lower:g}", "note"))
    parts.append(_text(330, 190, "○ 重心", "tick"))
    parts.append(_text(330, 212, f"({cx:g}, {cy:g})", "tick"))

    parts.append(_text(20, 350, "② 線の向きと距離の二乗和"))
    gx = _scale(0.0, 180.0, 60, 410)
    gy = _scale(0.0, 14.0, 560, 380)
    parts.append(f'<path d="M60 380V560H410" fill="none" stroke="{GRID}"/>')
    for angle in (0, 45, 90, 135, 180):
        parts.append(_text(gx(angle), 580, f"{angle}°", "tick", "middle"))
    for value in (0, 4, 8, 12):
        parts.append(_text(52, gy(value) + 5, str(value), "tick", "end"))
    parts.append(
        _polyline(
            [(gx(angle), gy(eig_perpendicular_sum(angle))) for angle in range(0, 181, 2)],
            LINE,
            3,
        )
    )
    worst = (best + 90) % 180
    marks = (
        (best, lower, UPDATE, f"{best:.1f}° で最小 {lower:g}", "start", 10, 26),
        (worst, upper, MUTED, f"{worst:.1f}° で最大 {upper:g}", "end", -10, 2),
        (vertical_angle, vertical_sum, POINT, "", "end", 0, 0),
    )
    for angle, value, color, label, anchor, shift, lift in marks:
        parts.append(f'<circle cx="{gx(angle):.1f}" cy="{gy(value):.1f}" r="6" fill="{color}"/>')
        parts.append(_text(gx(angle) + shift, gy(value) + lift, label, "tick", anchor))
    parts.append(_text(20, 612, f"紺の点：45°（縦のずれで当てはめた直線）で {vertical_sum:g}"))
    parts.append(_text(20, 636, f"二乗和は {lower:g} と {upper:g} の間を行き来する", "note"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


def _eig_condition_svg() -> str:
    """Two unit normals n and the arrows M n: parallel only at the eigenvector."""
    a, b, c = eig_scatter()
    lower, _ = eig_values()
    best = eig_best_angle()
    normal_best = best - 90
    parts = _open(
        "最小の向きでは、M n が n と同じ向きになる",
        (
            f"長さ1の向き n と、行列 M=[[{a:g},{b:g}],[{b:g},{c:g}]] を掛けた M n の矢印。"
            f"n=(1,0) では M n=({a:g},{b:g}) で、n と向きが違う。"
            f"二乗和が最小の向き n=(2,−1)/√5 では M n={lower:g}n で、同じ向きを指す。"
        ),
        360,
    )
    centres = ((120.0, 190.0), (320.0, 190.0))
    scale = 14.0
    cases = (
        (0.0, "n=(1, 0)", f"M n=({a:g}, {b:g})"),
        (normal_best, "n=(2, −1)/√5", f"M n={lower:g} n"),
    )
    parts.append(
        "<defs>"
        f'<marker id="eig-head-n" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="5" '
        f'markerHeight="5" orient="auto"><path d="M0 0L10 5L0 10z" fill="{POINT}"/></marker>'
        f'<marker id="eig-head-m" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="5" '
        f'markerHeight="5" orient="auto"><path d="M0 0L10 5L0 10z" fill="{UPDATE}"/></marker>'
        "</defs>"
    )
    for (ox, oy), (angle, n_label, mn_label) in zip(centres, cases, strict=True):
        theta = math.radians(angle)
        nx, ny = math.cos(theta), math.sin(theta)
        mx, my = a * nx + b * ny, b * nx + c * ny
        radius = 4 * scale
        parts.append(
            f'<circle cx="{ox}" cy="{oy}" r="{radius}" fill="none" stroke="{GRID}" '
            'stroke-width="1.5"/>'
        )
        for (vx, vy), color, factor, head in (
            ((nx, ny), POINT, radius, "n"),
            ((mx, my), UPDATE, scale, "m"),
        ):
            ex, ey = ox + vx * factor, oy - vy * factor
            parts.append(
                f'<path d="M{ox} {oy}L{ex:.1f} {ey:.1f}" stroke="{color}" stroke-width="3" '
                f'marker-end="url(#eig-head-{head})"/>'
            )
        parts.append(_text(ox, 300, n_label, "", "middle"))
        parts.append(_text(ox, 324, mn_label, "note", "middle"))
    parts.append(_text(20, 64, "紺：長さ1の向き n（円の上）　橙：M n", "tick"))
    parts.append(_text(20, 350, "同じ向きのとき、円に沿って回す向きの傾きが0", "tick"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


FIGURES: dict[str, Callable[[], str]] = {
    "eigenvalue-fence-direction.svg": _eig_fence_svg,
    "eigenvalue-parallel-condition.svg": _eig_condition_svg,
}
