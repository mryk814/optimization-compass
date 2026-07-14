from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from optimization_compass.content_models import ContentPage, load_content
from optimization_compass.db import KnowledgeRepository, split_ids
from optimization_compass.trace_models import TraceIndex

EntityType = Literal[
    "case",
    "comparison",
    "content",
    "feature",
    "feature_value",
    "implementation",
    "method",
    "problem",
    "source",
    "trace",
    "view",
]


class LinkModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class EntityRelation(LinkModel):
    relation_type: str = Field(min_length=1)
    target_type: EntityType
    target_id: str = Field(min_length=1)


class LinkedEntity(LinkModel):
    entity_type: EntityType
    entity_id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    summary: str = ""
    canonical_url: str | None = None
    aliases: list[str] = Field(default_factory=list)
    external_url: str | None = None
    relations: list[EntityRelation] = Field(default_factory=list)

    @field_validator("canonical_url")
    @classmethod
    def validate_canonical_url(cls, value: str | None) -> str | None:
        if value is not None:
            _validate_route(value)
        return value

    @field_validator("aliases")
    @classmethod
    def validate_aliases(cls, values: list[str]) -> list[str]:
        for value in values:
            _validate_route(value)
        if len(values) != len(set(values)):
            raise ValueError("entity aliases must be unique")
        return values


class EntityLinkIndex(LinkModel):
    contract_version: Literal["1.0.0"] = "1.0.0"
    dataset_version: str = Field(min_length=1)
    generated_at: datetime
    entities: list[LinkedEntity]

    @model_validator(mode="after")
    def validate_graph(self) -> Self:
        keys: dict[tuple[str, str], LinkedEntity] = {}
        routes: dict[str, tuple[str, str]] = {}
        for entity in self.entities:
            key = (entity.entity_type, entity.entity_id)
            if key in keys:
                raise ValueError(f"duplicate entity key: {key[0]}:{key[1]}")
            keys[key] = entity
            for route in ([entity.canonical_url] if entity.canonical_url else []) + entity.aliases:
                owner = routes.get(route)
                if owner is not None:
                    raise ValueError(
                        f"duplicate canonical or alias URL: {route} ({owner[0]}:{owner[1]} and "
                        f"{key[0]}:{key[1]})"
                    )
                routes[route] = key
        for entity in self.entities:
            for relation in entity.relations:
                target = (relation.target_type, relation.target_id)
                if target not in keys:
                    raise ValueError(
                        f"dangling relation from {entity.entity_type}:{entity.entity_id} to "
                        f"{target[0]}:{target[1]}"
                    )
        return self


