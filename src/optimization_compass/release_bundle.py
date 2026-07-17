from __future__ import annotations

import hashlib
import json
import re
import tempfile
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path, PurePosixPath

from optimization_compass.dataset_release import (
    DATASET_STEM,
    ROOT,
    ReleaseValidationError,
    sha256_file,
    verify_release_tree,
)

BUNDLE_INDEX_NAME = "bundle-index.json"
BUNDLE_SCHEMA_VERSION = 1
_COMMIT_PATTERN = re.compile(r"[0-9a-f]{40}")


@dataclass(frozen=True)
class ReleaseBundle:
    version: str
    release_date: str
    tag: str
    source_commit: str
    path: Path
    bytes: int
    sha256: str
    manifest_sha256: str


class ReleaseBundleError(ValueError):
    pass


def build_release_bundle(
    staged_directory: Path,
    output_directory: Path,
    *,
    source_commit: str,
    tag: str,
) -> ReleaseBundle:
    """Write one deterministic complete release ZIP outside the tracked release tree."""
    if _COMMIT_PATTERN.fullmatch(source_commit) is None:
        raise ReleaseBundleError("source commit must be a 40-character lowercase SHA")
    verify_release_tree(staged_directory)
    manifest_path, manifest = _release_manifest(staged_directory)
    version = _required_string(manifest, "version")
    release_date = _required_string(manifest, "release_date")
    if tag != f"v{version}":
        raise ReleaseBundleError("release tag must equal v<dataset version>")
    resolved_output = output_directory.resolve(strict=False)
    repository_root = ROOT.resolve()
    if resolved_output == repository_root or repository_root in resolved_output.parents:
        raise ReleaseBundleError("complete release bundles must be written outside the repository")
    output_directory.mkdir(parents=True, exist_ok=True)
    stem = DATASET_STEM.format(version=version)
    archive_path = output_directory / f"{stem}_bundle.zip"
    if archive_path.exists():
        raise ReleaseBundleError(f"bundle output already exists: {archive_path}")

    files = _tree_files(staged_directory)
    index = {
        "schema_version": BUNDLE_SCHEMA_VERSION,
        "version": version,
        "release_date": release_date,
        "tag": tag,
        "source_commit": source_commit,
        "release_tree_directory": stem,
        "manifest": {
            "path": manifest_path.name,
            "bytes": manifest_path.stat().st_size,
            "sha256": sha256_file(manifest_path),
        },
        "files": files,
    }
    index_bytes = _canonical_json(index)
    timestamp = _zip_timestamp(release_date)
    with zipfile.ZipFile(
        archive_path,
        "x",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
        strict_timestamps=True,
    ) as archive:
        _write_zip_member(archive, BUNDLE_INDEX_NAME, index_bytes, timestamp)
        for relative in sorted(files):
            _write_zip_member(
                archive,
                f"{stem}/{relative}",
                (staged_directory / relative).read_bytes(),
                timestamp,
            )
    result = ReleaseBundle(
        version=version,
        release_date=release_date,
        tag=tag,
        source_commit=source_commit,
        path=archive_path,
        bytes=archive_path.stat().st_size,
        sha256=sha256_file(archive_path),
        manifest_sha256=sha256_file(manifest_path),
    )
    try:
        verify_release_bundle(archive_path)
    except Exception:
        archive_path.unlink(missing_ok=True)
        raise
    return result


