"""Written versus real constraints (content/concepts/written-and-real-constraints.md): the same
tank. The tool fails when the tank runs dry within the 30 minutes; in the (a, q) plane that region
lies under a curve that the dry time T(a, q) = 1800 s draws for q <= 0.
"""

from __future__ import annotations

import math
from collections.abc import Callable

from ._svg import (
    GRID,
    INK,
    LINE,
    MUTED,
    POINT,
    RING,
    UPDATE,
    VIOLATION,
    _open,
    _polyline,
    _scale,
    _text,
)

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


FIGURES: dict[str, Callable[[], str]] = {
    "written-constraint-plane.svg": _con_plane_svg,
}
