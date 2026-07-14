from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from optimization_compass.entity_links import (
    EntityLinkIndex,
    EntityRelation,
    LinkedEntity,
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
