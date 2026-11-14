"""Nonconvex QP (content/concepts/nonconvex-qp-qcqp.md): two knobs x1, x2 in [-1, 1] and the loss
f(x) = x1^2 + x2^2 - 3 x1 x2 + 0.5 (x1 + x2). The Hessian 2Q = [[2, -3], [-3, 2]] has eigenvalues 5
and -1, so f is not convex; the box has two local minima, (-1, -1) and (1, 1).
"""

from __future__ import annotations

import html
from collections.abc import Callable

from ._svg import LINE, MUTED, POINT, RING, UPDATE, _contour_segments, _open, _scale, _text

NCQP_STEP = 0.1  # projected-gradient step length used for the basin picture and the article
NCQP_ITERATIONS = 500
NCQP_GRID = 19  # starting points per axis; the cell centres never sit on x1 + x2 = 1


def ncqp_value(x1: float, x2: float) -> float:
    return x1 * x1 + x2 * x2 - 3 * x1 * x2 + 0.5 * (x1 + x2)


def ncqp_gradient(x1: float, x2: float) -> tuple[float, float]:
    return 2 * x1 - 3 * x2 + 0.5, 2 * x2 - 3 * x1 + 0.5


def ncqp_projected_gradient(
    start: tuple[float, float], step: float = NCQP_STEP, iterations: int = NCQP_ITERATIONS
) -> tuple[float, float]:
    """Projected gradient descent on the box [-1, 1]^2 (a local method: it stops at KKT points)."""
    x1, x2 = start
    for _ in range(iterations):
        g1, g2 = ncqp_gradient(x1, x2)
        x1 = min(1.0, max(-1.0, x1 - step * g1))
        x2 = min(1.0, max(-1.0, x2 - step * g2))
    return x1, x2


def ncqp_starts() -> list[tuple[float, float]]:
    centres = [-1 + (2 * i + 1) / NCQP_GRID for i in range(NCQP_GRID)]
    return [(a, b) for a in centres for b in centres]


def ncqp_basins() -> dict[str, object]:
    """Where projected gradient ends from each start: the corner (-1, -1) or the corner (1, 1)."""
    ends = [ncqp_projected_gradient(start) for start in ncqp_starts()]
    low = [start for start, end in zip(ncqp_starts(), ends, strict=True) if end[0] < 0]
    high = [start for start, end in zip(ncqp_starts(), ends, strict=True) if end[0] > 0]
    return {"low": low, "high": high, "other": len(ends) - len(low) - len(high)}


def _halo_text(x: float, y: float, body: str, anchor: str = "start") -> str:
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" '
        'style="paint-order:stroke;stroke:#f7f8f3;stroke-width:4px;stroke-linejoin:round">'
        f"{html.escape(body)}</text>"
    )


def _ncqp_frame(top: float, title: str) -> tuple[list[str], Callable, Callable]:
    """One square plot of the box [-1, 1]^2 (150 px per unit) with ticks; returns the x/y maps."""
    px = _scale(-1.2, 1.2, 80, 380)
    py = _scale(1.2, -1.2, top + 14, top + 314)
    parts = [
        _text(20, top, title, "title"),
        f'<rect x="{px(-1):.1f}" y="{py(1):.1f}" width="{px(1) - px(-1):.1f}" '
        f'height="{py(-1) - py(1):.1f}" fill="#ffffff" stroke="{MUTED}" stroke-width="2"/>',
    ]
    for value in (-1, 0, 1):
        parts.append(_text(px(value), top + 338, f"{value}", "tick", "middle"))
        parts.append(_text(72, py(value) + 5, f"{value}", "tick", "end"))
    parts.append(_text(396, top + 338, "x₁", "tick", "end"))
    parts.append(_text(24, top + 36, "x₂", "tick"))
    return parts, px, py


