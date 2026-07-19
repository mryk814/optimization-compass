from __future__ import annotations

import json
from pathlib import Path

import pytest

from optimization_compass.dataset_release import RELEASE_AUTHORITY, RELEASE_AUTHORITY_PATH
from optimization_compass.release_identity import (
    DatasetReleaseIdentity,
    ReleaseIdentityError,
    canonical_identity_json,
    load_dataset_release_identity,
    load_release_authority,
)


def test_repository_release_authority_is_the_target_version_source() -> None:
    authority = load_release_authority(RELEASE_AUTHORITY_PATH)

    assert authority == RELEASE_AUTHORITY
    assert authority.dataset_version == "0.18.8"
    assert authority.base_dataset_version == "0.2.0"


def test_dataset_release_identity_round_trips_canonically(tmp_path: Path) -> None:
    identity = DatasetReleaseIdentity(
        schema_version=1,
        dataset_version="0.3.0",
        release_date="2026-07-15",
        database_sha256="a" * 64,
    )
    path = tmp_path / "release.json"
    path.write_text(canonical_identity_json(identity), encoding="utf-8")

    assert load_dataset_release_identity(path) == identity
    assert path.read_text(encoding="utf-8").endswith("\n")


def test_release_authority_rejects_unknown_fields(tmp_path: Path) -> None:
    payload = json.loads(RELEASE_AUTHORITY_PATH.read_text(encoding="utf-8"))
    payload["legacy_version"] = "0.2.0"
    path = tmp_path / "authority.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ReleaseIdentityError, match="fields"):
        load_release_authority(path)
