"""Robust optimization (content/concepts/robust-optimization.md): ten kilograms of nitrogen from
bags of chemical fertilizer (A) and compost (B), whose nitrogen per bag is only known to lie in a
range. At most eight bags fit on the truck.
"""

from __future__ import annotations

import itertools
from collections.abc import Callable, Sequence

from ._svg import GRID, INK, LINE, MUTED, POINT, UPDATE, _open, _polyline, _scale, _text

RO_COST = (3.0, 1.2)  # thousand yen per bag
RO_MEAN = (2.0, 1.0)  # kg of nitrogen per bag, the middle of the recorded range
RO_HALF = (0.2, 0.5)  # half-width of the recorded range
RO_NEED, RO_CAP = 10.0, 8.0


def ro_coefficients(k: float) -> tuple[float, float]:
    """The low corner of the range shrunk to k times its recorded half-width."""
    return (RO_MEAN[0] - k * RO_HALF[0], RO_MEAN[1] - k * RO_HALF[1])


def ro_solve(k: float) -> tuple[tuple[float, float], float]:
    """min c'x s.t. a(k)'x >= need, x1 + x2 <= cap, x >= 0, by enumerating the vertices."""
    a = ro_coefficients(k)
    lines = (  # (p, q, r) for p x1 + q x2 = r
        (a[0], a[1], RO_NEED),
        (1.0, 1.0, RO_CAP),
        (1.0, 0.0, 0.0),
        (0.0, 1.0, 0.0),
    )
    best: tuple[tuple[float, float], float] | None = None
    for (p1, q1, r1), (p2, q2, r2) in itertools.combinations(lines, 2):
        det = p1 * q2 - p2 * q1
        if abs(det) < 1e-12:
            continue
        x = ((r1 * q2 - r2 * q1) / det, (p1 * r2 - p2 * r1) / det)
        feasible = (
            min(x) >= -1e-9
            and x[0] + x[1] <= RO_CAP + 1e-9
            and a[0] * x[0] + a[1] * x[1] >= RO_NEED - 1e-9
        )
        cost = RO_COST[0] * x[0] + RO_COST[1] * x[1]
        if feasible and (best is None or cost < best[1] - 1e-12):
            best = (x, cost)
    assert best is not None
    return best


def ro_content(x: Sequence[float], a: Sequence[float]) -> float:
    return a[0] * x[0] + a[1] * x[1]


def ro_shortfall_probability(x: Sequence[float]) -> float:
    """P(a'x < need) when a is uniform on the recorded box: area of the clipped box / box area."""
    low = ro_coefficients(1.0)
    high = (RO_MEAN[0] + RO_HALF[0], RO_MEAN[1] + RO_HALF[1])
    box = [(low[0], low[1]), (high[0], low[1]), (high[0], high[1]), (low[0], high[1])]

    def gap(point: tuple[float, float]) -> float:
        return RO_NEED - ro_content(x, point)

    kept: list[tuple[float, float]] = []
    for p, q in zip(box, box[1:] + box[:1], strict=True):
        if gap(p) > 0:
            kept.append(p)
        if (gap(p) > 0) != (gap(q) > 0):
            s = gap(p) / (gap(p) - gap(q))
            kept.append((p[0] + s * (q[0] - p[0]), p[1] + s * (q[1] - p[1])))
    if len(kept) < 3:
        return 0.0
    area = 0.5 * abs(
        sum(p[0] * q[1] - q[0] * p[1] for p, q in zip(kept, kept[1:] + kept[:1], strict=True))
    )
    return area / (4 * RO_HALF[0] * RO_HALF[1])


def ro_switch() -> float:
    """The range factor k at which the cheapest plan stops using compost (bisection)."""
    low, high = 0.0, 1.0
    for _ in range(200):
        mid = (low + high) / 2
        low, high = (mid, high) if ro_solve(mid)[0][1] > 1e-9 else (low, mid)
    return (low + high) / 2


def _ro_number(value: float, digits: int = 2) -> str:
    return f"{round(value, digits):g}"


