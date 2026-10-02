"""Verify optimization, closed-loop dynamics, and executed interval clearance."""

import json
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from optimization_compass import drone_scene


@pytest.fixture(scope="module")
def scene() -> dict[str, Any]:
    return drone_scene.generate_drone_scene()


def test_closed_loop_predictions_dynamics_and_constraints(scene: dict[str, Any]) -> None:
    for variant in scene["variants"]:
        frames = variant["frames"]
        assert variant["metrics"]["solverSuccess"] == drone_scene.STEPS
        for frame, following in zip(frames, frames[1:], strict=False):
            p, v, a = (np.array(frame[key]) for key in ("position", "velocity", "acceleration"))
            expected = p + drone_scene.DT * v + 0.5 * drone_scene.DT**2 * a
            np.testing.assert_allclose(following["position"], expected, atol=1e-12)
            np.testing.assert_allclose(following["velocity"], v + drone_scene.DT * a, atol=1e-12)
            np.testing.assert_allclose(frame["prediction"][0], p, atol=1e-12)
            np.testing.assert_allclose(frame["prediction"][1], expected, atol=1e-12)
            assert len(frame["prediction"]) == drone_scene.HORIZON + 1
            assert np.max(np.abs(a)) <= drone_scene.ACCELERATION_BOUND + 1e-9
            assert drone_scene.interval_clearance(p, v, a) >= 0.02
        assert frames[-1]["trackingError"] < 0.1


def test_weight_tradeoff_is_measured_from_computed_motion(scene: dict[str, Any]) -> None:
    tracking, smooth = scene["variants"]
    assert smooth["metrics"]["rmsInputChange"] < tracking["metrics"]["rmsInputChange"]
    assert smooth["metrics"]["rmsTrackingError"] > tracking["metrics"]["rmsTrackingError"]
    tp = np.array([f["position"] for f in tracking["frames"]])
    sp = np.array([f["position"] for f in smooth["frames"]])
    assert np.max(np.linalg.norm(tp - sp, axis=1)) > 0.08
    assert np.ptp(tp[:, 2]) > 0.6


def test_optimizer_is_repeated_and_each_prediction_uses_its_solution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = drone_scene.minimize
    controls = []

    def recorded_minimize(*args: Any, **kwargs: Any) -> Any:
        solved = original(*args, **kwargs)
        controls.append(solved.x.reshape(drone_scene.HORIZON, 3).copy())
        return solved

    monkeypatch.setattr(drone_scene, "minimize", recorded_minimize)
    variant = drone_scene.simulate_variant("verification", "検証", 0.04)
    assert len(controls) == drone_scene.STEPS
    for frame, optimized in zip(variant["frames"][:-1], controls, strict=True):
        np.testing.assert_array_equal(frame["acceleration"], optimized[0])
        p, v = np.array(frame["position"]), np.array(frame["velocity"])
        predicted = [p.copy()]
        for a in optimized:
            assert np.max(np.abs(a)) <= drone_scene.ACCELERATION_BOUND + 1e-9
            midpoint = p + 0.5 * drone_scene.DT * v + 0.125 * drone_scene.DT**2 * a
            p = p + drone_scene.DT * v + 0.5 * drone_scene.DT**2 * a
            v = v + drone_scene.DT * a
            for center, radius in drone_scene.OBSTACLES:
                for checkpoint in (midpoint, p):
                    assert np.linalg.norm(checkpoint - center) >= (
                        radius + drone_scene.BODY_RADIUS + 0.025 - 1e-6
                    )
            predicted.append(p.copy())
        np.testing.assert_allclose(frame["prediction"], predicted, atol=2e-14)


def test_continuous_clearance_detects_between_sample_collision() -> None:
    center, radius = drone_scene.OBSTACLES[0]
    # Both endpoints are clear, yet the middle of this interval crosses center.
    p = center + np.array([-1.0, 0.0, 0.0])
    v = np.array([2.0 / drone_scene.DT, 0.0, 0.0])
    assert drone_scene.interval_clearance(p, v, np.zeros(3)) == pytest.approx(
        -radius - drone_scene.BODY_RADIUS
    )


def test_committed_projection_matches_computation(scene: dict[str, Any]) -> None:
    root = Path(__file__).resolve().parents[1]
    path = root / "site/src/features/physical-scenes/data/drone.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert path.stat().st_size < 200_000
    for actual, expected in zip(payload["variants"], scene["variants"], strict=True):
        for saved, computed in zip(actual["frames"], expected["frames"], strict=True):
            for key in saved:
                np.testing.assert_allclose(saved[key], computed[key], atol=5.1e-7, rtol=0)
        assert actual["metrics"]["solveCount"] == drone_scene.STEPS
