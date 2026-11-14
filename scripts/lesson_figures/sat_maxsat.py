"""SAT and MaxSAT (content/concepts/sat-maxsat.md): whom to invite to a weekend study group.
Variables 1..5 are A..E (true = invite). Clauses list signed variable numbers.
"""

from __future__ import annotations

import itertools
from collections.abc import Callable, Sequence

from ._svg import INK, LINE, MUTED, POINT, UPDATE, _open, _text

SAT_NAMES = "ABCDE"
SAT_HARD = (
    ((1, 2), "鍵"),  # only A and B hold the key
    ((-1, -3), "店番A・C"),  # A and C keep the same shop
    ((-2, 4), "車"),  # B comes in D's car
    ((-4, -5), "店番D・E"),  # D and E keep the same shop
)
SAT_SOFT = (((3,), 3), ((5,), 2), ((1,), 2))  # wishes: C 3, E 2, A 2


def sat_holds(clause: Sequence[int], x: Sequence[bool]) -> bool:
    return any((lit > 0) == x[abs(lit) - 1] for lit in clause)


def sat_weight(x: Sequence[bool]) -> int:
    return sum(w for clause, w in SAT_SOFT if sat_holds(clause, x))


def sat_label(x: Sequence[bool]) -> str:
    return "".join(n for n, b in zip(SAT_NAMES, x, strict=True) if b) or "なし"


def sat_feasible() -> list[tuple[bool, ...]]:
    return [
        x
        for x in itertools.product((False, True), repeat=5)
        if all(sat_holds(clause, x) for clause, _ in SAT_HARD)
    ]


def sat_implications(first: int) -> list[tuple[int, str]]:
    """Unit propagation from one decided literal over the hard clauses: (literal, reason)."""
    value = {abs(first): first > 0}
    chain = [(first, "")]
    changed = True
    while changed:
        changed = False
        for clause, reason in SAT_HARD:
            if any(value.get(abs(lit)) == (lit > 0) for lit in clause):
                continue
            free = [lit for lit in clause if abs(lit) not in value]
            if len(free) == 1:
                value[abs(free[0])] = free[0] > 0
                chain.append((free[0], reason))
                changed = True
    return chain


def sat_greedy() -> tuple[bool, ...]:
    """Grant the wishes heaviest first, keeping each one only if some feasible plan remains."""
    plans = sat_feasible()
    for clause, _ in sorted(SAT_SOFT, key=lambda item: -item[1]):
        kept = [x for x in plans if sat_holds(clause, x)]
        plans = kept or plans
    return max(plans, key=sat_weight)


def _sat_literal(lit: int) -> str:
    return ("" if lit > 0 else "¬") + SAT_NAMES[abs(lit) - 1]


