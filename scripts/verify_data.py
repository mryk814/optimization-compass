from __future__ import annotations

import argparse
import json
from pathlib import Path

from optimization_compass.dataset_release import verify_release_tree
from optimization_compass.db import KnowledgeRepository


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Recompute live SQLite checks and optionally verify every release format."
    )
    parser.add_argument("--database", type=Path)
    parser.add_argument("--release-tree", type=Path)
    args = parser.parse_args()
    result = KnowledgeRepository(args.database).verify()
    payload: dict[str, object] = {"database": result}
    if args.release_tree is not None:
        formats = verify_release_tree(args.release_tree)
        payload["release_tree"] = {
            "ok": formats.ok,
            "formats": sorted(formats.formats),
            "table_count": formats.table_count,
        }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
