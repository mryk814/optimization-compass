"""Steps from the inner solver (content/concepts/inner-solver-error.md): the same tank with q fixed
at 0.000501, solved by solve_ivp's default RK45 at rtol = 1e-3. INNER_E is the tool's sum of squares
minus the model's (Radau, rtol = 1e-10), in units of 1e-5, at a = 0.00031, 0.000311, ..., 0.00049;
INNER_RUNS is the number of right-hand-side evaluations (sol.nfev) and how many consecutive samples
share it. Recorded with SciPy 1.18.1; the tests rerun SciPy and check both.
"""

from __future__ import annotations

from collections.abc import Callable

from ._svg import GRID, LINE, POINT, UPDATE, VIOLATION, _open, _polyline, _scale, _text

INNER_Q = 0.000501
INNER_A0, INNER_DA = 0.00031, 0.000001
INNER_E = (
    -24.425,
    -23.426,
    -22.44,
    -21.47,
    -20.515,
    -19.579,
    -18.655,
    -17.743,
    -16.845,
    -15.961,
    -15.092,
    -14.235,
    -13.386,
    -12.542,
    -11.703,
    -10.864,
    -10.012,
    -9.127,
    -8.156,
    -13.429,
    -13.158,
    -12.898,
    -12.648,
    -12.413,
    -12.193,
    -11.987,
    -11.796,
    -11.62,
    -11.462,
    -11.32,
    -11.195,
    -11.089,
    -11.002,
    -10.936,
    -10.892,
    -10.87,
    -10.872,
    -10.899,
    -10.951,
    -11.031,
    -11.139,
    -11.278,
    -11.449,
    -11.384,
    -11.071,
    -10.759,
    -10.45,
    -10.144,
    -9.84,
    -9.538,
    -9.24,
    -8.946,
    -8.654,
    -8.365,
    -8.079,
    -7.797,
    -7.518,
    -7.242,
    -6.969,
    -6.7,
    -6.435,
    -6.174,
    -5.916,
    -5.662,
    -5.41,
    -5.162,
    -4.917,
    -4.675,
    -4.438,
    -4.205,
    -3.975,
    -3.749,
    -3.527,
    -3.308,
    -3.092,
    -2.881,
    -2.673,
    -2.468,
    -2.267,
    -2.07,
    -1.876,
    -1.685,
    -1.498,
    -1.313,
    -1.132,
    -0.954,
    -0.779,
    -0.606,
    -0.437,
    -0.27,
    -0.104,
    0.058,
    0.22,
    0.38,
    0.538,
    0.696,
    0.855,
    1.013,
    1.173,
    1.335,
    1.5,
    1.669,
    1.843,
    2.024,
    2.213,
    2.412,
    2.625,
    2.85,
    3.015,
    3.179,
    3.341,
    3.502,
    3.661,
    3.819,
    3.975,
    4.129,
    4.282,
    4.434,
    4.586,
    4.736,
    4.884,
    5.031,
    5.176,
    5.32,
    5.463,
    5.604,
    5.744,
    5.883,
    6.022,
    6.157,
    6.291,
    6.423,
    6.553,
    6.683,
    6.811,
    6.939,
    7.065,
    5.946,
    6.03,
    6.113,
    6.196,
    6.279,
    6.361,
    6.443,
    6.527,
    6.611,
    6.696,
    6.783,
    6.873,
    6.966,
    7.063,
    7.166,
    7.265,
    7.328,
    7.389,
    7.449,
    7.509,
    7.567,
    7.625,
    7.682,
    7.74,
    7.797,
    7.853,
    7.909,
    7.964,
    8.018,
    8.073,
    8.127,
    8.18,
    8.232,
    8.286,
    8.339,
    8.393,
    8.448,
    8.502,
    8.553,
    8.604,
    8.654,
    8.704,
    8.752,
    8.802,
)
INNER_RUNS = ((50, 19), (62, 24), (68, 64), (74, 30), (80, 15), (86, 29))
# Where the count changes, found by bisection: (a, sum-of-squares jump). Two of the five
# changes make the result jump; at the other three it only bends.
INNER_JUMPS = ((0.0003288929884, -6.79e-5), (0.0004466880265, -1.23e-5))


