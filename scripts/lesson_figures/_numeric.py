"""Linear-algebra helpers shared by several lessons, in pure Python (no numeric extra)."""

from __future__ import annotations

Matrix3 = list[list[float]]


def _det3(a: Matrix3) -> float:
    return (
        a[0][0] * (a[1][1] * a[2][2] - a[1][2] * a[2][1])
        - a[0][1] * (a[1][0] * a[2][2] - a[1][2] * a[2][0])
        + a[0][2] * (a[1][0] * a[2][1] - a[1][1] * a[2][0])
    )


def _solve_linear(matrix: list[list[float]], rhs: list[float]) -> list[float]:
    size = len(rhs)
    a = [[*row, rhs[i]] for i, row in enumerate(matrix)]
    for col in range(size):
        pivot = max(range(col, size), key=lambda r: abs(a[r][col]))
        a[col], a[pivot] = a[pivot], a[col]
        for r in range(col + 1, size):
            factor = a[r][col] / a[col][col]
            for c in range(col, size + 1):
                a[r][c] -= factor * a[col][c]
    solution = [0.0] * size
    for r in range(size - 1, -1, -1):
        tail = sum(a[r][c] * solution[c] for c in range(r + 1, size))
        solution[r] = (a[r][size] - tail) / a[r][r]
    return solution
