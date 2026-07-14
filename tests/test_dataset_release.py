from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
from pathlib import Path

import pytest

import optimization_compass.dataset_release as dataset_release_module
from optimization_compass.dataset_release import (
    BASE_DATASET_SHA256,
    BASE_DATASET_VERSION,
    TARGET_DATASET_VERSION,
    ReleaseValidationError,
    build_staged_release,
    publish_release,
    tree_hash,
    verify_database,
)

ROOT = Path(__file__).parents[1]
BASE_DATABASE = ROOT / "data/optimization_method_selection_database_v0.2.0.sqlite"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_live_checks_detect_mutation_after_stored_pass(tmp_path: Path) -> None:
    mutated = tmp_path / "mutated.sqlite"
    shutil.copy2(BASE_DATABASE, mutated)
    connection = sqlite3.connect(mutated)
    try:
        connection.execute("PRAGMA foreign_keys = OFF")
        connection.execute("DELETE FROM sources WHERE source_id = 'S001'")
        connection.commit()
    finally:
        connection.close()

    result = verify_database(mutated)

    assert result.ok is False
    assert result.live_failures
    assert "CHK005" in {check.check_id for check in result.live_failures}


def test_staging_preserves_published_dataset_and_is_reproducible(tmp_path: Path) -> None:
    before = sha256(BASE_DATABASE)

    first = build_staged_release(BASE_DATABASE, tmp_path / "first")
    second = build_staged_release(BASE_DATABASE, tmp_path / "second")

    assert before == BASE_DATASET_SHA256
    assert sha256(BASE_DATABASE) == before
    assert first.version == TARGET_DATASET_VERSION
    assert tree_hash(first.output_directory) == tree_hash(second.output_directory)
    assert first.tree_sha256 == second.tree_sha256


def test_staging_rejects_existing_or_overlapping_output_directories(tmp_path: Path) -> None:
    existing = tmp_path / "existing"
    existing.mkdir()
    marker = existing / "keep.txt"
    marker.write_text("keep", encoding="utf-8")

    with pytest.raises(ReleaseValidationError, match="must not already exist"):
        build_staged_release(BASE_DATABASE, existing)

    assert marker.read_text(encoding="utf-8") == "keep"
    with pytest.raises(ReleaseValidationError, match="overlaps protected input"):
        build_staged_release(BASE_DATABASE, BASE_DATABASE)
    with pytest.raises(ReleaseValidationError, match="overlaps protected input"):
        build_staged_release(BASE_DATABASE, ROOT / "data")
    with pytest.raises(ReleaseValidationError, match="overlaps protected input"):
        build_staged_release(BASE_DATABASE, BASE_DATABASE / "nested-output")


def test_new_version_stage_updates_every_versioned_artifact(tmp_path: Path) -> None:
    release = build_staged_release(
        BASE_DATABASE,
        tmp_path / "release",
        target_version="0.3.0",
        release_date="2026-07-14",
    )

    assert release.version == "0.3.0"
    assert release.database_path.name.endswith("_v0.3.0.sqlite")
    manifest = json.loads(release.manifest_path.read_text(encoding="utf-8"))
    assert manifest["version"] == "0.3.0"
    assert manifest["release_date"] == "2026-07-14"
    assert all("v0.3.0" in name for name in manifest["artifacts"].values())
    json_path = release.output_directory / "optimization_method_selection_database_v0.3.0.json"
    json_payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert (json_payload["version"], json_payload["release_date"]) == (
        "0.3.0",
        "2026-07-14",
    )
    jsonl_header = json.loads(
        next(release.output_directory.glob("*.jsonl")).read_text(encoding="utf-8").splitlines()[0]
    )
    assert (jsonl_header["version"], jsonl_header["release_date"]) == (
        "0.3.0",
        "2026-07-14",
    )
    assert "Version: `0.3.0`" in next(release.output_directory.glob("*_report.md")).read_text(
        encoding="utf-8"
    )
    connection = sqlite3.connect(release.database_path)
    try:
        versions = connection.execute(
            "SELECT version, release_date FROM version_history ORDER BY release_date"
        ).fetchall()
        revisions = connection.execute(
            "SELECT version, date FROM model_revisions WHERE version = '0.3.0'"
        ).fetchall()
    finally:
        connection.close()
    assert ("0.3.0", "2026-07-14") in versions
    assert revisions == [("0.3.0", "2026-07-14")]


