from __future__ import annotations

import json
from pathlib import Path

import pytest

from optimization_compass.db import KnowledgeRepository
from optimization_compass.site_export import export_site_data
from optimization_compass.view_spec import SiteManifest, ViewSpec

EXPECTED_BRANCHES = [
    "代替解法を先に確認",
    "変数と計算資源",
    "目的関数と評価情報",
    "制約と特殊構造",
    "求める解と保証",
]

EXPECTED_ANSWER_LABELS = {
    "answer:Q01:continuous": "連続",
    "answer:Q01:binary": "0-1",
    "answer:Q01:structured_or_unknown": "構造化・複雑な型（structured or unknown）",
    "answer:Q02:explicit_algebraic": "数式で表せる（explicit algebraic）",
    "answer:Q10:global_proof_required": "大域最適性の証明が必要（global proof required）",
}


class BlankQuestionLabelRepository(KnowledgeRepository):
    def atlas_questions(self) -> list[dict[str, object]]:
        questions = super().atlas_questions()
        questions[0] = {**questions[0], "question_ja": " \t"}
        return questions


def test_exporter_rejects_blank_canonical_question_label(
    tmp_path: Path, database_path: Path
) -> None:
    repository = BlankQuestionLabelRepository(database_path)

    with pytest.raises(ValueError, match=r"question Q01 question_ja"):
        export_site_data(tmp_path, repository)


def test_exporter_writes_five_branch_golden_and_is_byte_identical(
    tmp_path: Path, repository: KnowledgeRepository
) -> None:
    first_output = tmp_path / "first"
    second_output = tmp_path / "second"

    first_manifest = export_site_data(first_output, repository)
    second_manifest = export_site_data(second_output, repository)

    first_view_bytes = (first_output / "views/problem-structure.json").read_bytes()
    second_view_bytes = (second_output / "views/problem-structure.json").read_bytes()
    first_manifest_bytes = (first_output / "manifest.json").read_bytes()
    second_manifest_bytes = (second_output / "manifest.json").read_bytes()
    first_recommendation_bytes = (first_output / "recommendation/site-data.json").read_bytes()
    second_recommendation_bytes = (second_output / "recommendation/site-data.json").read_bytes()

    assert first_view_bytes == second_view_bytes
    assert first_manifest_bytes == second_manifest_bytes
    assert first_recommendation_bytes == second_recommendation_bytes
    assert first_manifest == second_manifest
    assert first_view_bytes.endswith(b"\n")
    assert first_manifest_bytes.endswith(b"\n")

    view = ViewSpec.model_validate_json(first_view_bytes)
    nodes = {node.node_id: node for node in view.nodes}
    entities = {(entity.entity_type, entity.entity_id): entity for entity in view.entities}
    assert view.title == "最適化問題の構造マップ"
    assert view.description == (
        "問題の特徴から、関連する問題型・手法・代替解法・根拠をたどるためのビュー。"
    )
    assert [nodes[node_id].label for node_id in view.root_node_ids] == EXPECTED_BRANCHES
    assert view.root_node_ids == [
        "branch:alternative-first",
        "branch:variable-domain",
        "branch:objective-information",
        "branch:constraint-structure",
        "branch:required-outcome-guarantee",
    ]
    assert view.generated_at.isoformat() == "2026-07-13T00:00:00+00:00"
    assert view.dataset_version == repository.dataset_version()

    roots = [nodes[node_id] for node_id in view.root_node_ids]
    assert [node.display_order for node in roots] == list(range(5))
    assert all(node.summary for node in roots)
    assert all(node.default_collapsed for node in roots)
    assert {node.emphasis for node in roots} == {"primary"}

    question_nodes = [node for node in view.nodes if node.node_type == "question"]
    assert {node.question_id for node in question_nodes} == {
        f"Q{number:02d}" for number in range(1, 13)
    }
    assert {node.answer_type for node in question_nodes} == {
        "single_choice",
        "multi_choice",
    }
    assert all(node.allowed_answers for node in question_nodes)
    assert all(node.summary for node in question_nodes)
    assert all(node.default_collapsed for node in question_nodes)
    assert {node.emphasis for node in question_nodes} == {"normal"}
    assert nodes["question:Q01"].summary == (
        "変数型は利用できるsolver familyを最初に大きく分ける。"
    )
    assert [
        nodes[node_id].display_order for node_id in ["question:Q01", "question:Q08", "question:Q12"]
    ] == [0, 1, 2]

    for node_id, label in EXPECTED_ANSWER_LABELS.items():
        assert nodes[node_id].label == label
    assert nodes["answer:Q02:explicit_algebraic"].label_en == "explicit algebraic"
    assert nodes["answer:Q10:global_proof_required"].label_en == "global proof required"

    q01_binary = nodes["answer:Q01:binary"]
    q01_continuous = nodes["answer:Q01:continuous"]
    q02_explicit = nodes["answer:Q02:explicit_algebraic"]
    assert q01_binary.default_collapsed is False
    assert q01_binary.emphasis == "normal"
    assert q01_binary.display_order == 2
    assert q01_binary.summary == "Boolean/0-1構造をnativeに扱う。"
    assert {("method", "M_BRANCH_CUT"), ("method", "M_CP_SAT")} <= {
        (reference.entity_type, reference.entity_id) for reference in q01_binary.related_entities
    }
    assert ("problem", "PA006") in {
        (reference.entity_type, reference.entity_id)
        for reference in q01_continuous.related_entities
    }
    assert ("alternative", "ALT_SPECIALIZED") in {
        (reference.entity_type, reference.entity_id) for reference in q02_explicit.related_entities
    }
    assert q01_binary.source_ids == ["S054", "S055", "S056"]

    alternative = nodes["entity:alternative:ALT_SPECIALIZED"]
    assert alternative.summary == "保証・数値性・速度"
    assert alternative.default_collapsed is False
    assert alternative.emphasis == "muted"
    assert [
        (reference.entity_type, reference.entity_id) for reference in alternative.related_entities
    ] == [("alternative", "ALT_SPECIALIZED")]

    assert all(edge.explanation for edge in view.edges if edge.edge_type == "hierarchy")
    assert "entity_refs" not in view.model_dump(mode="json")["nodes"][0]
    assert entities[("method", "M_BRANCH_CUT")].summary
    assert entities[("problem", "PA006")].summary
    assert entities[("feature", "F_VARIABLE_DOMAIN")].summary
    assert entities[("alternative", "ALT_SPECIALIZED")].summary
    assert entities[("source", "S054")].url.startswith("https://")

    bindings = [binding for node in view.nodes for binding in node.answer_bindings]
    assert ("Q01", "continuous") in {
        (binding.question_id, binding.answer_value) for binding in bindings
    }

    manifest_payload = json.loads(first_manifest_bytes)
    SiteManifest.model_validate(manifest_payload)
    assert manifest_payload["views"] == [
        {
            "path": "views/problem-structure.json",
            "view_id": "problem-structure",
            "version": "1.0.0",
        }
    ]
    assert manifest_payload["recommendation"] == {
        "path": "recommendation/site-data.json",
        "version": "1.0.0",
    }
