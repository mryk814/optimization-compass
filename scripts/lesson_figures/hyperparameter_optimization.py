"""Hyperparameter optimization (content/concepts/hyperparameter-optimization.md): a ridge polynomial
fit on 30 noisy points; the objective is the 5-fold cross-validation error.
"""

from __future__ import annotations

import math
import random
from collections.abc import Callable, Sequence

from ._numeric import _solve_linear
from ._svg import LINE, POINT, UPDATE, _open, _scale, _text

HPO_N = 30
HPO_SIGMA = 0.4
HPO_LOG_LAM = (-6.0, 1.0)
HPO_DEGREES = list(range(2, 16))
HPO_DATA_SEED = 1
HPO_BUDGET = 16
HPO_RANDOM_SEED = 0
HPO_GRID_DEGREES = (2, 6, 11, 15)


def hpo_data(seed: int = HPO_DATA_SEED, n: int = HPO_N) -> tuple[list[float], list[float]]:
    rng = random.Random(seed)
    xs = [rng.uniform(-1, 1) for _ in range(n)]
    ys = [math.sin(3 * v) + 0.5 * v + HPO_SIGMA * rng.gauss(0, 1) for v in xs]
    return xs, ys


def _legendre_row(x: float, degree: int) -> list[float]:
    row = [1.0, x]
    for n in range(2, degree + 1):
        row.append(((2 * n - 1) * x * row[n - 1] - (n - 1) * row[n - 2]) / n)
    return row[: degree + 1]


def _hpo_fit(xs: Sequence[float], ys: Sequence[float], degree: int, lam: float) -> list[float]:
    rows = [_legendre_row(x, degree) for x in xs]
    size = degree + 1
    gram = [
        [sum(r[i] * r[j] for r in rows) + (len(xs) * lam if i == j else 0.0) for j in range(size)]
        for i in range(size)
    ]
    rhs = [sum(r[i] * y for r, y in zip(rows, ys, strict=True)) for i in range(size)]
    return _solve_linear(gram, rhs)


def hpo_cv_mse(
    xs: Sequence[float],
    ys: Sequence[float],
    degree: int,
    lam: float,
    k: int = 5,
    split_seed: int = 0,
) -> float:
    order = list(range(len(xs)))
    random.Random(split_seed).shuffle(order)
    errors = []
    for i in range(k):
        fold = order[i::k]
        train = [j for j in order if j not in fold]
        w = _hpo_fit([xs[j] for j in train], [ys[j] for j in train], degree, lam)
        squares = [
            (sum(c * b for c, b in zip(w, _legendre_row(xs[j], degree), strict=True)) - ys[j]) ** 2
            for j in fold
        ]
        errors.append(sum(squares) / len(squares))
    return sum(errors) / k


def hpo_random_configs(seed: int = HPO_RANDOM_SEED, n: int = HPO_BUDGET) -> list[tuple[int, float]]:
    rng = random.Random(seed)
    low, high = HPO_LOG_LAM
    return [(rng.choice(HPO_DEGREES), 10.0 ** rng.uniform(low, high)) for _ in range(n)]


def hpo_grid_configs() -> list[tuple[int, float]]:
    low, high = HPO_LOG_LAM
    exponents = [low + (high - low) * i / 3 for i in range(4)]
    return [(d, 10.0**e) for d in HPO_GRID_DEGREES for e in exponents]


def hpo_search_data() -> dict[str, object]:
    xs, ys = hpo_data()
    out: dict[str, object] = {}
    for name, configs in (("grid", hpo_grid_configs()), ("random", hpo_random_configs())):
        values = [hpo_cv_mse(xs, ys, d, lam) for d, lam in configs]
        best = min(range(len(configs)), key=lambda i: values[i])
        out[name] = {
            "configs": configs,
            "values": values,
            "best": best,
            "distinct_lam": len({lam for _, lam in configs}),
            "distinct_degree": len({d for d, _ in configs}),
        }
    low, high = HPO_LOG_LAM
    columns = int((high - low) * 2)
    out["terrain"] = {
        (d, c): hpo_cv_mse(xs, ys, d, 10.0 ** (low + (c + 0.5) / 2))
        for d in HPO_DEGREES
        for c in range(columns)
    }
    return out


