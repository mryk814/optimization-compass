from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from optimization_compass.release_catalog import (
    ReleaseArchiveDescriptor,
    ReleaseBundleDescriptor,
    ReleaseCatalog,
    ReleaseCatalogEntry,
    ReleaseCatalogError,
    backfill_catalog_entries,
    canonical_release_catalog_json,
    catalog_entry_from_bundle,
    load_release_catalog,
    merge_catalog_entry,
    validate_release_catalog,
)
from optimization_compass.release_identity import DatasetReleaseIdentity


def _entry(version: str = "0.12.0") -> ReleaseCatalogEntry:
    return ReleaseCatalogEntry(
        version=version,
        release_date="2026-07-17",
        database_sha256="a" * 64,
        manifest_sha256="d" * 64,
        source_commit="b" * 40,
        tag=f"v{version}",
        bundle=ReleaseBundleDescriptor(
            url=(
                "https://github.com/mryk814/optimization-compass/releases/download/"
                f"v{version}/optimization_method_selection_database_v{version}_bundle.zip"
            ),
            sha256="c" * 64,
            size_bytes=1234,
        ),
        archival=None,
    )


def test_empty_release_catalog_is_an_offline_valid_start(tmp_path: Path) -> None:
    path = tmp_path / "release-catalog.json"
    path.write_text(
        json.dumps({"schema_version": 1, "current_version": None, "releases": []}),
        encoding="utf-8",
    )

    assert load_release_catalog(path) == ReleaseCatalog(1, None, ())


def test_catalog_requires_unique_semantically_sorted_versions() -> None:
    older = _entry("0.9.0")
    newer = _entry("0.10.0")

    validate_release_catalog(ReleaseCatalog(1, "0.10.0", (older, newer)))
    with pytest.raises(ReleaseCatalogError, match="sorted"):
        validate_release_catalog(ReleaseCatalog(1, "0.9.0", (newer, older)))
    with pytest.raises(ReleaseCatalogError, match="unique"):
        validate_release_catalog(ReleaseCatalog(1, "0.9.0", (older, older)))


def test_current_entry_must_match_release_identity() -> None:
    catalog = ReleaseCatalog(1, "0.12.0", (_entry(),))
    identity = DatasetReleaseIdentity(1, "0.12.0", "2026-07-17", "a" * 64)

    validate_release_catalog(catalog, identity)
    with pytest.raises(ReleaseCatalogError, match="current entry"):
        validate_release_catalog(catalog, replace(identity, database_sha256="d" * 64))


def test_archival_metadata_is_an_explicit_strict_object(tmp_path: Path) -> None:
    archival = ReleaseArchiveDescriptor(
        provider="Zenodo",
        identifier="10.5281/zenodo.123",
        url="https://doi.org/10.5281/zenodo.123",
    )
    catalog = ReleaseCatalog(1, "0.12.0", (replace(_entry(), archival=archival),))
    path = tmp_path / "catalog.json"
    path.write_text(canonical_release_catalog_json(catalog), encoding="utf-8")

    assert load_release_catalog(path) == catalog


def test_catalog_entry_is_derived_from_a_verified_bundle() -> None:
    bundle = SimpleNamespace(
        version="0.12.0",
        release_date="2026-07-17",
        tag="v0.12.0",
        source_commit="b" * 40,
        path=Path("optimization_method_selection_database_v0.12.0_bundle.zip"),
        bytes=1234,
        sha256="c" * 64,
        manifest_sha256="d" * 64,
    )

    entry = catalog_entry_from_bundle(bundle, database_sha256="a" * 64)

    assert entry == _entry()