def test_database_verification_rejects_missing_extra_checks_and_atlas_tables(
    tmp_path: Path,
) -> None:
    base_missing = tmp_path / "base-missing.sqlite"
    shutil.copy2(BASE_DATABASE, base_missing)
    connection = sqlite3.connect(base_missing)
    connection.execute("DELETE FROM release_checks WHERE check_id = 'CHK012'")
    connection.commit()
    connection.close()
    base_result = verify_database(base_missing)
    assert base_result.ok is False
    assert "missing-stored:CHK012" in base_result.status_mismatches

    staged = build_staged_release(BASE_DATABASE, tmp_path / "staged")
    connection = sqlite3.connect(staged.database_path)
    connection.execute("DELETE FROM release_checks WHERE check_id = 'CHK015'")
    connection.execute(
        """
        INSERT INTO release_checks VALUES (
          'CHK999', 'extra', 'test', 'critical', 'pass', '1', '1', 'extra', '2026-07-13'
        )
        """
    )
    connection.commit()
    connection.close()
    check_result = verify_database(staged.database_path)
    assert check_result.ok is False
    assert "missing-stored:CHK015" in check_result.status_mismatches
    assert "extra-stored:CHK999" in check_result.status_mismatches

    missing_table = tmp_path / "missing-table.sqlite"
    shutil.copy2(staged.database_path, missing_table)
    connection = sqlite3.connect(missing_table)
    connection.execute("PRAGMA foreign_keys = OFF")
    connection.execute("DROP TABLE view_presets")
    connection.commit()
    connection.close()
    table_result = verify_database(missing_table)
    assert table_result.ok is False
    assert "CHK013" in {check.check_id for check in table_result.live_failures}


def test_require_atlas_rejects_database_with_entire_atlas_contract_removed(
    tmp_path: Path,
) -> None:
    staged = build_staged_release(BASE_DATABASE, tmp_path / "staged")
    stripped = tmp_path / "stripped.sqlite"
    shutil.copy2(staged.database_path, stripped)
    connection = sqlite3.connect(stripped)
    try:
        connection.execute("PRAGMA foreign_keys = OFF")
        for table in dataset_release_module.ATLAS_TABLES:
            connection.execute(f'DROP TABLE "{table}"')
        connection.execute("DELETE FROM release_checks WHERE check_id >= 'CHK013'")
        connection.commit()
    finally:
        connection.close()

    assert verify_database(stripped).ok is True
    required = verify_database(stripped, require_atlas=True)

    assert required.ok is False
    assert "CHK013" in {check.check_id for check in required.live_failures}
    assert "missing-stored:CHK020" in required.status_mismatches