def _hpo_shade(value: float) -> str:
    """Grey ramp for the cross-validation error: pale at 0.13 or less, dark at 1 or more."""
    t = (math.log10(max(value, 0.13)) - math.log10(0.13)) / (math.log10(1.0) - math.log10(0.13))
    t = min(max(t, 0.0), 1.0)
    low, high = (0xEE, 0xF0, 0xEA), (0x7C, 0x86, 0x7E)
    r, g, b = (round(a + (c - a) * t) for a, c in zip(low, high, strict=True))
    return f"#{r:02x}{g:02x}{b:02x}"


def _hpo_search_svg() -> str:
    data = hpo_search_data()
    terrain = data["terrain"]
    low, high = HPO_LOG_LAM
    grid, rand = data["grid"], data["random"]
    parts = _open(
        "同じ16回で試す設定",
        (
            "次数と正則化の強さの2つの設定を、評価16回で探す2つの方法です。"
            f"格子ではlog10 λの値が{grid['distinct_lam']}種類、"  # type: ignore[index]
            f"ランダムでは{rand['distinct_lam']}種類（seed 0）になります。"  # type: ignore[index]
            f"背景の灰色の濃さは交差検証誤差で、16点の最良は格子が{grid['values'][grid['best']]:.3f}、"  # type: ignore[index]
            f"ランダムが{rand['values'][rand['best']]:.3f}です。"  # type: ignore[index]
        ),
        596,
    )
    px = _scale(low, high, 64, 420)
    cell_w = (420 - 64) / ((high - low) * 2)
    cell_h = 10
    for index, (key, label) in enumerate(
        (
            ("grid", "格子（4×4）：λは{n}種類"),
            ("random", "ランダム：λは{n}種類"),
        )
    ):
        top = 66 + index * 216
        group = data[key]
        parts.append(_text(20, top - 12, label.format(n=group["distinct_lam"])))  # type: ignore[index]
        for d in HPO_DEGREES:
            y = top + (15 - d) * cell_h
            for c in range(int((high - low) * 2)):
                parts.append(
                    f'<rect x="{64 + c * cell_w:.2f}" y="{y}" width="{cell_w + 0.4:.2f}" '
                    f'height="{cell_h}" fill="{_hpo_shade(terrain[(d, c)])}"/>'  # type: ignore[index]
                )
        parts.append(
            f'<path d="M64 {top}V{top + 14 * cell_h}H420" fill="none" stroke="{POINT}" '
            'stroke-width="1.5"/>'
        )
        for d in (2, 8, 15):
            parts.append(_text(56, top + (15 - d) * cell_h + 9, f"{d}", "tick", "end"))
        for e in (-6, -4, -2, 0):
            parts.append(_text(px(e), top + 14 * cell_h + 36, f"{e}", "tick", "middle"))
        for _, lam in group["configs"]:  # type: ignore[index]
            parts.append(
                f'<path d="M{px(math.log10(lam)):.2f} {top + 14 * cell_h + 3}v10" '
                f'stroke="{POINT}" stroke-width="2"/>'
            )
        for i, (d, lam) in enumerate(group["configs"]):  # type: ignore[index]
            cx, cy = px(math.log10(lam)), top + (15 - d) * cell_h + cell_h / 2
            parts.append(
                f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="4.5" fill="{LINE}" stroke="#f7f8f3" '
                'stroke-width="1.5"/>'
            )
            if i == group["best"]:  # type: ignore[index]
                parts.append(
                    f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="9" fill="none" stroke="{UPDATE}" '
                    'stroke-width="3"/>'
                )
    parts.append(_text(420, 66 + 216 + 14 * cell_h + 58, "log10 λ", "tick", "end"))
    parts.append(_text(70, 66 + 216 + 14 * cell_h + 58, "各パネルの縦は次数 d", "tick"))
    parts.append(_text(20, 520, "緑の丸：評価した設定　橙の輪：16点のうちの最良"))
    parts.append(_text(20, 544, "紺の短い線：試したλの値　灰が濃いほど誤差が大きい", "note"))
    parts.append(
        _text(
            20,
            568,
            f"最良の誤差　格子 {grid['values'][grid['best']]:.3f}　"  # type: ignore[index]
            f"ランダム {rand['values'][rand['best']]:.3f}",
            "note",
        )
    )
    parts.append("</svg>")
    return "".join(parts) + "\n"


FIGURES: dict[str, Callable[[], str]] = {
    "hpo-search-points.svg": _hpo_search_svg,
}
