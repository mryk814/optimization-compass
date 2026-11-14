"""Robust regression (content/concepts/robust-regression.md): one constant fitted to
(0, 0, 0, 10).
"""

from __future__ import annotations

from collections.abc import Callable

from ._svg import GRID, POINT, UPDATE, _open, _polyline, _scale, _text

ROBUST_OBSERVATIONS = (0.0, 0.0, 0.0, 10.0)
ROBUST_DELTA = 1.0


def _robust_slope(residual: float, delta: float | None) -> float:
    """Loss slope: r for the squared loss (delta None), clip(r, -delta, delta) for Huber."""
    if delta is None:
        return residual
    return max(-delta, min(delta, residual))


def robust_fit(delta: float | None) -> tuple[float, list[float]]:
    """Minimiser of the summed loss (bisection on the monotone slope sum) and each slope there."""
    low, high = min(ROBUST_OBSERVATIONS), max(ROBUST_OBSERVATIONS)
    for _ in range(200):
        mid = (low + high) / 2
        total = sum(_robust_slope(mid - y, delta) for y in ROBUST_OBSERVATIONS)
        low, high = (low, mid) if total > 0 else (mid, high)
    x = (low + high) / 2
    return x, [_robust_slope(x - y, delta) for y in ROBUST_OBSERVATIONS]


def _fraction(value: float) -> str:
    return "1/3" if abs(value - 1 / 3) < 1e-9 else f"{value:g}".replace("-", "−")


def _robust_huber_svg() -> str:
    squared_x, squared = robust_fit(None)
    huber_x, huber = robust_fit(ROBUST_DELTA)
    parts = _open(
        "傾きを抑えると、釣合いが変わる",
        (
            "「残差 r と損失の傾き」は、二乗が r のまま増え、Huber（δ=1）は±1で頭打ちです。"
            f"「各解での、四観測の勾配への寄与」は観測 (0, 0, 0, 10) について、"
            f"二乗の解 x={squared_x:g} では 2.5, 2.5, 2.5, −7.5、"
            "Huberの解 x=1/3 では 1/3, 1/3, 1/3, −1 となり、"
            "どちらも合計は0です。"
        ),
        560,
    )
    parts.append(_text(20, 60, "① 残差 r と損失の傾き"))
    px = _scale(-3.0, 3.0, 64, 420)
    py = _scale(-3.0, 3.0, 220, 80)
    parts.append(f'<path d="M64 80V220H420" fill="none" stroke="{GRID}"/>')
    parts.append(f'<path d="M64 {py(0):.1f}H420" stroke="{GRID}" stroke-width="1"/>')
    for x in (-1.0, 1.0):
        parts.append(
            f'<path d="M{px(x):.1f} 80V220" stroke="{GRID}" stroke-width="1" '
            'stroke-dasharray="3 4"/>'
        )
    for value in (-3.0, 0.0, 3.0):
        parts.append(_text(56, py(value) + 5, f"{value:g}".replace("-", "−"), "tick", "end"))
        parts.append(_text(px(value), 240, f"{value:g}".replace("-", "−"), "tick", "middle"))
    parts.append(_text(420, 262, "残差 r", "tick", "end"))
    parts.append(_polyline([(px(-3), py(-3)), (px(3), py(3))], POINT, 3))
    parts.append(
        _polyline(
            [(px(r), py(_robust_slope(r, ROBUST_DELTA))) for r in (-3.0, -1.0, 1.0, 3.0)],
            UPDATE,
            3,
        )
    )
    parts.append(_text(72, 100, "二乗の傾き r").replace("<text ", f'<text style="fill:{POINT}" '))
    parts.append(
        _text(420, py(1.0) + 22, "Huber（δ=1）", anchor="end").replace(
            "<text ", f'<text style="fill:{UPDATE}" '
        )
    )

    parts.append(_text(20, 300, "② 各解での、四観測の勾配への寄与"))
    top, bottom = 330, 470
    qy = _scale(-10.5, 5.0, bottom, top)
    group = (420 - 64) / 4
    bar = 26.0
    parts.append(f'<path d="M64 {top}V{bottom}H420" fill="none" stroke="{GRID}"/>')
    parts.append(f'<path d="M64 {qy(0):.1f}H420" stroke="{GRID}" stroke-width="1"/>')
    for value in (-5.0, 0.0, 5.0):
        parts.append(_text(56, qy(value) + 5, f"{value:g}".replace("-", "−"), "tick", "end"))
    for index, label in enumerate(("0①", "0②", "0③", "10")):
        centre = 64 + group * (index + 0.5)
        parts.append(_text(centre, bottom + 20, label, "tick", "middle"))
        for offset, value, color in ((-bar - 2, squared[index], POINT), (2, huber[index], UPDATE)):
            y0, y1 = qy(0), qy(value)
            parts.append(
                f'<rect x="{centre + offset:.1f}" y="{min(y0, y1):.1f}" width="{bar}" '
                f'height="{abs(y1 - y0):.1f}" fill="{color}"/>'
            )
            label_y = y1 - 6 if value > 0 else y1 + 16
            parts.append(
                _text(centre + offset + bar / 2, label_y, _fraction(value), "tick", "middle")
            )
    parts.append(f'<rect x="20" y="504" width="20" height="12" fill="{POINT}"/>')
    parts.append(_text(48, 515, f"二乗の解 x={squared_x:g}"))
    parts.append(f'<rect x="230" y="504" width="20" height="12" fill="{UPDATE}"/>')
    parts.append(_text(258, 515, "Huberの解 x=1/3"))
    parts.append(_text(20, 546, "どちらの解でも、四つの寄与の和は0", "note"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


FIGURES: dict[str, Callable[[], str]] = {
    "robust-regression-huber.svg": _robust_huber_svg,
}