def _ncqp_basins_svg() -> str:
    basins = ncqp_basins()
    low, high = basins["low"], basins["high"]
    parts = _open(
        "非凸QPの局所解は二つ",
        (
            "二つのつまみ x1, x2 を -1 から 1 まで動かす損失 "
            "f = x1^2 + x2^2 - 3 x1 x2 + 0.5 (x1 + x2) の等高線と、射影勾配法の行き先です。"
            f"角 (-1, -1) の f = {ncqp_value(-1, -1):g} と角 (1, 1) の f = {ncqp_value(1, 1):g} が"
            f"局所解で、鞍点 (0.5, 0.5) の f = {ncqp_value(0.5, 0.5):g} です。"
            f"{NCQP_GRID * NCQP_GRID}個の出発点のうち、{len(high)}個が f = 0 の局所解へ、"
            f"{len(low)}個が f = -2 の局所解へ着きます。"
        ),
        920,
    )
    top_parts, px, py = _ncqp_frame(66, "損失の等高線")
    parts.extend(top_parts)
    for level in (-1.5, -1.0, -0.5, 0.0, 1.0, 2.0, 4.0):
        segments = _contour_segments(ncqp_value, level, (-1, 1), (-1, 1), (80, 80))
        data = "".join(
            f"M{px(a[0]):.1f} {py(a[1]):.1f}L{px(b[0]):.1f} {py(b[1]):.1f}" for a, b in segments
        )
        parts.append(f'<path d="{data}" fill="none" stroke="{RING}" stroke-width="1.5"/>')
    for corner in ((1, -1), (-1, 1)):
        parts.append(
            f'<circle cx="{px(corner[0]):.1f}" cy="{py(corner[1]):.1f}" r="5" fill="#f7f8f3" '
            f'stroke="{MUTED}" stroke-width="2"/>'
        )
    parts.append(f'<circle cx="{px(-1):.1f}" cy="{py(-1):.1f}" r="8" fill="{LINE}"/>')
    parts.append(f'<circle cx="{px(1):.1f}" cy="{py(1):.1f}" r="8" fill="{UPDATE}"/>')
    sx, sy = px(0.5), py(0.5)
    parts.append(
        f'<path d="M{sx:.1f} {sy - 8:.1f}L{sx + 8:.1f} {sy:.1f}L{sx:.1f} {sy + 8:.1f}'
        f'L{sx - 8:.1f} {sy:.1f}Z" fill="{POINT}"/>'
    )
    parts.append(_halo_text(px(-1) + 14, py(-1) - 12, f"局所解 f={ncqp_value(-1, -1):g}"))
    parts.append(_halo_text(px(1) - 14, py(1) + 26, f"局所解 f={ncqp_value(1, 1):g}", "end"))
    parts.append(_halo_text(sx - 14, sy + 26, f"鞍点 f={ncqp_value(0.5, 0.5):g}", "end"))
    parts.append(_text(20, 422, "線は f=-1.5, -1, -0.5, 0, 1, 2, 4。白抜きの角は f=5", "note"))
    low_parts, qx, qy = _ncqp_frame(484, "出発点ごとの行き先")
    parts.extend(low_parts)
    parts.append(
        f'<path d="M{qx(0):.1f} {qy(1):.1f}L{qx(1):.1f} {qy(0):.1f}" stroke="{MUTED}" '
        'stroke-width="2" fill="none"/>'
    )
    for x1, x2 in low:
        parts.append(f'<circle cx="{qx(x1):.1f}" cy="{qy(x2):.1f}" r="3.5" fill="{LINE}"/>')
    for x1, x2 in high:
        parts.append(
            f'<rect x="{qx(x1) - 3.5:.1f}" y="{qy(x2) - 3.5:.1f}" width="7" height="7" '
            f'fill="{UPDATE}"/>'
        )
    parts.append(_text(20, 858, f"緑の丸 {len(low)}点：f=-2 の局所解へ", "note"))
    parts.append(_text(20, 882, f"橙の四角 {len(high)}点：f=0 の局所解へ", "note"))
    parts.append(_text(20, 906, "灰の線：境目 x₁+x₂=1", "note"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


FIGURES: dict[str, Callable[[], str]] = {
    "nonconvex-qp-basins.svg": _ncqp_basins_svg,
}
