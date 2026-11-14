"""Large-scale stochastic ERM (content/concepts/stochastic-erm.md): logistic regression with an L2
penalty on 10,000 purchase records. The figure draws 200 minibatch gradients (32 records each) at
the start point and at the minimiser; the article's code prints the same numbers.
"""

from __future__ import annotations

import math
import random
from collections.abc import Callable, Sequence

from ._svg import GRID, LINE, MUTED, UPDATE, _open, _scale, _signed, _text

ERM_N = 10_000
ERM_LAM = 0.01
ERM_BATCH = 32
ERM_REPS = 200


def _sigmoid(s: float) -> float:
    return 1 / (1 + math.exp(-s)) if s >= 0 else math.exp(s) / (1 + math.exp(s))


def erm_data() -> tuple[list[float], list[int]]:
    rng = random.Random(0)
    xs = [rng.gauss(0.0, 1.0) for _ in range(ERM_N)]
    ys = [int(rng.random() < 1 / (1 + math.exp(1.0 - 2.0 * x))) for x in xs]
    return xs, ys


def erm_gradient(
    w: Sequence[float], xs: Sequence[float], ys: Sequence[int], idx: Sequence[int]
) -> tuple[float, float]:
    g0 = g1 = 0.0
    for i in idx:
        e = _sigmoid(w[0] + w[1] * xs[i]) - ys[i]
        g0, g1 = g0 + e, g1 + e * xs[i]
    return g0 / len(idx) + ERM_LAM * w[0], g1 / len(idx) + ERM_LAM * w[1]


def erm_minimiser(xs: Sequence[float], ys: Sequence[int]) -> tuple[float, float]:
    """Ten full Newton steps from (0, 0) on the 2x2 problem, as in the article."""
    every = range(ERM_N)
    w = [0.0, 0.0]
    for _ in range(10):
        g, h = erm_gradient(w, xs, ys, every), [ERM_LAM, 0.0, ERM_LAM]
        for x in xs:
            p = _sigmoid(w[0] + w[1] * x)
            q = p * (1 - p) / ERM_N
            h = [h[0] + q, h[1] + q * x, h[2] + q * x * x]
        det = h[0] * h[2] - h[1] ** 2
        w = [w[0] - (h[2] * g[0] - h[1] * g[1]) / det, w[1] - (h[0] * g[1] - h[1] * g[0]) / det]
    return w[0], w[1]


def erm_minibatch_data() -> dict[str, object]:
    """Full gradient, 200 minibatch gradients, their RMS deviation and same-side count."""
    xs, ys = erm_data()
    out: dict[str, object] = {"minimiser": erm_minimiser(xs, ys)}
    for name, point in (("start", (0.0, 0.0)), ("minimum", out["minimiser"])):
        full = erm_gradient(point, xs, ys, range(ERM_N))  # type: ignore[arg-type]
        rng = random.Random(1)
        grads = [
            erm_gradient(point, xs, ys, rng.sample(range(ERM_N), ERM_BATCH))  # type: ignore[arg-type]
            for _ in range(ERM_REPS)
        ]
        rms = math.sqrt(sum((a - full[0]) ** 2 + (b - full[1]) ** 2 for a, b in grads) / ERM_REPS)
        same = sum(a * full[0] + b * full[1] > 0 for a, b in grads)
        out[name] = {"point": point, "full": full, "grads": grads, "rms": rms, "same": same}
    return out


