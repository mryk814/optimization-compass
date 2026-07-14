from __future__ import annotations

from collections.abc import Sequence


def objective_spec(family: str) -> dict[str, object]:
    if family == "quadratic":
        return {
            "family": "quadratic",
            "dimensions": 2,
            "generator_id": "objective.quadratic.v1",
            "domain": {"x": [-4.0, 4.0], "y": [-4.0, 4.0]},
            "display_range": {"x": [-4.0, 4.0], "y": [-4.0, 4.0], "z": [0.0, 1600.0]},
            "display_expression": "f(x, y) = 100x² + y²",
            "optimum": {"point": [0.0, 0.0], "value": 0.0},
            "weights": [100.0, 1.0],
        }
    if family == "rosenbrock":
        return {
            "family": "rosenbrock",
            "dimensions": 2,
            "generator_id": "objective.rosenbrock.v1",
            "domain": {"x": [-2.0, 2.0], "y": [-1.0, 3.0]},
            "display_range": {"x": [-2.0, 2.0], "y": [-1.0, 3.0], "z": [0.0, 2500.0]},
            "display_expression": "f(x, y) = 100(y - x²)² + (1 - x)²",
            "optimum": {"point": [1.0, 1.0], "value": 0.0},
        }
    raise ValueError(f"unsupported educational objective family: {family}")


def objective_value(family: str, point: Sequence[float]) -> float:
    x, y = point
    if family == "quadratic":
        return 100.0 * x * x + y * y
    if family == "rosenbrock":
        return 100.0 * (y - x * x) ** 2 + (1.0 - x) ** 2
    raise ValueError(f"unsupported educational objective family: {family}")


def objective_gradient(family: str, point: Sequence[float]) -> list[float]:
    x, y = point
    if family == "quadratic":
        return [200.0 * x, 2.0 * y]
    if family == "rosenbrock":
        return [
            -400.0 * x * (y - x * x) - 2.0 * (1.0 - x),
            200.0 * (y - x * x),
        ]
    raise ValueError(f"unsupported educational objective family: {family}")
