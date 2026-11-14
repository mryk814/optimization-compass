"""MIQP (content/concepts/mixed-integer-quadratic-program.md): five assets, at most three held."""

from __future__ import annotations

import itertools
from collections.abc import Callable, Sequence

from ._svg import GRID, LINE, POINT, UPDATE, _open, _scale, _text

MIQP_NAMES = "ABCDE"
MIQP_VOL = (10.0, 12.0, 15.0, 20.0, 25.0)  # standard deviations in percent
MIQP_CORR = (
    (1.0, 0.5, 0.3, 0.1, 0.0),
    (0.5, 1.0, 0.4, 0.2, 0.1),
    (0.3, 0.4, 1.0, 0.3, 0.2),
    (0.1, 0.2, 0.3, 1.0, 0.4),
    (0.0, 0.1, 0.2, 0.4, 1.0),
)
MIQP_RETURN = (4.0, 5.0, 6.0, 8.0, 9.0)  # expected returns in percent
MIQP_CAP = (0.6, 0.5, 0.5, 0.4, 0.4)  # per-asset upper limit on the weight
MIQP_LOT = 0.1  # minimum weight of a held asset
MIQP_TARGET = 6.0  # required expected return
MIQP_MAX_HELD = 3
MIQP_FEE = 5.0  # fixed cost per held asset, on the same scale as the variance
MIQP_TOL = 1e-9


def _miqp_covariance() -> list[list[float]]:
    return [[MIQP_VOL[i] * MIQP_VOL[j] * MIQP_CORR[i][j] for j in range(5)] for i in range(5)]


def _solve_consistent(matrix: list[list[float]], rhs: list[float]) -> list[float] | None:
    """Gaussian elimination that tolerates redundant rows and rejects inconsistent ones."""
    rows, cols = len(matrix), len(matrix[0])
    a = [[*row, rhs[i]] for i, row in enumerate(matrix)]
    pivots: list[int] = []
    r = 0
    for col in range(cols):
        pivot = max(range(r, rows), key=lambda i: abs(a[i][col]), default=None)
        if pivot is None or abs(a[pivot][col]) < 1e-12:
            continue
        a[r], a[pivot] = a[pivot], a[r]
        a[r] = [v / a[r][col] for v in a[r]]
        for i in range(rows):
            if i != r:
                factor = a[i][col]
                a[i] = [v - factor * w for v, w in zip(a[i], a[r], strict=True)]
        pivots.append(col)
        r += 1
    if any(abs(a[i][cols]) > 1e-9 for i in range(r, rows)):
        return None
    solution = [0.0] * cols
    for i, col in enumerate(pivots):
        solution[col] = a[i][cols]
    return solution


def _miqp_small_qp(
    indices: Sequence[int],
    lower: float,
    upper: Sequence[float],
    linear: Sequence[float],
) -> tuple[float, list[float]] | None:
    """Exact minimum of x'Sx + linear'x with sum x = 1, mu'x >= target and lower <= x <= upper.

    The problem is convex, so any KKT point is a global minimum. With at most five variables the
    KKT points are found by trying every choice of "at lower / at upper / free" per variable and
    "return constraint active / inactive". Returns None when no feasible point exists.
    """
    sigma = _miqp_covariance()
    size = len(indices)
    q = [[sigma[i][j] for j in indices] for i in indices]
    c = [linear[i] for i in indices]
    mu = [MIQP_RETURN[i] for i in indices]
    ub = [upper[i] for i in indices]
    best: tuple[float, list[float]] | None = None
    for status in itertools.product((0, 1, 2), repeat=size):  # 0 free, 1 at lower, 2 at upper
        for active in (False, True):
            x = [lower if s == 1 else ub[j] if s == 2 else 0.0 for j, s in enumerate(status)]
            free = [j for j, s in enumerate(status) if s == 0]
            fixed = [j for j, s in enumerate(status) if s != 0]
            count = len(free) + 1 + (1 if active else 0)
            matrix, rhs = [], []
            for j in free:
                row = [2 * q[j][k] for k in free] + [-1.0] + ([-mu[j]] if active else [])
                matrix.append(row)
                rhs.append(-c[j] - sum(2 * q[j][k] * x[k] for k in fixed))
            matrix.append([1.0] * len(free) + [0.0] * (count - len(free)))
            rhs.append(1.0 - sum(x[k] for k in fixed))
            if active:
                matrix.append([mu[j] for j in free] + [0.0, 0.0])
                rhs.append(MIQP_TARGET - sum(mu[k] * x[k] for k in fixed))
            solved = _solve_consistent(matrix, rhs)
            if solved is None:
                continue
            for position, j in enumerate(free):
                x[j] = solved[position]
            lam = solved[len(free)]
            nu = solved[len(free) + 1] if active else 0.0
            if any(x[j] < lower - MIQP_TOL or x[j] > ub[j] + MIQP_TOL for j in range(size)):
                continue
            if abs(sum(x) - 1.0) > 1e-7 or sum(m * v for m, v in zip(mu, x, strict=True)) < (
                MIQP_TARGET - 1e-7
            ):
                continue
            if nu < -MIQP_TOL:
                continue
            gradient = [
                2 * sum(q[j][k] * x[k] for k in range(size)) + c[j] - lam - nu * mu[j]
                for j in range(size)
            ]
            if any(status[j] == 1 and gradient[j] < -1e-7 for j in range(size)):
                continue
            if any(status[j] == 2 and gradient[j] > 1e-7 for j in range(size)):
                continue
            value = sum(x[j] * q[j][k] * x[k] for j in range(size) for k in range(size))
            value += sum(c[j] * x[j] for j in range(size))
            if best is None or value < best[0]:
                best = (value, list(x))
    return best


