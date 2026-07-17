from __future__ import annotations

import hashlib
import io
import json
import re
import shutil
import subprocess
import tempfile
import zipfile
from collections.abc import Callable
from contextlib import AbstractContextManager
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Protocol, cast
from urllib.parse import urlparse
from urllib.request import urlopen

from optimization_compass.dataset_release import DATASET_STEM, ROOT, sha256_file
from optimization_compass.release_bundle import (
    BUNDLE_INDEX_NAME,
    BUNDLE_SCHEMA_VERSION,
    ReleaseBundle,
    _build_preverified_release_bundle,
)
from optimization_compass.release_catalog import (
    ReleaseCatalogEntry,
    backfill_catalog_entries,
    catalog_entry_from_bundle,
    load_release_catalog,
)
from optimization_compass.release_identity import (
    validate_release_identity,
    validate_semantic_version,
    validate_sha256,
)
from optimization_compass.repository_boundaries import (
    RepositoryBoundaryError,
    ensure_external_output_path,
)

_COMMIT_PATTERN = re.compile(r"[0-9a-f]{40}")
_REPOSITORY_PATTERN = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")
_REMOTE_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._/-]*")
_PLAN_FIELDS = {"schema_version", "repository", "releases"}
_ENTRY_FIELDS = {
    "version",
    "release_date",
    "source_commit",
    "reconstruction_commit",
    "tag",
    "verification_profile",
    "materialization_profile",
    "manifest_sha256",
    "database_sha256",
    "supplemental_files",
}
_SUPPLEMENTAL_FIELDS = {"bundle_path", "git_path", "sha256"}
_PROFILES = frozenset({"legacy-v0.2", "manifest-v2"})
_MATERIALIZATION_PROFILES = frozenset({"git-blob-v1", "manifest-crlf-v1"})
_REMOTE_TIMEOUT_SECONDS = 30.0
_LEGACY_LICENSE_PATHS = frozenset(
    {
        "licenses/CC-BY-4.0.txt",
        "licenses/CONTENT_LICENSE.txt",
        "licenses/DATA_LICENSE.txt",
        "licenses/LICENSE.txt",
        "licenses/NOTICE.txt",
    }
)


class HistoricalReleaseError(ValueError):
    pass


@dataclass(frozen=True)
class SupplementalFile:
    bundle_path: str
    git_path: str
    sha256: str


@dataclass(frozen=True)
class HistoricalReleasePlanEntry:
    version: str
    release_date: str
    source_commit: str
    reconstruction_commit: str
    tag: str
    verification_profile: str
    materialization_profile: str
    manifest_sha256: str
    database_sha256: str
    supplemental_files: tuple[SupplementalFile, ...]


@dataclass(frozen=True)
class HistoricalBackfillPlan:
    schema_version: int
    repository: str
    releases: tuple[HistoricalReleasePlanEntry, ...]


class _UrlResponse(Protocol):
    headers: Any

    def read(self, amount: int = -1) -> bytes: ...

    def geturl(self) -> str: ...


UrlOpener = Callable[[str], AbstractContextManager[_UrlResponse]]


def _open_remote_url(url: str) -> AbstractContextManager[_UrlResponse]:
    return cast(
        AbstractContextManager[_UrlResponse],
        urlopen(url, timeout=_REMOTE_TIMEOUT_SECONDS),
    )


def load_historical_backfill_plan(path: Path) -> HistoricalBackfillPlan:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise HistoricalReleaseError(
            f"historical backfill plan is not valid JSON: {path}"
        ) from error
    plan_payload = _strict_object(payload, _PLAN_FIELDS, "historical backfill plan")
    if plan_payload["schema_version"] != 1:
        raise HistoricalReleaseError("unsupported historical backfill plan schema version")
    repository = _required_string(plan_payload, "repository", "historical backfill plan")
    if _REPOSITORY_PATTERN.fullmatch(repository) is None:
        raise HistoricalReleaseError("historical backfill repository must use owner/name")
    releases_payload = plan_payload["releases"]
    if not isinstance(releases_payload, list) or not releases_payload:
        raise HistoricalReleaseError("historical backfill plan must contain releases")
    releases = tuple(_parse_plan_entry(item) for item in releases_payload)
    versions = [entry.version for entry in releases]
    if len(versions) != len(set(versions)):
        raise HistoricalReleaseError("historical backfill versions must be unique")
    if versions != sorted(versions, key=_version_key):
        raise HistoricalReleaseError("historical backfill versions must be semantically sorted")
    return HistoricalBackfillPlan(1, repository, releases)


