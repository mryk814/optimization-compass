"""Assignment (content/concepts/assignment-matching.md): three ambulances, three calls, minutes."""

from __future__ import annotations

import itertools
from collections.abc import Callable, Sequence

from ._svg import GRID, UPDATE, _open, _text

ASSIGN_TIMES = ((3, 2, 5), (10, 3, 8), (14, 5, 9))
ASSIGN_ROWS = ("救急車1", "救急車2", "救急車3")
ASSIGN_COLS = ("A", "B", "C")
# A row value u and a column value v with u_i + v_j <= time everywhere (the dual certificate).
ASSIGN_U = (1, 3, 5)
ASSIGN_V = (2, 0, 4)


def assignment_total(columns: Sequence[int]) -> int:
    return sum(ASSIGN_TIMES[i][j] for i, j in enumerate(columns))


def assignment_all() -> list[tuple[int, int, tuple[int, ...]]]:
    """Every one-to-one assignment as (total, longest single trip, columns), cheapest first."""
    rows = []
    for columns in itertools.permutations(range(len(ASSIGN_TIMES))):
        longest = max(ASSIGN_TIMES[i][j] for i, j in enumerate(columns))
        rows.append((assignment_total(columns), longest, columns))
    return sorted(rows)


def assignment_greedy() -> list[tuple[int, int]]:
    """Take the shortest remaining (ambulance, call) pair until every ambulance is sent."""
    free_rows, free_cols = set(range(3)), set(range(3))
    picks = []
    while free_rows:
        i, j = min(
            ((i, j) for i in free_rows for j in free_cols),
            key=lambda cell: (ASSIGN_TIMES[cell[0]][cell[1]], cell),
        )
        picks.append((i, j))
        free_rows.remove(i)
        free_cols.remove(j)
    return picks


def assignment_reduced() -> list[list[int]]:
    """time - u_i - v_j: never negative, and 0 on the cells of the cheapest assignment."""
    return [[ASSIGN_TIMES[i][j] - ASSIGN_U[i] - ASSIGN_V[j] for j in range(3)] for i in range(3)]


def _assignment_grid(
    top: float,
    values: Sequence[Sequence[int]],
    chosen: dict[tuple[int, int], str],
    column_labels: Sequence[str],
    row_labels: Sequence[str],
) -> list[str]:
    """A 3x3 table: column headers at `top`, rows below. Chosen cells are filled orange."""
    left, cell_w, cell_h = 168, 84, 46
    parts = []
    for j, label in enumerate(column_labels):
        parts.append(_text(left + cell_w * (j + 0.5), top + 18, label, "", "middle"))
    for i, label in enumerate(row_labels):
        y = top + 28 + cell_h * i
        parts.append(_text(left - 12, y + 29, label, "", "end"))
        for j in range(3):
            x = left + cell_w * j
            mark = chosen.get((i, j))
            fill = "#f3d2b5" if mark is not None else "#ffffff"
            stroke = UPDATE if mark is not None else GRID
            width = 2.5 if mark is not None else 1
            parts.append(
                f'<rect x="{x + 3}" y="{y + 3:.1f}" width="{cell_w - 6}" height="{cell_h - 6}" '
                f'rx="6" fill="{fill}" stroke="{stroke}" stroke-width="{width}"/>'
            )
            parts.append(_text(x + cell_w / 2, y + 29, str(values[i][j]), "", "middle"))
            if mark:
                parts.append(_text(x + 9, y + 21, mark, "tick"))
    return parts


def _assignment_greedy_svg() -> str:
    greedy = assignment_greedy()
    greedy_times = [ASSIGN_TIMES[i][j] for i, j in greedy]
    best_total, best_longest, best = assignment_all()[0]
    best_times = [ASSIGN_TIMES[i][j] for i, j in enumerate(best)]
    parts = _open(
        "近い組から決めると、合計が延びる",
        (
            "救急車3台と通報A・B・Cの到着時間（分）の表を2枚並べたもの。"
            f"① 近い組から決めると {'、'.join(map(str, greedy_times))} 分を選び、"
            f"合計は {sum(greedy_times)} 分。"
            f"② 合計が最小の割当は {'、'.join(map(str, best_times))} 分を選び、"
            f"合計は {best_total} 分。どちらも各行・各列から一つずつ選んでいる。"
        ),
        520,
    )
    columns = [f"通報{name}" for name in ASSIGN_COLS]
    parts.append(_text(20, 66, "① 近い組から決める"))
    parts.append(_text(420, 66, f"合計 {sum(greedy_times)} 分", "note", "end"))
    order = {cell: str(k + 1) for k, cell in enumerate(greedy)}
    parts += _assignment_grid(76, ASSIGN_TIMES, order, columns, ASSIGN_ROWS)
    parts.append(_text(20, 296, "② 合計が最小の割当"))
    parts.append(_text(420, 296, f"合計 {best_total} 分", "note", "end"))
    parts += _assignment_grid(
        306, ASSIGN_TIMES, {(i, j): "" for i, j in enumerate(best)}, columns, ASSIGN_ROWS
    )
    parts.append(_text(20, 496, f"① {' + '.join(map(str, greedy_times))} = {sum(greedy_times)}"))
    parts.append(
        _text(
            420,
            496,
            f"② {' + '.join(map(str, best_times))} = {best_total}",
            "note",
            "end",
        )
    )
    parts.append("</svg>")
    return "".join(parts) + "\n"


def _assignment_dual_svg() -> str:
    reduced = assignment_reduced()
    best_total, _, best = assignment_all()[0]
    bound = sum(ASSIGN_U) + sum(ASSIGN_V)
    parts = _open(
        "どの割当も15分を下回らない理由",
        (
            f"救急車ごとの値 u=({', '.join(map(str, ASSIGN_U))}) と、"
            f"通報ごとの値 v=({', '.join(map(str, ASSIGN_V))}) を到着時間から引いた表。"
            "すべてのマスが0以上で、合計が最小の割当の3マスは0。"
            f"そのため、どの割当の合計も u と v の合計 {bound} 分以上になる。"
        ),
        360,
    )
    columns = [f"{name} v={value}" for name, value in zip(ASSIGN_COLS, ASSIGN_V, strict=True)]
    rows = [f"{name} u={value}" for name, value in zip(ASSIGN_ROWS, ASSIGN_U, strict=True)]
    parts.append(_text(20, 64, "時間 − u − v"))
    parts += _assignment_grid(74, reduced, {(i, j): "" for i, j in enumerate(best)}, columns, rows)
    parts.append(_text(20, 266, f"u の合計 {sum(ASSIGN_U)} ＋ v の合計 {sum(ASSIGN_V)} = {bound}"))
    parts.append(_text(20, 292, "どの割当も各行・各列を一度ずつ使うので、"))
    parts.append(_text(20, 316, f"合計 ＝ {bound} ＋ 選んだマスの値 ≧ {bound}"))
    parts.append(_text(20, 344, f"橙の3マスは0なので、合計 {best_total} 分が最小", "note"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


FIGURES: dict[str, Callable[[], str]] = {
    "assignment-greedy-optimal.svg": _assignment_greedy_svg,
    "assignment-dual-bound.svg": _assignment_dual_svg,
}