@pytest.mark.parametrize(
    ("replacement", "message"),
    [
        ({"source_commit": "A" * 40}, "source_commit"),
        ({"tag": "dataset-0.12.0"}, "tag"),
        ({"database_sha256": "not-a-hash"}, "database_sha256"),
        ({"manifest_sha256": "not-a-hash"}, "manifest_sha256"),
        (
            {
                "bundle": ReleaseBundleDescriptor(
                    url="http://github.com/mryk814/optimization-compass/releases/download/v0.12.0/a.tgz",
                    sha256="c" * 64,
                    size_bytes=1234,
                )
            },
            "HTTPS",
        ),
        (
            {
                "bundle": ReleaseBundleDescriptor(
                    url="https://example.com/releases/download/v0.12.0/a.tgz",
                    sha256="c" * 64,
                    size_bytes=1234,
                )
            },
            "github.com",
        ),
        (
            {
                "bundle": ReleaseBundleDescriptor(
                    url=(
                        "https://github.com/mryk814/optimization-compass/releases/download/"
                        "v0.11.0/a.tgz"
                    ),
                    sha256="c" * 64,
                    size_bytes=1234,
                )
            },
            "matching GitHub Release tag",
        ),
    ],
)
def test_catalog_rejects_invalid_release_provenance(
    replacement: dict[str, object], message: str
) -> None:
    with pytest.raises(ReleaseCatalogError, match=message):
        validate_release_catalog(ReleaseCatalog(1, "0.12.0", (replace(_entry(), **replacement),)))


@pytest.mark.parametrize("scope", ["catalog", "entry", "bundle", "archive"])
def test_loader_rejects_unknown_fields_at_every_schema_level(tmp_path: Path, scope: str) -> None:
    payload = json.loads(canonical_release_catalog_json(ReleaseCatalog(1, "0.12.0", (_entry(),))))
    if scope == "catalog":
        payload["unknown"] = True
    elif scope == "entry":
        payload["releases"][0]["unknown"] = True
    elif scope == "bundle":
        payload["releases"][0]["bundle"]["unknown"] = True
    else:
        payload["releases"][0]["archival"] = {
            "provider": "Zenodo",
            "identifier": "10.5281/zenodo.123",
            "url": "https://doi.org/10.5281/zenodo.123",
            "unknown": True,
        }
    path = tmp_path / "catalog.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ReleaseCatalogError, match="fields"):
        load_release_catalog(path)


def test_merge_catalog_entry_is_sorted_idempotent_and_version_immutable(tmp_path: Path) -> None:
    source = tmp_path / "empty.json"
    source.write_text(canonical_release_catalog_json(ReleaseCatalog(1, None, ())), encoding="utf-8")
    output = tmp_path / "catalog.json"

    merged = merge_catalog_entry(source, _entry("0.12.0"), output)
    merge_catalog_entry(output, _entry("0.12.0"), output)

    assert load_release_catalog(output) == merged
    with pytest.raises(ReleaseCatalogError, match="immutable"):
        merge_catalog_entry(output, replace(_entry("0.12.0"), source_commit="d" * 40), output)


def test_historical_backfill_preserves_current_and_is_idempotent(tmp_path: Path) -> None:
    current = _entry("0.15.1")
    source = tmp_path / "catalog.json"
    source.write_text(
        canonical_release_catalog_json(ReleaseCatalog(1, "0.15.1", (current,))),
        encoding="utf-8",
    )
    output = tmp_path / "candidate.json"
    historical = (_entry("0.2.0"), _entry("0.12.0"))

    candidate = backfill_catalog_entries(source, historical, output)
    replayed = backfill_catalog_entries(output, historical, output)

    assert candidate == replayed
    assert replayed.current_version == "0.15.1"
    assert [entry.version for entry in replayed.releases] == ["0.2.0", "0.12.0", "0.15.1"]


def test_historical_backfill_rejects_conflict_without_writing_candidate(tmp_path: Path) -> None:
    historical = _entry("0.12.0")
    current = _entry("0.15.1")
    source = tmp_path / "catalog.json"
    source.write_text(
        canonical_release_catalog_json(ReleaseCatalog(1, "0.15.1", (historical, current))),
        encoding="utf-8",
    )
    output = tmp_path / "candidate.json"

    with pytest.raises(ReleaseCatalogError, match="immutable"):
        backfill_catalog_entries(
            source,
            (replace(historical, source_commit="d" * 40),),
            output,
        )

    assert not output.exists()


def test_historical_backfill_cannot_advance_current(tmp_path: Path) -> None:
    source = tmp_path / "catalog.json"
    source.write_text(
        canonical_release_catalog_json(ReleaseCatalog(1, "0.15.1", (_entry("0.15.1"),))),
        encoding="utf-8",
    )

    with pytest.raises(ReleaseCatalogError, match="advance current"):
        backfill_catalog_entries(source, (_entry("0.16.0"),), tmp_path / "candidate.json")
