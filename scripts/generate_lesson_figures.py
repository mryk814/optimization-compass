"""Generate the computed supporting figures that sit next to one formula in a lesson.

uv run python scripts/generate_lesson_figures.py            # write figures and explorable fixture
uv run python scripts/generate_lesson_figures.py --check    # fail if a committed figure is stale

Supporting figures are drawn at the width they are shown on a PC (440 px, the 27.5rem cap
for static figures), so one SVG unit is one CSS pixel there. Text uses 16 px (15 px for axis
ticks): the same size as the body on a PC and 12 px or more at a 375 px phone width. Every
coordinate comes from the lesson's data, never from hand-placed numbers.
See docs/teaching-article-playbook.md §5.4.
"""

from __future__ import annotations

import argparse
import functools
import html
import itertools
import json
import math
import random
from collections.abc import Callable, Sequence
from fractions import Fraction
from pathlib import Path
from typing import Any

ROOT = Path(__file__).parents[1]
OUTPUT = ROOT / "site" / "public" / "figures"
# Inputs of the inverse-problem explorable. Python owns the example; the TS math only imports it.
INVERSE_FIXTURE = (
    ROOT / "site" / "src" / "features" / "explorable" / "math" / "inverseProblem.fixture.json"
)

WIDTH = 440
INK, MUTED, GRID = "#17211b", "#56645b", "#aab4ab"
LINE, POINT, UPDATE, RING = "#315c48", "#24406b", "#b3532d", "#91b8a4"

# Linear least squares (content/concepts/linear-least-squares.md): four temperature readings.
LSQ_T = (0.0, 1.0, 2.0, 3.0)
LSQ_Y = (1.0, 2.0, 2.0, 4.0)
LSQ_EXAMPLE = (0.5, 1.3)  # the explorable's starting line, y = 0.5 + 1.3 t


def _open(title: str, description: str, height: int) -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}" '
        f'viewBox="0 0 {WIDTH} {height}" role="img" '
        'aria-labelledby="figure-title figure-description">',
        f'<title id="figure-title">{html.escape(title)}</title>',
        f'<desc id="figure-description">{html.escape(description)}</desc>',
        "<style>"
        "text{font-family:system-ui,-apple-system,'Segoe UI',sans-serif;"
        f"font-size:16px;fill:{INK}}}"
        ".title{font-size:17px;font-weight:700}"
        f".tick{{font-size:15px;fill:{MUTED}}}"
        f".note{{fill:{LINE}}}"
        "</style>",
        f'<rect width="{WIDTH}" height="{height}" rx="14" fill="#f7f8f3"/>',
        f'<text x="20" y="30" class="title">{html.escape(title)}</text>',
    ]


def _text(x: float, y: float, body: str, cls: str = "", anchor: str = "start") -> str:
    attributes = f' class="{cls}"' if cls else ""
    if anchor != "start":
        attributes += f' text-anchor="{anchor}"'
    return f'<text x="{x:.1f}" y="{y:.1f}"{attributes}>{html.escape(body)}</text>'


def _polyline(points: Sequence[tuple[float, float]], color: str, width: float) -> str:
    joined = " ".join(f"{x:.2f},{y:.2f}" for x, y in points)
    return (
        f'<polyline points="{joined}" fill="none" stroke="{color}" '
        f'stroke-width="{width}" stroke-linejoin="round"/>'
    )


def _scale(lower: float, upper: float, start: float, end: float) -> Callable[[float], float]:
    return lambda value: start + (value - lower) / (upper - lower) * (end - start)


def least_squares_fit() -> tuple[float, float, float]:
    """Solve the 2x2 normal equations for the four readings; return (x1, x2, SSE)."""
    m = len(LSQ_T)
    st, stt = sum(LSQ_T), sum(t * t for t in LSQ_T)
    sy, sty = sum(LSQ_Y), sum(t * y for t, y in zip(LSQ_T, LSQ_Y, strict=True))
    det = m * stt - st * st
    x1 = (stt * sy - st * sty) / det
    x2 = (m * sty - st * sy) / det
    return x1, x2, least_squares_sse(x1, x2)


def least_squares_sse(x1: float, x2: float) -> float:
    return sum((y - (x1 + x2 * t)) ** 2 for t, y in zip(LSQ_T, LSQ_Y, strict=True))


def _least_squares_residuals_svg() -> str:
    x1, x2, sse = least_squares_fit()
    px = _scale(-0.3, 3.3, 56, 416)
    py = _scale(0.5, 4.5, 272, 52)
    unit = py(0.0) - py(1.0)  # pixels per temperature unit; squares use it on both sides
    parts = _open(
        "残差の二乗を、面積にする",
        (
            f"初期の4点と二乗和が最小の直線 y={x1:.1f}+{x2:.1f}t。"
            "各点の縦のずれ（残差）を一辺とする正方形の面積が残差の二乗で、"
            f"面積の合計は {sse:.2f} です。"
        ),
        380,
    )
    parts.append(f'<path d="M56 52V272H416" fill="none" stroke="{GRID}"/>')
    for t in LSQ_T:
        parts.append(_text(px(t), 292, f"{t:g}", "tick", "middle"))
    for y in (1.0, 2.0, 3.0, 4.0):
        parts.append(_text(48, py(y) + 5, f"{y:g}", "tick", "end"))
    parts.append(_text(416, 262, "時刻 t", "tick", "end"))
    parts.append(_text(62, 62, "温度 y", "tick"))
    parts.append(_polyline([(px(t), py(x1 + x2 * t)) for t in (-0.2, 3.2)], LINE, 3))
    for t, y in zip(LSQ_T, LSQ_Y, strict=True):
        fitted = x1 + x2 * t
        side = abs(y - fitted) * unit
        top = min(py(y), py(fitted))
        parts.append(
            f'<rect x="{px(t):.2f}" y="{top:.2f}" width="{side:.2f}" height="{side:.2f}" '
            f'fill="#e8b88b" fill-opacity=".7" stroke="{UPDATE}"/>'
        )
        parts.append(
            f'<path d="M{px(t):.2f} {py(y):.2f}V{py(fitted):.2f}" stroke="{UPDATE}" '
            'stroke-width="3"/>'
        )
        parts.append(f'<circle cx="{px(t):.2f}" cy="{py(y):.2f}" r="6" fill="{POINT}"/>')
    parts.append(_text(20, 324, "縦のずれ r → 四角の面積 r²"))
    parts.append(_text(20, 348, "面積の合計を最小にする直線を選ぶ"))
    parts.append(_text(20, 372, f"この直線では合計 {sse:.2f}", "note"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


def _least_squares_contours_svg() -> str:
    x1, x2, sse = least_squares_fit()
    ex1, ex2 = LSQ_EXAMPLE
    example_sse = least_squares_sse(ex1, ex2)
    # sse(x) - sse_min = d^T H d with H = A^T A; draw the rings through the example point.
    m = len(LSQ_T)
    st, stt = sum(LSQ_T), sum(t * t for t in LSQ_T)
    h11, h12, h22 = float(m), st, stt
    gap = example_sse - sse
    px = _scale(-1.0, 2.8, 56, 416)
    py = _scale(0.0, 1.8, 262, 52)
    parts = _open(
        "二乗和を、等高線で見る",
        (
            f"切片と傾きの平面で、初期の4点の二乗和の等高線を描いた図です。中心は切片 {x1:.1f}、"
            f"傾き {x2:.1f} で、最小の二乗和は {sse:.2f} です。例の直線（切片 {ex1}、傾き {ex2}）"
            f"は二乗和 {example_sse:.2f} の輪の上にあり、中心へ向かうほど二乗和が減ります。"
        ),
        388,
    )
    parts.append(f'<path d="M56 52V262H416" fill="none" stroke="{GRID}"/>')
    for value in (-1.0, 0.0, 1.0, 2.0):
        parts.append(_text(px(value), 282, f"{value:g}", "tick", "middle"))
    for value in (0.0, 0.5, 1.0, 1.5):
        parts.append(_text(48, py(value) + 5, f"{value:g}", "tick", "end"))
    parts.append(_text(416, 300, "切片 x₁", "tick", "end"))
    parts.append(_text(62, 62, "傾き x₂", "tick"))
    # Ellipse d^T H d = level: rotate into H's eigenbasis.
    half_trace, root = (h11 + h22) / 2, math.hypot((h11 - h22) / 2, h12)
    small, large = half_trace - root, half_trace + root
    angle = math.atan2(small - h11, h12)
    for k in (1, 2, 3, 4):
        level = gap * (k / 2) ** 2
        a, b = math.sqrt(level / small), math.sqrt(level / large)
        ring = []
        for step in range(121):
            phase = 2 * math.pi * step / 120
            u, v = a * math.cos(phase), b * math.sin(phase)
            dx = u * math.cos(angle) - v * math.sin(angle)
            dy = u * math.sin(angle) + v * math.cos(angle)
            ring.append((px(x1 + dx), py(x2 + dy)))
        parts.append(_polyline(ring, RING, 2))
    parts.append(
        f'<path d="M{px(ex1):.2f} {py(ex2):.2f}L{px(x1):.2f} {py(x2):.2f}" '
        f'stroke="{UPDATE}" stroke-width="3"/>'
    )
    parts.append(f'<circle cx="{px(x1):.2f}" cy="{py(x2):.2f}" r="6" fill="{LINE}"/>')
    parts.append(f'<circle cx="{px(ex1):.2f}" cy="{py(ex2):.2f}" r="7" fill="{UPDATE}"/>')
    parts.append(_text(20, 328, f"中心：切片 {x1:.1f}、傾き {x2:.1f}、二乗和 {sse:.2f}", "note"))
    parts.append(_text(20, 352, f"橙の点：例の直線（{ex1}, {ex2}）、二乗和 {example_sse:.2f}"))
    parts.append(_text(20, 376, "内側の輪ほど二乗和が小さい"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


def _least_squares_minimum_svg() -> str:
    x1, x2, sse = least_squares_fit()
    panels = (
        (f"切片だけ動かす（傾きは {x2:.1f}）", x1, lambda v: least_squares_sse(v, x2)),
        (f"傾きだけ動かす（切片は {x1:.1f}）", x2, lambda v: least_squares_sse(x1, v)),
    )
    parts = _open(
        "底では、二方向の傾きが 0",
        (
            f"最小の直線のまわりで、切片だけ、または傾きだけを動かしたときの二乗和の断面です。"
            f"どちらも {x1:.1f}（傾きは {x2:.1f}）で最小値 {sse:.2f} になり、接線が水平です。"
        ),
        400,
    )
    for index, (label, center, section) in enumerate(panels):
        top = 52 + index * 176
        px = _scale(center - 0.5, center + 0.5, 76, 396)
        py = _scale(0.0, 6.0, top + 140, top + 30)
        parts.append(_text(20, top + 14, label))
        parts.append(f'<path d="M76 {top + 30}V{top + 140}H396" fill="none" stroke="{GRID}"/>')
        for offset in (-0.5, 0.0, 0.5):
            parts.append(
                _text(px(center + offset), top + 158, f"{center + offset:.1f}", "tick", "middle")
            )
        parts.append(_text(68, py(0.0) + 5, "0", "tick", "end"))
        parts.append(_text(68, py(4.0) + 5, "4", "tick", "end"))
        samples = [center - 0.5 + step / 80 for step in range(81)]
        curve = [(px(v), py(section(v))) for v in samples]
        parts.append(_polyline(curve, LINE, 3))
        parts.append(
            f'<path d="M{px(center - 0.25):.2f} {py(sse):.2f}H{px(center + 0.25):.2f}" '
            f'stroke="{UPDATE}" stroke-width="2"/>'
        )
        parts.append(f'<circle cx="{px(center):.2f}" cy="{py(sse):.2f}" r="6" fill="{LINE}"/>')
        parts.append(
            _text(px(center), top + 50, f"{center:.1f} で最小 {sse:.2f}", "note", "middle")
        )
    parts.append("</svg>")
    return "".join(parts) + "\n"


# Nonlinear least squares (content/concepts/nonlinear-least-squares.md): y = a sin(ωt) fitted to
# eight spring readings taken every 0.5 s.
SPRING_T = tuple(0.5 * index for index in range(8))
SPRING_Y = (0.0, 1.9, 1.6, 0.4, -1.6, -1.7, -0.7, 1.4)


def spring_best_amplitude(w: float) -> float:
    """For a fixed ω the amplitude is a one-column linear least-squares problem."""
    ss = sum(math.sin(w * t) ** 2 for t in SPRING_T)
    sy = sum(math.sin(w * t) * y for t, y in zip(SPRING_T, SPRING_Y, strict=True))
    return sy / ss if ss > 1e-12 else 0.0


def spring_profile(w: float) -> float:
    """Smallest sum of squares over the amplitude, at a fixed ω."""
    a = spring_best_amplitude(w)
    return sum((a * math.sin(w * t) - y) ** 2 for t, y in zip(SPRING_T, SPRING_Y, strict=True))


def spring_profile_minima(lower: float = 0.2, upper: float = 6.0, steps: int = 5800) -> list[float]:
    grid = [lower + (upper - lower) * index / steps for index in range(steps + 1)]
    values = [spring_profile(w) for w in grid]
    return [
        grid[index]
        for index in range(1, steps)
        if values[index] < values[index - 1] and values[index] < values[index + 1]
    ]


def _nonlinear_least_squares_profile_svg() -> str:
    flat = sum(y * y for y in SPRING_Y)
    minima = spring_profile_minima()
    best = min(minima, key=spring_profile)
    px = _scale(0.0, 6.2, 56, 416)
    py = _scale(0.0, 16.0, 252, 52)
    parts = _open(
        "周波数ごとの、いちばん小さい二乗和",
        (
            "角周波数ωを固定し、振幅aを線形最小二乗で決めたときの残差の二乗和です。"
            f"谷が{len(minima)}つあり、最も深い谷はω={best:.2f}で二乗和{spring_profile(best):.2f}です。"
            f"ほかの谷の二乗和は13.5から14.0で、a=0の直線（{flat:.2f}）とほとんど変わりません。"
        ),
        356,
    )
    parts.append(f'<path d="M56 52V252H416" fill="none" stroke="{GRID}"/>')
    for w in (0, 1, 2, 3, 4, 5, 6):
        parts.append(_text(px(w), 272, f"{w}", "tick", "middle"))
    for value in (0, 5, 10, 15):
        parts.append(_text(48, py(value) + 5, f"{value}", "tick", "end"))
    parts.append(_text(416, 236, "角周波数 ω", "tick", "end"))
    parts.append(_text(62, 62, "二乗和", "tick"))
    parts.append(
        f'<path d="M56 {py(flat):.2f}H416" stroke="{MUTED}" stroke-width="1.5" '
        'stroke-dasharray="5 4"/>'
    )
    curve = [(px(w), py(spring_profile(w))) for w in (0.2 + 5.8 * i / 290 for i in range(291))]
    parts.append(_polyline(curve, LINE, 3))
    for w in minima:
        color = LINE if w == best else UPDATE
        cy = py(spring_profile(w))
        parts.append(f'<circle cx="{px(w):.2f}" cy="{cy:.2f}" r="6" fill="{color}"/>')
    label = f"ω={best:.2f}、二乗和 {spring_profile(best):.2f}"
    parts.append(_text(px(best) + 12, py(spring_profile(best)) - 6, label, "note"))
    parts.append(_text(20, 302, f"破線：a=0（何も振動しない）の二乗和 {flat:.2f}"))
    parts.append(_text(20, 326, "橙の点：別の谷。どれも破線とほとんど同じ高さ"))
    parts.append(_text(20, 350, "緑の点：最も深い谷", "note"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


# Smooth low-dimensional unconstrained (content/concepts/smooth-low-dimensional-unconstrained.md):
# f(x) = (x1^2 - 1)^2 + x1 x2 + 2 x2^2 has a saddle at the origin and two valley bottoms.
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


def _contour_segments(
    func: Callable[[float, float], float],
    level: float,
    x_range: tuple[float, float],
    y_range: tuple[float, float],
    cells: tuple[int, int],
) -> list[tuple[tuple[float, float], tuple[float, float]]]:
    """Marching squares on a regular grid; each cell contributes zero, one or two segments."""
    nx, ny = cells
    xs = [x_range[0] + (x_range[1] - x_range[0]) * i / nx for i in range(nx + 1)]
    ys = [y_range[0] + (y_range[1] - y_range[0]) * j / ny for j in range(ny + 1)]
    values = [[func(x, y) - level for y in ys] for x in xs]

    def cross(a: tuple[float, float, float], b: tuple[float, float, float]) -> tuple[float, float]:
        t = a[2] / (a[2] - b[2])
        return a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])

    segments = []
    for i in range(nx):
        for j in range(ny):
            corners = [
                (xs[i], ys[j], values[i][j]),
                (xs[i + 1], ys[j], values[i + 1][j]),
                (xs[i + 1], ys[j + 1], values[i + 1][j + 1]),
                (xs[i], ys[j + 1], values[i][j + 1]),
            ]
            hits = [
                cross(corners[k], corners[(k + 1) % 4])
                for k in range(4)
                if (corners[k][2] > 0) != (corners[(k + 1) % 4][2] > 0)
            ]
            if len(hits) == 2:
                segments.append((hits[0], hits[1]))
            elif len(hits) == 4:
                segments.append((hits[0], hits[1]))
                segments.append((hits[2], hits[3]))
    return segments


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


# Inverse problem (content/concepts/inverse-problem.md): a rod's initial temperature profile is
# recovered from 40 blurred, noisy readings. Pure Python, so the figure needs no numeric extra.
INV_N = 40
INV_WIDTH = 0.05
INV_SIGMA = 1e-3


def inverse_problem_data() -> tuple[list[list[float]], list[float], list[float]]:
    xs = [(i + 0.5) / INV_N for i in range(INV_N)]
    kernel = [[math.exp(-((a - b) ** 2) / (2 * INV_WIDTH**2)) for b in xs] for a in xs]
    blur = [[v / sum(row) for v in row] for row in kernel]
    truth = [
        math.exp(-(((x - 0.3) / 0.08) ** 2)) + 0.6 * math.exp(-(((x - 0.7) / 0.06) ** 2))
        for x in xs
    ]
    rng = random.Random(0)
    noise = [INV_SIGMA * rng.gauss(0, 1) for _ in range(INV_N)]
    data = [
        sum(a * t for a, t in zip(row, truth, strict=True)) + e
        for row, e in zip(blur, noise, strict=True)
    ]
    return blur, truth, data


def _solve_linear(matrix: list[list[float]], rhs: list[float]) -> list[float]:
    size = len(rhs)
    a = [[*row, rhs[i]] for i, row in enumerate(matrix)]
    for col in range(size):
        pivot = max(range(col, size), key=lambda r: abs(a[r][col]))
        a[col], a[pivot] = a[pivot], a[col]
        for r in range(col + 1, size):
            factor = a[r][col] / a[col][col]
            for c in range(col, size + 1):
                a[r][c] -= factor * a[col][c]
    solution = [0.0] * size
    for r in range(size - 1, -1, -1):
        tail = sum(a[r][c] * solution[c] for c in range(r + 1, size))
        solution[r] = (a[r][size] - tail) / a[r][r]
    return solution


def inverse_problem_curve() -> tuple[float, float, list[tuple[float, float]]]:
    """Return the discrepancy-principle alpha, its error, and (log10 alpha, error) points."""
    blur, truth, data = inverse_problem_data()
    size = INV_N
    gram = [
        [sum(blur[k][i] * blur[k][j] for k in range(size)) for j in range(size)]
        for i in range(size)
    ]
    gtd = [sum(blur[k][i] * data[k] for k in range(size)) for i in range(size)]
    norm_truth = math.sqrt(sum(t * t for t in truth))

    def solve(alpha: float) -> list[float]:
        shifted = [
            [gram[i][j] + (alpha if i == j else 0.0) for j in range(size)] for i in range(size)
        ]
        return _solve_linear(shifted, gtd)

    def error(m: list[float]) -> float:
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(m, truth, strict=True))) / norm_truth

    def residual(m: list[float]) -> float:
        return math.sqrt(
            sum(
                (sum(a * v for a, v in zip(row, m, strict=True)) - d) ** 2
                for row, d in zip(blur, data, strict=True)
            )
        )

    delta = INV_SIGMA * math.sqrt(size)
    lo, hi = -10.0, 0.0
    for _ in range(50):
        mid = (lo + hi) / 2
        if residual(solve(10**mid)) < delta:
            lo = mid
        else:
            hi = mid
    alpha = 10 ** ((lo + hi) / 2)
    curve = [(e / 4, error(solve(10 ** (e / 4)))) for e in range(-40, 1)]
    return alpha, error(solve(alpha)), curve


def inverse_problem_fixture() -> str:
    """JSON text of the rod example's fixed inputs for the inverse-problem explorable."""
    blur, truth, data = inverse_problem_data()
    payload = {
        "generated_by": "scripts/generate_lesson_figures.py (inverse_problem_data)",
        "n": INV_N,
        "blur_width": INV_WIDTH,
        "sigma": INV_SIGMA,
        "truth": truth,
        "data": data,
        "blur": blur,
    }
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n"


def _inverse_problem_alpha_svg() -> str:
    alpha, err, curve = inverse_problem_curve()
    px = _scale(-10.0, 0.0, 64, 416)
    py = _scale(-2.0, 2.0, 252, 52)
    parts = _open(
        "正則化の強さ α ごとの誤差",
        (
            "40点の観測から初期温度を復元したときの、真値との相対誤差です。"
            f"α=1e-10 では誤差{curve[0][1]:.1f}、残差が雑音の大きさに等しくなるα={alpha:.2e}で"
            f"誤差{err:.3f}、α=1 では{curve[-1][1]:.2f}です。縦軸と横軸は対数です。"
        ),
        360,
    )
    parts.append(f'<path d="M64 52V252H416" fill="none" stroke="{GRID}"/>')
    for e in (-10, -7, -4, -1):
        parts.append(_text(px(e), 272, f"1e{e}", "tick", "middle"))
    for e, label in ((-2, "0.01"), (-1, "0.1"), (0, "1"), (1, "10"), (2, "100")):
        parts.append(_text(56, py(e) + 5, label, "tick", "end"))
    parts.append(_text(416, 236, "α", "tick", "end"))
    parts.append(_text(70, 62, "相対誤差", "tick"))
    parts.append(_polyline([(px(e), py(math.log10(v))) for e, v in curve], LINE, 3))
    cx, cy = px(math.log10(alpha)), py(math.log10(err))
    parts.append(f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="6" fill="{UPDATE}"/>')
    parts.append(_text(20, 306, f"橙の点：残差が雑音の大きさに等しい α={alpha:.2e}"))
    parts.append(_text(20, 330, f"そのときの誤差 {err:.3f}", "note"))
    parts.append(_text(20, 354, "α=0（正則化なし）の誤差は 4.75e4（図の外）"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


# L1 sparse regularization (content/concepts/l1-sparse-regularization.md): twelve rental
# listings, four candidate features, rent in units of 10,000 yen.
RENT_FEATURES = ("面積", "築年数", "徒歩", "階数")
RENT_COLUMNS = (
    (20, 36, 19, 27, 45, 57, 35, 44, 25, 37, 39, 39),
    (8, 14, 25, 3, 17, 9, 28, 2, 3, 28, 7, 22),
    (2, 7, 3, 15, 11, 6, 10, 11, 7, 12, 12, 4),
    (3, 4, 7, 2, 4, 4, 1, 4, 1, 2, 8, 8),
)
RENT_Y = (6.0, 6.3, 4.6, 3.9, 6.8, 11.1, 4.1, 9.9, 5.4, 3.8, 7.3, 6.0)
RENT_COLORS = (LINE, POINT, UPDATE, MUTED)


def _rent_design() -> tuple[list[list[float]], list[float]]:
    """Standardized feature columns (mean 0, standard deviation 1) and centered rent."""
    columns = []
    for column in RENT_COLUMNS:
        mean = sum(column) / len(column)
        spread = math.sqrt(sum((v - mean) ** 2 for v in column) / len(column))
        columns.append([(v - mean) / spread for v in column])
    mean_y = sum(RENT_Y) / len(RENT_Y)
    return columns, [y - mean_y for y in RENT_Y]


def _soft_threshold(value: float, threshold: float) -> float:
    return math.copysign(max(abs(value) - threshold, 0.0), value)


def lasso_solution(lam: float, sweeps: int = 400) -> list[float]:
    """Coordinate descent for 1/2 |Ax-b|^2 + lam |x|_1 on the standardized rent data."""
    columns, y = _rent_design()
    coef = [0.0] * len(columns)
    residual = list(y)
    for _ in range(sweeps):
        for j, column in enumerate(columns):
            norm = sum(v * v for v in column)
            rho = sum(v * r for v, r in zip(column, residual, strict=True)) + norm * coef[j]
            new = _soft_threshold(rho, lam) / norm
            residual = [r + v * (coef[j] - new) for v, r in zip(column, residual, strict=True)]
            coef[j] = new
    return coef


def ridge_solution(lam: float) -> list[float]:
    """Solve (A^T A + lam I) x = A^T b by Gaussian elimination."""
    columns, y = _rent_design()
    size = len(columns)
    rows = [
        [sum(u * v for u, v in zip(columns[i], columns[j], strict=True)) for j in range(size)]
        + [sum(u * v for u, v in zip(columns[i], y, strict=True))]
        for i in range(size)
    ]
    for i in range(size):
        rows[i][i] += lam
    for i in range(size):
        pivot = rows[i][i]
        rows[i] = [v / pivot for v in rows[i]]
        for k in range(size):
            if k != i:
                factor = rows[k][i]
                rows[k] = [a - factor * c for a, c in zip(rows[k], rows[i], strict=True)]
    return [rows[i][size] for i in range(size)]


def lasso_lambda_max() -> float:
    columns, y = _rent_design()
    return max(abs(sum(u * v for u, v in zip(column, y, strict=True))) for column in columns)


def lasso_zero_points() -> list[float]:
    """The lambda at which each coefficient first becomes exactly 0 (bisection)."""
    points = []
    for j in range(len(RENT_COLUMNS)):
        low, high = 0.0, lasso_lambda_max()
        for _ in range(40):
            middle = (low + high) / 2
            if lasso_solution(middle, 120)[j] == 0.0:
                high = middle
            else:
                low = middle
        points.append(high)
    return points


def _l1_path_svg() -> str:
    top_lam = 20.0
    zero_points = lasso_zero_points()
    steps = [top_lam * index / 80 for index in range(81)]
    lasso = [lasso_solution(lam, 200) for lam in steps]
    ridge = [ridge_solution(lam) for lam in steps]
    lam_max = lasso_lambda_max()
    parts = _open(
        "λ を上げたときの係数",
        (
            "標準化した4つの特徴量について、λを0から20まで上げたときの係数の変化です。"
            f"上のパネルのL1では係数がちょうど0になり、階数は{zero_points[3]:.1f}、"
            f"徒歩は{zero_points[2]:.1f}、築年数は{zero_points[1]:.1f}、"
            f"面積は{zero_points[0]:.1f}で0になります。"
            "下のパネルのL2（ridge）では、どの係数も0にならず小さくなるだけです。"
        ),
        580,
    )
    px = _scale(0.0, top_lam, 64, 420)
    for index, (label, path) in enumerate(
        (("L1（lasso）の係数", lasso), ("L2（ridge）の係数", ridge))
    ):
        top = 56 + index * 208
        py = _scale(-1.5, 2.0, top + 150, top + 20)
        parts.append(_text(20, top + 2, label))
        parts.append(f'<path d="M64 {top + 20}V{top + 150}H420" fill="none" stroke="{GRID}"/>')
        parts.append(f'<path d="M64 {py(0.0):.2f}H420" stroke="{GRID}" stroke-width="1"/>')
        for value in (-1.0, 0.0, 1.0, 2.0):
            parts.append(_text(56, py(value) + 5, f"{value:g}", "tick", "end"))
        for lam in (0, 10, 20):
            parts.append(_text(px(lam), top + 170, f"{lam}", "tick", "middle"))
        parts.append(_text(420, top + 190, "λ", "tick", "end"))
        # Draw the last feature first so a coefficient resting on 0 shows the first feature's color.
        for j in reversed(range(len(RENT_COLORS))):
            points = [(px(lam), py(coef[j])) for lam, coef in zip(steps, path, strict=True)]
            parts.append(_polyline(points, RENT_COLORS[j], 3))
        if index == 0:
            for j, color in enumerate(RENT_COLORS):
                parts.append(
                    f'<circle cx="{px(zero_points[j]):.2f}" cy="{py(0.0):.2f}" r="6" '
                    f'fill="#f7f8f3" stroke="{color}" stroke-width="3"/>'
                )
    legend_top = 484
    for j, (name, color) in enumerate(zip(RENT_FEATURES, RENT_COLORS, strict=True)):
        x = 20 + (j % 2) * 200
        y = legend_top + (j // 2) * 24
        parts.append(f'<path d="M{x} {y - 5}h28" stroke="{color}" stroke-width="3"/>')
        parts.append(_text(x + 36, y, name))
    parts.append(_text(20, legend_top + 52, "白抜きの丸：係数がちょうど0になる λ", "note"))
    parts.append(_text(20, legend_top + 76, f"λ が {lam_max:.1f} 以上なら係数はすべて0", "note"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


# MPC (content/concepts/model-predictive-control.md): a cart on a rail with a wall at p = 0.
MPC_A = ((1.0, 1.0), (0.0, 1.0))
MPC_B = (0.5, 1.0)
MPC_Q = (1.0, 0.1)  # diag(Q); the input weight R is MPC_R
MPC_R = 0.1
MPC_X0 = (3.0, 0.0)


def _mpc_terminal_weight() -> tuple[tuple[float, float], tuple[float, float]]:
    """Solve the discrete algebraic Riccati equation by iterating the recursion."""
    a, b, r = MPC_A, MPC_B, MPC_R
    p = [[MPC_Q[0], 0.0], [0.0, MPC_Q[1]]]
    for _ in range(2000):
        pb = [p[0][0] * b[0] + p[0][1] * b[1], p[1][0] * b[0] + p[1][1] * b[1]]
        gain = r + b[0] * pb[0] + b[1] * pb[1]
        pa = [[sum(p[i][m] * a[m][j] for m in range(2)) for j in range(2)] for i in range(2)]
        bpa = [sum(b[m] * pa[m][j] for m in range(2)) for j in range(2)]
        at_pa = [[sum(a[m][i] * pa[m][j] for m in range(2)) for j in range(2)] for i in range(2)]
        p = [
            [(MPC_Q[i] if i == j else 0.0) + at_pa[i][j] - bpa[i] * bpa[j] / gain for j in range(2)]
            for i in range(2)
        ]
    return (p[0][0], p[0][1]), (p[1][0], p[1][1])


def _mpc_plan(horizon: int, state: tuple[float, float], gain_scale: float = 1.0) -> list[float]:
    """Solve the condensed MPC QP with |u|<=1 and p_k>=0 by ADMM (the OSQP iteration)."""
    n = horizon
    terminal = _mpc_terminal_weight()
    # x_k = free_k + sum_j phi[k][j] u_j  (the model the planner believes in)
    free, phi = [], []
    x = list(state)
    cols = [[0.0, 0.0] for _ in range(n)]
    for k in range(n):
        x = [MPC_A[i][0] * x[0] + MPC_A[i][1] * x[1] for i in range(2)]
        free.append(list(x))
        cols = [[MPC_A[i][0] * c[0] + MPC_A[i][1] * c[1] for i in range(2)] for c in cols]
        cols[k] = [MPC_B[0] * gain_scale, MPC_B[1] * gain_scale]
        phi.append([[cols[j][i] for j in range(n)] for i in range(2)])
    # cost = sum_k x_k' W_k x_k + R u'u,  W_k = diag(Q), the last one is the terminal P
    weights = [((MPC_Q[0], 0.0), (0.0, MPC_Q[1]))] * (n - 1) + [terminal]
    hess = [[0.0] * n for _ in range(n)]
    lin = [0.0] * n
    for k in range(n):
        w = weights[k]
        for a_ in range(n):
            wa = [sum(w[i][m] * phi[k][m][a_] for m in range(2)) for i in range(2)]
            lin[a_] += 2 * sum(wa[i] * free[k][i] for i in range(2))
            for b_ in range(n):
                hess[a_][b_] += 2 * sum(wa[i] * phi[k][i][b_] for i in range(2))
    for j in range(n):
        hess[j][j] += 2 * MPC_R
    # constraints l <= C u <= h : rows 0..n-1 are u_j, rows n.. are p_k = free + phi u
    cmat = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]
    cmat += [phi[k][0] for k in range(n)]
    low = [-1.0] * n + [-free[k][0] for k in range(n)]
    high = [1.0] * n + [1e9] * n
    rho, sigma, alpha = 1.0, 1e-9, 1.6
    m = 2 * n
    system = [
        [
            hess[i][j]
            + (sigma if i == j else 0.0)
            + rho * sum(cmat[r][i] * cmat[r][j] for r in range(m))
            for j in range(n)
        ]
        for i in range(n)
    ]
    inverse = [
        list(col)
        for col in zip(
            *[_solve_linear(system, [1.0 if i == j else 0.0 for i in range(n)]) for j in range(n)],
            strict=True,
        )
    ]
    u, z, y = [0.0] * n, [0.0] * m, [0.0] * m
    for _ in range(60000):
        rhs = [
            sigma * u[i] - lin[i] + sum(cmat[r][i] * (rho * z[r] - y[r]) for r in range(m))
            for i in range(n)
        ]
        u_tilde = [sum(inverse[i][j] * rhs[j] for j in range(n)) for i in range(n)]
        cu = [sum(cmat[r][j] * u_tilde[j] for j in range(n)) for r in range(m)]
        z_tilde = cu
        u_next = [alpha * u_tilde[i] + (1 - alpha) * u[i] for i in range(n)]
        z_relaxed = [alpha * z_tilde[r] + (1 - alpha) * z[r] for r in range(m)]
        z_next = [min(max(z_relaxed[r] + y[r] / rho, low[r]), high[r]) for r in range(m)]
        y = [y[r] + rho * (z_relaxed[r] - z_next[r]) for r in range(m)]
        change = max(abs(a_ - b_) for a_, b_ in zip(u_next, u, strict=True))
        u, z = u_next, z_next
        if change < 1e-13:
            break
    return u


MPC_GAIN_ERROR = 1.3  # the real cart responds 30 % more strongly to the input than the model says
MPC_STEPS = 12


def _mpc_step(state: Sequence[float], u: float, scale: float = 1.0) -> list[float]:
    return [
        MPC_A[i][0] * state[0] + MPC_A[i][1] * state[1] + scale * MPC_B[i] * u for i in range(2)
    ]


def mpc_wall_data() -> dict[str, list[float]]:
    """Positions over 12 steps: the model's plan, the plan run open loop, and receding horizon."""
    plan = _mpc_plan(MPC_STEPS, MPC_X0)
    model, real = [list(MPC_X0)], [list(MPC_X0)]
    for u in plan:
        model.append(_mpc_step(model[-1], u))
        real.append(_mpc_step(real[-1], u, MPC_GAIN_ERROR))
    state, receding = list(MPC_X0), [list(MPC_X0)]
    for _ in range(MPC_STEPS):
        u = _mpc_plan(5, (state[0], state[1]))[0]
        state = _mpc_step(state, u, MPC_GAIN_ERROR)
        receding.append(state)
    return {
        "model": [s[0] for s in model],
        "open_loop": [s[0] for s in real],
        "receding": [s[0] for s in receding],
        "receding_velocity_end": [receding[-1][1]],
    }


def _mpc_wall_svg() -> str:
    data = mpc_wall_data()
    open_loop, receding, model = data["open_loop"], data["receding"], data["model"]
    low = min(open_loop)
    parts = _open(
        "解き直しと壁",
        (
            "台車を位置3から壁（位置0）の手前で止める12歩の計画です。実機の入力の効きは"
            f"モデルの{MPC_GAIN_ERROR}倍とします。計画を解き直さず最後まで実行すると、"
            f"位置が{open_loop[-1]:.2f}まで進んで壁を越えます。毎回5歩先まで解き直すと、"
            f"最小の位置は{min(receding):.3f}で、壁を越えません。"
        ),
        392,
    )
    px = _scale(0.0, MPC_STEPS, 64, 420)
    py = _scale(-1.2, 3.2, 270, 52)
    parts.append(f'<path d="M64 52V270H420" fill="none" stroke="{GRID}"/>')
    for step in (0, 4, 8, 12):
        parts.append(_text(px(step), 292, f"{step}", "tick", "middle"))
    for value in (-1, 0, 1, 2, 3):
        parts.append(_text(56, py(value) + 5, f"{value}", "tick", "end"))
    parts.append(_text(420, 314, "歩数", "tick", "end"))
    parts.append(_text(70, 62, "位置", "tick"))
    parts.append(f'<path d="M64 {py(0):.2f}H420" stroke="{POINT}" stroke-width="5"/>')
    parts.append(_polyline([(px(k), py(v)) for k, v in enumerate(model)], UPDATE, 2))
    parts.append(_polyline([(px(k), py(v)) for k, v in enumerate(open_loop)], MUTED, 3))
    parts.append(_polyline([(px(k), py(v)) for k, v in enumerate(receding)], LINE, 3))
    parts.append(_text(20, 340, "紺：壁（位置0）　橙：モデル上の計画"))
    parts.append(
        _text(20, 364, f"灰：解き直さず実行。12歩後 {open_loop[-1]:.2f}（最小 {low:.2f}）", "note")
    )
    parts.append(_text(20, 388, f"緑：毎回解き直し。最小 {min(receding):.3f}", "note"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


# Vehicle routing (content/concepts/vehicle-routing.md): depot 0 and seven customers, two vehicles.
VRP_XY = ((0, 0), (0, 6), (0, -6), (-2, 2), (1, 0), (6, -2), (1, -1), (3, -3))
VRP_DEMAND = (0, 2, 3, 2, 1, 3, 2, 3)
VRP_CAPACITY = 9
VIOLATION = "#c23a2b"


def _vrp_length(route: Sequence[int]) -> float:
    path = [0, *route, 0]
    return sum(math.dist(VRP_XY[a], VRP_XY[b]) for a, b in zip(path, path[1:], strict=False))


def _vrp_nearest_neighbour() -> list[list[int]]:
    left, routes = set(range(1, len(VRP_XY))), []
    while left:
        route, load, here = [], 0, 0
        while True:
            fits = [j for j in left if load + VRP_DEMAND[j] <= VRP_CAPACITY]
            if not fits:
                break
            j = min(fits, key=lambda j: math.dist(VRP_XY[here], VRP_XY[j]))
            route.append(j)
            left.remove(j)
            load, here = load + VRP_DEMAND[j], j
        routes.append(route)
    return routes


def _vrp_two_opt(route: Sequence[int]) -> list[int]:
    best, improved = list(route), True
    while improved:
        improved = False
        for i in range(len(best) - 1):
            for j in range(i + 1, len(best)):
                trial = best[:i] + best[i : j + 1][::-1] + best[j + 1 :]
                if _vrp_length(trial) < _vrp_length(best) - 1e-12:
                    best, improved = trial, True
    return best


def _vrp_degree_only() -> tuple[float, list[list[int]], list[list[int]]]:
    """Minimum-cost successor assignment: every customer in/out once, two depot arcs, no loads.

    The two depot copies are nodes 7 and 8; depot-to-depot arcs are forbidden. Pure Python
    brute force over the 9! successor permutations (the MILP without subtour constraints).
    """
    n = len(VRP_XY)

    def node(i: int) -> int:  # successor-permutation index -> instance node
        return i + 1 if i < n - 1 else 0

    cost = [
        [
            math.inf
            if (a == b or (a >= n - 1 and b >= n - 1))
            else math.dist(VRP_XY[node(a)], VRP_XY[node(b)])
            for b in range(n + 1)
        ]
        for a in range(n + 1)
    ]
    best_cost, best = math.inf, ()
    for perm in itertools.permutations(range(n + 1)):
        total = 0.0
        for a, b in enumerate(perm):
            total += cost[a][b]
            if total >= best_cost:
                break
        else:
            best_cost, best = total, perm
    successor = {node(a): node(b) for a, b in enumerate(best) if a < n - 1}
    starts = [node(b) for a, b in enumerate(best) if a >= n - 1]
    routes, seen = [], set()
    for start in starts:
        route = [start]
        while successor[route[-1]] != 0:
            route.append(successor[route[-1]])
        routes.append(route)
        seen.update(route)
    loops: list[list[int]] = []
    for start in range(1, n):
        if start not in seen:
            loop = [start]
            while successor[loop[-1]] != start:
                loop.append(successor[loop[-1]])
            loops.append(loop)
            seen.update(loop)
    return best_cost, sorted(routes), sorted(loops)


def vrp_data() -> dict[str, object]:
    """Optimum by enumeration, nearest neighbour + 2-opt, and the degree-only relaxation."""
    n = len(VRP_XY)
    best_route: dict[tuple[int, ...], tuple[int, ...]] = {}

    def shortest(members: tuple[int, ...]) -> tuple[int, ...]:
        if members not in best_route:
            best_route[members] = min(itertools.permutations(members), key=_vrp_length)
        return best_route[members]

    splits = []
    for mask in range(1, 2 ** (n - 1) - 1):
        a = tuple(i for i in range(1, n) if mask >> (i - 1) & 1)
        b = tuple(i for i in range(1, n) if not mask >> (i - 1) & 1)
        if a < b and all(sum(VRP_DEMAND[i] for i in s) <= VRP_CAPACITY for s in (a, b)):
            ra, rb = shortest(a), shortest(b)
            splits.append((_vrp_length(ra) + _vrp_length(rb), list(ra), list(rb)))
    splits.sort()
    nearest = _vrp_nearest_neighbour()
    improved = [_vrp_two_opt(route) for route in nearest]
    degree_cost, degree_routes, degree_loops = _vrp_degree_only()
    return {
        "optimum": splits[0][0],
        "optimum_routes": [splits[0][1], splits[0][2]],
        "split_count": len(splits),
        "nearest": sum(_vrp_length(r) for r in nearest),
        "nearest_routes": nearest,
        "heuristic": sum(_vrp_length(r) for r in improved),
        "heuristic_routes": improved,
        "degree_cost": degree_cost,
        "degree_routes": degree_routes,
        "degree_loops": degree_loops,
    }


def _vrp_panel(
    left: float,
    top: float,
    routes: Sequence[Sequence[int]],
    color: str,
    loops: Sequence[Sequence[int]] = (),
) -> list[str]:
    """One map panel, 22 px per unit: depot (navy square), customers (numbered circles)."""
    px = _scale(-2, 6, left + 12, left + 12 + 8 * 22)
    py = _scale(6, -6, top + 12, top + 12 + 12 * 22)
    parts = []
    paths = [([0, *r, 0], color) for r in routes] + [([*lp, lp[0]], VIOLATION) for lp in loops]
    for path, stroke in paths:
        parts.append(_polyline([(px(VRP_XY[i][0]), py(VRP_XY[i][1])) for i in path], stroke, 3))
    x0, y0 = px(0), py(0)
    parts.append(f'<rect x="{x0 - 8:.1f}" y="{y0 - 8:.1f}" width="16" height="16" fill="{POINT}"/>')
    for i in range(1, len(VRP_XY)):
        x, y = px(VRP_XY[i][0]), py(VRP_XY[i][1])
        parts.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="10" fill="#f7f8f3" stroke="{POINT}" '
            'stroke-width="1.5"/>'
        )
        parts.append(_text(x, y + 5.5, str(i), "tick", "middle"))
    return parts


def _vrp_routes_svg() -> str:
    data = vrp_data()
    parts = _open(
        "配送経路：近似と最適",
        (
            "depotと7人の顧客を、容量9の2台で回る配送経路です。最近傍法と2-optの結果は"
            f"{data['heuristic']:.3f}、全探索の最適は{data['optimum']:.3f}で、"
            "2台への顧客の分け方が違います。"
        ),
        448,
    )
    parts += _vrp_panel(14, 96, data["heuristic_routes"], UPDATE)  # type: ignore[arg-type]
    parts += _vrp_panel(226, 96, data["optimum_routes"], LINE)  # type: ignore[arg-type]
    parts.append(_text(20, 56, "最近傍法＋2-opt"))
    parts.append(_text(20, 78, f"{data['heuristic']:.3f}", "note"))
    parts.append(_text(232, 56, "全探索の最適"))
    parts.append(_text(232, 78, f"{data['optimum']:.3f}", "note"))
    parts.append(_text(20, 404, "紺の四角：depot　数字：顧客"))
    parts.append(_text(20, 428, "橙：最近傍法＋2-opt　緑：最適"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


def _vrp_subtour_svg() -> str:
    data = vrp_data()
    loops = data["degree_loops"]
    parts = _open(
        "輪を禁じないと現れる解",
        (
            "各顧客に入る弧と出る弧を1本ずつにして、depotを出る弧を2本にするだけの制約では、"
            f"費用{data['degree_cost']:.3f}の解が選ばれます。depotにつながらない輪が"
            f"{len(loops)}つ残り、実際には回れません。積載の制約を足すと、輪が消えて"  # type: ignore[arg-type]
            f"費用{data['optimum']:.3f}になります。"
        ),
        448,
    )
    parts += _vrp_panel(14, 96, data["degree_routes"], LINE, loops)  # type: ignore[arg-type]
    parts += _vrp_panel(226, 96, data["optimum_routes"], LINE)  # type: ignore[arg-type]
    parts.append(_text(20, 56, "次数の制約だけ"))
    parts.append(_text(20, 78, f"{data['degree_cost']:.3f}", "note"))
    parts.append(_text(232, 56, "積載の制約つき"))
    parts.append(_text(232, 78, f"{data['optimum']:.3f}", "note"))
    parts.append(_text(20, 404, "赤：depotにつながらない輪"))
    parts.append(_text(20, 428, "緑：depotから出る経路　紺の四角：depot"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


# MIQP (content/concepts/mixed-integer-quadratic-program.md): five assets, at most three held.
MIQP_NAMES = "ABCDE"
MIQP_VOL = (10.0, 12.0, 15.0, 20.0, 25.0)  # standard deviations in percent
MIQP_CORR = (
    (1.0, 0.5, 0.3, 0.1, 0.0),
    (0.5, 1.0, 0.4, 0.2, 0.1),
    (0.3, 0.4, 1.0, 0.3, 0.2),
    (0.1, 0.2, 0.3, 1.0, 0.4),
    (0.0, 0.1, 0.2, 0.4, 1.0),
)
MIQP_RETURN = (4.0, 5.0, 6.0, 8.0, 9.0)  # expected returns in percent
MIQP_CAP = (0.6, 0.5, 0.5, 0.4, 0.4)  # per-asset upper limit on the weight
MIQP_LOT = 0.1  # minimum weight of a held asset
MIQP_TARGET = 6.0  # required expected return
MIQP_MAX_HELD = 3
MIQP_FEE = 5.0  # fixed cost per held asset, on the same scale as the variance
MIQP_TOL = 1e-9


def _miqp_covariance() -> list[list[float]]:
    return [[MIQP_VOL[i] * MIQP_VOL[j] * MIQP_CORR[i][j] for j in range(5)] for i in range(5)]


def _solve_consistent(matrix: list[list[float]], rhs: list[float]) -> list[float] | None:
    """Gaussian elimination that tolerates redundant rows and rejects inconsistent ones."""
    rows, cols = len(matrix), len(matrix[0])
    a = [[*row, rhs[i]] for i, row in enumerate(matrix)]
    pivots: list[int] = []
    r = 0
    for col in range(cols):
        pivot = max(range(r, rows), key=lambda i: abs(a[i][col]), default=None)
        if pivot is None or abs(a[pivot][col]) < 1e-12:
            continue
        a[r], a[pivot] = a[pivot], a[r]
        a[r] = [v / a[r][col] for v in a[r]]
        for i in range(rows):
            if i != r:
                factor = a[i][col]
                a[i] = [v - factor * w for v, w in zip(a[i], a[r], strict=True)]
        pivots.append(col)
        r += 1
    if any(abs(a[i][cols]) > 1e-9 for i in range(r, rows)):
        return None
    solution = [0.0] * cols
    for i, col in enumerate(pivots):
        solution[col] = a[i][cols]
    return solution


def _miqp_small_qp(
    indices: Sequence[int],
    lower: float,
    upper: Sequence[float],
    linear: Sequence[float],
) -> tuple[float, list[float]] | None:
    """Exact minimum of x'Sx + linear'x with sum x = 1, mu'x >= target and lower <= x <= upper.

    The problem is convex, so any KKT point is a global minimum. With at most five variables the
    KKT points are found by trying every choice of "at lower / at upper / free" per variable and
    "return constraint active / inactive". Returns None when no feasible point exists.
    """
    sigma = _miqp_covariance()
    size = len(indices)
    q = [[sigma[i][j] for j in indices] for i in indices]
    c = [linear[i] for i in indices]
    mu = [MIQP_RETURN[i] for i in indices]
    ub = [upper[i] for i in indices]
    best: tuple[float, list[float]] | None = None
    for status in itertools.product((0, 1, 2), repeat=size):  # 0 free, 1 at lower, 2 at upper
        for active in (False, True):
            x = [lower if s == 1 else ub[j] if s == 2 else 0.0 for j, s in enumerate(status)]
            free = [j for j, s in enumerate(status) if s == 0]
            fixed = [j for j, s in enumerate(status) if s != 0]
            count = len(free) + 1 + (1 if active else 0)
            matrix, rhs = [], []
            for j in free:
                row = [2 * q[j][k] for k in free] + [-1.0] + ([-mu[j]] if active else [])
                matrix.append(row)
                rhs.append(-c[j] - sum(2 * q[j][k] * x[k] for k in fixed))
            matrix.append([1.0] * len(free) + [0.0] * (count - len(free)))
            rhs.append(1.0 - sum(x[k] for k in fixed))
            if active:
                matrix.append([mu[j] for j in free] + [0.0, 0.0])
                rhs.append(MIQP_TARGET - sum(mu[k] * x[k] for k in fixed))
            solved = _solve_consistent(matrix, rhs)
            if solved is None:
                continue
            for position, j in enumerate(free):
                x[j] = solved[position]
            lam = solved[len(free)]
            nu = solved[len(free) + 1] if active else 0.0
            if any(x[j] < lower - MIQP_TOL or x[j] > ub[j] + MIQP_TOL for j in range(size)):
                continue
            if abs(sum(x) - 1.0) > 1e-7 or sum(m * v for m, v in zip(mu, x, strict=True)) < (
                MIQP_TARGET - 1e-7
            ):
                continue
            if nu < -MIQP_TOL:
                continue
            gradient = [
                2 * sum(q[j][k] * x[k] for k in range(size)) + c[j] - lam - nu * mu[j]
                for j in range(size)
            ]
            if any(status[j] == 1 and gradient[j] < -1e-7 for j in range(size)):
                continue
            if any(status[j] == 2 and gradient[j] > 1e-7 for j in range(size)):
                continue
            value = sum(x[j] * q[j][k] * x[k] for j in range(size) for k in range(size))
            value += sum(c[j] * x[j] for j in range(size))
            if best is None or value < best[0]:
                best = (value, list(x))
    return best


def miqp_enumerate(
    upper: Sequence[float] = MIQP_CAP,
) -> list[tuple[float, tuple[int, ...], list[float]]]:
    """Subsets of at most MIQP_MAX_HELD assets as (variance + fee, subset, weights), best first."""
    found = []
    for size in range(1, MIQP_MAX_HELD + 1):
        for subset in itertools.combinations(range(5), size):
            result = _miqp_small_qp(subset, MIQP_LOT, upper, [0.0] * 5)
            if result is not None:
                found.append((result[0] + MIQP_FEE * size, subset, result[1]))
    return sorted(found, key=lambda item: item[0])


def miqp_relaxation(big_m: Sequence[float]) -> tuple[float, list[float]]:
    """Continuous relaxation of the big-M model: z_i = x_i / M_i leaves cost fee * x_i / M_i."""
    upper = [min(cap, m) for cap, m in zip(MIQP_CAP, big_m, strict=True)]
    linear = [MIQP_FEE / m for m in big_m]
    result = _miqp_small_qp(range(5), 0.0, upper, linear)
    assert result is not None
    return result


def miqp_big_m_rows() -> list[tuple[str, float, float, tuple[int, ...]]]:
    """(label, relaxation bound, integer optimum, optimal subset) for each choice of M."""
    rows = []
    for label, big_m in (
        ("M ＝ 各銘柄の上限", MIQP_CAP),
        ("M ＝ 1", (1.0,) * 5),
        ("M ＝ 10", (10.0,) * 5),
        ("M ＝ 100", (100.0,) * 5),
        ("M ＝ 0.4（上限より小さい別の問題）", (0.4,) * 5),
    ):
        upper = [min(cap, m) for cap, m in zip(MIQP_CAP, big_m, strict=True)]
        best = miqp_enumerate(upper)[0]
        rows.append((label, miqp_relaxation(big_m)[0], best[0], best[1]))
    return rows


def _miqp_big_m_svg() -> str:
    rows = miqp_big_m_rows()
    parts = _open(
        "M の大きさと下界",
        (
            "5銘柄から3銘柄以内を選ぶポートフォリオで、"
            "big-M の M を変えたときの連続緩和の下界と整数の最適値です。"
            + "".join(
                f"{label.split('（')[0]}では下界{bound:.2f}、最適値{best:.2f}。"
                for label, bound, best, _ in rows
            )
        ),
        524,
    )
    px = _scale(88.0, 130.0, 40, 420)
    axis_y = 60 + len(rows) * 68
    for tick in (90, 100, 110, 120, 130):
        parts.append(
            f'<path d="M{px(tick):.2f} {axis_y - 6}V{axis_y + 6}" '
            f'stroke="{POINT}" stroke-width="2"/>'
        )
        parts.append(_text(px(tick), axis_y + 22, f"{tick}", "tick", "middle"))
    parts.append(f'<path d="M40 {axis_y}H420" stroke="{POINT}" stroke-width="2"/>')
    parts.append(_text(420, axis_y + 46, "目的値（分散＋固定費）", "tick", "end"))
    for index, (label, bound, best, _) in enumerate(rows):
        top = 66 + index * 68
        line_y = top + 24
        parts.append(_text(20, top + 6, label))
        for tick in (90, 100, 110, 120, 130):
            parts.append(
                f'<path d="M{px(tick):.2f} {line_y - 9}V{line_y + 9}" '
                f'stroke="{GRID}" stroke-width="1"/>'
            )
        parts.append(
            f'<path d="M{px(bound):.2f} {line_y}H{px(best):.2f}" '
            f'stroke="{POINT}" stroke-width="3"/>'
        )
        parts.append(
            f'<circle cx="{px(bound):.2f}" cy="{line_y}" r="7" fill="{UPDATE}"/>'
            f'<circle cx="{px(best):.2f}" cy="{line_y}" r="7" fill="{LINE}"/>'
        )
        parts.append(_text(min(max(px(bound), 62), 398), line_y + 28, f"{bound:.2f}", "", "middle"))
        parts.append(_text(min(max(px(best), 62), 398), line_y + 28, f"{best:.2f}", "", "middle"))
    legend_y = axis_y + 76
    parts.append(f'<circle cx="28" cy="{legend_y - 5}" r="7" fill="{UPDATE}"/>')
    parts.append(_text(44, legend_y, "橙：連続緩和の下界"))
    parts.append(f'<circle cx="28" cy="{legend_y + 23}" r="7" fill="{LINE}"/>')
    parts.append(_text(44, legend_y + 28, "緑：整数の最適値（列挙で確認）"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


# Robust regression (content/concepts/robust-regression.md): one constant fitted to (0, 0, 0, 10).
ROBUST_OBSERVATIONS = (0.0, 0.0, 0.0, 10.0)
ROBUST_DELTA = 1.0


def _robust_slope(residual: float, delta: float | None) -> float:
    """Loss slope: r for the squared loss (delta None), clip(r, -delta, delta) for Huber."""
    if delta is None:
        return residual
    return max(-delta, min(delta, residual))


def robust_fit(delta: float | None) -> tuple[float, list[float]]:
    """Minimiser of the summed loss (bisection on the monotone slope sum) and each slope there."""
    low, high = min(ROBUST_OBSERVATIONS), max(ROBUST_OBSERVATIONS)
    for _ in range(200):
        mid = (low + high) / 2
        total = sum(_robust_slope(mid - y, delta) for y in ROBUST_OBSERVATIONS)
        low, high = (low, mid) if total > 0 else (mid, high)
    x = (low + high) / 2
    return x, [_robust_slope(x - y, delta) for y in ROBUST_OBSERVATIONS]


def _fraction(value: float) -> str:
    return "1/3" if abs(value - 1 / 3) < 1e-9 else f"{value:g}".replace("-", "−")


def _robust_huber_svg() -> str:
    squared_x, squared = robust_fit(None)
    huber_x, huber = robust_fit(ROBUST_DELTA)
    parts = _open(
        "傾きを抑えると、釣合いが変わる",
        (
            "「残差 r と損失の傾き」は、二乗が r のまま増え、Huber（δ=1）は±1で頭打ちです。"
            f"「各解での、四観測の勾配への寄与」は観測 (0, 0, 0, 10) について、"
            f"二乗の解 x={squared_x:g} では 2.5, 2.5, 2.5, −7.5、"
            "Huberの解 x=1/3 では 1/3, 1/3, 1/3, −1 となり、"
            "どちらも合計は0です。"
        ),
        560,
    )
    parts.append(_text(20, 60, "① 残差 r と損失の傾き"))
    px = _scale(-3.0, 3.0, 64, 420)
    py = _scale(-3.0, 3.0, 220, 80)
    parts.append(f'<path d="M64 80V220H420" fill="none" stroke="{GRID}"/>')
    parts.append(f'<path d="M64 {py(0):.1f}H420" stroke="{GRID}" stroke-width="1"/>')
    for x in (-1.0, 1.0):
        parts.append(
            f'<path d="M{px(x):.1f} 80V220" stroke="{GRID}" stroke-width="1" '
            'stroke-dasharray="3 4"/>'
        )
    for value in (-3.0, 0.0, 3.0):
        parts.append(_text(56, py(value) + 5, f"{value:g}".replace("-", "−"), "tick", "end"))
        parts.append(_text(px(value), 240, f"{value:g}".replace("-", "−"), "tick", "middle"))
    parts.append(_text(420, 262, "残差 r", "tick", "end"))
    parts.append(_polyline([(px(-3), py(-3)), (px(3), py(3))], POINT, 3))
    parts.append(
        _polyline(
            [(px(r), py(_robust_slope(r, ROBUST_DELTA))) for r in (-3.0, -1.0, 1.0, 3.0)],
            UPDATE,
            3,
        )
    )
    parts.append(_text(72, 100, "二乗の傾き r").replace("<text ", f'<text style="fill:{POINT}" '))
    parts.append(
        _text(420, py(1.0) + 22, "Huber（δ=1）", anchor="end").replace(
            "<text ", f'<text style="fill:{UPDATE}" '
        )
    )

    parts.append(_text(20, 300, "② 各解での、四観測の勾配への寄与"))
    top, bottom = 330, 470
    qy = _scale(-10.5, 5.0, bottom, top)
    group = (420 - 64) / 4
    bar = 26.0
    parts.append(f'<path d="M64 {top}V{bottom}H420" fill="none" stroke="{GRID}"/>')
    parts.append(f'<path d="M64 {qy(0):.1f}H420" stroke="{GRID}" stroke-width="1"/>')
    for value in (-5.0, 0.0, 5.0):
        parts.append(_text(56, qy(value) + 5, f"{value:g}".replace("-", "−"), "tick", "end"))
    for index, label in enumerate(("0①", "0②", "0③", "10")):
        centre = 64 + group * (index + 0.5)
        parts.append(_text(centre, bottom + 20, label, "tick", "middle"))
        for offset, value, color in ((-bar - 2, squared[index], POINT), (2, huber[index], UPDATE)):
            y0, y1 = qy(0), qy(value)
            parts.append(
                f'<rect x="{centre + offset:.1f}" y="{min(y0, y1):.1f}" width="{bar}" '
                f'height="{abs(y1 - y0):.1f}" fill="{color}"/>'
            )
            label_y = y1 - 6 if value > 0 else y1 + 16
            parts.append(
                _text(centre + offset + bar / 2, label_y, _fraction(value), "tick", "middle")
            )
    parts.append(f'<rect x="20" y="504" width="20" height="12" fill="{POINT}"/>')
    parts.append(_text(48, 515, f"二乗の解 x={squared_x:g}"))
    parts.append(f'<rect x="230" y="504" width="20" height="12" fill="{UPDATE}"/>')
    parts.append(_text(258, 515, "Huberの解 x=1/3"))
    parts.append(_text(20, 546, "どちらの解でも、四つの寄与の和は0", "note"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


# Hyperparameter optimization (content/concepts/hyperparameter-optimization.md): a ridge
# polynomial fit on 30 noisy points; the objective is the 5-fold cross-validation error.
HPO_N = 30
HPO_SIGMA = 0.4
HPO_LOG_LAM = (-6.0, 1.0)
HPO_DEGREES = list(range(2, 16))
HPO_DATA_SEED = 1
HPO_BUDGET = 16
HPO_RANDOM_SEED = 0
HPO_GRID_DEGREES = (2, 6, 11, 15)


def hpo_data(seed: int = HPO_DATA_SEED, n: int = HPO_N) -> tuple[list[float], list[float]]:
    rng = random.Random(seed)
    xs = [rng.uniform(-1, 1) for _ in range(n)]
    ys = [math.sin(3 * v) + 0.5 * v + HPO_SIGMA * rng.gauss(0, 1) for v in xs]
    return xs, ys


def _legendre_row(x: float, degree: int) -> list[float]:
    row = [1.0, x]
    for n in range(2, degree + 1):
        row.append(((2 * n - 1) * x * row[n - 1] - (n - 1) * row[n - 2]) / n)
    return row[: degree + 1]


def _hpo_fit(xs: Sequence[float], ys: Sequence[float], degree: int, lam: float) -> list[float]:
    rows = [_legendre_row(x, degree) for x in xs]
    size = degree + 1
    gram = [
        [sum(r[i] * r[j] for r in rows) + (len(xs) * lam if i == j else 0.0) for j in range(size)]
        for i in range(size)
    ]
    rhs = [sum(r[i] * y for r, y in zip(rows, ys, strict=True)) for i in range(size)]
    return _solve_linear(gram, rhs)


def hpo_cv_mse(
    xs: Sequence[float],
    ys: Sequence[float],
    degree: int,
    lam: float,
    k: int = 5,
    split_seed: int = 0,
) -> float:
    order = list(range(len(xs)))
    random.Random(split_seed).shuffle(order)
    errors = []
    for i in range(k):
        fold = order[i::k]
        train = [j for j in order if j not in fold]
        w = _hpo_fit([xs[j] for j in train], [ys[j] for j in train], degree, lam)
        squares = [
            (sum(c * b for c, b in zip(w, _legendre_row(xs[j], degree), strict=True)) - ys[j]) ** 2
            for j in fold
        ]
        errors.append(sum(squares) / len(squares))
    return sum(errors) / k


def hpo_random_configs(seed: int = HPO_RANDOM_SEED, n: int = HPO_BUDGET) -> list[tuple[int, float]]:
    rng = random.Random(seed)
    low, high = HPO_LOG_LAM
    return [(rng.choice(HPO_DEGREES), 10.0 ** rng.uniform(low, high)) for _ in range(n)]


def hpo_grid_configs() -> list[tuple[int, float]]:
    low, high = HPO_LOG_LAM
    exponents = [low + (high - low) * i / 3 for i in range(4)]
    return [(d, 10.0**e) for d in HPO_GRID_DEGREES for e in exponents]


def hpo_search_data() -> dict[str, object]:
    xs, ys = hpo_data()
    out: dict[str, object] = {}
    for name, configs in (("grid", hpo_grid_configs()), ("random", hpo_random_configs())):
        values = [hpo_cv_mse(xs, ys, d, lam) for d, lam in configs]
        best = min(range(len(configs)), key=lambda i: values[i])
        out[name] = {
            "configs": configs,
            "values": values,
            "best": best,
            "distinct_lam": len({lam for _, lam in configs}),
            "distinct_degree": len({d for d, _ in configs}),
        }
    low, high = HPO_LOG_LAM
    columns = int((high - low) * 2)
    out["terrain"] = {
        (d, c): hpo_cv_mse(xs, ys, d, 10.0 ** (low + (c + 0.5) / 2))
        for d in HPO_DEGREES
        for c in range(columns)
    }
    return out


def _hpo_shade(value: float) -> str:
    """Grey ramp for the cross-validation error: pale at 0.13 or less, dark at 1 or more."""
    t = (math.log10(max(value, 0.13)) - math.log10(0.13)) / (math.log10(1.0) - math.log10(0.13))
    t = min(max(t, 0.0), 1.0)
    low, high = (0xEE, 0xF0, 0xEA), (0x7C, 0x86, 0x7E)
    r, g, b = (round(a + (c - a) * t) for a, c in zip(low, high, strict=True))
    return f"#{r:02x}{g:02x}{b:02x}"


def _hpo_search_svg() -> str:
    data = hpo_search_data()
    terrain = data["terrain"]
    low, high = HPO_LOG_LAM
    grid, rand = data["grid"], data["random"]
    parts = _open(
        "同じ16回で試す設定",
        (
            "次数と正則化の強さの2つの設定を、評価16回で探す2つの方法です。"
            f"格子ではlog10 λの値が{grid['distinct_lam']}種類、"  # type: ignore[index]
            f"ランダムでは{rand['distinct_lam']}種類（seed 0）になります。"  # type: ignore[index]
            f"背景の灰色の濃さは交差検証誤差で、16点の最良は格子が{grid['values'][grid['best']]:.3f}、"  # type: ignore[index]
            f"ランダムが{rand['values'][rand['best']]:.3f}です。"  # type: ignore[index]
        ),
        596,
    )
    px = _scale(low, high, 64, 420)
    cell_w = (420 - 64) / ((high - low) * 2)
    cell_h = 10
    for index, (key, label) in enumerate(
        (
            ("grid", "格子（4×4）：λは{n}種類"),
            ("random", "ランダム：λは{n}種類"),
        )
    ):
        top = 66 + index * 216
        group = data[key]
        parts.append(_text(20, top - 12, label.format(n=group["distinct_lam"])))  # type: ignore[index]
        for d in HPO_DEGREES:
            y = top + (15 - d) * cell_h
            for c in range(int((high - low) * 2)):
                parts.append(
                    f'<rect x="{64 + c * cell_w:.2f}" y="{y}" width="{cell_w + 0.4:.2f}" '
                    f'height="{cell_h}" fill="{_hpo_shade(terrain[(d, c)])}"/>'  # type: ignore[index]
                )
        parts.append(
            f'<path d="M64 {top}V{top + 14 * cell_h}H420" fill="none" stroke="{POINT}" '
            'stroke-width="1.5"/>'
        )
        for d in (2, 8, 15):
            parts.append(_text(56, top + (15 - d) * cell_h + 9, f"{d}", "tick", "end"))
        for e in (-6, -4, -2, 0):
            parts.append(_text(px(e), top + 14 * cell_h + 36, f"{e}", "tick", "middle"))
        for _, lam in group["configs"]:  # type: ignore[index]
            parts.append(
                f'<path d="M{px(math.log10(lam)):.2f} {top + 14 * cell_h + 3}v10" '
                f'stroke="{POINT}" stroke-width="2"/>'
            )
        for i, (d, lam) in enumerate(group["configs"]):  # type: ignore[index]
            cx, cy = px(math.log10(lam)), top + (15 - d) * cell_h + cell_h / 2
            parts.append(
                f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="4.5" fill="{LINE}" stroke="#f7f8f3" '
                'stroke-width="1.5"/>'
            )
            if i == group["best"]:  # type: ignore[index]
                parts.append(
                    f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="9" fill="none" stroke="{UPDATE}" '
                    'stroke-width="3"/>'
                )
    parts.append(_text(420, 66 + 216 + 14 * cell_h + 58, "log10 λ", "tick", "end"))
    parts.append(_text(70, 66 + 216 + 14 * cell_h + 58, "各パネルの縦は次数 d", "tick"))
    parts.append(_text(20, 520, "緑の丸：評価した設定　橙の輪：16点のうちの最良"))
    parts.append(_text(20, 544, "紺の短い線：試したλの値　灰が濃いほど誤差が大きい", "note"))
    parts.append(
        _text(
            20,
            568,
            f"最良の誤差　格子 {grid['values'][grid['best']]:.3f}　"  # type: ignore[index]
            f"ランダム {rand['values'][rand['best']]:.3f}",
            "note",
        )
    )
    parts.append("</svg>")
    return "".join(parts) + "\n"


# Mixed-integer linear program (content/concepts/mixed-integer-linear-program.md):
# max 5x1 + 4x2 s.t. 6x1 + 4x2 <= 24, x1 + 2x2 <= 6, x >= 0. Five LP relaxations chosen by hand.
MILP_PROFIT = (5, 4)
MILP_ROWS = ((6, 4, 24), (1, 2, 6), (-1, 0, 0), (0, -1, 0))
# (name, label, extra rows a1*x1 + a2*x2 <= b added to the relaxation)
MILP_NODES = (
    ("root", "整数条件を外す", ()),
    ("left", "x₂ ≤ 1", ((0, 1, 1),)),
    ("left_left", "x₁ ≤ 3", ((0, 1, 1), (1, 0, 3))),
    ("left_right", "x₁ ≥ 4", ((0, 1, 1), (-1, 0, -4))),
    ("right", "x₂ ≥ 2", ((0, -1, -2),)),
)


def milp_relaxation(
    extra: Sequence[tuple[int, int, int]] = (),
) -> tuple[tuple[Fraction, Fraction], Fraction]:
    """Exact optimum of the LP relaxation with the added bound rows, by vertex enumeration."""
    rows = [*MILP_ROWS, *extra]
    best: tuple[Fraction, Fraction, Fraction] | None = None
    for (a1, a2, b), (c1, c2, d) in itertools.combinations(rows, 2):
        det = a1 * c2 - a2 * c1
        if det == 0:
            continue
        x1, x2 = Fraction(b * c2 - a2 * d, det), Fraction(a1 * d - b * c1, det)
        if all(r1 * x1 + r2 * x2 <= rb for r1, r2, rb in rows):
            value = MILP_PROFIT[0] * x1 + MILP_PROFIT[1] * x2
            if best is None or value > best[2]:
                best = (x1, x2, value)
    assert best is not None
    return (best[0], best[1]), best[2]


def milp_integer_points() -> list[tuple[int, int]]:
    return [
        (i, j)
        for i in range(8)
        for j in range(8)
        if all(a * i + b * j <= c for a, b, c in MILP_ROWS)
    ]


def _milp_number(value: Fraction) -> str:
    if value.denominator == 1:
        return str(value.numerator)
    if value.denominator in (2, 4, 5, 8, 10):
        return f"{float(value):g}"
    return f"{value.numerator}/{value.denominator}"


def _milp_tree_svg() -> str:
    solved = {name: milp_relaxation(extra) for name, _, extra in MILP_NODES}
    labels = {name: label for name, label, _ in MILP_NODES}
    # (centre x, top y, width) of each box; one SVG unit is one CSS pixel on a PC.
    boxes = {
        "root": (220, 50, 170),
        "left": (134, 168, 140),
        "right": (350, 168, 140),
        "left_left": (68, 286, 124),
        "left_right": (200, 286, 124),
    }
    height_box = 80
    parts = _open(
        "手で指定した5個のLP緩和",
        (
            "最大化の例の分枝木です。根のLP緩和は(3, 1.5)で上界21。"
            "x2を1以下と2以上に分け、x2が1以下の枝をさらにx1が3以下と4以上に分けます。"
            "葉の値は19、20、18で、整数解(4, 0)の利益20が最良です。"
        ),
        430,
    )
    for parent, child in (
        ("root", "left"),
        ("root", "right"),
        ("left", "left_left"),
        ("left", "left_right"),
    ):
        px_, py_, _ = boxes[parent]
        cx, cy, _ = boxes[child]
        parts.append(
            f'<path d="M{px_} {py_ + height_box}L{cx} {cy}" stroke="{POINT}" stroke-width="2"/>'
        )
    for name, (cx, top, width) in boxes.items():
        point, value = solved[name]
        best = name == "left_right"
        parts.append(
            f'<rect x="{cx - width / 2}" y="{top}" width="{width}" height="{height_box}" rx="8" '
            f'fill="{"#fbeee6" if best else "#ffffff"}" '
            f'stroke="{UPDATE if best else POINT}" stroke-width="{3 if best else 1.5}"/>'
        )
        coordinates = f"({_milp_number(point[0])}, {_milp_number(point[1])})"
        kind = "値" if name in ("left_left", "left_right") else "上界"
        parts.append(_text(cx, top + 23, labels[name], "", "middle"))
        parts.append(_text(cx, top + 47, coordinates, "", "middle"))
        parts.append(_text(cx, top + 70, f"{kind} {_milp_number(value)}", "note", "middle"))
    parts.append(_text(20, 392, "橙の枠：整数解 (4, 0)、利益20"))
    parts.append(_text(20, 416, "葉の19、20、18は、どれも20以下", "note"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


# Smooth bound-constrained (content/concepts/bound-constrained-smooth.md): a greenhouse heater
# x1 and fan x2, both in [0, 1]. f(x) = (x1-2)^2 + 2(x2-1)^2 + 2 x1 x2.
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


# Second-order cone program (content/concepts/second-order-cone-program.md): one relay station
# that reaches three villages, min t s.t. |x - p_i| <= t. Coordinates in km.
SOCP_VILLAGES = ((0, 0), (6, 0), (2, 4))
SOCP_WIDE_RADIUS = 3.6  # a radius above the optimum, where the three discs still overlap


def socp_center() -> tuple[tuple[Fraction, Fraction], tuple[Fraction, Fraction, Fraction]]:
    """Circumcentre of the three villages and its barycentric weights (the optimal multipliers).

    In an acute triangle all three constraints are active at the optimum, so the centre is the
    point equidistant from the villages; weights that are all positive certify optimality.
    """
    (ax, ay), (bx, by), (cx, cy) = SOCP_VILLAGES
    d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    sq = [x * x + y * y for x, y in SOCP_VILLAGES]
    ux = Fraction(sq[0] * (by - cy) + sq[1] * (cy - ay) + sq[2] * (ay - by), d)
    uy = Fraction(sq[0] * (cx - bx) + sq[1] * (ax - cx) + sq[2] * (bx - ax), d)
    # Solve l_a a + l_b b + l_c c = centre with l_a + l_b + l_c = 1 (Cramer's rule).
    area = Fraction((bx - ax) * (cy - ay) - (cx - ax) * (by - ay))
    l_b = ((ux - ax) * (cy - ay) - (cx - ax) * (uy - ay)) / area
    l_c = ((bx - ax) * (uy - ay) - (ux - ax) * (by - ay)) / area
    return (ux, uy), (1 - l_b - l_c, l_b, l_c)


def _socp_panel(top: float, radius: float, title: str, clip: str) -> tuple[list[str], Callable]:
    """One map panel (44 px per km) with the three discs of the given radius, clipped to it."""
    px = _scale(-0.8, 6.8, 64, 398)
    py = _scale(-1.0, 4.8, top + 268, top + 13)
    parts = [
        _text(20, top, title, "title"),
        f'<clipPath id="{clip}"><rect x="{px(-0.8):.1f}" y="{py(4.8):.1f}" '
        f'width="{px(6.8) - px(-0.8):.1f}" height="{py(-1.0) - py(4.8):.1f}"/></clipPath>',
        f'<rect x="{px(-0.8):.1f}" y="{py(4.8):.1f}" width="{px(6.8) - px(-0.8):.1f}" '
        f'height="{py(-1.0) - py(4.8):.1f}" fill="#ffffff" stroke="{GRID}"/>',
    ]
    scale = px(1) - px(0)
    for index, (vx, vy) in enumerate(SOCP_VILLAGES):
        parts.append(f'<clipPath id="{clip}-{index}">')
        parts.append(f'<circle cx="{px(vx):.2f}" cy="{py(vy):.2f}" r="{radius * scale:.2f}"/>')
        parts.append("</clipPath>")
    # The overlap of the three discs: disc A drawn inside the clips of discs B and C.
    (ax, ay) = SOCP_VILLAGES[0]
    parts.append(
        f'<g clip-path="url(#{clip}-1)"><g clip-path="url(#{clip}-2)">'
        f'<circle cx="{px(ax):.2f}" cy="{py(ay):.2f}" r="{radius * scale:.2f}" '
        'fill="#f2c9b4"/></g></g>'
    )
    parts.append(f'<g clip-path="url(#{clip})">')
    for vx, vy in SOCP_VILLAGES:
        parts.append(
            f'<circle cx="{px(vx):.2f}" cy="{py(vy):.2f}" r="{radius * scale:.2f}" '
            f'fill="none" stroke="{LINE}" stroke-width="1.5"/>'
        )
    parts.append("</g>")
    for (vx, vy), name in zip(SOCP_VILLAGES, "ABC", strict=True):
        parts.append(
            f'<rect x="{px(vx) - 6:.2f}" y="{py(vy) - 6:.2f}" width="12" height="12" '
            f'fill="{POINT}"/>'
        )
        parts.append(_text(px(vx) + 10, py(vy) - 8, name))
    return parts, lambda x, y: (px(x), py(y))


def _socp_relay_svg() -> str:
    (cx, cy), weights = socp_center()
    radius = math.dist((float(cx), float(cy)), SOCP_VILLAGES[0])
    centroid = tuple(sum(p[k] for p in SOCP_VILLAGES) / 3 for k in range(2))
    centroid_far = max(math.dist(centroid, p) for p in SOCP_VILLAGES)
    parts = _open(
        "3集落に届く中継局",
        (
            f"集落A(0,0)、B(6,0)、C(2,4)と、半径{SOCP_WIDE_RADIUS}kmと半径√10の円です。"
            f"半径{SOCP_WIDE_RADIUS}kmでは3つの円が重なる領域があり、重心"
            f"({centroid[0]:.2f}, {centroid[1]:.2f})もその中にあります。"
            f"半径√10≈{radius:.3f}kmでは、3つの円が点({cx}, {cy})だけで重なります。"
            "その点から各集落へ向かう矢印の長さは重み"
            f"{'、'.join(str(w) for w in weights)}に比例し、3本の和は0です。"
        ),
        758,
    )
    top_parts, top_xy = _socp_panel(66, SOCP_WIDE_RADIUS, f"半径 {SOCP_WIDE_RADIUS} km", "socp-a")
    parts.extend(top_parts)
    gx, gy = top_xy(*centroid)
    parts.append(f'<circle cx="{gx:.2f}" cy="{gy:.2f}" r="5" fill="{MUTED}"/>')
    parts.append(_text(gx - 10, gy + 5, "重心", "tick", "end"))
    far = max(range(3), key=lambda i: math.dist(centroid, SOCP_VILLAGES[i]))
    parts.append(_text(20, 362, "橙の領域：3集落すべてに届く位置", "note"))
    parts.append(_text(20, 386, f"重心から最も遠い{'ABC'[far]}まで {centroid_far:.3f} km", "note"))
    low_parts, low_xy = _socp_panel(430, radius, f"半径 √10 ≈ {radius:.3f} km", "socp-b")
    parts.extend(low_parts)
    ox, oy = low_xy(float(cx), float(cy))
    arrow_km = 4.0  # an arrow of weight 1 would be 4 km long
    for (vx, vy), weight in zip(SOCP_VILLAGES, weights, strict=True):
        dx, dy = (vx - float(cx)) / radius, (vy - float(cy)) / radius
        hx, hy = low_xy(
            float(cx) + dx * arrow_km * float(weight), float(cy) + dy * arrow_km * float(weight)
        )
        parts.append(
            f'<path d="M{ox:.2f} {oy:.2f}L{hx:.2f} {hy:.2f}" stroke="{UPDATE}" stroke-width="3"/>'
        )
        parts.append(f'<circle cx="{hx:.2f}" cy="{hy:.2f}" r="3.5" fill="{UPDATE}"/>')
        parts.append(
            _text(
                hx + (8 if dx >= 0 else -8),
                hy + (18 if dy < 0 else -6),
                str(weight),
                "tick",
                "start" if dx >= 0 else "end",
            )
        )
    parts.append(f'<circle cx="{ox:.2f}" cy="{oy:.2f}" r="6" fill="{UPDATE}"/>')
    parts.append(_text(20, 724, f"円が1点 ({cx}, {cy}) だけで重なる", "note"))
    parts.append(_text(20, 748, "矢印の長さは重み。3本の和は0", "note"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


# Network flow (content/concepts/network-flow.md): four boxes from the factory S to the shop T.
FLOW_NODES = ("S", "A", "B", "T")
# (from, to, cost per box, capacity per day)
FLOW_ARCS = (
    ("S", "A", 1, 3),
    ("S", "B", 4, 3),
    ("A", "B", 1, 3),
    ("A", "T", 5, 2),
    ("B", "T", 1, 3),
)
FLOW_BOXES = 4


def flow_successive_paths(
    boxes: int = FLOW_BOXES, use_reverse: bool = True
) -> list[tuple[str, int, int, dict[tuple[str, str], int]]]:
    """Successive shortest paths on the residual network (Bellman–Ford).

    Returns (path, cost per box, boxes sent, flow after the push) for each push; the list
    stops early when no residual path reaches T.
    """
    flow = {(u, v): 0 for u, v, _, _ in FLOW_ARCS}
    pushes: list[tuple[str, int, int, dict[tuple[str, str], int]]] = []
    sent = 0
    while sent < boxes:
        residual = []
        for u, v, cost, cap in FLOW_ARCS:
            if flow[u, v] < cap:
                residual.append((u, v, cost, cap - flow[u, v], (u, v), 1))
            if use_reverse and flow[u, v] > 0:
                residual.append((v, u, -cost, flow[u, v], (u, v), -1))
        dist: dict[str, float] = {n: math.inf for n in FLOW_NODES}
        dist["S"] = 0
        pred: dict[str, tuple[str, int, tuple[str, str], int]] = {}
        for _ in FLOW_NODES:
            for u, v, cost, left, arc, sign in residual:
                if dist[u] + cost < dist[v]:
                    dist[v], pred[v] = dist[u] + cost, (u, left, arc, sign)
        if dist["T"] == math.inf:
            break
        path, amount, node = ["T"], boxes - sent, "T"
        while node != "S":
            u, left, _, _ = pred[node]
            amount, node = min(amount, left), u
            path.insert(0, node)
        node = "T"
        while node != "S":
            u, _, arc, sign = pred[node]
            flow[arc] += sign * amount
            node = u
        sent += amount
        pushes.append(("→".join(path), int(dist["T"]), amount, dict(flow)))
    return pushes


def flow_cost(flow: dict[tuple[str, str], int]) -> int:
    return sum(cost * flow[u, v] for u, v, cost, _ in FLOW_ARCS)


def _flow_panel(top: float, flow: dict[tuple[str, str], int]) -> list[str]:
    """One network panel: arcs drawn thicker with more boxes, labelled flow/capacity and cost."""
    at = {"S": (44, top + 92), "A": (220, top + 26), "B": (220, top + 158), "T": (396, top + 92)}
    # label anchor (x, y, text-anchor) for each arc, placed beside its middle
    label = {
        ("S", "A"): (122, top + 34, "middle"),
        ("S", "B"): (122, top + 166, "middle"),
        ("A", "B"): (232, top + 86, "start"),
        ("A", "T"): (318, top + 34, "middle"),
        ("B", "T"): (318, top + 166, "middle"),
    }
    parts = []
    radius = 19
    for u, v, cost, cap in FLOW_ARCS:
        (x1, y1), (x2, y2) = at[u], at[v]
        length = math.hypot(x2 - x1, y2 - y1)
        dx, dy = (x2 - x1) / length, (y2 - y1) / length
        sx, sy = x1 + dx * radius, y1 + dy * radius
        ex, ey = x2 - dx * (radius + 4), y2 - dy * (radius + 4)
        boxes = flow[u, v]
        color = UPDATE if boxes else GRID
        width = 2 + 2.5 * boxes
        marker = "flow-head" if boxes else "flow-head-empty"
        parts.append(
            f'<path d="M{sx:.1f} {sy:.1f}L{ex:.1f} {ey:.1f}" stroke="{color}" '
            f'stroke-width="{width:g}" stroke-linecap="round" marker-end="url(#{marker})"/>'
        )
        lx, ly, anchor = label[u, v]
        full = "（満杯）" if boxes == cap else ""
        parts.append(_text(lx, ly, f"{boxes}/{cap}{full}", "", anchor))
        parts.append(_text(lx, ly + 19, f"運賃{cost}", "tick", anchor))
    for name, (x, y) in at.items():
        parts.append(
            f'<circle cx="{x}" cy="{y:.1f}" r="{radius}" fill="#ffffff" stroke="{POINT}" '
            'stroke-width="2"/>'
        )
        parts.append(_text(x, y + 6, name, "", "middle"))
    return parts


def _network_flow_svg() -> str:
    pushes = flow_successive_paths()
    first, last = pushes[0], pushes[-1]
    first_cost, total = first[1] * first[2], flow_cost(last[3])
    parts = _open(
        "4箱目は、A→Bを1箱戻して通す",
        (
            f"工場Sから店Tへ{FLOW_BOXES}箱を送る最小費用流です。"
            "各辺の数字は流量/容量と1箱の運賃です。"
            f"最安の経路{first[0]}（1箱{first[1]}）に{first[2]}箱を送ると費用{first_cost}で、"
            "S→AとB→Tが満杯になります。"
            f"4箱目は{last[0]}を通り、A→Bの流れを1箱減らします。"
            f"1箱の運賃は4−1+5={last[1]}で、合計は{total}です。"
        ),
        576,
    )
    parts.append(
        "<defs>"
        f'<marker id="flow-head" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="4" '
        f'markerHeight="4" orient="auto"><path d="M0 0L10 5L0 10z" fill="{UPDATE}"/></marker>'
        f'<marker id="flow-head-empty" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" '
        f'markerHeight="6" orient="auto"><path d="M0 0L10 5L0 10z" fill="{GRID}"/></marker>'
        "</defs>"
    )
    parts.append(_text(20, 64, f"① 最安の経路に{first[2]}箱"))
    parts.append(_text(420, 64, f"費用 {first_cost}", "note", "end"))
    parts += _flow_panel(74, first[3])
    parts.append(_text(20, 304, f"② 4箱目は {last[0]}"))
    parts.append(_text(420, 304, f"費用 {total}", "note", "end"))
    parts += _flow_panel(314, last[3])
    parts.append(_text(20, 536, "辺の数字：流量/容量　橙が太いほど多く流す"))
    parts.append(_text(20, 560, f"4箱目の運賃 4−1+5={last[1]}（A→Bは1箱戻す）", "note"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


# SO(3)/SE(3) (content/concepts/so3-se3-optimization.md): four markers on a box, measured by a
# camera. After subtracting the centroids, only the rotation is left to fit.
SO3_P = ((0.0, 0.0, 0.0), (30.0, 0.0, 0.0), (0.0, 20.0, 0.0), (0.0, 0.0, 10.0))
SO3_Q = ((50.6, 19.2, 80.1), (25.7, 36.2, 87.0), (49.6, 12.2, 98.2), (56.9, 27.5, 83.0))
SO3_STEP = 5e-4
SO3_ITERATIONS = 60

Matrix3 = list[list[float]]


def _identity3() -> Matrix3:
    return [[1.0 if i == j else 0.0 for j in range(3)] for i in range(3)]


def _mat3_mul(a: Matrix3, b: Matrix3) -> Matrix3:
    return [[sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


def _mat3_t(a: Matrix3) -> Matrix3:
    return [[a[j][i] for j in range(3)] for i in range(3)]


def _det3(a: Matrix3) -> float:
    return (
        a[0][0] * (a[1][1] * a[2][2] - a[1][2] * a[2][1])
        - a[0][1] * (a[1][0] * a[2][2] - a[1][2] * a[2][0])
        + a[0][2] * (a[1][0] * a[2][1] - a[1][1] * a[2][0])
    )


def _so3_centered() -> tuple[list[list[float]], list[list[float]]]:
    def centre(points: Sequence[Sequence[float]]) -> list[list[float]]:
        mean = [sum(p[i] for p in points) / len(points) for i in range(3)]
        return [[p[i] - mean[i] for i in range(3)] for p in points]

    return centre(SO3_P), centre(SO3_Q)


def so3_objective(m: Matrix3) -> float:
    """Sum of squared distances between M p_i and q_i for the centred markers."""
    pc, qc = _so3_centered()
    return sum(
        sum((sum(m[i][k] * p[k] for k in range(3)) - q[i]) ** 2 for i in range(3))
        for p, q in zip(pc, qc, strict=True)
    )


def _so3_gradient(m: Matrix3) -> Matrix3:
    pc, qc = _so3_centered()
    grad = [[0.0] * 3 for _ in range(3)]
    for p, q in zip(pc, qc, strict=True):
        r = [sum(m[i][k] * p[k] for k in range(3)) - q[i] for i in range(3)]
        for i in range(3):
            for j in range(3):
                grad[i][j] += 2 * r[i] * p[j]
    return grad


def _so3_exp(w: Sequence[float]) -> Matrix3:
    """Rodrigues' formula: the rotation by |w| about the axis w / |w|."""
    theta = math.sqrt(sum(v * v for v in w))
    k = [[0.0, -w[2], w[1]], [w[2], 0.0, -w[0]], [-w[1], w[0], 0.0]]
    if theta < 1e-12:
        return [[_identity3()[i][j] + k[i][j] for j in range(3)] for i in range(3)]
    k = [[v / theta for v in row] for row in k]
    k2 = _mat3_mul(k, k)
    return [
        [
            _identity3()[i][j] + math.sin(theta) * k[i][j] + (1 - math.cos(theta)) * k2[i][j]
            for j in range(3)
        ]
        for i in range(3)
    ]


def _orthogonality_error(m: Matrix3) -> float:
    mtm = _mat3_mul(_mat3_t(m), m)
    return math.sqrt(sum((mtm[i][j] - _identity3()[i][j]) ** 2 for i in range(3) for j in range(3)))


def _so3_riemannian_step(x: Matrix3) -> Matrix3:
    g = _mat3_mul(_mat3_t(x), _so3_gradient(x))
    w = [(g[2][1] - g[1][2]) / 2, (g[0][2] - g[2][0]) / 2, (g[1][0] - g[0][1]) / 2]
    return _mat3_mul(x, _so3_exp([-SO3_STEP * v for v in w]))


def so3_paths(iterations: int = SO3_ITERATIONS) -> list[dict[str, float]]:
    """From the identity, a gradient step on all nine entries vs a step that stays a rotation."""
    ambient, rotation = _identity3(), _identity3()
    rows = []
    for k in range(iterations + 1):
        if k:
            grad = _so3_gradient(ambient)
            ambient = [[ambient[i][j] - SO3_STEP * grad[i][j] for j in range(3)] for i in range(3)]
            rotation = _so3_riemannian_step(rotation)
        rows.append(
            {
                "k": k,
                "ambient_f": so3_objective(ambient),
                "ambient_orth": _orthogonality_error(ambient),
                "ambient_det": _det3(ambient),
                "rotation_f": so3_objective(rotation),
                "rotation_orth": _orthogonality_error(rotation),
            }
        )
    return rows


def so3_rotation_minimum(iterations: int = 400) -> float:
    rotation = _identity3()
    for _ in range(iterations):
        rotation = _so3_riemannian_step(rotation)
    return so3_objective(rotation)


def _so3_paths_svg() -> str:
    rows = so3_paths()
    best = so3_rotation_minimum()
    flipped = [row["k"] for row in rows if row["ambient_det"] < 0]
    below = next(row["k"] for row in rows if row["ambient_f"] < best)
    last = rows[-1]
    parts = _open(
        "9成分を動かすか、回転のまま動かすか",
        (
            f"箱の4つのマーカーの例で、単位行列から一歩の大きさ{SO3_STEP:g}で{SO3_ITERATIONS}回"
            "更新した2つの経路です。9成分の勾配法は"
            f"k={below}で回転での最小{best:.3f}を下回り、k={SO3_ITERATIONS}で"
            f"{last['ambient_f']:.3f}になります。そのときの‖MᵀM−I‖は{last['ambient_orth']:.3f}で、"
            f"k={flipped[0]}では行列式が{rows[flipped[0]]['ambient_det']:.2f}です。"
            f"回転のまま動かす経路は{last['rotation_f']:.3f}に近づき、"
            "‖MᵀM−I‖は全反復で1e−14より小さいままです。"
        ),
        604,
    )
    px = _scale(0.0, float(SO3_ITERATIONS), 64, 420)

    def panel(
        top: int, bottom: int, upper: float, key_a: str, key_r: str, ticks: Sequence[float]
    ) -> Callable[[float], float]:
        py = _scale(0.0, upper, bottom, top)
        parts.append(f'<path d="M64 {top}V{bottom}H420" fill="none" stroke="{GRID}"/>')
        for value in ticks:
            parts.append(_text(56, py(value) + 5, f"{value:g}", "tick", "end"))
        for k in (0, 20, 40, 60):
            parts.append(_text(px(k), bottom + 20, f"{k}", "tick", "middle"))
        for key, color in ((key_r, POINT), (key_a, UPDATE)):
            points = [(px(row["k"]), py(min(row[key], upper))) for row in rows]
            parts.append(_polyline(points, color, 3))
        return py

    parts.append(_text(20, 62, "① 二乗和（8より大きい値は上端で切る）"))
    py1 = panel(80, 240, 8.0, "ambient_f", "rotation_f", (0.0, 4.0, 8.0))
    parts.append(
        f'<path d="M64 {py1(best):.1f}H420" stroke="{POINT}" stroke-width="1.5" '
        'stroke-dasharray="5 4"/>'
    )
    parts.append(_text(420, py1(best) - 8, f"回転での最小 {best:.3f}", "note", "end"))
    parts.append(_text(420, 282, "反復 k", "tick", "end"))

    parts.append(_text(20, 318, "② 回転からのはずれ ‖MᵀM − I‖"))
    py2 = panel(336, 476, 1.2, "ambient_orth", "rotation_orth", (0.0, 0.6, 1.2))
    first = rows[flipped[0]]
    parts.append(
        f'<circle cx="{px(first["k"]):.1f}" cy="{py2(first["ambient_orth"]):.1f}" r="5" '
        f'fill="none" stroke="{UPDATE}" stroke-width="2"/>'
    )
    parts.append(
        _text(
            px(first["k"]) + 12,
            py2(first["ambient_orth"]) + 6,
            f"k={first['k']}：行列式 {first['ambient_det']:.2f}（鏡像）".replace("-", "−"),
        )
    )
    parts.append(_text(420, 518, "反復 k", "tick", "end"))

    parts.append(f'<path d="M20 548H48" stroke="{UPDATE}" stroke-width="3"/>')
    parts.append(_text(56, 554, "9成分の勾配法"))
    parts.append(f'<path d="M190 548H218" stroke="{POINT}" stroke-width="3"/>')
    parts.append(_text(226, 554, "回転のまま動かす"))
    parts.append(_text(20, 584, f"どちらも単位行列から、一歩の大きさ {SO3_STEP:g}", "note"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


# SO(3) and its Lie algebra (content/concepts/so3-rotation-representation.md): a plane rotation
# [[a, -b], [b, a]] is the point (a, b). Rotations fill the unit circle, the Lie algebra is the
# tangent line at I, and exp wraps the line onto the circle by arc length.
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


# Neural network training (content/concepts/neural-network-training.md): the smallest network
# h(x) = v tanh(u x), four steering readings, mean squared error, full-batch gradient descent.
NN_X = (-2.0, -1.0, 1.0, 2.0)
NN_Y = (-1.0, -0.6, 0.7, 0.9)
NN_ETA = 0.5
NN_START_A = (0.3, -0.2)
NN_START_B = (0.2, -0.3)


def nn_loss(u: float, v: float) -> float:
    return sum((v * math.tanh(u * x) - y) ** 2 for x, y in zip(NN_X, NN_Y, strict=True)) / len(NN_X)


def nn_gradient(u: float, v: float) -> tuple[float, float]:
    gu = gv = 0.0
    for x, y in zip(NN_X, NN_Y, strict=True):
        t = math.tanh(u * x)
        r = v * t - y
        gu += 2 * r * v * x * (1 - t * t) / len(NN_X)
        gv += 2 * r * t / len(NN_X)
    return gu, gv


def nn_path(start: tuple[float, float], steps: int) -> list[tuple[float, float]]:
    u, v = start
    path = [(u, v)]
    for _ in range(steps):
        gu, gv = nn_gradient(u, v)
        u, v = u - NN_ETA * gu, v - NN_ETA * gv
        path.append((u, v))
    return path


def nn_minimum() -> tuple[float, float]:
    return nn_path(NN_START_A, 400)[-1]


def _nn_two_valleys_svg() -> str:
    wu, wv = nn_minimum()
    bottom, saddle = nn_loss(wu, wv), nn_loss(0.0, 0.0)
    path_a, path_b = nn_path(NN_START_A, 12), nn_path(NN_START_B, 12)
    px = _scale(-1.6, 1.6, 64, 400)
    py = _scale(1.6, -1.6, 48, 384)
    parts = _open(
        "重みの平面",
        (
            f"h(x)=v tanh(u x) の4点の平均二乗誤差の等高線。谷底は w*=({wu:.2f}, {wv:.2f}) と "
            f"−w* の二つで、どちらも損失 {bottom:.4f}。原点は勾配が0の鞍点で、損失 {saddle:.3f}。"
            f"学習率 {NN_ETA} の勾配降下法は、始点A {NN_START_A} から w* へ、"
            f"始点B {NN_START_B} から −w* へ進みます。"
            f"二つの谷底を結ぶ線分では、中点の原点で損失が {saddle:.3f} に上がります。"
        ),
        816,
    )
    parts.append(f'<path d="M64 48V384H400V48Z" fill="none" stroke="{GRID}"/>')
    for level in (0.05, 0.2, 0.4, saddle, 1.0, 2.0, 3.5):
        style = (
            f'stroke="{MUTED}" stroke-width="2"'
            if level == saddle
            else f'stroke="{RING}" stroke-width="1.5"'
        )
        segments = _contour_segments(nn_loss, level, (-1.6, 1.6), (-1.6, 1.6), (128, 128))
        data = "".join(
            f"M{px(a[0]):.1f} {py(a[1]):.1f}L{px(b[0]):.1f} {py(b[1]):.1f}" for a, b in segments
        )
        parts.append(f'<path d="{data}" fill="none" {style}/>')
    for value in (-1, 0, 1):
        parts.append(_text(px(value), 404, f"{value}", "tick", "middle"))
        parts.append(_text(56, py(value) + 5, f"{value}", "tick", "end"))
    parts.append(_text(400, 426, "u（入力側の重み）", "tick", "end"))
    parts.append(_text(72, 68, "v（出力側の重み）", "tick"))
    parts.append(
        f'<path d="M{px(-wu):.1f} {py(-wv):.1f}L{px(wu):.1f} {py(wv):.1f}" '
        f'stroke="{MUTED}" stroke-width="2" stroke-dasharray="6 5"/>'
    )
    for path, color in ((path_a, LINE), (path_b, POINT)):
        parts.append(_polyline([(px(a), py(b)) for a, b in path], color, 2.5))
        for a, b in path[1:]:
            parts.append(f'<circle cx="{px(a):.1f}" cy="{py(b):.1f}" r="3.5" fill="{color}"/>')
        a, b = path[0]
        parts.append(
            f'<rect x="{px(a) - 5:.1f}" y="{py(b) - 5:.1f}" width="10" height="10" fill="#f7f8f3" '
            f'stroke="{color}" stroke-width="2.5"/>'
        )
    for sign in (1, -1):
        parts.append(
            f'<circle cx="{px(sign * wu):.1f}" cy="{py(sign * wv):.1f}" r="7" fill="{UPDATE}"/>'
        )
    parts.append(f'<circle cx="{px(0):.1f}" cy="{py(0):.1f}" r="5" fill="{INK}"/>')
    parts.append(_text(px(wu) + 12, py(wv) - 10, "w*"))
    parts.append(_text(px(-wu) - 12, py(-wv) + 22, "−w*", "", "end"))
    parts.append(_text(px(0) - 10, py(0) - 12, "鞍点", "", "end"))
    parts.append(_text(px(NN_START_A[0]) + 10, py(NN_START_A[1]) + 4, "A", "note"))
    parts.append(_text(px(NN_START_B[0]) - 10, py(NN_START_B[1]) + 14, "B", "", "end"))
    parts.append(_text(20, 456, f"緑：始点A {NN_START_A} から w* へ", "note"))
    parts.append(_text(20, 480, f"青：始点B {NN_START_B} から −w* へ"))
    parts.append(_text(20, 504, f"濃い線：損失 {saddle:.3f}（u=0 か v=0 で出力が0）", "tick"))
    parts.append(_text(20, 528, f"学習率 {NN_ETA}、点は1回の更新ごと（12回分）", "tick"))

    # Panel 2: the loss on the segment s w*, s from -1 to 1.
    parts.append(_text(20, 576, "谷底を結ぶ線分での損失", "title"))
    sx = _scale(-1.0, 1.0, 64, 400)
    sy = _scale(0.0, 0.7, 748, 608)
    parts.append(f'<path d="M64 608V748H400" fill="none" stroke="{GRID}"/>')
    for value, label in ((-1.0, "−w*"), (0.0, "0"), (1.0, "w*")):
        parts.append(_text(sx(value), 768, label, "tick", "middle"))
    for value in (0.0, 0.3, 0.6):
        parts.append(_text(56, sy(value) + 5, f"{value:.1f}", "tick", "end"))
    profile = [(s / 50, nn_loss(s / 50 * wu, s / 50 * wv)) for s in range(-50, 51)]
    parts.append(
        f'<path d="M{sx(-1):.1f} {sy(bottom):.1f}L{sx(1):.1f} {sy(bottom):.1f}" '
        f'stroke="{UPDATE}" stroke-width="2" stroke-dasharray="6 5"/>'
    )
    parts.append(_polyline([(sx(s), sy(value)) for s, value in profile], LINE, 3))
    parts.append(f'<circle cx="{sx(0):.1f}" cy="{sy(saddle):.1f}" r="5" fill="{INK}"/>')
    parts.append(_text(sx(0) + 12, sy(saddle) + 5, f"中点 {saddle:.3f}"))
    parts.append(_text(20, 796, f"橙の破線：両端の損失 {bottom:.4f} を結ぶ弦", "note"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


# Large-scale stochastic ERM (content/concepts/stochastic-erm.md): logistic regression with
# an L2 penalty on 10,000 purchase records. The figure draws 200 minibatch gradients (32 records
# each) at the start point and at the minimiser; the article's code prints the same numbers.
ERM_N = 10_000
ERM_LAM = 0.01
ERM_BATCH = 32
ERM_REPS = 200


def _sigmoid(s: float) -> float:
    return 1 / (1 + math.exp(-s)) if s >= 0 else math.exp(s) / (1 + math.exp(s))


def erm_data() -> tuple[list[float], list[int]]:
    rng = random.Random(0)
    xs = [rng.gauss(0.0, 1.0) for _ in range(ERM_N)]
    ys = [int(rng.random() < 1 / (1 + math.exp(1.0 - 2.0 * x))) for x in xs]
    return xs, ys


def erm_gradient(
    w: Sequence[float], xs: Sequence[float], ys: Sequence[int], idx: Sequence[int]
) -> tuple[float, float]:
    g0 = g1 = 0.0
    for i in idx:
        e = _sigmoid(w[0] + w[1] * xs[i]) - ys[i]
        g0, g1 = g0 + e, g1 + e * xs[i]
    return g0 / len(idx) + ERM_LAM * w[0], g1 / len(idx) + ERM_LAM * w[1]


def erm_minimiser(xs: Sequence[float], ys: Sequence[int]) -> tuple[float, float]:
    """Ten full Newton steps from (0, 0) on the 2x2 problem, as in the article."""
    every = range(ERM_N)
    w = [0.0, 0.0]
    for _ in range(10):
        g, h = erm_gradient(w, xs, ys, every), [ERM_LAM, 0.0, ERM_LAM]
        for x in xs:
            p = _sigmoid(w[0] + w[1] * x)
            q = p * (1 - p) / ERM_N
            h = [h[0] + q, h[1] + q * x, h[2] + q * x * x]
        det = h[0] * h[2] - h[1] ** 2
        w = [w[0] - (h[2] * g[0] - h[1] * g[1]) / det, w[1] - (h[0] * g[1] - h[1] * g[0]) / det]
    return w[0], w[1]


def erm_minibatch_data() -> dict[str, object]:
    """Full gradient, 200 minibatch gradients, their RMS deviation and same-side count."""
    xs, ys = erm_data()
    out: dict[str, object] = {"minimiser": erm_minimiser(xs, ys)}
    for name, point in (("start", (0.0, 0.0)), ("minimum", out["minimiser"])):
        full = erm_gradient(point, xs, ys, range(ERM_N))  # type: ignore[arg-type]
        rng = random.Random(1)
        grads = [
            erm_gradient(point, xs, ys, rng.sample(range(ERM_N), ERM_BATCH))  # type: ignore[arg-type]
            for _ in range(ERM_REPS)
        ]
        rms = math.sqrt(sum((a - full[0]) ** 2 + (b - full[1]) ** 2 for a, b in grads) / ERM_REPS)
        same = sum(a * full[0] + b * full[1] > 0 for a, b in grads)
        out[name] = {"point": point, "full": full, "grads": grads, "rms": rms, "same": same}
    return out


def _signed(value: float, digits: int) -> str:
    return f"{value:.{digits}f}".replace("-", "−")


def _erm_minibatch_svg() -> str:
    data = erm_minibatch_data()
    start, minimum = data["start"], data["minimum"]
    w0, w1 = data["minimiser"]  # type: ignore[misc]
    parts = _open(
        "32件の勾配は、全件の勾配のまわりに散らばる",
        (
            "1万件のロジスティック回帰で、32件ずつ選んで作った勾配200本を、"
            "全件の勾配と同じ平面に描いた図です。"
            f"初期点 (0, 0) では全件の勾配が ({start['full'][0]:.3f}, "  # type: ignore[index]
            f"{_signed(start['full'][1], 3)}) で、"  # type: ignore[index]
            f"200本のうち{start['same']}本が同じ側にあり、ずれのRMSは"  # type: ignore[index]
            f"{start['rms']:.3f}です。"  # type: ignore[index]
            f"最小点 ({_signed(w0, 3)}, {w1:.3f}) では全件の勾配が0で、"
            f"32件の勾配の大きさのRMSは{minimum['rms']:.3f}です。"  # type: ignore[index]
        ),
        780,
    )
    low, high = -0.36, 0.54
    y_low, y_high = -0.64, 0.26
    size = 220.0
    left = 110.0
    px = _scale(low, high, left, left + size)
    for index, (key, label) in enumerate(
        (
            ("start", "① 初期点 w = (0, 0)"),
            ("minimum", f"② 最小点 w* = ({_signed(w0, 3)}, {w1:.3f})"),
        )
    ):
        group = data[key]
        top = 90 + index * 322
        py = _scale(y_low, y_high, top + size, top)
        parts.append(_text(20, top - 18, label))
        parts.append(
            f'<rect x="{left}" y="{top}" width="{size}" height="{size}" fill="#ffffff" '
            f'stroke="{GRID}"/>'
        )
        parts.append(
            f'<path d="M{left} {py(0):.1f}H{left + size}M{px(0):.1f} {top}V{top + size}" '
            f'stroke="{GRID}" stroke-width="1"/>'
        )
        for value in (-0.3, 0.0, 0.3):
            parts.append(_text(px(value), top + size + 20, _signed(value, 1), "tick", "middle"))
        for value in (-0.6, -0.3, 0.0):
            parts.append(_text(left - 8, py(value) + 5, _signed(value, 1), "tick", "end"))
        full = group["full"]  # type: ignore[index]
        if math.hypot(*full) > 1e-9:
            # Points on this line have zero inner product with the full gradient.
            ux, uy = -full[1], full[0]
            reach = 0.62 / math.hypot(ux, uy)
            a = (px(-ux * reach), py(-uy * reach))
            b = (px(ux * reach), py(uy * reach))
            parts.append(
                f'<clipPath id="erm-clip-{index}"><rect x="{left}" y="{top}" '
                f'width="{size}" height="{size}"/></clipPath>'
            )
            parts.append(
                f'<path d="M{a[0]:.1f} {a[1]:.1f}L{b[0]:.1f} {b[1]:.1f}" stroke="{MUTED}" '
                f'stroke-width="1.5" clip-path="url(#erm-clip-{index})"/>'
            )
        for g0, g1 in group["grads"]:  # type: ignore[index]
            assert low < g0 < high and y_low < g1 < y_high, (g0, g1)
            parts.append(
                f'<circle cx="{px(g0):.1f}" cy="{py(g1):.1f}" r="2.6" fill="{LINE}" '
                'fill-opacity="0.55"/>'
            )
        fx, fy = px(full[0]), py(full[1])
        if math.hypot(*full) > 1e-9:
            parts.append(
                f'<path d="M{px(0):.1f} {py(0):.1f}L{fx:.1f} {fy:.1f}" stroke="{UPDATE}" '
                'stroke-width="3"/>'
            )
        parts.append(
            f'<path d="M{fx:.1f} {fy - 8:.1f}L{fx + 8:.1f} {fy:.1f}L{fx:.1f} {fy + 8:.1f}'
            f'L{fx - 8:.1f} {fy:.1f}Z" fill="{UPDATE}" stroke="#ffffff" stroke-width="1.5"/>'
        )
        if key == "start":
            note = f"200本のうち{group['same']}本が灰の線の同じ側"  # type: ignore[index]
        else:
            note = f"全件の勾配は0、32件の勾配はRMS {group['rms']:.3f}"  # type: ignore[index]
        parts.append(_text(20, top + size + 46, note, "note"))
    parts.append(_text(20, 710, "青緑の点：32件で作った勾配（200回）"))
    parts.append(_text(20, 734, "橙のひし形：全件の勾配"))
    parts.append(_text(20, 760, "横は切片の勾配 g₀、縦は傾きの勾配 g₁", "tick"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


# Bilevel optimization (content/concepts/bilevel-optimization.md): a seller sets the price x,
# a buyer picks the quantity y that minimises 0.5 y^2 + x y - 4 y over y >= 0.
BILEVEL_X_MAX = 6.0
BILEVEL_ASSUMED_QUANTITY = 3.0  # the quantity at x = 1, wrongly held fixed


def _bilevel_response(x: float) -> float:
    """The buyer's unique best quantity: the gradient y + x - 4 = 0 clipped at y >= 0."""
    return max(0.0, 4.0 - x)


def _bilevel_data() -> dict[str, object]:
    xs = [i / 100 for i in range(int(BILEVEL_X_MAX * 100) + 1)]
    revenue = [x * _bilevel_response(x) for x in xs]
    best = max(range(len(xs)), key=lambda index: revenue[index])
    return {
        "xs": xs,
        "response": [_bilevel_response(x) for x in xs],
        "revenue": revenue,
        "assumed": [BILEVEL_ASSUMED_QUANTITY * x for x in xs],
        "best_x": xs[best],
        "best_y": _bilevel_response(xs[best]),
        "best_revenue": revenue[best],
        "assumed_at_max": BILEVEL_ASSUMED_QUANTITY * BILEVEL_X_MAX,
        "actual_at_max": revenue[-1],
    }


def _bilevel_axes(
    parts: list[str],
    left: float,
    right: float,
    top: float,
    bottom: float,
    x_ticks: Sequence[float],
    y_ticks: Sequence[float],
    px: Callable[[float], float],
    py: Callable[[float], float],
    x_label: str,
) -> None:
    parts.append(f'<path d="M{left} {top}V{bottom}H{right}" fill="none" stroke="{GRID}"/>')
    for value in x_ticks:
        parts.append(_text(px(value), bottom + 20, f"{value:g}", "tick", "middle"))
    for value in y_ticks:
        parts.append(_text(left - 8, py(value) + 5, f"{value:g}", "tick", "end"))
    parts.append(_text(right, bottom + 40, x_label, "tick", "end"))


def _bilevel_svg() -> str:
    data = _bilevel_data()
    xs: list[float] = data["xs"]  # type: ignore[assignment]
    best_x, best_y = data["best_x"], data["best_y"]
    best_revenue = data["best_revenue"]
    assumed_at_max, actual_at_max = data["assumed_at_max"], data["actual_at_max"]
    parts = _open(
        "価格に反応する買い手",
        (
            "「① 価格 x と買い手の購入量」では、購入量が価格 4 まで直線で 4 から 0 へ減り、"
            "4 以上では 0 です。「② 価格 x と売上」では、実際の売上が x=2 で最大の 4 になり、"
            "購入量が 3 のままと見なした売上 3x は x=6 で 18 まで増えますが、"
            "実際の x=6 の売上は 0 です。"
        ),
        584,
    )
    left, right = 64.0, 420.0
    px = _scale(0.0, BILEVEL_X_MAX, left, right)

    parts.append(_text(20, 60, "① 価格 x と買い手の購入量 y"))
    py1 = _scale(0.0, 4.0, 200, 84)
    _bilevel_axes(parts, left, right, 80, 200, (0, 2, 4, 6), (0, 2, 4), px, py1, "価格 x")
    parts.append(_polyline([(px(x), py1(_bilevel_response(x))) for x in xs], POINT, 3))
    parts.append(f'<circle cx="{px(best_x):.1f}" cy="{py1(best_y):.1f}" r="7" fill="{LINE}"/>')
    parts.append(_text(px(best_x) + 12, py1(best_y) - 8, f"x={best_x:g} で y={best_y:g}"))

    parts.append(_text(20, 296, "② 価格 x と売上 x·y"))
    py2 = _scale(0.0, 18.0, 480, 316)
    _bilevel_axes(parts, left, right, 312, 480, (0, 2, 4, 6), (0, 4, 18), px, py2, "価格 x")
    parts.append(
        _polyline([(px(x), py2(a)) for x, a in zip(xs, data["assumed"], strict=True)], UPDATE, 3)
    )
    parts.append(
        _polyline([(px(x), py2(r)) for x, r in zip(xs, data["revenue"], strict=True)], LINE, 3)
    )
    parts.append(
        f'<circle cx="{px(best_x):.1f}" cy="{py2(best_revenue):.1f}" r="7" fill="{LINE}"/>'
    )
    parts.append(_text(px(best_x) + 12, py2(best_revenue) + 22, f"最大 {best_revenue:g}"))
    parts.append(
        _text(px(BILEVEL_X_MAX) - 6, py2(assumed_at_max) + 22, f"{assumed_at_max:g}", "", "end")
    )
    parts.append(
        _text(px(BILEVEL_X_MAX) - 6, py2(actual_at_max) - 10, f"{actual_at_max:g}", "", "end")
    )
    parts.append(f'<rect x="20" y="526" width="20" height="12" fill="{UPDATE}"/>')
    parts.append(_text(48, 537, "購入量が 3 のままと見なした売上 3x"))
    parts.append(f'<rect x="20" y="550" width="20" height="12" fill="{LINE}"/>')
    parts.append(_text(48, 561, "買い手が反応した実際の売上"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


# Shape-dependent domain (content/concepts/shape-dependent-domain.md): a cooling fin of length L
# with -u'' + u = 0 on (0, L), u(0) = 1, u'(L) = 0, so u(x) = cosh(L - x) / cosh(L) and the
# heat leaving the surface is tanh(L). The design minimizes J(L) = 0.25 L - tanh(L).
FIN_COST = 0.25
FIN_ELEMENTS = 4
FIN_LENGTHS = (1.0, math.acosh(2.0), math.acosh(4.0))  # short, optimal, tip-slice-only answer


def fin_temperature(length: float, x: float) -> float:
    return math.cosh(length - x) / math.cosh(length)


def fin_objective(length: float) -> float:
    return FIN_COST * length - math.tanh(length)


def _fin_length_svg() -> str:
    colors = (POINT, UPDATE, LINE)
    px = _scale(0.0, 2.2, 64, 416)
    py = _scale(0.0, 1.0, 250, 86)
    parts = _open(
        "フィンの長さと温度・目的",
        (
            "放熱フィンの長さ L を 1.0、1.317、2.063 にしたときの温度分布と、"
            "長さごとの目的 J(L)=0.25L−tanh L です。先端の温度は 0.648、0.500、0.250 で、"
            "J は L=1.317 で最小の −0.537、L=2.063 では −0.452 です。"
            "点は4要素のメッシュの節点の位置で、長さとともに動きます。"
        ),
        610,
    )
    parts.append(_text(20, 64, "長さごとの温度 u(x)", "", "start"))
    parts.append(f'<path d="M64 86V250H416" fill="none" stroke="{GRID}"/>')
    for value in (0.0, 0.5, 1.0, 1.5, 2.0):
        parts.append(_text(px(value), 270, f"{value:g}", "tick", "middle"))
    for value in (0.0, 0.5, 1.0):
        parts.append(_text(56, py(value) + 5, f"{value:g}", "tick", "end"))
    parts.append(_text(416, 240, "位置 x", "tick", "end"))
    for length, color in zip(FIN_LENGTHS, colors, strict=True):
        curve = [
            (px(length * step / 80), py(fin_temperature(length, length * step / 80)))
            for step in range(81)
        ]
        parts.append(_polyline(curve, color, 3))
        for node in range(FIN_ELEMENTS + 1):
            x = length * node / FIN_ELEMENTS
            parts.append(
                f'<circle cx="{px(x):.2f}" cy="{py(fin_temperature(length, x)):.2f}" '
                f'r="4.5" fill="{color}"/>'
            )
    for row, (length, color) in enumerate(zip(FIN_LENGTHS, colors, strict=True)):
        y = 300 + 24 * row
        parts.append(
            f'<path d="M20 {y - 5}H44" stroke="{color}" stroke-width="4" stroke-linecap="round"/>'
        )
        tip = fin_temperature(length, length)
        parts.append(_text(52, y, f"L={length:.3f}：先端 {tip:.3f}、間隔 {length / 4:.3f}"))
    jx = _scale(0.2, 3.0, 64, 416)
    jy = _scale(-0.6, -0.1, 560, 404)
    parts.append(_text(20, 382, "長さ L と目的 J(L)"))
    parts.append(f'<path d="M64 404V560H416" fill="none" stroke="{GRID}"/>')
    for value in (0.5, 1.0, 1.5, 2.0, 2.5, 3.0):
        parts.append(_text(jx(value), 580, f"{value:g}", "tick", "middle"))
    for value in (-0.5, -0.3, -0.1):
        parts.append(_text(56, jy(value) + 5, f"{value:g}".replace("-", "−"), "tick", "end"))
    parts.append(_text(416, 550, "長さ L", "tick", "end"))
    steps = 140
    parts.append(
        _polyline(
            [
                (jx(0.2 + 2.8 * k / steps), jy(fin_objective(0.2 + 2.8 * k / steps)))
                for k in range(steps + 1)
            ],
            INK,
            2,
        )
    )
    for length, color in zip(FIN_LENGTHS, colors, strict=True):
        parts.append(
            f'<circle cx="{jx(length):.2f}" cy="{jy(fin_objective(length)):.2f}" '
            f'r="6.5" fill="{color}"/>'
        )
    best = FIN_LENGTHS[1]
    parts.append(
        _text(
            416,
            430,
            f"最小 J={fin_objective(best):.3f}（L={best:.3f}）".replace("-", "−"),
            "note",
            "end",
        )
    )
    parts.append(_text(20, 604, "点：4要素のメッシュの節点。長さとともに動く", "tick"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


# Nonsmooth convex composite (content/concepts/nonsmooth-convex-composite.md): two sensor
# stations A and B with two channels each. min 1/2 |A x - b|^2 + lam (|x_A| + |x_B|), solved by
# proximal gradient from x = 0 with a fixed step.
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


# Deterministic but discontinuous simulation (content/concepts/discontinuous-simulation.md):
# a dryer dial x in [0, 1] whose simulator switches operating regime at x = 0.55.
DRYER_CLIFF = 0.55


def dryer_value(x: float) -> float:
    if x < DRYER_CLIFF:
        return 0.40 + 2.0 * (x - 0.25) ** 2
    return 0.20 + 2.0 * (x - 0.80) ** 2


def dryer_compass(x0: float, step0: float, tol: float = 1e-4) -> tuple[float, float, int]:
    """Compass search on [0, 1]: poll +step then -step, take the first improvement, else halve."""
    x, fx, step, evaluations = x0, dryer_value(x0), step0, 1
    while step > tol:
        moved = False
        for candidate in (x + step, x - step):
            if 0.0 <= candidate <= 1.0:
                value = dryer_value(candidate)
                evaluations += 1
                if value < fx:
                    x, fx, moved = candidate, value, True
                    break
        if not moved:
            step /= 2
    return x, fx, evaluations


def _discontinuous_dryer_svg() -> str:
    start = 0.10
    cliff_left = 0.40 + 2.0 * (DRYER_CLIFF - 0.25) ** 2  # limit of the low-dial piece at the cliff
    cliff_right = dryer_value(DRYER_CLIFF)
    px = _scale(0.0, 1.0, 56, 416)
    py = _scale(0.65, 0.10, 52, 300)
    parts = _open(
        "運転ダイヤルと1バッチの総コスト",
        (
            f"ダイヤル x が {DRYER_CLIFF:g} で運転の切り替わる乾燥機の総コスト F。"
            f"x が {DRYER_CLIFF:g} 未満では底が (0.25, F = 0.4) の谷、{DRYER_CLIFF:g} 以上では"
            f"底が (0.8, F = 0.2) の谷。段差で F は {cliff_left:g} から"
            f"{cliff_right:g} に飛びます。"
            f"出発 {start:g} で F = {dryer_value(start):g}。"
        ),
        486,
    )
    parts.append(f'<path d="M56 52V300H416" fill="none" stroke="{GRID}" stroke-width="1.5"/>')
    for value in (0.2, 0.4, 0.6):
        parts.append(
            f'<path d="M56 {py(value):.1f}H416" stroke="{GRID}" stroke-width="0.6" opacity="0.6"/>'
        )
        parts.append(_text(48, py(value) + 5, f"{value:g}", "tick", "end"))
    for value in (0, 0.5, 1):
        parts.append(_text(px(value), 320, f"{value:g}", "tick", "middle"))
    parts.append(_text(416, 344, "ダイヤル x", "tick", "end"))
    parts.append(_text(62, 70, "総コスト F", "tick"))
    for lo, hi in ((0.0, DRYER_CLIFF - 1e-9), (DRYER_CLIFF, 1.0)):
        xs = [lo + (hi - lo) * i / 100 for i in range(101)]
        parts.append(_polyline([(px(x), py(dryer_value(x))) for x in xs], LINE, 3))
    cx = px(DRYER_CLIFF)
    parts.append(
        f'<path d="M{cx:.1f} 52V300" stroke="{GRID}" stroke-width="1.2" stroke-dasharray="4 4"/>'
    )
    parts.append(
        f'<path d="M{cx:.1f} {py(cliff_left):.1f}V{py(cliff_right):.1f}" '
        f'stroke="{UPDATE}" stroke-width="3"/>'
    )
    parts.append(
        f'<circle cx="{cx:.1f}" cy="{py(cliff_left):.1f}" r="6" fill="#f7f8f3" '
        f'stroke="{LINE}" stroke-width="2.5"/>'
    )
    parts.append(f'<circle cx="{cx:.1f}" cy="{py(cliff_right):.1f}" r="6" fill="{LINE}"/>')
    jump = round(cliff_right - cliff_left, 6)
    parts.append(
        _text(
            cx + 10, py((cliff_left + cliff_right) / 2) + 5, f"段差 {jump:g}".replace("-", "−"), ""
        )
    )
    for first in (start + 0.4, start + 0.5):
        parts.append(
            f'<rect x="{px(first) - 6:.1f}" y="{py(dryer_value(first)) - 6:.1f}" width="12" '
            f'height="12" fill="#f7f8f3" stroke="{POINT}" stroke-width="2.5"/>'
        )
    parts.append(_text(px(0.5) - 10, py(dryer_value(0.5)) - 12, "0.50", "tick", "end"))
    parts.append(_text(px(0.6) + 10, py(dryer_value(0.6)) - 10, "0.60", "tick"))
    for bottom in (0.25, 0.80):
        parts.append(
            f'<circle cx="{px(bottom):.1f}" cy="{py(dryer_value(bottom)):.1f}" r="6.5" '
            f'fill="{POINT}"/>'
        )
        parts.append(
            _text(px(bottom), py(dryer_value(bottom)) + 30, f"{bottom:.2f}", "tick", "middle")
        )
    parts.append(
        f'<circle cx="{px(start):.1f}" cy="{py(dryer_value(start)):.1f}" r="7" fill="{UPDATE}"/>'
    )
    parts.append(_text(px(start), py(dryer_value(start)) - 14, "出発", "", "middle"))
    parts.append(
        _text(20, 372, f"段差：F(0.55) = {cliff_right:g}、直前の極限は {cliff_left:g}", "note")
    )
    parts.append(_text(20, 396, f"橙の丸：出発 {start:.2f}、F = {dryer_value(start):g}"))
    parts.append(_text(20, 420, f"紺の丸：0.55 未満の谷の底 0.25、F = {dryer_value(0.25):g}"))
    parts.append(_text(20, 444, f"紺の丸：0.55 以上の谷の底 0.80、F = {dryer_value(0.80):g}"))
    parts.append(_text(20, 468, "白い四角：最初に試す 0.50 と 0.60"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


# Noisy black box (content/concepts/noisy-black-box.md): an oven temperature scored with noise.
# The mean score is 2(x - 0.6)^2 and each bake adds N(0, 0.2^2) noise. 60 bakes are spent either
# on 60 temperatures once each or on 12 temperatures five times each.
OVEN_SIGMA = 0.2
OVEN_BUDGET = 60
OVEN_FIGURE_SEED = 0


def oven_true_score(x: float) -> float:
    return 2.0 * (x - 0.6) ** 2


def oven_bake(x: float, rng: random.Random) -> float:
    return oven_true_score(x) + rng.gauss(0.0, OVEN_SIGMA)


def oven_temperatures(k: int) -> list[float]:
    return [(i + 0.5) / k for i in range(k)]


def oven_reversal(n: int, gap: float, sigma: float = OVEN_SIGMA) -> float:
    """Probability that means of n bakes each order two temperatures the wrong way round."""
    z = gap / (sigma * math.sqrt(2.0 / n))
    return 0.5 * (1.0 + math.erf(-z / math.sqrt(2.0)))


def oven_spread(
    k: int, budget: int = OVEN_BUDGET, reps: int = 2000, seed: int = 1
) -> tuple[float, float]:
    """Mean true score of the chosen temperature, and mean (reported mean - true score)."""
    rng = random.Random(seed)
    n = budget // k
    xs = oven_temperatures(k)
    chosen, optimism = [], []
    for _ in range(reps):
        means = [sum(oven_bake(x, rng) for _ in range(n)) / n for x in xs]
        best = min(range(k), key=means.__getitem__)
        chosen.append(oven_true_score(xs[best]))
        optimism.append(means[best] - oven_true_score(xs[best]))
    return sum(chosen) / reps, sum(optimism) / reps


def oven_figure_data(seed: int = OVEN_FIGURE_SEED) -> list[dict[str, object]]:
    rng = random.Random(seed)
    panels = []
    for k in (60, 12):
        n = OVEN_BUDGET // k
        xs = oven_temperatures(k)
        observed = [[oven_bake(x, rng) for _ in range(n)] for x in xs]
        means = [sum(values) / n for values in observed]
        best = min(range(k), key=means.__getitem__)
        panels.append(
            {
                "k": k,
                "n": n,
                "xs": xs,
                "observed": observed,
                "means": means,
                "best": best,
                "true_at_best": oven_true_score(xs[best]),
            }
        )
    return panels


def _signed_3dp(value: float) -> str:
    return f"{value:.3f}".replace("-", "−")


def _noisy_oven_svg() -> str:
    panels = oven_figure_data()
    first, second = panels
    parts = _open(
        "同じ60回の焼き方",
        (
            "焼成温度を決めるために60回焼く2つの配分です。"
            f"60温度を1回ずつ測ると、最良の観測は{_signed_3dp(first['means'][first['best']])}"  # type: ignore[index]
            f"で、その温度の真の点数は{first['true_at_best']:.3f}です。"
            f"12温度を5回ずつ測ると、平均が最小の温度の平均は"
            f"{_signed_3dp(second['means'][second['best']])}"  # type: ignore[index]
            f"で、真の点数は{second['true_at_best']:.3f}です（乱数種{OVEN_FIGURE_SEED}の1回分）。"
        ),
        618,
    )
    px = _scale(0.0, 1.0, 56, 420)
    low, high = -0.8, 1.2
    for index, panel in enumerate(panels):
        top = 74 + index * 262
        height = 150
        py = _scale(high, low, top, top + height)
        label = "① 60温度を1回ずつ" if panel["k"] == 60 else "② 12温度を5回ずつ"
        parts.append(_text(20, top - 12, label))
        parts.append(
            f'<path d="M56 {top}V{top + height}H420" fill="none" stroke="{GRID}" '
            'stroke-width="1.5"/>'
        )
        for tick in (1.0, 0.0, -0.5):
            parts.append(_text(48, py(tick) + 5, f"{tick:g}".replace("-", "−"), "tick", "end"))
            parts.append(
                f'<path d="M52 {py(tick):.1f}H420" stroke="{GRID}" stroke-width="0.8" '
                'opacity="0.6"/>'
            )
        for tick in (0.0, 0.6, 1.0):
            parts.append(_text(px(tick), top + height + 22, f"{tick:g}", "tick", "middle"))
        curve = [(px(i / 100), py(oven_true_score(i / 100))) for i in range(101)]
        parts.append(_polyline(curve, LINE, 2.5))
        n = panel["n"]
        for x, values, mean in zip(panel["xs"], panel["observed"], panel["means"], strict=True):  # type: ignore[arg-type]
            for value in values:
                parts.append(
                    f'<circle cx="{px(x):.2f}" cy="{py(value):.2f}" r="3" fill="{POINT}" '
                    'opacity="0.55"/>'
                )
            if n > 1:
                parts.append(
                    f'<rect x="{px(x) - 4.5:.2f}" y="{py(mean) - 4.5:.2f}" width="9" height="9" '
                    f'fill="{INK}"/>'
                )
        best = panel["best"]
        bx, bm = panel["xs"][best], panel["means"][best]  # type: ignore[index]
        parts.append(
            f'<circle cx="{px(bx):.2f}" cy="{py(bm):.2f}" r="10" fill="none" stroke="{UPDATE}" '
            'stroke-width="3"/>'
        )
        what = "最良の観測" if n == 1 else "最良の平均"
        parts.append(
            _text(
                20,
                top + height + 48,
                f"{what} {_signed_3dp(bm)}、真の点数 {panel['true_at_best']:.3f}",
                "note",
            )
        )
    parts.append(_text(20, 566, "横軸：焼成温度 x　縦軸：点数（小さいほど良い）"))
    parts.append(_text(20, 590, "緑の線：真の点数　青の点：1回の焼成　黒の四角：平均", "note"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


# Nonconvex QP (content/concepts/nonconvex-qp-qcqp.md): two knobs x1, x2 in [-1, 1] and the loss
# f(x) = x1^2 + x2^2 - 3 x1 x2 + 0.5 (x1 + x2). The Hessian 2Q = [[2, -3], [-3, 2]] has eigenvalues
# 5 and -1, so f is not convex; the box has two local minima, (-1, -1) and (1, 1).
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


# MINLP (content/concepts/mixed-integer-nonlinear-program.md): n machines, each run at load q.
MINLP_FIXED = 6  # fixed cost of one machine
MINLP_PRICE = 8  # profit per unit of output
MINLP_Q_MAX = 2.4  # rated load of one machine
MINLP_MARKET = 10  # the market takes at most this much in total
MINLP_MACHINES = (1, 2, 3, 4, 5, 6)


def minlp_value(n: float) -> float:
    """Best cost minus profit for n machines, after optimising the total output x = n q.

    The inner problem min_x  x^2/n - 8x  on 0 <= x <= min(10, 2.4 n)  has its unconstrained
    minimiser 4n above both caps, so x sits on the smaller cap. The result is convex in n.
    """
    x = min(MINLP_MARKET, MINLP_Q_MAX * n)
    return MINLP_FIXED * n + x * x / n - MINLP_PRICE * x


def minlp_interval_min(lower: float, upper: float) -> tuple[float, float]:
    """Minimise the convex minlp_value over [lower, upper] by ternary search."""
    for _ in range(200):
        a = lower + (upper - lower) / 3
        b = upper - (upper - lower) / 3
        if minlp_value(a) < minlp_value(b):
            upper = b
        else:
            lower = a
    n = (lower + upper) / 2
    return n, minlp_value(n)


def _minlp_panel(top: float, branched: bool) -> list[str]:
    """One panel: the relaxed value over n, or the same curve with n between 4 and 5 removed."""
    px = _scale(3.0, 6.2, 56, 416)
    py = _scale(-34.0, -21.0, top + 140, top)
    parts = [f'<path d="M56 {top}V{top + 140}H416" fill="none" stroke="{GRID}"/>']
    for n in (3, 4, 5, 6):
        parts.append(_text(px(n), top + 160, f"{n}", "tick", "middle"))
    for value in (-22, -26, -30):
        parts.append(_text(48, py(value) + 5, f"{value}".replace("-", "−"), "tick", "end"))
    steps = 64
    grid = [3.0 + 3.2 * k / steps for k in range(steps + 1)]
    if branched:
        removed = [px(4), px(5)]
        parts.append(
            f'<rect x="{removed[0]:.1f}" y="{top}" width="{removed[1] - removed[0]:.1f}" '
            f'height="140" fill="{GRID}" fill-opacity="0.3"/>'
        )
        parts.append(_text((removed[0] + removed[1]) / 2, top + 20, "除く", "tick", "middle"))
        for low, high in ((3.0, 4.0), (5.0, 6.2)):
            pts = [(px(n), py(minlp_value(n))) for n in grid if low <= n <= high]
            pts = [(px(low), py(minlp_value(low))), *pts, (px(high), py(minlp_value(high)))]
            parts.append(_polyline(pts, LINE, 3))
    else:
        parts.append(_polyline([(px(n), py(minlp_value(n))) for n in grid], LINE, 3))
        relaxed_n, relaxed_value = minlp_interval_min(1.0, 6.0)
        parts.append(
            f'<circle cx="{px(relaxed_n):.1f}" cy="{py(relaxed_value):.1f}" r="7" '
            f'fill="{UPDATE}" stroke="#ffffff" stroke-width="2"/>'
        )
    for n in (3, 4, 5, 6):
        parts.append(
            f'<circle cx="{px(n):.1f}" cy="{py(minlp_value(n)):.1f}" r="5" fill="{POINT}"/>'
        )
    if branched:
        parts.append(
            f'<circle cx="{px(5):.1f}" cy="{py(minlp_value(5)):.1f}" r="10" fill="none" '
            f'stroke="{UPDATE}" stroke-width="3"/>'
        )
    return parts


def _minlp_svg() -> str:
    relaxed_n, relaxed_value = minlp_interval_min(1.0, 6.0)
    rounded = round(relaxed_n)
    left_n, left_value = minlp_interval_min(1.0, 4.0)
    right_n, right_value = minlp_interval_min(5.0, 6.0)
    parts = _open(
        "台数を実数にした緩和と、分枝",
        (
            f"機械を何台使うかを決める例です。台数を実数にした緩和の最小は n={relaxed_n:.2f}、"
            f"値{relaxed_value:.1f}で、整数ではありません。"
            f"丸めた{rounded}台の値は{minlp_value(rounded):.2f}です。"
            f"4と5の間を除いて分けると、n={left_n:.0f}で{left_value:.2f}、"
            f"n={right_n:.0f}で{right_value:.1f}となり、n={right_n:.0f}が最良です。"
        ),
        556,
    )
    parts.append(_text(20, 64, "① 台数 n を実数にした緩和"))
    parts.append(_text(420, 64, f"最小 {relaxed_value:.1f}".replace("-", "−"), "note", "end"))
    parts += _minlp_panel(74, False)
    parts.append(
        _text(20, 256, f"緩和の最小：n={relaxed_n:.2f}、値 {relaxed_value:.1f}".replace("-", "−"))
    )
    parts.append(
        _text(
            20,
            278,
            f"丸めた n={rounded}：値 {minlp_value(rounded):.2f}".replace("-", "−"),
            "note",
        )
    )
    parts.append(_text(20, 312, "② 4と5の間を除いて分ける"))
    parts.append(_text(420, 312, f"最良 {right_value:.1f}".replace("-", "−"), "note", "end"))
    parts += _minlp_panel(322, True)
    parts.append(
        _text(20, 504, f"n≤4 の節点：n={left_n:.0f}、値 {left_value:.2f}".replace("-", "−"))
    )
    parts.append(
        _text(
            20,
            526,
            f"n≥5 の節点：n={right_n:.0f}、値 {right_value:.1f}".replace("-", "−"),
            "note",
        )
    )
    parts.append("</svg>")
    return "".join(parts) + "\n"


# Shortest path (content/concepts/shortest-path.md): a van from the depot S to the customer T.
PATH_NODES = ("S", "A", "B", "C", "T")  # arcs only go forward in this order
# (from, to) -> minutes
PATH_ARCS = {
    ("S", "A"): 2,
    ("S", "B"): 4,
    ("S", "T"): 12,
    ("A", "B"): 5,
    ("A", "T"): 6,
    ("B", "C"): 1,
    ("C", "T"): 2,
}


def path_routes(node: str = "S", seen: tuple[str, ...] = ("S",)) -> list[tuple[str, ...]]:
    """Every route from S to T that visits no node twice."""
    routes = [seen] if node == "T" else []
    for tail, head in PATH_ARCS:
        if tail == node and head not in seen:
            routes += path_routes(head, (*seen, head))
    return routes


def path_total(route: Sequence[str]) -> int:
    return sum(PATH_ARCS[edge] for edge in zip(route, route[1:], strict=False))


def path_distances() -> tuple[dict[str, int], tuple[str, ...]]:
    """Shortest time from S to each node, and the shortest route to T (acyclic: one pass)."""
    dist = {"S": 0}
    pred: dict[str, str] = {}
    for node in PATH_NODES[1:]:
        dist[node], pred[node] = min(
            (dist[tail] + weight, tail)
            for (tail, head), weight in PATH_ARCS.items()
            if head == node
        )
    route = ["T"]
    while route[-1] != "S":
        route.append(pred[route[-1]])
    return dist, tuple(reversed(route))


def path_rules() -> list[tuple[str, tuple[str, ...]]]:
    """Three ways to pick a route: fewest arcs, cheapest next arc at every node, least total."""
    cheapest_first = ("S",)
    while cheapest_first[-1] != "T":
        here = cheapest_first[-1]
        cheapest_first += (
            min(
                (head for tail, head in PATH_ARCS if tail == here), key=lambda h: PATH_ARCS[here, h]
            ),
        )
    routes = path_routes()
    return [
        ("道の数が最少", min(routes, key=lambda r: (len(r), path_total(r)))),
        ("次の道が最安", cheapest_first),
        ("合計が最小", min(routes, key=path_total)),
    ]


def _path_svg() -> str:
    dist, best = path_distances()
    rules = path_rules()
    assert rules[2][1] == best
    parts = _open(
        f"最短の{dist['T']}分は、道が{len(best) - 1}本の経路",
        (
            "拠点Sから客先Tへ向かう、一方通行の7本の道の図です。"
            "辺の数字は所要時間（分）で、各点の d はSからの最短時間です。"
            + "".join(
                f"{name}では{'→'.join(route)}で{path_total(route)}分、"
                for name, route in rules[:-1]
            )
            + f"合計が最小の{'→'.join(best)}は{dist['T']}分です。"
        ),
        520,
    )
    at = {"S": (44, 190), "A": (150, 130), "B": (150, 250), "C": (290, 250), "T": (396, 190)}
    radius = 19
    on_best = set(zip(best, best[1:], strict=False))
    parts.append(
        "<defs>"
        '<marker id="path-head" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="4" '
        f'markerHeight="4" orient="auto"><path d="M0 0L10 5L0 10z" fill="{UPDATE}"/></marker>'
        '<marker id="path-head-quiet" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" '
        f'markerHeight="6" orient="auto"><path d="M0 0L10 5L0 10z" fill="{GRID}"/></marker>'
        "</defs>"
    )
    # weight label anchor (x, y, text-anchor), placed beside each arc
    label = {
        ("S", "A"): (86, 152, "end"),
        ("S", "B"): (86, 238, "end"),
        ("S", "T"): (220, 66, "middle"),
        ("A", "B"): (162, 196, "start"),
        ("A", "T"): (273, 148, "middle"),
        ("B", "C"): (220, 238, "middle"),
        ("C", "T"): (356, 246, "start"),
    }
    for (tail, head), weight in PATH_ARCS.items():
        (x1, y1), (x2, y2) = at[tail], at[head]
        chosen = (tail, head) in on_best
        color, width = (UPDATE, 5) if chosen else (GRID, 2)
        marker = "path-head" if chosen else "path-head-quiet"
        if (tail, head) == ("S", "T"):  # the direct road bends over the others
            ctrl = (220.0, -20.0)
            a = math.hypot(ctrl[0] - x1, ctrl[1] - y1)
            b = math.hypot(x2 - ctrl[0], y2 - ctrl[1])
            sx, sy = x1 + (ctrl[0] - x1) / a * radius, y1 + (ctrl[1] - y1) / a * radius
            ex = x2 - (x2 - ctrl[0]) / b * (radius + 4)
            ey = y2 - (y2 - ctrl[1]) / b * (radius + 4)
            shape = f"M{sx:.1f} {sy:.1f}Q{ctrl[0]:.1f} {ctrl[1]:.1f} {ex:.1f} {ey:.1f}"
        else:
            length = math.hypot(x2 - x1, y2 - y1)
            dx, dy = (x2 - x1) / length, (y2 - y1) / length
            shape = (
                f"M{x1 + dx * radius:.1f} {y1 + dy * radius:.1f}"
                f"L{x2 - dx * (radius + 4):.1f} {y2 - dy * (radius + 4):.1f}"
            )
        parts.append(
            f'<path d="{shape}" fill="none" stroke="{color}" stroke-width="{width}" '
            f'stroke-linecap="round" marker-end="url(#{marker})"/>'
        )
        lx, ly, anchor = label[tail, head]
        parts.append(_text(lx, ly, str(weight), "", anchor))
    below = {"S": (44, 226), "A": (150, 170), "B": (150, 286), "C": (290, 286), "T": (396, 226)}
    for name, (x, y) in at.items():
        stroke = UPDATE if name in best else POINT
        parts.append(
            f'<circle cx="{x}" cy="{y}" r="{radius}" fill="#ffffff" stroke="{stroke}" '
            'stroke-width="2"/>'
        )
        parts.append(_text(x, y + 6, name, "", "middle"))
        parts.append(_text(below[name][0], below[name][1], f"d={dist[name]}", "tick", "middle"))
    parts.append(_text(20, 322, "辺の数字：所要時間（分）　d：Sからの最短時間", "tick"))
    for index, (name, route) in enumerate(rules):
        top = 358 + index * 56
        won = route == best
        style = f' style="fill:{UPDATE}"' if won else ""
        parts.append(_text(20, top, name))
        parts.append(
            f'<text x="420" y="{top}" text-anchor="end"{style}>{path_total(route)}分</text>'
        )
        parts.append(_text(20, top + 22, f"{'→'.join(route)}（道{len(route) - 1}本）", "tick"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


# Linear complementarity problem (content/concepts/complementarity-problem.md): a plate on two
# floor points. w = q + M z, z >= 0, w >= 0, z_i w_i = 0 for each of the two contact points.
LCP_M = ((Fraction(2), Fraction(1)), (Fraction(1), Fraction(2)))
LCP_Q = (Fraction(-1), Fraction(-3, 2))


def _lcp_solve_set(
    matrix: Sequence[Sequence[Fraction]], q: Sequence[Fraction], active: Sequence[int]
) -> tuple[list[Fraction], list[Fraction]]:
    """Exact (z, w) for one complementary choice: w_i = 0 on `active`, z_i = 0 elsewhere."""
    z = [Fraction(0), Fraction(0)]
    if len(active) == 1:
        i = active[0]
        z[i] = -q[i] / matrix[i][i]
    elif len(active) == 2:
        det = matrix[0][0] * matrix[1][1] - matrix[0][1] * matrix[1][0]
        z[0] = (-q[0] * matrix[1][1] + q[1] * matrix[0][1]) / det
        z[1] = (-q[1] * matrix[0][0] + q[0] * matrix[1][0]) / det
    w = [q[i] + sum(matrix[i][j] * z[j] for j in range(2)) for i in range(2)]
    return z, w


def lcp_contact_data() -> list[dict[str, object]]:
    """The four complementary active sets of the contact example and whether each is a solution."""
    rows: list[dict[str, object]] = []
    for active in ((), (0,), (1,), (0, 1)):
        z, w = _lcp_solve_set(LCP_M, LCP_Q, active)
        rows.append({"active": active, "z": z, "w": w, "ok": min(z + w) >= 0})
    return rows


def _lcp_number(value: Fraction) -> str:
    if value.denominator == 1:
        return str(value.numerator)
    return f"{float(value):.3f}".rstrip("0")


def _lcp_contact_svg() -> str:
    rows = lcp_contact_data()
    lower, upper = (0.0, 0.0), (0.65, 1.05)  # z1 and z2 range of the plot window
    left, right, top, bottom = 62, 416, 58, 340
    sx = _scale(lower[0], upper[0], left, right)
    sy = _scale(lower[1], upper[1], bottom, top)
    q1, q2 = float(LCP_Q[0]), float(LCP_Q[1])
    # w1 = q1 + 2 z1 + z2 = 0 and w2 = q2 + z1 + 2 z2 = 0 as lines z2 = f(z1).
    line1 = lambda z1: -(q1 + float(LCP_M[0][0]) * z1) / float(LCP_M[0][1])  # noqa: E731
    line2 = lambda z1: -(q2 + float(LCP_M[1][0]) * z1) / float(LCP_M[1][1])  # noqa: E731
    corner = rows[3]["z"]
    cx, cy = float(corner[0]), float(corner[1])  # type: ignore[index]
    parts = _open(
        "4つの活性集合の判定",
        (
            "二つの接触点の例で、各点が接触しているかどうかの4通りを z1 と z2 の平面に描きます。"
            "どちらの接触点も接触している候補だけが z も w も非負で、解です。"
        ),
        488,
    )
    shade = [
        (lower[0], upper[1]),
        (lower[0], line1(0.0)),
        (cx, cy),
        (upper[0], line2(upper[0])),
        (upper[0], upper[1]),
    ]
    polygon = " ".join(f"{sx(x):.1f},{sy(y):.1f}" for x, y in shade)
    parts.append(f'<polygon points="{polygon}" fill="{RING}" fill-opacity="0.45"/>')
    parts.append(
        f'<path d="M{left} {top}V{bottom}H{right}" fill="none" stroke="{INK}" stroke-width="1.5"/>'
    )
    for value in (0.0, 0.5):
        parts.append(_text(sx(value), bottom + 20, f"{value:g}", "tick", "middle"))
    for value in (0.0, 0.5, 1.0):
        parts.append(_text(left - 8, sy(value) + 5, f"{value:g}", "tick", "end"))
    parts.append(_text(right, bottom + 40, "z₁（点Aの接触力）", "", "end"))
    parts.append(_text(left - 8, top - 8, "z₂（点B）", "", "start"))
    parts.append(_polyline([(sx(0.0), sy(line1(0.0))), (sx(0.5), sy(line1(0.5)))], LINE, 2.5))
    parts.append(
        _polyline([(sx(0.0), sy(line2(0.0))), (sx(upper[0]), sy(line2(upper[0])))], LINE, 2.5)
    )
    parts.append(_text(sx(0.3) - 12, sy(line1(0.3)) + 5, "w₁=0", "note", "end"))
    parts.append(_text(sx(0.58), sy(line2(0.58)) + 24, "w₂=0", "note", "middle"))
    names = {(): "接触なし", (0,): "Aだけ", (1,): "Bだけ", (0, 1): "AとB"}
    for row in rows:
        z = row["z"]
        ok = bool(row["ok"])
        px_, py_ = sx(float(z[0])), sy(float(z[1]))  # type: ignore[index]
        color = UPDATE if ok else POINT
        if ok:
            parts.append(f'<circle cx="{px_:.1f}" cy="{py_:.1f}" r="7" fill="{color}"/>')
        else:
            parts.append(
                f'<circle cx="{px_:.1f}" cy="{py_:.1f}" r="7" fill="#ffffff" '
                f'stroke="{color}" stroke-width="2"/>'
            )
        mark = "解" if ok else "w<0"
        dx = 14 if row["active"] != (0,) else -12
        anchor = "start" if row["active"] != (0,) else "end"
        dy = -14 if row["active"] != () else -12
        parts.append(
            _text(px_ + dx, py_ + dy, f"{names[row['active']]}（{mark}）", "", anchor)  # type: ignore[index]
        )
    parts.append(_text(20, 424, "橙の点：z≧0 かつ w≧0 を満たす候補（解）"))
    parts.append(_text(20, 448, "薄緑：w₁≧0 かつ w₂≧0 の領域", "note"))
    parts.append(_text(20, 472, "白抜き：w に負の成分があり、解ではない", "note"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


# Large smooth minimisation (content/concepts/high-dimensional-smooth-unconstrained.md):
# deblurring a 1000-point signal with an edge-preserving smooth penalty. Gradient costs O(n log n)
# (FFT), the Hessian is dense. numpy and scipy are imported inside the functions so the other
# figures keep generating without the optional "scenes" extra.
PA007_N = 1000
PA007_LAMBDA = 0.05
PA007_DELTA = 0.05
PA007_TOLERANCE = 1e-6
PA007_SEED = 0
PA007_WINDOW = (180, 240)  # the first step of the signal sits at position 200


@functools.cache
def _pa007_problem() -> dict[str, Any]:
    import numpy as np

    n = PA007_N
    rng = np.random.default_rng(PA007_SEED)
    x_true = np.zeros(n)
    x_true[200:450], x_true[450:700], x_true[700:850] = 1.0, 2.0, 0.5
    dist = np.minimum(np.arange(n), n - np.arange(n))
    kernel = np.exp(-(dist**2) / (2 * 4.0**2))
    kernel /= kernel.sum()
    spectrum = np.fft.rfft(kernel)

    def blur(x: Any) -> Any:
        return np.fft.irfft(spectrum * np.fft.rfft(x), n)

    def blur_t(r: Any) -> Any:
        return np.fft.irfft(np.conj(spectrum) * np.fft.rfft(r), n)

    b = blur(x_true) + 0.01 * rng.standard_normal(n)

    def f_and_grad(x: Any) -> tuple[float, Any]:
        r = blur(x) - b
        d = np.roll(x, -1) - x
        root = np.sqrt(1 + (d / PA007_DELTA) ** 2)
        value = 0.5 * r @ r + PA007_LAMBDA * PA007_DELTA**2 * np.sum(root - 1)
        p = PA007_LAMBDA * d / root
        return float(value), blur_t(r) + np.roll(p, 1) - p

    return {"x_true": x_true, "b": b, "f_and_grad": f_and_grad, "x0": np.zeros(n)}


@functools.cache
def pa007_runs() -> dict[str, dict[str, Any]]:
    """Gradient descent (step 1/L), CG and L-BFGS-B (m=10), each stopped at max|g| <= 1e-6."""
    import numpy as np
    from scipy.optimize import minimize

    problem = _pa007_problem()
    f_and_grad = problem["f_and_grad"]
    x0 = problem["x0"]
    lipschitz = 1 + 4 * PA007_LAMBDA
    runs: dict[str, dict[str, Any]] = {}

    x = x0.copy()
    history: list[float] = []
    while True:
        value, gradient = f_and_grad(x)
        history.append(float(np.abs(gradient).max()))
        if history[-1] <= PA007_TOLERANCE:
            break
        x = x - gradient / lipschitz
    runs["GD"] = {"x": x, "f": value, "iterations": len(history) - 1, "history": history}

    for name, method, options in (
        ("CG", "CG", {}),
        ("L-BFGS", "L-BFGS-B", {"ftol": 0.0, "maxcor": 10}),
    ):
        calls: list[float] = []

        def counted(point: Any, calls: list[float] = calls) -> tuple[float, Any]:
            value, gradient = f_and_grad(point)
            calls.append(float(np.abs(gradient).max()))
            return value, gradient

        res = minimize(
            counted,
            x0,
            jac=True,
            method=method,
            options={"gtol": PA007_TOLERANCE, "maxiter": 100000, **options},
        )
        runs[name] = {"x": res.x, "f": float(res.fun), "iterations": int(res.nit), "history": calls}
    return runs


def pa007_milestones(history: list[float]) -> list[tuple[int, int]]:
    """Return first evaluation at or below each decade, rather than raw gradient values."""
    milestones = []
    for exponent in range(0, -7, -1):
        threshold = 10.0**exponent
        for evaluation, value in enumerate(history, start=1):
            if value <= threshold:
                milestones.append((evaluation, exponent))
                break
    return milestones


def _pa007_decade(value: int) -> str:
    superscript = str.maketrans("-0123456789", "⁻⁰¹²³⁴⁵⁶⁷⁸⁹")
    return "10" + str(value).translate(superscript)


def _pa007_deblur_svg() -> str:
    import numpy as np

    problem = _pa007_problem()
    runs = pa007_runs()
    x_true, b = problem["x_true"], problem["b"]
    x_star = runs["L-BFGS"]["x"]
    norm = float(np.linalg.norm(x_true))
    err_b = float(np.linalg.norm(b - x_true)) / norm
    err_x = float(np.linalg.norm(x_star - x_true)) / norm
    counts = {name: len(run["history"]) for name, run in runs.items()}
    parts = _open(
        "復元の精度と、収束の速さ",
        (
            "ぼかして雑音を足した1000点の測定から信号を復元する例。"
            f"復元した信号の誤差は{err_x:.1%}で、ぼけた測定そのものの誤差は{err_b:.1%}。"
            f"勾配の最大成分が1e-6以下になるまでの勾配の評価回数は、"
            f"勾配降下法が{counts['GD']}回、共役勾配法が{counts['CG']}回、"
            f"L-BFGS法が{counts['L-BFGS']}回。"
            "収束の線は各桁の基準以下に初めてなった評価回数を結び、評価ごとの軌跡は示さない。"
        ),
        654,
    )
    left, right = 56, 416
    px = _scale(PA007_WINDOW[0], PA007_WINDOW[1], left, right)
    py = _scale(-0.3, 1.3, 190, 70)
    parts.append(f'<path d="M{left} 70V190H{right}" fill="none" stroke="{GRID}"/>')
    for value in (0, 1):
        parts.append(_text(left - 8, py(value) + 5, f"{value}", "tick", "end"))
    for value in (180, 210, 240):
        parts.append(_text(px(value), 212, f"{value}", "tick", "middle"))
    parts.append(_text(20, 56, "階段の立ち上がり（位置 180〜240）", "title"))
    indices = list(range(PA007_WINDOW[0], PA007_WINDOW[1] + 1))
    for series, color, width in (
        (b, GRID, 1.2),
        (x_true, LINE, 2.0),
        (x_star, UPDATE, 2.0),
    ):
        parts.append(_polyline([(px(i), py(float(series[i]))) for i in indices], color, width))
    parts.append(_text(20, 238, f"灰：測定 b（全体の誤差 {err_b:.1%}）", "note"))
    parts.append(_text(20, 260, "緑：元の信号", "note"))
    parts.append(_text(20, 282, f"橙：復元 x*（全体の誤差 {err_x:.1%}）", "note"))

    parts.append(_text(20, 316, "勾配の最大成分と評価回数（両対数）", "title"))
    top, bottom, plot_left = 332, 468, 70
    qx = _scale(0, 4, plot_left, right)  # log10 of evaluations, 1 .. 10^4
    qy = _scale(-6.4, 0.6, bottom, top)  # log10 of max|g|
    parts.append(f'<path d="M{plot_left} {top}V{bottom}H{right}" fill="none" stroke="{GRID}"/>')
    for exponent in range(0, 5):
        label = "1" if exponent == 0 else _pa007_decade(exponent)
        parts.append(_text(qx(exponent), bottom + 22, label, "tick", "middle"))
    for exponent in (-6, -3, 0):
        parts.append(_text(plot_left - 6, qy(exponent) + 5, _pa007_decade(exponent), "tick", "end"))
    stop = qy(math.log10(PA007_TOLERANCE))
    parts.append(
        f'<path d="M{plot_left} {stop:.1f}H{right}" fill="none" '
        f'stroke="{GRID}" stroke-width="1.5"/>'
    )
    for name, color in (("GD", MUTED), ("CG", POINT), ("L-BFGS", UPDATE)):
        history = runs[name]["history"]
        points = [
            (qx(math.log10(evaluation)), qy(exponent))
            for evaluation, exponent in pa007_milestones(history)
        ]
        parts.append(_polyline(points, color, 2.0))
    parts.append(_text(right, bottom + 46, "勾配の評価回数", "", "end"))
    for row, (_name, color, label) in enumerate(
        (
            ("GD", MUTED, f"勾配降下法（一歩 1/L）：{counts['GD']}回"),
            ("CG", POINT, f"共役勾配法：{counts['CG']}回"),
            ("L-BFGS", UPDATE, f"L-BFGS法（履歴 m=10）：{counts['L-BFGS']}回"),
        )
    ):
        y = 568 + 22 * row
        parts.append(f'<path d="M20 {y - 5}H44" fill="none" stroke="{color}" stroke-width="3"/>')
        parts.append(_text(54, y, label))
    parts.append(_text(20, 636, "線：各桁の基準以下になった最初の評価", "note"))
    parts.append(_text(20, 542, "灰の横線：停止の基準 10⁻⁶", "note"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


# Closed-form candidate (content/concepts/closed-form-candidate.md): the yearly cost of an order
# quantity Q, f(Q) = K D / Q + h Q / 2. K = 1500 yen per order, D = 1200 units a year, h = 10 yen
# per unit per year. Setting f'(Q) = 0 gives Q* = sqrt(2 K D / h).
_PA001_K, _PA001_D, _PA001_H = 1500.0, 1200.0, 10.0


def _pa001_ordering(q: float) -> float:
    return _PA001_K * _PA001_D / q


def _pa001_holding(q: float) -> float:
    return _PA001_H * q / 2


def _pa001_cost(q: float) -> float:
    return _pa001_ordering(q) + _pa001_holding(q)


def _pa001_slope(q: float) -> float:
    return -_PA001_K * _PA001_D / q**2 + _PA001_H / 2


def _pa001_best_quantity() -> float:
    return math.sqrt(2 * _PA001_K * _PA001_D / _PA001_H)


def _pa001_cost_svg() -> str:
    best = _pa001_best_quantity()
    low, high = 200.0, 1200.0
    px = _scale(low, high, 62, 416)
    py = _scale(0.0, 10500.0, 300, 74)
    quantities = [low + 10.0 * i for i in range(int((high - low) / 10) + 1)]
    parts = _open(
        "注文量と年間の費用",
        (
            "1回の注文量 Q を横軸に、発注費 KD/Q、保管費 hQ/2、その合計を描きます。"
            f"合計は Q={best:g} 個で最小の {_pa001_cost(best):g} 円になり、"
            f"その点で発注費と保管費はどちらも {_pa001_ordering(best):g} 円で交わります。"
        ),
        444,
    )
    parts.append(f'<path d="M62 74V300H416" fill="none" stroke="{INK}" stroke-width="1.5"/>')
    for value in (0, 3000, 6000, 9000):
        parts.append(_text(54, py(value) + 5, f"{value}", "tick", "end"))
        parts.append(f'<path d="M62 {py(value):.1f}H416" stroke="{GRID}" stroke-width="0.6"/>')
    for value in (200, 600, 1000):
        parts.append(_text(px(value), 322, f"{value}", "tick", "middle"))
    parts.append(_text(416, 346, "1回の注文量 Q（個）", "", "end"))
    parts.append(_text(20, 58, "年間の費用（円）", "tick"))
    parts.append(
        f'<path d="M{px(best):.1f} {py(0):.1f}V{py(_pa001_cost(best)):.1f}" '
        f'stroke="{GRID}" stroke-width="1.5"/>'
    )
    for color, width, func in (
        (LINE, 2.5, _pa001_ordering),
        (POINT, 2.5, _pa001_holding),
        (UPDATE, 3.5, _pa001_cost),
    ):
        parts.append(_polyline([(px(q), py(func(q))) for q in quantities], color, width))
    parts.append(_text(px(1000), py(_pa001_ordering(1000)) - 10, "発注費", "note", "middle"))
    parts.append(_text(px(1200) - 4, py(_pa001_holding(1200)) + 24, "保管費", "", "end"))
    parts.append(_text(px(900), py(_pa001_cost(900)) - 12, "合計", "title", "middle"))
    parts.append(
        f'<circle cx="{px(best):.1f}" cy="{py(_pa001_ordering(best)):.1f}" r="6" fill="#f7f8f3" '
        f'stroke="{INK}" stroke-width="2.5"/>'
    )
    parts.append(
        f'<circle cx="{px(best):.1f}" cy="{py(_pa001_cost(best)):.1f}" r="7" fill="{UPDATE}"/>'
    )
    parts.append(_text(px(best) + 14, py(_pa001_cost(best)) - 12, f"Q={best:g}", "title"))
    parts.append(_text(20, 374, f"橙：合計。Q={best:g} で最小の {_pa001_cost(best):g} 円", "note"))
    parts.append(_text(20, 398, f"緑：発注費 KD/Q。Q={best:g} で {_pa001_ordering(best):g} 円"))
    parts.append(_text(20, 422, f"紺：保管費 hQ/2。Q={best:g} で {_pa001_holding(best):g} 円"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


# High-dimensional black box (content/concepts/high-dimensional-black-box.md): a device with n
# knobs in [0, 1], score = mean squared miss from 0.6. 200 evaluations are spent on random points.
_PA015_BUDGET = 200
_PA015_IDEAL = 0.6
_PA015_BOX_HALF = 0.1  # the "small box" is 0.5 <= every knob <= 0.7, side 0.2
_PA015_BOX_DIMS = (1, 2, 3, 4, 5, 6)
_PA015_SEARCH_DIMS = (2, 5, 10, 20, 50)
_PA015_REPS = 200
_PA015_SEED = 0
_PA015_CACHE: dict[int, dict[str, float]] = {}


def _pa015_score(x: Sequence[float]) -> float:
    return sum((v - _PA015_IDEAL) ** 2 for v in x) / len(x)


def _pa015_score_two(x: Sequence[float]) -> float:
    return ((x[0] - _PA015_IDEAL) ** 2 + (x[1] - _PA015_IDEAL) ** 2) / 2


def _pa015_median_best(n: int, score: Callable[[Sequence[float]], float]) -> float:
    rng = random.Random(_PA015_SEED)
    bests = sorted(
        min(score([rng.random() for _ in range(n)]) for _ in range(_PA015_BUDGET))
        for _ in range(_PA015_REPS)
    )
    return (bests[_PA015_REPS // 2 - 1] + bests[_PA015_REPS // 2]) / 2


def _pa015_expected_hits(n: int) -> float:
    return _PA015_BUDGET * (2 * _PA015_BOX_HALF) ** n


def _pa015_search_data() -> dict[int, dict[str, float]]:
    if not _PA015_CACHE:
        for n in _PA015_SEARCH_DIMS:
            _PA015_CACHE[n] = {
                "all": _pa015_median_best(n, _pa015_score),
                "two": _pa015_median_best(n, _pa015_score_two),
            }
    return _PA015_CACHE


def _pa015_typical_score() -> float:
    return (0.4**3 + 0.6**3) / 3  # mean score of a uniformly drawn knob position


def _pa015_label(value: float) -> str:
    return f"{value:.3g}" if value >= 0.01 else f"{value:.2g}"


def _pa015_budget_svg() -> str:
    search = _pa015_search_data()
    parts = _open(
        "つまみの数と、200回の届き方",
        (
            "つまみの数を増やしたとき、200回の評価で何が変わるかを2つのパネルで示します。"
            "小箱（全部のつまみが0.5から0.7）に入る点の期待数は、つまみ3本で"
            f"{_pa015_label(_pa015_expected_hits(3))}、4本で{_pa015_label(_pa015_expected_hits(4))}です。"
            "ランダム探索の最良スコアの中央値は、つまみ2本で"
            f"{search[2]['all']:.4f}、50本で{search[50]['all']:.4f}です。"
        ),
        618,
    )
    px_left, px_right = 56.0, 420.0

    # Panel 1: expected number of random points inside the small box, log scale.
    top, height = 74.0, 150.0
    low, high = 0.01, 100.0
    py = _scale(math.log10(low), math.log10(high), top + height, top)
    parts.append(_text(20, top - 12, "① 小箱に入る点の期待数（200点中）"))
    parts.append(
        f'<path d="M{px_left:.0f} {top:.0f}V{top + height:.0f}H{px_right:.0f}" fill="none" '
        f'stroke="{GRID}" stroke-width="1.5"/>'
    )
    for tick in (0.01, 1.0, 100.0):
        parts.append(_text(48, py(math.log10(tick)) + 5, f"{tick:g}", "", "end"))
        parts.append(
            f'<path d="M52 {py(math.log10(tick)):.1f}H{px_right:.0f}" stroke="{GRID}" '
            'stroke-width="0.8" opacity="0.6"/>'
        )
    slot = (px_right - px_left) / len(_PA015_BOX_DIMS)
    for index, n in enumerate(_PA015_BOX_DIMS):
        value = _pa015_expected_hits(n)
        center = px_left + slot * (index + 0.5)
        color = LINE if value >= 1.0 else UPDATE
        y_top = py(math.log10(value))
        parts.append(
            f'<rect x="{center - 17:.1f}" y="{y_top:.1f}" width="34" '
            f'height="{top + height - y_top:.1f}" fill="{color}" opacity="0.85"/>'
        )
        parts.append(_text(center, y_top - 6, _pa015_label(value), "", "middle"))
        parts.append(_text(center, top + height + 22, str(n), "", "middle"))
    parts.append(
        f'<path d="M{px_left:.0f} {py(0.0):.1f}H{px_right:.0f}" stroke="{INK}" '
        'stroke-width="1.5" stroke-dasharray="5 4"/>'
    )
    parts.append(_text(20, top + height + 48, "横軸：つまみの数 n　縦軸：期待個数（対数）", "note"))

    # Panel 2: median best score of 200 random points, linear scale.
    top = 74.0 + 262.0
    py = _scale(0.1, 0.0, top, top + height)
    parts.append(_text(20, top - 12, "② ランダム200点の最良スコア（中央値）"))
    parts.append(
        f'<path d="M{px_left:.0f} {top:.0f}V{top + height:.0f}H{px_right:.0f}" fill="none" '
        f'stroke="{GRID}" stroke-width="1.5"/>'
    )
    for tick in (0.0, 0.05, 0.1):
        parts.append(_text(48, py(tick) + 5, f"{tick:g}", "", "end"))
        parts.append(
            f'<path d="M52 {py(tick):.1f}H{px_right:.0f}" stroke="{GRID}" stroke-width="0.8" '
            'opacity="0.6"/>'
        )
    typical = _pa015_typical_score()
    parts.append(
        f'<path d="M{px_left:.0f} {py(typical):.1f}H{px_right:.0f}" stroke="{UPDATE}" '
        'stroke-width="2" stroke-dasharray="6 4"/>'
    )
    parts.append(
        _text(px_right, py(typical) + 20, f"ランダムな1点の平均 {typical:.3f}", "note", "end")
    )
    slot = (px_right - px_left) / len(_PA015_SEARCH_DIMS)
    for index, n in enumerate(_PA015_SEARCH_DIMS):
        center = px_left + slot * (index + 0.5)
        value, two = search[n]["all"], search[n]["two"]
        y_top = py(value)
        parts.append(
            f'<rect x="{center - 20:.1f}" y="{y_top:.1f}" width="40" '
            f'height="{top + height - y_top:.1f}" fill="{LINE}" opacity="0.85"/>'
        )
        parts.append(_text(center, y_top - 6, f"{value:.4f}".rstrip("0"), "", "middle"))
        parts.append(_text(center, top + height + 22, str(n), "", "middle"))
        cy = py(two)
        parts.append(
            f'<path d="M{center:.1f} {cy - 8:.1f}L{center + 8:.1f} {cy:.1f}'
            f'L{center:.1f} {cy + 8:.1f}L{center - 8:.1f} {cy:.1f}Z" fill="{INK}"/>'
        )
    parts.append(_text(20, top + height + 48, "横軸：つまみの数 n　縦軸：スコア", "note"))
    parts.append(_text(20, 566, "緑の棒：全部のつまみが効く　黒のひし形：2本だけ効く"))
    parts.append(_text(20, 590, "橙の棒：期待数が1個未満　破線：期待数1個", "note"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


# General nonsmooth local (content/concepts/general-nonsmooth-local.md): two pumps with outputs
# x1, x2. cost(x) = 3|x1 - x2| + |(|t - 2| - 1)| + 0.2 t with t = (x1 + x2) / 2.
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


# Linear system (content/concepts/linear-system.md): three nodes in a row, nodes 1 and 3 joined to
# ground by conductance 1 S, every wire 1 S, 3 A injected at node 1. A x = b with
# A = [[2, -1, 0], [-1, 2, -1], [0, -1, 2]] and b = (3, 0, 0).
PA002_MATRIX = ((2, -1, 0), (-1, 2, -1), (0, -1, 2))
PA002_INJECTION = (3, 0, 0)


def _pa002_circuit_data() -> dict[str, object]:
    """Exact node voltages, the elimination pivots and the current in every wire."""
    rows = [
        [Fraction(v) for v in row] + [Fraction(r)]
        for row, r in zip(PA002_MATRIX, PA002_INJECTION, strict=True)
    ]
    pivots: list[Fraction] = []
    for i in range(3):
        pivots.append(rows[i][i])
        for j in range(i + 1, 3):
            factor = rows[j][i] / rows[i][i]
            rows[j] = [a - factor * c for a, c in zip(rows[j], rows[i], strict=True)]
    voltage = [Fraction(0)] * 3
    for i in (2, 1, 0):
        tail = sum(rows[i][j] * voltage[j] for j in range(i + 1, 3))
        voltage[i] = (rows[i][3] - tail) / rows[i][i]
    return {
        "voltage": voltage,
        "pivots": pivots,
        "wire_12": voltage[0] - voltage[1],
        "wire_23": voltage[1] - voltage[2],
        "ground_1": voltage[0],
        "ground_3": voltage[2],
    }


def _pa002_value(value: Fraction) -> str:
    return f"{float(value):g}"


def _pa002_arrow(x: float, y: float, direction: str) -> str:
    if direction == "right":
        points = f"{x - 7:.1f},{y - 6:.1f} {x + 7:.1f},{y:.1f} {x - 7:.1f},{y + 6:.1f}"
    else:
        points = f"{x - 6:.1f},{y - 7:.1f} {x:.1f},{y + 7:.1f} {x + 6:.1f},{y - 7:.1f}"
    return f'<polygon points="{points}" fill="{UPDATE}"/>'


def _pa002_circuit_svg() -> str:
    data = _pa002_circuit_data()
    voltage: list[Fraction] = data["voltage"]  # type: ignore[assignment]
    nodes = (110.0, 235.0, 360.0)
    wire_y, ground_y = 160.0, 290.0
    amps = {
        "w12": _pa002_value(data["wire_12"]),  # type: ignore[arg-type]
        "w23": _pa002_value(data["wire_23"]),  # type: ignore[arg-type]
        "g1": _pa002_value(data["ground_1"]),  # type: ignore[arg-type]
        "g3": _pa002_value(data["ground_3"]),  # type: ignore[arg-type]
    }
    total = _pa002_value(data["ground_1"] + data["ground_3"])  # type: ignore[operator]
    parts = _open(
        "接点の電圧と電流",
        (
            "3つの接点を一列につないだ回路。接点1に外から3 Aを流し込み、"
            "接点1と接点3は接地につながる。"
            f"電圧は接点1が{_pa002_value(voltage[0])} V、接点2が{_pa002_value(voltage[1])} V、"
            f"接点3が{_pa002_value(voltage[2])} V。接点1と接点2の間と接点2と接点3の間を"
            f"それぞれ{amps['w12']} Aが流れ、接地へは接点1から{amps['g1']} A、"
            f"接点3から{amps['g3']} A流れる。"
        ),
        420,
    )
    parts.append(
        f'<line x1="24" y1="{wire_y}" x2="86" y2="{wire_y}" stroke="{UPDATE}" stroke-width="3"/>'
    )
    parts.append(_pa002_arrow(86, wire_y, "right"))
    parts.append(_text(55, wire_y - 14, "3 A", "", "middle"))
    for a, c in ((nodes[0], nodes[1]), (nodes[1], nodes[2])):
        parts.append(
            f'<line x1="{a + 22:.1f}" y1="{wire_y}" x2="{c - 22:.1f}" y2="{wire_y}" '
            f'stroke="{LINE}" stroke-width="3"/>'
        )
        mid = (a + c) / 2
        parts.append(_pa002_arrow(mid, wire_y, "right"))
    parts.append(_text((nodes[0] + nodes[1]) / 2, wire_y - 14, f"{amps['w12']} A", "", "middle"))
    parts.append(_text((nodes[1] + nodes[2]) / 2, wire_y - 14, f"{amps['w23']} A", "", "middle"))
    for x, key in ((nodes[0], "g1"), (nodes[2], "g3")):
        parts.append(
            f'<line x1="{x:.1f}" y1="{wire_y + 22}" x2="{x:.1f}" y2="{ground_y}" '
            f'stroke="{LINE}" stroke-width="3"/>'
        )
        parts.append(_pa002_arrow(x, (wire_y + ground_y) / 2, "down"))
        parts.append(_text(x + 14, (wire_y + ground_y) / 2 + 5, f"{amps[key]} A"))
    parts.append(_text(nodes[1], 240, "接地なし", "tick", "middle"))
    parts.append(
        f'<line x1="70" y1="{ground_y}" x2="400" y2="{ground_y}" stroke="{INK}" stroke-width="3"/>'
    )
    parts.append(_text(235, ground_y + 28, "接地（0 V）", "", "middle"))
    for index, x in enumerate(nodes):
        parts.append(
            f'<circle cx="{x:.1f}" cy="{wire_y}" r="22" fill="#e3eee6" '
            f'stroke="{POINT}" stroke-width="2.5"/>'
        )
        parts.append(_text(x, wire_y + 6, str(index + 1), "", "middle"))
        parts.append(
            _text(
                x, wire_y - 42, f"v{'₁₂₃'[index]} = {_pa002_value(voltage[index])} V", "", "middle"
            )
        )
    parts.append(_text(20, 364, "各抵抗は 1 S。電流 = 電圧差 × 1 S", "note"))
    parts.append(_text(20, 388, f"接点2：流入 {amps['w12']} A、流出 {amps['w23']} A"))
    parts.append(_text(20, 412, f"接地へ：{amps['g1']} + {amps['g3']} = {total} A"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


# Assignment (content/concepts/assignment-matching.md): three ambulances, three calls, minutes.
ASSIGN_TIMES = ((3, 2, 5), (10, 3, 8), (14, 5, 9))
ASSIGN_ROWS = ("救急車1", "救急車2", "救急車3")
ASSIGN_COLS = ("A", "B", "C")
# A row value u and a column value v with u_i + v_j <= time everywhere (the dual certificate).
ASSIGN_U = (1, 3, 5)
ASSIGN_V = (2, 0, 4)


def assignment_total(columns: Sequence[int]) -> int:
    return sum(ASSIGN_TIMES[i][j] for i, j in enumerate(columns))


def assignment_all() -> list[tuple[int, int, tuple[int, ...]]]:
    """Every one-to-one assignment as (total, longest single trip, columns), cheapest first."""
    rows = []
    for columns in itertools.permutations(range(len(ASSIGN_TIMES))):
        longest = max(ASSIGN_TIMES[i][j] for i, j in enumerate(columns))
        rows.append((assignment_total(columns), longest, columns))
    return sorted(rows)


def assignment_greedy() -> list[tuple[int, int]]:
    """Take the shortest remaining (ambulance, call) pair until every ambulance is sent."""
    free_rows, free_cols = set(range(3)), set(range(3))
    picks = []
    while free_rows:
        i, j = min(
            ((i, j) for i in free_rows for j in free_cols),
            key=lambda cell: (ASSIGN_TIMES[cell[0]][cell[1]], cell),
        )
        picks.append((i, j))
        free_rows.remove(i)
        free_cols.remove(j)
    return picks


def assignment_reduced() -> list[list[int]]:
    """time - u_i - v_j: never negative, and 0 on the cells of the cheapest assignment."""
    return [[ASSIGN_TIMES[i][j] - ASSIGN_U[i] - ASSIGN_V[j] for j in range(3)] for i in range(3)]


def _assignment_grid(
    top: float,
    values: Sequence[Sequence[int]],
    chosen: dict[tuple[int, int], str],
    column_labels: Sequence[str],
    row_labels: Sequence[str],
) -> list[str]:
    """A 3x3 table: column headers at `top`, rows below. Chosen cells are filled orange."""
    left, cell_w, cell_h = 168, 84, 46
    parts = []
    for j, label in enumerate(column_labels):
        parts.append(_text(left + cell_w * (j + 0.5), top + 18, label, "", "middle"))
    for i, label in enumerate(row_labels):
        y = top + 28 + cell_h * i
        parts.append(_text(left - 12, y + 29, label, "", "end"))
        for j in range(3):
            x = left + cell_w * j
            mark = chosen.get((i, j))
            fill = "#f3d2b5" if mark is not None else "#ffffff"
            stroke = UPDATE if mark is not None else GRID
            width = 2.5 if mark is not None else 1
            parts.append(
                f'<rect x="{x + 3}" y="{y + 3:.1f}" width="{cell_w - 6}" height="{cell_h - 6}" '
                f'rx="6" fill="{fill}" stroke="{stroke}" stroke-width="{width}"/>'
            )
            parts.append(_text(x + cell_w / 2, y + 29, str(values[i][j]), "", "middle"))
            if mark:
                parts.append(_text(x + 9, y + 21, mark, "tick"))
    return parts


def _assignment_greedy_svg() -> str:
    greedy = assignment_greedy()
    greedy_times = [ASSIGN_TIMES[i][j] for i, j in greedy]
    best_total, best_longest, best = assignment_all()[0]
    best_times = [ASSIGN_TIMES[i][j] for i, j in enumerate(best)]
    parts = _open(
        "近い組から決めると、合計が延びる",
        (
            "救急車3台と通報A・B・Cの到着時間（分）の表を2枚並べたもの。"
            f"① 近い組から決めると {'、'.join(map(str, greedy_times))} 分を選び、"
            f"合計は {sum(greedy_times)} 分。"
            f"② 合計が最小の割当は {'、'.join(map(str, best_times))} 分を選び、"
            f"合計は {best_total} 分。どちらも各行・各列から一つずつ選んでいる。"
        ),
        520,
    )
    columns = [f"通報{name}" for name in ASSIGN_COLS]
    parts.append(_text(20, 66, "① 近い組から決める"))
    parts.append(_text(420, 66, f"合計 {sum(greedy_times)} 分", "note", "end"))
    order = {cell: str(k + 1) for k, cell in enumerate(greedy)}
    parts += _assignment_grid(76, ASSIGN_TIMES, order, columns, ASSIGN_ROWS)
    parts.append(_text(20, 296, "② 合計が最小の割当"))
    parts.append(_text(420, 296, f"合計 {best_total} 分", "note", "end"))
    parts += _assignment_grid(
        306, ASSIGN_TIMES, {(i, j): "" for i, j in enumerate(best)}, columns, ASSIGN_ROWS
    )
    parts.append(_text(20, 496, f"① {' + '.join(map(str, greedy_times))} = {sum(greedy_times)}"))
    parts.append(
        _text(
            420,
            496,
            f"② {' + '.join(map(str, best_times))} = {best_total}",
            "note",
            "end",
        )
    )
    parts.append("</svg>")
    return "".join(parts) + "\n"


def _assignment_dual_svg() -> str:
    reduced = assignment_reduced()
    best_total, _, best = assignment_all()[0]
    bound = sum(ASSIGN_U) + sum(ASSIGN_V)
    parts = _open(
        "どの割当も15分を下回らない理由",
        (
            f"救急車ごとの値 u=({', '.join(map(str, ASSIGN_U))}) と、"
            f"通報ごとの値 v=({', '.join(map(str, ASSIGN_V))}) を到着時間から引いた表。"
            "すべてのマスが0以上で、合計が最小の割当の3マスは0。"
            f"そのため、どの割当の合計も u と v の合計 {bound} 分以上になる。"
        ),
        360,
    )
    columns = [f"{name} v={value}" for name, value in zip(ASSIGN_COLS, ASSIGN_V, strict=True)]
    rows = [f"{name} u={value}" for name, value in zip(ASSIGN_ROWS, ASSIGN_U, strict=True)]
    parts.append(_text(20, 64, "時間 − u − v"))
    parts += _assignment_grid(74, reduced, {(i, j): "" for i, j in enumerate(best)}, columns, rows)
    parts.append(_text(20, 266, f"u の合計 {sum(ASSIGN_U)} ＋ v の合計 {sum(ASSIGN_V)} = {bound}"))
    parts.append(_text(20, 292, "どの割当も各行・各列を一度ずつ使うので、"))
    parts.append(_text(20, 316, f"合計 ＝ {bound} ＋ 選んだマスの値 ≧ {bound}"))
    parts.append(_text(20, 344, f"橙の3マスは0なので、合計 {best_total} 分が最小", "note"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


# Eigenvalue problem (content/concepts/eigenvalue-problem.md): five stakes along a straight
# fence, read off a map with errors in both coordinates. The fence's unit normal n minimises
# the sum of squared perpendicular distances n^T M n, M = sum of (p - mean)(p - mean)^T.
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


# Stochastic programming (content/concepts/stochastic-programming.md): lunch boxes made in the
# morning at 100 yen; any shortage is brought in from a nearby shop at 250 yen each.
SP_MAKE, SP_BUY = 100, 250
SP_SCENARIOS = (("雨", 20, 0.3), ("曇り", 40, 0.4), ("晴れ", 80, 0.3))


def sp_cost(made: float, demand: float) -> float:
    return SP_MAKE * made + SP_BUY * max(demand - made, 0.0)


def sp_expected(made: float) -> float:
    return sum(p * sp_cost(made, d) for _, d, p in SP_SCENARIOS)


def sp_mean_demand() -> float:
    return sum(p * d for _, d, p in SP_SCENARIOS)


def sp_best() -> tuple[int, float]:
    """The minimiser over whole boxes (the expected cost is piecewise linear in made)."""
    return min(((made, sp_expected(made)) for made in range(0, 101)), key=lambda r: r[1])


def _sp_cost_svg() -> str:
    best, best_cost = sp_best()
    mean = sp_mean_demand()
    worst = max(d for _, d, _ in SP_SCENARIOS)
    parts = _open(
        "天気ごとの費用と、その期待値",
        (
            f"朝に作る弁当の数 x（0〜100個）と費用。1個{SP_MAKE}円で作り、"
            f"足りない分は1個{SP_BUY}円で取り寄せる。"
            "① 注文が雨20個・曇り40個・晴れ80個の三つの場合の費用の折れ線。"
            "② 確率0.3・0.4・0.3で重みを付けた期待費用。"
            f"期待費用は x={best} で最小の {best_cost:g} 円、平均の注文の数 {mean:g} 個では "
            f"{sp_expected(mean):g} 円、最大の注文の数 {worst} 個では {sp_expected(worst):g} 円。"
        ),
        622,
    )
    px = _scale(0.0, 100.0, 76, 410)
    for tick in (0, 20, 40, 60, 80, 100):
        parts.append(_text(px(tick), 300, str(tick), "tick", "middle"))
        parts.append(_text(px(tick), 584, str(tick), "tick", "middle"))
    parts.append(_text(20, 64, "① 天気ごとの費用（千円）"))
    py = _scale(0.0, 25000.0, 280, 80)
    parts.append(f'<path d="M76 80V280H410" fill="none" stroke="{GRID}"/>')
    for value in (0, 10000, 20000):
        parts.append(_text(68, py(value) + 5, str(value // 1000), "tick", "end"))
    colors = {"雨": RING, "曇り": LINE, "晴れ": INK}
    for index, (name, demand, _) in enumerate(reversed(SP_SCENARIOS)):
        points = [(px(x), py(sp_cost(x, demand))) for x in (0, demand, 100)]
        parts.append(_polyline(points, colors[name], 2.5))
        y = 104 + 24 * index
        parts.append(_polyline([(300, y - 5), (322, y - 5)], colors[name], 2.5))
        parts.append(_text(330, y, f"{name} {demand}個", "tick"))
    parts.append(_text(20, 340, "② 期待費用（千円）"))
    gy = _scale(6000.0, 12000.0, 564, 364)
    parts.append(f'<path d="M76 364V564H410" fill="none" stroke="{GRID}"/>')
    for value in (6000, 8000, 10000, 12000):
        parts.append(_text(68, gy(value) + 5, str(value // 1000), "tick", "end"))
    kinks = [0, *sorted(d for _, d, _ in SP_SCENARIOS), 100]
    parts.append(_polyline([(px(x), gy(sp_expected(x))) for x in kinks], MUTED, 3))
    marks = (
        (best, UPDATE, f"x={best}：{sp_expected(best):g}円", -12, 26),
        (mean, POINT, f"x={mean:g}：{sp_expected(mean):g}円", 14, 26),
        (worst, GRID, f"x={worst}：{sp_expected(worst):g}円", -12, -12),
    )
    for x, color, label, shift, lift in marks:
        parts.append(
            f'<circle cx="{px(x):.1f}" cy="{gy(sp_expected(x)):.1f}" r="7" fill="{color}" '
            f'stroke="{INK}" stroke-width="1.5"/>'
        )
        anchor = "start" if shift > 0 else "end"
        parts.append(_text(px(x) + shift, gy(sp_expected(x)) + lift, label, "tick", anchor))
    parts.append(_text(410, 604, "朝に作る数 x（個）", "tick", "end"))
    parts.append(_text(20, 604, f"最小は x={best}", "note"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


def _sp_tree_svg() -> str:
    """One morning decision shared by every branch; the afternoon decision differs by branch."""
    best, _ = sp_best()
    parts = _open(
        "朝の決定は一つ、昼の対応は天気ごと",
        (
            f"朝に作る数 x は天気を知る前に一つだけ決める（例では x={best}）。"
            "天気が分かった後の取り寄せ数 y は、雨・曇り・晴れの枝ごとに別々に決める。"
            f"x={best} なら y は雨0・曇り0・晴れ{80 - best}。"
        ),
        370,
    )
    root = (70.0, 210.0)
    parts.append(
        f'<rect x="{root[0] - 50}" y="{root[1] - 34}" width="100" height="68" rx="10" '
        f'fill="#f3d2b5" stroke="{UPDATE}" stroke-width="2.5"/>'
    )
    parts.append(_text(root[0], root[1] - 6, "朝", "", "middle"))
    parts.append(_text(root[0], root[1] + 18, f"x={best}", "", "middle"))
    for index, (name, demand, prob) in enumerate(SP_SCENARIOS):
        y = 120.0 + 90.0 * index
        bring = max(demand - best, 0)
        parts.append(
            f'<path d="M{root[0] + 50} {root[1]}L250 {y}" stroke="{GRID}" stroke-width="2"/>'
        )
        parts.append(_text(185, (root[1] + y) / 2 - 10, f"{prob:g}", "tick", "middle"))
        parts.append(
            f'<rect x="250" y="{y - 30}" width="170" height="60" rx="10" fill="#ffffff" '
            f'stroke="{LINE}" stroke-width="2"/>'
        )
        parts.append(_text(262, y - 6, f"{name}：注文 {demand}"))
        parts.append(_text(262, y + 18, f"取り寄せ y={bring}", "note"))
    parts.append(_text(20, 64, "天気が分かる前", "tick"))
    parts.append(_text(420, 64, "天気が分かった後", "tick", "end"))
    parts.append(_text(20, 358, "線の数字は天気の確率", "tick"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


# Optimization with an external solver in the objective
# (content/concepts/external-solver-objective.md): an A–B alloy whose stand-in "tool" returns the
# phase combination with the lowest Gibbs energy, g_α = (x − 0.1)², g_β = (x − 0.6)² + 0.1.
EXT_TANGENT = (0.2, 0.7)  # where the common tangent G = 0.2x − 0.03 touches the two parabolas
EXT_TARGET = 0.3
EXT_START = 0.6
# The three runs of the article's pitfall, as SciPy 1.18.1 reports them from x0 = 0.6 with the
# article's J (finite-difference gradients for the first two): (name, bounds, end, calls).
EXT_RUNS = (
    ("BFGS", "範囲なし", -0.41, 4),
    ("L-BFGS-B", "範囲 [0,1]", 0.0, 4),
    ("Nelder–Mead", "範囲 [0,1]", 0.35, 30),
)


def ext_equilibrium(x: float) -> tuple[str, float, float]:
    """(phases, β fraction, Gibbs energy) of the candidate with the lowest Gibbs energy."""
    low, high = EXT_TANGENT
    candidates = [("α", 0.0, (x - 0.1) ** 2), ("β", 1.0, (x - 0.6) ** 2 + 0.1)]
    if low < x < high:
        fraction = (x - low) / (high - low)
        candidates.append(("α+β", fraction, 0.2 * x - 0.03))
    return min(candidates, key=lambda c: c[2])


def ext_objective(x: float) -> float:
    value = (ext_equilibrium(x)[1] - EXT_TARGET) ** 2
    return 0.0 if abs(value) < 1e-12 else value


def _ext_flat_stop_svg() -> str:
    low, high = EXT_TANGENT
    start_j = ext_objective(EXT_START)
    parts = _open(
        "差分の勾配は、βが0の平らな範囲で止まる",
        (
            "Bの分率 x（−0.5〜1）と外側の目的 J=(βの量−0.30)²。"
            f"x が {low:g} 以下では β がなく J=0.09 で平ら、"
            f"{high:g} 以上では β だけで J=0.49 で平ら、"
            f"そのあいだで J=4(x−0.35)² の谷。始点 {EXT_START:g}（J={start_j:g}）から、"
            "範囲なしのBFGSは x=−0.41 で、範囲 [0, 1] のL-BFGS-Bは x=0 で、どちらも J=0.09 のまま"
            "止まる。範囲 [0, 1] のNelder–Meadは 30 回の計算で x=0.35、J=0 に着く。"
        ),
        478,
    )
    px = _scale(-0.5, 1.0, 56, 416)
    py = _scale(0.0, 0.5, 300, 84)
    parts.append(
        f'<rect x="{px(-0.5):.1f}" y="84" width="{px(0.0) - px(-0.5):.1f}" height="216" '
        f'fill="{VIOLATION}" opacity="0.08"/>'
    )
    parts.append(
        f'<rect x="{px(low):.1f}" y="84" width="{px(high) - px(low):.1f}" height="216" '
        f'fill="{RING}" opacity="0.25"/>'
    )
    parts.append(_text((px(-0.5) + px(0.0)) / 2, 74, "組成の外", "tick", "middle"))
    parts.append(_text((px(0.0) + px(low)) / 2, 74, "αだけ", "tick", "middle"))
    parts.append(_text((px(low) + px(high)) / 2, 74, "α+β", "tick", "middle"))
    parts.append(_text((px(high) + px(1.0)) / 2, 74, "βだけ", "tick", "middle"))
    parts.append(f'<path d="M56 84V300H416" fill="none" stroke="{GRID}" stroke-width="1.5"/>')
    for value in (0.0, 0.09, 0.25, 0.49):
        parts.append(
            f'<path d="M56 {py(value):.1f}H416" stroke="{GRID}" stroke-width="0.6" opacity="0.6"/>'
        )
        parts.append(_text(48, py(value) + 5, f"{value:g}", "tick", "end"))
    for value in (-0.5, 0.0, 0.35, 0.6, 1.0):
        parts.append(_text(px(value), 320, f"{value:g}".replace("-", "−"), "tick", "middle"))
    parts.append(_text(416, 342, "Bの分率 x", "tick", "end"))
    xs = [-0.5 + 1.5 * i / 600 for i in range(601)]
    parts.append(_polyline([(px(x), py(ext_objective(x))) for x in xs], LINE, 3))
    sx, sy = px(EXT_START), py(start_j)
    for name, _, end, _ in EXT_RUNS:
        ex, ey = px(end), py(ext_objective(end))
        lift = 70 if name == "BFGS" else 40
        parts.append(
            f'<path d="M{sx:.1f} {sy:.1f}Q{(sx + ex) / 2:.1f} {min(sy, ey) - lift:.1f} '
            f'{ex:.1f} {ey:.1f}" fill="none" stroke="{UPDATE}" stroke-width="1.6" '
            'stroke-dasharray="5 4"/>'
        )
        if end == 0.35:
            parts.append(f'<circle cx="{ex:.1f}" cy="{ey:.1f}" r="7" fill="{LINE}"/>')
            parts.append(_text(ex, ey - 12, name, "tick", "middle"))
        else:
            parts.append(
                f'<rect x="{ex - 6:.1f}" y="{ey - 6:.1f}" width="12" height="12" fill="#f7f8f3" '
                f'stroke="{POINT}" stroke-width="2.5"/>'
            )
            # Both labels sit under their squares; L-BFGS-B ends at its square to clear Nelder–Mead.
            if name == "BFGS":
                parts.append(_text(ex, ey + 26, name, "tick", "middle"))
            else:
                parts.append(_text(ex + 6, ey + 26, name, "tick", "end"))
    parts.append(f'<circle cx="{sx:.1f}" cy="{sy:.1f}" r="7" fill="{UPDATE}"/>')
    parts.append(_text(sx + 12, sy + 5, "始点", ""))
    parts.append(_text(20, 372, f"始点 x={EXT_START:.2f}（J={start_j:g}）から："))
    for index, (name, bounds, end, calls) in enumerate(EXT_RUNS):
        value = ext_objective(end)
        tail = f"、{calls}回" if name == "Nelder–Mead" else ""
        line = f"{name}（{bounds}）→ x={end:.2f}、J={value:g}{tail}".replace("-0", "−0")
        parts.append(_text(20, 396 + 24 * index, line, "note" if value == 0 else ""))
    parts.append(_text(20, 468, "上の2つは「成功」と報告して止まる"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


# Robust optimization (content/concepts/robust-optimization.md): ten kilograms of nitrogen
# from bags of chemical fertilizer (A) and compost (B), whose nitrogen per bag is only known
# to lie in a range. At most eight bags fit on the truck.
RO_COST = (3.0, 1.2)  # thousand yen per bag
RO_MEAN = (2.0, 1.0)  # kg of nitrogen per bag, the middle of the recorded range
RO_HALF = (0.2, 0.5)  # half-width of the recorded range
RO_NEED, RO_CAP = 10.0, 8.0


def ro_coefficients(k: float) -> tuple[float, float]:
    """The low corner of the range shrunk to k times its recorded half-width."""
    return (RO_MEAN[0] - k * RO_HALF[0], RO_MEAN[1] - k * RO_HALF[1])


def ro_solve(k: float) -> tuple[tuple[float, float], float]:
    """min c'x s.t. a(k)'x >= need, x1 + x2 <= cap, x >= 0, by enumerating the vertices."""
    a = ro_coefficients(k)
    lines = (  # (p, q, r) for p x1 + q x2 = r
        (a[0], a[1], RO_NEED),
        (1.0, 1.0, RO_CAP),
        (1.0, 0.0, 0.0),
        (0.0, 1.0, 0.0),
    )
    best: tuple[tuple[float, float], float] | None = None
    for (p1, q1, r1), (p2, q2, r2) in itertools.combinations(lines, 2):
        det = p1 * q2 - p2 * q1
        if abs(det) < 1e-12:
            continue
        x = ((r1 * q2 - r2 * q1) / det, (p1 * r2 - p2 * r1) / det)
        feasible = (
            min(x) >= -1e-9
            and x[0] + x[1] <= RO_CAP + 1e-9
            and a[0] * x[0] + a[1] * x[1] >= RO_NEED - 1e-9
        )
        cost = RO_COST[0] * x[0] + RO_COST[1] * x[1]
        if feasible and (best is None or cost < best[1] - 1e-12):
            best = (x, cost)
    assert best is not None
    return best


def ro_content(x: Sequence[float], a: Sequence[float]) -> float:
    return a[0] * x[0] + a[1] * x[1]


def ro_shortfall_probability(x: Sequence[float]) -> float:
    """P(a'x < need) when a is uniform on the recorded box: area of the clipped box / box area."""
    low = ro_coefficients(1.0)
    high = (RO_MEAN[0] + RO_HALF[0], RO_MEAN[1] + RO_HALF[1])
    box = [(low[0], low[1]), (high[0], low[1]), (high[0], high[1]), (low[0], high[1])]

    def gap(point: tuple[float, float]) -> float:
        return RO_NEED - ro_content(x, point)

    kept: list[tuple[float, float]] = []
    for p, q in zip(box, box[1:] + box[:1], strict=True):
        if gap(p) > 0:
            kept.append(p)
        if (gap(p) > 0) != (gap(q) > 0):
            s = gap(p) / (gap(p) - gap(q))
            kept.append((p[0] + s * (q[0] - p[0]), p[1] + s * (q[1] - p[1])))
    if len(kept) < 3:
        return 0.0
    area = 0.5 * abs(
        sum(p[0] * q[1] - q[0] * p[1] for p, q in zip(kept, kept[1:] + kept[:1], strict=True))
    )
    return area / (4 * RO_HALF[0] * RO_HALF[1])


def ro_switch() -> float:
    """The range factor k at which the cheapest plan stops using compost (bisection)."""
    low, high = 0.0, 1.0
    for _ in range(200):
        mid = (low + high) / 2
        low, high = (mid, high) if ro_solve(mid)[0][1] > 1e-9 else (low, mid)
    return (low + high) / 2


def _ro_number(value: float, digits: int = 2) -> str:
    return f"{round(value, digits):g}"


def _ro_box_svg() -> str:
    nominal, nominal_cost = ro_solve(0.0)
    robust, robust_cost = ro_solve(1.0)
    worst = ro_coefficients(1.0)
    parts = _open(
        "含有量の範囲と、袋数の選び方",
        (
            "① 1袋あたりの窒素の範囲：化成肥料1.8〜2.2kg、堆肥0.5〜1.5kg。中央は (2, 1)、"
            "どちらも少ない角は (1.8, 0.5)。"
            "② 袋数の平面：化成肥料 x₁ と堆肥 x₂。中央の含有量で窒素10kgの線、"
            "少ない角の含有量で窒素10kgの線、8袋の線。"
            f"中央の含有量で最も安い (2, 6) は{_ro_number(nominal_cost)}千円だが、"
            f"少ない角では窒素{_ro_number(ro_content(nominal, worst))}kg。"
            f"範囲のどこでも10kgを守る最も安い組み合わせは"
            f"({_ro_number(robust[0])}, 0)で{_ro_number(robust_cost)}千円。"
        ),
        660,
    )
    parts.append(_text(20, 64, "① 1袋あたりの窒素（kg）の範囲"))
    ax = _scale(1.7, 2.3, 96, 400)
    ay = _scale(0.3, 1.7, 236, 84)
    parts.append(f'<path d="M96 84V236H400" fill="none" stroke="{GRID}"/>')
    for value in (1.8, 2.0, 2.2):
        parts.append(_text(ax(value), 256, f"{value:g}", "tick", "middle"))
    for value in (0.5, 1.0, 1.5):
        parts.append(_text(88, ay(value) + 5, f"{value:g}", "tick", "end"))
    parts.append(_text(400, 280, "化成肥料 a₁", "tick", "end"))
    parts.append(_text(104, 100, "堆肥 a₂", "tick"))
    lo, hi = ro_coefficients(1.0), ro_coefficients(-1.0)
    parts.append(
        f'<rect x="{ax(lo[0]):.1f}" y="{ay(hi[1]):.1f}" width="{ax(hi[0]) - ax(lo[0]):.1f}" '
        f'height="{ay(lo[1]) - ay(hi[1]):.1f}" fill="#e3ece6" stroke="{LINE}" stroke-width="2"/>'
    )
    parts.append(
        f'<circle cx="{ax(RO_MEAN[0]):.1f}" cy="{ay(RO_MEAN[1]):.1f}" r="7" fill="{POINT}"/>'
    )
    parts.append(_text(ax(RO_MEAN[0]) + 12, ay(RO_MEAN[1]) + 5, "中央 (2, 1)"))
    parts.append(f'<circle cx="{ax(worst[0]):.1f}" cy="{ay(worst[1]):.1f}" r="7" fill="{UPDATE}"/>')
    parts.append(
        _text(ax(worst[0]) + 12, ay(worst[1]) - 8, "少ない角 (1.8, 0.5)").replace(
            "<text ", f'<text style="fill:{UPDATE}" '
        )
    )

    parts.append(_text(20, 318, "② 袋数の平面"))
    parts.append(_text(410, 318, "縦：堆肥 x₂（袋）", "tick", "end"))
    px = _scale(0.0, 8.0, 76, 410)
    py = _scale(0.0, 8.0, 584, 348)
    parts.append(f'<path d="M76 348V584H410" fill="none" stroke="{GRID}"/>')
    for value in (0, 2, 4, 6, 8):
        parts.append(_text(px(value), 604, str(value), "tick", "middle"))
        parts.append(_text(68, py(value) + 5, str(value), "tick", "end"))
    parts.append(_text(410, 628, "化成肥料 x₁（袋）", "tick", "end"))
    corner = (
        (RO_NEED - worst[1] * RO_CAP) / (worst[0] - worst[1]),
        RO_CAP - (RO_NEED - worst[1] * RO_CAP) / (worst[0] - worst[1]),
    )
    region = [(RO_NEED / worst[0], 0.0), (RO_CAP, 0.0), corner]
    joined = " ".join(f"{px(x):.1f},{py(y):.1f}" for x, y in region)
    parts.append(f'<polygon points="{joined}" fill="#f3d2b5" stroke="none"/>')
    parts.append(_polyline([(px(0), py(RO_CAP)), (px(RO_CAP), py(0))], MUTED, 2))
    top = (RO_NEED - RO_MEAN[1] * RO_CAP) / RO_MEAN[0]  # where the mean line meets x2 = 8
    mean_line = [(px(RO_NEED / RO_MEAN[0]), py(0)), (px(top), py(RO_CAP))]
    parts.append(_polyline(mean_line, POINT, 2.5))
    worst_top = (RO_NEED - worst[1] * RO_CAP) / worst[0]  # where it meets x2 = 8
    worst_line = [(px(RO_NEED / worst[0]), py(0)), (px(worst_top), py(RO_CAP))]
    parts.append(_polyline(worst_line, UPDATE, 2.5))
    parts.append(
        f'<circle cx="{px(nominal[0]):.1f}" cy="{py(nominal[1]):.1f}" r="7" fill="{POINT}" '
        f'stroke="{INK}" stroke-width="1.5"/>'
    )
    parts.append(
        _text(px(nominal[0]) + 12, py(nominal[1]) - 8, f"(2, 6)：{_ro_number(nominal_cost)}千円")
    )
    parts.append(
        f'<circle cx="{px(robust[0]):.1f}" cy="{py(robust[1]):.1f}" r="7" fill="{UPDATE}" '
        f'stroke="{INK}" stroke-width="1.5"/>'
    )
    parts.append(_text(410, py(7.4), f"橙の点 ({_ro_number(robust[0])}, 0)", anchor="end"))
    parts.append(_text(410, py(7.4) + 22, f"{_ro_number(robust_cost)}千円", anchor="end"))
    parts.append(_polyline([(20, 646 - 5), (42, 646 - 5)], POINT, 2.5))
    parts.append(_text(48, 646, "中央で10kg", "tick"))
    parts.append(_polyline([(152, 646 - 5), (174, 646 - 5)], UPDATE, 2.5))
    parts.append(_text(180, 646, "少ない角で10kg", "tick"))
    parts.append(_polyline([(312, 646 - 5), (334, 646 - 5)], MUTED, 2))
    parts.append(_text(340, 646, "8袋", "tick"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


def _ro_set_size_svg() -> str:
    switch = ro_switch()
    ks = [i / 200 for i in range(201)]
    parts = _open(
        "備える範囲の広さと、費用・不足の確率",
        (
            "備える範囲を、記録された範囲の k 倍（k=0 は中央の値だけ、k=1 は記録された範囲全体）"
            "にしたときの最も安い組み合わせ。"
            f"① 費用は k=0 の{_ro_number(ro_solve(0.0)[1])}千円から k=1 の"
            f"{_ro_number(ro_solve(1.0)[1])}千円まで増える。"
            f"k={_ro_number(switch, 3)} で堆肥を使わない組み合わせに切り替わる。"
            "② 含有量が記録された範囲の中で一様にばらつくと仮定したときの、"
            "窒素が10kgに届かない確率。"
            f"k=0 で{_ro_number(100 * ro_shortfall_probability(ro_solve(0.0)[0]), 1)}%、"
            f"k=1 で0%。切り替わりの直後に確率が上がる。"
        ),
        610,
    )
    px = _scale(0.0, 1.0, 76, 410)
    for tick in (0.0, 0.25, 0.5, 0.75, 1.0):
        parts.append(_text(px(tick), 300, f"{tick:g}", "tick", "middle"))
        parts.append(_text(px(tick), 564, f"{tick:g}", "tick", "middle"))
    parts.append(_text(20, 64, "① 最も安い組み合わせの費用（千円）"))
    cy = _scale(12.0, 17.0, 280, 84)
    parts.append(f'<path d="M76 84V280H410" fill="none" stroke="{GRID}"/>')
    for value in (12, 14, 16):
        parts.append(_text(68, cy(value) + 5, str(value), "tick", "end"))
    parts.append(_polyline([(px(k), cy(ro_solve(k)[1])) for k in ks], LINE, 3))
    parts.append(_text(20, 344, "② 窒素が10kgに届かない確率（%）"))
    qy = _scale(0.0, 60.0, 544, 364)
    parts.append(f'<path d="M76 364V544H410" fill="none" stroke="{GRID}"/>')
    for value in (0, 25, 50):
        parts.append(_text(68, qy(value) + 5, str(value), "tick", "end"))
    before = [k for k in ks if k < switch]
    after = [k for k in ks if k > switch]
    for segment in (before, after):
        points = [(px(k), qy(100 * ro_shortfall_probability(ro_solve(k)[0]))) for k in segment]
        parts.append(_polyline(points, UPDATE, 3))
    for top, bottom in ((84, 280), (364, 544)):
        parts.append(
            f'<path d="M{px(switch):.1f} {top}V{bottom}" stroke="{MUTED}" stroke-width="1.5" '
            'stroke-dasharray="5 4"/>'
        )
    parts.append(_text(px(switch) + 8, 392, f"k={_ro_number(switch, 3)}", "tick"))
    parts.append(_text(px(switch) + 8, 412, "ここから堆肥0袋", "tick"))
    for k, shift, lift, anchor in (
        (0.0, 10, -10, "start"),
        (0.45, -10, 22, "end"),
        (0.5, 10, -10, "start"),
    ):
        x, cost = ro_solve(k)
        probability = 100 * ro_shortfall_probability(x)
        parts.append(f'<circle cx="{px(k):.1f}" cy="{qy(probability):.1f}" r="5" fill="{INK}"/>')
        label = f"{_ro_number(probability, 1)}%"
        parts.append(_text(px(k) + shift, qy(probability) + lift, label, "tick", anchor))
        parts.append(f'<circle cx="{px(k):.1f}" cy="{cy(cost):.1f}" r="5" fill="{INK}"/>')
        if k == 0.0:
            parts.append(_text(px(k) + shift, cy(cost) + 22, _ro_number(cost), "tick"))
    switch_cost = ro_solve(switch)[1]
    parts.append(
        _text(px(switch) - 10, cy(switch_cost) - 12, f"{_ro_number(switch_cost)}", "tick", "end")
    )
    full = ro_solve(1.0)[1]
    parts.append(f'<circle cx="{px(1.0):.1f}" cy="{cy(full):.1f}" r="5" fill="{INK}"/>')
    parts.append(_text(px(1.0), cy(full) + 24, _ro_number(full), "tick", "end"))
    parts.append(_text(410, 588, "備える範囲の広さ k", "tick", "end"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


# Robust parameter estimation (content/concepts/robust-parameter-estimation.md): the spring's
# eight readings from the nonlinear least-squares lesson, with the reading at t=2.5 s recorded
# without its minus sign (1.7 instead of -1.7). Huber loss with scale 0.3.
RPE_Y = tuple(1.7 if index == 5 else y for index, y in enumerate(SPRING_Y))
RPE_BAD = 5
RPE_DELTA = 0.3


def rpe_huber(residual: float, delta: float = RPE_DELTA) -> float:
    size = abs(residual)
    return 0.5 * size * size if size <= delta else delta * (size - 0.5 * delta)


def rpe_huber_slope(residual: float, delta: float = RPE_DELTA) -> float:
    return max(-delta, min(delta, residual))


def rpe_squares_profile(w: float, ys: Sequence[float] = RPE_Y) -> tuple[float, float]:
    """(smallest sum of squares over the amplitude, that amplitude) at a fixed ω."""
    s = [math.sin(w * t) for t in SPRING_T]
    a = sum(si * yi for si, yi in zip(s, ys, strict=True)) / sum(si * si for si in s)
    return sum((a * si - yi) ** 2 for si, yi in zip(s, ys, strict=True)), a


def rpe_huber_profile(w: float) -> tuple[float, float]:
    """(smallest Huber loss over the amplitude, that amplitude): bisection on the monotone slope."""
    s = [math.sin(w * t) for t in SPRING_T]
    low, high = -20.0, 20.0
    for _ in range(100):
        mid = (low + high) / 2
        slope = sum(rpe_huber_slope(mid * si - yi) * si for si, yi in zip(s, RPE_Y, strict=True))
        low, high = (low, mid) if slope > 0 else (mid, high)
    a = (low + high) / 2
    return sum(rpe_huber(a * si - yi) for si, yi in zip(s, RPE_Y, strict=True)), a


def rpe_clean_profile(w: float) -> tuple[float, float]:
    """The same profile for the eight readings with the correct sign."""
    return rpe_squares_profile(w, SPRING_Y)


@functools.cache
def rpe_valleys(profile: Callable[[float], tuple[float, float]]) -> list[tuple[float, float]]:
    """Local minima of a profile on (0.2, 2π], each refined by golden-section search."""
    grid = [0.2 + (2 * math.pi - 0.2) * i / 1200 for i in range(1201)]
    values = [profile(w)[0] for w in grid]
    found = []
    for i in range(1, len(grid) - 1):
        if values[i] < values[i - 1] and values[i] <= values[i + 1]:
            low, high = grid[i - 1], grid[i + 1]
            ratio = (math.sqrt(5) - 1) / 2
            for _ in range(80):
                left, right = high - ratio * (high - low), low + ratio * (high - low)
                low, high = (low, right) if profile(left)[0] < profile(right)[0] else (left, high)
            w = (low + high) / 2
            found.append((w, profile(w)[0]))
    return found


def rpe_residuals(a: float, w: float) -> list[float]:
    return [a * math.sin(w * t) - y for t, y in zip(SPRING_T, RPE_Y, strict=True)]


def rpe_weights(a: float, w: float) -> list[float]:
    return [min(1.0, RPE_DELTA / max(abs(r), 1e-15)) for r in rpe_residuals(a, w)]


def rpe_irls(start: tuple[float, float] = (1.0, 1.8), steps: int = 8) -> list[tuple[float, ...]]:
    """Weighted Gauss–Newton: (J'WJ) d = -J'W r with Huber weights; rows (a, ω, Huber, SS, r, w)."""
    a, w = start
    rows = []
    for _ in range(steps + 1):
        r = rpe_residuals(a, w)
        weights = rpe_weights(a, w)
        rows.append(
            (
                a,
                w,
                sum(rpe_huber(ri) for ri in r),
                sum(ri * ri for ri in r),
                r[RPE_BAD],
                weights[RPE_BAD],
            )
        )
        j = [(math.sin(w * t), a * t * math.cos(w * t)) for t in SPRING_T]
        m11 = sum(wi * ji[0] * ji[0] for wi, ji in zip(weights, j, strict=True))
        m12 = sum(wi * ji[0] * ji[1] for wi, ji in zip(weights, j, strict=True))
        m22 = sum(wi * ji[1] * ji[1] for wi, ji in zip(weights, j, strict=True))
        g1 = sum(wi * ji[0] * ri for wi, ji, ri in zip(weights, j, r, strict=True))
        g2 = sum(wi * ji[1] * ri for wi, ji, ri in zip(weights, j, r, strict=True))
        det = m11 * m22 - m12 * m12
        a += (-m22 * g1 + m12 * g2) / det
        w += (m12 * g1 - m11 * g2) / det
    return rows


def _rpe_profile_svg() -> str:
    squares = rpe_valleys(rpe_squares_profile)
    huber = rpe_valleys(rpe_huber_profile)
    clean = rpe_valleys(rpe_clean_profile)
    sq_best = min(squares, key=lambda v: v[1])
    hu_best = min(huber, key=lambda v: v[1])
    near = min(squares, key=lambda v: abs(v[0] - 2.0))
    parts = _open(
        "外れた1点で、最も深い谷が入れ替わる",
        (
            "角周波数ωを固定し、振幅aを最もよく選んだときの損失。2.5秒の読みを1.7と記録した8点。"
            f"① 二乗和：最も深い谷はω={sq_best[0]:.2f}（{sq_best[1]:.2f}）、"
            f"ω=2付近の谷はω={near[0]:.2f}（{near[1]:.2f}）。"
            f"破線は符号が正しい8点の二乗和で、最も深い谷はω={clean[0][0]:.2f}。"
            f"② Huber損失（尺度0.3）：最も深い谷はω={hu_best[0]:.2f}（{hu_best[1]:.3f}）。"
        ),
        612,
    )
    px = _scale(0.0, 2 * math.pi, 64, 416)
    # sin(2π t) is 0 at every reading, so the amplitude is undefined at ω = 2π itself.
    ws = [0.2 + (2 * math.pi - 0.25) * i / 400 for i in range(401)]
    for tick in range(7):
        parts.append(_text(px(tick), 292, str(tick), "tick", "middle"))
        parts.append(_text(px(tick), 572, str(tick), "tick", "middle"))
    parts.append(_text(20, 64, "① 二乗和"))
    sy = _scale(0.0, 16.0, 272, 84)
    parts.append(f'<path d="M64 84V272H416" fill="none" stroke="{GRID}"/>')
    for value in (0, 5, 10, 15):
        parts.append(_text(56, sy(value) + 5, str(value), "tick", "end"))
    clean_curve = [(px(w), sy(rpe_clean_profile(w)[0])) for w in ws]
    parts.append(_polyline(clean_curve, MUTED, 1.5).replace("/>", ' stroke-dasharray="5 4"/>'))
    parts.append(_polyline([(px(w), sy(rpe_squares_profile(w)[0])) for w in ws], POINT, 3))
    for w, value in squares:
        color = POINT if (w, value) == sq_best else RING
        parts.append(f'<circle cx="{px(w):.1f}" cy="{sy(value):.1f}" r="6" fill="{color}"/>')
    parts.append(
        _text(
            px(sq_best[0]) - 10,
            sy(sq_best[1]) + 26,
            f"ω={sq_best[0]:.2f}：{sq_best[1]:.2f}",
            anchor="end",
        )
    )
    parts.append(_text(px(near[0]) + 10, sy(near[1]) + 24, f"ω={near[0]:.2f}：{near[1]:.2f}"))
    parts.append(_text(20, 318, "実線：記録どおりの8点　破線：符号が正しい8点", "tick"))

    parts.append(_text(20, 344, f"② Huber損失（尺度 {RPE_DELTA:g}）"))
    hy = _scale(0.0, 3.2, 552, 364)
    parts.append(f'<path d="M64 364V552H416" fill="none" stroke="{GRID}"/>')
    for value in (0, 1, 2, 3):
        parts.append(_text(56, hy(value) + 5, str(value), "tick", "end"))
    parts.append(_polyline([(px(w), hy(rpe_huber_profile(w)[0])) for w in ws], UPDATE, 3))
    for w, value in huber:
        color = UPDATE if (w, value) == hu_best else RING
        parts.append(f'<circle cx="{px(w):.1f}" cy="{hy(value):.1f}" r="6" fill="{color}"/>')
    parts.append(
        _text(px(hu_best[0]) + 10, hy(hu_best[1]) + 24, f"ω={hu_best[0]:.2f}：{hu_best[1]:.2f}")
    )
    parts.append(_text(416, 596, "角周波数 ω", "tick", "end"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


def _rpe_weights_svg() -> str:
    a_h, w_h = rpe_irls()[-1][:2]
    sq_best = min(rpe_valleys(rpe_squares_profile), key=lambda v: v[1])
    a_s = rpe_squares_profile(sq_best[0])[1]
    weights = rpe_weights(a_h, w_h)
    parts = _open(
        "Huberの当てはめと、各観測の重み",
        (
            "① 8つの観測と2本の曲線。2.5秒の読みは −1.7 を 1.7 と記録したもの。"
            f"Huber損失の当てはめは a={a_h:.2f}、ω={w_h:.2f}、"
            f"二乗和で最も深い谷は a={a_s:.2f}、ω={sq_best[0]:.2f}。"
            "② Huberの当てはめでの各観測の重み min(1, 0.3/|r|)。"
            f"2.5秒の観測だけが {weights[RPE_BAD]:.3f}、ほかの7つは1。"
        ),
        604,
    )
    parts.append(_text(20, 64, "① 観測点と曲線"))
    px = _scale(0.0, 3.5, 64, 410)
    py = _scale(-2.6, 2.6, 290, 84)
    parts.append(f'<path d="M64 84V290H410" fill="none" stroke="{GRID}"/>')
    parts.append(f'<path d="M64 {py(0):.1f}H410" stroke="{GRID}" stroke-width="1"/>')
    for value in (-2, 0, 2):
        parts.append(_text(56, py(value) + 5, f"{value}".replace("-", "−"), "tick", "end"))
    for value in (0, 1, 2, 3):
        parts.append(_text(px(value), 310, str(value), "tick", "middle"))
    parts.append(_text(410, 332, "時刻 t（秒）", "tick", "end"))
    ts = [3.5 * i / 280 for i in range(281)]
    parts.append(
        _polyline([(px(t), py(a_s * math.sin(sq_best[0] * t))) for t in ts], POINT, 2).replace(
            "/>", ' stroke-dasharray="6 4"/>'
        )
    )
    parts.append(_polyline([(px(t), py(a_h * math.sin(w_h * t))) for t in ts], UPDATE, 3))
    for index, (t, y) in enumerate(zip(SPRING_T, RPE_Y, strict=True)):
        if index == RPE_BAD:
            parts.append(
                f'<circle cx="{px(t):.1f}" cy="{py(y):.1f}" r="9" fill="none" '
                f'stroke="{VIOLATION}" stroke-width="2.5"/>'
            )
        parts.append(f'<circle cx="{px(t):.1f}" cy="{py(y):.1f}" r="5" fill="{INK}"/>')
    parts.append(_polyline([(20, 360 - 5), (42, 360 - 5)], UPDATE, 3))
    parts.append(_text(48, 360, f"Huber：ω={w_h:.2f}", "tick"))
    parts.append(
        _polyline([(210, 360 - 5), (232, 360 - 5)], POINT, 2).replace(
            "/>", ' stroke-dasharray="6 4"/>'
        )
    )
    parts.append(_text(238, 360, f"二乗和：ω={sq_best[0]:.2f}", "tick"))
    parts.append(
        f'<circle cx="31" cy="379" r="8" fill="none" stroke="{VIOLATION}" stroke-width="2.5"/>'
    )
    parts.append(_text(48, 384, "2.5秒の読み：記録は1.7（本来は −1.7）", "tick"))

    parts.append(_text(20, 422, "② Huberの当てはめでの重み"))
    by = _scale(0.0, 1.0, 536, 446)
    bx = _scale(-0.25, 3.75, 64, 410)
    parts.append(f'<path d="M64 446V536H410" fill="none" stroke="{GRID}"/>')
    for value in (0, 1):
        parts.append(_text(56, by(value) + 5, str(value), "tick", "end"))
    for index, (t, weight) in enumerate(zip(SPRING_T, weights, strict=True)):
        color = VIOLATION if index == RPE_BAD else LINE
        top = by(weight)
        parts.append(
            f'<rect x="{bx(t) - 10:.1f}" y="{top:.1f}" width="20" height="{536 - top:.1f}" '
            f'fill="{color}"/>'
        )
        parts.append(_text(bx(t), 556, f"{t:g}", "tick", "middle"))
    parts.append(
        _text(
            bx(SPRING_T[RPE_BAD]),
            by(weights[RPE_BAD]) - 8,
            f"{weights[RPE_BAD]:.3f}",
            anchor="middle",
        )
    )
    parts.append(_text(410, 584, "観測の時刻 t（秒）", "tick", "end"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


# SAT and MaxSAT (content/concepts/sat-maxsat.md): whom to invite to a weekend study group.
# Variables 1..5 are A..E (true = invite). Clauses list signed variable numbers.
SAT_NAMES = "ABCDE"
SAT_HARD = (
    ((1, 2), "鍵"),  # only A and B hold the key
    ((-1, -3), "店番A・C"),  # A and C keep the same shop
    ((-2, 4), "車"),  # B comes in D's car
    ((-4, -5), "店番D・E"),  # D and E keep the same shop
)
SAT_SOFT = (((3,), 3), ((5,), 2), ((1,), 2))  # wishes: C 3, E 2, A 2


def sat_holds(clause: Sequence[int], x: Sequence[bool]) -> bool:
    return any((lit > 0) == x[abs(lit) - 1] for lit in clause)


def sat_weight(x: Sequence[bool]) -> int:
    return sum(w for clause, w in SAT_SOFT if sat_holds(clause, x))


def sat_label(x: Sequence[bool]) -> str:
    return "".join(n for n, b in zip(SAT_NAMES, x, strict=True) if b) or "なし"


def sat_feasible() -> list[tuple[bool, ...]]:
    return [
        x
        for x in itertools.product((False, True), repeat=5)
        if all(sat_holds(clause, x) for clause, _ in SAT_HARD)
    ]


def sat_implications(first: int) -> list[tuple[int, str]]:
    """Unit propagation from one decided literal over the hard clauses: (literal, reason)."""
    value = {abs(first): first > 0}
    chain = [(first, "")]
    changed = True
    while changed:
        changed = False
        for clause, reason in SAT_HARD:
            if any(value.get(abs(lit)) == (lit > 0) for lit in clause):
                continue
            free = [lit for lit in clause if abs(lit) not in value]
            if len(free) == 1:
                value[abs(free[0])] = free[0] > 0
                chain.append((free[0], reason))
                changed = True
    return chain


def sat_greedy() -> tuple[bool, ...]:
    """Grant the wishes heaviest first, keeping each one only if some feasible plan remains."""
    plans = sat_feasible()
    for clause, _ in sorted(SAT_SOFT, key=lambda item: -item[1]):
        kept = [x for x in plans if sat_holds(clause, x)]
        plans = kept or plans
    return max(plans, key=sat_weight)


def _sat_literal(lit: int) -> str:
    return ("" if lit > 0 else "¬") + SAT_NAMES[abs(lit) - 1]


def _sat_grid_svg() -> str:
    feasible = set(sat_feasible())
    best = max(feasible, key=sat_weight)
    greedy = sat_greedy()
    parts = _open(
        "32通りの呼び方と、希望の重み",
        (
            "5人A〜Eを呼ぶかどうかの32通り。行はAとBの呼び方、列はC・D・Eの呼び方。"
            f"決まり（鍵・店番・車・店番）を守るのは{len(feasible)}通りで、"
            "守る組には、かなった希望の重み（Cが3、Eが2、Aが2）の合計を書く。"
            f"最も重いのは{sat_label(best)}の{sat_weight(best)}、"
            f"重い希望から順に決めると{sat_label(greedy)}の{sat_weight(greedy)}。"
        ),
        380,
    )
    left, top, cell_w, cell_h = 92, 96, 41, 50
    columns = list(itertools.product((False, True), repeat=3))
    rows = list(itertools.product((False, True), repeat=2))
    parts.append(_text(20, 64, "列：C・D・Eのうち呼ぶ人　行：A・Bのうち呼ぶ人", "tick"))
    for j, cde in enumerate(columns):
        name = "".join(n for n, b in zip("CDE", cde, strict=True) if b) or "−"
        parts.append(_text(left + cell_w * (j + 0.5), top - 8, name, "tick", "middle"))
    for i, ab in enumerate(rows):
        name = "".join(n for n, b in zip("AB", ab, strict=True) if b) or "−"
        parts.append(_text(left - 10, top + cell_h * (i + 0.5) + 5, name, "tick", "end"))
        for j, cde in enumerate(columns):
            x = (*ab, *cde)
            cx, cy = left + cell_w * j, top + cell_h * i
            if x in feasible:
                fill = "#ffffff"
                parts.append(
                    f'<rect x="{cx + 2}" y="{cy + 2}" width="{cell_w - 4}" height="{cell_h - 4}" '
                    f'rx="6" fill="{fill}" stroke="{LINE}" stroke-width="1.5"/>'
                )
                parts.append(
                    _text(cx + cell_w / 2, cy + cell_h / 2 + 6, str(sat_weight(x)), "", "middle")
                )
            else:
                parts.append(
                    f'<rect x="{cx + 2}" y="{cy + 2}" width="{cell_w - 4}" height="{cell_h - 4}" '
                    f'rx="6" fill="#e4e7e1"/>'
                )
                parts.append(_text(cx + cell_w / 2, cy + cell_h / 2 + 5, "×", "tick", "middle"))
            for plan, color in ((best, UPDATE), (greedy, POINT)):
                if x == plan:
                    parts.append(
                        f'<rect x="{cx}" y="{cy}" width="{cell_w}" height="{cell_h}" rx="8" '
                        f'fill="none" stroke="{color}" stroke-width="3.5"/>'
                    )
    bottom = top + cell_h * 4
    parts.append(
        f'<rect x="20" y="{bottom + 20}" width="18" height="18" rx="4" fill="none" '
        f'stroke="{UPDATE}" stroke-width="3"/>'
    )
    parts.append(_text(46, bottom + 35, f"最も重い：{sat_label(best)}（{sat_weight(best)}）"))
    parts.append(
        f'<rect x="230" y="{bottom + 20}" width="18" height="18" rx="4" fill="none" '
        f'stroke="{POINT}" stroke-width="3"/>'
    )
    parts.append(_text(256, bottom + 35, f"重い順：{sat_label(greedy)}（{sat_weight(greedy)}）"))
    parts.append(_text(20, bottom + 64, "×：決まりを一つ以上破る組", "tick"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


def _sat_chain_svg() -> str:
    parts = _open(
        "1人を決めると、残りが芋づる式に決まる",
        (
            "決まりの節だけで単位伝播した結果。"
            "① Cを呼ぶと、店番A・Cで¬A、鍵でB、車でD、店番D・Eで¬E。"
            "② Eを呼ぶと、店番D・Eで¬D、車で¬B、鍵でA、店番A・Cで¬C。"
            "CとEは両方は呼べない。"
        ),
        330,
    )
    for row, (first, title) in enumerate(((3, "① Cを呼ぶと"), (5, "② Eを呼ぶと"))):
        base = 64 + 130 * row
        parts.append(_text(20, base, title))
        chain = sat_implications(first)
        step = (420 - 20) / len(chain)
        for index, (lit, reason) in enumerate(chain):
            cx = 20 + step * (index + 0.5)
            color = INK if index == 0 else (POINT if lit > 0 else MUTED)
            width = 3.5 if index == 0 else 2.5
            parts.append(
                f'<rect x="{cx - 30:.1f}" y="{base + 22}" width="60" height="44" rx="10" '
                f'fill="#ffffff" stroke="{color}" stroke-width="{width}"/>'
            )
            parts.append(_text(cx, base + 51, _sat_literal(lit), "", "middle"))
            if index:
                arrow = cx - step + 30
                tip = cx - 32
                parts.append(
                    f'<path d="M{arrow:.1f} {base + 44}H{tip - 6:.1f}" stroke="{MUTED}" '
                    'stroke-width="2"/>'
                )
                parts.append(
                    f'<path d="M{tip - 8:.1f} {base + 39}L{tip:.1f} {base + 44}'
                    f'L{tip - 8:.1f} {base + 49}Z" fill="{MUTED}"/>'
                )
                parts.append(_text(cx - step / 2, base + 92, reason, "tick", "middle"))
    parts.append(_text(20, 316, "¬A は「Aを呼ばない」。箱の間の文字は使った決まり", "tick"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


# Trajectory optimization (content/concepts/trajectory-optimization.md): a warehouse robot
# moves 4 m in 4 s from rest to rest around a pillar. The acceleration u is held constant
# on each of N intervals (zero-order hold), so p and v are linear in u and the path between
# grid points is a known parabola. Cost: h * sum |u_k|^2. Pillar: centre (2, -0.3), radius 0.8.
TRAJ_START, TRAJ_GOAL = (0.0, 0.0), (4.0, 0.0)
TRAJ_PILLAR, TRAJ_RADIUS = (2.0, -0.3), 0.8
TRAJ_T = 4.0


@functools.cache
def traj_solve(n: int, side: float = 1.0) -> tuple[float, tuple[tuple[float, float], ...]]:
    """Augmented Lagrangian with Gauss–Newton steps; returns (cost, u_0..u_{n-1})."""
    h = TRAJ_T / n
    coef = [[h * h * (k - j - 0.5) if j < k else 0.0 for j in range(n)] for k in range(n + 1)]
    size = 2 * n

    def position(u: list[float], k: int) -> tuple[float, float]:
        return (
            TRAJ_START[0] + sum(coef[k][j] * u[j] for j in range(n)),
            TRAJ_START[1] + sum(coef[k][j] * u[n + j] for j in range(n)),
        )

    ends = [
        [*coef[n], *[0.0] * n],
        [*[0.0] * n, *coef[n]],
        [*[h] * n, *[0.0] * n],
        [*[0.0] * n, *[h] * n],
    ]
    target = [TRAJ_GOAL[0] - TRAJ_START[0], TRAJ_GOAL[1] - TRAJ_START[1], 0.0, 0.0]
    # Start from the controls that best follow an arc on the chosen side of the pillar.
    hess = [[2 * h if i == j else 0.0 for j in range(size)] for i in range(size)]
    rhs = [0.0] * size
    for k in range(n + 1):
        arc = (4 * k / n, side * 1.2 * math.sin(math.pi * k / n))
        for d in range(2):
            for i in range(n):
                rhs[d * n + i] += 2 * coef[k][i] * (arc[d] - TRAJ_START[d])
                for j in range(n):
                    hess[d * n + i][d * n + j] += 2 * coef[k][i] * coef[k][j]
    u = _solve_linear(hess, rhs)
    lam_end, lam, mu, last = [0.0] * 4, [0.0] * (n + 1), 10.0, math.inf

    def gaps(u: list[float]) -> list[float]:
        return [
            (px - TRAJ_PILLAR[0]) ** 2 + (py - TRAJ_PILLAR[1]) ** 2 - TRAJ_RADIUS**2
            for px, py in (position(u, k) for k in range(n + 1))
        ]

    def misses(u: list[float]) -> list[float]:
        return [
            sum(r[j] * u[j] for j in range(size)) - t for r, t in zip(ends, target, strict=True)
        ]

    def merit(u: list[float]) -> float:
        value = h * sum(x * x for x in u)
        value += sum(m * e + 0.5 * mu * e * e for m, e in zip(lam_end, misses(u), strict=True))
        for m, g in zip(lam, gaps(u), strict=True):
            value += (max(0.0, m - mu * g) ** 2 - m * m) / (2 * mu)
        return value

    for _ in range(80):
        for _ in range(50):
            grad = [2 * h * x for x in u]
            hess = [[2 * h if i == j else 0.0 for j in range(size)] for i in range(size)]
            rows = [(lam_end[i] + mu * e, ends[i]) for i, e in enumerate(misses(u))]
            for k, g in enumerate(gaps(u)):
                weight = max(0.0, lam[k] - mu * g)
                if weight > 0:
                    px, py = position(u, k)
                    dx, dy = 2 * (px - TRAJ_PILLAR[0]), 2 * (py - TRAJ_PILLAR[1])
                    rows.append(
                        (-weight, [dx * c for c in coef[k][:n]] + [dy * c for c in coef[k][:n]])
                    )
            for scale, row in rows:
                nonzero = [i for i in range(size) if row[i]]
                for i in nonzero:
                    grad[i] += scale * row[i]
                    for j in nonzero:
                        hess[i][j] += mu * row[i] * row[j]
            step = _solve_linear(hess, [-g for g in grad])
            slope = sum(g * s for g, s in zip(grad, step, strict=True))
            base, t = merit(u), 1.0
            while (
                merit([x + t * s for x, s in zip(u, step, strict=True)]) > base + 1e-4 * t * slope
            ):
                t *= 0.5
                if t < 1e-10:
                    break
            u = [x + t * s for x, s in zip(u, step, strict=True)]
            if max(abs(t * s) for s in step) < 1e-12:
                break
        lam_end = [m + mu * e for m, e in zip(lam_end, misses(u), strict=True)]
        lam = [max(0.0, m - mu * g) for m, g in zip(lam, gaps(u), strict=True)]
        violation = max([abs(e) for e in misses(u)] + [max(0.0, -g) for g in gaps(u)])
        if violation < 1e-11:
            break
        if violation > 0.25 * last:
            mu = min(4 * mu, 1e6)
        last = violation
    cost = h * sum(x * x for x in u)
    return cost, tuple((u[j], u[n + j]) for j in range(n))


def traj_states(n: int, side: float = 1.0) -> list[tuple[float, float, float, float]]:
    """(px, py, vx, vy) at the n+1 grid points."""
    h = TRAJ_T / n
    px, py, vx, vy = *TRAJ_START, 0.0, 0.0
    states = [(px, py, vx, vy)]
    for ux, uy in traj_solve(n, side)[1]:
        px, py = px + h * vx + 0.5 * h * h * ux, py + h * vy + 0.5 * h * h * uy
        vx, vy = vx + h * ux, vy + h * uy
        states.append((px, py, vx, vy))
    return states


def traj_path(n: int, side: float = 1.0, samples: int = 40) -> list[tuple[float, float]]:
    """The continuous path: a parabola on each interval, sampled `samples` times."""
    h = TRAJ_T / n
    points = []
    controls = traj_solve(n, side)[1]
    for (px, py, vx, vy), (ux, uy) in zip(traj_states(n, side), controls, strict=False):
        for s in range(samples):
            tau = h * s / samples
            points.append(
                (px + vx * tau + 0.5 * ux * tau * tau, py + vy * tau + 0.5 * uy * tau * tau)
            )
    points.append(TRAJ_GOAL)
    return points


def traj_clearance(points: Sequence[tuple[float, float]]) -> float:
    return min(math.hypot(x - TRAJ_PILLAR[0], y - TRAJ_PILLAR[1]) for x, y in points)


def _traj_floor(
    parts: list[str], top: float, bottom: float
) -> Callable[[float, float], tuple[float, float]]:
    px = _scale(-0.8, 4.8, 50, 410)
    unit = (410 - 50) / 5.6
    mid = (top + bottom) / 2

    def at(x: float, y: float) -> tuple[float, float]:
        return px(x), mid - unit * (y + 0.3)

    cx, cy = at(*TRAJ_PILLAR)
    parts.append(
        f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{unit * TRAJ_RADIUS:.1f}" fill="#e4e7e1" '
        f'stroke="{MUTED}" stroke-width="1.5"/>'
    )
    parts.append(_text(cx, cy + 5, "柱", "tick", "middle"))
    for (x, y), name in ((TRAJ_START, "出発"), (TRAJ_GOAL, "到着")):
        sx, sy = at(x, y)
        parts.append(
            f'<rect x="{sx - 6:.1f}" y="{sy - 6:.1f}" width="12" height="12" fill="{INK}"/>'
        )
        left = x < TRAJ_PILLAR[0]
        parts.append(
            _text(sx + (-12 if left else 12), sy + 5, name, "tick", "end" if left else "start")
        )
    return at


def _traj_paths_svg() -> str:
    above, below = traj_solve(20, 1.0), traj_solve(20, -1.0)
    parts = _open(
        "柱の上を回る経路と、下を回る経路",
        (
            "搬送ロボットが4秒で4m先へ、止まった状態から止まった状態へ動く。時間を20区間に分け、"
            "区間ごとに一定の加速度を決める。"
            f"① 床の上の経路。柱の上を回る経路は加速度の二乗の積分が{above[0]:.2f}、"
            f"下を回る経路は{below[0]:.2f}。"
            "② 時刻ごとの加速度の大きさ。"
        ),
        612,
    )
    parts.append(_text(20, 64, "① 床の上の経路（m）"))
    at = _traj_floor(parts, 80, 330)
    for side, color, dash in ((-1.0, POINT, ' stroke-dasharray="6 4"'), (1.0, UPDATE, "")):
        parts.append(
            _polyline([at(x, y) for x, y in traj_path(20, side)], color, 3).replace(
                "/>", f"{dash}/>"
            )
        )
        for x, y, _, _ in traj_states(20, side):
            sx, sy = at(x, y)
            parts.append(f'<circle cx="{sx:.1f}" cy="{sy:.1f}" r="3.5" fill="{color}"/>')
    parts.append(
        _text(410, 96, f"上を回る：{above[0]:.2f}", anchor="end").replace(
            "<text ", f'<text style="fill:{UPDATE}" '
        )
    )
    parts.append(
        _text(410, 324, f"下を回る：{below[0]:.2f}", anchor="end").replace(
            "<text ", f'<text style="fill:{POINT}" '
        )
    )

    parts.append(_text(20, 380, "② 加速度の大きさ（m/s²）"))
    tx = _scale(0.0, TRAJ_T, 64, 410)
    ay = _scale(0.0, 3.0, 560, 400)
    parts.append(f'<path d="M64 400V560H410" fill="none" stroke="{GRID}"/>')
    for value in (0, 1, 2, 3):
        parts.append(_text(56, ay(value) + 5, str(value), "tick", "end"))
    for value in (0, 1, 2, 3, 4):
        parts.append(_text(tx(value), 580, str(value), "tick", "middle"))
    parts.append(_text(410, 600, "時刻（秒）", "tick", "end"))
    h = TRAJ_T / 20
    for side, color, dash in ((-1.0, POINT, ' stroke-dasharray="6 4"'), (1.0, UPDATE, "")):
        steps = []
        for k, (ux, uy) in enumerate(traj_solve(20, side)[1]):
            size = math.hypot(ux, uy)
            steps += [(tx(k * h), ay(size)), (tx((k + 1) * h), ay(size))]
        parts.append(_polyline(steps, color, 2.5).replace("/>", f"{dash}/>"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


def _traj_grid_svg() -> str:
    coarse_points = traj_path(5)
    depth = TRAJ_RADIUS - traj_clearance(coarse_points)
    nodes = traj_states(5)
    node_gap = min(math.hypot(x - TRAJ_PILLAR[0], y - TRAJ_PILLAR[1]) for x, y, _, _ in nodes)
    counts = (5, 10, 20, 40)
    parts = _open(
        "格子点の外でも、間で柱に入る",
        (
            "① 5区間で解いた経路。6つの格子点はどれも柱の外（柱の中心から"
            f"{node_gap:.2f}m以上）だが、格子点の間の経路は柱に{100 * depth:.0f}cm入る。"
            "② 区間の数ごとの、加速度の二乗の積分。"
            + "、".join(f"{n}区間 {traj_solve(n)[0]:.2f}" for n in counts)
            + "。5区間だけが柱を通り抜けて安くなっている。"
        ),
        600,
    )
    parts.append(_text(20, 64, "① 5区間で解いた経路"))
    at = _traj_floor(parts, 80, 330)
    inside = [
        p
        for p in coarse_points
        if math.hypot(p[0] - TRAJ_PILLAR[0], p[1] - TRAJ_PILLAR[1]) < TRAJ_RADIUS
    ]
    parts.append(_polyline([at(x, y) for x, y in coarse_points], UPDATE, 3))
    parts.append(
        _polyline([at(x, y) for x, y in inside], VIOLATION, 8).replace(
            "/>", ' stroke-linecap="round"/>'
        )
    )
    for x, y, _, _ in nodes:
        sx, sy = at(x, y)
        parts.append(
            f'<circle cx="{sx:.1f}" cy="{sy:.1f}" r="6" fill="#ffffff" '
            f'stroke="{UPDATE}" stroke-width="3"/>'
        )
    parts.append(
        _text(410, 324, f"赤：柱の中（最大{100 * depth:.0f}cm）", anchor="end").replace(
            "<text ", f'<text style="fill:{VIOLATION}" '
        )
    )
    parts.append(_text(20, 380, "② 区間の数と、加速度の二乗の積分"))
    by = _scale(0.0, 4.0, 540, 400)
    parts.append(f'<path d="M100 400V540H410" fill="none" stroke="{GRID}"/>')
    width = (410 - 100) / len(counts)
    for i, n in enumerate(counts):
        cost = traj_solve(n)[0]
        left = 100 + width * i + 14
        color = VIOLATION if n == 5 else LINE
        parts.append(
            f'<rect x="{left:.1f}" y="{by(cost):.1f}" width="{width - 28:.1f}" '
            f'height="{540 - by(cost):.1f}" fill="{color}"/>'
        )
        parts.append(_text(left + (width - 28) / 2, by(cost) - 8, f"{cost:.2f}", "tick", "middle"))
        parts.append(_text(left + (width - 28) / 2, 560, f"{n}区間", "tick", "middle"))
    for value in (0, 2, 4):
        parts.append(_text(92, by(value) + 5, str(value), "tick", "end"))
    parts.append(_text(20, 590, "赤：格子点の間で柱を通り抜ける解", "tick"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


# Where a solver evaluates (content/concepts/solver-evaluation-points.md): water levels of a
# draining tank, fitted by the outlet area a [m^2] and the inflow q [m^3/s]. The tool solves the
# ODE A dh/dt = q - a sqrt(2 g h) with solve_ivp and fails when the tank runs dry.
EVAL_START = (1e-4, 1e-4)
# Points SciPy 1.18.1 passed to the tool, as recorded by the article's Python block. The test
# tests/test_lesson_figures.py reruns SciPy and checks that these sequences still hold.
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


# Written versus real constraints (content/concepts/written-and-real-constraints.md): the same
# tank. The tool fails when the tank runs dry within the 30 minutes; in the (a, q) plane that
# region lies under a curve that the dry time T(a, q) = 1800 s draws for q <= 0.
CON_SPAN = 1800.0
CON_K = math.sqrt(2 * 9.81)
# Points from solver-evaluation-points (fmin's 13th to 15th, the clipped 15th) and the BFGS
# answer when a failure returns 100, recorded with SciPy 1.18.1 and checked by the tests.
CON_FMIN = ((0.000192344, -1.4375e-5), (0.000220156, -3.5625e-5), (0.000265547, -8.46875e-5))
CON_CLIPPED = (0.000265547, 0.0)
CON_PENALTY_100 = (-1.11572e-5, -5.88288e-4)
CON_ANSWER = (0.000401, 0.000501)


def con_dry_time(a: float, q: float) -> float:
    """Seconds until a 1 m tank of area 1 m^2 runs dry under A dh/dt = q - a sqrt(2 g h).

    With s = sqrt(h) the time is the integral of 2 s ds / (a k s - q) from 0 to 1, k = sqrt(2 g).
    It is infinite when the level never reaches 0 (q > 0, or an outlet that adds water faster
    than q removes it).
    """
    b, c = a * CON_K, -q
    if c < 0 or b + c <= 0:
        return math.inf
    if c == 0:
        return 2 / b
    if abs(b) < 1e-15:
        return 1 / c
    return (2 / b) * (1 - (c / b) * math.log((b + c) / c))


def con_critical_area() -> float:
    """Outlet area above which the tank runs dry within the span when q = 0."""
    return 2 / (CON_SPAN * CON_K)


def con_boundary_q(a: float) -> float:
    """Inflow q <= 0 at which the tank runs dry exactly at the end of the span."""
    if a >= con_critical_area():
        return 0.0
    lo, hi = -5e-3, 0.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if con_dry_time(a, mid) < CON_SPAN:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def _con_plane_svg() -> str:
    crit = con_critical_area()
    parts = _open(
        "ありうる値と、ツールが計算できる値",
        (
            "流出口の面積 a と流入量 q（どちらも×10⁻⁴）の平面。"
            "緑は、ありうる値 a≥0、q≥0。赤は、30分のうちにタンクが空になり、ツールが失敗する値で、"
            f"q=0 の線の上でも a が {crit * 1e4:.2f}×10⁻⁴ より大きければ失敗する。"
            "どちらでもない白い部分は、ツールが値を返すのにありえない値。"
            "白抜きの丸は fmin の13回目と14回目で、q が負なのに計算された。"
            "×は fmin の15回目と、下限0の Nelder–Mead の15回目で、ツールが失敗した。"
            "◆は、失敗した点に100を返した BFGS の答えで、a も q も負。"
            "●は記録を作った値の近くの答え。"
        ),
        478,
    )
    px = _scale(-1.0, 5.0, 64, 410)
    py = _scale(-9.0, 6.0, 386, 70)
    left, right, top, bottom = px(-1.0), px(5.0), py(6.0), py(-9.0)
    parts.append(
        f'<rect x="{px(0):.1f}" y="{top:.1f}" width="{right - px(0):.1f}" '
        f'height="{py(0) - top:.1f}" fill="{RING}" fill-opacity="0.35"/>'
    )
    curve = [
        (px(a * 1e4), py(max(con_boundary_q(a) * 1e4, -9.0)))
        for a in (-1e-4 + i * (crit + 1e-4) / 120 for i in range(121))
    ]
    region = [(left, bottom), *curve, (right, py(0)), (right, bottom)]
    joined = " ".join(f"{x:.2f},{y:.2f}" for x, y in region)
    parts.append(f'<polygon points="{joined}" fill="{VIOLATION}" fill-opacity="0.16"/>')
    parts.append(_polyline(curve, VIOLATION, 2))
    parts.append(
        f'<path d="M{px(crit * 1e4):.1f} {py(0):.1f}H{right:.1f}" stroke="{VIOLATION}" '
        'stroke-width="4"/>'
    )
    parts.append(
        f'<path d="M{left:.1f} {top:.1f}V{bottom:.1f}H{right:.1f}" fill="none" stroke="{GRID}"/>'
    )
    parts.append(f'<path d="M{left:.1f} {py(0):.1f}H{right:.1f}" stroke="{MUTED}"/>')
    parts.append(f'<path d="M{px(0):.1f} {top:.1f}V{bottom:.1f}" stroke="{MUTED}"/>')
    for tick in (-1, 0, 1, 2, 3, 4, 5):
        parts.append(_text(px(tick), bottom + 20, f"{tick}".replace("-", "−"), "tick", "middle"))
    for tick in (-8, -6, -4, -2, 0, 2, 4, 6):
        parts.append(_text(left - 8, py(tick) + 5, f"{tick}".replace("-", "−"), "tick", "end"))
    parts.append(_text(px(0.3), py(4.9), "ありうる値", "note"))
    parts.append(_text(px(2.6), py(-4.0), "ツールが失敗", "tick"))
    for row, label in enumerate(("計算できるが", "ありえない")):
        parts.append(
            f'<text x="{px(-0.9):.1f}" y="{py(-1.4 - 1.1 * row):.1f}" class="tick" '
            f'paint-order="stroke" stroke="#f7f8f3" stroke-width="5">{label}</text>'
        )
    ax, aq = CON_ANSWER
    parts.append(f'<circle cx="{px(ax * 1e4):.1f}" cy="{py(aq * 1e4):.1f}" r="6" fill="{LINE}"/>')
    parts.append(_text(px(ax * 1e4) - 12, py(aq * 1e4) + 5, "記録に合う答え", "tick", "end"))
    for a, q in CON_FMIN[:2]:
        parts.append(
            f'<circle cx="{px(a * 1e4):.1f}" cy="{py(q * 1e4):.1f}" r="5" fill="#ffffff" '
            f'stroke="{POINT}" stroke-width="2.5"/>'
        )
    for a, q in (CON_FMIN[2], CON_CLIPPED):
        x, y = px(a * 1e4), py(q * 1e4)
        parts.append(
            f'<path d="M{x - 6:.1f} {y - 6:.1f}L{x + 6:.1f} {y + 6:.1f}M{x + 6:.1f} {y - 6:.1f}'
            f'L{x - 6:.1f} {y + 6:.1f}" stroke="{INK}" stroke-width="3"/>'
        )
    pa, pq = CON_PENALTY_100
    x, y = px(pa * 1e4), py(pq * 1e4)
    parts.append(
        f'<path d="M{x:.1f} {y - 8:.1f}L{x + 8:.1f} {y:.1f}L{x:.1f} {y + 8:.1f}'
        f'L{x - 8:.1f} {y:.1f}Z" '
        f'fill="{UPDATE}" stroke="{INK}" stroke-width="1"/>'
    )
    parts.append(_text(x + 12, y + 5, "失敗を100にした答え", "tick"))
    parts.append(_text(20, bottom + 44, "横軸 a、縦軸 q（どちらも×10⁻⁴）", "tick"))
    legend_y = bottom + 70
    parts.append(
        f'<circle cx="28" cy="{legend_y - 5}" r="5" fill="#ffffff" stroke="{POINT}" '
        'stroke-width="2.5"/>'
    )
    parts.append(_text(42, legend_y, "q が負なのに計算された点", "tick"))
    parts.append(
        f'<path d="M{236} {legend_y - 11}L{248} {legend_y + 1}M{248} {legend_y - 11}'
        f'L{236} {legend_y + 1}" stroke="{INK}" stroke-width="3"/>'
    )
    parts.append(_text(256, legend_y, "ツールが失敗した点", "tick"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


# Steps from the inner solver (content/concepts/inner-solver-error.md): the same tank with q
# fixed at 0.000501, solved by solve_ivp's default RK45 at rtol = 1e-3. INNER_E is the tool's
# sum of squares minus the model's (Radau, rtol = 1e-10), in units of 1e-5, at
# a = 0.00031, 0.000311, ..., 0.00049; INNER_RUNS is the number of right-hand-side evaluations
# (sol.nfev) and how many consecutive samples share it. Recorded with SciPy 1.18.1; the tests
# rerun SciPy and check both.
INNER_Q = 0.000501
INNER_A0, INNER_DA = 0.00031, 0.000001
INNER_E = (
    -24.425,
    -23.426,
    -22.44,
    -21.47,
    -20.515,
    -19.579,
    -18.655,
    -17.743,
    -16.845,
    -15.961,
    -15.092,
    -14.235,
    -13.386,
    -12.542,
    -11.703,
    -10.864,
    -10.012,
    -9.127,
    -8.156,
    -13.429,
    -13.158,
    -12.898,
    -12.648,
    -12.413,
    -12.193,
    -11.987,
    -11.796,
    -11.62,
    -11.462,
    -11.32,
    -11.195,
    -11.089,
    -11.002,
    -10.936,
    -10.892,
    -10.87,
    -10.872,
    -10.899,
    -10.951,
    -11.031,
    -11.139,
    -11.278,
    -11.449,
    -11.384,
    -11.071,
    -10.759,
    -10.45,
    -10.144,
    -9.84,
    -9.538,
    -9.24,
    -8.946,
    -8.654,
    -8.365,
    -8.079,
    -7.797,
    -7.518,
    -7.242,
    -6.969,
    -6.7,
    -6.435,
    -6.174,
    -5.916,
    -5.662,
    -5.41,
    -5.162,
    -4.917,
    -4.675,
    -4.438,
    -4.205,
    -3.975,
    -3.749,
    -3.527,
    -3.308,
    -3.092,
    -2.881,
    -2.673,
    -2.468,
    -2.267,
    -2.07,
    -1.876,
    -1.685,
    -1.498,
    -1.313,
    -1.132,
    -0.954,
    -0.779,
    -0.606,
    -0.437,
    -0.27,
    -0.104,
    0.058,
    0.22,
    0.38,
    0.538,
    0.696,
    0.855,
    1.013,
    1.173,
    1.335,
    1.5,
    1.669,
    1.843,
    2.024,
    2.213,
    2.412,
    2.625,
    2.85,
    3.015,
    3.179,
    3.341,
    3.502,
    3.661,
    3.819,
    3.975,
    4.129,
    4.282,
    4.434,
    4.586,
    4.736,
    4.884,
    5.031,
    5.176,
    5.32,
    5.463,
    5.604,
    5.744,
    5.883,
    6.022,
    6.157,
    6.291,
    6.423,
    6.553,
    6.683,
    6.811,
    6.939,
    7.065,
    5.946,
    6.03,
    6.113,
    6.196,
    6.279,
    6.361,
    6.443,
    6.527,
    6.611,
    6.696,
    6.783,
    6.873,
    6.966,
    7.063,
    7.166,
    7.265,
    7.328,
    7.389,
    7.449,
    7.509,
    7.567,
    7.625,
    7.682,
    7.74,
    7.797,
    7.853,
    7.909,
    7.964,
    8.018,
    8.073,
    8.127,
    8.18,
    8.232,
    8.286,
    8.339,
    8.393,
    8.448,
    8.502,
    8.553,
    8.604,
    8.654,
    8.704,
    8.752,
    8.802,
)
INNER_RUNS = ((50, 19), (62, 24), (68, 64), (74, 30), (80, 15), (86, 29))
# Where the count changes, found by bisection: (a, sum-of-squares jump). Two of the five
# changes move the result; the other three add only rejected steps.
INNER_JUMPS = ((0.0003288929884, -6.79e-5), (0.0004466880265, -1.23e-5))


def inner_samples() -> list[tuple[float, float, int]]:
    counts = [count for count, length in INNER_RUNS for _ in range(length)]
    return [
        (INNER_A0 + i * INNER_DA, error, count)
        for i, (error, count) in enumerate(zip(INNER_E, counts, strict=True))
    ]


def _inner_steps_svg() -> str:
    samples = inner_samples()
    parts = _open(
        "RK45 で解いた二乗和の、式からのずれ",
        (
            f"流入量 q を {INNER_Q} に固定し、流出口の面積 a を0.00031から0.00049まで動かす。"
            "縦軸は、solve_ivp の既定（RK45、rtol=1e-3）で解いた二乗和から、"
            "細かい許容誤差で解いた二乗和を引いた値（×10⁻⁵）。"
            "線は、右辺を計算した回数が同じ範囲ごとに切れている。回数は"
            + "・".join(str(count) for count, _ in INNER_RUNS)
            + "回と増える。"
            + "、".join(
                f"a={a * 1e4:.3f}×10⁻⁴ で {jump * 1e5:+.2f}×10⁻⁵".replace("-", "−")
                for a, jump in INNER_JUMPS
            )
            + "の段差がある。ほかの3か所では、線は折れるが跳ばない。"
            "答えの a=0.000401 は、回数68回の範囲の中にある。"
        ),
        394,
    )
    px = _scale(3.1, 4.9, 64, 410)
    py = _scale(-26.0, 10.0, 290, 70)
    parts.append(f'<path d="M64 70V290H410" fill="none" stroke="{GRID}"/>')
    parts.append(f'<path d="M64 {py(0):.1f}H410" stroke="{GRID}" stroke-dasharray="5 4"/>')
    for tick in (-20, -10, 0, 10):
        parts.append(_text(56, py(tick) + 5, f"{tick}".replace("-", "−"), "tick", "end"))
    for a_tick in (3.2, 3.6, 4.0, 4.4, 4.8):
        parts.append(_text(px(a_tick), 312, f"{a_tick:.1f}", "tick", "middle"))
    for jump_a, _ in INNER_JUMPS:
        x = px(jump_a * 1e4)
        parts.append(
            f'<path d="M{x:.1f} 70V290" stroke="{VIOLATION}" stroke-width="1.5" '
            'stroke-dasharray="3 3"/>'
        )
    start = 0
    for index, (count, length) in enumerate(INNER_RUNS):
        piece = samples[start : start + length]
        start += length
        color = LINE if count == 68 else POINT
        parts.append(
            _polyline([(px(a * 1e4), py(e)) for a, e, _ in piece], color, 3 if count == 68 else 2.5)
        )
        middle = piece[len(piece) // 2][0] * 1e4
        parts.append(_text(px(middle), 338 + 0 * index, str(count), "tick", "middle"))
    answer_x = px(4.01)
    parts.append(
        f'<path d="M{answer_x - 7:.1f} 298L{answer_x:.1f} 288L{answer_x + 7:.1f} 298Z" '
        f'fill="{UPDATE}"/>'
    )
    parts.append(_text(answer_x + 10, 284, "答え", "tick"))
    first, second = INNER_JUMPS
    parts.append(
        _text(px(first[0] * 1e4) + 6, 92, f"段差 {first[1] * 1e5:.2f}".replace("-", "−"), "tick")
    )
    parts.append(
        _text(
            px(second[0] * 1e4) - 6,
            py(-5),
            f"段差 {second[1] * 1e5:.2f}".replace("-", "−"),
            "tick",
            "end",
        )
    )
    parts.append(_text(20, 362, "目盛りの下の数：右辺を計算した回数。横軸 a（×10⁻⁴）", "tick"))
    parts.append(_text(20, 384, "縦軸 ずれ（×10⁻⁵）。q=0.000501、SciPy 1.18.1", "tick"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


# Distributed consensus (content/concepts/distributed-consensus.md): three hospitals each keep
# their own records (dose above the reference t, effective y) and share one coefficient theta
# in P(effective) = sigma(theta * t). Raw records never leave a hospital.
DC_SITES = {
    "A": ((-1, 1, 2, 3), (0, 1, 0, 1)),
    "B": ((-2, -1, 1, 1, 2), (0, 1, 1, 1, 1)),
    "C": ((-3, -2, -1, 1, 2, 3), (0, 0, 1, 0, 1, 1)),
}


def _dc_sigmoid(value: float) -> float:
    return 1.0 / (1.0 + math.exp(-value))


def dc_loss(site: str, theta: float) -> float:
    """Negative log-likelihood of one hospital's records."""
    ts, ys = DC_SITES[site]
    return sum(math.log1p(math.exp(theta * t)) - y * theta * t for t, y in zip(ts, ys, strict=True))


def _dc_slope(site: str, theta: float) -> float:
    ts, ys = DC_SITES[site]
    return sum(t * (_dc_sigmoid(theta * t) - y) for t, y in zip(ts, ys, strict=True))


def _dc_curvature(site: str, theta: float) -> float:
    ts, _ = DC_SITES[site]
    return sum(t * t * _dc_sigmoid(theta * t) * (1 - _dc_sigmoid(theta * t)) for t in ts)


def _dc_newton(slope: Callable[[float], float], curve: Callable[[float], float]) -> float:
    theta = 0.0
    for _ in range(60):
        theta -= slope(theta) / curve(theta)
    return theta


def dc_local(site: str) -> float:
    return _dc_newton(lambda th: _dc_slope(site, th), lambda th: _dc_curvature(site, th))


def dc_global() -> float:
    return _dc_newton(
        lambda th: sum(_dc_slope(s, th) for s in DC_SITES),
        lambda th: sum(_dc_curvature(s, th) for s in DC_SITES),
    )


def dc_admm(rho: float, rounds: int = 2000) -> list[tuple[dict[str, float], float]]:
    """Consensus ADMM; stops when every hospital is within 1e-3 of z and z is within 1e-3
    of the pooled answer."""
    x = dict.fromkeys(DC_SITES, 0.0)
    u = dict.fromkeys(DC_SITES, 0.0)
    z = 0.0
    target = dc_global()
    history = [(dict(x), z)]
    for _ in range(rounds):
        x = {
            s: _dc_newton(
                lambda th, s=s, z=z, u=u: _dc_slope(s, th) + rho * (th - z + u[s]),
                lambda th, s=s: _dc_curvature(s, th) + rho,
            )
            for s in DC_SITES
        }
        z = sum(x[s] + u[s] for s in DC_SITES) / len(DC_SITES)
        u = {s: u[s] + x[s] - z for s in DC_SITES}
        history.append((dict(x), z))
        if max(abs(x[s] - z) for s in DC_SITES) < 1e-3 and abs(z - target) < 1e-3:
            break
    return history


DC_COLORS = {"A": RING, "B": POINT, "C": UPDATE}


def _dc_losses_svg() -> str:
    local = {s: dc_local(s) for s in DC_SITES}
    best = dc_global()
    mean = sum(local.values()) / 3
    counts = {s: len(DC_SITES[s][0]) for s in DC_SITES}
    weighted = sum(counts[s] * local[s] for s in DC_SITES) / sum(counts.values())
    parts = _open(
        "病院ごとの損失と、3病院の合計",
        (
            "効く確率 σ(θt) の係数 θ ごとの損失。① 病院ごとの損失（底の値を0にそろえた）。"
            + "、".join(f"病院{s}の底は θ={local[s]:.2f}" for s in DC_SITES)
            + "。② 3病院の損失の合計。底は "
            f"θ={best:.3f}。病院ごとの答えの平均 {mean:.3f}、患者の数で重み付けした平均 "
            f"{weighted:.3f} はどちらも合計の底からずれる。"
        ),
        610,
    )
    px = _scale(0.0, 2.0, 64, 410)
    for tick in (0, 0.5, 1, 1.5, 2):
        parts.append(_text(px(tick), 292, f"{tick:g}", "tick", "middle"))
    thetas = [2.0 * i / 200 for i in range(201)]
    parts.append(_text(20, 64, "① 病院ごとの損失（底を0にそろえる）"))
    ly = _scale(0.0, 1.2, 272, 84)
    parts.append(f'<path d="M64 84V272H410" fill="none" stroke="{GRID}"/>')
    for value in (0, 0.5, 1):
        parts.append(_text(56, ly(value) + 5, f"{value:g}", "tick", "end"))
    for index, s in enumerate(DC_SITES):
        floor = dc_loss(s, local[s])
        points = [
            (px(t), ly(dc_loss(s, t) - floor)) for t in thetas if dc_loss(s, t) - floor <= 1.2
        ]
        parts.append(_polyline(points, DC_COLORS[s], 3))
        parts.append(
            f'<circle cx="{px(local[s]):.1f}" cy="{ly(0):.1f}" r="6" fill="{DC_COLORS[s]}"/>'
        )
        x0 = 20 + 132 * index
        parts.append(_polyline([(x0, 316 - 5), (x0 + 20, 316 - 5)], DC_COLORS[s], 3))
        parts.append(_text(x0 + 26, 316, f"病院{s}：{local[s]:.2f}", "tick"))
    parts.append(_text(20, 364, "② 3病院の損失の合計（θ=0.5〜1を拡大）"))
    qx = _scale(0.5, 1.0, 64, 410)
    zoom = [0.5 + 0.5 * i / 200 for i in range(201)]
    total = [sum(dc_loss(s, t) for s in DC_SITES) for t in zoom]
    low = min(total)
    sy = _scale(0.0, 0.3, 552, 384)
    parts.append(f'<path d="M64 384V552H410" fill="none" stroke="{GRID}"/>')
    for value in (0, 0.1, 0.2, 0.3):
        parts.append(_text(56, sy(value) + 5, f"{value:g}", "tick", "end"))
    for tick in (0.5, 0.6, 0.7, 0.8, 0.9, 1.0):
        parts.append(_text(qx(tick), 572, f"{tick:g}", "tick", "middle"))
    curve = [(qx(t), sy(min(v - low, 0.3))) for t, v in zip(zoom, total, strict=True)]
    parts.append(_polyline(curve, LINE, 3))
    marks = (
        (best, f"合計の底 {best:.2f}", 120, 470, True),
        (mean, f"平均 {mean:.2f}", 250, 440, False),
        (weighted, f"患者の数の重み {weighted:.2f}", 280, 470, False),
    )
    for theta, label, tx, ty, solid in marks:
        value = sum(dc_loss(s, theta) for s in DC_SITES) - low
        cx, cy = qx(theta), sy(value)
        parts.append(
            f'<path d="M{cx:.1f} {cy - 6:.1f}L{tx:.1f} {ty + 6:.1f}" stroke="{MUTED}" '
            'stroke-width="1"/>'
        )
        fill = LINE if solid else "#ffffff"
        parts.append(
            f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="5.5" fill="{fill}" stroke="{INK}" '
            'stroke-width="1.5"/>'
        )
        parts.append(_text(tx, ty, label, "tick", "middle"))
    parts.append(_text(410, 596, "係数 θ", "tick", "end"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


DC_RHOS = (0.1, 0.5, 1.0, 2.0, 5.0, 20.0, 100.0)


def _dc_admm_svg() -> str:
    history = dc_admm(2.0)
    best = dc_global()
    parts = _open(
        "合意へ近づく様子と、罰則係数",
        (
            f"① 罰則係数 ρ=2 のADMMで、3病院の係数と共通の値 z が {best:.3f} へ近づく。"
            f"{len(history) - 1}回のやり取りで、各病院の値と z の差が0.001未満、"
            f"z が {best:.3f} から0.001以内になる。"
            "② ρ ごとの、そろうまでのやり取りの回数。"
            + "、".join(f"ρ={rho:g}で{len(dc_admm(rho)) - 1}回" for rho in DC_RHOS)
            + "。"
        ),
        612,
    )
    parts.append(_text(20, 64, "① ρ=2 のときの、病院ごとの係数と共通の値 z"))
    px = _scale(0.0, float(len(history) - 1), 64, 410)
    vy = _scale(0.0, 1.0, 272, 84)
    parts.append(f'<path d="M64 84V272H410" fill="none" stroke="{GRID}"/>')
    for value in (0, 0.5, 1):
        parts.append(_text(56, vy(value) + 5, f"{value:g}", "tick", "end"))
    for k in range(0, len(history), 2):
        parts.append(_text(px(k), 292, str(k), "tick", "middle"))
    parts.append(
        f'<path d="M64 {vy(best):.1f}H410" stroke="{GRID}" stroke-width="1.5" '
        'stroke-dasharray="5 4"/>'
    )
    for s in DC_SITES:
        points = [(px(k), vy(x[s])) for k, (x, _) in enumerate(history)]
        parts.append(_polyline(points, DC_COLORS[s], 2.5))
    parts.append(
        _polyline([(px(k), vy(z)) for k, (_, z) in enumerate(history)], INK, 2.5).replace(
            "/>", ' stroke-dasharray="6 4"/>'
        )
    )
    for index, (name, color) in enumerate(
        (*((f"病院{s}", DC_COLORS[s]) for s in DC_SITES), ("z", INK))
    ):
        x0 = 64 + 88 * index
        parts.append(_polyline([(x0, 316 - 5), (x0 + 22, 316 - 5)], color, 2.5))
        parts.append(_text(x0 + 28, 316, name, "tick"))
    parts.append(_text(410, 340, "やり取りの回数", "tick", "end"))

    parts.append(_text(20, 384, "② ρ ごとの、そろうまでの回数"))
    by = _scale(0.0, math.log10(1000.0), 560, 410)
    parts.append(f'<path d="M64 410V560H410" fill="none" stroke="{GRID}"/>')
    for value in (1, 10, 100, 1000):
        parts.append(_text(56, by(math.log10(value)) + 5, str(value), "tick", "end"))
    width = (410 - 64) / len(DC_RHOS)
    for index, rho in enumerate(DC_RHOS):
        count = len(dc_admm(rho)) - 1
        left = 64 + width * index + 8
        top = by(math.log10(count))
        color = INK if rho == 2.0 else LINE
        parts.append(
            f'<rect x="{left:.1f}" y="{top:.1f}" width="{width - 16:.1f}" height="{560 - top:.1f}" '
            f'fill="{color}"/>'
        )
        parts.append(_text(left + (width - 16) / 2, top - 6, str(count), "tick", "middle"))
        parts.append(_text(left + (width - 16) / 2, 580, f"{rho:g}", "tick", "middle"))
    parts.append(_text(410, 602, "罰則係数 ρ（縦は対数目盛）", "tick", "end"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


# Online optimization (content/concepts/online-optimization.md): every morning a shop splits its
# ad budget between media A and B (x = share to A); each day's results per share are known only
# in the evening. Two sequences: alternating days, and an A, A, B pattern.
OL_STEP_HORIZONS = (10, 100, 1000, 10000)


def ol_alternating(days: int) -> list[tuple[float, float]]:
    """(A, B) results: day 1 is (1.5, 1.0), then B wins on even days and A on odd days."""
    return [(1.5, 1.0)] + [((1.0, 2.0) if t % 2 == 0 else (2.0, 1.0)) for t in range(2, days + 1)]


def ol_pattern(days: int) -> list[tuple[float, float]]:
    """(A, B) results repeating A, A, B: A wins two days out of three."""
    return [((1.0, 2.0) if t % 3 == 0 else (2.0, 1.0)) for t in range(1, days + 1)]


def ol_play(results: Sequence[tuple[float, float]], rule: str) -> tuple[list[float], float]:
    """Shares chosen each morning and the regret against the better medium in hindsight."""
    days = len(results)
    x, lead, shares, gained = 0.5, 0.0, [], 0.0
    for a, b in results:
        if rule == "leader":
            x = 0.5 if lead == 0 else (1.0 if lead > 0 else 0.0)
        elif rule == "half":
            x = 0.5
        shares.append(x)
        gained += x * a + (1 - x) * b
        lead += a - b
        if rule == "ogd":
            x = min(1.0, max(0.0, x + (a - b) / math.sqrt(days)))
    best = max(sum(a for a, _ in results), sum(b for _, b in results))
    return shares, best - gained


OL_RULES = (
    ("leader", "勝ち側に全額", POINT),
    ("half", "いつも半分", MUTED),
    ("ogd", "勾配で少しずつ", UPDATE),
)


def _ol_days_svg() -> str:
    days = ol_alternating(10)
    parts = _open(
        "交互に入れ替わる10日間と、毎朝の割合",
        (
            "① 媒体A・Bの1日の成果（広告費1あたり）。1日目はA1.5・B1.0、"
            "その後は偶数日にB、奇数日にAが2倍。"
            "② 毎朝Aに回す割合 x。前日までの合計が多い側に全額を回すと、"
            "2日目から毎日負ける側を選ぶ。"
            "勾配で少しずつ動かす決め方（学習率 η=1/√10）は0.34と0.66の間を行き来する。"
        ),
        560,
    )
    px = _scale(1.0, 10.0, 84, 400)
    for day in range(1, 11):
        parts.append(_text(px(day), 272, str(day), "tick", "middle"))
        parts.append(_text(px(day), 520, str(day), "tick", "middle"))
    parts.append(_text(20, 64, "① 1日の成果"))
    ay = _scale(0.5, 2.0, 252, 84)
    parts.append(f'<path d="M64 84V252H410" fill="none" stroke="{GRID}"/>')
    for value in (1, 2):
        parts.append(_text(56, ay(value) + 5, str(value), "tick", "end"))
    for index, (name, color, dash) in enumerate((("A", LINE, ""), ("B", MUTED, "5 4"))):
        points = [(px(t + 1), ay(r[index])) for t, r in enumerate(days)]
        line = _polyline(points, color, 2.5)
        if dash:
            line = line.replace("/>", f' stroke-dasharray="{dash}"/>')
        parts.append(line)
        for x, y in points:
            parts.append(
                f'<rect x="{x - 4:.1f}" y="{y - 4:.1f}" width="8" height="8" fill="{color}"/>'
            )
        x0 = 100 + 110 * index
        parts.append(_polyline([(x0, 300 - 5), (x0 + 22, 300 - 5)], color, 2.5))
        parts.append(_text(x0 + 28, 300, f"媒体{name}", "tick"))
    parts.append(_text(20, 344, "② 毎朝Aに回す割合 x"))
    xy = _scale(0.0, 1.0, 500, 364)
    parts.append(f'<path d="M64 364V500H410" fill="none" stroke="{GRID}"/>')
    for value in (0, 0.5, 1):
        parts.append(_text(56, xy(value) + 5, f"{value:g}", "tick", "end"))
    for rule, _, color in (OL_RULES[0], OL_RULES[2]):
        shares, _ = ol_play(days, rule)
        points = [(px(t + 1), xy(s)) for t, s in enumerate(shares)]
        parts.append(_polyline(points, color, 2.5))
        for x, y in points:
            parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.5" fill="{color}"/>')
    parts.append(
        _text(20, 548, "紺：前日までの勝ち側に全額", "tick").replace(
            "<text ", f'<text style="fill:{POINT}" '
        )
    )
    parts.append(
        _text(250, 548, "橙：勾配で少しずつ", "tick").replace(
            "<text ", f'<text style="fill:{UPDATE}" '
        )
    )
    parts.append(_text(400, 300, "日", "tick", "end"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


def _ol_regret_svg() -> str:
    sequences = (("① 交互に入れ替わる日", ol_alternating), ("② A・A・Bの繰り返し", ol_pattern))
    regrets = {
        (name, rule): [ol_play(seq(days), rule)[1] for days in OL_STEP_HORIZONS]
        for name, seq in sequences
        for rule, _, _ in OL_RULES
    }
    parts = _open(
        "日数が増えると、後悔はどう増えるか",
        (
            "後悔＝後から見てよかった方の媒体に毎日全額を回した場合との差。"
            "横は日数 T、縦は後悔（どちらも対数目盛）。"
            "破線は √T。"
            + "。".join(
                f"{name}："
                + "、".join(f"{label} {regrets[(name, rule)][1]:g}" for rule, label, _ in OL_RULES)
                + "（T=100）"
                for name, _ in sequences
            )
            + "。"
        ),
        620,
    )
    px = _scale(1.0, 4.0, 84, 400)
    ly = {}
    for panel, (name, _) in enumerate(sequences):
        top = 84 + 260 * panel
        bottom = top + 180
        parts.append(_text(20, top - 20, name))
        ly[name] = _scale(-1.0, 4.0, bottom, top)
        y = ly[name]
        parts.append(f'<path d="M84 {top}V{bottom}H400" fill="none" stroke="{GRID}"/>')
        for exponent in (0, 2, 4):
            parts.append(_text(76, y(exponent) + 5, f"{10**exponent:g}", "tick", "end"))
        for exponent in (1, 2, 3, 4):
            parts.append(_text(px(exponent), bottom + 20, f"{10**exponent:g}", "tick", "middle"))
        root = [(px(e), y(e / 2)) for e in (1, 2, 3, 4)]
        parts.append(_polyline(root, MUTED, 1.5).replace("/>", ' stroke-dasharray="5 4"/>'))
        parts.append(_text(px(4) - 4, y(2) - 10, "√T", "tick", "end"))
        parts.append(_text(92, top + 4, "後悔", "tick"))
        for rule, _, color in OL_RULES:
            points = [
                (px(math.log10(days)), y(math.log10(max(value, 0.1))))
                for days, value in zip(OL_STEP_HORIZONS, regrets[(name, rule)], strict=True)
            ]
            parts.append(_polyline(points, color, 2.5))
            for x, yy in points:
                parts.append(f'<circle cx="{x:.1f}" cy="{yy:.1f}" r="4" fill="{color}"/>')
    for x0, (_, label, color) in zip((20, 210, 310), OL_RULES, strict=True):
        parts.append(
            _text(x0, 604, label, "tick").replace("<text ", f'<text style="fill:{color}" ')
        )
    parts.append(_text(400, 580, "日数 T", "tick", "end"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


# Design of experiments (content/concepts/design-of-experiments.md): six test bakes between
# 160 and 200 degC, coded x = (T - 180) / 20, for a quadratic score model (1, x, x^2).
DOE_DESIGNS = (
    ("等間隔", tuple(-1 + 0.4 * i for i in range(6)), POINT),
    ("中央付近", (-0.4, -0.4, 0.0, 0.0, 0.4, 0.4), UPDATE),
    ("端と中央に2回ずつ", (-1.0, -1.0, 0.0, 0.0, 1.0, 1.0), LINE),
)
DOE_ENDS = (-1.0, -1.0, -1.0, 1.0, 1.0, 1.0)
DOE_CANDIDATES = tuple(round(-1 + 0.1 * i, 1) for i in range(21))
DOE_SHOWN_STEPS = (0, 10, 1000)


def _doe_phi(x: float) -> list[float]:
    return [1.0, x, x * x]


def doe_information(xs: Sequence[float], weights: Sequence[float] | None = None) -> Matrix3:
    """M = sum w_i phi(x_i) phi(x_i)^T (weight 1 per bake for an exact design)."""
    w = weights if weights is not None else [1.0] * len(xs)
    return [
        [
            sum(wi * _doe_phi(x)[r] * _doe_phi(x)[c] for x, wi in zip(xs, w, strict=True))
            for c in range(3)
        ]
        for r in range(3)
    ]


def doe_variance(m: Matrix3, x: float) -> float:
    """Prediction variance phi(x)^T M^{-1} phi(x), in units of the measurement noise variance."""
    phi = _doe_phi(x)
    return sum(p * q for p, q in zip(phi, _solve_linear([row[:] for row in m], phi), strict=True))


@functools.cache
def doe_frank_wolfe(steps: int = 1000) -> tuple[tuple[tuple[float, ...], float], ...]:
    """Frank-Wolfe on candidate weights for max log det M(w); (weights, max d - 3) per step."""
    weights = [1.0 / len(DOE_CANDIDATES)] * len(DOE_CANDIDATES)
    history = []
    for _ in range(steps + 1):
        m = doe_information(DOE_CANDIDATES, weights)
        d = [doe_variance(m, x) for x in DOE_CANDIDATES]
        top = max(range(len(d)), key=d.__getitem__)
        history.append((tuple(weights), d[top] - 3))
        alpha = (d[top] / 3 - 1) / (d[top] - 1)  # the step that raises log det the most
        weights = [(1 - alpha) * w for w in weights]
        weights[top] += alpha
    return tuple(history)


def _doe_x(x: float) -> float:
    return _scale(-1.1, 1.1, 64, 410)(x)


def _doe_designs_svg() -> str:
    grid = [i / 100 for i in range(-100, 101)]
    worst = {
        name: max(doe_variance(doe_information(xs), x) for x in grid) for name, xs, _ in DOE_DESIGNS
    }
    dets = {name: _det3(doe_information(xs)) for name, xs, _ in DOE_DESIGNS}
    parts = _open(
        "6回の焼き温度と、予測のばらつき",
        (
            "① 6回の焼き温度の選び方。等間隔、中央付近（172・180・188℃に2回ずつ）、"
            "端と中央に2回ずつ（160・180・200℃）、両端だけ（160℃と200℃に3回ずつ）。"
            "両端だけでは2次式の係数が決まらない。"
            "② 点数を2次式で予測したときの、予測のばらつき（測定の誤差の分散を1とした値）。"
            + "、".join(
                f"{name}は最大 {worst[name]:.2f}（det M = {dets[name]:.3g}）"
                for name, _, _ in DOE_DESIGNS
            )
            + "。"
        ),
        640,
    )
    parts.append(_text(20, 64, "① 6回の焼き温度"))
    rows = (*DOE_DESIGNS, ("両端だけ", DOE_ENDS, MUTED))
    for index, (name, xs, color) in enumerate(rows):
        y = 112 + 46 * index
        parts.append(f'<path d="M64 {y:.1f}H410" stroke="{GRID}"/>')
        parts.append(_text(64, y - 16, name, "tick"))
        for value in sorted(set(xs)):
            count = xs.count(value)
            for k in range(count):
                cx = _doe_x(value) + 13 * k - 6.5 * (count - 1)
                parts.append(f'<circle cx="{cx:.1f}" cy="{y:.1f}" r="5.5" fill="{color}"/>')
    parts.append(_text(410, 112 + 46 * 3 - 16, "2次式の係数が決まらない", "tick", "end"))
    for t in (160, 170, 180, 190, 200):
        parts.append(_text(_doe_x((t - 180) / 20), 302, f"{t}", "tick", "middle"))
    parts.append(_text(410, 324, "焼き温度（℃）", "tick", "end"))

    parts.append(_text(20, 368, "② 点数の予測のばらつき"))
    vy = _scale(0.0, 1.2, 540, 384)
    parts.append(f'<path d="M64 384V540H410" fill="none" stroke="{GRID}"/>')
    for value in (0, 0.5, 1):
        parts.append(_text(56, vy(value) + 5, f"{value:g}", "tick", "end"))
    for _name, xs, color in DOE_DESIGNS:
        m = doe_information(xs)
        values = [(x, doe_variance(m, x)) for x in grid]
        parts.append(_polyline([(_doe_x(x), vy(v)) for x, v in values if v <= 1.2], color, 3))
    for t in (160, 180, 200):
        parts.append(_text(_doe_x((t - 180) / 20), 560, f"{t}℃", "tick", "middle"))
    labels = (
        (f"等間隔：最大 {worst['等間隔']:.2f}", POINT),
        (f"中央付近：両端で {worst['中央付近']:.0f}", UPDATE),
        (f"端と中央に2回ずつ：最大 {worst['端と中央に2回ずつ']:.2f}", LINE),
    )
    for index, (label, color) in enumerate(labels):
        y = 584 + 20 * index
        parts.append(_polyline([(64, y - 5), (84, y - 5)], color, 3))
        parts.append(_text(90, y, label, "tick"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


def _doe_weights_svg() -> str:
    history = doe_frank_wolfe()
    parts = _open(
        "候補の温度への重みと、最適の確かめ",
        (
            "160〜200℃を2℃おきに分けた21の候補温度に、実験の割合（重み）を配る。"
            "① Frank–Wolfe法で重みを動かした回数ごとの重み。"
            + "、".join(
                f"{k}回で160・180・200℃の重みの合計 "
                f"{sum(history[k][0][i] for i in (0, 10, 20)):.3f}"
                for k in DOE_SHOWN_STEPS
            )
            + "。② 重みで測った予測のばらつき（6回の値の6倍）の最大値と、係数の数3の差。"
            + "、".join(f"{k}回で {history[k][1]:.3g}" for k in (1, 10, 100, 1000))
            + "。0になる重みが最適。"
        ),
        600,
    )
    parts.append(_text(20, 64, "① 21の候補温度への重み"))
    for index, k in enumerate(DOE_SHOWN_STEPS):
        base = 150 + 70 * index
        wy = _scale(0.0, 0.4, base, base - 52)
        parts.append(f'<path d="M64 {base}H410" stroke="{GRID}"/>')
        parts.append(_text(100, base - 30, f"{k}回", "tick"))
        for x, w in zip(DOE_CANDIDATES, history[k][0], strict=True):
            color = LINE if x in (-1.0, 0.0, 1.0) else MUTED
            parts.append(
                f'<path d="M{_doe_x(x):.1f} {base}V{wy(w):.1f}" stroke="{color}" stroke-width="5"/>'
            )
    parts.append(_text(56, 150 - 52 + 5, "0.4", "tick", "end"))
    parts.append(_text(56, 150 + 5, "0", "tick", "end"))
    for t in (160, 180, 200):
        parts.append(_text(_doe_x((t - 180) / 20), 312, f"{t}", "tick", "middle"))
    parts.append(_text(410, 334, "焼き温度（℃）", "tick", "end"))

    parts.append(_text(20, 378, "② 重みで測った予測のばらつきの最大値 − 3"))
    gx = _scale(0.0, 3.0, 64, 410)
    gy = _scale(-3.0, 1.0, 548, 396)
    parts.append(f'<path d="M64 396V548H410" fill="none" stroke="{GRID}"/>')
    for e in (-3, -2, -1, 0, 1):
        parts.append(_text(56, gy(e) + 5, f"{10.0**e:g}", "tick", "end"))
    for e in range(4):
        parts.append(_text(gx(e), 568, f"{10**e}", "tick", "middle"))
    points = [(gx(math.log10(k)), gy(math.log10(g))) for k, (_, g) in enumerate(history) if k >= 1]
    parts.append(_polyline(points, UPDATE, 3))
    parts.append(_text(410, 590, "重みを動かした回数（どちらも対数目盛）", "tick", "end"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


# Repeated parametric QP (content/concepts/repeated-parametric-optimization.md): two machines
# share an order of theta (hundreds of pieces) every two hours. Cost 1/2 x1^2 + x2^2; machine 1
# caps at 4, machine 2 runs between 1 and 3. Constraints are a^T x >= b0 + bt * theta.
PQ_COST = (1.0, 2.0)
PQ_CONSTRAINTS = (
    ("注文を満たす", (1.0, 1.0), 0.0, 1.0),
    ("1号機の上限", (-1.0, 0.0), -4.0, 0.0),
    ("2号機の下限", (0.0, 1.0), 1.0, 0.0),
    ("2号機の上限", (0.0, -1.0), -3.0, 0.0),
    ("1号機の下限", (1.0, 0.0), 0.0, 0.0),
)
PQ_ORDERS = (2.0, 2.5, 3.5, 4.5, 5.5, 6.5, 6.8, 6.2, 5.0, 3.5, 2.0, 6.5)


def _pq_equality_qp(working: frozenset[int], theta: float) -> tuple[list[float], dict[int, float]]:
    """Solve min cost s.t. the working constraints hold with equality (one KKT system)."""
    rows = sorted(working)
    size = 2 + len(rows)
    kkt = [[0.0] * size for _ in range(size)]
    rhs = [0.0] * size
    for i in range(2):
        kkt[i][i] = PQ_COST[i]
    for k, index in enumerate(rows):
        _, a, b0, bt = PQ_CONSTRAINTS[index]
        for i in range(2):
            kkt[i][2 + k] = -a[i]
            kkt[2 + k][i] = a[i]
        rhs[2 + k] = b0 + bt * theta
    solution = _solve_linear(kkt, rhs)
    return solution[:2], {index: solution[2 + k] for k, index in enumerate(rows)}


def pq_solve(
    theta: float, start: frozenset[int] = frozenset()
) -> tuple[list[float], dict[int, float], frozenset[int], int]:
    """Active-set loop: drop the most negative multiplier, else add the most violated constraint.

    Returns the plan, the multipliers, the final working set and the number of KKT solves.
    """
    working, solves = set(start), 0
    while True:
        x, lam = _pq_equality_qp(frozenset(working), theta)
        solves += 1
        negative = {i: v for i, v in lam.items() if v < -1e-9}
        if negative:
            working.remove(min(negative, key=negative.__getitem__))
            continue
        gaps = {
            i: b0 + bt * theta - (a[0] * x[0] + a[1] * x[1])
            for i, (_, a, b0, bt) in enumerate(PQ_CONSTRAINTS)
            if i not in working
        }
        worst = max(gaps, key=gaps.__getitem__)
        if gaps[worst] > 1e-9:
            working.add(worst)
            continue
        return x, lam, frozenset(working), solves


def pq_sequence() -> tuple[list[int], list[int]]:
    """KKT solves per period: from an empty working set, and from the previous period's set."""
    cold, warm, working = [], [], frozenset[int]()
    for theta in PQ_ORDERS:
        cold.append(pq_solve(theta)[3])
        *_, working, solves = pq_solve(theta, working)
        warm.append(solves)
    return cold, warm


def _pq_regions_svg() -> str:
    parts = _open(
        "注文量と、2台の生産量",
        (
            "① 注文量 θ（百個）ごとの、費用が最小の生産量。θ<3 では2号機の下限1が効き、"
            "1号機が θ−1 を作る。3≦θ≦6 では1号機が 2θ/3、2号機が θ/3 を作る。"
            "θ>6 では1号機の上限4が効き、2号機が θ−4 を作る。"
            "② 2時間ごとの12回の注文量："
            + "・".join(f"{t:g}" for t in PQ_ORDERS)
            + "。点の色は、その回にどの制約が効くか"
            "（白は2号機の下限、緑は注文だけ、紺は1号機の上限）。"
        ),
        610,
    )
    tx = _scale(1.0, 7.0, 64, 410)
    vy = _scale(0.0, 4.5, 272, 92)
    parts.append(_text(20, 64, "① 注文量 θ ごとの生産量"))
    for boundary in (3.0, 6.0):
        parts.append(
            f'<path d="M{tx(boundary):.1f} 84V272" stroke="{GRID}" stroke-dasharray="5 4"/>'
        )
    parts.append(f'<path d="M64 84V272H410" fill="none" stroke="{GRID}"/>')
    for value in (0, 1, 2, 3, 4):
        parts.append(_text(56, vy(value) + 5, f"{value}", "tick", "end"))
    for value in range(1, 8):
        parts.append(_text(tx(value), 292, f"{value}", "tick", "middle"))
    thetas = [1 + 6 * i / 240 for i in range(241)]
    plans = [pq_solve(t)[0] for t in thetas]
    for machine, color in ((0, POINT), (1, UPDATE)):
        parts.append(
            _polyline(
                [(tx(t), vy(p[machine])) for t, p in zip(thetas, plans, strict=True)], color, 3
            )
        )
    regions = ((2.0, "下限", "#ffffff"), (4.5, "注文だけ", LINE), (6.5, "上限", POINT))
    for theta, label, color in regions:
        width = 15 * len(label) + 16
        left = tx(theta) - width / 2
        parts.append(
            f'<circle cx="{left + 6:.1f}" cy="95" r="6" fill="{color}" '
            f'stroke="{INK}" stroke-width="1.5"/>'
        )
        parts.append(_text(left + 16, 100, label, "tick"))
    parts.append(_text(tx(4.0), vy(2.67) - 14, "1号機", "tick", "end"))
    parts.append(_text(tx(4.5), vy(1.5) + 26, "2号機", "tick", "middle"))
    parts.append(_text(410, 314, "注文量 θ（百個）", "tick", "end"))

    parts.append(_text(20, 358, "② 2時間ごとの注文量"))
    ox = _scale(0.5, 12.5, 64, 410)
    oy = _scale(1.0, 7.0, 548, 380)
    parts.append(f'<path d="M64 380V548H410" fill="none" stroke="{GRID}"/>')
    for boundary in (3.0, 6.0):
        parts.append(
            f'<path d="M64 {oy(boundary):.1f}H410" stroke="{GRID}" stroke-dasharray="5 4"/>'
        )
    for value in (1, 3, 5, 7):
        parts.append(_text(56, oy(value) + 5, f"{value}", "tick", "end"))
    for boundary in (3, 6):
        parts.append(_text(70, oy(boundary) - 5, f"θ={boundary}", "tick"))
    region_colors = {frozenset({0, 2}): "#ffffff", frozenset({0}): LINE, frozenset({0, 1}): POINT}
    for k, theta in enumerate(PQ_ORDERS, start=1):
        color = region_colors[pq_solve(theta)[2]]
        parts.append(
            f'<circle cx="{ox(k):.1f}" cy="{oy(theta):.1f}" r="6" fill="{color}" '
            f'stroke="{INK}" stroke-width="1.5"/>'
        )
        parts.append(_text(ox(k), 568, str(k), "tick", "middle"))
    legend = (("2号機の下限", "#ffffff"), ("注文だけ", LINE), ("1号機の上限", POINT))
    for index, (label, color) in enumerate(legend):
        x0 = 64 + 118 * index
        parts.append(
            f'<circle cx="{x0 + 6}" cy="591" r="6" fill="{color}" '
            f'stroke="{INK}" stroke-width="1.5"/>'
        )
        parts.append(_text(x0 + 18, 596, label, "tick"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


def _pq_warm_svg() -> str:
    cold, warm = pq_sequence()
    parts = _open(
        "毎回ゼロからと、前回の作業集合から",
        (
            "12回の注文ごとに、連立一次方程式を解いた回数。"
            f"毎回ゼロから始めると合計{sum(cold)}回、前回の作業集合から始めると合計{sum(warm)}回。"
            "同じ制約が効き続ける回は、前回から始めると1回で済む。"
            "12回目は注文が2から6.5へ跳び、どちらも3回かかる。"
        ),
        340,
    )
    ox = _scale(0.5, 12.5, 64, 410)
    parts.append(_text(20, 64, "連立一次方程式を解いた回数"))
    cy = _scale(0.0, 3.0, 262, 94)
    parts.append(f'<path d="M64 94V262H410" fill="none" stroke="{GRID}"/>')
    for value in (0, 1, 2, 3):
        parts.append(_text(56, cy(value) + 5, f"{value}", "tick", "end"))
    width = (410 - 64) / 12
    for k, (c, w) in enumerate(zip(cold, warm, strict=True), start=1):
        left = ox(k) - width / 2 + 4
        bar = (width - 8) / 2
        parts.append(
            f'<rect x="{left:.1f}" y="{cy(c):.1f}" width="{bar:.1f}" height="{262 - cy(c):.1f}" '
            f'fill="{MUTED}"/>'
        )
        parts.append(
            f'<rect x="{left + bar:.1f}" y="{cy(w):.1f}" width="{bar:.1f}" '
            f'height="{262 - cy(w):.1f}" fill="{UPDATE}"/>'
        )
        parts.append(_text(ox(k), 282, str(k), "tick", "middle"))
    parts.append(_text(410, 304, "何回目の注文か", "tick", "end"))
    parts.append(f'<rect x="64" y="316" width="14" height="14" fill="{MUTED}"/>')
    parts.append(_text(84, 328, f"毎回ゼロから：合計{sum(cold)}", "tick"))
    parts.append(f'<rect x="250" y="316" width="14" height="14" fill="{UPDATE}"/>')
    parts.append(_text(270, 328, f"前回から：合計{sum(warm)}", "tick"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


# Game, equilibrium and VI (content/concepts/equilibrium-variational-inequality.md): three
# bakeries choose daily quantities q (hundreds); the price is 10 - (total); costs 1, 2, 3 and
# bakery A's oven caps it at 2.5. F_i(q) = -(d profit_i / d q_i) = q_i + Q - (10 - c_i).
EQ_PRICE = 10.0
EQ_COSTS = (1.0, 2.0, 3.0)
EQ_CAPS = (2.5, math.inf, math.inf)
EQ_NAMES = ("A", "B", "C")
EQ_COLORS = (POINT, UPDATE, LINE)
EQ_STEPS = (0.1, 0.2, 0.25, 0.3, 0.4, 0.5, 0.55, 0.6)


def eq_field(q: Sequence[float]) -> list[float]:
    total = sum(q)
    return [qi + total - (EQ_PRICE - c) for qi, c in zip(q, EQ_COSTS, strict=True)]


def eq_profit(q: Sequence[float]) -> list[float]:
    price = EQ_PRICE - sum(q)
    return [qi * (price - c) for qi, c in zip(q, EQ_COSTS, strict=True)]


def _eq_project(q: Sequence[float]) -> list[float]:
    return [min(cap, max(0.0, qi)) for qi, cap in zip(q, EQ_CAPS, strict=True)]


def eq_projection(step: float, rounds: int = 2000, tol: float = 1e-6) -> list[list[float]]:
    """q <- clip(q - step * F(q)) from q = 0; stops when a round moves q by less than tol."""
    history = [[0.0, 0.0, 0.0]]
    for _ in range(rounds):
        q = history[-1]
        nxt = _eq_project([qi - step * fi for qi, fi in zip(q, eq_field(q), strict=True)])
        history.append(nxt)
        if max(abs(a - b) for a, b in zip(nxt, q, strict=True)) < tol:
            break
    return history


@functools.cache
def eq_equilibrium() -> tuple[float, ...]:
    return tuple(eq_projection(0.25, tol=1e-13)[-1])


EQ_PLANS = (
    ("均衡", None),
    ("上限を外して解き、後で切る", (2.5, 2.0, 1.0)),
    ("3軒の利益の合計を最大", (2.5, 1.5, 0.0)),
)


def _eq_profit_svg() -> str:
    eq = eq_equilibrium()
    parts = _open(
        "パン屋の例：自分の利益と、3つの決め方",
        (
            "① ほかの2軒が均衡の量のとき、自分の量ごとの利益。均衡の量は"
            + "・".join(f"{n} {q:.2f}" for n, q in zip(EQ_NAMES, eq, strict=True))
            + "。BとCは利益の山の頂上、Aは上限2.5で止まる（Aの頂上は2.83）。"
            "② 3つの決め方の量と値段。"
            + "、".join(
                f"{name}は値段 {EQ_PRICE - sum(plan or eq):.2f}・"
                f"利益の合計 {sum(eq_profit(plan or eq)):.2f}"
                for name, plan in EQ_PLANS
            )
            + "。"
        ),
        624,
    )
    px = _scale(0.0, 4.0, 64, 410)
    py = _scale(0.0, 9.0, 272, 84)
    parts.append(_text(20, 64, "① 自分の量ごとの利益（ほかの2軒は均衡の量）"))
    parts.append(f'<path d="M64 84V272H410" fill="none" stroke="{GRID}"/>')
    for value in (0, 4, 8):
        parts.append(_text(56, py(value) + 5, f"{value}", "tick", "end"))
    for value in range(5):
        parts.append(_text(px(value), 292, f"{value}", "tick", "middle"))

    def own_profit(i: int, x: float) -> float:
        return x * (EQ_PRICE - (sum(eq) - eq[i]) - x - EQ_COSTS[i])

    parts.append(
        f'<path d="M{px(2.5):.1f} {py(own_profit(0, eq[0])) + 9:.1f}V272" stroke="{GRID}" '
        'stroke-width="1.5" stroke-dasharray="5 4"/>'
    )
    parts.append(_text(px(2.5) + 6, 262, "Aの上限 2.5", "tick"))
    for i, (name, color) in enumerate(zip(EQ_NAMES, EQ_COLORS, strict=True)):
        own = [4.0 * k / 160 for k in range(161)]
        inside = [(px(x), py(own_profit(i, x))) for x in own if x <= EQ_CAPS[i]]
        parts.append(_polyline([(x, y) for x, y in inside if y <= 272], color, 3))
        if EQ_CAPS[i] < 4.0:
            beyond = [(px(x), py(own_profit(i, x))) for x in own if x >= EQ_CAPS[i]]
            parts.append(
                _polyline([(x, y) for x, y in beyond if y <= 272], color, 1.5).replace(
                    "/>", ' stroke-dasharray="4 4"/>'
                )
            )
            top = (EQ_PRICE - (sum(eq) - eq[i]) - EQ_COSTS[i]) / 2
            parts.append(
                f'<circle cx="{px(top):.1f}" cy="{py(own_profit(i, top)):.1f}" r="5" '
                f'fill="#ffffff" stroke="{color}" stroke-width="2"/>'
            )
            parts.append(_text(px(2.5) + 8, py(own_profit(i, top)) + 30, f"頂上 {top:.2f}", "tick"))
        value = own_profit(i, eq[i])
        parts.append(
            f'<circle cx="{px(eq[i]):.1f}" cy="{py(value):.1f}" r="6" fill="{color}" '
            f'stroke="#ffffff" stroke-width="1.5"/>'
        )
        parts.append(_text(px(eq[i]) - 10, py(value) - 6, name, "tick", "end"))
    parts.append(_text(410, 314, "自分の量（百個）", "tick", "end"))

    parts.append(_text(20, 358, "② 3つの決め方の量と値段"))
    bx = _scale(0.0, 6.0, 64, 300)
    for row, (name, plan) in enumerate(EQ_PLANS):
        q = plan or eq
        y = 400 + 58 * row
        parts.append(_text(64, y - 8, name, "tick"))
        left = 64.0
        for qi, color in zip(q, EQ_COLORS, strict=True):
            width = bx(qi) - 64
            if width > 0:
                parts.append(
                    f'<rect x="{left:.1f}" y="{y:.1f}" width="{width:.1f}" height="18" '
                    f'fill="{color}"/>'
                )
            left += width
        parts.append(_text(310, y + 15, f"値段 {EQ_PRICE - sum(q):.2f}", "tick"))
    for value in (0, 2, 4, 6):
        parts.append(_text(bx(value), 554, f"{value}", "tick", "middle"))
    for index, (name, color) in enumerate(zip(EQ_NAMES, EQ_COLORS, strict=True)):
        x0 = 64 + 50 * index
        parts.append(f'<rect x="{x0}" y="584" width="14" height="14" fill="{color}"/>')
        parts.append(_text(x0 + 20, 596, name, "tick"))
    parts.append(_text(410, 596, "横は3軒の量の合計（百個）", "tick", "end"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


def _eq_steps_svg() -> str:
    eq = eq_equilibrium()
    counts = {step: len(eq_projection(step)) - 1 for step in EQ_STEPS}
    shown = (0.1, 0.25, 0.5)
    parts = _open(
        "射影法の歩幅と、均衡までの回数",
        (
            "① 歩幅 γ ごとの、均衡からの最大のずれ。γ=0.25は"
            f"{counts[0.25]}回、γ=0.5は{counts[0.5]}回で、1回に動く量が10⁻⁶未満になる。"
            "② 歩幅ごとの回数。"
            + "、".join(
                f"γ={s:g}で{counts[s]}回" if counts[s] < 2000 else f"γ={s:g}では着かない"
                for s in EQ_STEPS
            )
            + "。γ=0.6では、0と(2.5, 4.8, 4.2)を往復する。"
        ),
        560,
    )
    parts.append(_text(20, 64, "① 均衡からの最大のずれ"))
    gx = _scale(0.0, 110.0, 64, 410)
    gy = _scale(-7.0, 1.0, 272, 84)
    parts.append(f'<path d="M64 84V272H410" fill="none" stroke="{GRID}"/>')
    for e, label in ((-6, "10⁻⁶"), (-4, "10⁻⁴"), (-2, "10⁻²"), (0, "1")):
        parts.append(_text(56, gy(e) + 5, label, "tick", "end"))
    for value in (0, 25, 50, 75, 100):
        parts.append(_text(gx(value), 292, f"{value}", "tick", "middle"))
    for step, color in zip(shown, (MUTED, UPDATE, POINT), strict=True):
        points = []
        for k, q in enumerate(eq_projection(step)):
            gap = max(abs(a - b) for a, b in zip(q, eq, strict=True))
            if gap > 1e-7:
                points.append((gx(k), gy(math.log10(gap))))
        parts.append(_polyline(points, color, 2.5))
    for index, (step, color) in enumerate(zip(shown, (MUTED, UPDATE, POINT), strict=True)):
        x0 = 64 + 110 * index
        parts.append(_polyline([(x0, 311), (x0 + 20, 311)], color, 3))
        parts.append(_text(x0 + 26, 316, f"γ={step:g}", "tick"))
    parts.append(_text(410, 336, "回数（縦は対数目盛）", "tick", "end"))

    parts.append(_text(20, 380, "② 歩幅 γ ごとの、均衡までの回数"))
    by = _scale(0.0, 120.0, 520, 400)
    parts.append(f'<path d="M64 400V520H410" fill="none" stroke="{GRID}"/>')
    width = (410 - 64) / len(EQ_STEPS)
    for index, step in enumerate(EQ_STEPS):
        left = 64 + width * index + 6
        count = counts[step]
        center = left + (width - 12) / 2
        if count < 2000:
            top = by(count)
            parts.append(
                f'<rect x="{left:.1f}" y="{top:.1f}" width="{width - 12:.1f}" '
                f'height="{520 - top:.1f}" fill="{UPDATE if step == 0.25 else LINE}"/>'
            )
            parts.append(_text(center, top - 6, str(count), "tick", "middle"))
        else:
            parts.append(_text(center, 510, "×", "tick", "middle"))
        parts.append(_text(center, 540, f"{step:g}", "tick", "middle"))
    parts.append(_text(410, 556, "歩幅 γ（×は着かない）", "tick", "end"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


# General conic optimization (content/concepts/general-conic-optimization.md): split a promotion
# budget of 6 across three stores, effect sum w_i log(1 + x_i) with w = (3, 2, 1), and keep the
# spread ||x - mean(x)||_2 <= 1.5. Cones: three exponential, one second-order, nonnegative.
CN_WEIGHTS = (3.0, 2.0, 1.0)
CN_BUDGET = 6.0
CN_SPREAD = 1.5
CN_COLORS = (POINT, UPDATE, LINE)


def cn_effect(x: Sequence[float]) -> float:
    return sum(w * math.log1p(v) for w, v in zip(CN_WEIGHTS, x, strict=True))


@functools.cache
def cn_solve(spread: float = CN_SPREAD, budget: float = CN_BUDGET) -> tuple[float, ...]:
    """Maximize the effect with the whole budget spent and the spread at its limit.

    Both limits are active in this example, so x = mean + spread * (cos f e1 + sin f e2) with
    e1, e2 an orthonormal basis of the plane sum(x) = 0; search f on a grid, then refine.
    """
    e1 = (1 / math.sqrt(2), -1 / math.sqrt(2), 0.0)
    e2 = (1 / math.sqrt(6), 1 / math.sqrt(6), -2 / math.sqrt(6))

    def alloc(f: float) -> list[float]:
        return [
            budget / 3 + spread * (math.cos(f) * a + math.sin(f) * b)
            for a, b in zip(e1, e2, strict=True)
        ]

    grid = [-math.pi + 2 * math.pi * k / 3600 for k in range(3600)]
    best = max(grid, key=lambda f: cn_effect(alloc(f)))
    lo, hi = best - 2 * math.pi / 3600, best + 2 * math.pi / 3600
    ratio = (math.sqrt(5) - 1) / 2
    for _ in range(100):
        a, b = hi - ratio * (hi - lo), lo + ratio * (hi - lo)
        if cn_effect(alloc(a)) > cn_effect(alloc(b)):
            hi = b
        else:
            lo = a
    return tuple(alloc((lo + hi) / 2))


def cn_multipliers(x: Sequence[float]) -> tuple[float, float]:
    """(budget, spread) multipliers from w_i / (1 + x_i) = lam + mu * d_i / |d|."""
    grad = [w / (1 + v) for w, v in zip(CN_WEIGHTS, x, strict=True)]
    mean = sum(x) / 3
    d = [v - mean for v in x]
    norm = math.sqrt(sum(v * v for v in d))
    return sum(grad) / 3, sum(g * v / norm for g, v in zip(grad, d, strict=True))


CN_PLANS = (
    ("対数だけ（ばらつきの上限なし）", (3.5, 2.0, 0.5)),
    ("ばらつきの上限 1.5 あり", None),
    ("対数を2次式で近似", (1.0, 1.0, 1.0)),
)


def _cn_allocation_svg() -> str:
    x = cn_solve()
    parts = _open(
        "3店への販促費と、効果",
        (
            "① 店ごとの効果 w log(1+x)（w は3・2・1）。"
            "点は、予算6とばらつきの上限1.5のもとでの答え "
            + "・".join(f"{v:.2f}" for v in x)
            + "。② 3つの決め方の配分と効果の合計。"
            + "、".join(f"{name}は {cn_effect(plan or x):.2f}" for name, plan in CN_PLANS)
            + "。"
        ),
        600,
    )
    px = _scale(0.0, 4.0, 64, 410)
    py = _scale(0.0, 5.0, 272, 84)
    parts.append(_text(20, 64, "① 店ごとの効果 w log(1 + x)"))
    parts.append(f'<path d="M64 84V272H410" fill="none" stroke="{GRID}"/>')
    for value in (0, 2, 4):
        parts.append(_text(56, py(value) + 5, f"{value}", "tick", "end"))
    for value in range(5):
        parts.append(_text(px(value), 292, f"{value}", "tick", "middle"))
    names = ("店1（w=3）", "店2（w=2）", "店3（w=1）")
    for w, xi, color, name in zip(CN_WEIGHTS, x, CN_COLORS, names, strict=True):
        curve = [(px(4 * k / 120), py(w * math.log1p(4 * k / 120))) for k in range(121)]
        parts.append(_polyline(curve, color, 3))
        parts.append(
            f'<circle cx="{px(xi):.1f}" cy="{py(w * math.log1p(xi)):.1f}" r="6" fill="{color}" '
            f'stroke="#ffffff" stroke-width="1.5"/>'
        )
        parts.append(_text(px(4.0) - 4, py(w * math.log1p(4.0)) - 8, name, "tick", "end"))
    parts.append(_text(410, 314, "販促費 x", "tick", "end"))

    parts.append(_text(20, 358, "② 3つの決め方の配分と、効果の合計"))
    bx = _scale(0.0, 6.0, 64, 300)
    for row, (name, plan) in enumerate(CN_PLANS):
        q = plan or x
        y = 400 + 58 * row
        parts.append(_text(64, y - 8, name, "tick"))
        left = 64.0
        for qi, color in zip(q, CN_COLORS, strict=True):
            width = bx(qi) - 64
            parts.append(
                f'<rect x="{left:.1f}" y="{y:.1f}" width="{width:.1f}" height="18" fill="{color}"/>'
            )
            left += width
        parts.append(_text(318, y + 15, f"効果 {cn_effect(q):.2f}", "tick"))
    parts.append(
        f'<path d="M{bx(CN_BUDGET):.1f} 384V540" stroke="{MUTED}" stroke-width="1.5" '
        'stroke-dasharray="5 4"/>'
    )
    parts.append(_text(bx(CN_BUDGET), 556, "予算6", "tick", "middle"))
    for index, color in enumerate(CN_COLORS):
        x0 = 64 + 70 * index
        parts.append(f'<rect x="{x0}" y="572" width="14" height="14" fill="{color}"/>')
        parts.append(_text(x0 + 20, 584, f"店{index + 1}", "tick"))
    parts.append(_text(410, 584, "横は販促費（合計6）", "tick", "end"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


def cn_blocks() -> list[tuple[str, list[float], str]]:
    """The stacked vector b - Ax at the answer, split by cone, with each block's check."""
    x = cn_solve()
    t = [math.log1p(v) for v in x]
    mean = sum(x) / 3
    d = [v - mean for v in x]
    blocks = [
        (f"指数錐{i + 1}", [ti, 1.0, 1 + xi], f"e^{ti:.3f} = {math.exp(ti):.2f} ≦ {1 + xi:.2f}")
        for i, (ti, xi) in enumerate(zip(t, x, strict=True))
    ]
    norm = math.sqrt(sum(v * v for v in d))
    blocks.append(("二次錐", [CN_SPREAD, *d], f"長さ {norm:.2f} ≦ {CN_SPREAD:g}"))
    blocks.append(("非負の象限", [CN_BUDGET - sum(x), *x], "どれも 0 以上"))
    return blocks


def _cn_blocks_svg() -> str:
    blocks = cn_blocks()
    rows = sum(len(v) for _, v, _ in blocks)
    parts = _open(
        "b − Az を、錐ごとに区切る",
        (
            f"答えの点での {rows} 行のベクトル b − Az を、5つの錐に区切ったもの。"
            + "。".join(
                f"{name}：("
                + ", ".join(f"{v:.2f}".replace("-", "−") for v in values)
                + f")、{check}"
                for name, values, check in blocks
            )
            + "。"
        ),
        84 + 76 * len(blocks),
    )
    colors = {"指数錐": POINT, "二次錐": UPDATE, "非負の象限": LINE}
    for row, (name, values, check) in enumerate(blocks):
        y = 64 + 76 * row
        color = next(c for key, c in colors.items() if name.startswith(key))
        parts.append(_text(20, y + 22, name, "tick"))
        for k, value in enumerate(values):
            left = 108 + 64 * k
            parts.append(
                f'<rect x="{left}" y="{y}" width="58" height="32" rx="4" fill="#ffffff" '
                f'stroke="{color}" stroke-width="2"/>'
            )
            parts.append(
                _text(left + 29, y + 22, f"{value:.2f}".replace("-", "−"), "tick", "middle")
            )
        parts.append(_text(108, y + 54, check, "note"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


def generate_lesson_figures() -> dict[str, str]:
    return {
        "least-squares-residuals.svg": _least_squares_residuals_svg(),
        "least-squares-contours.svg": _least_squares_contours_svg(),
        "least-squares-minimum.svg": _least_squares_minimum_svg(),
        "nonlinear-least-squares-profile.svg": _nonlinear_least_squares_profile_svg(),
        "smooth-landscape-saddle.svg": _smooth_landscape_svg(),
        "inverse-problem-alpha.svg": _inverse_problem_alpha_svg(),
        "l1-sparse-regularization-path.svg": _l1_path_svg(),
        "mpc-wall-receding.svg": _mpc_wall_svg(),
        "vrp-routes.svg": _vrp_routes_svg(),
        "vrp-subtour.svg": _vrp_subtour_svg(),
        "miqp-big-m-bound.svg": _miqp_big_m_svg(),
        "robust-regression-huber.svg": _robust_huber_svg(),
        "stochastic-erm-minibatch.svg": _erm_minibatch_svg(),
        "hpo-search-points.svg": _hpo_search_svg(),
        "milp-relaxation-tree.svg": _milp_tree_svg(),
        "bound-constrained-box.svg": _bound_constrained_box_svg(),
        "socp-relay-station.svg": _socp_relay_svg(),
        "network-flow-paths.svg": _network_flow_svg(),
        "so3-rotation-paths.svg": _so3_paths_svg(),
        "so3-lie-algebra-circle.svg": _so2_circle_svg(),
        "nn-training-two-valleys.svg": _nn_two_valleys_svg(),
        "shape-fin-length.svg": _fin_length_svg(),
        "composite-group-shrink.svg": _composite_group_svg(),
        "discontinuous-dryer-cliff.svg": _discontinuous_dryer_svg(),
        "noisy-black-box-budget.svg": _noisy_oven_svg(),
        "nonconvex-qp-basins.svg": _ncqp_basins_svg(),
        "minlp-relaxation-branch.svg": _minlp_svg(),
        "shortest-path-routes.svg": _path_svg(),
        "bilevel-pricing-response.svg": _bilevel_svg(),
        "complementarity-active-sets.svg": _lcp_contact_svg(),
        "large-smooth-deblur.svg": _pa007_deblur_svg(),
        "closed-form-order-cost.svg": _pa001_cost_svg(),
        "high-dimensional-black-box-budget.svg": _pa015_budget_svg(),
        "general-nonsmooth-kink-valley.svg": _pa011_kink_valley_svg(),
        "linear-system-circuit.svg": _pa002_circuit_svg(),
        "assignment-greedy-optimal.svg": _assignment_greedy_svg(),
        "assignment-dual-bound.svg": _assignment_dual_svg(),
        "eigenvalue-fence-direction.svg": _eig_fence_svg(),
        "eigenvalue-parallel-condition.svg": _eig_condition_svg(),
        "stochastic-programming-expected-cost.svg": _sp_cost_svg(),
        "stochastic-programming-two-stage.svg": _sp_tree_svg(),
        "external-solver-flat-stop.svg": _ext_flat_stop_svg(),
        "robust-optimization-box.svg": _ro_box_svg(),
        "robust-optimization-set-size.svg": _ro_set_size_svg(),
        "robust-estimation-profile.svg": _rpe_profile_svg(),
        "robust-estimation-weights.svg": _rpe_weights_svg(),
        "sat-invite-grid.svg": _sat_grid_svg(),
        "sat-invite-chain.svg": _sat_chain_svg(),
        "trajectory-pillar-paths.svg": _traj_paths_svg(),
        "trajectory-grid-check.svg": _traj_grid_svg(),
        "solver-evaluation-inflow.svg": _eval_inflow_svg(),
        "solver-evaluation-breakdown.svg": _eval_breakdown_svg(),
        "written-constraint-plane.svg": _con_plane_svg(),
        "inner-solver-steps.svg": _inner_steps_svg(),
        "distributed-consensus-losses.svg": _dc_losses_svg(),
        "distributed-consensus-admm.svg": _dc_admm_svg(),
        "online-budget-days.svg": _ol_days_svg(),
        "online-regret-growth.svg": _ol_regret_svg(),
        "doe-designs-variance.svg": _doe_designs_svg(),
        "doe-weights-gap.svg": _doe_weights_svg(),
        "parametric-production-regions.svg": _pq_regions_svg(),
        "parametric-warm-start.svg": _pq_warm_svg(),
        "equilibrium-bakery-profit.svg": _eq_profit_svg(),
        "equilibrium-projection-steps.svg": _eq_steps_svg(),
        "conic-promo-allocation.svg": _cn_allocation_svg(),
        "conic-blocks.svg": _cn_blocks_svg(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="fail if a figure is stale")
    args = parser.parse_args()
    stale = []
    outputs = {OUTPUT / n: b for n, b in generate_lesson_figures().items()}
    outputs[INVERSE_FIXTURE] = inverse_problem_fixture()
    for path, body in outputs.items():
        name = path.name
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != body:
                stale.append(name)
        else:
            path.write_text(body, encoding="utf-8", newline="\n")
    if stale:
        raise SystemExit(f"stale lesson figures: {', '.join(stale)}")


if __name__ == "__main__":
    main()
