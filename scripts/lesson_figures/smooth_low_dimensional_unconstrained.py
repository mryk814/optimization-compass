"""Smooth low-dimensional unconstrained (content/concepts/smooth-low-dimensional-unconstrained.md):
f(x) = (x1^2 - 1)^2 + x1 x2 + 2 x2^2 has a saddle at the origin and two valley bottoms.
"""

from __future__ import annotations

import math
from collections.abc import Callable

from ._svg import (
    GRID,
    LINE,
    MUTED,
    POINT,
    RING,
    UPDATE,
    _contour_segments,
    _open,
    _polyline,
    _scale,
    _text,
)

LANDSCAPE_START_A = (0.5, 1.0)
LANDSCAPE_START_B = (0.2, 0.1)


def landscape_value(x1: float, x2: float) -> float:
    return (x1 * x1 - 1) ** 2 + x1 * x2 + 2 * x2 * x2


def landscape_gradient(x1: float, x2: float) -> tuple[float, float]:
    return 4 * x1 * (x1 * x1 - 1) + x2, x1 + 4 * x2


def landscape_newton_path(
    start: tuple[float, float], tolerance: float = 1e-8
) -> list[tuple[float, float]]:
    """Pure Newton iteration with the exact 2x2 Hessian [[12 x1^2 - 4, 1], [1, 4]]."""
    x1, x2 = start
    path = [(x1, x2)]
    while math.hypot(*landscape_gradient(x1, x2)) >= tolerance and len(path) < 50:
        g1, g2 = landscape_gradient(x1, x2)
        h11, h12, h22 = 12 * x1 * x1 - 4, 1.0, 4.0
        det = h11 * h22 - h12 * h12
        x1 -= (h22 * g1 - h12 * g2) / det
        x2 -= (-h12 * g1 + h11 * g2) / det
        path.append((x1, x2))
    return path


def _smooth_landscape_svg() -> str:
    root = math.sqrt(17) / 4
    minima = ((root, -root / 4), (-root, root / 4))
    bottom = landscape_value(*minima[0])
    px = _scale(-1.8, 1.8, 56, 416)
    py = _scale(1.2, -1.2, 52, 292)
    path_a = landscape_newton_path(LANDSCAPE_START_A)
    path_b = landscape_newton_path(LANDSCAPE_START_B)
    parts = _open(
        "谷が二つ、その間に峠",
        (
            f"f(x)=(x1^2-1)^2+x1x2+2x2^2 の等高線。原点が峠（鞍点、f=1）で、"
            f"x=(±{root:.2f}, ∓{root / 4:.2f}) の二つの谷底が最小値 {bottom:.3f} です。"
            f"Newton法は始点Aから{len(path_a) - 1}回で左の谷底へ、"
            f"始点Bから{len(path_b) - 1}回で峠へ着きます。"
        ),
        396,
    )
    parts.append(f'<path d="M56 52V292H416V52Z" fill="none" stroke="{GRID}"/>')
    for level in (-0.1, 0.5, 1.0, 2.0, 4.0):
        style = (
            f'stroke="{MUTED}" stroke-width="2"'
            if level == 1.0
            else f'stroke="{RING}" stroke-width="1.5"'
        )
        segments = _contour_segments(landscape_value, level, (-1.8, 1.8), (-1.2, 1.2), (144, 96))
        data = "".join(
            f"M{px(a[0]):.1f} {py(a[1]):.1f}L{px(b[0]):.1f} {py(b[1]):.1f}" for a, b in segments
        )
        parts.append(f'<path d="{data}" fill="none" {style}/>')
    for value in (-1, 0, 1):
        parts.append(_text(px(value), 312, f"{value}", "tick", "middle"))
        parts.append(_text(48, py(value) + 5, f"{value}", "tick", "end"))
    parts.append(_text(416, 332, "x₁", "tick", "end"))
    parts.append(_text(62, 70, "x₂", "tick"))
    for path, color in ((path_a, LINE), (path_b, POINT)):
        parts.append(_polyline([(px(a), py(b)) for a, b in path], color, 2.5))
        for a, b in path[1:]:
            parts.append(f'<circle cx="{px(a):.1f}" cy="{py(b):.1f}" r="3.5" fill="{color}"/>')
        a, b = path[0]
        parts.append(
            f'<rect x="{px(a) - 5:.1f}" y="{py(b) - 5:.1f}" width="10" height="10" fill="#f7f8f3" '
            f'stroke="{color}" stroke-width="2.5"/>'
        )
    for a, b in minima:
        parts.append(f'<circle cx="{px(a):.1f}" cy="{py(b):.1f}" r="7" fill="{UPDATE}"/>')
    parts.append(_text(px(minima[0][0]) - 12, py(minima[0][1]) + 24, "谷底", "", "end"))
    parts.append(_text(px(minima[1][0]) + 14, py(minima[1][1]) - 10, "谷底"))
    parts.append(_text(px(0) - 12, py(0) + 26, "峠", "", "end"))
    parts.append(_text(px(LANDSCAPE_START_A[0]) + 12, py(LANDSCAPE_START_A[1]) + 5, "始点A"))
    parts.append(_text(px(LANDSCAPE_START_B[0]) + 12, py(LANDSCAPE_START_B[1]) - 8, "始点B"))
    parts.append(_text(20, 356, f"緑：始点AからNewton法 {len(path_a) - 1}回で左の谷底", "note"))
    parts.append(_text(20, 380, f"青：始点BからNewton法 {len(path_b) - 1}回で峠"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


FIGURES: dict[str, Callable[[], str]] = {
    "smooth-landscape-saddle.svg": _smooth_landscape_svg,
}
