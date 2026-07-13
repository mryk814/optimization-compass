from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
from pathlib import Path

import pytest

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

    first = build_staged_release(BASE_DATABASE, tmp_path / "first")
    second = build_staged_release(BASE_DATABASE, tmp_path / "second")

    assert before == BASE_DATASET_SHA256
    assert sha256(BASE_DATABASE) == before
    assert first.version == BASE_DATASET_VERSION
    assert tree_hash(first.output_directory) == tree_hash(second.output_directory)
    assert first.tree_sha256 == second.tree_sha256


def test_publish_rejects_version_filename_manifest_and_runtime_mismatches(
    tmp_path: Path,
) -> None:
    staged = build_staged_release(BASE_DATABASE, tmp_path / "staged")
    data_dir = tmp_path / "published"
    data_dir.mkdir()
    runtime = tmp_path / "knowledge.sqlite"
    shutil.copy2(BASE_DATABASE, runtime)
    version_file = tmp_path / "DATASET_VERSION"
    version_file.write_text(
        f"{BASE_DATASET_VERSION}\nsha256={BASE_DATASET_SHA256}\n", encoding="utf-8"
    )

    with pytest.raises(ReleaseValidationError, match="new release version"):
        publish_release(
            staged.output_directory,
            data_dir,
            runtime,
            version_file,
            version=BASE_DATASET_VERSION,
        )

    runtime.write_bytes(runtime.read_bytes() + b"tampered")
    with pytest.raises(ReleaseValidationError, match="runtime hash"):
        publish_release(
            staged.output_directory,
            data_dir,
            runtime,
            version_file,
            version="0.3.0",
        )

    shutil.copy2(BASE_DATABASE, runtime)
    with pytest.raises(ReleaseValidationError, match="manifest version"):
        publish_release(
            staged.output_directory,
            data_dir,
            runtime,
            version_file,
            version="0.3.0",
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
            version="0.3.0",
        )


def test_base_hash_is_pinned() -> None:
    assert sha256(BASE_DATABASE) == BASE_DATASET_SHA256
