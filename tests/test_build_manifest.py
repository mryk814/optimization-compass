from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from optimization_compass.build_manifest import (
    DEFAULT_BUILD_MANIFEST,
    BuildManifest,
    BuildManifestError,
    validate_build_manifest,
)

ROOT = Path(__file__).parents[1]


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _write_manifest(root: Path, migrations: list[dict[str, str]]) -> Path:
    (root / "data/migrations").mkdir(parents=True)
    (root / "data/seeds").mkdir(parents=True)
    (root / "src/optimization_compass/resources").mkdir(parents=True)
    for migration in migrations:
        path = root / migration["path"]
        path.write_text(migration.get("content", "-- migration\n"), encoding="utf-8")
        migration["sha256"] = _digest(path)
    for relative in (
        "data/seeds/atlas_metadata.json",
        "data/seeds/atomic_predicates.json",
        "src/optimization_compass/resources/problem-suite.json",
    ):
        (root / relative).write_text("{}", encoding="utf-8")
    manifest_path = root / "data/build-manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "manifest_version": "1.0.0",
                "schema_migrations": [
                    {
                        "id": migration["id"],
                        "path": migration["path"],
                        "sha256": migration["sha256"],
                    }
                    for migration in migrations
                ],
                "specialized_inputs": [
                    "data/seeds/atlas_metadata.json",
                    "data/seeds/atomic_predicates.json",
                    "src/optimization_compass/resources/problem-suite.json",
                ],
            }
        ),
        encoding="utf-8",
    )
    return manifest_path


def test_repository_manifest_validates_all_current_migrations() -> None:
    manifest = validate_build_manifest(DEFAULT_BUILD_MANIFEST, repository_root=ROOT)

    assert [migration.id for migration in manifest.schema_migrations] == [
        f"{number:03d}" for number in range(3, 21)
    ]


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        (
            {
                "manifest_version": "1.0.0",
                "schema_migrations": [
                    {"id": "003", "path": "data/migrations/003_a.sql", "sha256": "a" * 64},
                    {"id": "003", "path": "data/migrations/004_b.sql", "sha256": "b" * 64},
                ],
                "specialized_inputs": ["data/seeds/atlas_metadata.json"],
            },
            "IDs must be unique",
        ),
        (
            {
                "manifest_version": "1.0.0",
                "schema_migrations": [
                    {"id": "004", "path": "data/migrations/004_b.sql", "sha256": "b" * 64},
                    {"id": "003", "path": "data/migrations/003_a.sql", "sha256": "a" * 64},
                ],
                "specialized_inputs": ["data/seeds/atlas_metadata.json"],
            },
            "ordered by increasing ID",
        ),
    ],
)
def test_manifest_model_rejects_duplicate_or_unordered_migrations(
    payload: dict[str, object], message: str
) -> None:
    with pytest.raises(ValidationError, match=message):
        BuildManifest.model_validate(payload)


def test_manifest_rejects_unregistered_migration(tmp_path: Path) -> None:
    manifest_path = _write_manifest(
        tmp_path,
        [{"id": "003", "path": "data/migrations/003_a.sql"}],
    )
    extra = tmp_path / "data/migrations/004_b.sql"
    extra.write_text("-- unregistered\n", encoding="utf-8")

    with pytest.raises(BuildManifestError, match="unregistered_migration"):
        validate_build_manifest(manifest_path, repository_root=tmp_path)


def test_manifest_rejects_hash_drift(tmp_path: Path) -> None:
    manifest_path = _write_manifest(
        tmp_path,
        [{"id": "003", "path": "data/migrations/003_a.sql"}],
    )
    (tmp_path / "data/migrations/003_a.sql").write_text("-- changed\n", encoding="utf-8")

    with pytest.raises(BuildManifestError, match="hash_mismatch"):
        validate_build_manifest(manifest_path, repository_root=tmp_path)


def test_manifest_hash_is_stable_across_text_checkout_line_endings(tmp_path: Path) -> None:
    manifest_path = _write_manifest(
        tmp_path,
        [{"id": "003", "path": "data/migrations/003_a.sql"}],
    )
    migration_path = tmp_path / "data/migrations/003_a.sql"
    migration_path.write_bytes(
        migration_path.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
    )

    validate_build_manifest(manifest_path, repository_root=tmp_path)


def test_manifest_rejects_missing_specialized_input(tmp_path: Path) -> None:
    manifest_path = _write_manifest(
        tmp_path,
        [{"id": "003", "path": "data/migrations/003_a.sql"}],
    )
    (tmp_path / "data/seeds/atomic_predicates.json").unlink()

    with pytest.raises(BuildManifestError, match="missing_input"):
        validate_build_manifest(manifest_path, repository_root=tmp_path)
