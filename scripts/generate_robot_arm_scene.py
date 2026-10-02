"""Regenerate the compact teaching scene from an independently validated solve."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from optimization_compass.robot_arm_scene import generate_scene


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("site/src/features/physical-scenes/data/arm.json"),
    )
    args = parser.parse_args()
    scene = generate_scene()
    root = Path(__file__).resolve().parents[1]
    module_path = root / "src/optimization_compass/robot_arm_scene.py"
    scene["generator_input_sha256"] = hashlib.sha256(
        b"".join(
            path.read_text(encoding="utf-8").encode("utf-8")
            for path in (module_path, Path(__file__), root / "uv.lock")
        )
    ).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(scene, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
    )
    print(f"Generated {args.output}: {args.output.stat().st_size} bytes")
    for variant in scene["variants"]:
        print(variant["id"], variant["metrics"])


if __name__ == "__main__":
    main()
