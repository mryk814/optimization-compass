from __future__ import annotations

import json
import os
import re
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Protocol
from urllib.parse import ParseResult, urlparse

from optimization_compass.release_identity import (
    DatasetReleaseIdentity,
    ReleaseIdentityError,
    validate_release_identity,
    validate_semantic_version,
    validate_sha256,
)


class ReleaseCatalogError(ValueError):
    pass


@dataclass(frozen=True)
class ReleaseBundleDescriptor:
    url: str
    sha256: str
    size_bytes: int


@dataclass(frozen=True)
class ReleaseArchiveDescriptor:
    provider: str
    identifier: str
    url: str


@dataclass(frozen=True)
class ReleaseCatalogEntry:
    version: str
    release_date: str
    database_sha256: str
    manifest_sha256: str
    source_commit: str
    tag: str
    bundle: ReleaseBundleDescriptor
    archival: ReleaseArchiveDescriptor | None


@dataclass(frozen=True)
class ReleaseCatalog:
    schema_version: int
    current_version: str | None
    releases: tuple[ReleaseCatalogEntry, ...]

    def as_json_object(self) -> dict[str, object]:
        return asdict(self)


_CATALOG_FIELDS = {"schema_version", "current_version", "releases"}
_ENTRY_FIELDS = {
    "version",
    "release_date",
    "database_sha256",
    "manifest_sha256",
    "source_commit",
    "tag",
    "bundle",
    "archival",
}
_BUNDLE_FIELDS = {"url", "sha256", "size_bytes"}
_ARCHIVE_FIELDS = {"provider", "identifier", "url"}
_SOURCE_COMMIT_PATTERN = re.compile(r"[0-9a-f]{40}")
_REPOSITORY_PATTERN = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")
_ASSET_NAME_PATTERN = re.compile(r"[A-Za-z0-9._-]+")
_GITHUB_RELEASE_PATH_PATTERN = re.compile(
    r"/[^/]+/[^/]+/releases/download/(?P<tag>v[0-9]+\.[0-9]+\.[0-9]+)/[^/]+"
)


def load_release_catalog(path: Path) -> ReleaseCatalog:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ReleaseCatalogError(f"release catalog is not valid JSON: {path}") from error
    catalog = _parse_release_catalog(payload)
    validate_release_catalog(catalog)
    return catalog


def validate_release_catalog(
    catalog: ReleaseCatalog,
    expected_current_identity: DatasetReleaseIdentity | None = None,
) -> None:
    if catalog.schema_version != 1:
        raise ReleaseCatalogError("unsupported release catalog schema version")

    versions: list[str] = []
    for entry in catalog.releases:
        _validate_entry(entry)
        versions.append(entry.version)

    if len(versions) != len(set(versions)):
        raise ReleaseCatalogError("release catalog versions must be unique")
    if versions != sorted(versions, key=_semantic_version_key):
        raise ReleaseCatalogError("release catalog versions must be sorted in ascending order")

    if not catalog.releases:
        if catalog.current_version is not None:
            raise ReleaseCatalogError("an empty release catalog must have a null current_version")
    else:
        if catalog.current_version != catalog.releases[-1].version:
            raise ReleaseCatalogError("current_version must identify the latest catalog entry")

    if expected_current_identity is None:
        return

    if expected_current_identity.schema_version != 1:
        raise ReleaseCatalogError("expected current release identity schema is unsupported")
    try:
        validate_release_identity(
            expected_current_identity.dataset_version,
            expected_current_identity.release_date,
        )
        validate_sha256(expected_current_identity.database_sha256, "database_sha256")
    except ReleaseIdentityError as error:
        raise ReleaseCatalogError("expected current release identity is invalid") from error

    if catalog.current_version != expected_current_identity.dataset_version:
        raise ReleaseCatalogError(
            "catalog current version does not match expected release identity"
        )
    current = catalog.releases[-1]
    if (
        current.release_date != expected_current_identity.release_date
        or current.database_sha256 != expected_current_identity.database_sha256
    ):
        raise ReleaseCatalogError("catalog current entry does not match expected release identity")


