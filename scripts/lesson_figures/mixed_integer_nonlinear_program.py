"""MINLP (content/concepts/mixed-integer-nonlinear-program.md): n machines, each run at load q."""

from __future__ import annotations

from collections.abc import Callable

from ._svg import GRID, LINE, POINT, UPDATE, _open, _polyline, _scale, _text

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


FIGURES: dict[str, Callable[[], str]] = {
    "minlp-relaxation-branch.svg": _minlp_svg,
}