def prepare_historical_backfill(
    repository_root: Path,
    plan_path: Path,
    catalog_path: Path,
    output_directory: Path,
) -> dict[str, object]:
    """Prepare every reviewed historical bundle and a non-current catalog overlay atomically."""

    root = repository_root.resolve()
    plan = load_historical_backfill_plan(plan_path)
    try:
        output_directory = ensure_external_output_path(
            output_directory,
            repository_root=root,
        )
    except RepositoryBoundaryError as error:
        raise HistoricalReleaseError(str(error)) from error
    if output_directory.exists():
        raise HistoricalReleaseError(
            f"historical backfill output already exists: {output_directory}"
        )
    output_directory.parent.mkdir(parents=True, exist_ok=True)
    transaction = Path(
        tempfile.mkdtemp(prefix=f".{output_directory.name}.", dir=output_directory.parent)
    )
    bundles: list[ReleaseBundle] = []
    transformations: dict[str, tuple[str, ...]] = {}
    tag_targets: dict[str, str | None] = {}
    try:
        tree_root = transaction / ".release-trees"
        tree_root.mkdir()
        for plan_entry in plan.releases:
            tag_targets[plan_entry.version] = _verify_tag_relationship(root, plan_entry)
            release_tree = tree_root / DATASET_STEM.format(version=plan_entry.version)
            transformations[plan_entry.version] = reconstruct_historical_release_tree(
                root, plan_entry, release_tree
            )
            verify_historical_release_tree(release_tree, plan_entry)
            bundle = _build_preverified_release_bundle(
                release_tree,
                transaction,
                version=plan_entry.version,
                release_date=plan_entry.release_date,
                source_commit=plan_entry.source_commit,
                tag=plan_entry.tag,
                manifest_path=release_tree
                / f"{DATASET_STEM.format(version=plan_entry.version)}_manifest.json",
                repository_root=root,
            )
            verified = verify_historical_release_bundle(bundle.path, plan_entry)
            if verified != bundle:
                raise HistoricalReleaseError(
                    f"historical bundle verification metadata differs: {plan_entry.version}"
                )
            bundles.append(bundle)
            shutil.rmtree(release_tree)
        tree_root.rmdir()

        entries = tuple(
            catalog_entry_from_bundle(
                bundle,
                database_sha256=plan_entry.database_sha256,
                repository=plan.repository,
            )
            for plan_entry, bundle in zip(plan.releases, bundles, strict=True)
        )
        candidate_path = transaction / "catalog.candidate.json"
        candidate = backfill_catalog_entries(catalog_path, entries, candidate_path)
        report = {
            "schema_version": 1,
            "plan_sha256": hashlib.sha256(_canonical_json(asdict(plan))).hexdigest(),
            "catalog_current_version": candidate.current_version,
            "release_count": len(bundles),
            "bundles": [
                {
                    "version": item.version,
                    "tag": item.tag,
                    "source_commit": item.source_commit,
                    "reconstruction_commit": plan_entry.reconstruction_commit,
                    "observed_tag_target": tag_targets[plan_entry.version],
                    "materialization_profile": plan_entry.materialization_profile,
                    "crlf_from_lf_paths": list(transformations[plan_entry.version]),
                    "asset_name": item.path.name,
                    "bytes": item.bytes,
                    "sha256": item.sha256,
                    "manifest_sha256": item.manifest_sha256,
                    "database_sha256": plan_entry.database_sha256,
                }
                for plan_entry, item in zip(plan.releases, bundles, strict=True)
            ],
        }
        (transaction / "backfill-report.json").write_bytes(_canonical_json(report))
        transaction.replace(output_directory)
        return report
    except BaseException:
        shutil.rmtree(transaction, ignore_errors=True)
        raise


def reconstruct_historical_release_tree(
    repository_root: Path,
    plan_entry: HistoricalReleasePlanEntry,
    output_directory: Path,
) -> tuple[str, ...]:
    """Reconstruct a release from Git objects without consulting checkout file bytes."""

    if output_directory.exists():
        raise HistoricalReleaseError(f"historical release tree already exists: {output_directory}")
    _verify_commit(repository_root, plan_entry.source_commit)
    _verify_commit(repository_root, plan_entry.reconstruction_commit)
    _verify_tag_relationship(repository_root, plan_entry)
    stem = DATASET_STEM.format(version=plan_entry.version)
    manifest_relative = f"{stem}_manifest.json"
    manifest_git_path = f"data/{manifest_relative}"
    manifest_bytes = _read_git_blobs(
        repository_root, plan_entry.reconstruction_commit, (manifest_git_path,)
    )[manifest_git_path]
    if hashlib.sha256(manifest_bytes).hexdigest() != plan_entry.manifest_sha256:
        raise HistoricalReleaseError(
            f"reviewed manifest hash differs at source commit: {plan_entry.version}"
        )
    manifest = _read_json_object(manifest_bytes, f"historical manifest {plan_entry.version}")
    source_paths, bundle_paths, provenance_paths = _historical_source_paths(
        repository_root, plan_entry, manifest, manifest_git_path
    )
    blobs = _read_git_blobs(repository_root, plan_entry.reconstruction_commit, tuple(source_paths))
    if plan_entry.source_commit != plan_entry.reconstruction_commit:
        source = _read_git_blobs(repository_root, plan_entry.source_commit, tuple(provenance_paths))
        changed = [path for path in provenance_paths if source[path] != blobs[path]]
        if changed:
            raise HistoricalReleaseError(
                "historical artifacts changed between source and reconstruction commit: "
                + ", ".join(changed)
            )

    transformed: list[str] = []
    try:
        output_directory.mkdir(parents=True)
        for source_path, bundle_path in zip(source_paths, bundle_paths, strict=True):
            destination = output_directory.joinpath(*PurePosixPath(bundle_path).parts)
            destination.parent.mkdir(parents=True, exist_ok=True)
            content = blobs[source_path]
            descriptor = manifest.get("files", {}).get(bundle_path)
            if descriptor is not None:
                mode = _materialization_mode(plan_entry, bundle_path)
                content = _materialize_manifest_bytes(
                    content,
                    descriptor,
                    bundle_path,
                    mode=mode,
                )
                if mode == "crlf_from_lf":
                    transformed.append(bundle_path)
            destination.write_bytes(content)
    except BaseException:
        shutil.rmtree(output_directory, ignore_errors=True)
        raise
    return tuple(sorted(transformed))


