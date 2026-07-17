from __future__ import annotations

import json
import zipfile
from hashlib import sha256
from pathlib import Path

import pytest

from scripts.package_historical_release import (
    HistoricalReleaseError,
    load_manifest_entries,
    package_historical_release,
    write_catalog,
)


def _write_fixture(root: Path) -> Path:
    data = root / "data"
    data.mkdir()
    first = data / "release.sqlite"
    second = data / "release.json"
    first.write_bytes(b"sqlite fixture\n")
    second.write_bytes(b'{"fixture": true}\n')
    manifest = data / "release-manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "dataset_version": "1.2.3",
                "release_date": "2026-07-17",
                "files": [
                    {
                        "path": first.name,
                        "sha256": sha256(first.read_bytes()).hexdigest(),
                        "size_bytes": first.stat().st_size,
                    },
                    {
                        "path": second.name,
                        "sha256": sha256(second.read_bytes()).hexdigest(),
                        "size_bytes": second.stat().st_size,
                    },
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return manifest


def test_historical_release_bundle_is_deterministic_and_manifest_verified(tmp_path: Path) -> None:
    manifest = _write_fixture(tmp_path)
    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"

    first = package_historical_release(
        manifest,
        output_dir=first_dir,
        repository_root=tmp_path,
    )
    second = package_historical_release(
        manifest,
        output_dir=second_dir,
        repository_root=tmp_path,
    )

    assert first.bundle_sha256 == second.bundle_sha256
    assert first.file_count == 2
    assert first.bundle_path is not None
    with zipfile.ZipFile(first.bundle_path) as archive:
        assert archive.namelist() == [
            "release-manifest.json",
            "release.json",
            "release.sqlite",
        ]
        assert all(item.date_time == (1980, 1, 1, 0, 0, 0) for item in archive.infolist())


def test_check_only_verifies_without_writing_a_bundle(tmp_path: Path) -> None:
    manifest = _write_fixture(tmp_path)

    result = package_historical_release(
        manifest,
        output_dir=None,
        repository_root=tmp_path,
        check_only=True,
    )

    assert result.bundle_path is None
    assert result.bundle_sha256 is None
    assert result.payload_size_bytes > 0


def test_historical_release_packager_rejects_hash_drift(tmp_path: Path) -> None:
    manifest = _write_fixture(tmp_path)
    (manifest.parent / "release.json").write_text("changed\n", encoding="utf-8")

    with pytest.raises(HistoricalReleaseError, match="sha256 mismatch"):
        package_historical_release(
            manifest,
            output_dir=None,
            repository_root=tmp_path,
            check_only=True,
        )


def test_catalog_is_sorted_and_machine_readable(tmp_path: Path) -> None:
    manifest = _write_fixture(tmp_path)
    result = package_historical_release(
        manifest,
        output_dir=None,
        repository_root=tmp_path,
        check_only=True,
    )
    catalog = tmp_path / "catalog.json"

    write_catalog([result], catalog)

    payload = json.loads(catalog.read_text(encoding="utf-8"))
    assert payload["contract_version"] == "1.0.0"
    assert payload["releases"][0]["dataset_version"] == "1.2.3"


def test_current_release_manifest_shape_is_supported() -> None:
    root = Path(__file__).parents[1]
    manifest = root / "data/optimization_method_selection_database_v0.11.0_manifest.json"

    version, release_date, entries = load_manifest_entries(manifest, repository_root=root)

    assert version == "0.11.0"
    assert release_date
    assert entries