def _sat_grid_svg() -> str:
    feasible = set(sat_feasible())
    best = max(feasible, key=sat_weight)
    greedy = sat_greedy()
    parts = _open(
        "32通りの呼び方と、希望の重み",
        (
            "5人A〜Eを呼ぶかどうかの32通り。行はAとBの呼び方、列はC・D・Eの呼び方。"
            f"決まり（鍵・店番・車・店番）を守るのは{len(feasible)}通りで、"
            "守る組には、かなった希望の重み（Cが3、Eが2、Aが2）の合計を書く。"
            f"最も重いのは{sat_label(best)}の{sat_weight(best)}、"
            f"重い希望から順に決めると{sat_label(greedy)}の{sat_weight(greedy)}。"
        ),
        380,
    )
    left, top, cell_w, cell_h = 92, 96, 41, 50
    columns = list(itertools.product((False, True), repeat=3))
    rows = list(itertools.product((False, True), repeat=2))
    parts.append(_text(20, 64, "列：C・D・Eのうち呼ぶ人　行：A・Bのうち呼ぶ人", "tick"))
    for j, cde in enumerate(columns):
        name = "".join(n for n, b in zip("CDE", cde, strict=True) if b) or "−"
        parts.append(_text(left + cell_w * (j + 0.5), top - 8, name, "tick", "middle"))
    for i, ab in enumerate(rows):
        name = "".join(n for n, b in zip("AB", ab, strict=True) if b) or "−"
        parts.append(_text(left - 10, top + cell_h * (i + 0.5) + 5, name, "tick", "end"))
        for j, cde in enumerate(columns):
            x = (*ab, *cde)
            cx, cy = left + cell_w * j, top + cell_h * i
            if x in feasible:
                fill = "#ffffff"
                parts.append(
                    f'<rect x="{cx + 2}" y="{cy + 2}" width="{cell_w - 4}" height="{cell_h - 4}" '
                    f'rx="6" fill="{fill}" stroke="{LINE}" stroke-width="1.5"/>'
                )
                parts.append(
                    _text(cx + cell_w / 2, cy + cell_h / 2 + 6, str(sat_weight(x)), "", "middle")
                )
            else:
                parts.append(
                    f'<rect x="{cx + 2}" y="{cy + 2}" width="{cell_w - 4}" height="{cell_h - 4}" '
                    f'rx="6" fill="#e4e7e1"/>'
                )
                parts.append(_text(cx + cell_w / 2, cy + cell_h / 2 + 5, "×", "tick", "middle"))
            for plan, color in ((best, UPDATE), (greedy, POINT)):
                if x == plan:
                    parts.append(
                        f'<rect x="{cx}" y="{cy}" width="{cell_w}" height="{cell_h}" rx="8" '
                        f'fill="none" stroke="{color}" stroke-width="3.5"/>'
                    )
    bottom = top + cell_h * 4
    parts.append(
        f'<rect x="20" y="{bottom + 20}" width="18" height="18" rx="4" fill="none" '
        f'stroke="{UPDATE}" stroke-width="3"/>'
    )
    parts.append(_text(46, bottom + 35, f"最も重い：{sat_label(best)}（{sat_weight(best)}）"))
    parts.append(
        f'<rect x="230" y="{bottom + 20}" width="18" height="18" rx="4" fill="none" '
        f'stroke="{POINT}" stroke-width="3"/>'
    )
    parts.append(_text(256, bottom + 35, f"重い順：{sat_label(greedy)}（{sat_weight(greedy)}）"))
    parts.append(_text(20, bottom + 64, "×：決まりを一つ以上破る組", "tick"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


def _sat_chain_svg() -> str:
    parts = _open(
        "1人を決めると、残りが芋づる式に決まる",
        (
            "決まりの節だけで単位伝播した結果。"
            "① Cを呼ぶと、店番A・Cで¬A、鍵でB、車でD、店番D・Eで¬E。"
            "② Eを呼ぶと、店番D・Eで¬D、車で¬B、鍵でA、店番A・Cで¬C。"
            "CとEは両方は呼べない。"
        ),
        330,
    )
    for row, (first, title) in enumerate(((3, "① Cを呼ぶと"), (5, "② Eを呼ぶと"))):
        base = 64 + 130 * row
        parts.append(_text(20, base, title))
        chain = sat_implications(first)
        step = (420 - 20) / len(chain)
        for index, (lit, reason) in enumerate(chain):
            cx = 20 + step * (index + 0.5)
            color = INK if index == 0 else (POINT if lit > 0 else MUTED)
            width = 3.5 if index == 0 else 2.5
            parts.append(
                f'<rect x="{cx - 30:.1f}" y="{base + 22}" width="60" height="44" rx="10" '
                f'fill="#ffffff" stroke="{color}" stroke-width="{width}"/>'
            )
            parts.append(_text(cx, base + 51, _sat_literal(lit), "", "middle"))
            if index:
                arrow = cx - step + 30
                tip = cx - 32
                parts.append(
                    f'<path d="M{arrow:.1f} {base + 44}H{tip - 6:.1f}" stroke="{MUTED}" '
                    'stroke-width="2"/>'
                )
                parts.append(
                    f'<path d="M{tip - 8:.1f} {base + 39}L{tip:.1f} {base + 44}'
                    f'L{tip - 8:.1f} {base + 49}Z" fill="{MUTED}"/>'
                )
                parts.append(_text(cx - step / 2, base + 92, reason, "tick", "middle"))
    parts.append(_text(20, 316, "¬A は「Aを呼ばない」。箱の間の文字は使った決まり", "tick"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


FIGURES: dict[str, Callable[[], str]] = {
    "sat-invite-grid.svg": _sat_grid_svg,
    "sat-invite-chain.svg": _sat_chain_svg,
}
