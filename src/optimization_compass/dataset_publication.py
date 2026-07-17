from __future__ import annotations

import hashlib
import json
import re
import shutil
import tempfile
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

from optimization_compass.dataset_release import DATASET_STEM, ROOT
from optimization_compass.release_bundle import ReleaseBundleError, verify_release_bundle
from optimization_compass.release_catalog import (
    ReleaseArchiveDescriptor,
    ReleaseCatalog,
    ReleaseCatalogEntry,
    load_release_catalog,
)
from optimization_compass.repository_boundaries import (
    RepositoryBoundaryError,
    ensure_external_output_path,
)

PUBLICATION_AUTHORITY_PATH = ROOT / "data/releases/publication-authority.json"
RELEASE_CATALOG_PATH = ROOT / "data/releases/catalog.json"
CITATION_PATH = ROOT / "CITATION.cff"
DATASET_CARD_PATH = ROOT / "docs/dataset-card.md"
PUBLICATION_SCHEMA_VERSION = 1
PUBLICATION_OUTPUT_FILES = frozenset(
    {"CITATION.cff", "DATASET_CARD.md", "publication-metadata.json"}
)
_AUTHORITY_FIELDS = {
    "schema_version",
    "title",
    "abstract_ja",
    "abstract_en",
    "creators",
    "keywords",
    "license",
    "repository_url",
    "homepage_url",
    "primary_language",
    "canonical_terms_language",
    "coverage_limitations",
    "non_guarantees",
    "attribution",
}
_CREATOR_FIELDS = {"name"}
_DOI_PATTERN = re.compile(r"10\.[0-9]{4,9}/[-._;()/:A-Za-z0-9]+")


class DatasetPublicationError(ValueError):
    pass


@dataclass(frozen=True)
class PublicationCreator:
    name: str


@dataclass(frozen=True)
class PublicationAuthority:
    schema_version: int
    title: str
    abstract_ja: str
    abstract_en: str
    creators: tuple[PublicationCreator, ...]
    keywords: tuple[str, ...]
    license: str
    repository_url: str
    homepage_url: str
    primary_language: str
    canonical_terms_language: str
    coverage_limitations: tuple[str, ...]
    non_guarantees: tuple[str, ...]
    attribution: str


@dataclass(frozen=True)
class PreparedPublication:
    version: str
    output_directory: Path
    file_sha256: dict[str, str]


def load_publication_authority(path: Path = PUBLICATION_AUTHORITY_PATH) -> PublicationAuthority:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise DatasetPublicationError(f"publication authority is not valid JSON: {path}") from error
    authority_payload = _strict_object(payload, _AUTHORITY_FIELDS, "publication authority")
    schema_version = authority_payload["schema_version"]
    if isinstance(schema_version, bool) or schema_version != PUBLICATION_SCHEMA_VERSION:
        raise DatasetPublicationError("unsupported publication authority schema version")
    creators_payload = authority_payload["creators"]
    if not isinstance(creators_payload, list) or not creators_payload:
        raise DatasetPublicationError("publication authority creators must be a non-empty array")
    creators = tuple(
        PublicationCreator(
            name=_required_string(
                _strict_object(item, _CREATOR_FIELDS, "publication creator"),
                "name",
                "publication creator",
            )
        )
        for item in creators_payload
    )
    authority = PublicationAuthority(
        schema_version=PUBLICATION_SCHEMA_VERSION,
        title=_required_string(authority_payload, "title", "publication authority"),
        abstract_ja=_required_string(authority_payload, "abstract_ja", "publication authority"),
        abstract_en=_required_string(authority_payload, "abstract_en", "publication authority"),
        creators=creators,
        keywords=_string_tuple(authority_payload, "keywords"),
        license=_required_string(authority_payload, "license", "publication authority"),
        repository_url=_required_string(
            authority_payload, "repository_url", "publication authority"
        ),
        homepage_url=_required_string(authority_payload, "homepage_url", "publication authority"),
        primary_language=_required_string(
            authority_payload, "primary_language", "publication authority"
        ),
        canonical_terms_language=_required_string(
            authority_payload, "canonical_terms_language", "publication authority"
        ),
        coverage_limitations=_string_tuple(authority_payload, "coverage_limitations"),
        non_guarantees=_string_tuple(authority_payload, "non_guarantees"),
        attribution=_required_string(authority_payload, "attribution", "publication authority"),
    )
    _validate_publication_authority(authority)
    return authority


def select_release_entry(
    catalog: ReleaseCatalog, version: str | None = None
) -> ReleaseCatalogEntry:
    selected_version = catalog.current_version if version is None else version
    if selected_version is None:
        raise DatasetPublicationError("release catalog has no current publication candidate")
    entry = next((item for item in catalog.releases if item.version == selected_version), None)
    if entry is None:
        raise DatasetPublicationError(
            f"release version is not present in catalog: {selected_version}"
        )
    return entry


