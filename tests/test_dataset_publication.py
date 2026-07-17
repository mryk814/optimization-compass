from __future__ import annotations

import hashlib
import json
import zipfile
from dataclasses import replace
from pathlib import Path

import pytest
import yaml

import optimization_compass.dataset_publication as publication
from optimization_compass.dataset_publication import (
    CITATION_PATH,
    DATASET_CARD_PATH,
    DatasetPublicationError,
    canonical_publication_metadata_json,
    check_repository_publication_metadata,
    load_publication_authority,
    prepare_publication,
    render_citation_cff,
    render_dataset_card,
    select_release_entry,
    verify_publication_bundle,
)
from optimization_compass.release_bundle import ReleaseBundle
from optimization_compass.release_catalog import (
    ReleaseArchiveDescriptor,
    ReleaseBundleDescriptor,
    ReleaseCatalog,
    ReleaseCatalogEntry,
    canonical_release_catalog_json,
    load_release_catalog,
)


def _entry(version: str = "0.15.1") -> ReleaseCatalogEntry:
    asset_name = f"optimization_method_selection_database_v{version}_bundle.zip"
    return ReleaseCatalogEntry(
        version=version,
        release_date="2026-07-17",
        database_sha256="a" * 64,
        manifest_sha256="b" * 64,
        source_commit="c" * 40,
        tag=f"v{version}",
        bundle=ReleaseBundleDescriptor(
            url=(
                "https://github.com/mryk814/optimization-compass/releases/download/"
                f"v{version}/{asset_name}"
            ),
            sha256="d" * 64,
            size_bytes=1234,
        ),
        archival=None,
    )


def _fake_verified_bundle(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    entry: ReleaseCatalogEntry,
) -> tuple[Path, ReleaseCatalogEntry]:
    bundle_path = tmp_path / Path(entry.bundle.url).name
    database_path = f"optimization_method_selection_database_v{entry.version}.sqlite"
    index = {
        "files": {
            database_path: {
                "bytes": 10,
                "sha256": entry.database_sha256,
            }
        }
    }
    with zipfile.ZipFile(bundle_path, "w") as archive:
        archive.writestr("bundle-index.json", json.dumps(index))
    digest = hashlib.sha256(bundle_path.read_bytes()).hexdigest()
    matching = replace(
        entry,
        bundle=replace(
            entry.bundle,
            sha256=digest,
            size_bytes=bundle_path.stat().st_size,
        ),
    )
    monkeypatch.setattr(
        publication,
        "verify_release_bundle",
        lambda _path: ReleaseBundle(
            version=matching.version,
            release_date=matching.release_date,
            tag=matching.tag,
            source_commit=matching.source_commit,
            path=bundle_path,
            bytes=bundle_path.stat().st_size,
            sha256=digest,
            manifest_sha256=matching.manifest_sha256,
        ),
    )
    return bundle_path, matching


def test_current_repository_metadata_is_generated_from_current_catalog() -> None:
    authority = load_publication_authority()
    entry = select_release_entry(load_release_catalog(publication.RELEASE_CATALOG_PATH))

    assert CITATION_PATH.read_text(encoding="utf-8") == render_citation_cff(authority, entry)
    assert DATASET_CARD_PATH.read_text(encoding="utf-8") == render_dataset_card(authority, entry)
    citation = yaml.safe_load(CITATION_PATH.read_text(encoding="utf-8"))
    assert citation["cff-version"] == "1.2.0"
    assert citation["type"] == "dataset"
    assert citation["authors"] == [{"name": "TAKUYA OTANI"}]
    assert citation["version"] == entry.version
    check_repository_publication_metadata()


def test_publication_authority_is_strict_and_does_not_invent_person_metadata(
    tmp_path: Path,
) -> None:
    payload = json.loads(publication.PUBLICATION_AUTHORITY_PATH.read_text(encoding="utf-8"))
    assert payload["creators"] == [{"name": "TAKUYA OTANI"}]

    payload["creators"][0]["orcid"] = "0000-0000-0000-0000"
    path = tmp_path / "authority.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(DatasetPublicationError, match="creator fields"):
        load_publication_authority(path)

    del payload["creators"][0]["orcid"]
    payload["unreviewed_field"] = True
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(DatasetPublicationError, match="authority fields"):
        load_publication_authority(path)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("license", "CC0-1.0", "CC-BY-4.0"),
        ("repository_url", "http://example.com/project", "HTTPS"),
        ("primary_language", "en", "Japanese-first"),
        ("keywords", ["optimization", "optimization"], "keywords must be unique"),
        ("schema_version", True, "schema version"),
    ],
)
def test_publication_authority_rejects_invalid_contract_values(
    tmp_path: Path,
    field: str,
    value: object,
    message: str,
) -> None:
    payload = json.loads(publication.PUBLICATION_AUTHORITY_PATH.read_text(encoding="utf-8"))
    payload[field] = value
    path = tmp_path / "authority.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(DatasetPublicationError, match=message):
        load_publication_authority(path)


