"""Robust parameter estimation (content/concepts/robust-parameter-estimation.md): the spring's eight
readings from the nonlinear least-squares lesson, with the reading at t=2.5 s recorded without its
minus sign (1.7 instead of -1.7). Huber loss with scale 0.3.
"""

from __future__ import annotations

import functools
import math
from collections.abc import Callable, Sequence

from ._svg import (
    GRID,
    INK,
    LINE,
    MUTED,
    POINT,
    RING,
    UPDATE,
    VIOLATION,
    _open,
    _polyline,
    _scale,
    _text,
)
from .nonlinear_least_squares import SPRING_T, SPRING_Y

RPE_Y = tuple(1.7 if index == 5 else y for index, y in enumerate(SPRING_Y))
RPE_BAD = 5
RPE_DELTA = 0.3


def rpe_huber(residual: float, delta: float = RPE_DELTA) -> float:
    size = abs(residual)
    return 0.5 * size * size if size <= delta else delta * (size - 0.5 * delta)


def rpe_huber_slope(residual: float, delta: float = RPE_DELTA) -> float:
    return max(-delta, min(delta, residual))


def rpe_squares_profile(w: float, ys: Sequence[float] = RPE_Y) -> tuple[float, float]:
    """(smallest sum of squares over the amplitude, that amplitude) at a fixed ω."""
    s = [math.sin(w * t) for t in SPRING_T]
    a = sum(si * yi for si, yi in zip(s, ys, strict=True)) / sum(si * si for si in s)
    return sum((a * si - yi) ** 2 for si, yi in zip(s, ys, strict=True)), a


def rpe_huber_profile(w: float) -> tuple[float, float]:
    """(smallest Huber loss over the amplitude, that amplitude): bisection on the monotone slope."""
    s = [math.sin(w * t) for t in SPRING_T]
    low, high = -20.0, 20.0
    for _ in range(100):
        mid = (low + high) / 2
        slope = sum(rpe_huber_slope(mid * si - yi) * si for si, yi in zip(s, RPE_Y, strict=True))
        low, high = (low, mid) if slope > 0 else (mid, high)
    a = (low + high) / 2
    return sum(rpe_huber(a * si - yi) for si, yi in zip(s, RPE_Y, strict=True)), a


def rpe_clean_profile(w: float) -> tuple[float, float]:
    """The same profile for the eight readings with the correct sign."""
    return rpe_squares_profile(w, SPRING_Y)


@functools.cache
def rpe_valleys(profile: Callable[[float], tuple[float, float]]) -> list[tuple[float, float]]:
    """Local minima of a profile on (0.2, 2π], each refined by golden-section search."""
    grid = [0.2 + (2 * math.pi - 0.2) * i / 1200 for i in range(1201)]
    values = [profile(w)[0] for w in grid]
    found = []
    for i in range(1, len(grid) - 1):
        if values[i] < values[i - 1] and values[i] <= values[i + 1]:
            low, high = grid[i - 1], grid[i + 1]
            ratio = (math.sqrt(5) - 1) / 2
            for _ in range(80):
                left, right = high - ratio * (high - low), low + ratio * (high - low)
                low, high = (low, right) if profile(left)[0] < profile(right)[0] else (left, high)
            w = (low + high) / 2
            found.append((w, profile(w)[0]))
    return found


def rpe_residuals(a: float, w: float) -> list[float]:
    return [a * math.sin(w * t) - y for t, y in zip(SPRING_T, RPE_Y, strict=True)]


def rpe_weights(a: float, w: float) -> list[float]:
    return [min(1.0, RPE_DELTA / max(abs(r), 1e-15)) for r in rpe_residuals(a, w)]


def rpe_irls(start: tuple[float, float] = (1.0, 1.8), steps: int = 8) -> list[tuple[float, ...]]:
    """Weighted Gauss–Newton: (J'WJ) d = -J'W r with Huber weights; rows (a, ω, Huber, SS, r, w)."""
    a, w = start
    rows = []
    for _ in range(steps + 1):
        r = rpe_residuals(a, w)
        weights = rpe_weights(a, w)
        rows.append(
            (
                a,
                w,
                sum(rpe_huber(ri) for ri in r),
                sum(ri * ri for ri in r),
                r[RPE_BAD],
                weights[RPE_BAD],
            )
        )
        j = [(math.sin(w * t), a * t * math.cos(w * t)) for t in SPRING_T]
        m11 = sum(wi * ji[0] * ji[0] for wi, ji in zip(weights, j, strict=True))
        m12 = sum(wi * ji[0] * ji[1] for wi, ji in zip(weights, j, strict=True))
        m22 = sum(wi * ji[1] * ji[1] for wi, ji in zip(weights, j, strict=True))
        g1 = sum(wi * ji[0] * ri for wi, ji, ri in zip(weights, j, r, strict=True))
        g2 = sum(wi * ji[1] * ri for wi, ji, ri in zip(weights, j, r, strict=True))
        det = m11 * m22 - m12 * m12
        a += (-m22 * g1 + m12 * g2) / det
        w += (m12 * g1 - m11 * g2) / det
    return rows