def miqp_enumerate(
    upper: Sequence[float] = MIQP_CAP,
) -> list[tuple[float, tuple[int, ...], list[float]]]:
    """Subsets of at most MIQP_MAX_HELD assets as (variance + fee, subset, weights), best first."""
    found = []
    for size in range(1, MIQP_MAX_HELD + 1):
        for subset in itertools.combinations(range(5), size):
            result = _miqp_small_qp(subset, MIQP_LOT, upper, [0.0] * 5)
            if result is not None:
                found.append((result[0] + MIQP_FEE * size, subset, result[1]))
    return sorted(found, key=lambda item: item[0])


def miqp_relaxation(big_m: Sequence[float]) -> tuple[float, list[float]]:
    """Continuous relaxation of the big-M model: z_i = x_i / M_i leaves cost fee * x_i / M_i."""
    upper = [min(cap, m) for cap, m in zip(MIQP_CAP, big_m, strict=True)]
    linear = [MIQP_FEE / m for m in big_m]
    result = _miqp_small_qp(range(5), 0.0, upper, linear)
    assert result is not None
    return result


def miqp_big_m_rows() -> list[tuple[str, float, float, tuple[int, ...]]]:
    """(label, relaxation bound, integer optimum, optimal subset) for each choice of M."""
    rows = []
    for label, big_m in (
        ("M ＝ 各銘柄の上限", MIQP_CAP),
        ("M ＝ 1", (1.0,) * 5),
        ("M ＝ 10", (10.0,) * 5),
        ("M ＝ 100", (100.0,) * 5),
        ("M ＝ 0.4（上限より小さい別の問題）", (0.4,) * 5),
    ):
        upper = [min(cap, m) for cap, m in zip(MIQP_CAP, big_m, strict=True)]
        best = miqp_enumerate(upper)[0]
        rows.append((label, miqp_relaxation(big_m)[0], best[0], best[1]))
    return rows


def _miqp_big_m_svg() -> str:
    rows = miqp_big_m_rows()
    parts = _open(
        "M の大きさと下界",
        (
            "5銘柄から3銘柄以内を選ぶポートフォリオで、"
            "big-M の M を変えたときの連続緩和の下界と整数の最適値です。"
            + "".join(
                f"{label.split('（')[0]}では下界{bound:.2f}、最適値{best:.2f}。"
                for label, bound, best, _ in rows
            )
        ),
        524,
    )
    px = _scale(88.0, 130.0, 40, 420)
    axis_y = 60 + len(rows) * 68
    for tick in (90, 100, 110, 120, 130):
        parts.append(
            f'<path d="M{px(tick):.2f} {axis_y - 6}V{axis_y + 6}" '
            f'stroke="{POINT}" stroke-width="2"/>'
        )
        parts.append(_text(px(tick), axis_y + 22, f"{tick}", "tick", "middle"))
    parts.append(f'<path d="M40 {axis_y}H420" stroke="{POINT}" stroke-width="2"/>')
    parts.append(_text(420, axis_y + 46, "目的値（分散＋固定費）", "tick", "end"))
    for index, (label, bound, best, _) in enumerate(rows):
        top = 66 + index * 68
        line_y = top + 24
        parts.append(_text(20, top + 6, label))
        for tick in (90, 100, 110, 120, 130):
            parts.append(
                f'<path d="M{px(tick):.2f} {line_y - 9}V{line_y + 9}" '
                f'stroke="{GRID}" stroke-width="1"/>'
            )
        parts.append(
            f'<path d="M{px(bound):.2f} {line_y}H{px(best):.2f}" '
            f'stroke="{POINT}" stroke-width="3"/>'
        )
        parts.append(
            f'<circle cx="{px(bound):.2f}" cy="{line_y}" r="7" fill="{UPDATE}"/>'
            f'<circle cx="{px(best):.2f}" cy="{line_y}" r="7" fill="{LINE}"/>'
        )
        parts.append(_text(min(max(px(bound), 62), 398), line_y + 28, f"{bound:.2f}", "", "middle"))
        parts.append(_text(min(max(px(best), 62), 398), line_y + 28, f"{best:.2f}", "", "middle"))
    legend_y = axis_y + 76
    parts.append(f'<circle cx="28" cy="{legend_y - 5}" r="7" fill="{UPDATE}"/>')
    parts.append(_text(44, legend_y, "橙：連続緩和の下界"))
    parts.append(f'<circle cx="28" cy="{legend_y + 23}" r="7" fill="{LINE}"/>')
    parts.append(_text(44, legend_y + 28, "緑：整数の最適値（列挙で確認）"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


FIGURES: dict[str, Callable[[], str]] = {
    "miqp-big-m-bound.svg": _miqp_big_m_svg,
}
