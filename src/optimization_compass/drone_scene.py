"""Offline receding-horizon optimization for an educational 3D point-mass drone.

The acceleration is constant within each interval. This is not a quadrotor
attitude/motor simulation, nor a reproduction of UZH's perception-aware MPC.
"""

from typing import Any

import numpy as np
from scipy.optimize import minimize

DT = 0.16
STEPS = 90
HORIZON = 16
BODY_RADIUS = 0.12
ACCELERATION_BOUND = 2.0
OBSTACLES = [(np.array([0.0, 0.0, 1.8]), 0.48)]


def reference_position(time: float) -> Any:
    """Smooth, time-indexed reference that deliberately crosses an obstacle."""
    s = np.clip(time / 12.0, 0.0, 1.0)
    progress = 3 * s**2 - 2 * s**3
    return np.array(
        [
            -3.0 + 6.0 * progress,
            0.45 * np.sin(2 * np.pi * progress),
            1.8 + 0.3 * np.sin(2 * np.pi * progress),
        ]
    )


def interval_clearance(position: Any, velocity: Any, acceleration: Any) -> float:
    """Exact polynomial minimum over [0, DT] for every sphere, minus body radius.

    Squared distance along p + vt + at²/2 is quartic; its derivative is cubic.
    Endpoints and all real stationary points exhaust its interval minima.
    """
    result = float("inf")
    for center, radius in OBSTACLES:
        d = position - center
        coefficients = [
            float(acceleration @ acceleration),
            float(3 * velocity @ acceleration),
            float(2 * (velocity @ velocity + d @ acceleration)),
            float(2 * d @ velocity),
        ]
        roots: Any = np.roots(np.trim_zeros(coefficients, "f")) if any(coefficients) else []
        times = [0.0, DT] + [
            float(r.real) for r in roots if abs(r.imag) < 1e-9 and 0 <= r.real <= DT
        ]
        result = min(
            result,
            *(
                float(np.linalg.norm(d + velocity * t + 0.5 * acceleration * t**2))
                - radius
                - BODY_RADIUS
                for t in times
            ),
        )
    return result