def release_catalog_snapshot(
    catalog: ReleaseCatalog,
    release_identity: DatasetReleaseIdentity,
) -> ReleaseCatalog:
    """Return the catalog that can be embedded in a deterministic release tree."""

    validate_release_catalog(catalog)
    _validate_expected_identity(release_identity)
    target_key = _semantic_version_key(release_identity.dataset_version)
    matching = next(
        (entry for entry in catalog.releases if entry.version == release_identity.dataset_version),
        None,
    )
    if matching is not None and (
        matching.release_date != release_identity.release_date
        or matching.database_sha256 != release_identity.database_sha256
    ):
        raise ReleaseCatalogError("catalog current entry does not match expected release identity")
    releases = tuple(
        entry
        for entry in catalog.releases
        if _semantic_version_key(entry.version) <= target_key
        and (matching is not None or _semantic_version_key(entry.version) < target_key)
    )
    snapshot = ReleaseCatalog(
        schema_version=1,
        current_version=releases[-1].version if releases else None,
        releases=releases,
    )
    validate_release_catalog_snapshot(snapshot, release_identity)
    return snapshot


def validate_release_catalog_snapshot(
    catalog: ReleaseCatalog,
    release_identity: DatasetReleaseIdentity,
) -> None:
    """Validate a current or predecessor-only embedded release catalog."""

    validate_release_catalog(catalog)
    _validate_expected_identity(release_identity)
    target_key = _semantic_version_key(release_identity.dataset_version)
    if any(_semantic_version_key(entry.version) > target_key for entry in catalog.releases):
        raise ReleaseCatalogError("embedded catalog cannot contain releases newer than its tree")
    matching = next(
        (entry for entry in catalog.releases if entry.version == release_identity.dataset_version),
        None,
    )
    if matching is not None:
        if catalog.current_version != matching.version:
            raise ReleaseCatalogError("embedded current release must be the catalog current entry")
        if (
            matching.release_date != release_identity.release_date
            or matching.database_sha256 != release_identity.database_sha256
        ):
            raise ReleaseCatalogError(
                "embedded current entry does not match expected release identity"
            )
        return
    if catalog.current_version is not None and (
        _semantic_version_key(catalog.current_version) >= target_key
    ):
        raise ReleaseCatalogError(
            "pre-publication catalog current version must precede the staged release"
        )


def _validate_expected_identity(identity: DatasetReleaseIdentity) -> None:
    if identity.schema_version != 1:
        raise ReleaseCatalogError("expected current release identity schema is unsupported")
    try:
        validate_release_identity(identity.dataset_version, identity.release_date)
        validate_sha256(identity.database_sha256, "database_sha256")
    except ReleaseIdentityError as error:
        raise ReleaseCatalogError("expected current release identity is invalid") from error


def merge_catalog_entry(
    catalog_path: Path,
    entry: ReleaseCatalogEntry,
    output_path: Path,
) -> ReleaseCatalog:
    """Add an immutable release entry and make it current.

    Repeating the same entry is idempotent. Reusing a version with different metadata is rejected.
    """

    catalog = load_release_catalog(catalog_path)
    existing_by_version = {release.version: release for release in catalog.releases}
    existing = existing_by_version.get(entry.version)
    if existing is not None and existing != entry:
        raise ReleaseCatalogError(f"release catalog version is immutable: {entry.version}")
    existing_by_version[entry.version] = entry
    releases = tuple(
        sorted(existing_by_version.values(), key=lambda item: _semantic_version_key(item.version))
    )
    merged = ReleaseCatalog(schema_version=1, current_version=entry.version, releases=releases)
    validate_release_catalog(merged)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(canonical_release_catalog_json(merged), encoding="utf-8")
    return merged


