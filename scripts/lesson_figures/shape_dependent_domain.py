"""Shape-dependent domain (content/concepts/shape-dependent-domain.md): a cooling fin of length L
with -u'' + u = 0 on (0, L), u(0) = 1, u'(L) = 0, so u(x) = cosh(L - x) / cosh(L) and the heat
leaving the surface is tanh(L). The design minimizes J(L) = 0.25 L - tanh(L).
"""

from __future__ import annotations

import math
from collections.abc import Callable

from ._svg import GRID, INK, LINE, POINT, UPDATE, _open, _polyline, _scale, _text

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


FIGURES: dict[str, Callable[[], str]] = {
    "shape-fin-length.svg": _fin_length_svg,
}
