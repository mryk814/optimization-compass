from __future__ import annotations

import json
from pathlib import Path

import pytest

from optimization_compass.dataset_release import (
    ReleaseValidationError,
    build_staged_release,
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
    assert verification.table_count == 40


def test_format_verifier_rejects_mutated_json(tmp_path: Path) -> None:
    release = build_staged_release(BASE_DATABASE, tmp_path / "release")
    json_path = next(release.output_directory.glob("*.json"))
    if json_path.name.endswith("_manifest.json"):
        json_path = next(
            path for path in release.output_directory.glob("*.json") if "manifest" not in path.name
        )
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    payload["tables"]["methods"][0]["name_en"] = "tampered"
    json_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    with pytest.raises(ReleaseValidationError, match="json"):
        verify_release_tree(release.output_directory)
