"""Large smooth minimisation (content/concepts/high-dimensional-smooth-unconstrained.md): deblurring
a 1000-point signal with an edge-preserving smooth penalty. Gradient costs O(n log n) (FFT), the
Hessian is dense. numpy and scipy are imported inside the functions so the other figures keep
generating without the optional "scenes" extra.
"""

from __future__ import annotations

import functools
import math
from collections.abc import Callable
from typing import Any

from ._svg import GRID, LINE, MUTED, POINT, UPDATE, _open, _polyline, _scale, _text

PA007_N = 1000
PA007_LAMBDA = 0.05
PA007_DELTA = 0.05
PA007_TOLERANCE = 1e-6
PA007_SEED = 0
PA007_WINDOW = (180, 240)  # the first step of the signal sits at position 200


@functools.cache
def _pa007_problem() -> dict[str, Any]:
    import numpy as np

    n = PA007_N
    rng = np.random.default_rng(PA007_SEED)
    x_true = np.zeros(n)
    x_true[200:450], x_true[450:700], x_true[700:850] = 1.0, 2.0, 0.5
    dist = np.minimum(np.arange(n), n - np.arange(n))
    kernel = np.exp(-(dist**2) / (2 * 4.0**2))
    kernel /= kernel.sum()
    spectrum = np.fft.rfft(kernel)

    def blur(x: Any) -> Any:
        return np.fft.irfft(spectrum * np.fft.rfft(x), n)

    def blur_t(r: Any) -> Any:
        return np.fft.irfft(np.conj(spectrum) * np.fft.rfft(r), n)

    b = blur(x_true) + 0.01 * rng.standard_normal(n)

    def f_and_grad(x: Any) -> tuple[float, Any]:
        r = blur(x) - b
        d = np.roll(x, -1) - x
        root = np.sqrt(1 + (d / PA007_DELTA) ** 2)
        value = 0.5 * r @ r + PA007_LAMBDA * PA007_DELTA**2 * np.sum(root - 1)
        p = PA007_LAMBDA * d / root
        return float(value), blur_t(r) + np.roll(p, 1) - p

    return {"x_true": x_true, "b": b, "f_and_grad": f_and_grad, "x0": np.zeros(n)}


@functools.cache
def pa007_runs() -> dict[str, dict[str, Any]]:
    """Gradient descent (step 1/L), CG and L-BFGS-B (m=10), each stopped at max|g| <= 1e-6."""
    import numpy as np
    from scipy.optimize import minimize

    problem = _pa007_problem()
    f_and_grad = problem["f_and_grad"]
    x0 = problem["x0"]
    lipschitz = 1 + 4 * PA007_LAMBDA
    runs: dict[str, dict[str, Any]] = {}

    x = x0.copy()
    history: list[float] = []
    while True:
        value, gradient = f_and_grad(x)
        history.append(float(np.abs(gradient).max()))
        if history[-1] <= PA007_TOLERANCE:
            break
        x = x - gradient / lipschitz
    runs["GD"] = {"x": x, "f": value, "iterations": len(history) - 1, "history": history}

    for name, method, options in (
        ("CG", "CG", {}),
        ("L-BFGS", "L-BFGS-B", {"ftol": 0.0, "maxcor": 10}),
    ):
        calls: list[float] = []

        def counted(point: Any, calls: list[float] = calls) -> tuple[float, Any]:
            value, gradient = f_and_grad(point)
            calls.append(float(np.abs(gradient).max()))
            return value, gradient

        res = minimize(
            counted,
            x0,
            jac=True,
            method=method,
            options={"gtol": PA007_TOLERANCE, "maxiter": 100000, **options},
        )
        runs[name] = {"x": res.x, "f": float(res.fun), "iterations": int(res.nit), "history": calls}
    return runs


def pa007_milestones(history: list[float]) -> list[tuple[int, int]]:
    """Return first evaluation at or below each decade, rather than raw gradient values."""
    milestones = []
    for exponent in range(0, -7, -1):
        threshold = 10.0**exponent
        for evaluation, value in enumerate(history, start=1):
            if value <= threshold:
                milestones.append((evaluation, exponent))
                break
    return milestones


def _pa007_decade(value: int) -> str:
    superscript = str.maketrans("-0123456789", "⁻⁰¹²³⁴⁵⁶⁷⁸⁹")
    return "10" + str(value).translate(superscript)


