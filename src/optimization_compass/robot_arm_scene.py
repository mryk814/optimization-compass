"""Reproducible spatial arm trajectory optimization for the teaching scene.

The editable authority is this model; arm.json is its generated projection.
Coordinates are metres, joint angles radians, and time seconds. This is a
kinematic planning example, not a torque-controlled robot simulation.
"""

from __future__ import annotations

from typing import Any, TypedDict, cast

import numpy as np
from numpy.typing import NDArray
from scipy.optimize import minimize

FloatArray = NDArray[np.float64]


class TrajectorySolution(TypedDict):
    knots: FloatArray
    metrics: dict[str, Any]


LINK_LENGTHS = np.array([0.9, 0.75])
BASE = np.array([0.0, 0.0, 0.35])
OBSTACLES = ((np.array([1.1, 0.0, 0.45]), 0.30),)
LINK_RADIUS = 0.045
SAFETY_MARGIN = 0.025
VELOCITY_LIMIT = 1.5
DURATION = 4.0
START = np.array([-0.85, 0.25, -0.45])
GOAL = np.array([0.85, 0.25, -0.45])
LOWER = np.array([-1.4, -0.2, -1.9])
UPPER = np.array([1.4, 1.5, 0.4])


def forward_kinematics(joints: FloatArray) -> FloatArray:
    """Return base, elbow and tip for a yaw / shoulder pitch / elbow pitch arm."""
    q = np.asarray(joints, dtype=float)
    yaw, pitch, elbow = np.moveaxis(q, -1, 0)
    first = (
        np.stack(
            [np.cos(yaw) * np.cos(pitch), np.sin(yaw) * np.cos(pitch), np.sin(pitch)],
            axis=-1,
        )
        * LINK_LENGTHS[0]
    )
    second = (
        np.stack(
            [
                np.cos(yaw) * np.cos(pitch + elbow),
                np.sin(yaw) * np.cos(pitch + elbow),
                np.sin(pitch + elbow),
            ],
            axis=-1,
        )
        * LINK_LENGTHS[1]
    )
    base = np.broadcast_to(BASE, first.shape)
    return np.stack([base, base + first, base + first + second], axis=-2)


def capsule_clearances(points: FloatArray) -> FloatArray:
    """Exact capsule-to-sphere surface separation for every link and obstacle."""
    a, b = points[..., :-1, :], points[..., 1:, :]
    segment = b - a
    values = []
    for center, radius in OBSTACLES:
        fraction = np.clip(
            np.sum((center - a) * segment, axis=-1) / np.sum(segment**2, axis=-1),
            0.0,
            1.0,
        )
        closest = a + fraction[..., None] * segment
        values.append(np.linalg.norm(closest - center, axis=-1) - radius - LINK_RADIUS)
    return np.stack(values, axis=-1)


def interpolate_joints(knots: FloatArray, samples_per_segment: int) -> FloatArray:
    """Piecewise-linear joints; FK must be evaluated after interpolation."""
    alpha = np.arange(samples_per_segment) / samples_per_segment
    between = knots[:-1, None, :] * (1 - alpha[None, :, None])
    between += knots[1:, None, :] * alpha[None, :, None]
    return np.concatenate([between.reshape(-1, 3), knots[-1:]])


def validate_trajectory(knots: FloatArray, samples_per_segment: int = 100) -> dict[str, Any]:
    """Recheck dense interpolation independently of the optimizer's constraints."""
    dense = interpolate_joints(knots, samples_per_segment)
    minimum = float(capsule_clearances(forward_kinematics(dense)).min())
    velocity = float(np.abs(np.diff(knots, axis=0)).max() / (DURATION / (len(knots) - 1)))
    endpoint_error = float(
        max(
            np.linalg.norm(forward_kinematics(knots[0])[-1] - forward_kinematics(START)[-1]),
            np.linalg.norm(forward_kinematics(knots[-1])[-1] - forward_kinematics(GOAL)[-1]),
        )
    )
    bounds_ok = bool(np.all(dense >= LOWER - 1e-8) and np.all(dense <= UPPER + 1e-8))
    return {
        "minClearance": minimum,
        "maxVelocity": velocity,
        "endpointError": endpoint_error,
        "jointBoundsSatisfied": bounds_ok,
        "denseValidationSamples": len(dense),
        "valid": minimum >= SAFETY_MARGIN - 1e-7
        and velocity <= VELOCITY_LIMIT + 1e-7
        and endpoint_error < 1e-9
        and bounds_ok,
    }


