"""General conic optimization (content/concepts/general-conic-optimization.md): split a promotion
budget of 6 across three stores, effect sum w_i log(1 + x_i) with w = (3, 2, 1), and keep the spread
||x - mean(x)||_2 <= 1.5. Cones: three exponential, one second-order, nonnegative.
"""

from __future__ import annotations

import functools
import math
from collections.abc import Callable, Sequence

from ._svg import GRID, LINE, MUTED, POINT, UPDATE, _open, _polyline, _scale, _text

CN_WEIGHTS = (3.0, 2.0, 1.0)
CN_BUDGET = 6.0
CN_SPREAD = 1.5
CN_COLORS = (POINT, UPDATE, LINE)


def cn_effect(x: Sequence[float]) -> float:
    return sum(w * math.log1p(v) for w, v in zip(CN_WEIGHTS, x, strict=True))


@functools.cache
def cn_solve(spread: float = CN_SPREAD, budget: float = CN_BUDGET) -> tuple[float, ...]:
    """Maximize the effect with the whole budget spent and the spread at its limit.

    Both limits are active in this example, so x = mean + spread * (cos f e1 + sin f e2) with
    e1, e2 an orthonormal basis of the plane sum(x) = 0; search f on a grid, then refine.
    """
    e1 = (1 / math.sqrt(2), -1 / math.sqrt(2), 0.0)
    e2 = (1 / math.sqrt(6), 1 / math.sqrt(6), -2 / math.sqrt(6))

    def alloc(f: float) -> list[float]:
        return [
            budget / 3 + spread * (math.cos(f) * a + math.sin(f) * b)
            for a, b in zip(e1, e2, strict=True)
        ]

    grid = [-math.pi + 2 * math.pi * k / 3600 for k in range(3600)]
    best = max(grid, key=lambda f: cn_effect(alloc(f)))
    lo, hi = best - 2 * math.pi / 3600, best + 2 * math.pi / 3600
    ratio = (math.sqrt(5) - 1) / 2
    for _ in range(100):
        a, b = hi - ratio * (hi - lo), lo + ratio * (hi - lo)
        if cn_effect(alloc(a)) > cn_effect(alloc(b)):
            hi = b
        else:
            lo = a
    return tuple(alloc((lo + hi) / 2))


def cn_multipliers(x: Sequence[float]) -> tuple[float, float]:
    """(budget, spread) multipliers from w_i / (1 + x_i) = lam + mu * d_i / |d|."""
    grad = [w / (1 + v) for w, v in zip(CN_WEIGHTS, x, strict=True)]
    mean = sum(x) / 3
    d = [v - mean for v in x]
    norm = math.sqrt(sum(v * v for v in d))
    return sum(grad) / 3, sum(g * v / norm for g, v in zip(grad, d, strict=True))


CN_PLANS = (
    ("対数だけ（ばらつきの上限なし）", (3.5, 2.0, 0.5)),
    ("ばらつきの上限 1.5 あり", None),
    ("対数を2次式で近似", (1.0, 1.0, 1.0)),
)


