from __future__ import annotations

import json
from datetime import UTC, date, datetime, time
from pathlib import Path
from typing import Any, Literal

from optimization_compass.db import KnowledgeRepository
from optimization_compass.view_spec import (
    AnswerBinding,
    EntityReference,
    ManifestView,
    SiteManifest,
    ViewEdge,
    ViewEntity,
    ViewNode,
    ViewSpec,
)

VIEW_VERSION = "1.0.0"
VIEW_ID = "problem-structure"
VIEW_PATH = "views/problem-structure.json"

BRANCHES: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("alternative-first", "alternative-first", ()),
    ("variable-domain", "variable domain", ("Q01", "Q08", "Q12")),
    ("objective-information", "objective information", ("Q02", "Q03", "Q05", "Q06", "Q07")),
    ("constraint-structure", "constraint structure", ("Q04", "Q11")),
    ("required-outcome-guarantee", "required outcome / guarantee", ("Q09", "Q10")),
)


def export_site_data(output_dir: Path, repository: KnowledgeRepository) -> SiteManifest:
    release = repository.latest_release()
    generated_at = datetime.combine(
        date.fromisoformat(release["release_date"]), time.min, tzinfo=UTC
    )
    questions = repository.atlas_questions()
    alternatives = repository.atlas_alternatives()
    feature_ids = sorted({str(question["mapped_feature_id"]) for question in questions})
    features = repository.atlas_features(feature_ids)

    source_ids = sorted(
        {
            str(source_id)
            for row in [*questions, *features, *alternatives]
            for source_id in row["source_ids"]
        }
    )
    sources = repository.atlas_sources(source_ids)
    if {str(source["source_id"]) for source in sources} != set(source_ids):
        raise ValueError("atlas export references source IDs missing from the repository")

    view = _build_problem_structure(
        dataset_version=release["version"],
        generated_at=generated_at,
        questions=questions,
        features=features,
        alternatives=alternatives,
        sources=sources,
    )
    manifest = SiteManifest(
        version="1.0.0",
        dataset_version=release["version"],
        generated_at=generated_at,
        views=[ManifestView(view_id=VIEW_ID, version="1.0.0", path=VIEW_PATH)],
    )

    _write_json(output_dir / VIEW_PATH, view)
    _write_json(output_dir / "manifest.json", manifest)
    return manifest