def _ro_box_svg() -> str:
    nominal, nominal_cost = ro_solve(0.0)
    robust, robust_cost = ro_solve(1.0)
    worst = ro_coefficients(1.0)
    parts = _open(
        "含有量の範囲と、袋数の選び方",
        (
            "① 1袋あたりの窒素の範囲：化成肥料1.8〜2.2kg、堆肥0.5〜1.5kg。中央は (2, 1)、"
            "どちらも少ない角は (1.8, 0.5)。"
            "② 袋数の平面：化成肥料 x₁ と堆肥 x₂。中央の含有量で窒素10kgの線、"
            "少ない角の含有量で窒素10kgの線、8袋の線。"
            f"中央の含有量で最も安い (2, 6) は{_ro_number(nominal_cost)}千円だが、"
            f"少ない角では窒素{_ro_number(ro_content(nominal, worst))}kg。"
            f"範囲のどこでも10kgを守る最も安い組み合わせは"
            f"({_ro_number(robust[0])}, 0)で{_ro_number(robust_cost)}千円。"
        ),
        660,
    )
    parts.append(_text(20, 64, "① 1袋あたりの窒素（kg）の範囲"))
    ax = _scale(1.7, 2.3, 96, 400)
    ay = _scale(0.3, 1.7, 236, 84)
    parts.append(f'<path d="M96 84V236H400" fill="none" stroke="{GRID}"/>')
    for value in (1.8, 2.0, 2.2):
        parts.append(_text(ax(value), 256, f"{value:g}", "tick", "middle"))
    for value in (0.5, 1.0, 1.5):
        parts.append(_text(88, ay(value) + 5, f"{value:g}", "tick", "end"))
    parts.append(_text(400, 280, "化成肥料 a₁", "tick", "end"))
    parts.append(_text(104, 100, "堆肥 a₂", "tick"))
    lo, hi = ro_coefficients(1.0), ro_coefficients(-1.0)
    parts.append(
        f'<rect x="{ax(lo[0]):.1f}" y="{ay(hi[1]):.1f}" width="{ax(hi[0]) - ax(lo[0]):.1f}" '
        f'height="{ay(lo[1]) - ay(hi[1]):.1f}" fill="#e3ece6" stroke="{LINE}" stroke-width="2"/>'
    )
    parts.append(
        f'<circle cx="{ax(RO_MEAN[0]):.1f}" cy="{ay(RO_MEAN[1]):.1f}" r="7" fill="{POINT}"/>'
    )
    parts.append(_text(ax(RO_MEAN[0]) + 12, ay(RO_MEAN[1]) + 5, "中央 (2, 1)"))
    parts.append(f'<circle cx="{ax(worst[0]):.1f}" cy="{ay(worst[1]):.1f}" r="7" fill="{UPDATE}"/>')
    parts.append(
        _text(ax(worst[0]) + 12, ay(worst[1]) - 8, "少ない角 (1.8, 0.5)").replace(
            "<text ", f'<text style="fill:{UPDATE}" '
        )
    )

    parts.append(_text(20, 318, "② 袋数の平面"))
    parts.append(_text(410, 318, "縦：堆肥 x₂（袋）", "tick", "end"))
    px = _scale(0.0, 8.0, 76, 410)
    py = _scale(0.0, 8.0, 584, 348)
    parts.append(f'<path d="M76 348V584H410" fill="none" stroke="{GRID}"/>')
    for value in (0, 2, 4, 6, 8):
        parts.append(_text(px(value), 604, str(value), "tick", "middle"))
        parts.append(_text(68, py(value) + 5, str(value), "tick", "end"))
    parts.append(_text(410, 628, "化成肥料 x₁（袋）", "tick", "end"))
    corner = (
        (RO_NEED - worst[1] * RO_CAP) / (worst[0] - worst[1]),
        RO_CAP - (RO_NEED - worst[1] * RO_CAP) / (worst[0] - worst[1]),
    )
    region = [(RO_NEED / worst[0], 0.0), (RO_CAP, 0.0), corner]
    joined = " ".join(f"{px(x):.1f},{py(y):.1f}" for x, y in region)
    parts.append(f'<polygon points="{joined}" fill="#f3d2b5" stroke="none"/>')
    parts.append(_polyline([(px(0), py(RO_CAP)), (px(RO_CAP), py(0))], MUTED, 2))
    top = (RO_NEED - RO_MEAN[1] * RO_CAP) / RO_MEAN[0]  # where the mean line meets x2 = 8
    mean_line = [(px(RO_NEED / RO_MEAN[0]), py(0)), (px(top), py(RO_CAP))]
    parts.append(_polyline(mean_line, POINT, 2.5))
    worst_top = (RO_NEED - worst[1] * RO_CAP) / worst[0]  # where it meets x2 = 8
    worst_line = [(px(RO_NEED / worst[0]), py(0)), (px(worst_top), py(RO_CAP))]
    parts.append(_polyline(worst_line, UPDATE, 2.5))
    parts.append(
        f'<circle cx="{px(nominal[0]):.1f}" cy="{py(nominal[1]):.1f}" r="7" fill="{POINT}" '
        f'stroke="{INK}" stroke-width="1.5"/>'
    )
    parts.append(
        _text(px(nominal[0]) + 12, py(nominal[1]) - 8, f"(2, 6)：{_ro_number(nominal_cost)}千円")
    )
    parts.append(
        f'<circle cx="{px(robust[0]):.1f}" cy="{py(robust[1]):.1f}" r="7" fill="{UPDATE}" '
        f'stroke="{INK}" stroke-width="1.5"/>'
    )
    parts.append(_text(410, py(7.4), f"橙の点 ({_ro_number(robust[0])}, 0)", anchor="end"))
    parts.append(_text(410, py(7.4) + 22, f"{_ro_number(robust_cost)}千円", anchor="end"))
    parts.append(_polyline([(20, 646 - 5), (42, 646 - 5)], POINT, 2.5))
    parts.append(_text(48, 646, "中央で10kg", "tick"))
    parts.append(_polyline([(152, 646 - 5), (174, 646 - 5)], UPDATE, 2.5))
    parts.append(_text(180, 646, "少ない角で10kg", "tick"))
    parts.append(_polyline([(312, 646 - 5), (334, 646 - 5)], MUTED, 2))
    parts.append(_text(340, 646, "8袋", "tick"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


def _ro_set_size_svg() -> str:
    switch = ro_switch()
    ks = [i / 200 for i in range(201)]
    parts = _open(
        "備える範囲の広さと、費用・不足の確率",
        (
            "備える範囲を、記録された範囲の k 倍（k=0 は中央の値だけ、k=1 は記録された範囲全体）"
            "にしたときの最も安い組み合わせ。"
            f"① 費用は k=0 の{_ro_number(ro_solve(0.0)[1])}千円から k=1 の"
            f"{_ro_number(ro_solve(1.0)[1])}千円まで増える。"
            f"k={_ro_number(switch, 3)} で堆肥を使わない組み合わせに切り替わる。"
            "② 含有量が記録された範囲の中で一様にばらつくと仮定したときの、"
            "窒素が10kgに届かない確率。"
            f"k=0 で{_ro_number(100 * ro_shortfall_probability(ro_solve(0.0)[0]), 1)}%、"
            f"k=1 で0%。切り替わりの直後に確率が上がる。"
        ),
        610,
    )
    px = _scale(0.0, 1.0, 76, 410)
    for tick in (0.0, 0.25, 0.5, 0.75, 1.0):
        parts.append(_text(px(tick), 300, f"{tick:g}", "tick", "middle"))
        parts.append(_text(px(tick), 564, f"{tick:g}", "tick", "middle"))
    parts.append(_text(20, 64, "① 最も安い組み合わせの費用（千円）"))
    cy = _scale(12.0, 17.0, 280, 84)
    parts.append(f'<path d="M76 84V280H410" fill="none" stroke="{GRID}"/>')
    for value in (12, 14, 16):
        parts.append(_text(68, cy(value) + 5, str(value), "tick", "end"))
    parts.append(_polyline([(px(k), cy(ro_solve(k)[1])) for k in ks], LINE, 3))
    parts.append(_text(20, 344, "② 窒素が10kgに届かない確率（%）"))
    qy = _scale(0.0, 60.0, 544, 364)
    parts.append(f'<path d="M76 364V544H410" fill="none" stroke="{GRID}"/>')
    for value in (0, 25, 50):
        parts.append(_text(68, qy(value) + 5, str(value), "tick", "end"))
    before = [k for k in ks if k < switch]
    after = [k for k in ks if k > switch]
    for segment in (before, after):
        points = [(px(k), qy(100 * ro_shortfall_probability(ro_solve(k)[0]))) for k in segment]
        parts.append(_polyline(points, UPDATE, 3))
    for top, bottom in ((84, 280), (364, 544)):
        parts.append(
            f'<path d="M{px(switch):.1f} {top}V{bottom}" stroke="{MUTED}" stroke-width="1.5" '
            'stroke-dasharray="5 4"/>'
        )
    parts.append(_text(px(switch) + 8, 392, f"k={_ro_number(switch, 3)}", "tick"))
    parts.append(_text(px(switch) + 8, 412, "ここから堆肥0袋", "tick"))
    for k, shift, lift, anchor in (
        (0.0, 10, -10, "start"),
        (0.45, -10, 22, "end"),
        (0.5, 10, -10, "start"),
    ):
        x, cost = ro_solve(k)
        probability = 100 * ro_shortfall_probability(x)
        parts.append(f'<circle cx="{px(k):.1f}" cy="{qy(probability):.1f}" r="5" fill="{INK}"/>')
        label = f"{_ro_number(probability, 1)}%"
        parts.append(_text(px(k) + shift, qy(probability) + lift, label, "tick", anchor))
        parts.append(f'<circle cx="{px(k):.1f}" cy="{cy(cost):.1f}" r="5" fill="{INK}"/>')
        if k == 0.0:
            parts.append(_text(px(k) + shift, cy(cost) + 22, _ro_number(cost), "tick"))
    switch_cost = ro_solve(switch)[1]
    parts.append(
        _text(px(switch) - 10, cy(switch_cost) - 12, f"{_ro_number(switch_cost)}", "tick", "end")
    )
    full = ro_solve(1.0)[1]
    parts.append(f'<circle cx="{px(1.0):.1f}" cy="{cy(full):.1f}" r="5" fill="{INK}"/>')
    parts.append(_text(px(1.0), cy(full) + 24, _ro_number(full), "tick", "end"))
    parts.append(_text(410, 588, "備える範囲の広さ k", "tick", "end"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


FIGURES: dict[str, Callable[[], str]] = {
    "robust-optimization-box.svg": _ro_box_svg,
    "robust-optimization-set-size.svg": _ro_set_size_svg,
}
