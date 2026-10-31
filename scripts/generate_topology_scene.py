"""Regenerate the offline, equilibrium-validated 3-D topology scene."""

import json
from pathlib import Path

from optimization_compass.scene_fingerprint import generator_input_sha256
from optimization_compass.topology_scene import generate_topology_scene


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    target = root / "site/src/features/physical-scenes/data/topology.json"
    scene = generate_topology_scene()
    source = root / "src/optimization_compass/topology_scene.py"
    scene["generator_input_sha256"] = generator_input_sha256(root, source, Path(__file__))
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(scene, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8"
    )
    print(f"Generated {target.stat().st_size:,} bytes")
    for variant in scene["variants"]:
        print(variant["id"], variant["metrics"])


if __name__ == "__main__":
    main()