def verify_historical_release_tree(
    release_tree: Path,
    plan_entry: HistoricalReleasePlanEntry,
) -> None:
    stem = DATASET_STEM.format(version=plan_entry.version)
    manifest_name = f"{stem}_manifest.json"
    manifest_path = release_tree / manifest_name
    try:
        manifest_bytes = manifest_path.read_bytes()
    except OSError as error:
        raise HistoricalReleaseError(f"historical manifest is missing: {manifest_name}") from error
    if hashlib.sha256(manifest_bytes).hexdigest() != plan_entry.manifest_sha256:
        raise HistoricalReleaseError("historical manifest hash differs from reviewed plan")
    manifest = _read_json_object(manifest_bytes, f"historical manifest {plan_entry.version}")
    files = manifest.get("files")
    if not isinstance(files, dict) or not files:
        raise HistoricalReleaseError("historical manifest file inventory is empty")

    expected = {manifest_name}
    for relative, descriptor in files.items():
        _validate_manifest_descriptor(relative, descriptor)
        expected.add(relative)
        path = release_tree.joinpath(*PurePosixPath(relative).parts)
        try:
            content = path.read_bytes()
        except OSError as error:
            raise HistoricalReleaseError(
                f"historical manifest member is missing: {relative}"
            ) from error
        if len(content) != descriptor["bytes"]:
            raise HistoricalReleaseError(f"historical manifest member size differs: {relative}")
        if hashlib.sha256(content).hexdigest() != descriptor["sha256"]:
            raise HistoricalReleaseError(f"historical manifest member hash differs: {relative}")

    if plan_entry.verification_profile == "manifest-v2":
        _verify_manifest_v2(manifest, plan_entry, files)
    elif plan_entry.verification_profile == "legacy-v0.2":
        expected.update(_verify_legacy_v02(release_tree, manifest, plan_entry))
    else:  # pragma: no cover - rejected by the plan loader
        raise HistoricalReleaseError("unknown historical release verification profile")
    expected.update(file.bundle_path for file in plan_entry.supplemental_files)
    for supplemental in plan_entry.supplemental_files:
        path = release_tree.joinpath(*PurePosixPath(supplemental.bundle_path).parts)
        if not path.is_file() or sha256_file(path) != supplemental.sha256:
            raise HistoricalReleaseError(
                f"historical supplemental file differs: {supplemental.bundle_path}"
            )

    actual = {
        path.relative_to(release_tree).as_posix()
        for path in release_tree.rglob("*")
        if path.is_file()
    }
    if actual != expected:
        raise HistoricalReleaseError("historical release tree differs from reviewed inventory")
    database = release_tree / f"{stem}.sqlite"
    if not database.is_file() or sha256_file(database) != plan_entry.database_sha256:
        raise HistoricalReleaseError("historical database hash differs from reviewed plan")


def verify_historical_release_bundle(
    bundle_path: Path,
    plan_entry: HistoricalReleasePlanEntry,
) -> ReleaseBundle:
    """Verify a historical schema-1 bundle using only its explicit reviewed profile."""

    stem = DATASET_STEM.format(version=plan_entry.version)
    try:
        with zipfile.ZipFile(bundle_path) as archive:
            members = archive.infolist()
            names = [member.filename for member in members]
            if len(names) != len(set(names)):
                raise HistoricalReleaseError("historical bundle contains duplicate members")
            for name in names:
                path = PurePosixPath(name)
                if path.is_absolute() or ".." in path.parts or "\\" in name:
                    raise HistoricalReleaseError(f"unsafe historical bundle member: {name}")
            if BUNDLE_INDEX_NAME not in names:
                raise HistoricalReleaseError("historical bundle index is missing")
            index = _read_json_object(archive.read(BUNDLE_INDEX_NAME), "historical bundle index")
            expected_index_fields = {
                "schema_version",
                "version",
                "release_date",
                "tag",
                "source_commit",
                "release_tree_directory",
                "manifest",
                "files",
            }
            if (
                set(index) != expected_index_fields
                or index["schema_version"] != BUNDLE_SCHEMA_VERSION
            ):
                raise HistoricalReleaseError("historical bundle index schema differs")
            if (
                index["version"] != plan_entry.version
                or index["release_date"] != plan_entry.release_date
                or index["tag"] != plan_entry.tag
                or index["source_commit"] != plan_entry.source_commit
                or index["release_tree_directory"] != stem
            ):
                raise HistoricalReleaseError(
                    "historical bundle identity differs from reviewed plan"
                )
            files = index["files"]
            if not isinstance(files, dict) or not files:
                raise HistoricalReleaseError("historical bundle file inventory is empty")
            expected_names = {BUNDLE_INDEX_NAME, *(f"{stem}/{name}" for name in files)}
            if set(names) != expected_names:
                raise HistoricalReleaseError("historical bundle members differ from inventory")
            for relative, descriptor in files.items():
                _validate_manifest_descriptor(relative, descriptor)
                content = archive.read(f"{stem}/{relative}")
                if len(content) != descriptor["bytes"]:
                    raise HistoricalReleaseError(
                        f"historical bundle member size differs: {relative}"
                    )
                if hashlib.sha256(content).hexdigest() != descriptor["sha256"]:
                    raise HistoricalReleaseError(
                        f"historical bundle member hash differs: {relative}"
                    )
            manifest = index["manifest"]
            if not isinstance(manifest, dict) or set(manifest) != {"path", "bytes", "sha256"}:
                raise HistoricalReleaseError("historical bundle manifest descriptor differs")
            manifest_name = f"{stem}_manifest.json"
            if manifest.get("path") != manifest_name:
                raise HistoricalReleaseError("historical bundle manifest path differs")
            if manifest.get("sha256") != plan_entry.manifest_sha256:
                raise HistoricalReleaseError("historical bundle manifest hash differs from plan")
            if files.get(manifest_name) != {
                "bytes": manifest.get("bytes"),
                "sha256": manifest.get("sha256"),
            }:
                raise HistoricalReleaseError("historical bundle manifest inventory differs")
            with tempfile.TemporaryDirectory(
                prefix="optimization-compass-historical-verify-"
            ) as temporary:
                extracted = Path(temporary) / stem
                extracted.mkdir()
                for relative in files:
                    destination = extracted.joinpath(*PurePosixPath(relative).parts)
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    destination.write_bytes(archive.read(f"{stem}/{relative}"))
                verify_historical_release_tree(extracted, plan_entry)
    except (OSError, zipfile.BadZipFile, KeyError, json.JSONDecodeError, ValueError) as error:
        if isinstance(error, HistoricalReleaseError):
            raise
        raise HistoricalReleaseError(f"historical release bundle is invalid: {error}") from error
    return ReleaseBundle(
        version=plan_entry.version,
        release_date=plan_entry.release_date,
        tag=plan_entry.tag,
        source_commit=plan_entry.source_commit,
        path=bundle_path,
        bytes=bundle_path.stat().st_size,
        sha256=sha256_file(bundle_path),
        manifest_sha256=plan_entry.manifest_sha256,
    )


