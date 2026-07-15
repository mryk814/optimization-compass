from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from functools import lru_cache
from importlib.resources import files
from typing import cast

from optimization_compass.problem_instances import (
    ProblemDefinition,
    ProblemInstance,
    ProblemSuiteSeed,
)

ObjectiveValue = float | tuple[float, ...]
Evaluator = Callable[[ProblemInstance, Sequence[float]], ObjectiveValue]
Gradient = Callable[[ProblemInstance, Sequence[float]], list[float]]


@dataclass(frozen=True)
class RuntimeProblem:
    definition: ProblemDefinition
    instance: ProblemInstance
    evaluate: Evaluator
    gradient: Gradient | None

    def objective_value(self, point: Sequence[float]) -> ObjectiveValue:
        _require_dimension(self.instance, point)
        return self.evaluate(self.instance, point)

    def objective_gradient(self, point: Sequence[float]) -> list[float]:
        _require_dimension(self.instance, point)
        if self.gradient is None:
            raise ValueError(
                f"problem instance has no gradient oracle: {self.instance.problem_instance_id}"
            )
        return self.gradient(self.instance, point)

    def trace_objective(self) -> dict[str, object]:
        display_range = self.instance.display.get("range")
        expression = self.instance.display.get("expression")
        if not isinstance(display_range, dict) or not isinstance(expression, str):
            raise ValueError(
                f"trace problem lacks display metadata: {self.instance.problem_instance_id}"
            )
        payload: dict[str, object] = {
            "problem_definition_id": self.definition.problem_definition_id,
            "problem_instance_id": self.instance.problem_instance_id,
            "family": self.definition.mathematical_family,
            "direction": self.definition.objective_direction,
            "dimensions": self.instance.dimension,
            "generator_id": self.instance.registry_key,
            "domain": self.instance.bounds,
            "display_range": display_range,
            "display_expression": expression,
            "known_reference_status": self.instance.known_reference_status,
        }
        reference = self.instance.known_reference
        if reference is not None and "point" in reference and "value" in reference:
            payload["optimum"] = {"point": reference["point"], "value": reference["value"]}
        return payload


@lru_cache(maxsize=1)
def load_problem_suite() -> ProblemSuiteSeed:
    resource = files("optimization_compass").joinpath("resources/problem-suite.json")
    suite = ProblemSuiteSeed.model_validate_json(resource.read_text(encoding="utf-8"))
    seed_keys = {item.registry_key for item in suite.instances}
    registry_keys = set(_REGISTRY)
    if seed_keys != registry_keys:
        missing = sorted(seed_keys - registry_keys)
        orphaned = sorted(registry_keys - seed_keys)
        raise ValueError(f"problem registry mismatch: missing={missing}, orphaned={orphaned}")
    return suite


def get_runtime_problem(problem_instance_id: str) -> RuntimeProblem:
    suite = load_problem_suite()
    definitions = {item.problem_definition_id: item for item in suite.definitions}
    instance = next(
        (item for item in suite.instances if item.problem_instance_id == problem_instance_id), None
    )
    if instance is None:
        raise ValueError(f"unknown problem instance: {problem_instance_id}")
    evaluator, gradient = _REGISTRY[instance.registry_key]
    return RuntimeProblem(
        definition=definitions[instance.problem_definition_id],
        instance=instance,
        evaluate=evaluator,
        gradient=gradient,
    )


def _require_dimension(instance: ProblemInstance, point: Sequence[float]) -> None:
    if len(point) != instance.dimension:
        raise ValueError(
            f"{instance.problem_instance_id} expects dimension {instance.dimension}, "
            f"got {len(point)}"
        )


def _weights(instance: ProblemInstance) -> list[float]:
    values = instance.parameters.get("weights")
    if not isinstance(values, list) or not all(isinstance(value, int | float) for value in values):
        raise ValueError(f"invalid weights for {instance.problem_instance_id}")
    return [float(value) for value in values]


