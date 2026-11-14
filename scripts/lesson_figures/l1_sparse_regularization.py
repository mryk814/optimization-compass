"""L1 sparse regularization (content/concepts/l1-sparse-regularization.md): twelve rental listings,
four candidate features, rent in units of 10,000 yen.
"""

from __future__ import annotations

import math
from collections.abc import Callable

from ._svg import GRID, LINE, MUTED, POINT, UPDATE, _open, _polyline, _scale, _text

RENT_FEATURES = ("面積", "築年数", "徒歩", "階数")
RENT_COLUMNS = (
    (20, 36, 19, 27, 45, 57, 35, 44, 25, 37, 39, 39),
    (8, 14, 25, 3, 17, 9, 28, 2, 3, 28, 7, 22),
    (2, 7, 3, 15, 11, 6, 10, 11, 7, 12, 12, 4),
    (3, 4, 7, 2, 4, 4, 1, 4, 1, 2, 8, 8),
)
RENT_Y = (6.0, 6.3, 4.6, 3.9, 6.8, 11.1, 4.1, 9.9, 5.4, 3.8, 7.3, 6.0)
RENT_COLORS = (LINE, POINT, UPDATE, MUTED)


def _rent_design() -> tuple[list[list[float]], list[float]]:
    """Standardized feature columns (mean 0, standard deviation 1) and centered rent."""
    columns = []
    for column in RENT_COLUMNS:
        mean = sum(column) / len(column)
        spread = math.sqrt(sum((v - mean) ** 2 for v in column) / len(column))
        columns.append([(v - mean) / spread for v in column])
    mean_y = sum(RENT_Y) / len(RENT_Y)
    return columns, [y - mean_y for y in RENT_Y]


def _soft_threshold(value: float, threshold: float) -> float:
    return math.copysign(max(abs(value) - threshold, 0.0), value)


def lasso_solution(lam: float, sweeps: int = 400) -> list[float]:
    """Coordinate descent for 1/2 |Ax-b|^2 + lam |x|_1 on the standardized rent data."""
    columns, y = _rent_design()
    coef = [0.0] * len(columns)
    residual = list(y)
    for _ in range(sweeps):
        for j, column in enumerate(columns):
            norm = sum(v * v for v in column)
            rho = sum(v * r for v, r in zip(column, residual, strict=True)) + norm * coef[j]
            new = _soft_threshold(rho, lam) / norm
            residual = [r + v * (coef[j] - new) for v, r in zip(column, residual, strict=True)]
            coef[j] = new
    return coef


def ridge_solution(lam: float) -> list[float]:
    """Solve (A^T A + lam I) x = A^T b by Gaussian elimination."""
    columns, y = _rent_design()
    size = len(columns)
    rows = [
        [sum(u * v for u, v in zip(columns[i], columns[j], strict=True)) for j in range(size)]
        + [sum(u * v for u, v in zip(columns[i], y, strict=True))]
        for i in range(size)
    ]
    for i in range(size):
        rows[i][i] += lam
    for i in range(size):
        pivot = rows[i][i]
        rows[i] = [v / pivot for v in rows[i]]
        for k in range(size):
            if k != i:
                factor = rows[k][i]
                rows[k] = [a - factor * c for a, c in zip(rows[k], rows[i], strict=True)]
    return [rows[i][size] for i in range(size)]


def lasso_lambda_max() -> float:
    columns, y = _rent_design()
    return max(abs(sum(u * v for u, v in zip(column, y, strict=True))) for column in columns)


def lasso_zero_points() -> list[float]:
    """The lambda at which each coefficient first becomes exactly 0 (bisection)."""
    points = []
    for j in range(len(RENT_COLUMNS)):
        low, high = 0.0, lasso_lambda_max()
        for _ in range(40):
            middle = (low + high) / 2
            if lasso_solution(middle, 120)[j] == 0.0:
                high = middle
            else:
                low = middle
        points.append(high)
    return points


def _l1_path_svg() -> str:
    top_lam = 20.0
    zero_points = lasso_zero_points()
    steps = [top_lam * index / 80 for index in range(81)]
    lasso = [lasso_solution(lam, 200) for lam in steps]
    ridge = [ridge_solution(lam) for lam in steps]
    lam_max = lasso_lambda_max()
    parts = _open(
        "λ を上げたときの係数",
        (
            "標準化した4つの特徴量について、λを0から20まで上げたときの係数の変化です。"
            f"上のパネルのL1では係数がちょうど0になり、階数は{zero_points[3]:.1f}、"
            f"徒歩は{zero_points[2]:.1f}、築年数は{zero_points[1]:.1f}、"
            f"面積は{zero_points[0]:.1f}で0になります。"
            "下のパネルのL2（ridge）では、どの係数も0にならず小さくなるだけです。"
        ),
        580,
    )
    px = _scale(0.0, top_lam, 64, 420)
    for index, (label, path) in enumerate(
        (("L1（lasso）の係数", lasso), ("L2（ridge）の係数", ridge))
    ):
        top = 56 + index * 208
        py = _scale(-1.5, 2.0, top + 150, top + 20)
        parts.append(_text(20, top + 2, label))
        parts.append(f'<path d="M64 {top + 20}V{top + 150}H420" fill="none" stroke="{GRID}"/>')
        parts.append(f'<path d="M64 {py(0.0):.2f}H420" stroke="{GRID}" stroke-width="1"/>')
        for value in (-1.0, 0.0, 1.0, 2.0):
            parts.append(_text(56, py(value) + 5, f"{value:g}", "tick", "end"))
        for lam in (0, 10, 20):
            parts.append(_text(px(lam), top + 170, f"{lam}", "tick", "middle"))
        parts.append(_text(420, top + 190, "λ", "tick", "end"))
        # Draw the last feature first so a coefficient resting on 0 shows the first feature's color.
        for j in reversed(range(len(RENT_COLORS))):
            points = [(px(lam), py(coef[j])) for lam, coef in zip(steps, path, strict=True)]
            parts.append(_polyline(points, RENT_COLORS[j], 3))
        if index == 0:
            for j, color in enumerate(RENT_COLORS):
                parts.append(
                    f'<circle cx="{px(zero_points[j]):.2f}" cy="{py(0.0):.2f}" r="6" '
                    f'fill="#f7f8f3" stroke="{color}" stroke-width="3"/>'
                )
    legend_top = 484
    for j, (name, color) in enumerate(zip(RENT_FEATURES, RENT_COLORS, strict=True)):
        x = 20 + (j % 2) * 200
        y = legend_top + (j // 2) * 24
        parts.append(f'<path d="M{x} {y - 5}h28" stroke="{color}" stroke-width="3"/>')
        parts.append(_text(x + 36, y, name))
    parts.append(_text(20, legend_top + 52, "白抜きの丸：係数がちょうど0になる λ", "note"))
    parts.append(_text(20, legend_top + 76, f"λ が {lam_max:.1f} 以上なら係数はすべて0", "note"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


FIGURES: dict[str, Callable[[], str]] = {
    "l1-sparse-regularization-path.svg": _l1_path_svg,
}
