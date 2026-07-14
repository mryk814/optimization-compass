from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from optimization_compass.dataset_release import (
    BASE_DATASET_VERSION,
    RELEASE_AUTHORITY,
    build_staged_release,
    publish_release,
)

ROOT = Path(__file__).parents[1]
BASE_DATABASE = ROOT / f"data/optimization_method_selection_database_v{BASE_DATASET_VERSION}.sqlite"
RUNTIME_DATABASE = ROOT / "src/optimization_compass/resources/knowledge.sqlite"
VERSION_FILE = ROOT / "src/optimization_compass/resources/DATASET_VERSION"
SITE_DATA_DIRECTORY = ROOT / "site/public/data"


def stage(output_directory: Path | None = None) -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="optimization-compass-stage-") as temporary:
        root = Path(temporary)
        first_output = output_directory if output_directory is not None else root / "first"
        first = build_staged_release(BASE_DATABASE, first_output)
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
            "output_directory": str(output_directory) if output_directory is not None else None,
        }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Rebuild and cross-validate every deterministic dataset distribution."
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--stage", action="store_true", help="Build twice in temporary storage.")
    mode.add_argument("--publish", action="store_true", help="Atomically publish a validated tree.")
    parser.add_argument("--staged-directory", type=Path)
    parser.add_argument("--output", type=Path, help="Keep the first validated staged tree here.")
    args = parser.parse_args()
    if args.stage:
        if args.staged_directory is not None:
            parser.error("--staged-directory is only valid with --publish")
        print(json.dumps(stage(args.output), ensure_ascii=False, indent=2))
        return
    if args.output is not None:
        parser.error("--output is only valid with --stage")
    if args.staged_directory is None:
        parser.error("--publish requires --staged-directory")
    publish_release(
        args.staged_directory,
        ROOT / "data",
        RUNTIME_DATABASE,
        VERSION_FILE,
        SITE_DATA_DIRECTORY,
    )
    print(json.dumps({"mode": "publish", "version": RELEASE_AUTHORITY.dataset_version}, indent=2))


if __name__ == "__main__":
    main()
