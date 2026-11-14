"""Design of experiments (content/concepts/design-of-experiments.md): six test bakes between 160 and
200 degC, coded x = (T - 180) / 20, for a quadratic score model (1, x, x^2).
"""

from __future__ import annotations

import functools
import math
from collections.abc import Callable, Sequence

from ._numeric import Matrix3, _det3, _solve_linear
from ._svg import GRID, LINE, MUTED, POINT, UPDATE, _open, _polyline, _scale, _text

DOE_DESIGNS = (
    ("等間隔", tuple(-1 + 0.4 * i for i in range(6)), POINT),
    ("中央付近", (-0.4, -0.4, 0.0, 0.0, 0.4, 0.4), UPDATE),
    ("端と中央に2回ずつ", (-1.0, -1.0, 0.0, 0.0, 1.0, 1.0), LINE),
)
DOE_ENDS = (-1.0, -1.0, -1.0, 1.0, 1.0, 1.0)
DOE_CANDIDATES = tuple(round(-1 + 0.1 * i, 1) for i in range(21))
DOE_SHOWN_STEPS = (0, 10, 1000)


def _doe_phi(x: float) -> list[float]:
    return [1.0, x, x * x]


def doe_information(xs: Sequence[float], weights: Sequence[float] | None = None) -> Matrix3:
    """M = sum w_i phi(x_i) phi(x_i)^T (weight 1 per bake for an exact design)."""
    w = weights if weights is not None else [1.0] * len(xs)
    return [
        [
            sum(wi * _doe_phi(x)[r] * _doe_phi(x)[c] for x, wi in zip(xs, w, strict=True))
            for c in range(3)
        ]
        for r in range(3)
    ]


def doe_variance(m: Matrix3, x: float) -> float:
    """Prediction variance phi(x)^T M^{-1} phi(x), in units of the measurement noise variance."""
    phi = _doe_phi(x)
    return sum(p * q for p, q in zip(phi, _solve_linear([row[:] for row in m], phi), strict=True))


@functools.cache
def doe_frank_wolfe(steps: int = 1000) -> tuple[tuple[tuple[float, ...], float], ...]:
    """Frank-Wolfe on candidate weights for max log det M(w); (weights, max d - 3) per step."""
    weights = [1.0 / len(DOE_CANDIDATES)] * len(DOE_CANDIDATES)
    history = []
    for _ in range(steps + 1):
        m = doe_information(DOE_CANDIDATES, weights)
        d = [doe_variance(m, x) for x in DOE_CANDIDATES]
        top = max(range(len(d)), key=d.__getitem__)
        history.append((tuple(weights), d[top] - 3))
        alpha = (d[top] / 3 - 1) / (d[top] - 1)  # the step that raises log det the most
        weights = [(1 - alpha) * w for w in weights]
        weights[top] += alpha
    return tuple(history)


def _doe_x(x: float) -> float:
    return _scale(-1.1, 1.1, 64, 410)(x)


