from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from optimization_compass.dataset_release import (
    BASE_DATASET_VERSION,
    build_staged_release,
    publish_release,
)

ROOT = Path(__file__).parents[1]
BASE_DATABASE = ROOT / f"data/optimization_method_selection_database_v{BASE_DATASET_VERSION}.sqlite"
RUNTIME_DATABASE = ROOT / "src/optimization_compass/resources/knowledge.sqlite"
VERSION_FILE = ROOT / "src/optimization_compass/resources/DATASET_VERSION"


def stage() -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="optimization-compass-stage-") as temporary:
        root = Path(temporary)
        first = build_staged_release(BASE_DATABASE, root / "first")
        second = build_staged_release(BASE_DATABASE, root / "second")
        if first.tree_sha256 != second.tree_sha256:
            raise SystemExit(
                f"staged rebuild is not deterministic: {first.tree_sha256} != {second.tree_sha256}"
            )
        return {
            "mode": "stage",
            "version": first.version,
            "tree_sha256": first.tree_sha256,
            "rebuilds": 2,
            "published": False,
        }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Rebuild and cross-validate every deterministic dataset distribution."
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--stage", action="store_true", help="Build twice in temporary storage.")
    mode.add_argument("--publish", metavar="VERSION", help="Atomically publish a validated tree.")
    parser.add_argument("--staged-directory", type=Path)
    args = parser.parse_args()
    if args.stage:
        print(json.dumps(stage(), ensure_ascii=False, indent=2))
        return
    if args.staged_directory is None:
        parser.error("--publish requires --staged-directory")
    publish_release(
        args.staged_directory,
        ROOT / "data",
        RUNTIME_DATABASE,
        VERSION_FILE,
        version=str(args.publish),
    )
    print(json.dumps({"mode": "publish", "version": args.publish}, indent=2))


if __name__ == "__main__":
    main()
