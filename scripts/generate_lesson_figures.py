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
import json
import math
import random
from collections.abc import Callable, Sequence
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
