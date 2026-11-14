"""General nonsmooth local (content/concepts/general-nonsmooth-local.md): two pumps with outputs x1,
x2. cost(x) = 3|x1 - x2| + |(|t - 2| - 1)| + 0.2 t with t = (x1 + x2) / 2.
"""

from __future__ import annotations

import functools
import math
from collections.abc import Callable, Sequence

from ._svg import GRID, POINT, RING, UPDATE, _contour_segments, _open, _polyline, _scale, _text

PA011_START = (2.6, 1.2)
PA011_STEP = 0.1
PA011_STEPS = 16
PA011_LEVELS = (0.5, 1.0, 1.5, 2.5, 4.0)


def _pa011_cost(x1: float, x2: float) -> float:
    t = (x1 + x2) / 2
    return 3 * abs(x1 - x2) + abs(abs(t - 2) - 1) + 0.2 * t


def _pa011_sign(value: float) -> int:
    return (value > 0) - (value < 0)


def _pa011_slope(x1: float, x2: float) -> tuple[float, float]:
    """Gradient where it exists; on a kink select an element of the Clarke subdifferential."""
    t = (x1 + x2) / 2
    s = _pa011_sign(x1 - x2)
    m = _pa011_sign(abs(t - 2) - 1) * _pa011_sign(t - 2) + 0.2
    return 3 * s + m / 2, -3 * s + m / 2


def _pa011_descent(
    start: tuple[float, float] = PA011_START,
    step: float = PA011_STEP,
    iterations: int = PA011_STEPS,
) -> list[tuple[float, float]]:
    """Gradient descent with a fixed step length."""
    path = [start]
    for _ in range(iterations):
        g = _pa011_slope(*path[-1])
        path.append((path[-1][0] - step * g[0], path[-1][1] - step * g[1]))
    return path


def _pa011_gradient_norm(x: tuple[float, float]) -> float:
    return math.hypot(*_pa011_slope(*x))


def _pa011_compass(
    start: tuple[float, float],
    step: float,
    directions: Sequence[tuple[int, int]],
    tolerance: float = 1e-4,
) -> tuple[tuple[float, float], float, int]:
    """Poll the directions in order, take the first sufficient decrease, else halve the step."""
    x, fx, calls = start, _pa011_cost(*start), 1
    while step > tolerance:
        for d in directions:
            y = (x[0] + step * d[0], x[1] + step * d[1])
            calls += 1
            fy = _pa011_cost(*y)
            if fy < fx - 1e-9:
                x, fx = y, fy
                break
        else:
            step /= 2
    return x, fx, calls


def _pa011_clarke_derivative(x: tuple[float, float], d: tuple[float, float]) -> float:
    """Exact support function of the adjacent piecewise-affine gradients."""
    t, u = (x[0] + x[1]) / 2, x[0] - x[1]
    dt, du = (d[0] + d[1]) / 2, d[0] - d[1]
    if t in (1.0, 2.0, 3.0):
        mode = max(-0.8 * dt, 1.2 * dt)
    else:
        m = _pa011_sign(abs(t - 2) - 1) * _pa011_sign(t - 2) + 0.2
        mode = m * dt
    imbalance = 3 * abs(du) if u == 0 else 3 * _pa011_sign(u) * du
    return imbalance + mode


def _pa011_clarke_minimum(x: tuple[float, float]) -> float:
    """Smallest exact generalized derivative sampled over 360 unit directions."""
    return min(
        _pa011_clarke_derivative(
            x, (math.cos(math.radians(degrees)), math.sin(math.radians(degrees)))
        )
        for degrees in range(360)
    )


