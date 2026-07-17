from __future__ import annotations

import argparse
import json
import zipfile
from dataclasses import asdict
from pathlib import Path

from optimization_compass.historical_releases import (
    HistoricalReleaseError,
    load_historical_backfill_plan,
    prepare_historical_backfill,
    verify_cataloged_historical_release_bundle,
    verify_historical_release_bundle,
    verify_remote_historical_releases,
)
from optimization_compass.release_bundle import (
    BUNDLE_INDEX_NAME,
    ReleaseBundleError,
    build_release_bundle,
    verify_release_bundle,
)

ROOT = Path(__file__).parents[1]


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
    historical_prepare = commands.add_parser(
        "historical-prepare",
        help="Reconstruct the reviewed historical batch from exact Git blobs.",
    )
    historical_prepare.add_argument("--plan", type=Path, required=True)
    historical_prepare.add_argument("--catalog", type=Path, required=True)
    historical_prepare.add_argument("--output-directory", type=Path, required=True)
    historical_prepare.add_argument("--repo-root", type=Path, default=ROOT)
    historical_verify = commands.add_parser(
        "historical-verify",
        help="Verify one prepared historical ZIP against the reviewed plan.",
    )
    historical_verify.add_argument("--plan", type=Path, required=True)
    historical_verify.add_argument("--bundle", type=Path, required=True)
    historical_verify.add_argument("--catalog", type=Path)
    historical_remote = commands.add_parser(
        "historical-verify-remote",
        help="Anonymously download and verify every candidate historical asset.",
    )
    historical_remote.add_argument("--plan", type=Path, required=True)
    historical_remote.add_argument("--catalog", type=Path, required=True)
    historical_remote.add_argument("--repo-root", type=Path, default=ROOT)
    historical_remote.add_argument("--remote", default="origin")
    args = parser.parse_args()
    try:
        if args.command == "prepare":
            result = build_release_bundle(
                args.staged_directory,
                args.output_directory,
                source_commit=args.source_commit,
                tag=args.tag,
            )
            payload: object = asdict(result)
        elif args.command == "verify":
            result = verify_release_bundle(args.bundle)
            payload = asdict(result)
        elif args.command == "historical-prepare":
            payload = prepare_historical_backfill(
                args.repo_root,
                args.plan,
                args.catalog,
                args.output_directory,
            )
        elif args.command == "historical-verify":
            plan = load_historical_backfill_plan(args.plan)
            with zipfile.ZipFile(args.bundle) as archive:
                index = json.loads(archive.read(BUNDLE_INDEX_NAME))
            version = index.get("version") if isinstance(index, dict) else None
            entry = next((item for item in plan.releases if item.version == version), None)
            if entry is None:
                raise HistoricalReleaseError("historical bundle version is absent from the plan")
            if args.catalog is None:
                result = verify_historical_release_bundle(args.bundle, entry)
            else:
                result = verify_cataloged_historical_release_bundle(
                    args.bundle, entry, args.catalog, plan.repository
                )
            payload = asdict(result)
        else:
            payload = verify_remote_historical_releases(
                args.plan,
                args.catalog,
                repository_root=args.repo_root,
                remote=args.remote,
            )
    except (ReleaseBundleError, HistoricalReleaseError, OSError, zipfile.BadZipFile) as error:
        parser.exit(1, f"Release bundle failed: {error}\n")
    if isinstance(payload, dict) and isinstance(payload.get("path"), Path):
        payload["path"] = str(payload["path"])
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
