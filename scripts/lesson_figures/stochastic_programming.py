"""Stochastic programming (content/concepts/stochastic-programming.md): lunch boxes made in the
morning at 100 yen; any shortage is brought in from a nearby shop at 250 yen each.
"""

from __future__ import annotations

from collections.abc import Callable

from ._svg import GRID, INK, LINE, MUTED, POINT, RING, UPDATE, _open, _polyline, _scale, _text

SP_MAKE, SP_BUY = 100, 250
SP_SCENARIOS = (("雨", 20, 0.3), ("曇り", 40, 0.4), ("晴れ", 80, 0.3))


def sp_cost(made: float, demand: float) -> float:
    return SP_MAKE * made + SP_BUY * max(demand - made, 0.0)


def sp_expected(made: float) -> float:
    return sum(p * sp_cost(made, d) for _, d, p in SP_SCENARIOS)


def sp_mean_demand() -> float:
    return sum(p * d for _, d, p in SP_SCENARIOS)


def sp_best() -> tuple[int, float]:
    """The minimiser over whole boxes (the expected cost is piecewise linear in made)."""
    return min(((made, sp_expected(made)) for made in range(0, 101)), key=lambda r: r[1])


def _sp_cost_svg() -> str:
    best, best_cost = sp_best()
    mean = sp_mean_demand()
    worst = max(d for _, d, _ in SP_SCENARIOS)
    parts = _open(
        "天気ごとの費用と、その期待値",
        (
            f"朝に作る弁当の数 x（0〜100個）と費用。1個{SP_MAKE}円で作り、"
            f"足りない分は1個{SP_BUY}円で取り寄せる。"
            "① 注文が雨20個・曇り40個・晴れ80個の三つの場合の費用の折れ線。"
            "② 確率0.3・0.4・0.3で重みを付けた期待費用。"
            f"期待費用は x={best} で最小の {best_cost:g} 円、平均の注文の数 {mean:g} 個では "
            f"{sp_expected(mean):g} 円、最大の注文の数 {worst} 個では {sp_expected(worst):g} 円。"
        ),
        622,
    )
    px = _scale(0.0, 100.0, 76, 410)
    for tick in (0, 20, 40, 60, 80, 100):
        parts.append(_text(px(tick), 300, str(tick), "tick", "middle"))
        parts.append(_text(px(tick), 584, str(tick), "tick", "middle"))
    parts.append(_text(20, 64, "① 天気ごとの費用（千円）"))
    py = _scale(0.0, 25000.0, 280, 80)
    parts.append(f'<path d="M76 80V280H410" fill="none" stroke="{GRID}"/>')
    for value in (0, 10000, 20000):
        parts.append(_text(68, py(value) + 5, str(value // 1000), "tick", "end"))
    colors = {"雨": RING, "曇り": LINE, "晴れ": INK}
    for index, (name, demand, _) in enumerate(reversed(SP_SCENARIOS)):
        points = [(px(x), py(sp_cost(x, demand))) for x in (0, demand, 100)]
        parts.append(_polyline(points, colors[name], 2.5))
        y = 104 + 24 * index
        parts.append(_polyline([(300, y - 5), (322, y - 5)], colors[name], 2.5))
        parts.append(_text(330, y, f"{name} {demand}個", "tick"))
    parts.append(_text(20, 340, "② 期待費用（千円）"))
    gy = _scale(6000.0, 12000.0, 564, 364)
    parts.append(f'<path d="M76 364V564H410" fill="none" stroke="{GRID}"/>')
    for value in (6000, 8000, 10000, 12000):
        parts.append(_text(68, gy(value) + 5, str(value // 1000), "tick", "end"))
    kinks = [0, *sorted(d for _, d, _ in SP_SCENARIOS), 100]
    parts.append(_polyline([(px(x), gy(sp_expected(x))) for x in kinks], MUTED, 3))
    marks = (
        (best, UPDATE, f"x={best}：{sp_expected(best):g}円", -12, 26),
        (mean, POINT, f"x={mean:g}：{sp_expected(mean):g}円", 14, 26),
        (worst, GRID, f"x={worst}：{sp_expected(worst):g}円", -12, -12),
    )
    for x, color, label, shift, lift in marks:
        parts.append(
            f'<circle cx="{px(x):.1f}" cy="{gy(sp_expected(x)):.1f}" r="7" fill="{color}" '
            f'stroke="{INK}" stroke-width="1.5"/>'
        )
        anchor = "start" if shift > 0 else "end"
        parts.append(_text(px(x) + shift, gy(sp_expected(x)) + lift, label, "tick", anchor))
    parts.append(_text(410, 604, "朝に作る数 x（個）", "tick", "end"))
    parts.append(_text(20, 604, f"最小は x={best}", "note"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


def _sp_tree_svg() -> str:
    """One morning decision shared by every branch; the afternoon decision differs by branch."""
    best, _ = sp_best()
    parts = _open(
        "朝の決定は一つ、昼の対応は天気ごと",
        (
            f"朝に作る数 x は天気を知る前に一つだけ決める（例では x={best}）。"
            "天気が分かった後の取り寄せ数 y は、雨・曇り・晴れの枝ごとに別々に決める。"
            f"x={best} なら y は雨0・曇り0・晴れ{80 - best}。"
        ),
        370,
    )
    root = (70.0, 210.0)
    parts.append(
        f'<rect x="{root[0] - 50}" y="{root[1] - 34}" width="100" height="68" rx="10" '
        f'fill="#f3d2b5" stroke="{UPDATE}" stroke-width="2.5"/>'
    )
    parts.append(_text(root[0], root[1] - 6, "朝", "", "middle"))
    parts.append(_text(root[0], root[1] + 18, f"x={best}", "", "middle"))
    for index, (name, demand, prob) in enumerate(SP_SCENARIOS):
        y = 120.0 + 90.0 * index
        bring = max(demand - best, 0)
        parts.append(
            f'<path d="M{root[0] + 50} {root[1]}L250 {y}" stroke="{GRID}" stroke-width="2"/>'
        )
        parts.append(_text(185, (root[1] + y) / 2 - 10, f"{prob:g}", "tick", "middle"))
        parts.append(
            f'<rect x="250" y="{y - 30}" width="170" height="60" rx="10" fill="#ffffff" '
            f'stroke="{LINE}" stroke-width="2"/>'
        )
        parts.append(_text(262, y - 6, f"{name}：注文 {demand}"))
        parts.append(_text(262, y + 18, f"取り寄せ y={bring}", "note"))
    parts.append(_text(20, 64, "天気が分かる前", "tick"))
    parts.append(_text(420, 64, "天気が分かった後", "tick", "end"))
    parts.append(_text(20, 358, "線の数字は天気の確率", "tick"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


FIGURES: dict[str, Callable[[], str]] = {
    "stochastic-programming-expected-cost.svg": _sp_cost_svg,
    "stochastic-programming-two-stage.svg": _sp_tree_svg,
}