@functools.cache
def _pa011_kink_valley_svg() -> str:
    path = _pa011_descent()
    low, high = 0.5, 3.5
    px = _scale(low, high, 56, 416)  # 120 px per unit on both axes
    py = _scale(low, high, 412, 52)
    parts = _open(
        "折れ目の谷の上の勾配降下法",
        (
            "費用 3|x1-x2| + ||t-2|-1| + 0.2t（t は x1 と x2 の平均）の等高線。"
            "x1=x2 の谷の上に、費用 0.2 の谷底 (1, 1)、費用 0.6 の谷底 (3, 3)、"
            f"費用 {_pa011_cost(2, 2):g} の山の折れ目 (2, 2) がある。"
            f"出発 ({PA011_START[0]:g}, {PA011_START[1]:g}) の費用は "
            f"{_pa011_cost(*PA011_START):g}。一歩の大きさ {PA011_STEP:g} の勾配降下法は、"
            "谷を左右にまたぎながら谷底の方へ進む。"
        ),
        566,
    )
    parts.append(
        '<clipPath id="pa011-clip"><rect x="56" y="52" width="360" height="360"/></clipPath>'
    )
    parts.append(f'<path d="M56 52V412H416V52Z" fill="none" stroke="{GRID}"/>')
    parts.append('<g clip-path="url(#pa011-clip)">')
    for level in PA011_LEVELS:
        segments = _contour_segments(_pa011_cost, level, (low, high), (low, high), (180, 180))
        data = "".join(
            f"M{px(a[0]):.1f} {py(a[1]):.1f}L{px(b[0]):.1f} {py(b[1]):.1f}" for a, b in segments
        )
        parts.append(f'<path d="{data}" fill="none" stroke="{RING}" stroke-width="1.5"/>')
    parts.append(
        f'<path d="M{px(low):.1f} {py(low):.1f}L{px(high):.1f} {py(high):.1f}" '
        f'stroke="{GRID}" stroke-width="1.2" stroke-dasharray="4 4"/>'
    )
    parts.append(_polyline([(px(x), py(y)) for x, y in path], UPDATE, 2.5))
    for x, y in path[1:]:
        parts.append(f'<circle cx="{px(x):.1f}" cy="{py(y):.1f}" r="3" fill="{UPDATE}"/>')
    parts.append("</g>")
    sx, sy = px(PA011_START[0]), py(PA011_START[1])
    parts.append(f'<circle cx="{sx:.1f}" cy="{sy:.1f}" r="7" fill="{UPDATE}"/>')
    parts.append(_text(sx - 12, sy + 24, "出発", "", "end"))
    for bottom in (1.0, 3.0):
        parts.append(
            f'<circle cx="{px(bottom):.1f}" cy="{py(bottom):.1f}" r="6.5" fill="{POINT}"/>'
        )
    parts.append(_text(px(1) - 12, py(1) + 24, f"谷底 {_pa011_cost(1, 1):g}", "", "end"))
    parts.append(_text(px(3) - 12, py(3) - 12, f"谷底 {_pa011_cost(3, 3):.1f}", "", "end"))
    parts.append(
        f'<circle cx="{px(2):.1f}" cy="{py(2):.1f}" r="7" fill="#f7f8f3" '
        f'stroke="{POINT}" stroke-width="2.5"/>'
    )
    parts.append(_text(px(2) + 14, py(2) + 26, f"山 {_pa011_cost(2, 2):g}", ""))
    for value in (1, 2, 3):
        parts.append(_text(px(value), 432, f"{value}", "tick", "middle"))
        parts.append(_text(48, py(value) + 5, f"{value}", "tick", "end"))
    parts.append(_text(416, 454, "x₁ ポンプ1の出力", "tick", "end"))
    parts.append(_text(62, 70, "x₂ ポンプ2", "tick"))
    parts.append(_text(20, 482, "橙：一歩 0.1 の勾配降下法の16回", "note"))
    parts.append(_text(20, 506, f"橙の丸：出発 (2.6, 1.2)、費用 {_pa011_cost(*PA011_START):g}"))
    parts.append(_text(20, 530, "破線：谷 x₁ = x₂（出力が等しい線）"))
    parts.append(_text(20, 554, "紺の丸：谷底、白い丸：山の折れ目"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


FIGURES: dict[str, Callable[[], str]] = {
    "general-nonsmooth-kink-valley.svg": _pa011_kink_valley_svg,
}
