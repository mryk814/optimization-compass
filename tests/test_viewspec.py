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
        "preset_id": "VIEW_TEST",
        "title": "Test view",
        "description": "A complete test view.",
        "limitations": "This fixture does not rank methods.",
        "axis": "test_axis",
        "relation_types": ["related"],
        "max_depth": 2,
        "filter_policy": {
            "mode": "authored_groups",
            "groups": [
                {
                    "group_id": "test",
                    "label": "Test",
                    "label_en": "Test",
                    "question_ids": ["Q01"],
                    "feature_ids": [],
                    "method_ids": [],
                    "alternative_ids": [],
                }
            ],
        },
        "focus_fallback_entity_types": ["feature"],
        "dataset_version": "0.2.0",
        "generated_at": "2026-07-13T00:00:00Z",
        "root_node_ids": ["branch:test"],
        "nodes": [
            {
                "node_id": "branch:test",
                "node_type": "branch",
                "label": "Test branch",
                "summary": "Groups the test nodes.",
                "display_order": 0,
                "default_collapsed": True,
                "emphasis": "primary",
                "related_entities": [],
            },
            {
                "node_id": "question:Q01",
                "node_type": "question",
                "label": "Question",
                "summary": "Explains why the question matters.",
                "display_order": 0,
                "default_collapsed": True,
                "emphasis": "normal",
                "parent_node_id": "branch:test",
                "question_id": "Q01",
                "answer_type": "single_choice",
                "allowed_answers": ["continuous", "integer"],
                "related_entities": [{"entity_type": "feature", "entity_id": "F_VARIABLE_DOMAIN"}],
            },
            {
                "node_id": "answer:Q01:continuous",
                "node_type": "answer",
                "label": "Continuous",
                "summary": "Selects continuous optimization candidates.",
                "display_order": 0,
                "default_collapsed": False,
                "emphasis": "normal",
                "parent_node_id": "question:Q01",
                "answer_bindings": [{"question_id": "Q01", "answer_value": "continuous"}],
                "related_entities": [],
            },
        ],
        "edges": [
            {
                "edge_id": "edge:related",
                "source_node_id": "branch:test",
                "target_node_id": "answer:Q01:continuous",
                "edge_type": "related",
                "explanation": "Connects the branch to a related answer.",
            }
        ],
        "entities": [
            {
                "entity_type": "feature",
                "entity_id": "F_VARIABLE_DOMAIN",
                "label": "Variable domain",
                "summary": "Variable-domain feature definition.",
                "url": "",
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
            lambda payload: payload["nodes"][1]["related_entities"][0].update(
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
    entity = ViewEntity(
        entity_type="future_kind",
        entity_id="X01",
        label="Future",
        summary="Future entity.",
        url="",
    )
    node = ViewNode(
        node_id="future:X01",
        node_type="future_kind",
        label="Future",
        summary="Future node.",
        display_order=0,
        default_collapsed=False,
        emphasis="normal",
        related_entities=[],
    )

    assert reference.entity_type == "future_kind"
    assert entity.entity_type == "future_kind"
    assert node.node_type == "future_kind"
    assert EntityReference(entity_type=" future_kind ", entity_id="X02").entity_type == (
        " future_kind "
    )

    with pytest.raises(ValidationError):
        EntityReference(entity_type="", entity_id="X01")


@pytest.mark.parametrize("entity_type", [" ", "\t", "\r\n"])
def test_entity_reference_rejects_whitespace_only_entity_type(entity_type: str) -> None:
    with pytest.raises(ValidationError, match="entity_type"):
        EntityReference(entity_type=entity_type, entity_id="X01")


@pytest.mark.parametrize("entity_type", [" ", "\t", "\r\n"])
def test_view_entity_rejects_whitespace_only_entity_type(entity_type: str) -> None:
    with pytest.raises(ValidationError, match="entity_type"):
        ViewEntity(
            entity_type=entity_type,
            entity_id="X01",
            label="Future",
            summary="Future entity.",
            url="",
        )


@pytest.mark.parametrize("node_type", [" ", "\t", "\r\n"])
def test_view_node_rejects_whitespace_only_node_type(node_type: str) -> None:
    with pytest.raises(ValidationError, match="node_type"):
        ViewNode(
            node_id="future:X01",
            node_type=node_type,
            label="Future",
            summary="Future node.",
            display_order=0,
            default_collapsed=False,
            emphasis="normal",
            related_entities=[],
        )


def test_contract_models_preserve_exact_answer_bindings() -> None:
    binding = AnswerBinding(question_id="Q01", answer_value="structured_or_unknown")
    node = ViewNode(
        node_id="answer:opaque-id",
        node_type="answer",
        label="Structured or unknown",
        summary="No canonical structure is known.",
        display_order=0,
        default_collapsed=False,
        emphasis="normal",
        answer_bindings=[binding],
        related_entities=[],
    )
    edge = ViewEdge(
        edge_id="edge:opaque",
        source_node_id="question:Q01",
        target_node_id=node.node_id,
        edge_type="hierarchy",
        explanation="Expands to the bound answer.",
    )

    assert node.answer_bindings == [binding]
    assert edge.target_node_id == "answer:opaque-id"


def test_viewspec_accepts_complete_presentation_contract() -> None:
    view = ViewSpec.model_validate(valid_view_spec_payload())

    assert view.title == "Test view"
    assert view.description == "A complete test view."
    assert view.limitations == "This fixture does not rank methods."
    assert view.nodes[0].summary == "Groups the test nodes."
    assert view.nodes[0].display_order == 0
    assert view.nodes[0].default_collapsed is True
    assert view.nodes[0].emphasis == "primary"
    assert view.edges[0].explanation == "Connects the branch to a related answer."
    assert view.entities[0].summary == "Variable-domain feature definition."
    assert view.entities[0].url == ""


@pytest.mark.parametrize(
    ("path", "field"),
    [
        (("title",), "title"),
        (("description",), "description"),
        (("nodes", 0, "summary"), "summary"),
        (("nodes", 0, "display_order"), "display_order"),
        (("nodes", 0, "default_collapsed"), "default_collapsed"),
        (("nodes", 0, "emphasis"), "emphasis"),
        (("edges", 0, "explanation"), "explanation"),
        (("entities", 0, "summary"), "summary"),
        (("entities", 0, "url"), "url"),
    ],
)
def test_viewspec_requires_complete_presentation_fields(
    path: tuple[str | int, ...], field: str
) -> None:
    payload = valid_view_spec_payload()
    target: object = payload
    for key in path[:-1]:
        if isinstance(key, str):
            assert isinstance(target, dict)
            target = target[key]
        else:
            assert isinstance(target, list)
            target = target[key]
    assert isinstance(target, dict)
    target.pop(path[-1])

    with pytest.raises(ValidationError, match=field):
        ViewSpec.model_validate(payload)


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda payload: payload["nodes"][0].update(display_order=-1), "display_order"),
        (lambda payload: payload["nodes"][0].update(emphasis="loud"), "emphasis"),
        (lambda payload: payload.update(title=""), "title"),
        (lambda payload: payload.update(title="   "), "title"),
        (lambda payload: payload.update(description=""), "description"),
        (lambda payload: payload.update(description="\t"), "description"),
        (
            lambda payload: payload["edges"][0].update(edge_type="hierarchy", explanation=""),
            "explanation",
        ),
    ],
)
def test_viewspec_rejects_invalid_presentation_values(mutation: object, message: str) -> None:
    payload = valid_view_spec_payload()
    assert callable(mutation)
    mutation(payload)

    with pytest.raises(ValidationError, match=message):
        ViewSpec.model_validate(payload)


def test_viewspec_rejects_duplicate_related_entities_per_node() -> None:
    payload = valid_view_spec_payload()
    references = payload["nodes"][1]["related_entities"]
    references.append(deepcopy(references[0]))

    with pytest.raises(ValidationError, match="duplicate related entity"):
        ViewSpec.model_validate(payload)


def test_viewspec_rejects_undeclared_relation_type() -> None:
    payload = valid_view_spec_payload()
    payload["relation_types"] = ["hierarchy"]

    with pytest.raises(ValidationError, match="undeclared relation type"):
        ViewSpec.model_validate(payload)


def test_viewspec_rejects_nodes_beyond_preset_depth() -> None:
    payload = valid_view_spec_payload()
    payload["max_depth"] = 1

    with pytest.raises(ValidationError, match="exceeds max_depth"):
        ViewSpec.model_validate(payload)