def _erm_minibatch_svg() -> str:
    data = erm_minibatch_data()
    start, minimum = data["start"], data["minimum"]
    w0, w1 = data["minimiser"]  # type: ignore[misc]
    parts = _open(
        "32件の勾配は、全件の勾配のまわりに散らばる",
        (
            "1万件のロジスティック回帰で、32件ずつ選んで作った勾配200本を、"
            "全件の勾配と同じ平面に描いた図です。"
            f"初期点 (0, 0) では全件の勾配が ({start['full'][0]:.3f}, "  # type: ignore[index]
            f"{_signed(start['full'][1], 3)}) で、"  # type: ignore[index]
            f"200本のうち{start['same']}本が同じ側にあり、ずれのRMSは"  # type: ignore[index]
            f"{start['rms']:.3f}です。"  # type: ignore[index]
            f"最小点 ({_signed(w0, 3)}, {w1:.3f}) では全件の勾配が0で、"
            f"32件の勾配の大きさのRMSは{minimum['rms']:.3f}です。"  # type: ignore[index]
        ),
        780,
    )
    low, high = -0.36, 0.54
    y_low, y_high = -0.64, 0.26
    size = 220.0
    left = 110.0
    px = _scale(low, high, left, left + size)
    for index, (key, label) in enumerate(
        (
            ("start", "① 初期点 w = (0, 0)"),
            ("minimum", f"② 最小点 w* = ({_signed(w0, 3)}, {w1:.3f})"),
        )
    ):
        group = data[key]
        top = 90 + index * 322
        py = _scale(y_low, y_high, top + size, top)
        parts.append(_text(20, top - 18, label))
        parts.append(
            f'<rect x="{left}" y="{top}" width="{size}" height="{size}" fill="#ffffff" '
            f'stroke="{GRID}"/>'
        )
        parts.append(
            f'<path d="M{left} {py(0):.1f}H{left + size}M{px(0):.1f} {top}V{top + size}" '
            f'stroke="{GRID}" stroke-width="1"/>'
        )
        for value in (-0.3, 0.0, 0.3):
            parts.append(_text(px(value), top + size + 20, _signed(value, 1), "tick", "middle"))
        for value in (-0.6, -0.3, 0.0):
            parts.append(_text(left - 8, py(value) + 5, _signed(value, 1), "tick", "end"))
        full = group["full"]  # type: ignore[index]
        if math.hypot(*full) > 1e-9:
            # Points on this line have zero inner product with the full gradient.
            ux, uy = -full[1], full[0]
            reach = 0.62 / math.hypot(ux, uy)
            a = (px(-ux * reach), py(-uy * reach))
            b = (px(ux * reach), py(uy * reach))
            parts.append(
                f'<clipPath id="erm-clip-{index}"><rect x="{left}" y="{top}" '
                f'width="{size}" height="{size}"/></clipPath>'
            )
            parts.append(
                f'<path d="M{a[0]:.1f} {a[1]:.1f}L{b[0]:.1f} {b[1]:.1f}" stroke="{MUTED}" '
                f'stroke-width="1.5" clip-path="url(#erm-clip-{index})"/>'
            )
        for g0, g1 in group["grads"]:  # type: ignore[index]
            assert low < g0 < high and y_low < g1 < y_high, (g0, g1)
            parts.append(
                f'<circle cx="{px(g0):.1f}" cy="{py(g1):.1f}" r="2.6" fill="{LINE}" '
                'fill-opacity="0.55"/>'
            )
        fx, fy = px(full[0]), py(full[1])
        if math.hypot(*full) > 1e-9:
            parts.append(
                f'<path d="M{px(0):.1f} {py(0):.1f}L{fx:.1f} {fy:.1f}" stroke="{UPDATE}" '
                'stroke-width="3"/>'
            )
        parts.append(
            f'<path d="M{fx:.1f} {fy - 8:.1f}L{fx + 8:.1f} {fy:.1f}L{fx:.1f} {fy + 8:.1f}'
            f'L{fx - 8:.1f} {fy:.1f}Z" fill="{UPDATE}" stroke="#ffffff" stroke-width="1.5"/>'
        )
        if key == "start":
            note = f"200本のうち{group['same']}本が灰の線の同じ側"  # type: ignore[index]
        else:
            note = f"全件の勾配は0、32件の勾配はRMS {group['rms']:.3f}"  # type: ignore[index]
        parts.append(_text(20, top + size + 46, note, "note"))
    parts.append(_text(20, 710, "青緑の点：32件で作った勾配（200回）"))
    parts.append(_text(20, 734, "橙のひし形：全件の勾配"))
    parts.append(_text(20, 760, "横は切片の勾配 g₀、縦は傾きの勾配 g₁", "tick"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


FIGURES: dict[str, Callable[[], str]] = {
    "stochastic-erm-minibatch.svg": _erm_minibatch_svg,
}