def render_citation_cff(
    authority: PublicationAuthority,
    entry: ReleaseCatalogEntry,
) -> str:
    lines = [
        "# Generated from data/releases/publication-authority.json and data/releases/catalog.json.",
        "# Run `uv run python scripts/dataset_publication.py check` before committing.",
        'cff-version: "1.2.0"',
        f"message: {_yaml_string('If you use this dataset, please cite this exact version.')}",
        f"title: {_yaml_string(authority.title)}",
        "type: dataset",
        f"abstract: {_yaml_string(authority.abstract_en)}",
        "authors:",
    ]
    lines.extend(f"  - name: {_yaml_string(creator.name)}" for creator in authority.creators)
    lines.extend(
        [
            f"version: {_yaml_string(entry.version)}",
            f"date-released: {_yaml_string(entry.release_date)}",
            f"commit: {_yaml_string(entry.source_commit)}",
            f"license: {_yaml_string(authority.license)}",
            f"repository-code: {_yaml_string(authority.repository_url)}",
            f"repository-artifact: {_yaml_string(entry.bundle.url)}",
            f"url: {_yaml_string(authority.homepage_url)}",
        ]
    )
    doi = _version_doi(entry.archival)
    if doi is not None:
        lines.extend(
            [
                "identifiers:",
                f"  - description: {_yaml_string(f'Version DOI for dataset {entry.version}')}",
                "    type: doi",
                f"    value: {_yaml_string(doi)}",
            ]
        )
    lines.append("keywords:")
    lines.extend(f"  - {_yaml_string(keyword)}" for keyword in authority.keywords)
    return "\n".join(lines) + "\n"


def render_dataset_card(
    authority: PublicationAuthority,
    entry: ReleaseCatalogEntry,
) -> str:
    archive = (
        "未登録（この版はGitHub Release bundleでhash検証できます）"
        if entry.archival is None
        else f"[{entry.archival.provider}: {entry.archival.identifier}]({entry.archival.url})"
    )
    creators = ", ".join(creator.name for creator in authority.creators)
    coverage = "\n".join(f"- {item}" for item in authority.coverage_limitations)
    non_guarantees = "\n".join(f"- {item}" for item in authority.non_guarantees)
    commit_url = f"{authority.repository_url}/commit/{entry.source_commit}"
    tag_url = f"{authority.repository_url}/releases/tag/{entry.tag}"
    source_audit_url = (
        f"{authority.repository_url}/blob/{entry.source_commit}/THIRD_PARTY_SOURCE_AUDIT.md"
    )
    return f"""<!-- Generated publication metadata; do not edit release facts. -->
<!-- Run `uv run python scripts/dataset_publication.py check` before committing. -->

# {authority.title}

{authority.abstract_ja}

{authority.abstract_en}

## Release identity

| Field | Value |
|---|---|
| Dataset version | `{entry.version}` |
| Release date | `{entry.release_date}` |
| Source commit | [`{entry.source_commit}`]({commit_url}) |
| Source tag | [`{entry.tag}`]({tag_url}) |
| Database SHA-256 | `{entry.database_sha256}` |
| Manifest SHA-256 | `{entry.manifest_sha256}` |
| Complete bundle | [download]({entry.bundle.url}) ({entry.bundle.size_bytes:,} bytes) |
| Bundle SHA-256 | `{entry.bundle.sha256}` |
| Citable archive | {archive} |

The complete bundle contains the released SQLite, JSON, JSONL, CSV, Excel, SQL schema,
release report, site-data, manifest, and license/notice files. Its `bundle-index.json` and
canonical release manifest fix the byte count and SHA-256 of every member.

## Scope and evidence model

Optimization Compass records problem structure, methods, implementations, examples,
comparisons, learning artifacts, sources, evidence links, and explicit support states.
It preserves the distinction between a method and an implementation, and between
`unknown`, `not_applicable`, and `unsupported`.
It is intended for research, education, and traceable exploration rather than context-free ranking.

## Language position

Japanese (`{authority.primary_language}`) is the primary explanatory language.
Canonical English (`{authority.canonical_terms_language}`) technical terms, aliases,
source titles, APIs, and stable IDs remain visible and searchable. English metadata does not
imply complete English-language articles.

## Coverage limits

{coverage}

## Non-guarantees

{non_guarantees}

## Licensing and attribution

- Dataset and distributed structured data: `{authority.license}`.
- Creator metadata: {creators}.
- Attribution: {authority.attribution}
- Third-party papers, documentation, repositories, standards, product names, and linked works retain
  their own rights. See the bundle's `licenses/NOTICE.txt` and the source audit at
  [{source_audit_url}]({source_audit_url}).

## Citation

Use the repository `CITATION.cff`. It is generated from the same publication authority
and release catalog as this card, so version, release date, source commit, download URL,
and registered DOI cannot drift independently.
"""


