from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Literal, cast

from optimization_compass.problem_registry import RuntimeProblem, get_runtime_problem
from optimization_compass.trace_models import (
    AlgorithmTrace,
    DecisionState,
    TerminalStatus,
    TraceBundle,
    TraceFrame,
    TraceMetric,
    TracePoint,
    TraceVector,
)

GradientMethod = Literal["gradient_descent", "momentum", "adam"]

_EVENT_LABELS = {
    "initialize": ("初期化", "Initialize"),
    "order": ("単体を並べ替え", "Order simplex"),
    "reflect": ("反射", "Reflect"),
    "expand": ("膨張", "Expand"),
    "outside_contract": ("外側収縮", "Outside contract"),
    "inside_contract": ("内側収縮", "Inside contract"),
    "shrink": ("縮小", "Shrink"),
    "update": ("更新", "Update"),
    "stop": ("停止", "Stop"),
}


def generate_nelder_mead_trace(
    *,
    dataset_version: str,
    problem_instance_id: str = "OBJECTIVE_QUADRATIC_2D",
    initial_point: Sequence[float] | None = None,
    budget: int = 80,
    trace_id: str | None = None,
    scenario_id: str | None = None,
) -> AlgorithmTrace:
    if budget < 4:
        raise ValueError("Nelder–Mead budget must allow the initial simplex and one trial")
    problem = get_runtime_problem(problem_instance_id)
    objective = problem.trace_objective()
    objective_family = problem.definition.mathematical_family
    initial = list(
        initial_point or _initial_point(problem, "simplex_default", fallback=[-2.5, 2.0])
    )
    scale = 0.8
    simplex = [initial[:], [initial[0] + scale, initial[1]], [initial[0], initial[1] + scale]]
    values = [_scalar_value(problem, point) for point in simplex]
    frames: list[TraceFrame] = []
    evaluations = 3
    _append_nm_frame(
        frames,
        0,
        0,
        evaluations,
        "initialize",
        "not_applicable",
        simplex,
        values,
        None,
        objective_family,
    )
    iteration = 0
    frame_index = 1
    alpha, gamma, rho, sigma = 1.0, 2.0, 0.5, 0.5
    while evaluations < budget:
        iteration += 1
        order = sorted(range(3), key=lambda index: values[index])
        simplex = [simplex[index] for index in order]
        values = [values[index] for index in order]
        _append_nm_frame(
            frames,
            frame_index,
            iteration,
            evaluations,
            "order",
            "not_applicable",
            simplex,
            values,
            None,
            objective_family,
        )
        frame_index += 1
        if _simplex_size(simplex) < 1e-4:
            break
        centroid = [(simplex[0][axis] + simplex[1][axis]) / 2.0 for axis in range(2)]
        worst = simplex[2]
        reflected = [centroid[axis] + alpha * (centroid[axis] - worst[axis]) for axis in range(2)]
        reflected_value = _scalar_value(problem, reflected)
        evaluations += 1
        if evaluations >= budget:
            simplex[2], values[2] = reflected, reflected_value
            _append_nm_frame(
                frames,
                frame_index,
                iteration,
                evaluations,
                "reflect",
                "accepted",
                simplex,
                values,
                (reflected, reflected_value),
                objective_family,
            )
            frame_index += 1
            break
        if reflected_value < values[0]:
            expanded = [
                centroid[axis] + gamma * (reflected[axis] - centroid[axis]) for axis in range(2)
            ]
            expanded_value = _scalar_value(problem, expanded)
            evaluations += 1
            if expanded_value < reflected_value:
                simplex[2], values[2] = expanded, expanded_value
                event, candidate, candidate_value = "expand", expanded, expanded_value
            else:
                simplex[2], values[2] = reflected, reflected_value
                event, candidate, candidate_value = "reflect", reflected, reflected_value
            decision = "accepted"
        elif reflected_value < values[1]:
            simplex[2], values[2] = reflected, reflected_value
            event, candidate, candidate_value, decision = (
                "reflect",
                reflected,
                reflected_value,
                "accepted",
            )
        elif reflected_value < values[2]:
            contracted = [
                centroid[axis] + rho * (reflected[axis] - centroid[axis]) for axis in range(2)
            ]
            contracted_value = _scalar_value(problem, contracted)
            evaluations += 1
            if contracted_value <= reflected_value:
                simplex[2], values[2] = contracted, contracted_value
                event, candidate, candidate_value, decision = (
                    "outside_contract",
                    contracted,
                    contracted_value,
                    "accepted",
                )
            else:
                event, candidate, candidate_value, decision = (
                    "shrink",
                    contracted,
                    contracted_value,
                    "rejected",
                )
        else:
            contracted = [
                centroid[axis] - rho * (centroid[axis] - worst[axis]) for axis in range(2)
            ]
            contracted_value = _scalar_value(problem, contracted)
            evaluations += 1
            if contracted_value < values[2]:
                simplex[2], values[2] = contracted, contracted_value
                event, candidate, candidate_value, decision = (
                    "inside_contract",
                    contracted,
                    contracted_value,
                    "accepted",
                )
            else:
                event, candidate, candidate_value, decision = (
                    "shrink",
                    contracted,
                    contracted_value,
                    "rejected",
                )
        if event == "shrink":
            for index in (1, 2):
                if evaluations >= budget:
                    break
                simplex[index] = [
                    simplex[0][axis] + sigma * (simplex[index][axis] - simplex[0][axis])
                    for axis in range(2)
                ]
                values[index] = _scalar_value(problem, simplex[index])
                evaluations += 1
        candidate_pair = (
            None if candidate is None or candidate_value is None else (candidate, candidate_value)
        )
        _append_nm_frame(
            frames,
            frame_index,
            iteration,
            evaluations,
            event,
            cast(DecisionState, decision),
            simplex,
            values,
            candidate_pair,
            objective_family,
            operation_origin=centroid,
        )
        frame_index += 1
        if _simplex_size(simplex) < 1e-4:
            break
    terminal_status: TerminalStatus = (
        "converged" if _simplex_size(simplex) < 1e-4 else "budget_exhausted"
    )
    _append_nm_frame(
        frames,
        frame_index,
        iteration,
        evaluations,
        "stop",
        "not_applicable",
        simplex,
        values,
        None,
        objective_family,
    )
    return AlgorithmTrace(
        contract_version="1.0.0",
        dataset_version=dataset_version,
        data_version="1.0.0",
        trace_id=trace_id or f"nelder-mead-{objective_family}",
        method_id="M_NELDER_MEAD",
        profile_id="PROFILE_NELDER_MEAD_2D",
        objective_id=problem_instance_id,
        scenario_id=scenario_id or f"SCENARIO_NM_{objective_family.upper()}",
        generator_id="educational.nelder_mead.v1",
        generator_version="1.0.0",
        implementation_mapping_status="not_applicable",
        implementation_id=None,
        objective=objective,
        preset={"preset_id": "VIEW_NELDER_MEAD_THEATER"},
        parameters={
            "alpha": alpha,
            "gamma": gamma,
            "rho": rho,
            "sigma": sigma,
            "initial_scale": scale,
        },
        initial_state={
            "point": initial,
            "simplex": [
                initial[:],
                [initial[0] + scale, initial[1]],
                [initial[0], initial[1] + scale],
            ],
        },
        seed={"status": "not_applicable", "value": None},
        evaluation_budget=budget,
        stopping={"max_oracle_evaluations": budget, "simplex_tolerance": 1e-4},
        environment={"runtime": "educational", "version": "1.0.0"},
        fairness_statement="同じ初期simplex・目的関数・評価予算で再生する教育用Traceです。単独再生で優劣を断定しません。",
        frames=frames,
        terminal_status=terminal_status,
        terminal_summary_ja="Nelder–MeadのTraceを終了しました。初期simplexと評価予算で挙動は変わります。",
        terminal_summary_en=(
            "The Nelder–Mead educational trace finished; behavior depends on the initial "
            "simplex and budget."
        ),
        source_ids=["S001", "S002"],
    )