def verify_cataloged_historical_release_bundle(
    bundle_path: Path,
    plan_entry: HistoricalReleasePlanEntry,
    catalog_path: Path,
    repository: str,
) -> ReleaseBundle:
    """Verify uploaded bytes against the candidate catalog before inner identity."""

    catalog = load_release_catalog(catalog_path)
    catalog_entry = next(
        (entry for entry in catalog.releases if entry.version == plan_entry.version), None
    )
    if catalog_entry is None:
        raise HistoricalReleaseError(
            f"historical bundle version is absent from the candidate catalog: {plan_entry.version}"
        )
    _verify_catalog_provenance(catalog_entry, plan_entry, repository)
    expected_name = PurePosixPath(urlparse(catalog_entry.bundle.url).path).name
    if bundle_path.name != expected_name:
        raise HistoricalReleaseError("historical bundle name differs from candidate catalog")
    if bundle_path.stat().st_size != catalog_entry.bundle.size_bytes:
        raise HistoricalReleaseError("historical bundle size differs from candidate catalog")
    if sha256_file(bundle_path) != catalog_entry.bundle.sha256:
        raise HistoricalReleaseError("historical bundle digest differs from candidate catalog")
    return verify_historical_release_bundle(bundle_path, plan_entry)


def verify_remote_historical_releases(
    plan_path: Path,
    catalog_path: Path,
    *,
    repository_root: Path = ROOT,
    remote: str = "origin",
    opener: UrlOpener = _open_remote_url,
) -> dict[str, object]:
    """Download candidate assets anonymously and verify bytes plus internal identity."""

    plan = load_historical_backfill_plan(plan_path)
    catalog = load_release_catalog(catalog_path)
    remote_targets = _remote_tag_targets(repository_root, remote, plan.repository)
    for plan_entry in plan.releases:
        target = remote_targets.get(plan_entry.tag)
        if target is None:
            raise HistoricalReleaseError(f"remote release tag is missing: {plan_entry.tag}")
        if target != plan_entry.source_commit:
            raise HistoricalReleaseError(
                f"remote tag target differs from reviewed source commit: {plan_entry.tag}"
            )
    by_version = {entry.version: entry for entry in catalog.releases}
    verified: list[dict[str, object]] = []
    with tempfile.TemporaryDirectory(prefix="optimization-compass-remote-bundles-") as temporary:
        root = Path(temporary)
        for plan_entry in plan.releases:
            catalog_entry = by_version.get(plan_entry.version)
            if catalog_entry is None:
                raise HistoricalReleaseError(
                    f"candidate catalog is missing historical version: {plan_entry.version}"
                )
            _verify_catalog_provenance(catalog_entry, plan_entry, plan.repository)
            destination = root / PurePosixPath(urlparse(catalog_entry.bundle.url).path).name
            _download_exact_bundle(
                catalog_entry.bundle.url,
                destination,
                expected_bytes=catalog_entry.bundle.size_bytes,
                expected_sha256=catalog_entry.bundle.sha256,
                opener=opener,
            )
            bundle = verify_historical_release_bundle(destination, plan_entry)
            if (
                bundle.bytes != catalog_entry.bundle.size_bytes
                or bundle.sha256 != catalog_entry.bundle.sha256
            ):
                raise HistoricalReleaseError(
                    f"remote bundle differs from candidate catalog: {plan_entry.version}"
                )
            verified.append(
                {
                    "version": plan_entry.version,
                    "bytes": bundle.bytes,
                    "sha256": bundle.sha256,
                    "url": catalog_entry.bundle.url,
                    "tag_target": remote_targets[plan_entry.tag],
                }
            )
    return {"schema_version": 1, "verified_count": len(verified), "bundles": verified}


