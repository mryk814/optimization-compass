from __future__ import annotations

import argparse
import hashlib
import shutil
import sqlite3
from pathlib import Path


def verify(path: Path) -> None:
    uri = f"file:{path.resolve()}?mode=ro"
    connection = sqlite3.connect(uri, uri=True)
    try:
        violations = connection.execute("PRAGMA foreign_key_check").fetchall()
        failures = connection.execute(
            "SELECT check_id, details FROM release_checks WHERE status = 'fail'"
        ).fetchall()
    finally:
        connection.close()
    if violations:
        raise SystemExit(f"foreign key violations: {len(violations)}")
    if failures:
        raise SystemExit(f"failed release checks: {failures}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("database", type=Path)
    parser.add_argument("--version", required=True)
    args = parser.parse_args()
    source: Path = args.database
    if not source.exists():
        raise SystemExit(f"not found: {source}")
    verify(source)
    destination = Path(__file__).parents[1] / "src/optimization_compass/resources/knowledge.sqlite"
    shutil.copy2(source, destination)
    digest = hashlib.sha256(destination.read_bytes()).hexdigest()
    version_file = destination.parent / "DATASET_VERSION"
    version_file.write_text(f"{args.version}\nsha256={digest}\n", encoding="utf-8")
    print(f"updated {destination}")
    print(f"sha256={digest}")


if __name__ == "__main__":
    main()