def verify_release_bundle(bundle_path: Path) -> ReleaseBundle:
    try:
        with zipfile.ZipFile(bundle_path) as archive:
            members = archive.infolist()
            names = [member.filename for member in members]
            if len(names) != len(set(names)):
                raise ReleaseBundleError("bundle contains duplicate members")
            if BUNDLE_INDEX_NAME not in names:
                raise ReleaseBundleError("bundle index is missing")
            for name in names:
                path = PurePosixPath(name)
                if path.is_absolute() or ".." in path.parts or "\\" in name:
                    raise ReleaseBundleError(f"unsafe bundle member: {name}")
            index = json.loads(archive.read(BUNDLE_INDEX_NAME))
            if not isinstance(index, dict):
                raise ReleaseBundleError("bundle index must be an object")
            _expect_exact_fields(
                index,
                {
                    "schema_version",
                    "version",
                    "release_date",
                    "tag",
                    "source_commit",
                    "release_tree_directory",
                    "manifest",
                    "files",
                },
                "bundle index",
            )
            if index["schema_version"] != BUNDLE_SCHEMA_VERSION:
                raise ReleaseBundleError("unsupported bundle index schema version")
            version = _required_string(index, "version")
            release_date = _required_string(index, "release_date")
            datetime.strptime(release_date, "%Y-%m-%d")
            tag = _required_string(index, "tag")
            if tag != f"v{version}":
                raise ReleaseBundleError("bundle tag does not match its version")
            source_commit = _required_string(index, "source_commit")
            if _COMMIT_PATTERN.fullmatch(source_commit) is None:
                raise ReleaseBundleError("bundle source commit is invalid")
            stem = DATASET_STEM.format(version=version)
            if index["release_tree_directory"] != stem:
                raise ReleaseBundleError("bundle release tree directory is invalid")
            files = index["files"]
            if not isinstance(files, dict) or not files:
                raise ReleaseBundleError("bundle file inventory is empty")
            expected_names = {BUNDLE_INDEX_NAME, *(f"{stem}/{name}" for name in files)}
            if set(names) != expected_names:
                raise ReleaseBundleError("bundle members differ from the file inventory")
            for relative, descriptor in files.items():
                _validate_file_descriptor(relative, descriptor)
                content = archive.read(f"{stem}/{relative}")
                if len(content) != descriptor["bytes"]:
                    raise ReleaseBundleError(f"bundle member size differs: {relative}")
                if hashlib.sha256(content).hexdigest() != descriptor["sha256"]:
                    raise ReleaseBundleError(f"bundle member hash differs: {relative}")
            manifest = index["manifest"]
            _validate_file_descriptor("manifest", manifest, require_path=True)
            manifest_relative = _required_string(manifest, "path")
            manifest_descriptor = files.get(manifest_relative)
            if manifest_descriptor != {
                "bytes": manifest["bytes"],
                "sha256": manifest["sha256"],
            }:
                raise ReleaseBundleError("bundle manifest descriptor differs from inventory")
            with tempfile.TemporaryDirectory(prefix="optimization-compass-bundle-verify-") as temp:
                extracted = Path(temp) / stem
                extracted.mkdir()
                for relative in files:
                    destination = extracted / PurePosixPath(relative)
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    destination.write_bytes(archive.read(f"{stem}/{relative}"))
                verify_release_tree(extracted)
    except (OSError, zipfile.BadZipFile, KeyError, json.JSONDecodeError, ValueError) as error:
        if isinstance(error, ReleaseBundleError):
            raise
        if isinstance(error, ReleaseValidationError):
            raise ReleaseBundleError(str(error)) from error
        raise ReleaseBundleError(f"release bundle is invalid: {error}") from error
    return ReleaseBundle(
        version=version,
        release_date=release_date,
        tag=tag,
        source_commit=source_commit,
        path=bundle_path,
        bytes=bundle_path.stat().st_size,
        sha256=sha256_file(bundle_path),
        manifest_sha256=str(manifest["sha256"]),
    )


def _tree_files(directory: Path) -> dict[str, dict[str, int | str]]:
    return {
        path.relative_to(directory).as_posix(): {
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
        for path in sorted(item for item in directory.rglob("*") if item.is_file())
    }


def _release_manifest(directory: Path) -> tuple[Path, dict[str, object]]:
    manifests = list(directory.glob("*_manifest.json"))
    if len(manifests) != 1:
        raise ReleaseBundleError("release tree must contain exactly one manifest")
    payload = json.loads(manifests[0].read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ReleaseBundleError("release manifest must be an object")
    return manifests[0], payload


def _canonical_json(payload: object) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )


def _zip_timestamp(release_date: str) -> tuple[int, int, int, int, int, int]:
    parsed = datetime.strptime(release_date, "%Y-%m-%d")
    if parsed.year < 1980:
        raise ReleaseBundleError("ZIP release date must be 1980 or later")
    return (parsed.year, parsed.month, parsed.day, 0, 0, 0)


def _write_zip_member(
    archive: zipfile.ZipFile,
    name: str,
    content: bytes,
    timestamp: tuple[int, int, int, int, int, int],
) -> None:
    info = zipfile.ZipInfo(name, timestamp)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.create_system = 3
    info.external_attr = 0o100644 << 16
    archive.writestr(info, content, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def _expect_exact_fields(payload: dict[str, object], expected: set[str], label: str) -> None:
    if set(payload) != expected:
        raise ReleaseBundleError(f"{label} fields do not match schema")


def _required_string(payload: dict[str, object], field: str) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not value:
        raise ReleaseBundleError(f"bundle field is invalid: {field}")
    return value


def _validate_file_descriptor(
    relative: object,
    descriptor: object,
    *,
    require_path: bool = False,
) -> None:
    if not isinstance(relative, str) or not relative or PurePosixPath(relative).is_absolute():
        raise ReleaseBundleError("bundle file path is invalid")
    if ".." in PurePosixPath(relative).parts or "\\" in relative:
        raise ReleaseBundleError("bundle file path is unsafe")
    if not isinstance(descriptor, dict):
        raise ReleaseBundleError(f"bundle descriptor is invalid: {relative}")
    expected = {"path", "bytes", "sha256"} if require_path else {"bytes", "sha256"}
    if set(descriptor) != expected:
        raise ReleaseBundleError(f"bundle descriptor fields differ: {relative}")
    if not isinstance(descriptor["bytes"], int) or descriptor["bytes"] < 0:
        raise ReleaseBundleError(f"bundle descriptor bytes are invalid: {relative}")
    digest = descriptor["sha256"]
    if not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
        raise ReleaseBundleError(f"bundle descriptor hash is invalid: {relative}")
