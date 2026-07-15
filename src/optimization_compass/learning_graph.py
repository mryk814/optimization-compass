from __future__ import annotations

import json
from typing import Any

from optimization_compass.db import KnowledgeRepository
from optimization_compass.entity_links import EntityLinkIndex, LinkedEntity
from optimization_compass.trace_models import TraceIndex


def build_learning_graph_index(
    repository: KnowledgeRepository,
    *,
    dataset_version: str,
    entity_links: EntityLinkIndex,
    trace_index: TraceIndex,
) -> dict[str, Any]:
    """Export learning and search data with resolved labels and destinations."""

    edges = repository.fetch_all(
        "SELECT * FROM learning_edges WHERE status = 'current' ORDER BY display_order, edge_id"
    )
    aliases = repository.fetch_all("SELECT * FROM terminology_aliases ORDER BY term_id")
    for edge in edges:
        edge["source_ids"] = json.loads(str(edge.pop("source_ids_json")))
    json_fields = (
        "abbreviations",
        "synonyms",
        "domain_terms",
        "misspellings",
        "deprecated_terms",
        "source_ids",
    )
    for alias in aliases:
        for field in json_fields:
            alias[field] = json.loads(str(alias.pop(f"{field}_json")))

    endpoint_keys = {
        (str(edge[key]), str(edge[key.replace("type", "id")]))
        for edge in edges
        for key in ("source_type", "target_type")
    }
    endpoint_keys.update((str(row["target_type"]), str(row["target_id"])) for row in aliases)
    entities = [
        _resolve_entity(repository, entity_links, trace_index, entity_type, entity_id)
        for entity_type, entity_id in sorted(endpoint_keys)
    ]
    return {
        "contract_version": "1.0.0",
        "dataset_version": dataset_version,
        "edges": edges,
        "aliases": aliases,
        "entities": entities,
    }


def _resolve_entity(
    repository: KnowledgeRepository,
    entity_links: EntityLinkIndex,
    trace_index: TraceIndex,
    entity_type: str,
    entity_id: str,
) -> dict[str, str | None]:
    linked = _linked_entity(entity_links, entity_type, entity_id, repository, trace_index)
    label_ja, label_en = _labels(repository, entity_type, entity_id)
    return {
        "entity_type": entity_type,
        "entity_id": entity_id,
        "label_ja": label_ja,
        "label_en": label_en,
        "canonical_url": linked.canonical_url if linked else _fallback_route(entity_type),
        "external_url": linked.external_url if linked else None,
    }


def _linked_entity(
    index: EntityLinkIndex,
    entity_type: str,
    entity_id: str,
    repository: KnowledgeRepository,
    trace_index: TraceIndex,
) -> LinkedEntity | None:
    if entity_type == "scenario":
        trace_ids = sorted(
            entry.trace_id for entry in trace_index.traces if entry.scenario_id == entity_id
        )
        return next(
            (
                entity
                for trace_id in trace_ids
                for entity in index.entities
                if _key(entity) == ("trace", trace_id)
            ),
            None,
        )
    if entity_type == "view_preset":
        row = repository.fetch_one(
            "SELECT view_id FROM view_presets WHERE preset_id = ?", (entity_id,)
        )
        entity_id = str(row["view_id"]) if row else entity_id
        entity_type = "view"
    return next(
        (entity for entity in index.entities if _key(entity) == (entity_type, entity_id)), None
    )


def _labels(repository: KnowledgeRepository, entity_type: str, entity_id: str) -> tuple[str, str]:
    definitions = {
        "method": ("methods", "method_id", "name_ja", "name_en"),
        "problem": ("problem_archetypes", "problem_id", "name_ja", "name_en"),
        "feature": ("problem_features", "feature_id", "name_ja", "name_en"),
        "case": ("example_cases", "case_id", "title_ja", "title_ja"),
        "implementation": (
            "implementations",
            "implementation_id",
            "library_name",
            "solver_name",
        ),
        "scenario": ("demo_scenarios", "scenario_id", "name_ja", "name_en"),
        "comparison": ("comparison_sets", "comparison_set_id", "name_ja", "name_en"),
        "view_preset": ("view_presets", "preset_id", "name_ja", "name_en"),
    }
    table, id_column, ja_column, en_column = definitions[entity_type]
    row = repository.fetch_one(
        f'SELECT "{ja_column}" AS label_ja, "{en_column}" AS label_en '
        f'FROM "{table}" WHERE "{id_column}" = ?',
        (entity_id,),
    )
    if not row:
        raise ValueError(f"learning entity does not resolve: {entity_type}:{entity_id}")
    label_ja = str(row["label_ja"] or row["label_en"] or entity_id)
    label_en = str(row["label_en"] or row["label_ja"] or entity_id)
    return label_ja, label_en


def _fallback_route(entity_type: str) -> str | None:
    return "/map" if entity_type in {"problem", "feature", "view_preset"} else None


def _key(entity: LinkedEntity) -> tuple[str, str]:
    return entity.entity_type, entity.entity_id
