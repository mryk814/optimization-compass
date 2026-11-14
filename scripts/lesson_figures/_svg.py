"""Drawing helpers shared by the lesson figures: the frame, text, lines, scales and contours.

Supporting figures are drawn at the width they are shown on a PC (440 px, the 27.5rem cap for
static figures), so one SVG unit is one CSS pixel there. Text uses 16 px (15 px for axis ticks):
the same size as the body on a PC and 12 px or more at a 375 px phone width. Every coordinate comes
from the lesson's data, never from hand-placed numbers.

A change here redraws the figures of many articles: regenerate them all and look at the diff.
"""

from __future__ import annotations

import html
from collections.abc import Callable, Sequence

WIDTH = 440
INK, MUTED, GRID = "#17211b", "#56645b", "#aab4ab"
LINE, POINT, UPDATE, RING = "#315c48", "#24406b", "#b3532d", "#91b8a4"
VIOLATION = "#c23a2b"


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


def _signed(value: float, digits: int) -> str:
    return f"{value:.{digits}f}".replace("-", "−")


def _polyline(points: Sequence[tuple[float, float]], color: str, width: float) -> str:
    joined = " ".join(f"{x:.2f},{y:.2f}" for x, y in points)
    return (
        f'<polyline points="{joined}" fill="none" stroke="{color}" '
        f'stroke-width="{width}" stroke-linejoin="round"/>'
    )


def _scale(lower: float, upper: float, start: float, end: float) -> Callable[[float], float]:
    return lambda value: start + (value - lower) / (upper - lower) * (end - start)


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