def _parse_plan_entry(payload: object) -> HistoricalReleasePlanEntry:
    entry = _strict_object(payload, _ENTRY_FIELDS, "historical release plan entry")
    supplemental_payload = entry["supplemental_files"]
    if not isinstance(supplemental_payload, list):
        raise HistoricalReleaseError("historical supplemental_files must be an array")
    supplemental = tuple(_parse_supplemental_file(item) for item in supplemental_payload)
    plan_entry = HistoricalReleasePlanEntry(
        version=_required_string(entry, "version", "historical release plan entry"),
        release_date=_required_string(entry, "release_date", "historical release plan entry"),
        source_commit=_required_string(entry, "source_commit", "historical release plan entry"),
        reconstruction_commit=_required_string(
            entry, "reconstruction_commit", "historical release plan entry"
        ),
        tag=_required_string(entry, "tag", "historical release plan entry"),
        verification_profile=_required_string(
            entry, "verification_profile", "historical release plan entry"
        ),
        materialization_profile=_required_string(
            entry, "materialization_profile", "historical release plan entry"
        ),
        manifest_sha256=_required_string(entry, "manifest_sha256", "historical release plan entry"),
        database_sha256=_required_string(entry, "database_sha256", "historical release plan entry"),
        supplemental_files=supplemental,
    )
    try:
        validate_release_identity(plan_entry.version, plan_entry.release_date)
        validate_sha256(plan_entry.manifest_sha256, "manifest_sha256")
        validate_sha256(plan_entry.database_sha256, "database_sha256")
    except ValueError as error:
        raise HistoricalReleaseError(str(error)) from error
    for commit in (plan_entry.source_commit, plan_entry.reconstruction_commit):
        if _COMMIT_PATTERN.fullmatch(commit) is None:
            raise HistoricalReleaseError("historical plan commits must be full lowercase SHAs")
    if plan_entry.tag != f"v{plan_entry.version}":
        raise HistoricalReleaseError("historical plan tag must equal v<version>")
    if plan_entry.verification_profile not in _PROFILES:
        raise HistoricalReleaseError("unknown historical release verification profile")
    if plan_entry.materialization_profile not in _MATERIALIZATION_PROFILES:
        raise HistoricalReleaseError("unknown historical materialization profile")
    if plan_entry.verification_profile == "legacy-v0.2":
        if plan_entry.version != "0.2.0":
            raise HistoricalReleaseError("legacy-v0.2 profile is restricted to dataset 0.2.0")
        if (
            len(supplemental) != len(_LEGACY_LICENSE_PATHS)
            or {item.bundle_path for item in supplemental} != _LEGACY_LICENSE_PATHS
        ):
            raise HistoricalReleaseError("legacy-v0.2 must declare the complete license supplement")
        if plan_entry.materialization_profile != "git-blob-v1":
            raise HistoricalReleaseError("legacy-v0.2 must use exact Git blob materialization")
    elif supplemental:
        raise HistoricalReleaseError("manifest-v2 releases must not declare supplemental files")
    return plan_entry


def _parse_supplemental_file(payload: object) -> SupplementalFile:
    item = _strict_object(payload, _SUPPLEMENTAL_FIELDS, "historical supplemental file")
    result = SupplementalFile(
        bundle_path=_required_safe_path(item, "bundle_path"),
        git_path=_required_safe_path(item, "git_path"),
        sha256=_required_string(item, "sha256", "historical supplemental file"),
    )
    try:
        validate_sha256(result.sha256, "supplemental sha256")
    except ValueError as error:
        raise HistoricalReleaseError(str(error)) from error
    return result


def _historical_source_paths(
    repository_root: Path,
    plan_entry: HistoricalReleasePlanEntry,
    manifest: dict[str, Any],
    manifest_git_path: str,
) -> tuple[list[str], list[str], list[str]]:
    files = manifest.get("files")
    if not isinstance(files, dict) or not files:
        raise HistoricalReleaseError("historical manifest file inventory is empty")
    manifest_name = PurePosixPath(manifest_git_path).name
    source_paths = [manifest_git_path]
    bundle_paths = [manifest_name]
    for relative in files:
        safe_relative = _safe_relative_path(relative, "historical manifest member")
        source_paths.append(f"data/{safe_relative}")
        bundle_paths.append(safe_relative)
    if plan_entry.verification_profile == "legacy-v0.2":
        csv_prefix = f"data/{DATASET_STEM.format(version=plan_entry.version)}_csv"
        for source_path in _list_git_blob_paths(
            repository_root, plan_entry.reconstruction_commit, csv_prefix
        ):
            if source_path not in source_paths:
                source_paths.append(source_path)
                bundle_paths.append(source_path.removeprefix("data/"))
    provenance_paths = list(source_paths)
    for supplemental in plan_entry.supplemental_files:
        if supplemental.git_path in source_paths or supplemental.bundle_path in bundle_paths:
            raise HistoricalReleaseError("historical supplemental path collides with manifest")
        source_paths.append(supplemental.git_path)
        bundle_paths.append(supplemental.bundle_path)
    if len(bundle_paths) != len(set(bundle_paths)):
        raise HistoricalReleaseError("historical release inventory contains duplicate paths")
    return source_paths, bundle_paths, provenance_paths