def generate_gradient_trace(
    method: GradientMethod,
    *,
    dataset_version: str,
    problem_instance_id: str = "OBJECTIVE_QUADRATIC_2D",
    initial_point: Sequence[float] | None = None,
    budget: int = 40,
    parameters: dict[str, float] | None = None,
    trace_id: str | None = None,
    scenario_id: str | None = None,
) -> AlgorithmTrace:
    if budget < 2:
        raise ValueError("gradient trace budget must be at least two")
    defaults: dict[GradientMethod, dict[str, float]] = {
        "gradient_descent": {"learning_rate": 0.003},
        "momentum": {"learning_rate": 0.003, "momentum": 0.9},
        "adam": {"learning_rate": 0.03, "beta1": 0.9, "beta2": 0.999, "epsilon": 1e-8},
    }
    params = {**defaults[method], **(parameters or {})}
    problem = get_runtime_problem(problem_instance_id)
    objective = problem.trace_objective()
    objective_family = problem.definition.mathematical_family
    point = list(
        initial_point or _initial_point(problem, "first_order_default", fallback=[-1.6, 1.6])
    )
    frames: list[TraceFrame] = []
    value = _scalar_value(problem, point)
    _append_gradient_frame(
        frames, 0, 0, 1, "initialize", point, [0.0, 0.0], value, method, objective_family
    )
    velocity = [0.0, 0.0]
    first_moment = [0.0, 0.0]
    second_moment = [0.0, 0.0]
    terminal_status: TerminalStatus = "budget_exhausted"
    for iteration in range(1, budget):
        previous_point, previous_value = point[:], value
        gradient = problem.objective_gradient(point)
        if method == "gradient_descent":
            movement = [-params["learning_rate"] * value_component for value_component in gradient]
        elif method == "momentum":
            velocity = [
                params["momentum"] * velocity[index] - params["learning_rate"] * gradient[index]
                for index in range(2)
            ]
            movement = velocity[:]
        else:
            first_moment = [
                params["beta1"] * first_moment[index] + (1.0 - params["beta1"]) * gradient[index]
                for index in range(2)
            ]
            second_moment = [
                params["beta2"] * second_moment[index]
                + (1.0 - params["beta2"]) * gradient[index] ** 2
                for index in range(2)
            ]
            corrected_first = [
                component / (1.0 - params["beta1"] ** iteration) for component in first_moment
            ]
            corrected_second = [
                component / (1.0 - params["beta2"] ** iteration) for component in second_moment
            ]
            movement = [
                -params["learning_rate"]
                * corrected_first[index]
                / (corrected_second[index] ** 0.5 + params["epsilon"])
                for index in range(2)
            ]
        point = [point[index] + movement[index] for index in range(2)]
        value = _scalar_value(problem, point)
        if (
            not all(math.isfinite(item) for item in (*gradient, *movement, *point, value))
            or value > 1e12
        ):
            point, value = previous_point, previous_value
            terminal_status = "diverged"
            break
        _append_gradient_frame(
            frames,
            iteration,
            iteration,
            iteration + 1,
            "update",
            point,
            movement,
            value,
            method,
            objective_family,
            gradient,
        )
        if value < 1e-6:
            terminal_status = "converged"
            break
    _append_gradient_frame(
        frames,
        len(frames),
        len(frames) - 1,
        len(frames),
        "stop",
        point,
        [0.0, 0.0],
        value,
        method,
        objective_family,
    )
    method_id = {
        "gradient_descent": "M_GRADIENT_DESCENT",
        "momentum": "M_MOMENTUM_SGD",
        "adam": "M_ADAM",
    }[method]
    profile_id = {
        "gradient_descent": "PROFILE_GRADIENT_DESCENT_2D",
        "momentum": "PROFILE_MOMENTUM_2D",
        "adam": "PROFILE_ADAM_2D",
    }[method]
    return AlgorithmTrace(
        contract_version="1.0.0",
        dataset_version=dataset_version,
        data_version="1.0.0",
        trace_id=trace_id or f"{method}-{objective_family}",
        method_id=method_id,
        profile_id=profile_id,
        objective_id=problem_instance_id,
        scenario_id=scenario_id
        or {
            "gradient_descent": "SCENARIO_GD",
            "momentum": "SCENARIO_MOMENTUM",
            "adam": "SCENARIO_ADAM",
        }[method]
        + f"_{objective_family.upper()}",
        generator_id=f"educational.{method}.v1",
        generator_version="1.0.0",
        implementation_mapping_status="not_applicable",
        implementation_id=None,
        objective=objective,
        preset={"preset_id": "VIEW_FIRST_ORDER_COMPARISON"},
        parameters={key: cast(object, value) for key, value in params.items()},
        initial_state={
            "point": list(
                initial_point
                or _initial_point(problem, "first_order_default", fallback=[-1.6, 1.6])
            )
        },
        seed={"status": "not_applicable", "value": None},
        evaluation_budget=budget,
        stopping={"max_oracle_evaluations": budget, "objective_tolerance": 1e-6},
        environment={"runtime": "educational", "version": "1.0.0"},
        fairness_statement="同じ目的関数・初期点・評価予算で同期する比較用Traceです。初期値とパラメータ依存性を明示します。",
        frames=frames,
        terminal_status=terminal_status,
        terminal_summary_ja="更新則のTraceを終了しました。これは一般的な優劣ランキングではありません。",
        terminal_summary_en=(
            "The update trace finished; this is not a universal performance ranking."
        ),
        source_ids=["S001", "S002"],
    )


