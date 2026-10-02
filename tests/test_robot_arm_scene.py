"""Independent geometry and solve-boundary checks for spatial arm planning."""

import numpy as np
import pytest

from optimization_compass.robot_arm_scene import (
    BASE,
    OBSTACLES,
    SAFETY_MARGIN,
    VELOCITY_LIMIT,
    capsule_clearances,
    forward_kinematics,
    interpolate_joints,
    solve_trajectory,
    validate_trajectory,
)


def test_forward_kinematics_preserves_known_positions_and_link_lengths():
    np.testing.assert_allclose(
        forward_kinematics(np.zeros(3)), [[0, 0, 0.35], [0.9, 0, 0.35], [1.65, 0, 0.35]]
    )
    vertical = forward_kinematics(np.array([0.7, np.pi / 2, 0]))
    np.testing.assert_allclose(vertical[-1], BASE + [0, 0, 1.65], atol=1e-12)
    np.testing.assert_allclose(np.linalg.norm(np.diff(vertical, axis=0), axis=1), [0.9, 0.75])


def test_capsule_clearance_includes_segment_interior_and_radius():
    center, radius = OBSTACLES[0]
    points = np.array([center + [-1, 0.5, 0], center + [1, 0.5, 0]])
    assert capsule_clearances(points)[0, 0] == pytest.approx(0.5 - radius - 0.045)
    beyond_endpoint = np.array([center + [1, 0, 0], center + [2, 0, 0]])
    assert capsule_clearances(beyond_endpoint)[0, 0] == pytest.approx(1.0 - radius - 0.045)


def test_actual_optimizer_and_independent_dense_geometric_validation():
    solution = solve_trajectory(0.003)
    knots = solution["knots"]
    validation = validate_trajectory(knots, samples_per_segment=137)
    assert solution["metrics"]["solverSuccess"]
    assert validation["valid"]
    assert validation["maxVelocity"] <= VELOCITY_LIMIT + 1e-7
    # Independent distance calculation with a denser, different sampling grid.
    poses = forward_kinematics(interpolate_joints(knots, 137))
    for center, radius in OBSTACLES:
        for pose in poses:
            for a, b in zip(pose[:-1], pose[1:], strict=True):
                v = b - a
                t = min(1.0, max(0.0, float(np.dot(center - a, v) / np.dot(v, v))))
                assert np.linalg.norm(center - (a + t * v)) - radius - 0.045 >= SAFETY_MARGIN - 1e-7


def test_validation_rejects_interior_collision_between_clear_endpoints():
    from optimization_compass.robot_arm_scene import GOAL, START

    bad = np.vstack([START, GOAL])
    assert capsule_clearances(forward_kinematics(bad)).min() > SAFETY_MARGIN
    assert not validate_trajectory(bad)["valid"]


def test_objective_variants_have_a_real_distance_smoothness_tradeoff():
    short = solve_trajectory(0.003)["metrics"]
    smooth = solve_trajectory(0.5)["metrics"]
    assert short["tipTravel"] < smooth["tipTravel"] - 0.1
    assert smooth["integratedSquaredAcceleration"] < short["integratedSquaredAcceleration"] / 5
    assert smooth["maxVelocity"] < short["maxVelocity"] / 2
