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

    first = build_staged_release(
        BASE_DATABASE,
        tmp_path / "first",
        target_version="0.15.2",
        release_date="2026-07-18",
    )
    second = build_staged_release(
        BASE_DATABASE,
        tmp_path / "second",
        target_version="0.15.2",
        release_date="2026-07-18",
    )

    assert before == BASE_DATASET_SHA256
    assert sha256(BASE_DATABASE) == before
    assert first.version == "0.15.2"
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
        target_version="0.15.2",
        release_date="2026-07-18",
    )

    assert release.version == "0.15.2"
    assert release.database_path.name.endswith("_v0.15.2.sqlite")
    manifest = json.loads(release.manifest_path.read_text(encoding="utf-8"))
    assert manifest["version"] == "0.15.2"
    assert manifest["release_date"] == "2026-07-18"
    assert all("v0.15.2" in name for name in manifest["artifacts"].values())
    json_path = release.output_directory / "optimization_method_selection_database_v0.15.2.json"
    json_payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert (json_payload["version"], json_payload["release_date"]) == (
        "0.15.2",
        "2026-07-18",
    )
    jsonl_header = json.loads(
        next(release.output_directory.glob("*.jsonl")).read_text(encoding="utf-8").splitlines()[0]
    )
    assert (jsonl_header["version"], jsonl_header["release_date"]) == (
        "0.15.2",
        "2026-07-18",
    )
    assert "Version: `0.15.2`" in next(release.output_directory.glob("*_report.md")).read_text(
        encoding="utf-8"
    )
    connection = sqlite3.connect(release.database_path)
    try:
        versions = connection.execute(
            "SELECT version, release_date FROM version_history ORDER BY release_date"
        ).fetchall()
        revisions = connection.execute(
            "SELECT version, date FROM model_revisions WHERE version = '0.15.2'"
        ).fetchall()
    finally:
        connection.close()
    assert ("0.15.2", "2026-07-18") in versions
    assert revisions == [("0.15.2", "2026-07-18")]


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

    staged = build_staged_release(
        BASE_DATABASE,
        tmp_path / "staged",
        target_version="0.15.2",
        release_date="2026-07-18",
    )
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
    staged = build_staged_release(
        BASE_DATABASE,
        tmp_path / "staged",
        target_version="0.15.2",
        release_date="2026-07-18",
    )
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


def _published_fixture(tmp_path: Path) -> tuple[Path, Path, Path, Path, Path]:
    data_dir = tmp_path / "published"
    (data_dir / "releases").mkdir(parents=True)
    (data_dir / "keep.txt").write_text("original", encoding="utf-8")
    (data_dir / "releases/catalog.json").write_text(
        '{"current_version":null,"releases":[],"schema_version":1}\n',
        encoding="utf-8",
    )
    runtime = tmp_path / "knowledge.sqlite"
    shutil.copy2(BASE_DATABASE, runtime)
    version_file = tmp_path / "DATASET_VERSION"
    version_file.write_text(
        f"{BASE_DATASET_VERSION}\nsha256={BASE_DATASET_SHA256}\n", encoding="utf-8"
    )
    site_data = tmp_path / "site-data"
    site_data.mkdir()
    (site_data / "keep.json").write_text('{"status":"original"}\n', encoding="utf-8")
    readme = tmp_path / "README.md"
    readme.write_text("# current release\n", encoding="utf-8")
    return data_dir, runtime, version_file, site_data, readme


def _tree_bytes(directory: Path) -> dict[str, bytes]:
    return {
        path.relative_to(directory).as_posix(): path.read_bytes()
        for path in directory.rglob("*")
        if path.is_file()
    }


def _publish_release(
    staged_directory: Path,
    data_directory: Path,
    runtime_database: Path,
    version_file: Path,
    site_data_directory: Path,
    readme_path: Path,
    readme_content: str,
) -> None:
    manifest_path = next(staged_directory.glob("*_manifest.json"))
    version = json.loads(manifest_path.read_text(encoding="utf-8"))["version"]
    publish_release(
        staged_directory,
        data_directory,
        runtime_database,
        version_file,
        site_data_directory,
        readme_path,
        readme_content,
        readme_path.parent / "external-bundles",
        source_commit="1" * 40,
        tag=f"v{version}",
    )


def test_publish_succeeds_for_a_consistent_new_version(tmp_path: Path) -> None:
    staged = build_staged_release(
        BASE_DATABASE,
        tmp_path / "staged",
        target_version="0.15.2",
        release_date="2026-07-18",
    )
    data_dir, runtime, version_file, site_data, readme = _published_fixture(tmp_path)

    _publish_release(
        staged.output_directory,
        data_dir,
        runtime,
        version_file,
        site_data,
        readme,
        "# next release\n",
    )

    assert (data_dir / "keep.txt").read_text(encoding="utf-8") == "original"
    assert not (data_dir / staged.database_path.name).exists()
    manifest = json.loads(staged.manifest_path.read_text(encoding="utf-8"))
    assert (data_dir / staged.manifest_path.name).read_bytes() == staged.manifest_path.read_bytes()
    for key in ("ddl", "report", "release_identity"):
        relative = str(manifest["artifacts"][key])
        assert (data_dir / relative).read_bytes() == (
            staged.output_directory / relative
        ).read_bytes()
    assert not (data_dir / str(manifest["artifacts"]["json"])).exists()
    assert len(list((tmp_path / "external-bundles").glob("*_bundle.zip"))) == 1
    catalog = json.loads((data_dir / "releases/catalog.json").read_text(encoding="utf-8"))
    assert catalog["current_version"] == "0.15.2"
    assert catalog["releases"][0]["source_commit"] == "1" * 40
    assert catalog["releases"][0]["manifest_sha256"] == sha256(staged.manifest_path)
    assert runtime.read_bytes() == staged.database_path.read_bytes()
    assert version_file.read_text(encoding="utf-8") == (f"0.15.2\nsha256={sha256(runtime)}\n")
    assert _tree_bytes(site_data) == _tree_bytes(staged.site_data_directory)
    assert readme.read_text(encoding="utf-8") == "# next release\n"