def generate_gradient_bundle(
    *,
    dataset_version: str,
    problem_instance_id: str = "OBJECTIVE_QUADRATIC_2D",
    budget: int = 40,
    preset: Literal["valley", "divergence"] = "valley",
) -> TraceBundle:
    problem = get_runtime_problem(problem_instance_id)
    problem_family = problem.definition.mathematical_family
    initial = _initial_point(problem, "first_order_default", fallback=[-1.6, 1.6])
    methods: tuple[GradientMethod, ...] = ("gradient_descent", "momentum", "adam")
    parameters: dict[GradientMethod, dict[str, float]] = (
        {
            "gradient_descent": {"learning_rate": 0.012},
            "momentum": {"learning_rate": 0.008, "momentum": 0.9},
            "adam": {"learning_rate": 0.03, "beta1": 0.9, "beta2": 0.999, "epsilon": 1e-8},
        }
        if preset == "divergence"
        else {method: {} for method in methods}
    )
    suffix = "" if preset == "valley" else "-divergence"
    traces = [
        generate_gradient_trace(
            method,
            problem_instance_id=problem_instance_id,
            initial_point=initial,
            budget=budget,
            parameters=parameters[method],
            trace_id=f"{method}-{problem_family}{suffix}",
            scenario_id=(
                f"SCENARIO_{method.upper()}_{problem_family.upper()}"
                + ("" if preset == "valley" else "_DIVERGENCE")
            ),
            dataset_version=dataset_version,
        )
        for method in methods
    ]
    first = traces[0]
    return TraceBundle(
        contract_version="1.0.0",
        bundle_id=(
            f"gradient-{problem_family}"
            if preset == "valley"
            else f"gradient-{problem_family}-divergence"
        ),
        comparison_id=(
            "COMPARE_GRADIENT_FAMILY" if preset == "valley" else "COMPARE_GRADIENT_DIVERGENCE"
        ),
        dataset_version=first.dataset_version,
        data_version=first.data_version,
        objective_id=first.objective_id,
        objective=first.objective,
        initial_state=first.initial_state,
        seed=first.seed,
        evaluation_budget=budget,
        stopping=first.stopping,
        environment=first.environment,
        fairness_statement=first.fairness_statement,
        member_traces=traces,
        synchronization="oracle_evaluations",
    )