def _verify_manifest_v2(
    manifest: dict[str, Any],
    plan_entry: HistoricalReleasePlanEntry,
    files: dict[str, Any],
) -> None:
    if manifest.get("schema_version") != 2:
        raise HistoricalReleaseError("manifest-v2 profile requires schema version 2")
    if (
        manifest.get("version") != plan_entry.version
        or manifest.get("release_date") != plan_entry.release_date
    ):
        raise HistoricalReleaseError("historical manifest identity differs from reviewed plan")
    if manifest.get("database_sha256") != plan_entry.database_sha256:
        raise HistoricalReleaseError("historical manifest database hash differs from reviewed plan")
    if not _LEGACY_LICENSE_PATHS.issubset(files):
        raise HistoricalReleaseError("manifest-v2 historical release is missing bundled licenses")
    identity_name = f"{DATASET_STEM.format(version=plan_entry.version)}_release.json"
    if identity_name not in files:
        raise HistoricalReleaseError("manifest-v2 historical release identity is missing")


def _verify_legacy_v02(
    release_tree: Path,
    manifest: dict[str, Any],
    plan_entry: HistoricalReleasePlanEntry,
) -> set[str]:
    if "schema_version" in manifest:
        raise HistoricalReleaseError("legacy-v0.2 manifest unexpectedly declares a schema")
    if (
        manifest.get("version") != plan_entry.version
        or manifest.get("generated_at") != plan_entry.release_date
    ):
        raise HistoricalReleaseError("legacy-v0.2 manifest identity differs from reviewed plan")
    csv_directory = f"{DATASET_STEM.format(version=plan_entry.version)}_csv"
    csv_paths = {
        path.relative_to(release_tree).as_posix()
        for path in (release_tree / csv_directory).rglob("*")
        if path.is_file()
    }
    expected_count = manifest.get("validation", {}).get("csv_member_count")
    if not csv_paths or expected_count != len(csv_paths):
        raise HistoricalReleaseError("legacy-v0.2 CSV directory inventory differs")
    return csv_paths


def _verify_catalog_provenance(
    catalog_entry: ReleaseCatalogEntry,
    plan_entry: HistoricalReleasePlanEntry,
    repository: str,
) -> None:
    bundle_path = urlparse(catalog_entry.bundle.url).path
    if (
        catalog_entry.release_date != plan_entry.release_date
        or catalog_entry.database_sha256 != plan_entry.database_sha256
        or catalog_entry.manifest_sha256 != plan_entry.manifest_sha256
        or catalog_entry.source_commit != plan_entry.source_commit
        or catalog_entry.tag != plan_entry.tag
        or not bundle_path.startswith(f"/{repository}/releases/download/{plan_entry.tag}/")
    ):
        raise HistoricalReleaseError(
            f"candidate catalog provenance differs from plan: {plan_entry.version}"
        )


def _download_exact_bundle(
    url: str,
    destination: Path,
    *,
    expected_bytes: int,
    expected_sha256: str,
    opener: UrlOpener,
) -> None:
    digest = hashlib.sha256()
    written = 0
    try:
        with opener(url) as response, destination.open("xb") as output:
            final = urlparse(response.geturl())
            if final.scheme != "https" or not _is_allowed_release_host(final.hostname):
                raise HistoricalReleaseError("remote bundle redirected to an unapproved host")
            content_length = response.headers.get("Content-Length")
            if content_length is not None:
                try:
                    declared_bytes = int(content_length)
                except (TypeError, ValueError) as error:
                    raise HistoricalReleaseError(
                        "remote bundle Content-Length is invalid"
                    ) from error
                if declared_bytes != expected_bytes:
                    raise HistoricalReleaseError(
                        "remote bundle Content-Length differs from catalog"
                    )
            while True:
                chunk = response.read(min(1024 * 1024, expected_bytes - written + 1))
                if not chunk:
                    break
                written += len(chunk)
                if written > expected_bytes:
                    raise HistoricalReleaseError("remote bundle exceeds catalog size")
                digest.update(chunk)
                output.write(chunk)
    except BaseException:
        destination.unlink(missing_ok=True)
        raise
    if written != expected_bytes:
        destination.unlink(missing_ok=True)
        raise HistoricalReleaseError("remote bundle size differs from catalog")
    if digest.hexdigest() != expected_sha256:
        destination.unlink(missing_ok=True)
        raise HistoricalReleaseError("remote bundle digest differs from catalog")


def _is_allowed_release_host(hostname: str | None) -> bool:
    return hostname == "github.com" or bool(
        hostname and hostname.endswith(".githubusercontent.com")
    )


