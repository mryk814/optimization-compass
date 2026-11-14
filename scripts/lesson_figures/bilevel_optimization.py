"""Bilevel optimization (content/concepts/bilevel-optimization.md): a seller sets the price x, a
buyer picks the quantity y that minimises 0.5 y^2 + x y - 4 y over y >= 0.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence

from ._svg import GRID, LINE, POINT, UPDATE, _open, _polyline, _scale, _text

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


FIGURES: dict[str, Callable[[], str]] = {
    "bilevel-pricing-response.svg": _bilevel_svg,
}
