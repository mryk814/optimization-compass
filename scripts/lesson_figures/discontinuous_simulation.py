"""Deterministic but discontinuous simulation (content/concepts/discontinuous-simulation.md): a
dryer dial x in [0, 1] whose simulator switches operating regime at x = 0.55.
"""

from __future__ import annotations

from collections.abc import Callable

from ._svg import GRID, LINE, POINT, UPDATE, _open, _polyline, _scale, _text

DRYER_CLIFF = 0.55


def dryer_value(x: float) -> float:
    if x < DRYER_CLIFF:
        return 0.40 + 2.0 * (x - 0.25) ** 2
    return 0.20 + 2.0 * (x - 0.80) ** 2


def dryer_compass(x0: float, step0: float, tol: float = 1e-4) -> tuple[float, float, int]:
    """Compass search on [0, 1]: poll +step then -step, take the first improvement, else halve."""
    x, fx, step, evaluations = x0, dryer_value(x0), step0, 1
    while step > tol:
        moved = False
        for candidate in (x + step, x - step):
            if 0.0 <= candidate <= 1.0:
                value = dryer_value(candidate)
                evaluations += 1
                if value < fx:
                    x, fx, moved = candidate, value, True
                    break
        if not moved:
            step /= 2
    return x, fx, evaluations


def _discontinuous_dryer_svg() -> str:
    start = 0.10
    cliff_left = 0.40 + 2.0 * (DRYER_CLIFF - 0.25) ** 2  # limit of the low-dial piece at the cliff
    cliff_right = dryer_value(DRYER_CLIFF)
    px = _scale(0.0, 1.0, 56, 416)
    py = _scale(0.65, 0.10, 52, 300)
    parts = _open(
        "運転ダイヤルと1バッチの総コスト",
        (
            f"ダイヤル x が {DRYER_CLIFF:g} で運転の切り替わる乾燥機の総コスト F。"
            f"x が {DRYER_CLIFF:g} 未満では底が (0.25, F = 0.4) の谷、{DRYER_CLIFF:g} 以上では"
            f"底が (0.8, F = 0.2) の谷。段差で F は {cliff_left:g} から"
            f"{cliff_right:g} に飛びます。"
            f"出発 {start:g} で F = {dryer_value(start):g}。"
        ),
        486,
    )
    parts.append(f'<path d="M56 52V300H416" fill="none" stroke="{GRID}" stroke-width="1.5"/>')
    for value in (0.2, 0.4, 0.6):
        parts.append(
            f'<path d="M56 {py(value):.1f}H416" stroke="{GRID}" stroke-width="0.6" opacity="0.6"/>'
        )
        parts.append(_text(48, py(value) + 5, f"{value:g}", "tick", "end"))
    for value in (0, 0.5, 1):
        parts.append(_text(px(value), 320, f"{value:g}", "tick", "middle"))
    parts.append(_text(416, 344, "ダイヤル x", "tick", "end"))
    parts.append(_text(62, 70, "総コスト F", "tick"))
    for lo, hi in ((0.0, DRYER_CLIFF - 1e-9), (DRYER_CLIFF, 1.0)):
        xs = [lo + (hi - lo) * i / 100 for i in range(101)]
        parts.append(_polyline([(px(x), py(dryer_value(x))) for x in xs], LINE, 3))
    cx = px(DRYER_CLIFF)
    parts.append(
        f'<path d="M{cx:.1f} 52V300" stroke="{GRID}" stroke-width="1.2" stroke-dasharray="4 4"/>'
    )
    parts.append(
        f'<path d="M{cx:.1f} {py(cliff_left):.1f}V{py(cliff_right):.1f}" '
        f'stroke="{UPDATE}" stroke-width="3"/>'
    )
    parts.append(
        f'<circle cx="{cx:.1f}" cy="{py(cliff_left):.1f}" r="6" fill="#f7f8f3" '
        f'stroke="{LINE}" stroke-width="2.5"/>'
    )
    parts.append(f'<circle cx="{cx:.1f}" cy="{py(cliff_right):.1f}" r="6" fill="{LINE}"/>')
    jump = round(cliff_right - cliff_left, 6)
    parts.append(
        _text(
            cx + 10, py((cliff_left + cliff_right) / 2) + 5, f"段差 {jump:g}".replace("-", "−"), ""
        )
    )
    for first in (start + 0.4, start + 0.5):
        parts.append(
            f'<rect x="{px(first) - 6:.1f}" y="{py(dryer_value(first)) - 6:.1f}" width="12" '
            f'height="12" fill="#f7f8f3" stroke="{POINT}" stroke-width="2.5"/>'
        )
    parts.append(_text(px(0.5) - 10, py(dryer_value(0.5)) - 12, "0.50", "tick", "end"))
    parts.append(_text(px(0.6) + 10, py(dryer_value(0.6)) - 10, "0.60", "tick"))
    for bottom in (0.25, 0.80):
        parts.append(
            f'<circle cx="{px(bottom):.1f}" cy="{py(dryer_value(bottom)):.1f}" r="6.5" '
            f'fill="{POINT}"/>'
        )
        parts.append(
            _text(px(bottom), py(dryer_value(bottom)) + 30, f"{bottom:.2f}", "tick", "middle")
        )
    parts.append(
        f'<circle cx="{px(start):.1f}" cy="{py(dryer_value(start)):.1f}" r="7" fill="{UPDATE}"/>'
    )
    parts.append(_text(px(start), py(dryer_value(start)) - 14, "出発", "", "middle"))
    parts.append(
        _text(20, 372, f"段差：F(0.55) = {cliff_right:g}、直前の極限は {cliff_left:g}", "note")
    )
    parts.append(_text(20, 396, f"橙の丸：出発 {start:.2f}、F = {dryer_value(start):g}"))
    parts.append(_text(20, 420, f"紺の丸：0.55 未満の谷の底 0.25、F = {dryer_value(0.25):g}"))
    parts.append(_text(20, 444, f"紺の丸：0.55 以上の谷の底 0.80、F = {dryer_value(0.80):g}"))
    parts.append(_text(20, 468, "白い四角：最初に試す 0.50 と 0.60"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


FIGURES: dict[str, Callable[[], str]] = {
    "discontinuous-dryer-cliff.svg": _discontinuous_dryer_svg,
}