def _pa007_deblur_svg() -> str:
    import numpy as np

    problem = _pa007_problem()
    runs = pa007_runs()
    x_true, b = problem["x_true"], problem["b"]
    x_star = runs["L-BFGS"]["x"]
    norm = float(np.linalg.norm(x_true))
    err_b = float(np.linalg.norm(b - x_true)) / norm
    err_x = float(np.linalg.norm(x_star - x_true)) / norm
    counts = {name: len(run["history"]) for name, run in runs.items()}
    parts = _open(
        "復元の精度と、収束の速さ",
        (
            "ぼかして雑音を足した1000点の測定から信号を復元する例。"
            f"復元した信号の誤差は{err_x:.1%}で、ぼけた測定そのものの誤差は{err_b:.1%}。"
            f"勾配の最大成分が1e-6以下になるまでの勾配の評価回数は、"
            f"勾配降下法が{counts['GD']}回、共役勾配法が{counts['CG']}回、"
            f"L-BFGS法が{counts['L-BFGS']}回。"
            "収束の線は各桁の基準以下に初めてなった評価回数を結び、評価ごとの軌跡は示さない。"
        ),
        654,
    )
    left, right = 56, 416
    px = _scale(PA007_WINDOW[0], PA007_WINDOW[1], left, right)
    py = _scale(-0.3, 1.3, 190, 70)
    parts.append(f'<path d="M{left} 70V190H{right}" fill="none" stroke="{GRID}"/>')
    for value in (0, 1):
        parts.append(_text(left - 8, py(value) + 5, f"{value}", "tick", "end"))
    for value in (180, 210, 240):
        parts.append(_text(px(value), 212, f"{value}", "tick", "middle"))
    parts.append(_text(20, 56, "階段の立ち上がり（位置 180〜240）", "title"))
    indices = list(range(PA007_WINDOW[0], PA007_WINDOW[1] + 1))
    for series, color, width in (
        (b, GRID, 1.2),
        (x_true, LINE, 2.0),
        (x_star, UPDATE, 2.0),
    ):
        parts.append(_polyline([(px(i), py(float(series[i]))) for i in indices], color, width))
    parts.append(_text(20, 238, f"灰：測定 b（全体の誤差 {err_b:.1%}）", "note"))
    parts.append(_text(20, 260, "緑：元の信号", "note"))
    parts.append(_text(20, 282, f"橙：復元 x*（全体の誤差 {err_x:.1%}）", "note"))

    parts.append(_text(20, 316, "勾配の最大成分と評価回数（両対数）", "title"))
    top, bottom, plot_left = 332, 468, 70
    qx = _scale(0, 4, plot_left, right)  # log10 of evaluations, 1 .. 10^4
    qy = _scale(-6.4, 0.6, bottom, top)  # log10 of max|g|
    parts.append(f'<path d="M{plot_left} {top}V{bottom}H{right}" fill="none" stroke="{GRID}"/>')
    for exponent in range(0, 5):
        label = "1" if exponent == 0 else _pa007_decade(exponent)
        parts.append(_text(qx(exponent), bottom + 22, label, "tick", "middle"))
    for exponent in (-6, -3, 0):
        parts.append(_text(plot_left - 6, qy(exponent) + 5, _pa007_decade(exponent), "tick", "end"))
    stop = qy(math.log10(PA007_TOLERANCE))
    parts.append(
        f'<path d="M{plot_left} {stop:.1f}H{right}" fill="none" '
        f'stroke="{GRID}" stroke-width="1.5"/>'
    )
    for name, color in (("GD", MUTED), ("CG", POINT), ("L-BFGS", UPDATE)):
        history = runs[name]["history"]
        points = [
            (qx(math.log10(evaluation)), qy(exponent))
            for evaluation, exponent in pa007_milestones(history)
        ]
        parts.append(_polyline(points, color, 2.0))
    parts.append(_text(right, bottom + 46, "勾配の評価回数", "", "end"))
    for row, (_name, color, label) in enumerate(
        (
            ("GD", MUTED, f"勾配降下法（一歩 1/L）：{counts['GD']}回"),
            ("CG", POINT, f"共役勾配法：{counts['CG']}回"),
            ("L-BFGS", UPDATE, f"L-BFGS法（履歴 m=10）：{counts['L-BFGS']}回"),
        )
    ):
        y = 568 + 22 * row
        parts.append(f'<path d="M20 {y - 5}H44" fill="none" stroke="{color}" stroke-width="3"/>')
        parts.append(_text(54, y, label))
    parts.append(_text(20, 636, "線：各桁の基準以下になった最初の評価", "note"))
    parts.append(_text(20, 542, "灰の横線：停止の基準 10⁻⁶", "note"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


FIGURES: dict[str, Callable[[], str]] = {
    "large-smooth-deblur.svg": _pa007_deblur_svg,
}
