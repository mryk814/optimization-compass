"""Mixed-integer linear program (content/concepts/mixed-integer-linear-program.md): max 5x1 + 4x2
s.t. 6x1 + 4x2 <= 24, x1 + 2x2 <= 6, x >= 0. Five LP relaxations chosen by hand.
"""

from __future__ import annotations

import itertools
from collections.abc import Callable, Sequence
from fractions import Fraction

from ._svg import POINT, UPDATE, _open, _text

MILP_PROFIT = (5, 4)
MILP_ROWS = ((6, 4, 24), (1, 2, 6), (-1, 0, 0), (0, -1, 0))
# (name, label, extra rows a1*x1 + a2*x2 <= b added to the relaxation)
MILP_NODES = (
    ("root", "整数条件を外す", ()),
    ("left", "x₂ ≤ 1", ((0, 1, 1),)),
    ("left_left", "x₁ ≤ 3", ((0, 1, 1), (1, 0, 3))),
    ("left_right", "x₁ ≥ 4", ((0, 1, 1), (-1, 0, -4))),
    ("right", "x₂ ≥ 2", ((0, -1, -2),)),
)


def milp_relaxation(
    extra: Sequence[tuple[int, int, int]] = (),
) -> tuple[tuple[Fraction, Fraction], Fraction]:
    """Exact optimum of the LP relaxation with the added bound rows, by vertex enumeration."""
    rows = [*MILP_ROWS, *extra]
    best: tuple[Fraction, Fraction, Fraction] | None = None
    for (a1, a2, b), (c1, c2, d) in itertools.combinations(rows, 2):
        det = a1 * c2 - a2 * c1
        if det == 0:
            continue
        x1, x2 = Fraction(b * c2 - a2 * d, det), Fraction(a1 * d - b * c1, det)
        if all(r1 * x1 + r2 * x2 <= rb for r1, r2, rb in rows):
            value = MILP_PROFIT[0] * x1 + MILP_PROFIT[1] * x2
            if best is None or value > best[2]:
                best = (x1, x2, value)
    assert best is not None
    return (best[0], best[1]), best[2]


def milp_integer_points() -> list[tuple[int, int]]:
    return [
        (i, j)
        for i in range(8)
        for j in range(8)
        if all(a * i + b * j <= c for a, b, c in MILP_ROWS)
    ]


def _milp_number(value: Fraction) -> str:
    if value.denominator == 1:
        return str(value.numerator)
    if value.denominator in (2, 4, 5, 8, 10):
        return f"{float(value):g}"
    return f"{value.numerator}/{value.denominator}"


def _milp_tree_svg() -> str:
    solved = {name: milp_relaxation(extra) for name, _, extra in MILP_NODES}
    labels = {name: label for name, label, _ in MILP_NODES}
    # (centre x, top y, width) of each box; one SVG unit is one CSS pixel on a PC.
    boxes = {
        "root": (220, 50, 170),
        "left": (134, 168, 140),
        "right": (350, 168, 140),
        "left_left": (68, 286, 124),
        "left_right": (200, 286, 124),
    }
    height_box = 80
    parts = _open(
        "手で指定した5個のLP緩和",
        (
            "最大化の例の分枝木です。根のLP緩和は(3, 1.5)で上界21。"
            "x2を1以下と2以上に分け、x2が1以下の枝をさらにx1が3以下と4以上に分けます。"
            "葉の値は19、20、18で、整数解(4, 0)の利益20が最良です。"
        ),
        430,
    )
    for parent, child in (
        ("root", "left"),
        ("root", "right"),
        ("left", "left_left"),
        ("left", "left_right"),
    ):
        px_, py_, _ = boxes[parent]
        cx, cy, _ = boxes[child]
        parts.append(
            f'<path d="M{px_} {py_ + height_box}L{cx} {cy}" stroke="{POINT}" stroke-width="2"/>'
        )
    for name, (cx, top, width) in boxes.items():
        point, value = solved[name]
        best = name == "left_right"
        parts.append(
            f'<rect x="{cx - width / 2}" y="{top}" width="{width}" height="{height_box}" rx="8" '
            f'fill="{"#fbeee6" if best else "#ffffff"}" '
            f'stroke="{UPDATE if best else POINT}" stroke-width="{3 if best else 1.5}"/>'
        )
        coordinates = f"({_milp_number(point[0])}, {_milp_number(point[1])})"
        kind = "値" if name in ("left_left", "left_right") else "上界"
        parts.append(_text(cx, top + 23, labels[name], "", "middle"))
        parts.append(_text(cx, top + 47, coordinates, "", "middle"))
        parts.append(_text(cx, top + 70, f"{kind} {_milp_number(value)}", "note", "middle"))
    parts.append(_text(20, 392, "橙の枠：整数解 (4, 0)、利益20"))
    parts.append(_text(20, 416, "葉の19、20、18は、どれも20以下", "note"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


FIGURES: dict[str, Callable[[], str]] = {
    "milp-relaxation-tree.svg": _milp_tree_svg,
}