def build_entity_link_index(
    repository: KnowledgeRepository,
    *,
    dataset_version: str,
    generated_at: datetime,
    trace_index: TraceIndex,
    content_directory: Path,
    gallery_path: Path,
) -> EntityLinkIndex:
    """Build the one canonical cross-artifact graph used by every site journey."""

    content = load_content(content_directory)
    gallery = _load_gallery(gallery_path, dataset_version)
    entities: dict[tuple[EntityType, str], dict[str, Any]] = {}
    relations: defaultdict[tuple[EntityType, str], set[tuple[str, EntityType, str]]] = defaultdict(
        set
    )

    def add(
        entity_type: EntityType,
        entity_id: str,
        label: str,
        *,
        summary: str = "",
        canonical_url: str | None = None,
        aliases: tuple[str, ...] = (),
        external_url: str | None = None,
    ) -> None:
        key = (entity_type, entity_id)
        if key in entities:
            current = entities[key]
            current["aliases"] = sorted(set(current["aliases"]) | set(aliases))
            return
        entities[key] = {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "label": label or entity_id,
            "summary": summary or "",
            "canonical_url": canonical_url,
            "aliases": sorted(aliases),
            "external_url": external_url or None,
        }

    def connect(
        source_type: EntityType,
        source_id: str,
        relation_type: str,
        target_type: EntityType,
        target_id: str,
        *,
        reverse_type: str | None = None,
    ) -> None:
        relations[(source_type, source_id)].add((relation_type, target_type, target_id))
        if reverse_type:
            relations[(target_type, target_id)].add((reverse_type, source_type, source_id))

    methods = repository.fetch_all(
        "SELECT method_id, name_ja, summary, reference_source_ids FROM methods ORDER BY method_id"
    )
    for row in methods:
        add(
            "method",
            str(row["method_id"]),
            str(row["name_ja"] or row["method_id"]),
            summary=str(row["summary"] or ""),
            canonical_url=f"/methods/{row['method_id']}",
        )
        for source_id in split_ids(str(row["reference_source_ids"] or "")):
            connect("method", str(row["method_id"]), "evidence", "source", source_id)

    for row in repository.fetch_all(
        "SELECT problem_id, name_ja, summary FROM problem_archetypes ORDER BY problem_id"
    ):
        add(
            "problem",
            str(row["problem_id"]),
            str(row["name_ja"] or row["problem_id"]),
            summary=str(row["summary"] or ""),
        )
    for row in repository.fetch_all(
        "SELECT feature_id, name_ja, definition FROM problem_features ORDER BY feature_id"
    ):
        add(
            "feature",
            str(row["feature_id"]),
            str(row["name_ja"] or row["feature_id"]),
            summary=str(row["definition"] or ""),
        )
    for row in repository.fetch_all(
        "SELECT feature_id, value_code, label_ja FROM feature_values "
        "ORDER BY feature_id, sort_order, value_code"
    ):
        entity_id = f"{row['feature_id']}:{row['value_code']}"
        add("feature_value", entity_id, str(row["label_ja"] or entity_id))
        connect(
            "feature",
            str(row["feature_id"]),
            "has_value",
            "feature_value",
            entity_id,
            reverse_type="value_of",
        )

    for row in repository.fetch_all(
        "SELECT implementation_id, library_name, solver_name, notes, official_docs_url "
        "FROM implementations ORDER BY implementation_id"
    ):
        label = str(row["library_name"] or row["solver_name"] or row["implementation_id"])
        add(
            "implementation",
            str(row["implementation_id"]),
            label,
            summary=str(row["notes"] or ""),
            external_url=str(row["official_docs_url"] or "") or None,
        )
    for row in repository.fetch_all(
        "SELECT method_id, implementation_id FROM method_implementation_map "
        "ORDER BY method_id, implementation_id"
    ):
        connect(
            "method",
            str(row["method_id"]),
            "implementation",
            "implementation",
            str(row["implementation_id"]),
            reverse_type="implements",
        )

    for row in repository.fetch_all(
        "SELECT source_id, title, supported_claim, url FROM sources ORDER BY source_id"
    ):
        add(
            "source",
            str(row["source_id"]),
            str(row["title"] or row["source_id"]),
            summary=str(row["supported_claim"] or ""),
            canonical_url=f"/sources/{row['source_id']}",
            external_url=str(row["url"] or "") or None,
        )

    for page in content:
        _add_content_entity(add, page)
        for source_id in page.source_ids:
            connect("content", page.content_id, "evidence", "source", source_id)
        for related_id in (*page.prerequisites, *page.related_ids):
            connect("content", page.content_id, "related_content", "content", related_id)
        if page.method_id:
            method_aliases = tuple(page.aliases) or (f"/learn/{page.content_id}",)
            add("method", page.method_id, page.title_ja, aliases=method_aliases)
            connect(
                "method",
                page.method_id,
                "learning",
                "content",
                page.content_id,
                reverse_type="explains",
            )
            for source_id in page.source_ids:
                connect("method", page.method_id, "evidence", "source", source_id)
        for trace_id in page.visualization_ids:
            connect("content", page.content_id, "visualization", "trace", trace_id)
            if page.method_id:
                connect("method", page.method_id, "visualization", "trace", trace_id)
        for comparison_id in page.comparison_ids:
            add(
                "comparison",
                comparison_id,
                comparison_id,
                canonical_url=f"/compare/{comparison_id}",
                aliases=tuple(_aliases_for(page.comparison_aliases, comparison_id)),
            )
            connect("content", page.content_id, "comparison", "comparison", comparison_id)
            if page.method_id:
                connect("method", page.method_id, "comparison", "comparison", comparison_id)

    for entry in trace_index.traces:
        aliases = tuple(
            alias
            for page in content
            for alias in _aliases_for(page.visualization_aliases, entry.trace_id)
        )
        add(
            "trace",
            entry.trace_id,
            entry.title_ja,
            canonical_url=f"/traces/{entry.trace_id}",
            aliases=aliases,
        )
        connect(
            "trace",
            entry.trace_id,
            "visualizes",
            "method",
            entry.method_id,
            reverse_type="visualization",
        )

    for case in gallery["cases"]:
        case_id = str(case["case_id"])
        add(
            "case",
            case_id,
            str(case["title_ja"]),
            summary=str(case["question"]),
            canonical_url=f"/gallery/{case_id}",
        )
        connect(
            "case",
            case_id,
            "problem",
            "problem",
            str(case["problem_archetype_id"]),
            reverse_type="case",
        )
        for feature in case["feature_values"]:
            feature_value_id = f"{feature['feature_id']}:{feature['value']}"
            connect("case", case_id, "feature_value", "feature_value", feature_value_id)
        for method_id in case["candidate_method_ids"]:
            connect(
                "case", case_id, "candidate_method", "method", str(method_id), reverse_type="case"
            )
        for excluded in case["excluded_methods"]:
            connect(
                "case",
                case_id,
                "excluded_method",
                "method",
                str(excluded["method_id"]),
                reverse_type="case",
            )
        for implementation_id in case["implementation_ids"]:
            connect("case", case_id, "implementation", "implementation", str(implementation_id))
        for visualization_id in case["visualization_ids"]:
            visualization_type: EntityType = (
                "trace" if ("trace", str(visualization_id)) in entities else "view"
            )
            if visualization_type == "view":
                add("view", str(visualization_id), str(visualization_id))
            connect("case", case_id, "visualization", visualization_type, str(visualization_id))
        for comparison_id in case["comparison_ids"]:
            add(
                "comparison",
                str(comparison_id),
                str(comparison_id),
                canonical_url=f"/compare/{comparison_id}",
            )
            connect("case", case_id, "comparison", "comparison", str(comparison_id))
        for source_id in case["source_ids"]:
            connect("case", case_id, "evidence", "source", str(source_id))

    linked_entities = []
    for key in sorted(entities):
        data = entities[key]
        linked_entities.append(
            LinkedEntity(
                **data,
                relations=[
                    EntityRelation(
                        relation_type=relation_type,
                        target_type=target_type,
                        target_id=target_id,
                    )
                    for relation_type, target_type, target_id in sorted(relations[key])
                ],
            )
        )
    return EntityLinkIndex(
        dataset_version=dataset_version,
        generated_at=generated_at,
        entities=linked_entities,
    )


def _add_content_entity(add: Any, page: ContentPage) -> None:
    add(
        "content",
        page.content_id,
        page.title_ja,
        summary=page.summary,
        canonical_url=None if page.method_id else f"/learn/{page.content_id}",
    )


def _aliases_for(pairs: tuple[tuple[str, str], ...], entity_id: str) -> list[str]:
    return [alias for target_id, alias in pairs if target_id == entity_id]


def _load_gallery(path: Path, dataset_version: str) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("gallery index must be an object")
    payload: dict[str, Any] = raw
    if payload.get("contract_version") != "1.0.0":
        raise ValueError("unsupported gallery contract version")
    if payload.get("dataset_version") != dataset_version:
        raise ValueError("gallery dataset version does not match the release")
    if not isinstance(payload.get("cases"), list):
        raise ValueError("gallery cases must be a list")
    return payload


def _validate_route(value: str) -> None:
    if not value.startswith("/") or value.startswith("//") or "?" in value or "#" in value:
        raise ValueError(f"invalid site route: {value}")
