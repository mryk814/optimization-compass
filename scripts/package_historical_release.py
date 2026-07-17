from __future__ import annotations

import argparse
import json
import re
import zipfile
from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path, PurePosixPath
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
HEX_SHA256 = re.compile(r"^[0-9a-f]{64}$")
ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)


class HistoricalReleaseError(ValueError):
    pass


@dataclass(frozen=True)
class ManifestEntry:
    archive_path: str
    source_path: Path
    sha256: str
    size_bytes: int | None


@dataclass(frozen=True)
class BundleResult:
    contract_version: str
    dataset_version: str
    release_date: str | None
    source_manifest: str
    source_manifest_sha256: str
    bundle_path: str | None
    bundle_sha256: str | None
    bundle_size_bytes: int | None
    file_count: int
    payload_size_bytes: int


def load_manifest_entries(
    manifest_path: Path,
    *,
    repository_root: Path = ROOT,
) -> tuple[str, str | None, list[ManifestEntry]]:
    manifest_path = manifest_path.resolve()
    payload = _load_json_object(manifest_path)
    version = _first_text(payload, "dataset_version", "version")
    release_date = _optional_text(payload, "release_date", "date")
    raw_entries = _manifest_collection(payload)

    entries: list[ManifestEntry] = []
    for raw_path, metadata in _iter_manifest_rows(raw_entries):
        archive_path = _safe_archive_path(raw_path)
        expected_sha = _metadata_sha256(metadata)
        expected_size = _metadata_size(metadata)
        source_path = _resolve_source_path(
            raw_path,
            manifest_path=manifest_path,
            repository_root=repository_root.resolve(),
        )
        entries.append(
            ManifestEntry(
                archive_path=archive_path,
                source_path=source_path,
                sha256=expected_sha,
                size_bytes=expected_size,
            )
        )

    entries.sort(key=lambda entry: entry.archive_path)
    if not entries:
        raise HistoricalReleaseError(f"{manifest_path} contains no release files")
    if len({entry.archive_path for entry in entries}) != len(entries):
        raise HistoricalReleaseError(f"{manifest_path} contains duplicate release paths")
    return version, release_date, entries


def verify_manifest_entries(entries: list[ManifestEntry]) -> int:
    total = 0
    for entry in entries:
        if not entry.source_path.is_file():
            raise HistoricalReleaseError(f"missing release file: {entry.source_path}")
        data = entry.source_path.read_bytes()
        observed_sha = sha256(data).hexdigest()
        if observed_sha != entry.sha256:
            raise HistoricalReleaseError(
                f"sha256 mismatch for {entry.archive_path}: "
                f"expected {entry.sha256}, observed {observed_sha}"
            )
        if entry.size_bytes is not None and len(data) != entry.size_bytes:
            raise HistoricalReleaseError(
                f"size mismatch for {entry.archive_path}: "
                f"expected {entry.size_bytes}, observed {len(data)}"
            )
        total += len(data)
    return total


def package_historical_release(
    manifest_path: Path,
    *,
    output_dir: Path | None,
    repository_root: Path = ROOT,
    check_only: bool = False,
    overwrite: bool = False,
) -> BundleResult:
    manifest_path = manifest_path.resolve()
    version, release_date, entries = load_manifest_entries(
        manifest_path,
        repository_root=repository_root,
    )
    payload_size = verify_manifest_entries(entries)
    manifest_bytes = manifest_path.read_bytes()
    manifest_sha = sha256(manifest_bytes).hexdigest()

    if check_only:
        return BundleResult(
            contract_version="1.0.0",
            dataset_version=version,
            release_date=release_date,
            source_manifest=str(manifest_path),
            source_manifest_sha256=manifest_sha,
            bundle_path=None,
            bundle_sha256=None,
            bundle_size_bytes=None,
            file_count=len(entries),
            payload_size_bytes=payload_size,
        )

    if output_dir is None:
        raise HistoricalReleaseError("--output-dir is required unless --check-only is used")
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    bundle_path = output_dir / f"optimization-compass-dataset-v{version}.zip"
    if bundle_path.exists() and not overwrite:
        raise HistoricalReleaseError(
            f"bundle already exists: {bundle_path}; pass --overwrite to replace it"
        )

    temporary = bundle_path.with_suffix(".zip.tmp")
    temporary.unlink(missing_ok=True)
    try:
        with zipfile.ZipFile(
            temporary,
            mode="w",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=9,
            strict_timestamps=True,
        ) as archive:
            _write_zip_member(archive, manifest_path.name, manifest_bytes)
            for entry in entries:
                if entry.source_path == manifest_path:
                    continue
                _write_zip_member(archive, entry.archive_path, entry.source_path.read_bytes())
        temporary.replace(bundle_path)
    finally:
        temporary.unlink(missing_ok=True)

    bundle_bytes = bundle_path.read_bytes()
    return BundleResult(
        contract_version="1.0.0",
        dataset_version=version,
        release_date=release_date,
        source_manifest=str(manifest_path),
        source_manifest_sha256=manifest_sha,
        bundle_path=str(bundle_path),
        bundle_sha256=sha256(bundle_bytes).hexdigest(),
        bundle_size_bytes=len(bundle_bytes),
        file_count=len(entries),
        payload_size_bytes=payload_size,
    )


