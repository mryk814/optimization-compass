"""Optimization with an external solver in the objective
(content/concepts/external-solver-objective.md): an A–B alloy whose stand-in "tool" returns the
phase combination with the lowest Gibbs energy, g_α = (x − 0.1)², g_β = (x − 0.6)² + 0.1.
"""

from __future__ import annotations

from collections.abc import Callable

from ._svg import GRID, LINE, POINT, RING, UPDATE, VIOLATION, _open, _polyline, _scale, _text

EXT_TANGENT = (0.2, 0.7)  # where the common tangent G = 0.2x − 0.03 touches the two parabolas
EXT_TARGET = 0.3
EXT_START = 0.6
# The three runs of the article's pitfall, as SciPy 1.18.1 reports them from x0 = 0.6 with the
# article's J (finite-difference gradients for the first two): (name, bounds, end, calls).
EXT_RUNS = (
    ("BFGS", "範囲なし", -0.41, 4),
    ("L-BFGS-B", "範囲 [0,1]", 0.0, 4),
    ("Nelder–Mead", "範囲 [0,1]", 0.35, 30),
)


def ext_equilibrium(x: float) -> tuple[str, float, float]:
    """(phases, β fraction, Gibbs energy) of the candidate with the lowest Gibbs energy."""
    low, high = EXT_TANGENT
    candidates = [("α", 0.0, (x - 0.1) ** 2), ("β", 1.0, (x - 0.6) ** 2 + 0.1)]
    if low < x < high:
        fraction = (x - low) / (high - low)
        candidates.append(("α+β", fraction, 0.2 * x - 0.03))
    return min(candidates, key=lambda c: c[2])


def ext_objective(x: float) -> float:
    value = (ext_equilibrium(x)[1] - EXT_TARGET) ** 2
    return 0.0 if abs(value) < 1e-12 else value


def _ext_flat_stop_svg() -> str:
    low, high = EXT_TANGENT
    start_j = ext_objective(EXT_START)
    parts = _open(
        "差分の勾配は、βが0の平らな範囲で止まる",
        (
            "Bの分率 x（−0.5〜1）と外側の目的 J=(βの量−0.30)²。"
            f"x が {low:g} 以下では β がなく J=0.09 で平ら、"
            f"{high:g} 以上では β だけで J=0.49 で平ら、"
            f"そのあいだで J=4(x−0.35)² の谷。始点 {EXT_START:g}（J={start_j:g}）から、"
            "範囲なしのBFGSは x=−0.41 で、範囲 [0, 1] のL-BFGS-Bは x=0 で、どちらも J=0.09 のまま"
            "止まる。範囲 [0, 1] のNelder–Meadは 30 回の計算で x=0.35、J=0 に着く。"
        ),
        478,
    )
    px = _scale(-0.5, 1.0, 56, 416)
    py = _scale(0.0, 0.5, 300, 84)
    parts.append(
        f'<rect x="{px(-0.5):.1f}" y="84" width="{px(0.0) - px(-0.5):.1f}" height="216" '
        f'fill="{VIOLATION}" opacity="0.08"/>'
    )
    parts.append(
        f'<rect x="{px(low):.1f}" y="84" width="{px(high) - px(low):.1f}" height="216" '
        f'fill="{RING}" opacity="0.25"/>'
    )
    parts.append(_text((px(-0.5) + px(0.0)) / 2, 74, "組成の外", "tick", "middle"))
    parts.append(_text((px(0.0) + px(low)) / 2, 74, "αだけ", "tick", "middle"))
    parts.append(_text((px(low) + px(high)) / 2, 74, "α+β", "tick", "middle"))
    parts.append(_text((px(high) + px(1.0)) / 2, 74, "βだけ", "tick", "middle"))
    parts.append(f'<path d="M56 84V300H416" fill="none" stroke="{GRID}" stroke-width="1.5"/>')
    for value in (0.0, 0.09, 0.25, 0.49):
        parts.append(
            f'<path d="M56 {py(value):.1f}H416" stroke="{GRID}" stroke-width="0.6" opacity="0.6"/>'
        )
        parts.append(_text(48, py(value) + 5, f"{value:g}", "tick", "end"))
    for value in (-0.5, 0.0, 0.35, 0.6, 1.0):
        parts.append(_text(px(value), 320, f"{value:g}".replace("-", "−"), "tick", "middle"))
    parts.append(_text(416, 342, "Bの分率 x", "tick", "end"))
    xs = [-0.5 + 1.5 * i / 600 for i in range(601)]
    parts.append(_polyline([(px(x), py(ext_objective(x))) for x in xs], LINE, 3))
    sx, sy = px(EXT_START), py(start_j)
    for name, _, end, _ in EXT_RUNS:
        ex, ey = px(end), py(ext_objective(end))
        lift = 70 if name == "BFGS" else 40
        parts.append(
            f'<path d="M{sx:.1f} {sy:.1f}Q{(sx + ex) / 2:.1f} {min(sy, ey) - lift:.1f} '
            f'{ex:.1f} {ey:.1f}" fill="none" stroke="{UPDATE}" stroke-width="1.6" '
            'stroke-dasharray="5 4"/>'
        )
        if end == 0.35:
            parts.append(f'<circle cx="{ex:.1f}" cy="{ey:.1f}" r="7" fill="{LINE}"/>')
            parts.append(_text(ex, ey - 12, name, "tick", "middle"))
        else:
            parts.append(
                f'<rect x="{ex - 6:.1f}" y="{ey - 6:.1f}" width="12" height="12" fill="#f7f8f3" '
                f'stroke="{POINT}" stroke-width="2.5"/>'
            )
            # Both labels sit under their squares; L-BFGS-B ends at its square to clear Nelder–Mead.
            if name == "BFGS":
                parts.append(_text(ex, ey + 26, name, "tick", "middle"))
            else:
                parts.append(_text(ex + 6, ey + 26, name, "tick", "end"))
    parts.append(f'<circle cx="{sx:.1f}" cy="{sy:.1f}" r="7" fill="{UPDATE}"/>')
    parts.append(_text(sx + 12, sy + 5, "始点", ""))
    parts.append(_text(20, 372, f"始点 x={EXT_START:.2f}（J={start_j:g}）から："))
    for index, (name, bounds, end, calls) in enumerate(EXT_RUNS):
        value = ext_objective(end)
        tail = f"、{calls}回" if name == "Nelder–Mead" else ""
        line = f"{name}（{bounds}）→ x={end:.2f}、J={value:g}{tail}".replace("-0", "−0")
        parts.append(_text(20, 396 + 24 * index, line, "note" if value == 0 else ""))
    parts.append(_text(20, 468, "上の2つは「成功」と報告して止まる"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


FIGURES: dict[str, Callable[[], str]] = {
    "external-solver-flat-stop.svg": _ext_flat_stop_svg,
}
