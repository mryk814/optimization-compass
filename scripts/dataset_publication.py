from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from optimization_compass.dataset_publication import (
    CITATION_PATH,
    DATASET_CARD_PATH,
    PUBLICATION_AUTHORITY_PATH,
    RELEASE_CATALOG_PATH,
    DatasetPublicationError,
    check_repository_publication_metadata,
    prepare_publication,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Prepare and check deterministic dataset citation metadata without network writes."
        )
    )
    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser(
        "prepare",
        help="Verify a release bundle and write publication metadata outside the repository.",
    )
    prepare.add_argument("--bundle", type=Path, required=True)
    prepare.add_argument("--output-directory", type=Path, required=True)
    prepare.add_argument("--version")
    prepare.add_argument("--authority", type=Path, default=PUBLICATION_AUTHORITY_PATH)
    prepare.add_argument("--catalog", type=Path, default=RELEASE_CATALOG_PATH)
    check = commands.add_parser(
        "check", help="Fail when the committed CITATION.cff or dataset card is stale."
    )
    check.add_argument("--authority", type=Path, default=PUBLICATION_AUTHORITY_PATH)
    check.add_argument("--catalog", type=Path, default=RELEASE_CATALOG_PATH)
    check.add_argument("--citation", type=Path, default=CITATION_PATH)
    check.add_argument("--dataset-card", type=Path, default=DATASET_CARD_PATH)
    args = parser.parse_args()
    try:
        if args.command == "prepare":
            result = prepare_publication(
                bundle_path=args.bundle,
                output_directory=args.output_directory,
                authority_path=args.authority,
                catalog_path=args.catalog,
                version=args.version,
            )
            payload = asdict(result)
            payload["output_directory"] = str(result.output_directory)
            print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
            return
        check_repository_publication_metadata(
            authority_path=args.authority,
            catalog_path=args.catalog,
            citation_path=args.citation,
            dataset_card_path=args.dataset_card,
        )
    except DatasetPublicationError as error:
        parser.exit(1, f"Dataset publication failed: {error}\n")
    print("dataset publication metadata is current")


if __name__ == "__main__":
    main()
