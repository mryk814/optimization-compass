from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AnswerBinding(ContractModel):
    question_id: str = Field(min_length=1)
    answer_value: str = Field(min_length=1)


class EntityReference(ContractModel):
    entity_type: str = Field(min_length=1)
    entity_id: str = Field(min_length=1)


class ViewEntity(ContractModel):
    entity_type: str = Field(min_length=1)
    entity_id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    label_en: str = ""
    summary: str
    url: str
    source_ids: list[str] = Field(default_factory=list)


class ViewNode(ContractModel):
    node_id: str = Field(min_length=1)
    node_type: str = Field(min_length=1)
    label: str = Field(min_length=1)
    label_en: str = ""
    summary: str
    display_order: int = Field(ge=0)
    default_collapsed: bool
    emphasis: Literal["primary", "normal", "muted"]
    parent_node_id: str | None = None
    question_id: str | None = None
    answer_type: Literal["single_choice", "multi_choice"] | None = None
    allowed_answers: list[str] = Field(default_factory=list)
    answer_bindings: list[AnswerBinding] = Field(default_factory=list)
    related_entities: list[EntityReference]
    source_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_question_metadata(self) -> ViewNode:
        metadata = (self.question_id, self.answer_type, bool(self.allowed_answers))
        if self.node_type == "question" and not all(metadata):
            raise ValueError("question nodes require question_id, answer_type, and allowed_answers")
        if self.node_type != "question" and any(metadata):
            raise ValueError("question metadata is only valid on question nodes")
        if len(self.allowed_answers) != len(set(self.allowed_answers)):
            raise ValueError("question allowed_answers contains duplicate values")
        related_keys = [
            (reference.entity_type, reference.entity_id) for reference in self.related_entities
        ]
        if len(related_keys) != len(set(related_keys)):
            raise ValueError(f"duplicate related entity on node: {self.node_id}")
        return self


class ViewEdge(ContractModel):
    edge_id: str = Field(min_length=1)
    source_node_id: str = Field(min_length=1)
    target_node_id: str = Field(min_length=1)
    edge_type: str = Field(min_length=1)
    label: str = ""
    explanation: str

    @model_validator(mode="after")
    def validate_hierarchy_explanation(self) -> ViewEdge:
        if self.edge_type == "hierarchy" and not self.explanation.strip():
            raise ValueError("hierarchy edge explanation must be non-empty")
        return self


class ViewSpec(ContractModel):
    version: Literal["1.0.0"] = "1.0.0"
    view_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    dataset_version: str = Field(min_length=1)
    generated_at: datetime
    root_node_ids: list[str] = Field(min_length=1)
    nodes: list[ViewNode] = Field(min_length=1)
    edges: list[ViewEdge] = Field(default_factory=list)
    entities: list[ViewEntity] = Field(default_factory=list)

    @field_validator("title", "description")
    @classmethod
    def validate_non_blank_presentation_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("view title and description must be non-empty")
        return value

    @model_validator(mode="after")
    def validate_references(self) -> ViewSpec:
        node_by_id = _unique_by(self.nodes, "node_id", "node")
        _unique_by(self.edges, "edge_id", "edge")
        entity_by_key = _unique_entities(self.entities)

        if len(self.root_node_ids) != len(set(self.root_node_ids)):
            raise ValueError("root_node_ids contains duplicate node IDs")
        for root_id in self.root_node_ids:
            root = node_by_id.get(root_id)
            if root is None:
                raise ValueError(f"root_node_ids references missing node: {root_id}")
            if root.parent_node_id is not None:
                raise ValueError(f"root node has a parent: {root_id}")
            if root.node_type != "branch":
                raise ValueError(f"root node must be a branch: {root_id}")

        for node in self.nodes:
            if node.parent_node_id is not None and node.parent_node_id not in node_by_id:
                raise ValueError(
                    f"parent reference from {node.node_id} is missing: {node.parent_node_id}"
                )
            for reference in node.related_entities:
                key = (reference.entity_type, reference.entity_id)
                if key not in entity_by_key:
                    raise ValueError(
                        "entity reference from "
                        f"{node.node_id} is missing: {reference.entity_type}/{reference.entity_id}"
                    )

        for edge in self.edges:
            if edge.source_node_id not in node_by_id or edge.target_node_id not in node_by_id:
                raise ValueError(f"edge {edge.edge_id} has a missing node reference")

        question_by_id: dict[str, ViewNode] = {}
        for node in self.nodes:
            if node.question_id is None:
                continue
            if node.question_id in question_by_id:
                raise ValueError(f"duplicate question_id in nodes: {node.question_id}")
            question_by_id[node.question_id] = node

        for node in self.nodes:
            for binding in node.answer_bindings:
                question = question_by_id.get(binding.question_id)
                if question is None or binding.answer_value not in question.allowed_answers:
                    raise ValueError(
                        "answer binding is not canonical: "
                        f"{binding.question_id}/{binding.answer_value}"
                    )

        source_keys = {
            entity.entity_id for entity in self.entities if entity.entity_type == "source"
        }
        for entity in self.entities:
            missing_sources = set(entity.source_ids) - source_keys
            if missing_sources:
                raise ValueError(
                    f"entity {entity.entity_type}/{entity.entity_id} has missing source "
                    "references: " + ", ".join(sorted(missing_sources))
                )
        for node in self.nodes:
            missing_sources = set(node.source_ids) - source_keys
            if missing_sources:
                raise ValueError(
                    f"node {node.node_id} has missing source references: "
                    + ", ".join(sorted(missing_sources))
                )

        _validate_parent_cycles(self.nodes)
        return self


class ManifestView(ContractModel):
    view_id: str = Field(min_length=1)
    version: Literal["1.0.0"]
    path: str = Field(min_length=1)


class SiteManifest(ContractModel):
    version: Literal["1.0.0"] = "1.0.0"
    dataset_version: str = Field(min_length=1)
    generated_at: datetime
    views: list[ManifestView]


def _unique_by[ContractModelT: ContractModel](
    items: Sequence[ContractModelT], attribute: str, label: str
) -> dict[str, ContractModelT]:
    result: dict[str, ContractModelT] = {}
    for item in items:
        item_id = str(getattr(item, attribute))
        if item_id in result:
            raise ValueError(f"duplicate {label} ID: {item_id}")
        result[item_id] = item
    return result


def _unique_entities(entities: list[ViewEntity]) -> dict[tuple[str, str], ViewEntity]:
    result: dict[tuple[str, str], ViewEntity] = {}
    for entity in entities:
        key = (entity.entity_type, entity.entity_id)
        if key in result:
            raise ValueError(f"duplicate entity ID: {entity.entity_type}/{entity.entity_id}")
        result[key] = entity
    return result


def _validate_parent_cycles(nodes: list[ViewNode]) -> None:
    parent_by_id = {node.node_id: node.parent_node_id for node in nodes}
    for node in nodes:
        path: set[str] = set()
        current: str | None = node.node_id
        while current is not None:
            if current in path:
                raise ValueError(f"parent references contain a cycle at: {current}")
            path.add(current)
            current = parent_by_id.get(current)
