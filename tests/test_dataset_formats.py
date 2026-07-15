from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
from pathlib import Path

import pytest

import optimization_compass.dataset_release as dataset_release_module
from optimization_compass.dataset_release import (
    ReleaseValidationError,
    build_staged_release,
    verify_database,
    verify_release_tree,
)

ROOT = Path(__file__).parents[1]
BASE_DATABASE = ROOT / "data/optimization_method_selection_database_v0.2.0.sqlite"


def test_every_staged_format_round_trips_exactly(tmp_path: Path) -> None:
    release = build_staged_release(BASE_DATABASE, tmp_path / "release")

    verification = verify_release_tree(release.output_directory)

    assert verification.ok is True
    assert verification.formats == {
        "csv_directory",
        "csv_zip",
        "ddl",
        "json",
        "jsonl",
        "sqlite",
        "xlsx",
    }
    assert verification.table_count == 49
    database_verification = verify_database(release.database_path)
    check_020 = next(check for check in database_verification.checks if check.check_id == "CHK020")
    assert check_020.status == "not_run"


def test_format_verifier_rejects_mutated_json(tmp_path: Path) -> None:
    release = build_staged_release(BASE_DATABASE, tmp_path / "release")
    manifest = json.loads(release.manifest_path.read_text(encoding="utf-8"))
    json_path = release.output_directory / manifest["artifacts"]["json"]
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    payload["tables"]["methods"][0]["name_en"] = "tampered"
    json_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    with pytest.raises(ReleaseValidationError, match="json"):
        verify_release_tree(release.output_directory)


def test_release_tree_rejects_manifest_database_hash_mismatch(tmp_path: Path) -> None:
    release = build_staged_release(BASE_DATABASE, tmp_path / "release")
    manifest = json.loads(release.manifest_path.read_text(encoding="utf-8"))
    manifest["database_sha256"] = "0" * 64
    release.manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ReleaseValidationError, match="database hash"):
        verify_release_tree(release.output_directory)


@pytest.mark.parametrize("format_name", ["json", "jsonl"])
@pytest.mark.parametrize(
    ("field", "wrong_value"),
    [("version", "9.9.9"), ("release_date", "2026-07-15")],
)
def test_release_tree_rejects_self_hashed_wrong_format_identity(
    tmp_path: Path, format_name: str, field: str, wrong_value: str
) -> None:
    release = build_staged_release(
        BASE_DATABASE,
        tmp_path / "release",
        target_version="0.3.0",
        release_date="2026-07-14",
    )
    manifest = json.loads(release.manifest_path.read_text(encoding="utf-8"))
    artifact = release.output_directory / manifest["artifacts"][format_name]
    if format_name == "json":
        payload = json.loads(artifact.read_text(encoding="utf-8"))
        payload[field] = wrong_value
        artifact.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    else:
        lines = artifact.read_text(encoding="utf-8").splitlines()
        header = json.loads(lines[0])
        header[field] = wrong_value
        lines[0] = json.dumps(header, ensure_ascii=False)
        artifact.write_text("\n".join(lines) + "\n", encoding="utf-8")
    relative = artifact.relative_to(release.output_directory).as_posix()
    content = artifact.read_bytes()
    manifest["files"][relative] = {
        "bytes": len(content),
        "sha256": hashlib.sha256(content).hexdigest(),
    }
    release.manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ReleaseValidationError, match="identity"):
        verify_release_tree(release.output_directory)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("schema_version", 3, "manifest schema"),
        ("version", "not-semver", "semantic dataset version"),
        ("release_date", "14/07/2026", "release date"),
    ],
)
def test_release_tree_validates_manifest_identity_before_artifact_paths(
    tmp_path: Path, field: str, value: object, message: str
) -> None:
    release = build_staged_release(BASE_DATABASE, tmp_path / "release")
    manifest = json.loads(release.manifest_path.read_text(encoding="utf-8"))
    manifest[field] = value
    release.manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ReleaseValidationError, match=message):
        verify_release_tree(release.output_directory)


