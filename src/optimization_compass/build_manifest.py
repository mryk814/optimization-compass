"""Declarative validation for deterministic dataset build inputs.

The manifest records the ordered schema/data migrations that the staged
release applies.  It is an authoring input, not a generated release artifact;
the released SQLite database remains the runtime authority.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

MANIFEST_VERSION = "1.0.0"
ROOT = Path(__file__).parents[2]
DEFAULT_BUILD_MANIFEST = ROOT / "data/build-manifest.json"
_SHA256_PATTERN = r"^[0-9a-f]{64}$"


class BuildManifestError(ValueError):
    """Raised when the build manifest is invalid or drifts from the tree."""


class SchemaMigration(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    id: str = Field(pattern=r"^\d{3}$")
    path: str
    sha256: str = Field(pattern=_SHA256_PATTERN)

    @field_validator("path")
    @classmethod
    def validate_path(cls, value: str) -> str:
        path = PurePosixPath(value)
        if (
            not value
            or "\\" in value
            or path.is_absolute()
            or ".." in path.parts
            or path.parts[:2] != ("data", "migrations")
            or path.suffix != ".sql"
        ):
            raise ValueError("migration path must be a relative data/migrations/*.sql path")
        return value


class BuildManifest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    manifest_version: str = Field(default=MANIFEST_VERSION, pattern=r"^\d+\.\d+\.\d+$")
    schema_migrations: list[SchemaMigration] = Field(min_length=1)
    specialized_inputs: list[str] = Field(min_length=1)

    @field_validator("specialized_inputs")
    @classmethod
    def validate_specialized_inputs(cls, values: list[str]) -> list[str]:
        for value in values:
            path = PurePosixPath(value)
            if not value or "\\" in value or path.is_absolute() or ".." in path.parts:
                raise ValueError("specialized input paths must be relative repository paths")
        if len(values) != len(set(values)):
            raise ValueError("specialized input paths must be unique")
        return values

    @model_validator(mode="after")
    def validate_order_and_identity(self) -> BuildManifest:
        ids = [migration.id for migration in self.schema_migrations]
        paths = [migration.path for migration in self.schema_migrations]
        if len(ids) != len(set(ids)):
            raise ValueError("schema migration IDs must be unique")
        if len(paths) != len(set(paths)):
            raise ValueError("schema migration paths must be unique")
        if ids != sorted(ids):
            raise ValueError("schema migrations must be ordered by increasing ID")
        for migration in self.schema_migrations:
            filename_id = PurePosixPath(migration.path).stem.split("_", 1)[0]
            if migration.id != filename_id:
                raise ValueError(
                    f"schema migration ID {migration.id} does not match {migration.path}"
                )
        return self


def _sha256(path: Path) -> str:
    # Treat text checkout line endings consistently across Windows and CI.
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _repository_path(root: Path, relative: str) -> Path:
    path = (root / PurePosixPath(relative)).resolve()
    resolved_root = root.resolve()
    if path != resolved_root and resolved_root not in path.parents:
        raise BuildManifestError(f"manifest path escapes repository: {relative}")
    return path


def load_build_manifest(path: Path = DEFAULT_BUILD_MANIFEST) -> BuildManifest:
    try:
        return BuildManifest.model_validate_json(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, ValidationError) as error:
        raise BuildManifestError(f"data.manifest.invalid: {path}: {error}") from error


def validate_build_manifest(
    path: Path = DEFAULT_BUILD_MANIFEST,
    *,
    repository_root: Path | None = None,
) -> BuildManifest:
    """Validate manifest structure and every managed input in the repository."""
    root = (repository_root or ROOT).resolve()
    manifest = load_build_manifest(path)
    if manifest.manifest_version != MANIFEST_VERSION:
        raise BuildManifestError(
            f"data.manifest.version: unsupported manifest version {manifest.manifest_version}"
        )

    declared_paths = {migration.path for migration in manifest.schema_migrations}
    migration_directory = root / "data/migrations"
    discovered_paths = {
        item.relative_to(root).as_posix() for item in migration_directory.glob("*.sql")
    }
    missing_paths = sorted(declared_paths - discovered_paths)
    unregistered_paths = sorted(discovered_paths - declared_paths)
    if missing_paths:
        raise BuildManifestError(f"data.manifest.missing_migration: {', '.join(missing_paths)}")
    if unregistered_paths:
        raise BuildManifestError(
            f"data.manifest.unregistered_migration: {', '.join(unregistered_paths)}"
        )

    for migration in manifest.schema_migrations:
        migration_path = _repository_path(root, migration.path)
        observed = _sha256(migration_path)
        if observed != migration.sha256:
            raise BuildManifestError(
                f"data.manifest.hash_mismatch: {migration.path} expected {migration.sha256}"
                f" observed {observed}"
            )
    for relative in manifest.specialized_inputs:
        input_path = _repository_path(root, relative)
        if not input_path.is_file():
            raise BuildManifestError(f"data.manifest.missing_input: {relative}")
    return manifest


def migration_paths(
    manifest: BuildManifest, *, repository_root: Path | None = None
) -> tuple[Path, ...]:
    root = (repository_root or ROOT).resolve()
    return tuple(_repository_path(root, migration.path) for migration in manifest.schema_migrations)