def _initial_point(
    problem: RuntimeProblem, candidate_id: str, *, fallback: list[float]
) -> list[float]:
    for candidate in problem.instance.initialization_candidates:
        if candidate.get("candidate_id") == candidate_id:
            point = candidate.get("point")
            if isinstance(point, list) and all(isinstance(value, int | float) for value in point):
                return [float(value) for value in point]
    return fallback


def _scalar_value(problem: RuntimeProblem, point: Sequence[float]) -> float:
    value = problem.objective_value(point)
    if isinstance(value, tuple):
        raise ValueError(
            f"trace generator requires a scalar objective: {problem.instance.problem_instance_id}"
        )
    return value


def _append_nm_frame(
    frames: list[TraceFrame],
    frame_index: int,
    iteration: int,
    evaluations: int,
    event: str,
    decision: DecisionState,
    simplex: list[list[float]],
    values: list[float],
    candidate: tuple[list[float], float] | None,
    family: str,
    operation_origin: list[float] | None = None,
) -> None:
    labels = _EVENT_LABELS[event]
    points = [
        TracePoint(
            point_id=f"vertex-{index}",
            role="simplex-vertex",
            coordinates=list(point),
            value=value,
            label_ja=f"頂点{index + 1}",
            label_en=f"Vertex {index + 1}",
        )
        for index, (point, value) in enumerate(zip(simplex, values, strict=True))
    ]
    ranked = sorted(zip(simplex, values, strict=True), key=lambda item: item[1])
    centroid = operation_origin or [
        (ranked[0][0][axis] + ranked[1][0][axis]) / 2.0 for axis in range(2)
    ]
    points.append(
        TracePoint(
            point_id="centroid",
            role="centroid",
            coordinates=centroid,
            value=None,
            label_ja="最良2点の重心",
            label_en="Centroid of best two",
        )
    )
    vectors = []
    if candidate and candidate[0] is not None:
        points.append(
            TracePoint(
                point_id="candidate",
                role="trial-point",
                coordinates=list(candidate[0]),
                value=candidate[1],
                label_ja="候補点",
                label_en="Candidate",
            )
        )
        vectors.append(
            TraceVector(
                vector_id="candidate-movement",
                role="movement",
                origin=centroid,
                components=[candidate[0][axis] - centroid[axis] for axis in range(2)],
                label_ja="重心から候補点への操作",
                label_en="Operation from centroid to candidate",
            )
        )
    frames.append(
        TraceFrame(
            frame_index=frame_index,
            iteration=iteration,
            oracle_evaluations=evaluations,
            elapsed_steps=frame_index,
            elapsed_time_ms=float(frame_index * 120),
            event_type=event,
            decision=decision,
            explanation_key=f"trace.nelder-mead.{event}",
            event_label_ja=labels[0],
            event_label_en=labels[1],
            keyframe=event in {"initialize", "order", "shrink", "stop"},
            points=points,
            vectors=vectors,
            metrics=[
                TraceMetric(
                    metric_id="objective",
                    label_ja="目的関数値",
                    label_en="Objective value",
                    value=min(values),
                    unit=None,
                )
            ],
            payload={
                "values": {f"vertex-{index}": value for index, value in enumerate(values)},
                "simplex": [list(point) for point in simplex],
            },
        )
    )