def publication_metadata_object(
    authority: PublicationAuthority,
    entry: ReleaseCatalogEntry,
) -> dict[str, object]:
    return {
        "abstract": {"en": authority.abstract_en, "ja": authority.abstract_ja},
        "archival": None if entry.archival is None else asdict(entry.archival),
        "attribution": authority.attribution,
        "bundle": asdict(entry.bundle),
        "coverage_limitations": list(authority.coverage_limitations),
        "creators": [asdict(creator) for creator in authority.creators],
        "database_sha256": entry.database_sha256,
        "homepage_url": authority.homepage_url,
        "keywords": list(authority.keywords),
        "language": {
            "canonical_terms": authority.canonical_terms_language,
            "primary": authority.primary_language,
        },
        "license": authority.license,
        "manifest_sha256": entry.manifest_sha256,
        "non_guarantees": list(authority.non_guarantees),
        "release_date": entry.release_date,
        "repository_url": authority.repository_url,
        "schema_version": PUBLICATION_SCHEMA_VERSION,
        "source_commit": entry.source_commit,
        "tag": entry.tag,
        "title": authority.title,
        "version": entry.version,
    }


def canonical_publication_metadata_json(
    authority: PublicationAuthority,
    entry: ReleaseCatalogEntry,
) -> str:
    return (
        json.dumps(
            publication_metadata_object(authority, entry),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


def verify_publication_bundle(bundle_path: Path, entry: ReleaseCatalogEntry) -> None:
    try:
        verified = verify_release_bundle(bundle_path)
    except ReleaseBundleError as error:
        raise DatasetPublicationError(str(error)) from error
    expected = {
        "version": entry.version,
        "release_date": entry.release_date,
        "tag": entry.tag,
        "source_commit": entry.source_commit,
        "size_bytes": entry.bundle.size_bytes,
        "sha256": entry.bundle.sha256,
        "manifest_sha256": entry.manifest_sha256,
    }
    actual = {
        "version": verified.version,
        "release_date": verified.release_date,
        "tag": verified.tag,
        "source_commit": verified.source_commit,
        "size_bytes": verified.bytes,
        "sha256": verified.sha256,
        "manifest_sha256": verified.manifest_sha256,
    }
    mismatched = [field for field in expected if expected[field] != actual[field]]
    if mismatched:
        raise DatasetPublicationError(
            "release bundle differs from catalog: " + ", ".join(sorted(mismatched))
        )
    asset_name = Path(unquote(urlparse(entry.bundle.url).path)).name
    if bundle_path.name != asset_name:
        raise DatasetPublicationError("release bundle filename differs from catalog URL")
    try:
        with zipfile.ZipFile(bundle_path) as archive:
            index = json.loads(archive.read("bundle-index.json"))
    except (OSError, zipfile.BadZipFile, KeyError, json.JSONDecodeError) as error:
        raise DatasetPublicationError("release bundle index cannot be inspected") from error
    if not isinstance(index, dict) or not isinstance(index.get("files"), dict):
        raise DatasetPublicationError("release bundle file inventory is invalid")
    database_path = f"{DATASET_STEM.format(version=entry.version)}.sqlite"
    descriptor = index["files"].get(database_path)
    if not isinstance(descriptor, dict) or descriptor.get("sha256") != entry.database_sha256:
        raise DatasetPublicationError("release bundle database hash differs from catalog")


def prepare_publication(
    *,
    bundle_path: Path,
    output_directory: Path,
    authority_path: Path = PUBLICATION_AUTHORITY_PATH,
    catalog_path: Path = RELEASE_CATALOG_PATH,
    version: str | None = None,
) -> PreparedPublication:
    authority = load_publication_authority(authority_path)
    entry = select_release_entry(load_release_catalog(catalog_path), version)
    verify_publication_bundle(bundle_path, entry)
    try:
        output = ensure_external_output_path(output_directory, repository_root=ROOT)
    except RepositoryBoundaryError as error:
        raise DatasetPublicationError(
            f"publication output must be outside the repository: {error}"
        ) from error
    rendered = _rendered_publication_files(authority, entry)
    if output.exists():
        _verify_existing_output(output, rendered)
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        temporary = Path(tempfile.mkdtemp(prefix=f".{output.name}-", dir=output.parent))
        try:
            for name, content in rendered.items():
                (temporary / name).write_bytes(content)
            temporary.replace(output)
        except BaseException:
            shutil.rmtree(temporary, ignore_errors=True)
            raise
    return PreparedPublication(
        version=entry.version,
        output_directory=output,
        file_sha256={
            name: hashlib.sha256(content).hexdigest() for name, content in rendered.items()
        },
    )


def check_repository_publication_metadata(
    *,
    authority_path: Path = PUBLICATION_AUTHORITY_PATH,
    catalog_path: Path = RELEASE_CATALOG_PATH,
    citation_path: Path = CITATION_PATH,
    dataset_card_path: Path = DATASET_CARD_PATH,
) -> None:
    authority = load_publication_authority(authority_path)
    entry = select_release_entry(load_release_catalog(catalog_path))
    expected = {
        citation_path: render_citation_cff(authority, entry),
        dataset_card_path: render_dataset_card(authority, entry),
    }
    stale = [str(path) for path, content in expected.items() if _read_text(path) != content]
    if stale:
        raise DatasetPublicationError(
            "repository publication metadata is stale: " + ", ".join(stale)
        )


def _rendered_publication_files(
    authority: PublicationAuthority,
    entry: ReleaseCatalogEntry,
) -> dict[str, bytes]:
    return {
        "CITATION.cff": render_citation_cff(authority, entry).encode("utf-8"),
        "DATASET_CARD.md": render_dataset_card(authority, entry).encode("utf-8"),
        "publication-metadata.json": canonical_publication_metadata_json(authority, entry).encode(
            "utf-8"
        ),
    }


def _verify_existing_output(output: Path, expected: dict[str, bytes]) -> None:
    if not output.is_dir():
        raise DatasetPublicationError("publication output exists and is not a directory")
    actual_names = {path.name for path in output.iterdir() if path.is_file()}
    if actual_names != PUBLICATION_OUTPUT_FILES or any(path.is_dir() for path in output.iterdir()):
        raise DatasetPublicationError("publication output contains unexpected files")
    mismatched = [
        name for name, content in expected.items() if (output / name).read_bytes() != content
    ]
    if mismatched:
        raise DatasetPublicationError(
            "publication output differs from requested release: " + ", ".join(sorted(mismatched))
        )


def _validate_publication_authority(authority: PublicationAuthority) -> None:
    if authority.license != "CC-BY-4.0":
        raise DatasetPublicationError("dataset publication license must be CC-BY-4.0")
    _validate_https_url(authority.repository_url, "repository_url")
    _validate_https_url(authority.homepage_url, "homepage_url")
    if authority.primary_language != "ja" or authority.canonical_terms_language != "en":
        raise DatasetPublicationError(
            "publication language position must be Japanese-first and English-term-aware"
        )
    creator_names = [creator.name for creator in authority.creators]
    if len(creator_names) != len(set(creator_names)):
        raise DatasetPublicationError("publication creators must be unique")
    if len(authority.keywords) != len(set(authority.keywords)):
        raise DatasetPublicationError("publication keywords must be unique")
    if len(authority.coverage_limitations) != len(set(authority.coverage_limitations)):
        raise DatasetPublicationError("publication coverage limitations must be unique")
    if len(authority.non_guarantees) != len(set(authority.non_guarantees)):
        raise DatasetPublicationError("publication non-guarantees must be unique")


def _version_doi(archival: ReleaseArchiveDescriptor | None) -> str | None:
    if archival is None:
        return None
    if (
        archival.provider.casefold() != "zenodo"
        or _DOI_PATTERN.fullmatch(archival.identifier) is None
    ):
        raise DatasetPublicationError(
            "registered citable archive must provide a Zenodo version DOI"
        )
    parsed = urlparse(archival.url)
    if parsed.hostname != "doi.org" or unquote(parsed.path).lstrip("/") != archival.identifier:
        raise DatasetPublicationError("Zenodo archive URL must resolve its exact version DOI")
    return archival.identifier


def _validate_https_url(url: str, label: str) -> None:
    parsed = urlparse(url)
    try:
        port = parsed.port
    except ValueError as error:
        raise DatasetPublicationError(f"{label} must be a plain HTTPS URL") from error
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or port is not None
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
    ):
        raise DatasetPublicationError(f"{label} must be a plain HTTPS URL")


def _string_tuple(payload: dict[str, Any], field: str) -> tuple[str, ...]:
    value = payload[field]
    if not isinstance(value, list) or not value:
        raise DatasetPublicationError(f"publication authority {field} must be a non-empty array")
    result = tuple(value)
    if any(not isinstance(item, str) or not item.strip() for item in result):
        raise DatasetPublicationError(f"publication authority {field} contains an invalid string")
    return result


def _strict_object(payload: object, fields: set[str], label: str) -> dict[str, Any]:
    if not isinstance(payload, dict) or set(payload) != fields:
        raise DatasetPublicationError(f"{label} fields do not match schema")
    return payload


def _required_string(payload: dict[str, Any], field: str, label: str) -> str:
    value = payload[field]
    if not isinstance(value, str) or not value.strip():
        raise DatasetPublicationError(f"{label} field is invalid: {field}")
    return value


def _yaml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None
