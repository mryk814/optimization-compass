"""Generate the computed supporting figures that sit next to one formula in a lesson.

uv run python scripts/generate_lesson_figures.py            # write site/public/figures/*.svg
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
import math
from collections.abc import Callable, Sequence
from pathlib import Path

ROOT = Path(__file__).parents[1]
OUTPUT = ROOT / "site" / "public" / "figures"

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


def generate_lesson_figures() -> dict[str, str]:
    return {
        "least-squares-residuals.svg": _least_squares_residuals_svg(),
        "least-squares-contours.svg": _least_squares_contours_svg(),
        "least-squares-minimum.svg": _least_squares_minimum_svg(),
        "nonlinear-least-squares-profile.svg": _nonlinear_least_squares_profile_svg(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="fail if a figure is stale")
    args = parser.parse_args()
    stale = []
    for name, body in generate_lesson_figures().items():
        path = OUTPUT / name
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != body:
                stale.append(name)
        else:
            path.write_text(body, encoding="utf-8", newline="\n")
    if stale:
        raise SystemExit(f"stale lesson figures: {', '.join(stale)}")


if __name__ == "__main__":
    main()
