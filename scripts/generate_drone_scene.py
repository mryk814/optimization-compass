"""Generate the compact static projection; optimization stays offline."""

import hashlib
import json
from pathlib import Path
from typing import Any

from optimization_compass.drone_scene import generate_drone_scene


def rounded(value: Any) -> Any:
    if isinstance(value, float):
        return round(value, 6)
    if isinstance(value, list):
        return [rounded(item) for item in value]
    if isinstance(value, dict):
        return {key: rounded(item) for key, item in value.items()}
    return value


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    output = root / "site/src/features/physical-scenes/data/drone.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    scene = rounded(generate_drone_scene())
    module_path = root / "src/optimization_compass/drone_scene.py"
    scene["generator_input_sha256"] = hashlib.sha256(
        b"".join(
            path.read_text(encoding="utf-8").encode("utf-8")
            for path in (module_path, Path(__file__), root / "uv.lock")
        )
    ).hexdigest()
    output.write_text(
        json.dumps(scene, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8"
    )
    print(f"{output}: {output.stat().st_size:,} bytes")
    for variant in scene["variants"]:
        print(variant["id"], variant["metrics"])


if __name__ == "__main__":
    main()