def simulate_variant(identifier: str, label: str, smooth_weight: float) -> dict[str, Any]:
    """Solve the finite-horizon nonlinear program, apply only u[0], then repeat."""
    n = HORIZON
    times = DT * np.arange(1, n + 1)
    # Condensed exact zero-order-hold double-integrator dynamics.
    pm = DT**2 * np.maximum(np.arange(n)[:, None] - np.arange(n)[None, :] + 0.5, 0)
    vm = DT * np.tril(np.ones((n, n)))
    delta = np.eye(n) - np.eye(n, k=-1)
    position = reference_position(0.0)
    velocity = np.zeros(3)
    previous = np.zeros(3)
    warm = np.zeros((n, 3))
    frames: list[dict[str, Any]] = []
    successes = 0
    iterations = 0
    continuous_min = float("inf")
    errors = []
    acceleration_norms = []
    input_changes = []

    for step in range(STEPS):
        time = step * DT
        base = position + times[:, None] * velocity
        target = np.array([reference_position(time + t) for t in times])
        target_velocity = np.array(
            [
                (reference_position(time + t + 1e-3) - reference_position(time + t - 1e-3)) / 2e-3
                for t in times
            ]
        )
        weights = np.ones((n, 1))
        weights[-1] = 3.0
        delta_offset = np.zeros((n, 3))
        delta_offset[0] = previous

        def objective(
            flat: Any,
            base: Any = base,
            target: Any = target,
            velocity: Any = velocity,
            target_velocity: Any = target_velocity,
            delta_offset: Any = delta_offset,
            weights: Any = weights,
        ) -> tuple[float, Any]:
            u = flat.reshape(n, 3)
            error = base + pm @ u - target
            v_error = velocity + vm @ u - target_velocity
            changes = delta @ u - delta_offset
            cost = np.sum(weights * error**2) + 0.12 * np.sum(v_error**2)
            cost += 0.025 * np.sum(u**2) + smooth_weight * np.sum(changes**2)
            gradient = 2 * pm.T @ (weights * error) + 0.24 * vm.T @ v_error
            gradient += 0.05 * u + 2 * smooth_weight * delta.T @ changes
            return float(cost), gradient.ravel()

        # Constrain endpoints and exact constant-acceleration midpoints. The
        # committed executed trajectory is additionally checked continuously.
        mm = pm.copy()
        mm[np.diag_indices(n)] -= 0.375 * DT**2
        mm -= 0.5 * DT * (vm - DT * np.eye(n))
        midpoint_base = position + (times - 0.5 * DT)[:, None] * velocity
        matrices = np.vstack([pm, mm])
        bases = np.vstack([base, midpoint_base])

        def obstacle_constraints(flat: Any, bases: Any = bases, matrices: Any = matrices) -> Any:
            predicted = bases + matrices @ flat.reshape(n, 3)
            return np.concatenate(
                [
                    np.sum((predicted - center) ** 2, axis=1) - (radius + BODY_RADIUS + 0.025) ** 2
                    for center, radius in OBSTACLES
                ]
            )

        def obstacle_jacobian(flat: Any, bases: Any = bases, matrices: Any = matrices) -> Any:
            predicted = bases + matrices @ flat.reshape(n, 3)
            return np.vstack(
                [
                    np.einsum("ij,ik->ijk", 2 * (predicted - center), matrices)
                    .transpose(0, 2, 1)
                    .reshape(2 * n, 3 * n)
                    for center, _ in OBSTACLES
                ]
            )

        solved = minimize(
            objective,
            warm.ravel(),
            jac=True,
            method="SLSQP",
            bounds=[(-ACCELERATION_BOUND, ACCELERATION_BOUND)] * (3 * n),
            constraints={"type": "ineq", "fun": obstacle_constraints, "jac": obstacle_jacobian},
            options={"ftol": 1e-8, "maxiter": 160},
        )
        if not solved.success or np.min(obstacle_constraints(solved.x)) < -1e-6:
            raise RuntimeError(f"MPC failed at {identifier}:{step}: {solved.message}")
        successes += 1
        iterations += solved.nit
        controls = solved.x.reshape(n, 3)
        acceleration = controls[0].copy()
        clearance = interval_clearance(position, velocity, acceleration)
        if clearance < 0:
            raise RuntimeError(f"Continuous executed interval intersects obstacle: {clearance}")
        continuous_min = min(continuous_min, clearance)
        error = float(np.linalg.norm(position - reference_position(time)))
        errors.append(error)
        acceleration_norms.append(float(np.linalg.norm(acceleration)))
        input_changes.append(float(np.linalg.norm(acceleration - previous)))
        frames.append(
            {
                "time": time,
                "position": position.tolist(),
                "velocity": velocity.tolist(),
                "acceleration": acceleration.tolist(),
                "prediction": np.vstack([position, base + pm @ controls]).tolist(),
                "trackingError": error,
                "clearance": clearance,
            }
        )
        position = position + DT * velocity + 0.5 * DT**2 * acceleration
        velocity = velocity + DT * acceleration
        previous = acceleration
        warm = np.vstack([controls[1:], controls[-1]])

    frames.append(
        {
            "time": STEPS * DT,
            "position": position.tolist(),
            "velocity": velocity.tolist(),
            "acceleration": [0.0, 0.0, 0.0],
            "prediction": [position.tolist()],
            "trackingError": float(np.linalg.norm(position - reference_position(STEPS * DT))),
            "clearance": min(
                float(np.linalg.norm(position - c)) - r - BODY_RADIUS for c, r in OBSTACLES
            ),
        }
    )
    return {
        "id": identifier,
        "label": label,
        "frames": frames,
        "metrics": {
            "rmsTrackingError": float(np.sqrt(np.mean(np.square(errors)))),
            "maxAcceleration": max(acceleration_norms),
            "minClearance": continuous_min,
            "solverSuccess": successes,
            "solveCount": STEPS,
            "solverIterations": iterations,
            "rmsInputChange": float(np.sqrt(np.mean(np.square(input_changes)))),
            "horizonSteps": n,
            "smoothWeight": smooth_weight,
        },
    }


def generate_drone_scene() -> dict[str, Any]:
    """Canonical generator, full precision before JSON projection rounding."""
    return {
        "model": "3D質点の並進運動：p次=p+Δt v+½Δt²a、v次=v+Δt a。各軸|a|≤2 m/s²。",
        "dt": DT,
        "bodyRadius": BODY_RADIUS,
        "accelerationBound": ACCELERATION_BOUND,
        "reference": [reference_position(k * DT).tolist() for k in range(STEPS + 1)],
        "obstacles": [{"center": c.tolist(), "radius": r} for c, r in OBSTACLES],
        "target": reference_position(STEPS * DT).tolist(),
        "variants": [
            simulate_variant("tracking", "目標軌道への追従を優先", 0.04),
            simulate_variant("smooth", "加速度の変化を抑える", 0.6),
        ],
        "sources": [
            {
                "title": "OSQP — Model predictive control (MPC)",
                "url": "https://osqp.org/docs/examples/mpc.html",
            },
            {
                "title": "UZH RPG — Model Predictive Control for Quadrotors",
                "url": "https://github.com/uzh-rpg/rpg_mpc",
            },
        ],
        "limitations": [
            "並進の質点モデルによる独自の教材です。PAMPCの再現や実機の飛行検証ではありません。",
            "姿勢はa+[0,0,9.81]の推力方向から描画用に導出します。姿勢・モーターの応答、風、状態推定は計算していません。",
            "球障害物を既知として、SLSQPで局所解を求めます。大域最適性・任意条件での安定性は保証しません。",
            "予測の制約は端点と中点です。実行した各区間は距離の4次多項式の停留点と端点で連続時間の衝突を別途検査しています。",
            "同じ参照軌道・制約・予測時間で入力変化の重みだけを変更した比較です。設定の普遍的な優劣を示しません。",
        ],
    }