def _doe_designs_svg() -> str:
    grid = [i / 100 for i in range(-100, 101)]
    worst = {
        name: max(doe_variance(doe_information(xs), x) for x in grid) for name, xs, _ in DOE_DESIGNS
    }
    dets = {name: _det3(doe_information(xs)) for name, xs, _ in DOE_DESIGNS}
    parts = _open(
        "6回の焼き温度と、予測のばらつき",
        (
            "① 6回の焼き温度の選び方。等間隔、中央付近（172・180・188℃に2回ずつ）、"
            "端と中央に2回ずつ（160・180・200℃）、両端だけ（160℃と200℃に3回ずつ）。"
            "両端だけでは2次式の係数が決まらない。"
            "② 点数を2次式で予測したときの、予測のばらつき（測定の誤差の分散を1とした値）。"
            + "、".join(
                f"{name}は最大 {worst[name]:.2f}（det M = {dets[name]:.3g}）"
                for name, _, _ in DOE_DESIGNS
            )
            + "。"
        ),
        640,
    )
    parts.append(_text(20, 64, "① 6回の焼き温度"))
    rows = (*DOE_DESIGNS, ("両端だけ", DOE_ENDS, MUTED))
    for index, (name, xs, color) in enumerate(rows):
        y = 112 + 46 * index
        parts.append(f'<path d="M64 {y:.1f}H410" stroke="{GRID}"/>')
        parts.append(_text(64, y - 16, name, "tick"))
        for value in sorted(set(xs)):
            count = xs.count(value)
            for k in range(count):
                cx = _doe_x(value) + 13 * k - 6.5 * (count - 1)
                parts.append(f'<circle cx="{cx:.1f}" cy="{y:.1f}" r="5.5" fill="{color}"/>')
    parts.append(_text(410, 112 + 46 * 3 - 16, "2次式の係数が決まらない", "tick", "end"))
    for t in (160, 170, 180, 190, 200):
        parts.append(_text(_doe_x((t - 180) / 20), 302, f"{t}", "tick", "middle"))
    parts.append(_text(410, 324, "焼き温度（℃）", "tick", "end"))

    parts.append(_text(20, 368, "② 点数の予測のばらつき"))
    vy = _scale(0.0, 1.2, 540, 384)
    parts.append(f'<path d="M64 384V540H410" fill="none" stroke="{GRID}"/>')
    for value in (0, 0.5, 1):
        parts.append(_text(56, vy(value) + 5, f"{value:g}", "tick", "end"))
    for _name, xs, color in DOE_DESIGNS:
        m = doe_information(xs)
        values = [(x, doe_variance(m, x)) for x in grid]
        parts.append(_polyline([(_doe_x(x), vy(v)) for x, v in values if v <= 1.2], color, 3))
    for t in (160, 180, 200):
        parts.append(_text(_doe_x((t - 180) / 20), 560, f"{t}℃", "tick", "middle"))
    labels = (
        (f"等間隔：最大 {worst['等間隔']:.2f}", POINT),
        (f"中央付近：両端で {worst['中央付近']:.0f}", UPDATE),
        (f"端と中央に2回ずつ：最大 {worst['端と中央に2回ずつ']:.2f}", LINE),
    )
    for index, (label, color) in enumerate(labels):
        y = 584 + 20 * index
        parts.append(_polyline([(64, y - 5), (84, y - 5)], color, 3))
        parts.append(_text(90, y, label, "tick"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


def _doe_weights_svg() -> str:
    history = doe_frank_wolfe()
    parts = _open(
        "候補の温度への重みと、最適の確かめ",
        (
            "160〜200℃を2℃おきに分けた21の候補温度に、実験の割合（重み）を配る。"
            "① Frank–Wolfe法で重みを動かした回数ごとの重み。"
            + "、".join(
                f"{k}回で160・180・200℃の重みの合計 "
                f"{sum(history[k][0][i] for i in (0, 10, 20)):.3f}"
                for k in DOE_SHOWN_STEPS
            )
            + "。② 重みで測った予測のばらつき（6回の値の6倍）の最大値と、係数の数3の差。"
            + "、".join(f"{k}回で {history[k][1]:.3g}" for k in (1, 10, 100, 1000))
            + "。0になる重みが最適。"
        ),
        600,
    )
    parts.append(_text(20, 64, "① 21の候補温度への重み"))
    for index, k in enumerate(DOE_SHOWN_STEPS):
        base = 150 + 70 * index
        wy = _scale(0.0, 0.4, base, base - 52)
        parts.append(f'<path d="M64 {base}H410" stroke="{GRID}"/>')
        parts.append(_text(100, base - 30, f"{k}回", "tick"))
        for x, w in zip(DOE_CANDIDATES, history[k][0], strict=True):
            color = LINE if x in (-1.0, 0.0, 1.0) else MUTED
            parts.append(
                f'<path d="M{_doe_x(x):.1f} {base}V{wy(w):.1f}" stroke="{color}" stroke-width="5"/>'
            )
    parts.append(_text(56, 150 - 52 + 5, "0.4", "tick", "end"))
    parts.append(_text(56, 150 + 5, "0", "tick", "end"))
    for t in (160, 180, 200):
        parts.append(_text(_doe_x((t - 180) / 20), 312, f"{t}", "tick", "middle"))
    parts.append(_text(410, 334, "焼き温度（℃）", "tick", "end"))

    parts.append(_text(20, 378, "② 重みで測った予測のばらつきの最大値 − 3"))
    gx = _scale(0.0, 3.0, 64, 410)
    gy = _scale(-3.0, 1.0, 548, 396)
    parts.append(f'<path d="M64 396V548H410" fill="none" stroke="{GRID}"/>')
    for e in (-3, -2, -1, 0, 1):
        parts.append(_text(56, gy(e) + 5, f"{10.0**e:g}", "tick", "end"))
    for e in range(4):
        parts.append(_text(gx(e), 568, f"{10**e}", "tick", "middle"))
    points = [(gx(math.log10(k)), gy(math.log10(g))) for k, (_, g) in enumerate(history) if k >= 1]
    parts.append(_polyline(points, UPDATE, 3))
    parts.append(_text(410, 590, "重みを動かした回数（どちらも対数目盛）", "tick", "end"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


FIGURES: dict[str, Callable[[], str]] = {
    "doe-designs-variance.svg": _doe_designs_svg,
    "doe-weights-gap.svg": _doe_weights_svg,
}
