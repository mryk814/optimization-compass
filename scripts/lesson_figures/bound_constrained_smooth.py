"""Smooth bound-constrained (content/concepts/bound-constrained-smooth.md): a greenhouse heater x1
and fan x2, both in [0, 1]. f(x) = (x1-2)^2 + 2(x2-1)^2 + 2 x1 x2.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence

from ._svg import GRID, LINE, POINT, RING, UPDATE, _contour_segments, _open, _scale, _text

BOX_LOWER = (0.0, 0.0)
BOX_UPPER = (1.0, 1.0)


def box_value(x1: float, x2: float) -> float:
    return (x1 - 2) ** 2 + 2 * (x2 - 1) ** 2 + 2 * x1 * x2


def box_gradient(x1: float, x2: float) -> tuple[float, float]:
    return 2 * (x1 - 2) + 2 * x2, 4 * (x2 - 1) + 2 * x1


def _box_project(x: Sequence[float]) -> tuple[float, float]:
    return (
        min(max(x[0], BOX_LOWER[0]), BOX_UPPER[0]),
        min(max(x[1], BOX_LOWER[1]), BOX_UPPER[1]),
    )


def box_solution(step: float = 0.2, tolerance: float = 1e-12) -> tuple[float, float]:
    """Projected gradient from (0, 0) until the projected step stops moving."""
    x = BOX_LOWER
    for _ in range(1000):
        g = box_gradient(*x)
        moved = _box_project((x[0] - step * g[0], x[1] - step * g[1]))
        if math.hypot(moved[0] - x[0], moved[1] - x[1]) < tolerance:
            return moved
        x = moved
    raise RuntimeError("projected gradient did not settle")


def box_unconstrained_minimum() -> tuple[float, float]:
    """Solve grad f = 0, i.e. [[2, 2], [2, 4]] x = [4, 4], by Cramer's rule."""
    det = 2 * 4 - 2 * 2
    return (4 * 4 - 2 * 4) / det, (2 * 4 - 2 * 4) / det


def _bound_constrained_box_svg() -> str:
    solution = box_solution()
    free = box_unconstrained_minimum()
    clipped = _box_project(free)
    solution = (round(solution[0], 9) + 0.0, round(solution[1], 9) + 0.0)
    grad = tuple(round(value, 9) + 0.0 for value in box_gradient(*solution))
    px = _scale(-0.25, 2.25, 56, 416)  # 144 px per unit on both axes
    py = _scale(1.25, -0.5, 52, 304)
    parts = _open(
        "箱の縁で止まる解",
        (
            f"f(x)=(x1-2)^2+2(x2-1)^2+2x1x2 の等高線と、箱 0≤x1,x2≤1。"
            f"制約なしの最小点は箱の外の ({free[0]:g}, {free[1]:g})、f={box_value(*free):g}。"
            f"切り詰めた点 ({clipped[0]:g}, {clipped[1]:g}) は f={box_value(*clipped):g}。"
            f"解は縁の上の ({solution[0]:.2g}, {solution[1]:.2g}) で f={box_value(*solution):g}、"
            f"そこでの −∇f は ({0.0 - grad[0]:g}, {0.0 - grad[1]:g}) で箱の外を向きます。"
        ),
        444,
    )
    parts.append(f'<path d="M56 52V304H416V52Z" fill="none" stroke="{GRID}"/>')
    x0, x1_ = px(BOX_LOWER[0]), px(BOX_UPPER[0])
    y0, y1_ = py(BOX_LOWER[1]), py(BOX_UPPER[1])
    parts.append(
        f'<rect x="{x0:.1f}" y="{y1_:.1f}" width="{x1_ - x0:.1f}" height="{y0 - y1_:.1f}" '
        f'fill="#e3eee6" stroke="{LINE}" stroke-width="2.5"/>'
    )
    for level in (2.25, 3.0, 4.0, 6.0):
        segments = _contour_segments(box_value, level, (-0.25, 2.25), (-0.5, 1.25), (150, 105))
        data = "".join(
            f"M{px(a[0]):.1f} {py(a[1]):.1f}L{px(b[0]):.1f} {py(b[1]):.1f}" for a, b in segments
        )
        # The level through the clipped point is navy, like the clipped point itself.
        style = (
            f'stroke="{POINT}" stroke-width="1.5"'
            if level == box_value(*clipped)
            else f'stroke="{RING}" stroke-width="1.5"'
        )
        parts.append(f'<path d="{data}" fill="none" {style}/>')
    level = box_value(*solution)
    segments = _contour_segments(box_value, level, (-0.25, 2.25), (-0.5, 1.25), (150, 105))
    data = "".join(
        f"M{px(a[0]):.1f} {py(a[1]):.1f}L{px(b[0]):.1f} {py(b[1]):.1f}" for a, b in segments
    )
    parts.append(f'<path d="{data}" fill="none" stroke="{UPDATE}" stroke-width="2"/>')
    for value in (0, 1, 2):
        parts.append(_text(px(value), 324, f"{value}", "tick", "middle"))
    for value in (0, 1):
        parts.append(_text(48, py(value) + 5, f"{value}", "tick", "end"))
    parts.append(_text(416, 344, "x₁ 暖房", "tick", "end"))
    parts.append(_text(62, 70, "x₂ 換気扇", "tick"))
    # −∇f at the solution, 0.4 units per unit of gradient.
    sx, sy = px(solution[0]), py(solution[1])
    ex, ey = px(solution[0] - 0.4 * grad[0]), py(solution[1] - 0.4 * grad[1])
    parts.append(
        f'<path d="M{sx:.1f} {sy:.1f}L{ex - 9:.1f} {ey:.1f}" stroke="{UPDATE}" stroke-width="3"/>'
    )
    parts.append(
        f'<path d="M{ex:.1f} {ey:.1f}L{ex - 11:.1f} {ey - 6:.1f}L{ex - 11:.1f} {ey + 6:.1f}Z" '
        f'fill="{UPDATE}"/>'
    )
    parts.append(_text(ex + 4, ey - 10, "−∇f", "", "middle"))
    parts.append(f'<circle cx="{px(free[0]):.1f}" cy="{py(free[1]):.1f}" r="6" fill="{POINT}"/>')
    parts.append(
        f'<circle cx="{px(clipped[0]):.1f}" cy="{py(clipped[1]):.1f}" r="6" fill="#f7f8f3" '
        f'stroke="{POINT}" stroke-width="2.5"/>'
    )
    parts.append(f'<circle cx="{sx:.1f}" cy="{sy:.1f}" r="7" fill="{UPDATE}"/>')
    parts.append(_text(px(free[0]), py(free[1]) + 26, "制約なしの最小点", "", "end"))
    parts.append(_text(px(clipped[0]) - 12, py(clipped[1]) - 10, "切り詰めた点", "", "end"))
    parts.append(_text(sx - 12, sy - 10, "解", "", "end"))
    parts.append(
        _text(
            20, 372, f"橙：解 ({solution[0]:g}, {solution[1]:g}) と f = {level:g} の等高線", "note"
        )
    )
    parts.append(_text(20, 396, f"紺の線：切り詰めた点を通る f = {box_value(*clipped):g} の等高線"))
    parts.append(_text(20, 420, f"紺の丸：制約なしの最小点、f = {box_value(*free):g}"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


FIGURES: dict[str, Callable[[], str]] = {
    "bound-constrained-box.svg": _bound_constrained_box_svg,
}
