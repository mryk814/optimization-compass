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
import html
import itertools
import json
import math
import random
from collections.abc import Callable, Sequence
from fractions import Fraction
from pathlib import Path

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
        "nn-training-two-valleys.svg": _nn_two_valleys_svg(),
        "shape-fin-length.svg": _fin_length_svg(),
        "composite-group-shrink.svg": _composite_group_svg(),
        "discontinuous-dryer-cliff.svg": _discontinuous_dryer_svg(),
        "noisy-black-box-budget.svg": _noisy_oven_svg(),
        "nonconvex-qp-basins.svg": _ncqp_basins_svg(),
        "minlp-relaxation-branch.svg": _minlp_svg(),
        "shortest-path-routes.svg": _path_svg(),
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
