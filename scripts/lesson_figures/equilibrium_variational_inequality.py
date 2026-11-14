"""Game, equilibrium and VI (content/concepts/equilibrium-variational-inequality.md): three bakeries
choose daily quantities q (hundreds); the price is 10 - (total); costs 1, 2, 3 and bakery A's oven
caps it at 2.5. F_i(q) = -(d profit_i / d q_i) = q_i + Q - (10 - c_i).
"""

from __future__ import annotations

import functools
import math
from collections.abc import Callable, Sequence

from ._svg import GRID, LINE, MUTED, POINT, UPDATE, _open, _polyline, _scale, _text

EQ_PRICE = 10.0
EQ_COSTS = (1.0, 2.0, 3.0)
EQ_CAPS = (2.5, math.inf, math.inf)
EQ_NAMES = ("A", "B", "C")
EQ_COLORS = (POINT, UPDATE, LINE)
EQ_STEPS = (0.1, 0.2, 0.25, 0.3, 0.4, 0.5, 0.55, 0.6)


def eq_field(q: Sequence[float]) -> list[float]:
    total = sum(q)
    return [qi + total - (EQ_PRICE - c) for qi, c in zip(q, EQ_COSTS, strict=True)]


def eq_profit(q: Sequence[float]) -> list[float]:
    price = EQ_PRICE - sum(q)
    return [qi * (price - c) for qi, c in zip(q, EQ_COSTS, strict=True)]


def _eq_project(q: Sequence[float]) -> list[float]:
    return [min(cap, max(0.0, qi)) for qi, cap in zip(q, EQ_CAPS, strict=True)]


def eq_projection(step: float, rounds: int = 2000, tol: float = 1e-6) -> list[list[float]]:
    """q <- clip(q - step * F(q)) from q = 0; stops when a round moves q by less than tol."""
    history = [[0.0, 0.0, 0.0]]
    for _ in range(rounds):
        q = history[-1]
        nxt = _eq_project([qi - step * fi for qi, fi in zip(q, eq_field(q), strict=True)])
        history.append(nxt)
        if max(abs(a - b) for a, b in zip(nxt, q, strict=True)) < tol:
            break
    return history


@functools.cache
def eq_equilibrium() -> tuple[float, ...]:
    return tuple(eq_projection(0.25, tol=1e-13)[-1])


EQ_PLANS = (
    ("均衡", None),
    ("上限を外して解き、後で切る", (2.5, 2.0, 1.0)),
    ("3軒の利益の合計を最大", (2.5, 1.5, 0.0)),
)