def test_citation_and_metadata_add_only_an_exact_zenodo_version_doi() -> None:
    authority = load_publication_authority()
    without_archive = _entry()
    assert "identifiers:" not in render_citation_cff(authority, without_archive)
    assert (
        canonical_publication_metadata_json(authority, without_archive).count('"archival": null')
        == 1
    )

    archived = replace(
        without_archive,
        archival=ReleaseArchiveDescriptor(
            provider="Zenodo",
            identifier="10.5281/zenodo.1234567",
            url="https://doi.org/10.5281/zenodo.1234567",
        ),
    )
    citation = render_citation_cff(authority, archived)
    assert 'value: "10.5281/zenodo.1234567"' in citation
    assert "[Zenodo: 10.5281/zenodo.1234567]" in render_dataset_card(authority, archived)

    invalid = replace(
        without_archive,
        archival=ReleaseArchiveDescriptor(
            provider="Zenodo",
            identifier="record-123",
            url="https://zenodo.org/records/123",
        ),
    )
    with pytest.raises(DatasetPublicationError, match="version DOI"):
        render_citation_cff(authority, invalid)


def test_bundle_must_match_every_catalog_identity_before_preparation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bundle_path, entry = _fake_verified_bundle(tmp_path, monkeypatch, _entry())
    verify_publication_bundle(bundle_path, entry)

    with pytest.raises(DatasetPublicationError, match="size_bytes"):
        verify_publication_bundle(
            bundle_path,
            replace(entry, bundle=replace(entry.bundle, size_bytes=entry.bundle.size_bytes + 1)),
        )
    with pytest.raises(DatasetPublicationError, match="database hash"):
        verify_publication_bundle(
            bundle_path,
            replace(entry, database_sha256="e" * 64),
        )


def test_prepare_is_external_deterministic_and_idempotent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bundle_path, entry = _fake_verified_bundle(tmp_path, monkeypatch, _entry())
    catalog_path = tmp_path / "catalog.json"
    catalog_path.write_text(
        canonical_release_catalog_json(ReleaseCatalog(1, entry.version, (entry,))),
        encoding="utf-8",
    )
    output = tmp_path / "prepared"

    first = prepare_publication(
        bundle_path=bundle_path,
        output_directory=output,
        catalog_path=catalog_path,
    )
    second = prepare_publication(
        bundle_path=bundle_path,
        output_directory=output,
        catalog_path=catalog_path,
    )

    assert first.file_sha256 == second.file_sha256
    assert {path.name for path in output.iterdir()} == publication.PUBLICATION_OUTPUT_FILES
    metadata = json.loads((output / "publication-metadata.json").read_text(encoding="utf-8"))
    assert metadata["coverage_limitations"]
    assert metadata["non_guarantees"]
    assert metadata["bundle"]["sha256"] == entry.bundle.sha256
    (output / "unexpected.txt").write_text("not part of the contract", encoding="utf-8")
    with pytest.raises(DatasetPublicationError, match="unexpected files"):
        prepare_publication(
            bundle_path=bundle_path,
            output_directory=output,
            catalog_path=catalog_path,
        )


def test_prepare_rejects_repository_local_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bundle_path, entry = _fake_verified_bundle(tmp_path, monkeypatch, _entry())
    catalog_path = tmp_path / "catalog.json"
    catalog_path.write_text(
        canonical_release_catalog_json(ReleaseCatalog(1, entry.version, (entry,))),
        encoding="utf-8",
    )

    with pytest.raises(DatasetPublicationError, match="outside the repository"):
        prepare_publication(
            bundle_path=bundle_path,
            output_directory=publication.ROOT / "forbidden-publication-output",
            catalog_path=catalog_path,
        )


def test_unknown_release_version_is_not_inferred() -> None:
    with pytest.raises(DatasetPublicationError, match="not present"):
        select_release_entry(ReleaseCatalog(1, "0.15.1", (_entry(),)), "9.9.9")