def inner_samples() -> list[tuple[float, float, int]]:
    counts = [count for count, length in INNER_RUNS for _ in range(length)]
    return [
        (INNER_A0 + i * INNER_DA, error, count)
        for i, (error, count) in enumerate(zip(INNER_E, counts, strict=True))
    ]


def _inner_steps_svg() -> str:
    samples = inner_samples()
    parts = _open(
        "RK45 で解いた二乗和の、式からのずれ",
        (
            f"流入量 q を {INNER_Q} に固定し、流出口の面積 a を0.00031から0.00049まで動かす。"
            "縦軸は、solve_ivp の既定（RK45、rtol=1e-3）で解いた二乗和から、"
            "細かい許容誤差で解いた二乗和を引いた値（×10⁻⁵）。"
            "線は、右辺を計算した回数が同じ範囲ごとに切れている。回数は"
            + "・".join(str(count) for count, _ in INNER_RUNS)
            + "回と増える。"
            + "、".join(
                f"a={a * 1e4:.3f}×10⁻⁴ で {jump * 1e5:+.2f}×10⁻⁵".replace("-", "−")
                for a, jump in INNER_JUMPS
            )
            + "の段差がある。ほかの3か所では、線は折れるが跳ばない。"
            "答えの a=0.000401 は、回数68回の範囲の中にある。"
        ),
        394,
    )
    px = _scale(3.1, 4.9, 64, 410)
    py = _scale(-26.0, 10.0, 290, 70)
    parts.append(f'<path d="M64 70V290H410" fill="none" stroke="{GRID}"/>')
    parts.append(f'<path d="M64 {py(0):.1f}H410" stroke="{GRID}" stroke-dasharray="5 4"/>')
    for tick in (-20, -10, 0, 10):
        parts.append(_text(56, py(tick) + 5, f"{tick}".replace("-", "−"), "tick", "end"))
    for a_tick in (3.2, 3.6, 4.0, 4.4, 4.8):
        parts.append(_text(px(a_tick), 312, f"{a_tick:.1f}", "tick", "middle"))
    for jump_a, _ in INNER_JUMPS:
        x = px(jump_a * 1e4)
        parts.append(
            f'<path d="M{x:.1f} 70V290" stroke="{VIOLATION}" stroke-width="1.5" '
            'stroke-dasharray="3 3"/>'
        )
    start = 0
    for index, (count, length) in enumerate(INNER_RUNS):
        piece = samples[start : start + length]
        start += length
        color = LINE if count == 68 else POINT
        parts.append(
            _polyline([(px(a * 1e4), py(e)) for a, e, _ in piece], color, 3 if count == 68 else 2.5)
        )
        middle = piece[len(piece) // 2][0] * 1e4
        parts.append(_text(px(middle), 338 + 0 * index, str(count), "tick", "middle"))
    answer_x = px(4.01)
    parts.append(
        f'<path d="M{answer_x - 7:.1f} 298L{answer_x:.1f} 288L{answer_x + 7:.1f} 298Z" '
        f'fill="{UPDATE}"/>'
    )
    parts.append(_text(answer_x + 10, 284, "答え", "tick"))
    first, second = INNER_JUMPS
    parts.append(
        _text(px(first[0] * 1e4) + 6, 92, f"段差 {first[1] * 1e5:.2f}".replace("-", "−"), "tick")
    )
    parts.append(
        _text(
            px(second[0] * 1e4) - 6,
            py(-5),
            f"段差 {second[1] * 1e5:.2f}".replace("-", "−"),
            "tick",
            "end",
        )
    )
    parts.append(_text(20, 362, "目盛りの下の数：右辺を計算した回数。横軸 a（×10⁻⁴）", "tick"))
    parts.append(_text(20, 384, "縦軸 ずれ（×10⁻⁵）。q=0.000501、SciPy 1.18.1", "tick"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


FIGURES: dict[str, Callable[[], str]] = {
    "inner-solver-steps.svg": _inner_steps_svg,
}