def write_catalog(results: list[BundleResult], path: Path) -> None:
    ordered = sorted(results, key=lambda item: _version_key(item.dataset_version))
    payload = {
        "contract_version": "1.0.0",
        "releases": [asdict(item) for item in ordered],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _manifest_collection(payload: dict[str, Any]) -> object:
    for field in ("files", "artifacts", "outputs"):
        if field in payload:
            return payload[field]
    raise HistoricalReleaseError("release manifest needs files, artifacts, or outputs")


def _iter_manifest_rows(value: object) -> list[tuple[str, object]]:
    if isinstance(value, dict):
        return [(str(path), metadata) for path, metadata in value.items()]
    if not isinstance(value, list):
        raise HistoricalReleaseError("release manifest collection must be a list or object")

    rows: list[tuple[str, object]] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise HistoricalReleaseError(f"release manifest row {index} must be an object")
        path = _first_text(item, "path", "relative_path", "file", "name")
        rows.append((path, item))
    return rows


def _metadata_sha256(value: object) -> str:
    if isinstance(value, str):
        raw = value
    elif isinstance(value, dict):
        raw = _first_text(value, "sha256", "hash", "digest")
    else:
        raise HistoricalReleaseError("release file metadata needs a sha256 value")
    normalized = raw.removeprefix("sha256:").lower()
    if not HEX_SHA256.fullmatch(normalized):
        raise HistoricalReleaseError(f"invalid sha256 value: {raw}")
    return normalized


def _metadata_size(value: object) -> int | None:
    if not isinstance(value, dict):
        return None
    for field in ("size_bytes", "bytes", "size"):
        if field not in value:
            continue
        observed = value[field]
        if not isinstance(observed, int) or isinstance(observed, bool) or observed < 0:
            raise HistoricalReleaseError(f"invalid {field}: {observed}")
        return observed
    return None


def _resolve_source_path(
    raw_path: str,
    *,
    manifest_path: Path,
    repository_root: Path,
) -> Path:
    relative = Path(_safe_archive_path(raw_path))
    candidates = [
        manifest_path.parent / relative,
        repository_root / relative,
        repository_root.parent / relative,
    ]
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved.is_file():
            return resolved
    return candidates[0].resolve()


def _safe_archive_path(value: str) -> str:
    normalized = value.replace("\\", "/").removeprefix("./")
    path = PurePosixPath(normalized)
    if not normalized or path.is_absolute() or ".." in path.parts:
        raise HistoricalReleaseError(f"unsafe release path: {value}")
    return path.as_posix()


def _write_zip_member(archive: zipfile.ZipFile, name: str, data: bytes) -> None:
    info = zipfile.ZipInfo(_safe_archive_path(name), date_time=ZIP_TIMESTAMP)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.create_system = 3
    info.external_attr = 0o100644 << 16
    archive.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def _load_json_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise HistoricalReleaseError(f"{path} must contain a JSON object")
    return value


def _first_text(payload: dict[str, Any], *fields: str) -> str:
    for field in fields:
        value = payload.get(field)
        if isinstance(value, str) and value.strip():
            return value.strip()
    raise HistoricalReleaseError(f"missing non-empty field: {' or '.join(fields)}")


def _optional_text(payload: dict[str, Any], *fields: str) -> str | None:
    for field in fields:
        value = payload.get(field)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _version_key(value: str) -> tuple[int, ...]:
    try:
        return tuple(int(part) for part in value.split("."))
    except ValueError:
        return (0,)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verify and package immutable historical dataset releases without network access."
    )
    parser.add_argument("--manifest", action="append", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--catalog", type=Path)
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    results = [
        package_historical_release(
            manifest,
            output_dir=args.output_dir,
            check_only=args.check_only,
            overwrite=args.overwrite,
        )
        for manifest in args.manifest
    ]
    if args.catalog is not None:
        write_catalog(results, args.catalog)
    print(json.dumps([asdict(item) for item in results], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
