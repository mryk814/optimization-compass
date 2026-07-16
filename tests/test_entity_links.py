from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from optimization_compass.entity_links import (
    EntityLinkIndex,
    EntityRelation,
    LinkedEntity,
    _load_gallery,
)


def entity(
    entity_type: str,
    entity_id: str,
    route: str | None,
    *,
    relations: list[EntityRelation] | None = None,
) -> LinkedEntity:
    return LinkedEntity(
        entity_type=entity_type,
        entity_id=entity_id,
        label=entity_id,
        canonical_url=route,
        relations=relations or [],
    )


def test_relation_index_rejects_duplicate_canonical_urls() -> None:
    with pytest.raises(ValidationError, match="duplicate canonical or alias URL"):
        EntityLinkIndex(
            dataset_version="1.0.0",
            generated_at=datetime(2026, 1, 1, tzinfo=UTC),
            entities=[
                entity("method", "M_ONE", "/methods/shared"),
                entity("method", "M_TWO", "/methods/shared"),
            ],
        )


def test_relation_index_rejects_dangling_relations() -> None:
    with pytest.raises(ValidationError, match="dangling relation"):
        EntityLinkIndex(
            dataset_version="1.0.0",
            generated_at=datetime(2026, 1, 1, tzinfo=UTC),
            entities=[
                entity(
                    "method",
                    "M_ONE",
                    "/methods/M_ONE",
                    relations=[
                        EntityRelation(
                            relation_type="visualization",
                            target_type="trace",
                            target_id="missing",
                        )
                    ],
                )
            ],
        )


def test_gallery_loader_requires_v2_candidate_reasons_and_limitations(tmp_path: Path) -> None:
    path = tmp_path / "gallery.json"
    payload = {
        "contract_version": "2.0.0",
        "dataset_version": "1.0.0",
        "cases": [
            {
                "candidate_methods": [{"method_id": "M_ONE", "reason": "理由"}],
                "limitations": ["限界"],
            }
        ],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")

    assert _load_gallery(path, "1.0.0") == payload

    payload["contract_version"] = "1.0.0"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="unsupported gallery contract version"):
        _load_gallery(path, "1.0.0")