def _published_fixture(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    data_dir = tmp_path / "published"
    data_dir.mkdir()
    (data_dir / "keep.txt").write_text("original", encoding="utf-8")
    runtime = tmp_path / "knowledge.sqlite"
    shutil.copy2(BASE_DATABASE, runtime)
    version_file = tmp_path / "DATASET_VERSION"
    version_file.write_text(
        f"{BASE_DATASET_VERSION}\nsha256={BASE_DATASET_SHA256}\n", encoding="utf-8"
    )
    site_data = tmp_path / "site-data"
    site_data.mkdir()
    (site_data / "keep.json").write_text('{"status":"original"}\n', encoding="utf-8")
    return data_dir, runtime, version_file, site_data


def _tree_bytes(directory: Path) -> dict[str, bytes]:
    return {
        path.relative_to(directory).as_posix(): path.read_bytes()
        for path in directory.rglob("*")
        if path.is_file()
    }


def test_publish_succeeds_for_a_consistent_new_version(tmp_path: Path) -> None:
    staged = build_staged_release(
        BASE_DATABASE,
        tmp_path / "staged",
        target_version="0.3.0",
        release_date="2026-07-14",
    )
    data_dir, runtime, version_file, site_data = _published_fixture(tmp_path)

    publish_release(staged.output_directory, data_dir, runtime, version_file, site_data)

    assert (data_dir / "keep.txt").read_text(encoding="utf-8") == "original"
    assert (data_dir / staged.database_path.name).exists()
    assert runtime.read_bytes() == staged.database_path.read_bytes()
    assert version_file.read_text(encoding="utf-8") == (f"0.3.0\nsha256={sha256(runtime)}\n")
    assert _tree_bytes(site_data) == _tree_bytes(staged.site_data_directory)


@pytest.mark.parametrize("failure_target", ["data", "runtime", "version", "site"])
def test_publish_rolls_back_all_targets_after_injected_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure_target: str
) -> None:
    staged = build_staged_release(
        BASE_DATABASE,
        tmp_path / "staged",
        target_version="0.3.0",
        release_date="2026-07-14",
    )
    data_dir, runtime, version_file, site_data = _published_fixture(tmp_path)
    before_data = _tree_bytes(data_dir)
    before_runtime = runtime.read_bytes()
    before_version = version_file.read_bytes()
    before_site = _tree_bytes(site_data)
    real_replace = dataset_release_module._atomic_replace
    selected_target = {
        "data": data_dir,
        "runtime": runtime,
        "version": version_file,
        "site": site_data,
    }[failure_target]

    def fail_on_selected_target(source: Path, target: Path) -> None:
        if target == selected_target:
            raise OSError(f"injected {failure_target} replacement failure")
        real_replace(source, target)

    monkeypatch.setattr(dataset_release_module, "_atomic_replace", fail_on_selected_target)

    with pytest.raises(OSError, match="injected"):
        publish_release(staged.output_directory, data_dir, runtime, version_file, site_data)

    assert _tree_bytes(data_dir) == before_data
    assert runtime.read_bytes() == before_runtime
    assert version_file.read_bytes() == before_version
    assert _tree_bytes(site_data) == before_site


def test_publish_rejects_version_filename_manifest_and_runtime_mismatches(
    tmp_path: Path,
) -> None:
    staged = build_staged_release(
        BASE_DATABASE,
        tmp_path / "staged",
        target_version="0.3.0",
        release_date="2026-07-14",
    )
    data_dir, runtime, version_file, site_data = _published_fixture(tmp_path)

    with pytest.raises(ReleaseValidationError, match="new release version"):
        publish_release(
            build_staged_release(
                BASE_DATABASE,
                tmp_path / "current",
                target_version=BASE_DATASET_VERSION,
                release_date="2026-07-13",
            ).output_directory,
            data_dir,
            runtime,
            version_file,
            site_data,
        )

    runtime.write_bytes(runtime.read_bytes() + b"tampered")
    with pytest.raises(ReleaseValidationError, match="runtime hash"):
        publish_release(
            staged.output_directory,
            data_dir,
            runtime,
            version_file,
            site_data,
        )

    shutil.copy2(BASE_DATABASE, runtime)
    version_file.write_text(f"9.9.9\nsha256={BASE_DATASET_SHA256}\n", encoding="utf-8")
    with pytest.raises(ReleaseValidationError, match="code version"):
        publish_release(
            staged.output_directory,
            data_dir,
            runtime,
            version_file,
            site_data,
        )

    version_file.write_text(f"{BASE_DATASET_VERSION}\nsha256={'0' * 64}\n", encoding="utf-8")
    with pytest.raises(ReleaseValidationError, match="runtime hash"):
        publish_release(
            staged.output_directory,
            data_dir,
            runtime,
            version_file,
            site_data,
        )

    version_file.write_text(
        f"{BASE_DATASET_VERSION}\nsha256={BASE_DATASET_SHA256}\n", encoding="utf-8"
    )
    manifest = json.loads(staged.manifest_path.read_text(encoding="utf-8"))
    manifest["artifacts"]["database"] = "wrong.sqlite"
    staged.manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ReleaseValidationError, match="filenames"):
        publish_release(
            staged.output_directory,
            data_dir,
            runtime,
            version_file,
            site_data,
        )


def test_base_hash_is_pinned() -> None:
    assert sha256(BASE_DATABASE) == BASE_DATASET_SHA256
