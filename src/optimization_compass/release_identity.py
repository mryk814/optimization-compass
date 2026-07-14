from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


class ReleaseIdentityError(ValueError):
    pass


@dataclass(frozen=True)
class ReleaseAuthority:
    schema_version: int
    dataset_version: str
    release_date: str
    base_dataset_version: str
    base_database_sha256: str


@dataclass(frozen=True)
class DatasetReleaseIdentity:
    schema_version: int
    dataset_version: str
    release_date: str
    database_sha256: str

    def as_json_object(self) -> dict[str, int | str]:
        return asdict(self)


def load_release_authority(path: Path) -> ReleaseAuthority:
    payload = _read_json_object(path, "release authority")
    expected_fields = {
        "schema_version",
        "dataset_version",
        "release_date",
        "base_dataset_version",
        "base_database_sha256",
    }
    if set(payload) != expected_fields:
        raise ReleaseIdentityError("release authority fields do not match schema")
    if payload["schema_version"] != 1:
        raise ReleaseIdentityError("unsupported release authority schema version")
    authority = ReleaseAuthority(
        schema_version=1,
        dataset_version=_required_string(payload, "dataset_version"),
        release_date=_required_string(payload, "release_date"),
        base_dataset_version=_required_string(payload, "base_dataset_version"),
        base_database_sha256=_required_string(payload, "base_database_sha256"),
    )
    validate_release_identity(authority.dataset_version, authority.release_date)
    validate_semantic_version(authority.base_dataset_version)
    validate_sha256(authority.base_database_sha256, "base_database_sha256")
    if authority.dataset_version == authority.base_dataset_version:
        raise ReleaseIdentityError("release authority must advance the pinned base version")
    return authority


def parse_dataset_release_identity(payload: object) -> DatasetReleaseIdentity:
    if not isinstance(payload, dict):
        raise ReleaseIdentityError("dataset release identity must be an object")
    expected_fields = {"schema_version", "dataset_version", "release_date", "database_sha256"}
    if set(payload) != expected_fields:
        raise ReleaseIdentityError("dataset release identity fields do not match schema")
    if payload["schema_version"] != 1:
        raise ReleaseIdentityError("unsupported dataset release identity schema version")
    identity = DatasetReleaseIdentity(
        schema_version=1,
        dataset_version=_required_string(payload, "dataset_version"),
        release_date=_required_string(payload, "release_date"),
        database_sha256=_required_string(payload, "database_sha256"),
    )
    validate_release_identity(identity.dataset_version, identity.release_date)
    validate_sha256(identity.database_sha256, "database_sha256")
    return identity


def load_dataset_release_identity(path: Path) -> DatasetReleaseIdentity:
    return parse_dataset_release_identity(_read_json_object(path, "dataset release identity"))


def validate_release_identity(version: str, release_date: str) -> None:
    validate_semantic_version(version)
    try:
        datetime.strptime(release_date, "%Y-%m-%d")
    except ValueError as error:
        raise ReleaseIdentityError(f"invalid release date: {release_date}") from error


def validate_semantic_version(version: str) -> None:
    if re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version) is None:
        raise ReleaseIdentityError(f"invalid semantic dataset version: {version}")


def validate_sha256(value: str, field: str) -> None:
    if re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise ReleaseIdentityError(f"invalid {field}")


def canonical_identity_json(identity: DatasetReleaseIdentity) -> str:
    return (
        json.dumps(identity.as_json_object(), ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    )


def _read_json_object(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ReleaseIdentityError(f"{label} is not valid JSON: {path}") from error
    if not isinstance(payload, dict):
        raise ReleaseIdentityError(f"{label} must be an object")
    return payload


def _required_string(payload: dict[str, Any], field: str) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not value:
        raise ReleaseIdentityError(f"release identity field is invalid: {field}")
    return value
