"""Noisy black box (content/concepts/noisy-black-box.md): an oven temperature scored with noise. The
mean score is 2(x - 0.6)^2 and each bake adds N(0, 0.2^2) noise. 60 bakes are spent either on 60
temperatures once each or on 12 temperatures five times each.
"""

from __future__ import annotations

import math
import random
from collections.abc import Callable

from ._svg import GRID, INK, LINE, POINT, UPDATE, _open, _polyline, _scale, _text

OVEN_SIGMA = 0.2
OVEN_BUDGET = 60
OVEN_FIGURE_SEED = 0


def oven_true_score(x: float) -> float:
    return 2.0 * (x - 0.6) ** 2


def oven_bake(x: float, rng: random.Random) -> float:
    return oven_true_score(x) + rng.gauss(0.0, OVEN_SIGMA)


def oven_temperatures(k: int) -> list[float]:
    return [(i + 0.5) / k for i in range(k)]


def oven_reversal(n: int, gap: float, sigma: float = OVEN_SIGMA) -> float:
    """Probability that means of n bakes each order two temperatures the wrong way round."""
    z = gap / (sigma * math.sqrt(2.0 / n))
    return 0.5 * (1.0 + math.erf(-z / math.sqrt(2.0)))


def oven_spread(
    k: int, budget: int = OVEN_BUDGET, reps: int = 2000, seed: int = 1
) -> tuple[float, float]:
    """Mean true score of the chosen temperature, and mean (reported mean - true score)."""
    rng = random.Random(seed)
    n = budget // k
    xs = oven_temperatures(k)
    chosen, optimism = [], []
    for _ in range(reps):
        means = [sum(oven_bake(x, rng) for _ in range(n)) / n for x in xs]
        best = min(range(k), key=means.__getitem__)
        chosen.append(oven_true_score(xs[best]))
        optimism.append(means[best] - oven_true_score(xs[best]))
    return sum(chosen) / reps, sum(optimism) / reps


def oven_figure_data(seed: int = OVEN_FIGURE_SEED) -> list[dict[str, object]]:
    rng = random.Random(seed)
    panels = []
    for k in (60, 12):
        n = OVEN_BUDGET // k
        xs = oven_temperatures(k)
        observed = [[oven_bake(x, rng) for _ in range(n)] for x in xs]
        means = [sum(values) / n for values in observed]
        best = min(range(k), key=means.__getitem__)
        panels.append(
            {
                "k": k,
                "n": n,
                "xs": xs,
                "observed": observed,
                "means": means,
                "best": best,
                "true_at_best": oven_true_score(xs[best]),
            }
        )
    return panels


def _signed_3dp(value: float) -> str:
    return f"{value:.3f}".replace("-", "−")


def _noisy_oven_svg() -> str:
    panels = oven_figure_data()
    first, second = panels
    parts = _open(
        "同じ60回の焼き方",
        (
            "焼成温度を決めるために60回焼く2つの配分です。"
            f"60温度を1回ずつ測ると、最良の観測は{_signed_3dp(first['means'][first['best']])}"  # type: ignore[index]
            f"で、その温度の真の点数は{first['true_at_best']:.3f}です。"
            f"12温度を5回ずつ測ると、平均が最小の温度の平均は"
            f"{_signed_3dp(second['means'][second['best']])}"  # type: ignore[index]
            f"で、真の点数は{second['true_at_best']:.3f}です（乱数種{OVEN_FIGURE_SEED}の1回分）。"
        ),
        618,
    )
    px = _scale(0.0, 1.0, 56, 420)
    low, high = -0.8, 1.2
    for index, panel in enumerate(panels):
        top = 74 + index * 262
        height = 150
        py = _scale(high, low, top, top + height)
        label = "① 60温度を1回ずつ" if panel["k"] == 60 else "② 12温度を5回ずつ"
        parts.append(_text(20, top - 12, label))
        parts.append(
            f'<path d="M56 {top}V{top + height}H420" fill="none" stroke="{GRID}" '
            'stroke-width="1.5"/>'
        )
        for tick in (1.0, 0.0, -0.5):
            parts.append(_text(48, py(tick) + 5, f"{tick:g}".replace("-", "−"), "tick", "end"))
            parts.append(
                f'<path d="M52 {py(tick):.1f}H420" stroke="{GRID}" stroke-width="0.8" '
                'opacity="0.6"/>'
            )
        for tick in (0.0, 0.6, 1.0):
            parts.append(_text(px(tick), top + height + 22, f"{tick:g}", "tick", "middle"))
        curve = [(px(i / 100), py(oven_true_score(i / 100))) for i in range(101)]
        parts.append(_polyline(curve, LINE, 2.5))
        n = panel["n"]
        for x, values, mean in zip(panel["xs"], panel["observed"], panel["means"], strict=True):  # type: ignore[arg-type]
            for value in values:
                parts.append(
                    f'<circle cx="{px(x):.2f}" cy="{py(value):.2f}" r="3" fill="{POINT}" '
                    'opacity="0.55"/>'
                )
            if n > 1:
                parts.append(
                    f'<rect x="{px(x) - 4.5:.2f}" y="{py(mean) - 4.5:.2f}" width="9" height="9" '
                    f'fill="{INK}"/>'
                )
        best = panel["best"]
        bx, bm = panel["xs"][best], panel["means"][best]  # type: ignore[index]
        parts.append(
            f'<circle cx="{px(bx):.2f}" cy="{py(bm):.2f}" r="10" fill="none" stroke="{UPDATE}" '
            'stroke-width="3"/>'
        )
        what = "最良の観測" if n == 1 else "最良の平均"
        parts.append(
            _text(
                20,
                top + height + 48,
                f"{what} {_signed_3dp(bm)}、真の点数 {panel['true_at_best']:.3f}",
                "note",
            )
        )
    parts.append(_text(20, 566, "横軸：焼成温度 x　縦軸：点数（小さいほど良い）"))
    parts.append(_text(20, 590, "緑の線：真の点数　青の点：1回の焼成　黒の四角：平均", "note"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


FIGURES: dict[str, Callable[[], str]] = {
    "noisy-black-box-budget.svg": _noisy_oven_svg,
}
