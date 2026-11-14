"""Repeated parametric QP (content/concepts/repeated-parametric-optimization.md): two machines share
an order of theta (hundreds of pieces) every two hours. Cost 1/2 x1^2 + x2^2; machine 1 caps at 4,
machine 2 runs between 1 and 3. Constraints are a^T x >= b0 + bt * theta.
"""

from __future__ import annotations

from collections.abc import Callable

from ._numeric import _solve_linear
from ._svg import GRID, INK, LINE, MUTED, POINT, UPDATE, _open, _polyline, _scale, _text

PQ_COST = (1.0, 2.0)
PQ_CONSTRAINTS = (
    ("注文を満たす", (1.0, 1.0), 0.0, 1.0),
    ("1号機の上限", (-1.0, 0.0), -4.0, 0.0),
    ("2号機の下限", (0.0, 1.0), 1.0, 0.0),
    ("2号機の上限", (0.0, -1.0), -3.0, 0.0),
    ("1号機の下限", (1.0, 0.0), 0.0, 0.0),
)
PQ_ORDERS = (2.0, 2.5, 3.5, 4.5, 5.5, 6.5, 6.8, 6.2, 5.0, 3.5, 2.0, 6.5)


def _pq_equality_qp(working: frozenset[int], theta: float) -> tuple[list[float], dict[int, float]]:
    """Solve min cost s.t. the working constraints hold with equality (one KKT system)."""
    rows = sorted(working)
    size = 2 + len(rows)
    kkt = [[0.0] * size for _ in range(size)]
    rhs = [0.0] * size
    for i in range(2):
        kkt[i][i] = PQ_COST[i]
    for k, index in enumerate(rows):
        _, a, b0, bt = PQ_CONSTRAINTS[index]
        for i in range(2):
            kkt[i][2 + k] = -a[i]
            kkt[2 + k][i] = a[i]
        rhs[2 + k] = b0 + bt * theta
    solution = _solve_linear(kkt, rhs)
    return solution[:2], {index: solution[2 + k] for k, index in enumerate(rows)}


def pq_solve(
    theta: float, start: frozenset[int] = frozenset()
) -> tuple[list[float], dict[int, float], frozenset[int], int]:
    """Active-set loop: drop the most negative multiplier, else add the most violated constraint.

    Returns the plan, the multipliers, the final working set and the number of KKT solves.
    """
    working, solves = set(start), 0
    while True:
        x, lam = _pq_equality_qp(frozenset(working), theta)
        solves += 1
        negative = {i: v for i, v in lam.items() if v < -1e-9}
        if negative:
            working.remove(min(negative, key=negative.__getitem__))
            continue
        gaps = {
            i: b0 + bt * theta - (a[0] * x[0] + a[1] * x[1])
            for i, (_, a, b0, bt) in enumerate(PQ_CONSTRAINTS)
            if i not in working
        }
        worst = max(gaps, key=gaps.__getitem__)
        if gaps[worst] > 1e-9:
            working.add(worst)
            continue
        return x, lam, frozenset(working), solves


def pq_sequence() -> tuple[list[int], list[int]]:
    """KKT solves per period: from an empty working set, and from the previous period's set."""
    cold, warm, working = [], [], frozenset[int]()
    for theta in PQ_ORDERS:
        cold.append(pq_solve(theta)[3])
        *_, working, solves = pq_solve(theta, working)
        warm.append(solves)
    return cold, warm


