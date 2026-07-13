from __future__ import annotations

from copy import deepcopy

import pytest
from pydantic import ValidationError

from optimization_compass.view_spec import (
    AnswerBinding,
    EntityReference,
    ViewEdge,
    ViewEntity,
    ViewNode,
    ViewSpec,
)


def valid_view_spec_payload() -> dict[str, object]:
    return {
        "version": "1.0.0",
        "view_id": "test-view",
        "dataset_version": "0.2.0",
        "generated_at": "2026-07-13T00:00:00Z",
        "root_node_ids": ["branch:test"],
        "nodes": [
            {
                "node_id": "branch:test",
                "node_type": "branch",
                "label": "Test branch",
            },
            {
                "node_id": "question:Q01",
                "node_type": "question",
                "label": "Question",
                "parent_node_id": "branch:test",
                "question_id": "Q01",
                "answer_type": "single_choice",
                "allowed_answers": ["continuous", "integer"],
                "entity_refs": [
                    {"entity_type": "feature", "entity_id": "F_VARIABLE_DOMAIN"}
                ],
            },
            {
                "node_id": "answer:Q01:continuous",
                "node_type": "answer",
                "label": "Continuous",
                "parent_node_id": "question:Q01",
                "answer_bindings": [
                    {"question_id": "Q01", "answer_value": "continuous"}
                ],
            },
        ],
        "edges": [
            {
                "edge_id": "edge:related",
                "source_node_id": "branch:test",
                "target_node_id": "answer:Q01:continuous",
                "edge_type": "related",
            }
        ],
        "entities": [
            {
                "entity_type": "feature",
                "entity_id": "F_VARIABLE_DOMAIN",
                "label": "Variable domain",
            }
        ],
    }


@pytest.mark.parametrize(
    ("collection", "duplicate"),
    [
        ("nodes", "node_id"),
        ("edges", "edge_id"),
        ("entities", "entity"),
    ],
)
def test_viewspec_rejects_duplicate_ids(collection: str, duplicate: str) -> None:
    payload = valid_view_spec_payload()
    items = payload[collection]
    assert isinstance(items, list)
    if duplicate == "entity":
        items.append(deepcopy(items[0]))
    else:
        items.append(deepcopy(items[0]))

    with pytest.raises(ValidationError, match="duplicate"):
        ViewSpec.model_validate(payload)


def test_viewspec_rejects_missing_root() -> None:
    payload = valid_view_spec_payload()
    payload["root_node_ids"] = ["branch:missing"]

    with pytest.raises(ValidationError, match="root_node_ids"):
        ViewSpec.model_validate(payload)


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda payload: payload["nodes"][1].update(parent_node_id="node:missing"), "parent"),
        (
            lambda payload: payload["edges"][0].update(target_node_id="node:missing"),
            "edge",
        ),
        (
            lambda payload: payload["nodes"][1]["entity_refs"][0].update(
                entity_id="F_MISSING"
            ),
            "entity",
        ),
    ],
)
def test_viewspec_rejects_broken_references(mutation: object, message: str) -> None:
    payload = valid_view_spec_payload()
    assert callable(mutation)
    mutation(payload)

    with pytest.raises(ValidationError, match=message):
        ViewSpec.model_validate(payload)


@pytest.mark.parametrize(
    "binding",
    [
        {"question_id": "Q99", "answer_value": "continuous"},
        {"question_id": "Q01", "answer_value": "not-canonical"},
    ],
)
def test_viewspec_rejects_unknown_answer_bindings(binding: dict[str, str]) -> None:
    payload = valid_view_spec_payload()
    payload["nodes"][2]["answer_bindings"] = [binding]

    with pytest.raises(ValidationError, match="answer binding"):
        ViewSpec.model_validate(payload)


def test_entity_type_accepts_unknown_non_empty_strings() -> None:
    reference = EntityReference(entity_type="future_kind", entity_id="X01")
    entity = ViewEntity(entity_type="future_kind", entity_id="X01", label="Future")

    assert reference.entity_type == "future_kind"
    assert entity.entity_type == "future_kind"

    with pytest.raises(ValidationError):
        EntityReference(entity_type="", entity_id="X01")


def test_contract_models_preserve_exact_answer_bindings() -> None:
    binding = AnswerBinding(question_id="Q01", answer_value="structured_or_unknown")
    node = ViewNode(
        node_id="answer:opaque-id",
        node_type="answer",
        label="Structured or unknown",
        answer_bindings=[binding],
    )
    edge = ViewEdge(
        edge_id="edge:opaque",
        source_node_id="question:Q01",
        target_node_id=node.node_id,
        edge_type="hierarchy",
    )

    assert node.answer_bindings == [binding]
    assert edge.target_node_id == "answer:opaque-id"
