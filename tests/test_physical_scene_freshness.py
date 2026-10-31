"""A rendered result must belong to the checked-in model and numerical environment."""

import json
from pathlib import Path

import pytest

from optimization_compass.scene_fingerprint import generator_input_sha256, numerical_environment

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
    data = json.loads(
        (ROOT / "site/src/features/physical-scenes/data" / f"{scene}.json").read_text(
            encoding="utf-8"
        )
    )
    expected = generator_input_sha256(
        ROOT, ROOT / "src/optimization_compass" / module, ROOT / "scripts" / generator
    )
    assert data["generator_input_sha256"] == expected, (
        f"Regenerate {scene} with uv run python scripts/{generator}"
    )


LOCK = """
[[package]]
name = "certifi"
version = "{certifi}"

[[package]]
name = "numpy"
version = "{numpy}"

[[package]]
name = "scipy"
version = "1.18.1"
"""


def test_only_numerical_packages_enter_the_fingerprint(tmp_path: Path) -> None:
    lock = tmp_path / "uv.lock"
    lock.write_text(LOCK.format(certifi="2026.6.17", numpy="2.5.3"), encoding="utf-8")
    before = numerical_environment(lock)
    lock.write_text(LOCK.format(certifi="2026.10.23", numpy="2.5.3"), encoding="utf-8")
    assert numerical_environment(lock) == before == "numpy==2.5.3\nscipy==1.18.1\n"
    lock.write_text(LOCK.format(certifi="2026.10.23", numpy="2.6.0"), encoding="utf-8")
    assert numerical_environment(lock) != before


def test_a_missing_numerical_package_is_an_error(tmp_path: Path) -> None:
    lock = tmp_path / "uv.lock"
    lock.write_text('[[package]]\nname = "numpy"\nversion = "2.5.3"\n', encoding="utf-8")
    with pytest.raises(ValueError, match="scipy"):
        numerical_environment(lock)