def _append_gradient_frame(
    frames: list[TraceFrame],
    frame_index: int,
    iteration: int,
    evaluations: int,
    event: str,
    point: Sequence[float],
    movement: Sequence[float],
    value: float,
    method: str,
    family: str,
    gradient: Sequence[float] | None = None,
) -> None:
    labels = _EVENT_LABELS[event]
    frames.append(
        TraceFrame(
            frame_index=frame_index,
            iteration=iteration,
            oracle_evaluations=evaluations,
            elapsed_steps=frame_index,
            elapsed_time_ms=float(frame_index * 120),
            event_type=event,
            decision="not_applicable" if event in {"initialize", "stop"} else "accepted",
            explanation_key=f"trace.{method}.{event}",
            event_label_ja=labels[0],
            event_label_en=labels[1],
            keyframe=event in {"initialize", "stop"},
            points=[
                TracePoint(
                    point_id="current",
                    role="iterate",
                    coordinates=list(point),
                    value=value,
                    label_ja="現在位置",
                    label_en="Current point",
                )
            ],
            vectors=[
                TraceVector(
                    vector_id="update",
                    role="movement",
                    origin=[point[index] - movement[index] for index in range(2)],
                    components=list(movement),
                    label_ja="更新ベクトル",
                    label_en="Update vector",
                ),
                *(
                    [
                        TraceVector(
                            vector_id="gradient",
                            role="gradient",
                            origin=[point[index] - movement[index] for index in range(2)],
                            components=list(gradient),
                            label_ja="現在の勾配",
                            label_en="Current gradient",
                        )
                    ]
                    if gradient is not None
                    else []
                ),
            ],
            metrics=[
                TraceMetric(
                    metric_id="objective",
                    label_ja="目的関数値",
                    label_en="Objective value",
                    value=value,
                    unit=None,
                )
            ],
            payload={
                "method": method,
                "objective_family": family,
                "gradient": list(gradient or [0.0, 0.0]),
            },
        )
    )


def _simplex_size(simplex: list[list[float]]) -> float:
    return max(
        max(abs(simplex[index][axis] - simplex[0][axis]) for axis in range(2)) for index in (1, 2)
    )
