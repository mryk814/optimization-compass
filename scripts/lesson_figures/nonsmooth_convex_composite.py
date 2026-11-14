"""Nonsmooth convex composite (content/concepts/nonsmooth-convex-composite.md): two sensor stations
A and B with two channels each. min 1/2 |A x - b|^2 + lam (|x_A| + |x_B|), solved by proximal
gradient from x = 0 with a fixed step.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence

from ._svg import GRID, INK, POINT, UPDATE, _open, _scale, _text

COMPOSITE_A = (
    (2.0, 1.0, 0.0, 1.0),
    (1.0, 2.0, 1.0, 0.0),
    (2.0, 0.0, 1.0, 0.0),
    (0.0, 1.0, 0.0, 1.0),
)
COMPOSITE_B = (4.0, 3.0, 3.0, 1.0)
COMPOSITE_LAMBDA = 9.0
COMPOSITE_STEP = 0.05
COMPOSITE_GROUPS = ((0, 1), (2, 3))


def composite_gradient(x: Sequence[float]) -> list[float]:
    """Gradient A^T (A x - b) of the smooth part 1/2 |A x - b|^2."""
    residual = [
        sum(a * v for a, v in zip(row, x, strict=True)) - b
        for row, b in zip(COMPOSITE_A, COMPOSITE_B, strict=True)
    ]
    return [sum(COMPOSITE_A[i][j] * residual[i] for i in range(4)) for j in range(4)]


def composite_objective(x: Sequence[float]) -> float:
    residual = [
        sum(a * v for a, v in zip(row, x, strict=True)) - b
        for row, b in zip(COMPOSITE_A, COMPOSITE_B, strict=True)
    ]
    smooth = 0.5 * sum(r * r for r in residual)
    return smooth + COMPOSITE_LAMBDA * sum(math.hypot(x[i], x[j]) for i, j in COMPOSITE_GROUPS)


def composite_prox(v: Sequence[float], tau: float) -> list[float]:
    """Block soft-threshold: shrink each group's length by tau, or send the group to 0."""
    out = [0.0] * 4
    for i, j in COMPOSITE_GROUPS:
        length = math.hypot(v[i], v[j])
        scale = max(0.0, 1.0 - tau / length) if length > 0 else 0.0
        out[i], out[j] = scale * v[i], scale * v[j]
    return out


def composite_step(x: Sequence[float]) -> tuple[list[float], list[float]]:
    """One proximal gradient step: the gradient-stepped point v and prox(v)."""
    grad = composite_gradient(x)
    v = [xi - COMPOSITE_STEP * gi for xi, gi in zip(x, grad, strict=True)]
    return v, composite_prox(v, COMPOSITE_STEP * COMPOSITE_LAMBDA)


def composite_solution(tolerance: float = 1e-8) -> tuple[list[float], int]:
    """Iterate from 0 until the proximal gradient mapping |G| drops below the tolerance."""
    x = [0.0] * 4
    for count in range(1, 100000):
        _, moved = composite_step(x)
        x_next = moved
        mapping = math.hypot(*((a - b) / COMPOSITE_STEP for a, b in zip(x, x_next, strict=True)))
        x = x_next
        if mapping < tolerance:
            return x, count
    raise RuntimeError("proximal gradient did not settle")


def _composite_panel(top: float, title: str, indices: tuple[int, int], names: str) -> list[str]:
    """One group's v-plane (112.5 px per unit, -0.55 to 1.05): the zero disc, v, and prox(v)."""
    x = [0.0] * 4
    v, moved = composite_step(x)
    i, j = indices
    radius = COMPOSITE_STEP * COMPOSITE_LAMBDA
    length = math.hypot(v[i], v[j])
    px = _scale(-0.55, 1.05, 56, 236)
    py = _scale(1.05, -0.55, top + 12, top + 192)
    unit = px(1.0) - px(0.0)
    parts = [
        _text(20, top, title, "title"),
        f'<rect x="56" y="{top + 12:.1f}" width="180" height="180" fill="#ffffff" '
        f'stroke="{GRID}"/>',
        f'<circle cx="{px(0):.1f}" cy="{py(0):.1f}" r="{radius * unit:.1f}" fill="#f2c9b4" '
        f'stroke="{UPDATE}" stroke-width="1.5"/>',
    ]
    for value in (0.0, 0.5, 1.0):
        parts.append(_text(px(value), top + 212, f"{value:g}", "tick", "middle"))
        parts.append(_text(50, py(value) + 5, f"{value:g}", "tick", "end"))
    parts.append(_text(250, top + 217, f"v{names[0]} 軸", "tick"))
    parts.append(_text(62, top + 30, f"v{names[1]}", "tick"))
    ox, oy = px(0), py(0)
    vx, vy = px(v[i]), py(v[j])
    mx, my = px(moved[i]), py(moved[j])
    parts.append(
        f'<path d="M{vx:.1f} {vy:.1f}L{mx:.1f} {my:.1f}" stroke="{UPDATE}" stroke-width="3"/>'
    )
    parts.append(f'<circle cx="{vx:.1f}" cy="{vy:.1f}" r="6" fill="{POINT}"/>')
    parts.append(f'<circle cx="{mx:.1f}" cy="{my:.1f}" r="7" fill="{UPDATE}"/>')
    parts.append(f'<circle cx="{ox:.1f}" cy="{oy:.1f}" r="2.5" fill="{INK}"/>')
    inside = length <= radius
    parts.append(_text(250, top + 52, f"v = ({v[i]:g}, {v[j]:g})", "", "start"))
    parts.append(
        _text(250, top + 80, f"長さ {length:.3f} {'≤' if inside else '>'} {radius:g}", "", "start")
    )
    if inside:
        parts.append(_text(250, top + 108, "→ (0, 0)", "note", "start"))
        parts.append(_text(250, top + 136, "円の中は丸ごと 0", "note", "start"))
    else:
        parts.append(_text(250, top + 108, f"→ ({moved[i]:.3f}, {moved[j]:.3f})", "note", "start"))
        parts.append(_text(250, top + 136, f"長さが {radius:g} 縮む", "note", "start"))
    return parts


def _composite_group_svg() -> str:
    v, moved = composite_step([0.0] * 4)
    radius = COMPOSITE_STEP * COMPOSITE_LAMBDA
    lengths = [math.hypot(v[i], v[j]) for i, j in COMPOSITE_GROUPS]
    parts = _open(
        "グループごとに縮める",
        (
            f"最初の一歩の v。駅Aの v は ({v[0]:g}, {v[1]:g}) で長さ {lengths[0]:.3f}、"
            f"半径 {radius:g} の円の外なので長さが {radius:g} 縮み、"
            f"({moved[0]:.3f}, {moved[1]:.3f}) になります。"
            f"駅Bの v は ({v[2]:g}, {v[3]:g}) で長さ {lengths[1]:.3f}、円の中なので (0, 0) です。"
        ),
        610,
    )
    parts.extend(_composite_panel(66, "駅A（x₁, x₂）", COMPOSITE_GROUPS[0], "₁₂"))
    parts.extend(_composite_panel(316, "駅B（x₃, x₄）", COMPOSITE_GROUPS[1], "₃₄"))
    parts.append(_text(20, 566, f"橙の円：半径 {radius:g}。中の点は 0 に落ちる", "note"))
    parts.append(_text(20, 590, "紺の丸：v、橙の丸：prox(v)", "note"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


FIGURES: dict[str, Callable[[], str]] = {
    "composite-group-shrink.svg": _composite_group_svg,
}