def _rewrite_release_tree_from_database(release_directory: Path) -> None:
    manifest_path = next(release_directory.glob("*_manifest.json"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    version = manifest["version"]
    release_date = manifest["release_date"]
    stem = dataset_release_module.DATASET_STEM.format(version=version)
    database_path = release_directory / f"{stem}.sqlite"
    snapshot = dataset_release_module.read_snapshot(database_path)
    dataset_release_module._write_ddl(database_path, release_directory / f"{stem}_schema.sql")
    dataset_release_module._write_json(
        snapshot,
        release_directory / f"{stem}.json",
        version=version,
        release_date=release_date,
    )
    dataset_release_module._write_jsonl(
        snapshot,
        release_directory / f"{stem}.jsonl",
        version=version,
        release_date=release_date,
    )
    csv_directory = release_directory / f"{stem}_csv"
    shutil.rmtree(csv_directory)
    dataset_release_module._write_csv_directory(snapshot, csv_directory)
    dataset_release_module._write_csv_zip(
        csv_directory,
        release_directory / f"{stem}_csv.zip",
        release_date=release_date,
    )
    dataset_release_module._write_xlsx(
        snapshot,
        release_directory / f"{stem}.xlsx",
        release_date=release_date,
    )
    dataset_release_module._write_report(
        snapshot,
        release_directory / f"{stem}_report.md",
        version=version,
        release_date=release_date,
    )
    payload = dataset_release_module._manifest_payload(
        release_directory,
        stem,
        database_path,
        snapshot,
        version=version,
        release_date=release_date,
        include_manifest=False,
    )
    manifest_path.write_text(
        dataset_release_module._canonical_json(payload, pretty=True), encoding="utf-8"
    )


def test_release_tree_requires_atlas_when_all_contract_tables_and_checks_are_removed(
    tmp_path: Path,
) -> None:
    release = build_staged_release(BASE_DATABASE, tmp_path / "release")
    connection = sqlite3.connect(release.database_path)
    try:
        connection.execute("PRAGMA foreign_keys = OFF")
        for table in dataset_release_module.ATLAS_TABLES:
            connection.execute(f'DROP TABLE "{table}"')
        connection.execute("DELETE FROM release_checks WHERE check_id >= 'CHK013'")
        connection.commit()
    finally:
        connection.close()
    _rewrite_release_tree_from_database(release.output_directory)

    with pytest.raises(ReleaseValidationError, match="live release checks"):
        verify_release_tree(release.output_directory)


def test_release_tree_rejects_self_consistent_wrong_sqlite_release_identity(
    tmp_path: Path,
) -> None:
    release = build_staged_release(
        BASE_DATABASE,
        tmp_path / "release",
        target_version="0.3.0",
        release_date="2026-07-14",
    )
    connection = sqlite3.connect(release.database_path)
    try:
        connection.execute(
            "UPDATE version_history SET release_date = '2026-07-15' WHERE version = '0.3.0'"
        )
        connection.commit()
    finally:
        connection.close()
    _rewrite_release_tree_from_database(release.output_directory)

    with pytest.raises(ReleaseValidationError, match="sqlite release identity"):
        verify_release_tree(release.output_directory)


def test_release_tree_rejects_self_hashed_wrong_report_identity(tmp_path: Path) -> None:
    release = build_staged_release(BASE_DATABASE, tmp_path / "release")
    manifest = json.loads(release.manifest_path.read_text(encoding="utf-8"))
    report = release.output_directory / manifest["artifacts"]["report"]
    report.write_text(
        report.read_text(encoding="utf-8").replace(
            f"- Version: `{manifest['version']}`", "- Version: `9.9.9`"
        ),
        encoding="utf-8",
    )
    relative = report.relative_to(release.output_directory).as_posix()
    content = report.read_bytes()
    manifest["files"][relative] = {
        "bytes": len(content),
        "sha256": hashlib.sha256(content).hexdigest(),
    }
    release.manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ReleaseValidationError, match="report release identity"):
        verify_release_tree(release.output_directory)