def _pq_regions_svg() -> str:
    parts = _open(
        "注文量と、2台の生産量",
        (
            "① 注文量 θ（百個）ごとの、費用が最小の生産量。θ<3 では2号機の下限1が効き、"
            "1号機が θ−1 を作る。3≦θ≦6 では1号機が 2θ/3、2号機が θ/3 を作る。"
            "θ>6 では1号機の上限4が効き、2号機が θ−4 を作る。"
            "② 2時間ごとの12回の注文量："
            + "・".join(f"{t:g}" for t in PQ_ORDERS)
            + "。点の色は、その回にどの制約が効くか"
            "（白は2号機の下限、緑は注文だけ、紺は1号機の上限）。"
        ),
        610,
    )
    tx = _scale(1.0, 7.0, 64, 410)
    vy = _scale(0.0, 4.5, 272, 92)
    parts.append(_text(20, 64, "① 注文量 θ ごとの生産量"))
    for boundary in (3.0, 6.0):
        parts.append(
            f'<path d="M{tx(boundary):.1f} 84V272" stroke="{GRID}" stroke-dasharray="5 4"/>'
        )
    parts.append(f'<path d="M64 84V272H410" fill="none" stroke="{GRID}"/>')
    for value in (0, 1, 2, 3, 4):
        parts.append(_text(56, vy(value) + 5, f"{value}", "tick", "end"))
    for value in range(1, 8):
        parts.append(_text(tx(value), 292, f"{value}", "tick", "middle"))
    thetas = [1 + 6 * i / 240 for i in range(241)]
    plans = [pq_solve(t)[0] for t in thetas]
    for machine, color in ((0, POINT), (1, UPDATE)):
        parts.append(
            _polyline(
                [(tx(t), vy(p[machine])) for t, p in zip(thetas, plans, strict=True)], color, 3
            )
        )
    regions = ((2.0, "下限", "#ffffff"), (4.5, "注文だけ", LINE), (6.5, "上限", POINT))
    for theta, label, color in regions:
        width = 15 * len(label) + 16
        left = tx(theta) - width / 2
        parts.append(
            f'<circle cx="{left + 6:.1f}" cy="95" r="6" fill="{color}" '
            f'stroke="{INK}" stroke-width="1.5"/>'
        )
        parts.append(_text(left + 16, 100, label, "tick"))
    parts.append(_text(tx(4.0), vy(2.67) - 14, "1号機", "tick", "end"))
    parts.append(_text(tx(4.5), vy(1.5) + 26, "2号機", "tick", "middle"))
    parts.append(_text(410, 314, "注文量 θ（百個）", "tick", "end"))

    parts.append(_text(20, 358, "② 2時間ごとの注文量"))
    ox = _scale(0.5, 12.5, 64, 410)
    oy = _scale(1.0, 7.0, 548, 380)
    parts.append(f'<path d="M64 380V548H410" fill="none" stroke="{GRID}"/>')
    for boundary in (3.0, 6.0):
        parts.append(
            f'<path d="M64 {oy(boundary):.1f}H410" stroke="{GRID}" stroke-dasharray="5 4"/>'
        )
    for value in (1, 3, 5, 7):
        parts.append(_text(56, oy(value) + 5, f"{value}", "tick", "end"))
    for boundary in (3, 6):
        parts.append(_text(70, oy(boundary) - 5, f"θ={boundary}", "tick"))
    region_colors = {frozenset({0, 2}): "#ffffff", frozenset({0}): LINE, frozenset({0, 1}): POINT}
    for k, theta in enumerate(PQ_ORDERS, start=1):
        color = region_colors[pq_solve(theta)[2]]
        parts.append(
            f'<circle cx="{ox(k):.1f}" cy="{oy(theta):.1f}" r="6" fill="{color}" '
            f'stroke="{INK}" stroke-width="1.5"/>'
        )
        parts.append(_text(ox(k), 568, str(k), "tick", "middle"))
    legend = (("2号機の下限", "#ffffff"), ("注文だけ", LINE), ("1号機の上限", POINT))
    for index, (label, color) in enumerate(legend):
        x0 = 64 + 118 * index
        parts.append(
            f'<circle cx="{x0 + 6}" cy="591" r="6" fill="{color}" '
            f'stroke="{INK}" stroke-width="1.5"/>'
        )
        parts.append(_text(x0 + 18, 596, label, "tick"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


def _pq_warm_svg() -> str:
    cold, warm = pq_sequence()
    parts = _open(
        "毎回ゼロからと、前回の作業集合から",
        (
            "12回の注文ごとに、連立一次方程式を解いた回数。"
            f"毎回ゼロから始めると合計{sum(cold)}回、前回の作業集合から始めると合計{sum(warm)}回。"
            "同じ制約が効き続ける回は、前回から始めると1回で済む。"
            "12回目は注文が2から6.5へ跳び、どちらも3回かかる。"
        ),
        340,
    )
    ox = _scale(0.5, 12.5, 64, 410)
    parts.append(_text(20, 64, "連立一次方程式を解いた回数"))
    cy = _scale(0.0, 3.0, 262, 94)
    parts.append(f'<path d="M64 94V262H410" fill="none" stroke="{GRID}"/>')
    for value in (0, 1, 2, 3):
        parts.append(_text(56, cy(value) + 5, f"{value}", "tick", "end"))
    width = (410 - 64) / 12
    for k, (c, w) in enumerate(zip(cold, warm, strict=True), start=1):
        left = ox(k) - width / 2 + 4
        bar = (width - 8) / 2
        parts.append(
            f'<rect x="{left:.1f}" y="{cy(c):.1f}" width="{bar:.1f}" height="{262 - cy(c):.1f}" '
            f'fill="{MUTED}"/>'
        )
        parts.append(
            f'<rect x="{left + bar:.1f}" y="{cy(w):.1f}" width="{bar:.1f}" '
            f'height="{262 - cy(w):.1f}" fill="{UPDATE}"/>'
        )
        parts.append(_text(ox(k), 282, str(k), "tick", "middle"))
    parts.append(_text(410, 304, "何回目の注文か", "tick", "end"))
    parts.append(f'<rect x="64" y="316" width="14" height="14" fill="{MUTED}"/>')
    parts.append(_text(84, 328, f"毎回ゼロから：合計{sum(cold)}", "tick"))
    parts.append(f'<rect x="250" y="316" width="14" height="14" fill="{UPDATE}"/>')
    parts.append(_text(270, 328, f"前回から：合計{sum(warm)}", "tick"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


FIGURES: dict[str, Callable[[], str]] = {
    "parametric-production-regions.svg": _pq_regions_svg,
    "parametric-warm-start.svg": _pq_warm_svg,
}