def _verify_commit(repository_root: Path, commit: str) -> None:
    result = subprocess.run(
        ["git", "-C", str(repository_root), "cat-file", "-e", f"{commit}^{{commit}}"],
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise HistoricalReleaseError(f"reviewed source commit is unavailable: {commit}")


def _verify_tag_relationship(
    repository_root: Path,
    plan_entry: HistoricalReleasePlanEntry,
) -> str | None:
    result = subprocess.run(
        [
            "git",
            "-C",
            str(repository_root),
            "rev-parse",
            "--verify",
            f"refs/tags/{plan_entry.tag}^{{commit}}",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    target = result.stdout.strip()
    if target != plan_entry.source_commit:
        raise HistoricalReleaseError(
            f"existing tag target differs from reviewed source commit: {plan_entry.tag}"
        )
    return target


def _remote_tag_targets(
    repository_root: Path, remote: str, expected_repository: str
) -> dict[str, str]:
    if _REMOTE_PATTERN.fullmatch(remote) is None:
        raise HistoricalReleaseError("remote name is invalid")
    try:
        remote_url_result = subprocess.run(
            ["git", "-C", str(repository_root), "remote", "get-url", "--", remote],
            text=True,
            capture_output=True,
            check=False,
            timeout=_REMOTE_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as error:
        raise HistoricalReleaseError("git remote get-url timed out") from error
    if remote_url_result.returncode != 0:
        raise HistoricalReleaseError("git remote get-url failed for the selected remote")
    remote_urls = remote_url_result.stdout.splitlines()
    if len(remote_urls) != 1:
        raise HistoricalReleaseError("selected remote must resolve to exactly one fetch URL")
    actual_repository = _github_repository_from_remote_url(remote_urls[0])
    if actual_repository != expected_repository:
        raise HistoricalReleaseError(
            "selected remote does not identify the repository in the reviewed plan"
        )
    try:
        tags_result = subprocess.run(
            ["git", "-C", str(repository_root), "ls-remote", "--tags", "--", remote],
            text=True,
            capture_output=True,
            check=False,
            timeout=_REMOTE_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as error:
        raise HistoricalReleaseError("git ls-remote timed out") from error
    if tags_result.returncode != 0:
        raise HistoricalReleaseError(f"git ls-remote failed: {tags_result.stderr.strip()}")
    return _parse_remote_tag_targets(tags_result.stdout)


def _github_repository_from_remote_url(remote_url: str) -> str | None:
    value = remote_url.strip()
    if value.startswith("git@github.com:"):
        repository = value.removeprefix("git@github.com:")
    else:
        parsed = urlparse(value)
        if parsed.hostname != "github.com":
            return None
        repository = parsed.path.lstrip("/")
    if repository.endswith(".git"):
        repository = repository[:-4]
    if _REPOSITORY_PATTERN.fullmatch(repository) is None:
        return None
    return repository


def _parse_remote_tag_targets(output: str) -> dict[str, str]:
    direct: dict[str, str] = {}
    peeled: dict[str, str] = {}
    seen_refs: set[str] = set()
    for line in output.splitlines():
        fields = line.split("\t")
        if len(fields) != 2:
            raise HistoricalReleaseError("git ls-remote returned an invalid tag record")
        object_id, reference = fields
        if _COMMIT_PATTERN.fullmatch(object_id) is None or not reference.startswith("refs/tags/"):
            raise HistoricalReleaseError("git ls-remote returned an invalid tag identity")
        if reference in seen_refs:
            raise HistoricalReleaseError(f"git ls-remote returned a duplicate tag ref: {reference}")
        seen_refs.add(reference)
        tag_reference = reference.removeprefix("refs/tags/")
        if tag_reference.endswith("^{}"):
            tag = tag_reference.removesuffix("^{}")
            if not tag:
                raise HistoricalReleaseError("git ls-remote returned an invalid peeled tag")
            peeled[tag] = object_id
        else:
            if not tag_reference:
                raise HistoricalReleaseError("git ls-remote returned an invalid tag")
            direct[tag_reference] = object_id
    orphaned = peeled.keys() - direct.keys()
    if orphaned:
        raise HistoricalReleaseError(
            "git ls-remote returned peeled tags without direct refs: " + ", ".join(sorted(orphaned))
        )
    return {tag: peeled.get(tag, object_id) for tag, object_id in direct.items()}


def _list_git_blob_paths(repository_root: Path, commit: str, prefix: str) -> list[str]:
    result = subprocess.run(
        ["git", "-C", str(repository_root), "ls-tree", "-rz", "--full-tree", commit, "--", prefix],
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise HistoricalReleaseError("git ls-tree failed for historical release")
    paths: list[str] = []
    for record in result.stdout.split(b"\0"):
        if not record:
            continue
        metadata, separator, raw_path = record.partition(b"\t")
        fields = metadata.split()
        if not separator or len(fields) != 3 or fields[1] != b"blob":
            raise HistoricalReleaseError("historical Git tree contains an unexpected entry")
        path = raw_path.decode("utf-8")
        _safe_relative_path(path, "historical Git path")
        paths.append(path)
    if not paths:
        raise HistoricalReleaseError(f"historical Git prefix is empty: {prefix}")
    return sorted(paths)


def _read_git_blobs(
    repository_root: Path,
    commit: str,
    paths: tuple[str, ...],
) -> dict[str, bytes]:
    if len(paths) != len(set(paths)):
        raise HistoricalReleaseError("historical Git blob request contains duplicate paths")
    for path in paths:
        _safe_relative_path(path, "historical Git path")
    batch = subprocess.run(
        ["git", "-C", str(repository_root), "cat-file", "--batch"],
        input=b"".join(f"{commit}:{path}\n".encode() for path in paths),
        capture_output=True,
        check=False,
    )
    if batch.returncode != 0:
        raise HistoricalReleaseError(
            f"git cat-file failed: {batch.stderr.decode(errors='replace').strip()}"
        )
    stream = io.BytesIO(batch.stdout)
    result: dict[str, bytes] = {}
    for path in paths:
        header = stream.readline().rstrip(b"\n")
        fields = header.split()
        if len(fields) != 3 or fields[1] != b"blob":
            raise HistoricalReleaseError(f"historical Git blob is unavailable: {path}")
        size = int(fields[2])
        content = _read_exact(stream, size)
        if stream.read(1) != b"\n":
            raise HistoricalReleaseError("git cat-file batch framing is invalid")
        result[path] = content
    if stream.read(1):
        raise HistoricalReleaseError("git cat-file returned unexpected trailing output")
    return result


def _read_exact(stream: Any, size: int) -> bytes:
    chunks: list[bytes] = []
    remaining = size
    while remaining:
        chunk = stream.read(remaining)
        if not chunk:
            raise HistoricalReleaseError("git cat-file returned a truncated blob")
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def _validate_manifest_descriptor(relative: object, descriptor: object) -> None:
    safe_relative = _safe_relative_path(relative, "historical file path")
    if not isinstance(descriptor, dict) or set(descriptor) != {"bytes", "sha256"}:
        raise HistoricalReleaseError(f"historical file descriptor differs: {safe_relative}")
    if isinstance(descriptor["bytes"], bool) or not isinstance(descriptor["bytes"], int):
        raise HistoricalReleaseError(f"historical file byte count is invalid: {safe_relative}")
    try:
        validate_sha256(descriptor["sha256"], "historical file sha256")
    except (TypeError, ValueError) as error:
        raise HistoricalReleaseError(f"historical file hash is invalid: {safe_relative}") from error


def _materialize_manifest_bytes(
    git_blob: bytes,
    descriptor: object,
    relative: str,
    *,
    mode: str,
) -> bytes:
    """Rehydrate recorded CRLF bytes without consulting a platform checkout.

    Older release manifests were generated from a Windows checkout while Git stored normalized
    LF blobs. The reviewed plan selects a strict path class up front; an undeclared mismatch is
    never used as a signal to retry with another representation.
    """

    _validate_manifest_descriptor(relative, descriptor)
    assert isinstance(descriptor, dict)
    if mode == "git_blob":
        candidate = git_blob
    elif mode == "crlf_from_lf":
        if b"\r" in git_blob or b"\n" not in git_blob:
            raise HistoricalReleaseError(
                f"declared CRLF source is not an LF-normalized Git blob: {relative}"
            )
        candidate = git_blob.replace(b"\n", b"\r\n")
    else:  # pragma: no cover - selected by a closed materialization profile
        raise HistoricalReleaseError(f"unknown materialization mode: {mode}")
    if (
        len(candidate) != descriptor["bytes"]
        or hashlib.sha256(candidate).hexdigest() != descriptor["sha256"]
    ):
        raise HistoricalReleaseError(
            f"declared materialization does not reproduce manifest bytes: {relative}"
        )
    return candidate


def _materialization_mode(
    plan_entry: HistoricalReleasePlanEntry,
    relative: str,
) -> str:
    if plan_entry.materialization_profile == "git-blob-v1":
        return "git_blob"
    stem = DATASET_STEM.format(version=plan_entry.version)
    crlf_paths = {
        *_LEGACY_LICENSE_PATHS,
        f"{stem}.json",
        f"{stem}.jsonl",
        f"{stem}_report.md",
        f"{stem}_schema.sql",
        f"{stem}_site-data/coverage.json",
        f"{stem}_site-data/coverage.md",
    }
    return "crlf_from_lf" if relative in crlf_paths else "git_blob"


def _read_json_object(content: bytes, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(content)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise HistoricalReleaseError(f"{label} is not valid JSON") from error
    if not isinstance(payload, dict):
        raise HistoricalReleaseError(f"{label} must be an object")
    return payload


def _strict_object(payload: object, fields: set[str], label: str) -> dict[str, Any]:
    if not isinstance(payload, dict) or set(payload) != fields:
        raise HistoricalReleaseError(f"{label} fields do not match schema")
    return payload


def _required_string(payload: dict[str, Any], field: str, label: str) -> str:
    value = payload[field]
    if not isinstance(value, str) or not value:
        raise HistoricalReleaseError(f"{label} field is invalid: {field}")
    return value


def _required_safe_path(payload: dict[str, Any], field: str) -> str:
    return _safe_relative_path(
        _required_string(payload, field, "historical supplemental file"),
        f"historical supplemental {field}",
    )


def _safe_relative_path(value: object, label: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or "\\" in value
        or "\n" in value
        or "\r" in value
        or "\0" in value
    ):
        raise HistoricalReleaseError(f"{label} is invalid")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or "." in path.parts:
        raise HistoricalReleaseError(f"{label} is unsafe")
    return value


def _canonical_json(payload: object) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )


def _version_key(version: str) -> tuple[int, int, int]:
    try:
        validate_semantic_version(version)
    except ValueError as error:
        raise HistoricalReleaseError(str(error)) from error
    major, minor, patch = version.split(".")
    return int(major), int(minor), int(patch)
