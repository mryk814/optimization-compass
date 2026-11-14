"""Closed-form candidate (content/concepts/closed-form-candidate.md): the yearly cost of an order
quantity Q, f(Q) = K D / Q + h Q / 2. K = 1500 yen per order, D = 1200 units a year, h = 10 yen per
unit per year. Setting f'(Q) = 0 gives Q* = sqrt(2 K D / h).
"""

from __future__ import annotations

import math
from collections.abc import Callable

from ._svg import GRID, INK, LINE, POINT, UPDATE, _open, _polyline, _scale, _text

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


FIGURES: dict[str, Callable[[], str]] = {
    "closed-form-order-cost.svg": _pa001_cost_svg,
}
