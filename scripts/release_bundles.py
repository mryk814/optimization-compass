from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from optimization_compass.release_bundle import (
    ReleaseBundleError,
    build_release_bundle,
    verify_release_bundle,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Prepare and verify complete dataset release bundles."
    )
    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("prepare", help="Build a deterministic ZIP from a staged tree.")
    prepare.add_argument("--staged-directory", type=Path, required=True)
    prepare.add_argument("--output-directory", type=Path, required=True)
    prepare.add_argument("--source-commit", required=True)
    prepare.add_argument("--tag", required=True)
    verify = commands.add_parser("verify", help="Verify a prepared ZIP and its release tree.")
    verify.add_argument("--bundle", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "prepare":
            result = build_release_bundle(
                args.staged_directory,
                args.output_directory,
                source_commit=args.source_commit,
                tag=args.tag,
            )
        else:
            result = verify_release_bundle(args.bundle)
    except ReleaseBundleError as error:
        parser.exit(1, f"Release bundle failed: {error}\n")
    payload = asdict(result)
    payload["path"] = str(result.path)
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