def backfill_catalog_entries(
    catalog_path: Path,
    entries: tuple[ReleaseCatalogEntry, ...],
    output_path: Path,
) -> ReleaseCatalog:
    """Overlay immutable historical entries without changing the current release.

    This is intentionally separate from ``merge_catalog_entry``: normal publication makes a new
    version current, while migration backfill must preserve the already-published current entry.
    Every entry is checked before a candidate file is atomically replaced.
    """

    catalog = load_release_catalog(catalog_path)
    if not catalog.releases or catalog.current_version is None:
        raise ReleaseCatalogError("historical backfill requires a non-empty current catalog")
    current_key = _semantic_version_key(catalog.current_version)
    existing_by_version = {release.version: release for release in catalog.releases}
    incoming_versions: set[str] = set()
    for entry in entries:
        _validate_entry(entry)
        if entry.version in incoming_versions:
            raise ReleaseCatalogError(
                f"historical backfill versions must be unique: {entry.version}"
            )
        incoming_versions.add(entry.version)
        if _semantic_version_key(entry.version) >= current_key:
            raise ReleaseCatalogError(
                f"historical backfill cannot replace or advance current version: {entry.version}"
            )
        existing = existing_by_version.get(entry.version)
        if existing is not None and existing != entry:
            raise ReleaseCatalogError(f"release catalog version is immutable: {entry.version}")
        existing_by_version[entry.version] = entry

    releases = tuple(
        sorted(existing_by_version.values(), key=lambda item: _semantic_version_key(item.version))
    )
    candidate = ReleaseCatalog(
        schema_version=1,
        current_version=catalog.current_version,
        releases=releases,
    )
    validate_release_catalog(candidate)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{output_path.name}.", suffix=".tmp", dir=output_path.parent
    )
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        temporary.write_text(canonical_release_catalog_json(candidate), encoding="utf-8")
        temporary.replace(output_path)
    finally:
        temporary.unlink(missing_ok=True)
    return candidate


class ReleaseBundleMetadata(Protocol):
    @property
    def version(self) -> str: ...

    @property
    def release_date(self) -> str: ...

    @property
    def tag(self) -> str: ...

    @property
    def source_commit(self) -> str: ...

    @property
    def path(self) -> Path: ...

    @property
    def bytes(self) -> int: ...

    @property
    def sha256(self) -> str: ...

    @property
    def manifest_sha256(self) -> str: ...


def catalog_entry_from_bundle(
    bundle: ReleaseBundleMetadata,
    *,
    database_sha256: str,
    repository: str = "mryk814/optimization-compass",
    archival: ReleaseArchiveDescriptor | None = None,
) -> ReleaseCatalogEntry:
    if _REPOSITORY_PATTERN.fullmatch(repository) is None:
        raise ReleaseCatalogError("GitHub repository must use the owner/name form")
    asset_name = bundle.path.name
    if _ASSET_NAME_PATTERN.fullmatch(asset_name) is None:
        raise ReleaseCatalogError("release bundle asset name is not URL-safe")
    entry = ReleaseCatalogEntry(
        version=bundle.version,
        release_date=bundle.release_date,
        database_sha256=database_sha256,
        manifest_sha256=bundle.manifest_sha256,
        source_commit=bundle.source_commit,
        tag=bundle.tag,
        bundle=ReleaseBundleDescriptor(
            url=f"https://github.com/{repository}/releases/download/{bundle.tag}/{asset_name}",
            sha256=bundle.sha256,
            size_bytes=bundle.bytes,
        ),
        archival=archival,
    )
    _validate_entry(entry)
    return entry


