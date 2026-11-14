"""High-dimensional black box (content/concepts/high-dimensional-black-box.md): a device with n
knobs in [0, 1], score = mean squared miss from 0.6. 200 evaluations are spent on random points.
"""

from __future__ import annotations

import math
import random
from collections.abc import Callable, Sequence

from ._svg import GRID, INK, LINE, UPDATE, _open, _scale, _text

_PA015_BUDGET = 200
_PA015_IDEAL = 0.6
_PA015_BOX_HALF = 0.1  # the "small box" is 0.5 <= every knob <= 0.7, side 0.2
_PA015_BOX_DIMS = (1, 2, 3, 4, 5, 6)
_PA015_SEARCH_DIMS = (2, 5, 10, 20, 50)
_PA015_REPS = 200
_PA015_SEED = 0
_PA015_CACHE: dict[int, dict[str, float]] = {}


def _pa015_score(x: Sequence[float]) -> float:
    return sum((v - _PA015_IDEAL) ** 2 for v in x) / len(x)


def _pa015_score_two(x: Sequence[float]) -> float:
    return ((x[0] - _PA015_IDEAL) ** 2 + (x[1] - _PA015_IDEAL) ** 2) / 2


def _pa015_median_best(n: int, score: Callable[[Sequence[float]], float]) -> float:
    rng = random.Random(_PA015_SEED)
    bests = sorted(
        min(score([rng.random() for _ in range(n)]) for _ in range(_PA015_BUDGET))
        for _ in range(_PA015_REPS)
    )
    return (bests[_PA015_REPS // 2 - 1] + bests[_PA015_REPS // 2]) / 2


def _pa015_expected_hits(n: int) -> float:
    return _PA015_BUDGET * (2 * _PA015_BOX_HALF) ** n


def _pa015_search_data() -> dict[int, dict[str, float]]:
    if not _PA015_CACHE:
        for n in _PA015_SEARCH_DIMS:
            _PA015_CACHE[n] = {
                "all": _pa015_median_best(n, _pa015_score),
                "two": _pa015_median_best(n, _pa015_score_two),
            }
    return _PA015_CACHE


def _pa015_typical_score() -> float:
    return (0.4**3 + 0.6**3) / 3  # mean score of a uniformly drawn knob position


def _pa015_label(value: float) -> str:
    return f"{value:.3g}" if value >= 0.01 else f"{value:.2g}"


def _pa015_budget_svg() -> str:
    search = _pa015_search_data()
    parts = _open(
        "つまみの数と、200回の届き方",
        (
            "つまみの数を増やしたとき、200回の評価で何が変わるかを2つのパネルで示します。"
            "小箱（全部のつまみが0.5から0.7）に入る点の期待数は、つまみ3本で"
            f"{_pa015_label(_pa015_expected_hits(3))}、4本で{_pa015_label(_pa015_expected_hits(4))}です。"
            "ランダム探索の最良スコアの中央値は、つまみ2本で"
            f"{search[2]['all']:.4f}、50本で{search[50]['all']:.4f}です。"
        ),
        618,
    )
    px_left, px_right = 56.0, 420.0

    # Panel 1: expected number of random points inside the small box, log scale.
    top, height = 74.0, 150.0
    low, high = 0.01, 100.0
    py = _scale(math.log10(low), math.log10(high), top + height, top)
    parts.append(_text(20, top - 12, "① 小箱に入る点の期待数（200点中）"))
    parts.append(
        f'<path d="M{px_left:.0f} {top:.0f}V{top + height:.0f}H{px_right:.0f}" fill="none" '
        f'stroke="{GRID}" stroke-width="1.5"/>'
    )
    for tick in (0.01, 1.0, 100.0):
        parts.append(_text(48, py(math.log10(tick)) + 5, f"{tick:g}", "", "end"))
        parts.append(
            f'<path d="M52 {py(math.log10(tick)):.1f}H{px_right:.0f}" stroke="{GRID}" '
            'stroke-width="0.8" opacity="0.6"/>'
        )
    slot = (px_right - px_left) / len(_PA015_BOX_DIMS)
    for index, n in enumerate(_PA015_BOX_DIMS):
        value = _pa015_expected_hits(n)
        center = px_left + slot * (index + 0.5)
        color = LINE if value >= 1.0 else UPDATE
        y_top = py(math.log10(value))
        parts.append(
            f'<rect x="{center - 17:.1f}" y="{y_top:.1f}" width="34" '
            f'height="{top + height - y_top:.1f}" fill="{color}" opacity="0.85"/>'
        )
        parts.append(_text(center, y_top - 6, _pa015_label(value), "", "middle"))
        parts.append(_text(center, top + height + 22, str(n), "", "middle"))
    parts.append(
        f'<path d="M{px_left:.0f} {py(0.0):.1f}H{px_right:.0f}" stroke="{INK}" '
        'stroke-width="1.5" stroke-dasharray="5 4"/>'
    )
    parts.append(_text(20, top + height + 48, "横軸：つまみの数 n　縦軸：期待個数（対数）", "note"))

    # Panel 2: median best score of 200 random points, linear scale.
    top = 74.0 + 262.0
    py = _scale(0.1, 0.0, top, top + height)
    parts.append(_text(20, top - 12, "② ランダム200点の最良スコア（中央値）"))
    parts.append(
        f'<path d="M{px_left:.0f} {top:.0f}V{top + height:.0f}H{px_right:.0f}" fill="none" '
        f'stroke="{GRID}" stroke-width="1.5"/>'
    )
    for tick in (0.0, 0.05, 0.1):
        parts.append(_text(48, py(tick) + 5, f"{tick:g}", "", "end"))
        parts.append(
            f'<path d="M52 {py(tick):.1f}H{px_right:.0f}" stroke="{GRID}" stroke-width="0.8" '
            'opacity="0.6"/>'
        )
    typical = _pa015_typical_score()
    parts.append(
        f'<path d="M{px_left:.0f} {py(typical):.1f}H{px_right:.0f}" stroke="{UPDATE}" '
        'stroke-width="2" stroke-dasharray="6 4"/>'
    )
    parts.append(
        _text(px_right, py(typical) + 20, f"ランダムな1点の平均 {typical:.3f}", "note", "end")
    )
    slot = (px_right - px_left) / len(_PA015_SEARCH_DIMS)
    for index, n in enumerate(_PA015_SEARCH_DIMS):
        center = px_left + slot * (index + 0.5)
        value, two = search[n]["all"], search[n]["two"]
        y_top = py(value)
        parts.append(
            f'<rect x="{center - 20:.1f}" y="{y_top:.1f}" width="40" '
            f'height="{top + height - y_top:.1f}" fill="{LINE}" opacity="0.85"/>'
        )
        parts.append(_text(center, y_top - 6, f"{value:.4f}".rstrip("0"), "", "middle"))
        parts.append(_text(center, top + height + 22, str(n), "", "middle"))
        cy = py(two)
        parts.append(
            f'<path d="M{center:.1f} {cy - 8:.1f}L{center + 8:.1f} {cy:.1f}'
            f'L{center:.1f} {cy + 8:.1f}L{center - 8:.1f} {cy:.1f}Z" fill="{INK}"/>'
        )
    parts.append(_text(20, top + height + 48, "横軸：つまみの数 n　縦軸：スコア", "note"))
    parts.append(_text(20, 566, "緑の棒：全部のつまみが効く　黒のひし形：2本だけ効く"))
    parts.append(_text(20, 590, "橙の棒：期待数が1個未満　破線：期待数1個", "note"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


FIGURES: dict[str, Callable[[], str]] = {
    "high-dimensional-black-box-budget.svg": _pa015_budget_svg,
}
