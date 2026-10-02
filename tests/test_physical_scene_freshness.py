"""A rendered result must belong to the checked-in model and numerical environment."""

import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    ("scene", "module", "generator"),
    [
        ("topology", "topology_scene.py", "generate_topology_scene.py"),
        ("arm", "robot_arm_scene.py", "generate_robot_arm_scene.py"),
        ("drone", "drone_scene.py", "generate_drone_scene.py"),
    ],
)
def test_generated_scene_matches_its_computation(scene: str, module: str, generator: str) -> None:
    inputs = (
        (ROOT / "src/optimization_compass" / module).read_text(encoding="utf-8").encode("utf-8")
        + (ROOT / "scripts" / generator).read_text(encoding="utf-8").encode("utf-8")
        + (ROOT / "uv.lock").read_text(encoding="utf-8").encode("utf-8")
    )
    data = json.loads(
        (ROOT / "site/src/features/physical-scenes/data" / f"{scene}.json").read_text(
            encoding="utf-8"
        )
    )
    assert data["generator_input_sha256"] == hashlib.sha256(inputs).hexdigest(), (
        f"Regenerate {scene} with uv run python scripts/{generator}"
    )
