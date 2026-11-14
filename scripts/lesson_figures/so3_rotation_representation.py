"""SO(3) and its Lie algebra (content/concepts/so3-rotation-representation.md): a plane rotation
[[a, -b], [b, a]] is the point (a, b). Rotations fill the unit circle, the Lie algebra is the
tangent line at I, and exp wraps the line onto the circle by arc length.
"""

from __future__ import annotations

import math
from collections.abc import Callable

from ._svg import GRID, INK, LINE, POINT, UPDATE, _open, _text

SO2_TICKS = (0.5, 1.0, 1.5, 2.0)
SO2_SHOWN = 1.0


def so2_points(theta: float) -> dict[str, float]:
    """The tangent point I + theta J and the rotation exp(theta J), with the tangent point's det."""
    return {
        "line_a": 1.0,
        "line_b": theta,
        "line_det": 1.0 + theta * theta,
        "exp_a": math.cos(theta),
        "exp_b": math.sin(theta),
        "exp_det": math.cos(theta) ** 2 + math.sin(theta) ** 2,
    }


def _so2_circle_svg() -> str:
    shown = so2_points(SO2_SHOWN)
    cx, cy, radius = 150.0, 290.0, 100.0

    def at(a: float, b: float) -> tuple[float, float]:
        return cx + radius * a, cy - radius * b

    parts = _open(
        "平面の回転は円、リー代数は接線",
        (
            "平面の回転行列 [[a, −b], [b, a]] を点 (a, b) で表した図。回転は半径1の円の上に並び、"
            "単位行列 I は (1, 0)。I での接線の点 I+θJ は円の外にあり、"
            f"θ={SO2_SHOWN:g} の I+J は ({shown['line_a']:g}, {shown['line_b']:g})、"
            f"行列式 {shown['line_det']:g}。exp(θJ) は接線を円に巻き付けた点で、"
            f"θ={SO2_SHOWN:g} の exp(J) は ({shown['exp_a']:.3f}, {shown['exp_b']:.3f})、"
            f"I からの弧の長さは {SO2_SHOWN:g}。"
            "目盛り 0.5, 1, 1.5, 2 は接線と円で同じ長さに対応する。"
        ),
        520,
    )
    parts.append(f'<path d="M30 {cy}H430M{cx} 52V408" stroke="{GRID}"/>')
    parts.append(_text(430, cy - 8, "a", "tick", "end"))
    parts.append(_text(cx + 8, 64, "b", "tick"))
    parts.append(
        f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="none" stroke="{LINE}" stroke-width="2"/>'
    )
    top, bottom = at(1.0, 2.25), at(1.0, -0.6)
    parts.append(
        f'<path d="M{top[0]:.1f} {top[1]:.1f}V{bottom[1]:.1f}" stroke="{UPDATE}" '
        'stroke-width="2.5"/>'
    )
    parts.append(_text(top[0] + 10, top[1] + 6, "接線 θJ", "", "start"))
    arc_end = at(shown["exp_a"], shown["exp_b"])
    parts.append(
        f'<path d="M{at(1.0, 0.0)[0]:.1f} {cy:.1f}A{radius} {radius} 0 0 0 '
        f'{arc_end[0]:.2f} {arc_end[1]:.2f}" fill="none" stroke="{POINT}" stroke-width="5"/>'
    )
    for theta in SO2_TICKS:
        point = so2_points(theta)
        lx, ly = at(point["line_a"], point["line_b"])
        ex, ey = at(point["exp_a"], point["exp_b"])
        parts.append(f'<path d="M{lx - 6:.1f} {ly:.1f}H{lx + 6:.1f}" stroke="{UPDATE}"/>')
        parts.append(_text(lx + 12, ly + 5, f"{theta:g}", "tick"))
        parts.append(f'<circle cx="{ex:.2f}" cy="{ey:.2f}" r="3.5" fill="{POINT}"/>')
        ox, oy = at(0.8 * point["exp_a"], 0.8 * point["exp_b"])
        parts.append(_text(ox, oy + 5, f"{theta:g}", "tick", "middle"))
    ix, iy = at(1.0, 0.0)
    parts.append(f'<circle cx="{ix}" cy="{iy}" r="6" fill="{INK}"/>')
    parts.append(_text(ix + 12, iy + 22, "I", ""))
    lx, ly = at(shown["line_a"], shown["line_b"])
    parts.append(
        f'<circle cx="{lx}" cy="{ly}" r="7" fill="#f3d2b5" stroke="{UPDATE}" stroke-width="2.5"/>'
    )
    parts.append(_text(lx + 32, ly + 5, "I+J"))
    parts.append(
        f'<circle cx="{arc_end[0]:.2f}" cy="{arc_end[1]:.2f}" r="7" fill="{POINT}" '
        f'stroke="{INK}" stroke-width="1.5"/>'
    )
    label = at(1.27 * shown["exp_a"], 1.27 * shown["exp_b"])
    parts.append(_text(label[0], label[1], "exp(J)", "", "middle"))
    parts.append(_text(20, 438, "点 (a, b) は回転行列 [a −b; b a] を表す"))
    parts.append(_text(20, 464, "接線の上は自由に動けるが、円の外（回転でない）"))
    parts.append(_text(20, 490, "exp は接線を円に巻き付ける：長さ θ → θ rad 回す"))
    parts.append(
        _text(
            20,
            514,
            f"θ={SO2_SHOWN:g}：I+J は行列式 {shown['line_det']:g}、exp(J) は弧の長さ {SO2_SHOWN:g}",
            "note",
        )
    )
    parts.append("</svg>")
    return "".join(parts) + "\n"


FIGURES: dict[str, Callable[[], str]] = {
    "so3-lie-algebra-circle.svg": _so2_circle_svg,
}