def _rpe_profile_svg() -> str:
    squares = rpe_valleys(rpe_squares_profile)
    huber = rpe_valleys(rpe_huber_profile)
    clean = rpe_valleys(rpe_clean_profile)
    sq_best = min(squares, key=lambda v: v[1])
    hu_best = min(huber, key=lambda v: v[1])
    near = min(squares, key=lambda v: abs(v[0] - 2.0))
    parts = _open(
        "外れた1点で、最も深い谷が入れ替わる",
        (
            "角周波数ωを固定し、振幅aを最もよく選んだときの損失。2.5秒の読みを1.7と記録した8点。"
            f"① 二乗和：最も深い谷はω={sq_best[0]:.2f}（{sq_best[1]:.2f}）、"
            f"ω=2付近の谷はω={near[0]:.2f}（{near[1]:.2f}）。"
            f"破線は符号が正しい8点の二乗和で、最も深い谷はω={clean[0][0]:.2f}。"
            f"② Huber損失（尺度0.3）：最も深い谷はω={hu_best[0]:.2f}（{hu_best[1]:.3f}）。"
        ),
        612,
    )
    px = _scale(0.0, 2 * math.pi, 64, 416)
    # sin(2π t) is 0 at every reading, so the amplitude is undefined at ω = 2π itself.
    ws = [0.2 + (2 * math.pi - 0.25) * i / 400 for i in range(401)]
    for tick in range(7):
        parts.append(_text(px(tick), 292, str(tick), "tick", "middle"))
        parts.append(_text(px(tick), 572, str(tick), "tick", "middle"))
    parts.append(_text(20, 64, "① 二乗和"))
    sy = _scale(0.0, 16.0, 272, 84)
    parts.append(f'<path d="M64 84V272H416" fill="none" stroke="{GRID}"/>')
    for value in (0, 5, 10, 15):
        parts.append(_text(56, sy(value) + 5, str(value), "tick", "end"))
    clean_curve = [(px(w), sy(rpe_clean_profile(w)[0])) for w in ws]
    parts.append(_polyline(clean_curve, MUTED, 1.5).replace("/>", ' stroke-dasharray="5 4"/>'))
    parts.append(_polyline([(px(w), sy(rpe_squares_profile(w)[0])) for w in ws], POINT, 3))
    for w, value in squares:
        color = POINT if (w, value) == sq_best else RING
        parts.append(f'<circle cx="{px(w):.1f}" cy="{sy(value):.1f}" r="6" fill="{color}"/>')
    parts.append(
        _text(
            px(sq_best[0]) - 10,
            sy(sq_best[1]) + 26,
            f"ω={sq_best[0]:.2f}：{sq_best[1]:.2f}",
            anchor="end",
        )
    )
    parts.append(_text(px(near[0]) + 10, sy(near[1]) + 24, f"ω={near[0]:.2f}：{near[1]:.2f}"))
    parts.append(_text(20, 318, "実線：記録どおりの8点　破線：符号が正しい8点", "tick"))

    parts.append(_text(20, 344, f"② Huber損失（尺度 {RPE_DELTA:g}）"))
    hy = _scale(0.0, 3.2, 552, 364)
    parts.append(f'<path d="M64 364V552H416" fill="none" stroke="{GRID}"/>')
    for value in (0, 1, 2, 3):
        parts.append(_text(56, hy(value) + 5, str(value), "tick", "end"))
    parts.append(_polyline([(px(w), hy(rpe_huber_profile(w)[0])) for w in ws], UPDATE, 3))
    for w, value in huber:
        color = UPDATE if (w, value) == hu_best else RING
        parts.append(f'<circle cx="{px(w):.1f}" cy="{hy(value):.1f}" r="6" fill="{color}"/>')
    parts.append(
        _text(px(hu_best[0]) + 10, hy(hu_best[1]) + 24, f"ω={hu_best[0]:.2f}：{hu_best[1]:.2f}")
    )
    parts.append(_text(416, 596, "角周波数 ω", "tick", "end"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


def _rpe_weights_svg() -> str:
    a_h, w_h = rpe_irls()[-1][:2]
    sq_best = min(rpe_valleys(rpe_squares_profile), key=lambda v: v[1])
    a_s = rpe_squares_profile(sq_best[0])[1]
    weights = rpe_weights(a_h, w_h)
    parts = _open(
        "Huberの当てはめと、各観測の重み",
        (
            "① 8つの観測と2本の曲線。2.5秒の読みは −1.7 を 1.7 と記録したもの。"
            f"Huber損失の当てはめは a={a_h:.2f}、ω={w_h:.2f}、"
            f"二乗和で最も深い谷は a={a_s:.2f}、ω={sq_best[0]:.2f}。"
            "② Huberの当てはめでの各観測の重み min(1, 0.3/|r|)。"
            f"2.5秒の観測だけが {weights[RPE_BAD]:.3f}、ほかの7つは1。"
        ),
        604,
    )
    parts.append(_text(20, 64, "① 観測点と曲線"))
    px = _scale(0.0, 3.5, 64, 410)
    py = _scale(-2.6, 2.6, 290, 84)
    parts.append(f'<path d="M64 84V290H410" fill="none" stroke="{GRID}"/>')
    parts.append(f'<path d="M64 {py(0):.1f}H410" stroke="{GRID}" stroke-width="1"/>')
    for value in (-2, 0, 2):
        parts.append(_text(56, py(value) + 5, f"{value}".replace("-", "−"), "tick", "end"))
    for value in (0, 1, 2, 3):
        parts.append(_text(px(value), 310, str(value), "tick", "middle"))
    parts.append(_text(410, 332, "時刻 t（秒）", "tick", "end"))
    ts = [3.5 * i / 280 for i in range(281)]
    parts.append(
        _polyline([(px(t), py(a_s * math.sin(sq_best[0] * t))) for t in ts], POINT, 2).replace(
            "/>", ' stroke-dasharray="6 4"/>'
        )
    )
    parts.append(_polyline([(px(t), py(a_h * math.sin(w_h * t))) for t in ts], UPDATE, 3))
    for index, (t, y) in enumerate(zip(SPRING_T, RPE_Y, strict=True)):
        if index == RPE_BAD:
            parts.append(
                f'<circle cx="{px(t):.1f}" cy="{py(y):.1f}" r="9" fill="none" '
                f'stroke="{VIOLATION}" stroke-width="2.5"/>'
            )
        parts.append(f'<circle cx="{px(t):.1f}" cy="{py(y):.1f}" r="5" fill="{INK}"/>')
    parts.append(_polyline([(20, 360 - 5), (42, 360 - 5)], UPDATE, 3))
    parts.append(_text(48, 360, f"Huber：ω={w_h:.2f}", "tick"))
    parts.append(
        _polyline([(210, 360 - 5), (232, 360 - 5)], POINT, 2).replace(
            "/>", ' stroke-dasharray="6 4"/>'
        )
    )
    parts.append(_text(238, 360, f"二乗和：ω={sq_best[0]:.2f}", "tick"))
    parts.append(
        f'<circle cx="31" cy="379" r="8" fill="none" stroke="{VIOLATION}" stroke-width="2.5"/>'
    )
    parts.append(_text(48, 384, "2.5秒の読み：記録は1.7（本来は −1.7）", "tick"))

    parts.append(_text(20, 422, "② Huberの当てはめでの重み"))
    by = _scale(0.0, 1.0, 536, 446)
    bx = _scale(-0.25, 3.75, 64, 410)
    parts.append(f'<path d="M64 446V536H410" fill="none" stroke="{GRID}"/>')
    for value in (0, 1):
        parts.append(_text(56, by(value) + 5, str(value), "tick", "end"))
    for index, (t, weight) in enumerate(zip(SPRING_T, weights, strict=True)):
        color = VIOLATION if index == RPE_BAD else LINE
        top = by(weight)
        parts.append(
            f'<rect x="{bx(t) - 10:.1f}" y="{top:.1f}" width="20" height="{536 - top:.1f}" '
            f'fill="{color}"/>'
        )
        parts.append(_text(bx(t), 556, f"{t:g}", "tick", "middle"))
    parts.append(
        _text(
            bx(SPRING_T[RPE_BAD]),
            by(weights[RPE_BAD]) - 8,
            f"{weights[RPE_BAD]:.3f}",
            anchor="middle",
        )
    )
    parts.append(_text(410, 584, "観測の時刻 t（秒）", "tick", "end"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


FIGURES: dict[str, Callable[[], str]] = {
    "robust-estimation-profile.svg": _rpe_profile_svg,
    "robust-estimation-weights.svg": _rpe_weights_svg,
}