def canonical_release_catalog_json(catalog: ReleaseCatalog) -> str:
    validate_release_catalog(catalog)
    return json.dumps(catalog.as_json_object(), ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _parse_release_catalog(payload: object) -> ReleaseCatalog:
    catalog_payload = _strict_object(payload, _CATALOG_FIELDS, "release catalog")
    if catalog_payload["schema_version"] != 1:
        raise ReleaseCatalogError("unsupported release catalog schema version")
    current_version = catalog_payload["current_version"]
    if current_version is not None and not isinstance(current_version, str):
        raise ReleaseCatalogError("release catalog current_version must be a string or null")
    releases_payload = catalog_payload["releases"]
    if not isinstance(releases_payload, list):
        raise ReleaseCatalogError("release catalog releases must be an array")
    return ReleaseCatalog(
        schema_version=1,
        current_version=current_version,
        releases=tuple(_parse_entry(item) for item in releases_payload),
    )


def _parse_entry(payload: object) -> ReleaseCatalogEntry:
    entry = _strict_object(payload, _ENTRY_FIELDS, "release catalog entry")
    archival_payload = entry["archival"]
    archival = None if archival_payload is None else _parse_archive(archival_payload)
    return ReleaseCatalogEntry(
        version=_required_string(entry, "version", "release catalog entry"),
        release_date=_required_string(entry, "release_date", "release catalog entry"),
        database_sha256=_required_string(entry, "database_sha256", "release catalog entry"),
        manifest_sha256=_required_string(entry, "manifest_sha256", "release catalog entry"),
        source_commit=_required_string(entry, "source_commit", "release catalog entry"),
        tag=_required_string(entry, "tag", "release catalog entry"),
        bundle=_parse_bundle(entry["bundle"]),
        archival=archival,
    )


def _parse_bundle(payload: object) -> ReleaseBundleDescriptor:
    bundle = _strict_object(payload, _BUNDLE_FIELDS, "release bundle")
    size_bytes = bundle["size_bytes"]
    if isinstance(size_bytes, bool) or not isinstance(size_bytes, int):
        raise ReleaseCatalogError("release bundle size_bytes must be an integer")
    return ReleaseBundleDescriptor(
        url=_required_string(bundle, "url", "release bundle"),
        sha256=_required_string(bundle, "sha256", "release bundle"),
        size_bytes=size_bytes,
    )


def _parse_archive(payload: object) -> ReleaseArchiveDescriptor:
    archive = _strict_object(payload, _ARCHIVE_FIELDS, "release archive")
    return ReleaseArchiveDescriptor(
        provider=_required_string(archive, "provider", "release archive"),
        identifier=_required_string(archive, "identifier", "release archive"),
        url=_required_string(archive, "url", "release archive"),
    )


def _validate_entry(entry: ReleaseCatalogEntry) -> None:
    try:
        validate_release_identity(entry.version, entry.release_date)
        validate_sha256(entry.database_sha256, "database_sha256")
        validate_sha256(entry.manifest_sha256, "manifest_sha256")
        validate_sha256(entry.bundle.sha256, "bundle.sha256")
    except ReleaseIdentityError as error:
        raise ReleaseCatalogError(str(error)) from error

    if _SOURCE_COMMIT_PATTERN.fullmatch(entry.source_commit) is None:
        raise ReleaseCatalogError(
            "release catalog source_commit must be 40 lowercase hex characters"
        )
    if entry.tag != f"v{entry.version}":
        raise ReleaseCatalogError("release catalog tag must equal v<version>")
    if isinstance(entry.bundle.size_bytes, bool) or entry.bundle.size_bytes <= 0:
        raise ReleaseCatalogError("release bundle size_bytes must be a positive integer")
    _validate_github_release_url(entry.bundle.url, entry.tag)
    if entry.archival is not None:
        if not entry.archival.provider or not entry.archival.identifier:
            raise ReleaseCatalogError("release archive provider and identifier must be non-empty")
        _validate_https_url(entry.archival.url, "release archive URL")


def _validate_github_release_url(url: str, expected_tag: str) -> None:
    parsed = _validate_https_url(url, "release bundle URL")
    if parsed.hostname != "github.com" or parsed.port is not None:
        raise ReleaseCatalogError("release bundle URL must use github.com")
    match = _GITHUB_RELEASE_PATH_PATTERN.fullmatch(parsed.path)
    if match is None or match.group("tag") != expected_tag:
        raise ReleaseCatalogError("release bundle URL must target the matching GitHub Release tag")


def _validate_https_url(url: str, label: str) -> ParseResult:
    parsed = urlparse(url)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
    ):
        raise ReleaseCatalogError(f"{label} must be a plain HTTPS URL")
    return parsed


def _semantic_version_key(version: str) -> tuple[int, int, int]:
    try:
        validate_semantic_version(version)
    except ReleaseIdentityError as error:
        raise ReleaseCatalogError(str(error)) from error
    major, minor, patch = version.split(".")
    return int(major), int(minor), int(patch)


def _strict_object(payload: object, fields: set[str], label: str) -> dict[str, Any]:
    if not isinstance(payload, dict) or set(payload) != fields:
        raise ReleaseCatalogError(f"{label} fields do not match schema")
    return payload


def _required_string(payload: dict[str, Any], field: str, label: str) -> str:
    value = payload[field]
    if not isinstance(value, str) or not value:
        raise ReleaseCatalogError(f"{label} field is invalid: {field}")
    return value