@pytest.mark.parametrize("failure_target", ["data", "runtime", "version", "site", "readme"])
def test_publish_rolls_back_all_targets_after_injected_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure_target: str
) -> None:
    staged = build_staged_release(
        BASE_DATABASE,
        tmp_path / "staged",
        target_version="0.15.2",
        release_date="2026-07-18",
    )
    data_dir, runtime, version_file, site_data, readme = _published_fixture(tmp_path)
    before_data = _tree_bytes(data_dir)
    before_runtime = runtime.read_bytes()
    before_version = version_file.read_bytes()
    before_site = _tree_bytes(site_data)
    before_readme = readme.read_bytes()
    real_replace = dataset_release_module._atomic_replace
    selected_target = {
        "data": data_dir,
        "runtime": runtime,
        "version": version_file,
        "site": site_data,
        "readme": readme,
    }[failure_target]

    def fail_on_selected_target(source: Path, target: Path) -> None:
        if target == selected_target:
            raise OSError(f"injected {failure_target} replacement failure")
        real_replace(source, target)

    monkeypatch.setattr(dataset_release_module, "_atomic_replace", fail_on_selected_target)

    with pytest.raises(OSError, match="injected"):
        _publish_release(
            staged.output_directory,
            data_dir,
            runtime,
            version_file,
            site_data,
            readme,
            "# next release\n",
        )

    assert _tree_bytes(data_dir) == before_data
    assert runtime.read_bytes() == before_runtime
    assert version_file.read_bytes() == before_version
    assert _tree_bytes(site_data) == before_site
    assert readme.read_bytes() == before_readme
    assert not list((tmp_path / "external-bundles").glob("*_bundle.zip"))


def test_publish_rejects_version_filename_manifest_and_runtime_mismatches(
    tmp_path: Path,
) -> None:
    staged = build_staged_release(
        BASE_DATABASE,
        tmp_path / "staged",
        target_version="0.15.2",
        release_date="2026-07-18",
    )
    data_dir, runtime, version_file, site_data, readme = _published_fixture(tmp_path)

    version_file.write_text(
        "0.15.2\nsha256=ignored-for-same-version-check\n",
        encoding="utf-8",
    )
    with pytest.raises(ReleaseValidationError, match="new release version"):
        _publish_release(
            staged.output_directory,
            data_dir,
            runtime,
            version_file,
            site_data,
            readme,
            "# next release\n",
        )

    version_file.write_text(
        f"{BASE_DATASET_VERSION}\nsha256={BASE_DATASET_SHA256}\n",
        encoding="utf-8",
    )

    runtime.write_bytes(runtime.read_bytes() + b"tampered")
    with pytest.raises(ReleaseValidationError, match="runtime hash"):
        _publish_release(
            staged.output_directory,
            data_dir,
            runtime,
            version_file,
            site_data,
            readme,
            "# next release\n",
        )

    shutil.copy2(BASE_DATABASE, runtime)
    version_file.write_text(f"9.9.9\nsha256={BASE_DATASET_SHA256}\n", encoding="utf-8")
    with pytest.raises(ReleaseValidationError, match="code version"):
        _publish_release(
            staged.output_directory,
            data_dir,
            runtime,
            version_file,
            site_data,
            readme,
            "# next release\n",
        )

    version_file.write_text(f"{BASE_DATASET_VERSION}\nsha256={'0' * 64}\n", encoding="utf-8")
    with pytest.raises(ReleaseValidationError, match="runtime hash"):
        _publish_release(
            staged.output_directory,
            data_dir,
            runtime,
            version_file,
            site_data,
            readme,
            "# next release\n",
        )

    version_file.write_text(
        f"{BASE_DATASET_VERSION}\nsha256={BASE_DATASET_SHA256}\n", encoding="utf-8"
    )
    manifest = json.loads(staged.manifest_path.read_text(encoding="utf-8"))
    manifest["artifacts"]["database"] = "wrong.sqlite"
    staged.manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ReleaseValidationError, match="filenames"):
        _publish_release(
            staged.output_directory,
            data_dir,
            runtime,
            version_file,
            site_data,
            readme,
            "# next release\n",
        )


def test_publish_requires_catalog_and_external_bundle_output(tmp_path: Path) -> None:
    staged = build_staged_release(
        BASE_DATABASE,
        tmp_path / "staged",
        target_version="0.15.2",
        release_date="2026-07-18",
    )
    data_dir, runtime, version_file, site_data, readme = _published_fixture(tmp_path)
    catalog = data_dir / "releases/catalog.json"
    catalog.unlink()

    with pytest.raises(ReleaseValidationError, match="release catalog"):
        _publish_release(
            staged.output_directory,
            data_dir,
            runtime,
            version_file,
            site_data,
            readme,
            "# next release\n",
        )

    catalog.write_text(
        '{"current_version":null,"releases":[],"schema_version":1}\n',
        encoding="utf-8",
    )
    with pytest.raises(ReleaseValidationError, match="outside the repository"):
        publish_release(
            staged.output_directory,
            data_dir,
            runtime,
            version_file,
            site_data,
            readme,
            "# next release\n",
            ROOT / ".release-bundle-test",
            source_commit="1" * 40,
            tag="v0.15.2",
        )


def test_base_hash_is_pinned() -> None:
    assert sha256(BASE_DATABASE) == BASE_DATASET_SHA256