def _eq_profit_svg() -> str:
    eq = eq_equilibrium()
    parts = _open(
        "パン屋の例：自分の利益と、3つの決め方",
        (
            "① ほかの2軒が均衡の量のとき、自分の量ごとの利益。均衡の量は"
            + "・".join(f"{n} {q:.2f}" for n, q in zip(EQ_NAMES, eq, strict=True))
            + "。BとCは利益の山の頂上、Aは上限2.5で止まる（Aの頂上は2.83）。"
            "② 3つの決め方の量と値段。"
            + "、".join(
                f"{name}は値段 {EQ_PRICE - sum(plan or eq):.2f}・"
                f"利益の合計 {sum(eq_profit(plan or eq)):.2f}"
                for name, plan in EQ_PLANS
            )
            + "。"
        ),
        624,
    )
    px = _scale(0.0, 4.0, 64, 410)
    py = _scale(0.0, 9.0, 272, 84)
    parts.append(_text(20, 64, "① 自分の量ごとの利益（ほかの2軒は均衡の量）"))
    parts.append(f'<path d="M64 84V272H410" fill="none" stroke="{GRID}"/>')
    for value in (0, 4, 8):
        parts.append(_text(56, py(value) + 5, f"{value}", "tick", "end"))
    for value in range(5):
        parts.append(_text(px(value), 292, f"{value}", "tick", "middle"))

    def own_profit(i: int, x: float) -> float:
        return x * (EQ_PRICE - (sum(eq) - eq[i]) - x - EQ_COSTS[i])

    parts.append(
        f'<path d="M{px(2.5):.1f} {py(own_profit(0, eq[0])) + 9:.1f}V272" stroke="{GRID}" '
        'stroke-width="1.5" stroke-dasharray="5 4"/>'
    )
    parts.append(_text(px(2.5) + 6, 262, "Aの上限 2.5", "tick"))
    for i, (name, color) in enumerate(zip(EQ_NAMES, EQ_COLORS, strict=True)):
        own = [4.0 * k / 160 for k in range(161)]
        inside = [(px(x), py(own_profit(i, x))) for x in own if x <= EQ_CAPS[i]]
        parts.append(_polyline([(x, y) for x, y in inside if y <= 272], color, 3))
        if EQ_CAPS[i] < 4.0:
            beyond = [(px(x), py(own_profit(i, x))) for x in own if x >= EQ_CAPS[i]]
            parts.append(
                _polyline([(x, y) for x, y in beyond if y <= 272], color, 1.5).replace(
                    "/>", ' stroke-dasharray="4 4"/>'
                )
            )
            top = (EQ_PRICE - (sum(eq) - eq[i]) - EQ_COSTS[i]) / 2
            parts.append(
                f'<circle cx="{px(top):.1f}" cy="{py(own_profit(i, top)):.1f}" r="5" '
                f'fill="#ffffff" stroke="{color}" stroke-width="2"/>'
            )
            parts.append(_text(px(2.5) + 8, py(own_profit(i, top)) + 30, f"頂上 {top:.2f}", "tick"))
        value = own_profit(i, eq[i])
        parts.append(
            f'<circle cx="{px(eq[i]):.1f}" cy="{py(value):.1f}" r="6" fill="{color}" '
            f'stroke="#ffffff" stroke-width="1.5"/>'
        )
        parts.append(_text(px(eq[i]) - 10, py(value) - 6, name, "tick", "end"))
    parts.append(_text(410, 314, "自分の量（百個）", "tick", "end"))

    parts.append(_text(20, 358, "② 3つの決め方の量と値段"))
    bx = _scale(0.0, 6.0, 64, 300)
    for row, (name, plan) in enumerate(EQ_PLANS):
        q = plan or eq
        y = 400 + 58 * row
        parts.append(_text(64, y - 8, name, "tick"))
        left = 64.0
        for qi, color in zip(q, EQ_COLORS, strict=True):
            width = bx(qi) - 64
            if width > 0:
                parts.append(
                    f'<rect x="{left:.1f}" y="{y:.1f}" width="{width:.1f}" height="18" '
                    f'fill="{color}"/>'
                )
            left += width
        parts.append(_text(310, y + 15, f"値段 {EQ_PRICE - sum(q):.2f}", "tick"))
    for value in (0, 2, 4, 6):
        parts.append(_text(bx(value), 554, f"{value}", "tick", "middle"))
    for index, (name, color) in enumerate(zip(EQ_NAMES, EQ_COLORS, strict=True)):
        x0 = 64 + 50 * index
        parts.append(f'<rect x="{x0}" y="584" width="14" height="14" fill="{color}"/>')
        parts.append(_text(x0 + 20, 596, name, "tick"))
    parts.append(_text(410, 596, "横は3軒の量の合計（百個）", "tick", "end"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


def _eq_steps_svg() -> str:
    eq = eq_equilibrium()
    counts = {step: len(eq_projection(step)) - 1 for step in EQ_STEPS}
    shown = (0.1, 0.25, 0.5)
    parts = _open(
        "射影法の歩幅と、均衡までの回数",
        (
            "① 歩幅 γ ごとの、均衡からの最大のずれ。γ=0.25は"
            f"{counts[0.25]}回、γ=0.5は{counts[0.5]}回で、1回に動く量が10⁻⁶未満になる。"
            "② 歩幅ごとの回数。"
            + "、".join(
                f"γ={s:g}で{counts[s]}回" if counts[s] < 2000 else f"γ={s:g}では着かない"
                for s in EQ_STEPS
            )
            + "。γ=0.6では、0と(2.5, 4.8, 4.2)を往復する。"
        ),
        560,
    )
    parts.append(_text(20, 64, "① 均衡からの最大のずれ"))
    gx = _scale(0.0, 110.0, 64, 410)
    gy = _scale(-7.0, 1.0, 272, 84)
    parts.append(f'<path d="M64 84V272H410" fill="none" stroke="{GRID}"/>')
    for e, label in ((-6, "10⁻⁶"), (-4, "10⁻⁴"), (-2, "10⁻²"), (0, "1")):
        parts.append(_text(56, gy(e) + 5, label, "tick", "end"))
    for value in (0, 25, 50, 75, 100):
        parts.append(_text(gx(value), 292, f"{value}", "tick", "middle"))
    for step, color in zip(shown, (MUTED, UPDATE, POINT), strict=True):
        points = []
        for k, q in enumerate(eq_projection(step)):
            gap = max(abs(a - b) for a, b in zip(q, eq, strict=True))
            if gap > 1e-7:
                points.append((gx(k), gy(math.log10(gap))))
        parts.append(_polyline(points, color, 2.5))
    for index, (step, color) in enumerate(zip(shown, (MUTED, UPDATE, POINT), strict=True)):
        x0 = 64 + 110 * index
        parts.append(_polyline([(x0, 311), (x0 + 20, 311)], color, 3))
        parts.append(_text(x0 + 26, 316, f"γ={step:g}", "tick"))
    parts.append(_text(410, 336, "回数（縦は対数目盛）", "tick", "end"))

    parts.append(_text(20, 380, "② 歩幅 γ ごとの、均衡までの回数"))
    by = _scale(0.0, 120.0, 520, 400)
    parts.append(f'<path d="M64 400V520H410" fill="none" stroke="{GRID}"/>')
    width = (410 - 64) / len(EQ_STEPS)
    for index, step in enumerate(EQ_STEPS):
        left = 64 + width * index + 6
        count = counts[step]
        center = left + (width - 12) / 2
        if count < 2000:
            top = by(count)
            parts.append(
                f'<rect x="{left:.1f}" y="{top:.1f}" width="{width - 12:.1f}" '
                f'height="{520 - top:.1f}" fill="{UPDATE if step == 0.25 else LINE}"/>'
            )
            parts.append(_text(center, top - 6, str(count), "tick", "middle"))
        else:
            parts.append(_text(center, 510, "×", "tick", "middle"))
        parts.append(_text(center, 540, f"{step:g}", "tick", "middle"))
    parts.append(_text(410, 556, "歩幅 γ（×は着かない）", "tick", "end"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


FIGURES: dict[str, Callable[[], str]] = {
    "equilibrium-bakery-profit.svg": _eq_profit_svg,
    "equilibrium-projection-steps.svg": _eq_steps_svg,
}