def _cn_allocation_svg() -> str:
    x = cn_solve()
    parts = _open(
        "3店への販促費と、効果",
        (
            "① 店ごとの効果 w log(1+x)（w は3・2・1）。"
            "点は、予算6とばらつきの上限1.5のもとでの答え "
            + "・".join(f"{v:.2f}" for v in x)
            + "。② 3つの決め方の配分と効果の合計。"
            + "、".join(f"{name}は {cn_effect(plan or x):.2f}" for name, plan in CN_PLANS)
            + "。"
        ),
        600,
    )
    px = _scale(0.0, 4.0, 64, 410)
    py = _scale(0.0, 5.0, 272, 84)
    parts.append(_text(20, 64, "① 店ごとの効果 w log(1 + x)"))
    parts.append(f'<path d="M64 84V272H410" fill="none" stroke="{GRID}"/>')
    for value in (0, 2, 4):
        parts.append(_text(56, py(value) + 5, f"{value}", "tick", "end"))
    for value in range(5):
        parts.append(_text(px(value), 292, f"{value}", "tick", "middle"))
    names = ("店1（w=3）", "店2（w=2）", "店3（w=1）")
    for w, xi, color, name in zip(CN_WEIGHTS, x, CN_COLORS, names, strict=True):
        curve = [(px(4 * k / 120), py(w * math.log1p(4 * k / 120))) for k in range(121)]
        parts.append(_polyline(curve, color, 3))
        parts.append(
            f'<circle cx="{px(xi):.1f}" cy="{py(w * math.log1p(xi)):.1f}" r="6" fill="{color}" '
            f'stroke="#ffffff" stroke-width="1.5"/>'
        )
        parts.append(_text(px(4.0) - 4, py(w * math.log1p(4.0)) - 8, name, "tick", "end"))
    parts.append(_text(410, 314, "販促費 x", "tick", "end"))

    parts.append(_text(20, 358, "② 3つの決め方の配分と、効果の合計"))
    bx = _scale(0.0, 6.0, 64, 300)
    for row, (name, plan) in enumerate(CN_PLANS):
        q = plan or x
        y = 400 + 58 * row
        parts.append(_text(64, y - 8, name, "tick"))
        left = 64.0
        for qi, color in zip(q, CN_COLORS, strict=True):
            width = bx(qi) - 64
            parts.append(
                f'<rect x="{left:.1f}" y="{y:.1f}" width="{width:.1f}" height="18" fill="{color}"/>'
            )
            left += width
        parts.append(_text(318, y + 15, f"効果 {cn_effect(q):.2f}", "tick"))
    parts.append(
        f'<path d="M{bx(CN_BUDGET):.1f} 384V540" stroke="{MUTED}" stroke-width="1.5" '
        'stroke-dasharray="5 4"/>'
    )
    parts.append(_text(bx(CN_BUDGET), 556, "予算6", "tick", "middle"))
    for index, color in enumerate(CN_COLORS):
        x0 = 64 + 70 * index
        parts.append(f'<rect x="{x0}" y="572" width="14" height="14" fill="{color}"/>')
        parts.append(_text(x0 + 20, 584, f"店{index + 1}", "tick"))
    parts.append(_text(410, 584, "横は販促費（合計6）", "tick", "end"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


def cn_blocks() -> list[tuple[str, list[float], str]]:
    """The stacked vector b - Ax at the answer, split by cone, with each block's check."""
    x = cn_solve()
    t = [math.log1p(v) for v in x]
    mean = sum(x) / 3
    d = [v - mean for v in x]
    blocks = [
        (f"指数錐{i + 1}", [ti, 1.0, 1 + xi], f"e^{ti:.3f} = {math.exp(ti):.2f} ≦ {1 + xi:.2f}")
        for i, (ti, xi) in enumerate(zip(t, x, strict=True))
    ]
    norm = math.sqrt(sum(v * v for v in d))
    blocks.append(("二次錐", [CN_SPREAD, *d], f"長さ {norm:.2f} ≦ {CN_SPREAD:g}"))
    blocks.append(("非負の象限", [CN_BUDGET - sum(x), *x], "どれも 0 以上"))
    return blocks


def _cn_blocks_svg() -> str:
    blocks = cn_blocks()
    rows = sum(len(v) for _, v, _ in blocks)
    parts = _open(
        "b − Az を、錐ごとに区切る",
        (
            f"答えの点での {rows} 行のベクトル b − Az を、5つの錐に区切ったもの。"
            + "。".join(
                f"{name}：("
                + ", ".join(f"{v:.2f}".replace("-", "−") for v in values)
                + f")、{check}"
                for name, values, check in blocks
            )
            + "。"
        ),
        84 + 76 * len(blocks),
    )
    colors = {"指数錐": POINT, "二次錐": UPDATE, "非負の象限": LINE}
    for row, (name, values, check) in enumerate(blocks):
        y = 64 + 76 * row
        color = next(c for key, c in colors.items() if name.startswith(key))
        parts.append(_text(20, y + 22, name, "tick"))
        for k, value in enumerate(values):
            left = 108 + 64 * k
            parts.append(
                f'<rect x="{left}" y="{y}" width="58" height="32" rx="4" fill="#ffffff" '
                f'stroke="{color}" stroke-width="2"/>'
            )
            parts.append(
                _text(left + 29, y + 22, f"{value:.2f}".replace("-", "−"), "tick", "middle")
            )
        parts.append(_text(108, y + 54, check, "note"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


FIGURES: dict[str, Callable[[], str]] = {
    "conic-promo-allocation.svg": _cn_allocation_svg,
    "conic-blocks.svg": _cn_blocks_svg,
}