def _build_problem_structure(
    *,
    dataset_version: str,
    generated_at: datetime,
    questions: list[dict[str, Any]],
    features: list[dict[str, Any]],
    alternatives: list[dict[str, Any]],
    sources: list[dict[str, Any]],
) -> ViewSpec:
    question_by_id = {str(question["question_id"]): question for question in questions}
    expected_question_ids = {question_id for _, _, ids in BRANCHES for question_id in ids}
    if set(question_by_id) != expected_question_ids:
        missing = sorted(expected_question_ids - set(question_by_id))
        unexpected = sorted(set(question_by_id) - expected_question_ids)
        raise ValueError(
            "problem-structure question mapping is incomplete; "
            f"missing={missing}, unexpected={unexpected}"
        )

    nodes = [
        ViewNode(
            node_id=f"branch:{branch_id}",
            node_type="branch",
            label=label,
            label_en=label,
        )
        for branch_id, label, _ in BRANCHES
    ]

    alternative_group_id = "feature:alternative-first"
    nodes.append(
        ViewNode(
            node_id=alternative_group_id,
            node_type="feature",
            label="generic optimization alternatives",
            label_en="generic optimization alternatives",
            parent_node_id="branch:alternative-first",
        )
    )
    for alternative in alternatives:
        alternative_id = str(alternative["alternative_id"])
        nodes.append(
            ViewNode(
                node_id=f"entity:alternative:{alternative_id}",
                node_type="entity_reference",
                label=_display_text(alternative.get("name_ja"), alternative_id),
                label_en=_display_text(alternative.get("name_en"), alternative_id),
                parent_node_id=alternative_group_id,
                entity_refs=[
                    EntityReference(entity_type="alternative", entity_id=alternative_id)
                ],
                source_ids=_string_list(alternative["source_ids"]),
            )
        )

    for branch_id, _, question_ids in BRANCHES:
        for question_id in question_ids:
            question = question_by_id[question_id]
            question_node_id = f"question:{question_id}"
            allowed_answers = _string_list(question["allowed_answers"])
            nodes.append(
                ViewNode(
                    node_id=question_node_id,
                    node_type="question",
                    label=_display_text(question.get("question_ja"), question_id),
                    label_en=_display_text(question.get("question_en"), question_id),
                    parent_node_id=f"branch:{branch_id}",
                    question_id=question_id,
                    answer_type=_answer_type(question["answer_type"]),
                    allowed_answers=allowed_answers,
                    entity_refs=[
                        EntityReference(
                            entity_type="feature",
                            entity_id=str(question["mapped_feature_id"]),
                        )
                    ],
                    source_ids=_string_list(question["source_ids"]),
                )
            )
            for answer_value in allowed_answers:
                nodes.append(
                    ViewNode(
                        node_id=f"answer:{question_id}:{answer_value}",
                        node_type="answer",
                        label=_answer_label(answer_value),
                        label_en=_answer_label(answer_value),
                        parent_node_id=question_node_id,
                        answer_bindings=[
                            AnswerBinding(question_id=question_id, answer_value=answer_value)
                        ],
                        source_ids=_string_list(question["source_ids"]),
                    )
                )

    edges = [
        ViewEdge(
            edge_id=f"hierarchy:{node.parent_node_id}:{node.node_id}",
            source_node_id=node.parent_node_id,
            target_node_id=node.node_id,
            edge_type="hierarchy",
        )
        for node in nodes
        if node.parent_node_id is not None
    ]

    entities = [
        ViewEntity(
            entity_type="feature",
            entity_id=str(feature["feature_id"]),
            label=_display_text(feature.get("name_ja"), str(feature["feature_id"])),
            label_en=_display_text(feature.get("name_en"), str(feature["feature_id"])),
            source_ids=_string_list(feature["source_ids"]),
        )
        for feature in features
    ]
    entities.extend(
        ViewEntity(
            entity_type="alternative",
            entity_id=str(alternative["alternative_id"]),
            label=_display_text(alternative.get("name_ja"), str(alternative["alternative_id"])),
            label_en=_display_text(alternative.get("name_en"), str(alternative["alternative_id"])),
            source_ids=_string_list(alternative["source_ids"]),
        )
        for alternative in alternatives
    )
    entities.extend(
        ViewEntity(
            entity_type="source",
            entity_id=str(source["source_id"]),
            label=_display_text(source.get("title"), str(source["source_id"])),
        )
        for source in sources
    )

    return ViewSpec(
        version="1.0.0",
        view_id=VIEW_ID,
        dataset_version=dataset_version,
        generated_at=generated_at,
        root_node_ids=[f"branch:{branch_id}" for branch_id, _, _ in BRANCHES],
        nodes=nodes,
        edges=edges,
        entities=entities,
    )


def _write_json(path: Path, model: ViewSpec | SiteManifest) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(
        model.model_dump(mode="json"), ensure_ascii=False, indent=2, sort_keys=True
    )
    path.write_text(payload + "\n", encoding="utf-8", newline="\n")


def _display_text(value: object, fallback: str) -> str:
    text = str(value).strip() if value is not None else ""
    return text or fallback


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        raise TypeError("repository export lists must be normalized before serialization")
    return [str(item) for item in value]


def _answer_label(answer_value: str) -> str:
    return answer_value.replace("_", " ").capitalize()


def _answer_type(value: object) -> Literal["single_choice", "multi_choice"]:
    if value == "single_choice" or value == "multi_choice":
        return value
    raise ValueError(f"unsupported question answer_type: {value}")