def _quadratic(instance: ProblemInstance, point: Sequence[float]) -> float:
    return sum(
        weight * value * value for weight, value in zip(_weights(instance), point, strict=True)
    )


def _quadratic_gradient(instance: ProblemInstance, point: Sequence[float]) -> list[float]:
    return [2.0 * weight * value for weight, value in zip(_weights(instance), point, strict=True)]


def _rosenbrock(_instance: ProblemInstance, point: Sequence[float]) -> float:
    x, y = point
    return 100.0 * (y - x * x) ** 2 + (1.0 - x) ** 2


def _rosenbrock_gradient(_instance: ProblemInstance, point: Sequence[float]) -> list[float]:
    x, y = point
    return [-400.0 * x * (y - x * x) - 2.0 * (1.0 - x), 200.0 * (y - x * x)]


def _rastrigin(_instance: ProblemInstance, point: Sequence[float]) -> float:
    return 10.0 * len(point) + sum(
        value * value - 10.0 * math.cos(2.0 * math.pi * value) for value in point
    )


def _absolute_ridge(_instance: ProblemInstance, point: Sequence[float]) -> float:
    x, y = point
    return abs(x) + 2.0 * abs(y) + 0.25 * abs(x - y)


def _wavy_black_box(_instance: ProblemInstance, point: Sequence[float]) -> float:
    (x,) = point
    return 0.16 * (x - 1.7) ** 2 + 0.45 * math.sin(2.2 * x) + 0.12 * math.sin(5.3 * x)


def _knapsack(instance: ProblemInstance, point: Sequence[float]) -> float:
    items = instance.parameters.get("items")
    capacity = instance.parameters.get("capacity")
    if not isinstance(items, list) or not isinstance(capacity, int | float):
        raise ValueError("invalid knapsack data")
    selected = [int(value) for value in point]
    if any(value not in {0, 1} for value in selected):
        raise ValueError("knapsack decisions must be binary")
    rows = [cast(dict[str, object], item) for item in items]
    weight = sum(_number(row["weight"]) * value for row, value in zip(rows, selected, strict=True))
    if weight > float(capacity):
        return float("-inf")
    return sum(_number(row["value"]) * value for row, value in zip(rows, selected, strict=True))


def _assignment(instance: ProblemInstance, point: Sequence[float]) -> float:
    costs = instance.parameters.get("cost_matrix")
    if not isinstance(costs, list):
        raise ValueError("invalid assignment data")
    assignment = [int(value) for value in point]
    if sorted(assignment) != list(range(instance.dimension)):
        raise ValueError("assignment must be a permutation")
    rows = [cast(list[float], row) for row in costs]
    return sum(float(rows[row][column]) for row, column in enumerate(assignment))


def _number(value: object) -> float:
    if not isinstance(value, int | float):
        raise ValueError("problem registry expected a numeric value")
    return float(value)


def _constrained_disk(_instance: ProblemInstance, point: Sequence[float]) -> float:
    x, y = point
    return x * x + y * y


def _biobjective(_instance: ProblemInstance, point: Sequence[float]) -> tuple[float, float]:
    x, y = point
    return (x * x + y * y, (x - 2.0) ** 2 + (y - 2.0) ** 2)


_REGISTRY: dict[str, tuple[Evaluator, Gradient | None]] = {
    "problem.quadratic.isotropic.v1": (_quadratic, _quadratic_gradient),
    "problem.quadratic.ill_conditioned.v1": (_quadratic, _quadratic_gradient),
    "problem.rosenbrock.v1": (_rosenbrock, _rosenbrock_gradient),
    "problem.rastrigin.v1": (_rastrigin, None),
    "problem.absolute_ridge.v1": (_absolute_ridge, None),
    "problem.wavy_black_box.v1": (_wavy_black_box, None),
    "problem.knapsack.binary.v1": (_knapsack, None),
    "problem.assignment.linear.v1": (_assignment, None),
    "problem.constrained_disk.v1": (_constrained_disk, None),
    "problem.biobjective_quadratic.v1": (_biobjective, None),
}
