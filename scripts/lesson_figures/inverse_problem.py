"""Inverse problem (content/concepts/inverse-problem.md): a rod's initial temperature profile is
recovered from 40 blurred, noisy readings. Pure Python, so the figure needs no numeric extra.
"""

from __future__ import annotations

import json
import math
import random
from collections.abc import Callable

from ._numeric import _solve_linear
from ._svg import GRID, LINE, UPDATE, _open, _polyline, _scale, _text

INV_N = 40
INV_WIDTH = 0.05
INV_SIGMA = 1e-3


def inverse_problem_data() -> tuple[list[list[float]], list[float], list[float]]:
    xs = [(i + 0.5) / INV_N for i in range(INV_N)]
    kernel = [[math.exp(-((a - b) ** 2) / (2 * INV_WIDTH**2)) for b in xs] for a in xs]
    blur = [[v / sum(row) for v in row] for row in kernel]
    truth = [
        math.exp(-(((x - 0.3) / 0.08) ** 2)) + 0.6 * math.exp(-(((x - 0.7) / 0.06) ** 2))
        for x in xs
    ]
    rng = random.Random(0)
    noise = [INV_SIGMA * rng.gauss(0, 1) for _ in range(INV_N)]
    data = [
        sum(a * t for a, t in zip(row, truth, strict=True)) + e
        for row, e in zip(blur, noise, strict=True)
    ]
    return blur, truth, data


def inverse_problem_curve() -> tuple[float, float, list[tuple[float, float]]]:
    """Return the discrepancy-principle alpha, its error, and (log10 alpha, error) points."""
    blur, truth, data = inverse_problem_data()
    size = INV_N
    gram = [
        [sum(blur[k][i] * blur[k][j] for k in range(size)) for j in range(size)]
        for i in range(size)
    ]
    gtd = [sum(blur[k][i] * data[k] for k in range(size)) for i in range(size)]
    norm_truth = math.sqrt(sum(t * t for t in truth))

    def solve(alpha: float) -> list[float]:
        shifted = [
            [gram[i][j] + (alpha if i == j else 0.0) for j in range(size)] for i in range(size)
        ]
        return _solve_linear(shifted, gtd)

    def error(m: list[float]) -> float:
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(m, truth, strict=True))) / norm_truth

    def residual(m: list[float]) -> float:
        return math.sqrt(
            sum(
                (sum(a * v for a, v in zip(row, m, strict=True)) - d) ** 2
                for row, d in zip(blur, data, strict=True)
            )
        )

    delta = INV_SIGMA * math.sqrt(size)
    lo, hi = -10.0, 0.0
    for _ in range(50):
        mid = (lo + hi) / 2
        if residual(solve(10**mid)) < delta:
            lo = mid
        else:
            hi = mid
    alpha = 10 ** ((lo + hi) / 2)
    curve = [(e / 4, error(solve(10 ** (e / 4)))) for e in range(-40, 1)]
    return alpha, error(solve(alpha)), curve


def inverse_problem_fixture() -> str:
    """JSON text of the rod example's fixed inputs for the inverse-problem explorable."""
    blur, truth, data = inverse_problem_data()

    # Full 17-digit floats differ in the last digits between Windows and Linux libm, which made
    # `--check` fail on one platform. Twelve significant digits are far beyond what the figure
    # displays and are the same on both.
    def rounded(values: list[float]) -> list[float]:
        return [float(f"{value:.12g}") for value in values]

    blur = [rounded(row) for row in blur]
    truth, data = rounded(truth), rounded(data)
    payload = {
        # Written into the committed fixture as it is: the script that writes the file and
        # the function that computes the data. Changing it changes the fixture's bytes.
        "generated_by": "scripts/generate_lesson_figures.py (inverse_problem_data)",
        "n": INV_N,
        "blur_width": INV_WIDTH,
        "sigma": INV_SIGMA,
        "truth": truth,
        "data": data,
        "blur": blur,
    }
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n"


def _inverse_problem_alpha_svg() -> str:
    alpha, err, curve = inverse_problem_curve()
    px = _scale(-10.0, 0.0, 64, 416)
    py = _scale(-2.0, 2.0, 252, 52)
    parts = _open(
        "正則化の強さ α ごとの誤差",
        (
            "40点の観測から初期温度を復元したときの、真値との相対誤差です。"
            f"α=1e-10 では誤差{curve[0][1]:.1f}、残差が雑音の大きさに等しくなるα={alpha:.2e}で"
            f"誤差{err:.3f}、α=1 では{curve[-1][1]:.2f}です。縦軸と横軸は対数です。"
        ),
        360,
    )
    parts.append(f'<path d="M64 52V252H416" fill="none" stroke="{GRID}"/>')
    for e in (-10, -7, -4, -1):
        parts.append(_text(px(e), 272, f"1e{e}", "tick", "middle"))
    for e, label in ((-2, "0.01"), (-1, "0.1"), (0, "1"), (1, "10"), (2, "100")):
        parts.append(_text(56, py(e) + 5, label, "tick", "end"))
    parts.append(_text(416, 236, "α", "tick", "end"))
    parts.append(_text(70, 62, "相対誤差", "tick"))
    parts.append(_polyline([(px(e), py(math.log10(v))) for e, v in curve], LINE, 3))
    cx, cy = px(math.log10(alpha)), py(math.log10(err))
    parts.append(f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="6" fill="{UPDATE}"/>')
    parts.append(_text(20, 306, f"橙の点：残差が雑音の大きさに等しい α={alpha:.2e}"))
    parts.append(_text(20, 330, f"そのときの誤差 {err:.3f}", "note"))
    parts.append(_text(20, 354, "α=0（正則化なし）の誤差は 4.75e4（図の外）"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


FIGURES: dict[str, Callable[[], str]] = {
    "inverse-problem-alpha.svg": _inverse_problem_alpha_svg,
}
# Inputs of the inverse-problem explorable, keyed by the path from the repository root. Python
# owns the example; the TS math only imports it.
EXTRA_OUTPUTS: dict[str, Callable[[], str]] = {
    "site/src/features/explorable/math/inverseProblem.fixture.json": inverse_problem_fixture,
}
