"""Online optimization (content/concepts/online-optimization.md): every morning a shop splits its ad
budget between media A and B (x = share to A); each day's results per share are known only in the
evening. Two sequences: alternating days, and an A, A, B pattern.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence

from ._svg import GRID, LINE, MUTED, POINT, UPDATE, _open, _polyline, _scale, _text

OL_STEP_HORIZONS = (10, 100, 1000, 10000)


def ol_alternating(days: int) -> list[tuple[float, float]]:
    """(A, B) results: day 1 is (1.5, 1.0), then B wins on even days and A on odd days."""
    return [(1.5, 1.0)] + [((1.0, 2.0) if t % 2 == 0 else (2.0, 1.0)) for t in range(2, days + 1)]


def ol_pattern(days: int) -> list[tuple[float, float]]:
    """(A, B) results repeating A, A, B: A wins two days out of three."""
    return [((1.0, 2.0) if t % 3 == 0 else (2.0, 1.0)) for t in range(1, days + 1)]


def ol_play(results: Sequence[tuple[float, float]], rule: str) -> tuple[list[float], float]:
    """Shares chosen each morning and the regret against the better medium in hindsight."""
    days = len(results)
    x, lead, shares, gained = 0.5, 0.0, [], 0.0
    for a, b in results:
        if rule == "leader":
            x = 0.5 if lead == 0 else (1.0 if lead > 0 else 0.0)
        elif rule == "half":
            x = 0.5
        shares.append(x)
        gained += x * a + (1 - x) * b
        lead += a - b
        if rule == "ogd":
            x = min(1.0, max(0.0, x + (a - b) / math.sqrt(days)))
    best = max(sum(a for a, _ in results), sum(b for _, b in results))
    return shares, best - gained


OL_RULES = (
    ("leader", "勝ち側に全額", POINT),
    ("half", "いつも半分", MUTED),
    ("ogd", "勾配で少しずつ", UPDATE),
)


def _ol_days_svg() -> str:
    days = ol_alternating(10)
    parts = _open(
        "交互に入れ替わる10日間と、毎朝の割合",
        (
            "① 媒体A・Bの1日の成果（広告費1あたり）。1日目はA1.5・B1.0、"
            "その後は偶数日にB、奇数日にAが2倍。"
            "② 毎朝Aに回す割合 x。前日までの合計が多い側に全額を回すと、"
            "2日目から毎日負ける側を選ぶ。"
            "勾配で少しずつ動かす決め方（学習率 η=1/√10）は0.34と0.66の間を行き来する。"
        ),
        560,
    )
    px = _scale(1.0, 10.0, 84, 400)
    for day in range(1, 11):
        parts.append(_text(px(day), 272, str(day), "tick", "middle"))
        parts.append(_text(px(day), 520, str(day), "tick", "middle"))
    parts.append(_text(20, 64, "① 1日の成果"))
    ay = _scale(0.5, 2.0, 252, 84)
    parts.append(f'<path d="M64 84V252H410" fill="none" stroke="{GRID}"/>')
    for value in (1, 2):
        parts.append(_text(56, ay(value) + 5, str(value), "tick", "end"))
    for index, (name, color, dash) in enumerate((("A", LINE, ""), ("B", MUTED, "5 4"))):
        points = [(px(t + 1), ay(r[index])) for t, r in enumerate(days)]
        line = _polyline(points, color, 2.5)
        if dash:
            line = line.replace("/>", f' stroke-dasharray="{dash}"/>')
        parts.append(line)
        for x, y in points:
            parts.append(
                f'<rect x="{x - 4:.1f}" y="{y - 4:.1f}" width="8" height="8" fill="{color}"/>'
            )
        x0 = 100 + 110 * index
        parts.append(_polyline([(x0, 300 - 5), (x0 + 22, 300 - 5)], color, 2.5))
        parts.append(_text(x0 + 28, 300, f"媒体{name}", "tick"))
    parts.append(_text(20, 344, "② 毎朝Aに回す割合 x"))
    xy = _scale(0.0, 1.0, 500, 364)
    parts.append(f'<path d="M64 364V500H410" fill="none" stroke="{GRID}"/>')
    for value in (0, 0.5, 1):
        parts.append(_text(56, xy(value) + 5, f"{value:g}", "tick", "end"))
    for rule, _, color in (OL_RULES[0], OL_RULES[2]):
        shares, _ = ol_play(days, rule)
        points = [(px(t + 1), xy(s)) for t, s in enumerate(shares)]
        parts.append(_polyline(points, color, 2.5))
        for x, y in points:
            parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.5" fill="{color}"/>')
    parts.append(
        _text(20, 548, "紺：前日までの勝ち側に全額", "tick").replace(
            "<text ", f'<text style="fill:{POINT}" '
        )
    )
    parts.append(
        _text(250, 548, "橙：勾配で少しずつ", "tick").replace(
            "<text ", f'<text style="fill:{UPDATE}" '
        )
    )
    parts.append(_text(400, 300, "日", "tick", "end"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


def _ol_regret_svg() -> str:
    sequences = (("① 交互に入れ替わる日", ol_alternating), ("② A・A・Bの繰り返し", ol_pattern))
    regrets = {
        (name, rule): [ol_play(seq(days), rule)[1] for days in OL_STEP_HORIZONS]
        for name, seq in sequences
        for rule, _, _ in OL_RULES
    }
    parts = _open(
        "日数が増えると、後悔はどう増えるか",
        (
            "後悔＝後から見てよかった方の媒体に毎日全額を回した場合との差。"
            "横は日数 T、縦は後悔（どちらも対数目盛）。"
            "破線は √T。"
            + "。".join(
                f"{name}："
                + "、".join(f"{label} {regrets[(name, rule)][1]:g}" for rule, label, _ in OL_RULES)
                + "（T=100）"
                for name, _ in sequences
            )
            + "。"
        ),
        620,
    )
    px = _scale(1.0, 4.0, 84, 400)
    ly = {}
    for panel, (name, _) in enumerate(sequences):
        top = 84 + 260 * panel
        bottom = top + 180
        parts.append(_text(20, top - 20, name))
        ly[name] = _scale(-1.0, 4.0, bottom, top)
        y = ly[name]
        parts.append(f'<path d="M84 {top}V{bottom}H400" fill="none" stroke="{GRID}"/>')
        for exponent in (0, 2, 4):
            parts.append(_text(76, y(exponent) + 5, f"{10**exponent:g}", "tick", "end"))
        for exponent in (1, 2, 3, 4):
            parts.append(_text(px(exponent), bottom + 20, f"{10**exponent:g}", "tick", "middle"))
        root = [(px(e), y(e / 2)) for e in (1, 2, 3, 4)]
        parts.append(_polyline(root, MUTED, 1.5).replace("/>", ' stroke-dasharray="5 4"/>'))
        parts.append(_text(px(4) - 4, y(2) - 10, "√T", "tick", "end"))
        parts.append(_text(92, top + 4, "後悔", "tick"))
        for rule, _, color in OL_RULES:
            points = [
                (px(math.log10(days)), y(math.log10(max(value, 0.1))))
                for days, value in zip(OL_STEP_HORIZONS, regrets[(name, rule)], strict=True)
            ]
            parts.append(_polyline(points, color, 2.5))
            for x, yy in points:
                parts.append(f'<circle cx="{x:.1f}" cy="{yy:.1f}" r="4" fill="{color}"/>')
    for x0, (_, label, color) in zip((20, 210, 310), OL_RULES, strict=True):
        parts.append(
            _text(x0, 604, label, "tick").replace("<text ", f'<text style="fill:{color}" ')
        )
    parts.append(_text(400, 580, "日数 T", "tick", "end"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


FIGURES: dict[str, Callable[[], str]] = {
    "online-budget-days.svg": _ol_days_svg,
    "online-regret-growth.svg": _ol_regret_svg,
}
