"""Second-order cone program (content/concepts/second-order-cone-program.md): one relay station that
reaches three villages, min t s.t. |x - p_i| <= t. Coordinates in km.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from fractions import Fraction

from ._svg import GRID, LINE, MUTED, POINT, UPDATE, _open, _scale, _text

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


FIGURES: dict[str, Callable[[], str]] = {
    "socp-relay-station.svg": _socp_relay_svg,
}