def solve_trajectory(smoothness_weight: float, knot_count: int = 19) -> TrajectorySolution:
    """SLSQP minimizes tip travel and joint acceleration subject to hard bounds.

    End configurations are fixed rather than penalized. Five collision samples
    per segment and a 5 mm buffer are used during solving; a separate 100-sample
    check determines whether a result can be exported as successful.
    """
    dt = DURATION / (knot_count - 1)
    phase = np.linspace(0, 1, knot_count)
    seed = START + (GOAL - START) * phase[:, None]
    seed[:, 1] += 0.8 * np.sin(np.pi * phase)

    def unpack(x: FloatArray) -> FloatArray:
        return np.vstack([START, x.reshape(-1, 3), GOAL])

    def costs(knots: FloatArray) -> tuple[float, float]:
        tip = forward_kinematics(knots)[:, -1, :]
        travel = float(np.linalg.norm(np.diff(tip, axis=0), axis=1).sum())
        acceleration = np.diff(knots, n=2, axis=0) / dt**2
        roughness = float(np.sum(acceleration**2) * dt)
        return travel, roughness

    def objective(x: FloatArray) -> float:
        travel, roughness = costs(unpack(x))
        return travel + smoothness_weight * roughness

    def constraints(x: FloatArray) -> FloatArray:
        knots = unpack(x)
        clearance = capsule_clearances(forward_kinematics(interpolate_joints(knots, 5)))
        speed = np.diff(knots, axis=0) / dt
        return np.concatenate(
            [
                (clearance - SAFETY_MARGIN - 0.005).ravel(),
                (VELOCITY_LIMIT - speed).ravel(),
                (VELOCITY_LIMIT + speed).ravel(),
            ]
        )

    # scipy-stubs types old-style constraint callbacks as scalar-returning,
    # although SLSQP accepts vector inequalities. Keep the actual vector model.
    collision_and_speed = cast(Any, [{"type": "ineq", "fun": constraints}])
    result = minimize(
        objective,
        seed[1:-1].ravel(),
        method="SLSQP",
        bounds=list(zip(LOWER, UPPER, strict=True)) * (knot_count - 2),
        constraints=collision_and_speed,
        options={"ftol": 1e-9, "maxiter": 500},
    )
    knots = unpack(result.x)
    metrics = validate_trajectory(knots)
    travel, roughness = costs(knots)
    metrics.update(
        objective=float(result.fun),
        tipTravel=travel,
        integratedSquaredAcceleration=roughness,
        smoothnessWeight=smoothness_weight,
        solverSuccess=bool(result.success),
        solverMessage=str(result.message),
        solverIterations=int(result.nit),
    )
    if not result.success or not metrics["valid"]:
        raise RuntimeError(f"Arm solve failed independent validation: {metrics}")
    return {"knots": knots, "metrics": metrics}


def generate_scene() -> dict[str, Any]:
    """Build two genuinely solved objective variants with identical constraints."""
    variants = []
    for identifier, label, weight in (
        ("short", "手先の移動距離を重視", 0.003),
        ("smooth", "関節の滑らかさを重視", 0.5),
    ):
        solution = solve_trajectory(weight)
        dense = interpolate_joints(solution["knots"], 5)
        points = forward_kinematics(dense)
        clearance = capsule_clearances(points).min(axis=(1, 2))
        frames = [
            {
                "time": round(i * DURATION / (len(dense) - 1), 8),
                "joints": joints.tolist(),
                "points": pose.tolist(),
                "clearance": float(distance),
            }
            for i, (joints, pose, distance) in enumerate(zip(dense, points, clearance, strict=True))
        ]
        variants.append(
            {"id": identifier, "label": label, "frames": frames, "metrics": solution["metrics"]}
        )
    return {
        "obstacles": [
            {"center": center.tolist(), "radius": radius} for center, radius in OBSTACLES
        ],
        "linkLengths": LINK_LENGTHS.tolist(),
        "linkRadius": LINK_RADIUS,
        "base": BASE.tolist(),
        "duration": DURATION,
        "safetyMargin": SAFETY_MARGIN,
        "velocityLimit": VELOCITY_LIMIT,
        "variants": variants,
        "sources": [
            {
                "title": "MIT Robotic Manipulation — Motion Planning",
                "url": "https://manipulation.mit.edu/trajectories.html",
            },
            {
                "title": "SciPy minimize(method='SLSQP')",
                "url": "https://docs.scipy.org/doc/scipy/reference/optimize.minimize-slsqp.html",
            },
        ],
        "model": (
            "3自由度（旋回・肩・肘）の空間アーム。全リンクをカプセル、障害物を球で表し、"
            "固定した始終端姿勢・関節角・速度・離隔を制約にSLSQPで軌道を計算。"
        ),
        "limitations": [
            "運動学的な軌道計画。質量・トルク・重力・駆動系・接触を含む動力学は扱わない。",
            "非凸問題の局所解。初期軌道や重みで解が変わり、大域最適性は保証しない。",
            "関節角を区分線形に補間。節点間を100分割して全リンク離隔を再検証するが、連続時間の衝突なし証明ではない。",
            "滑らかさ指標は節点の二階差分による近似。区分線形補間の節点では速度が切り替わり、連続加速度の保証はない。",
            "同じ始終端・障害物・時間・制約・初期軌道で目的の重みだけを変更。自己衝突や実機安全性の保証は含まない。",
        ],
    }
