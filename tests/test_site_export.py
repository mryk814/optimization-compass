from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path

import pytest

from optimization_compass.db import KnowledgeRepository
from optimization_compass.site_export import export_site_data
from optimization_compass.trace_models import (
    AlgorithmTrace,
    TraceIndex,
    canonical_trace_bytes,
)
from optimization_compass.view_spec import SiteManifest, ViewSpec
from optimization_compass.visualization_scenarios import VisualizationScenarioIndex

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
    first_scenario_bytes = (first_output / "visualization-scenarios.json").read_bytes()
    second_scenario_bytes = (second_output / "visualization-scenarios.json").read_bytes()

    assert first_view_bytes == second_view_bytes
    assert first_manifest_bytes == second_manifest_bytes
    assert (first_output / "release.json").read_bytes() == (
        second_output / "release.json"
    ).read_bytes()
    assert first_recommendation_bytes == second_recommendation_bytes
    assert first_scenario_bytes == second_scenario_bytes
    assert first_manifest == second_manifest
    assert first_view_bytes.endswith(b"\n")
    assert first_manifest_bytes.endswith(b"\n")

    view = ViewSpec.model_validate_json(first_view_bytes)
    nodes = {node.node_id: node for node in view.nodes}
    entities = {(entity.entity_type, entity.entity_id): entity for entity in view.entities}
    assert view.title == "問題構造マップ"
    assert view.description == "問題の特徴から手法候補へ辿る意味階層。"
    assert view.preset_id == "VIEW_PROBLEM_STRUCTURE"
    assert view.axis == "problem_structure"
    assert view.relation_types == ["hierarchy"]
    assert view.max_depth == 3
    assert view.limitations
    assert view.focus_fallback_entity_types == ["feature", "method", "problem", "alternative"]
    assert [nodes[node_id].label for node_id in view.root_node_ids] == EXPECTED_BRANCHES
    assert view.root_node_ids == [
        "branch:alternative-first",
        "branch:variable-domain",
        "branch:objective-information",
        "branch:constraint-structure",
        "branch:required-outcome-guarantee",
    ]
    assert view.generated_at.date().isoformat() == repository.latest_release()["release_date"]
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
        },
        {
            "path": "views/available-information.json",
            "view_id": "available-information",
            "version": "1.0.0",
        },
        {
            "path": "views/guarantee-outcome.json",
            "view_id": "guarantee-outcome",
            "version": "1.0.0",
        },
        {
            "path": "views/method-mechanism.json",
            "view_id": "method-mechanism",
            "version": "1.0.0",
        },
    ]
    for item in manifest_payload["views"]:
        semantic_view = ViewSpec.model_validate_json((first_output / item["path"]).read_bytes())
        assert semantic_view.description
        assert semantic_view.limitations
        assert semantic_view.filter_policy.groups
    assert manifest_payload["recommendation"] == {
        "path": "recommendation/site-data.json",
        "version": "2.0.0",
    }
    assert manifest_payload["traces"]["path"] == "traces/index.json"
    assert manifest_payload["traces"]["contract_version"] == "1.0.0"
    assert manifest_payload["traces"]["index_version"] == "1.0.0"
    index_bytes = (first_output / "traces/index.json").read_bytes()
    assert manifest_payload["traces"]["bytes"] == len(index_bytes)
    assert manifest_payload["traces"]["sha256"] == sha256(index_bytes).hexdigest()
    assert manifest_payload["problems"] == {
        "path": "problems.json",
        "version": "1.0.0",
    }
    problem_catalog = json.loads((first_output / "problems.json").read_bytes())
    assert len(problem_catalog["definitions"]) == 9
    assert len(problem_catalog["instances"]) == 10
    search_tree_index_bytes = (first_output / "search-trees/index.json").read_bytes()
    search_tree_index = json.loads(search_tree_index_bytes)
    assert {item["scenario_id"] for item in search_tree_index["artifacts"]} == {
        "SCENARIO_BINARY_KNAPSACK_BNB_COMPLETE",
        "SCENARIO_BINARY_KNAPSACK_BNB_BUDGET",
    }
    for entry in search_tree_index["artifacts"]:
        assert (first_output / entry["path"]).is_file()
        assert (first_output / entry["static_fallback_path"]).is_file()
    assert manifest_payload["visualization_scenarios"] == {
        "path": "visualization-scenarios.json",
        "version": "1.2.0",
    }
    assert manifest_payload["derived_media"] == {
        "path": "media/manifest.json",
        "version": "1.1.0",
    }
    first_media_bytes = (first_output / "media/manifest.json").read_bytes()
    assert first_media_bytes == (second_output / "media/manifest.json").read_bytes()
    media_manifest = json.loads(first_media_bytes)
    for entry in media_manifest["entries"]:
        for file in entry["files"]:
            content = (first_output / file["path"]).read_bytes()
            assert content == (second_output / file["path"]).read_bytes()
            assert file["bytes"] == len(content)
            assert file["sha256"] == sha256(content).hexdigest()
        for key in ("captions", "transcript"):
            text_asset = entry[key]
            content = (first_output / text_asset["path"]).read_bytes()
            assert content == (second_output / text_asset["path"]).read_bytes()
            assert text_asset["bytes"] == len(content)
            assert text_asset["sha256"] == sha256(content).hexdigest()
    assert manifest_payload["entity_links"] == {
        "path": "entity-links.json",
        "version": "1.0.0",
    }
    assert manifest_payload["learning_journeys"] == {
        "path": "learning-journeys.json",
        "version": "1.1.0",
    }
    assert (first_output / "learning-journeys.json").read_bytes() == (
        second_output / "learning-journeys.json"
    ).read_bytes()
    assert manifest_payload["formulation_primer"] == {
        "path": "formulation-primer.json",
        "version": "1.0.0",
    }
    formulation_primer = json.loads(
        (first_output / "formulation-primer.json").read_text(encoding="utf-8")
    )
    assert len(formulation_primer["diagnosis_mappings"]) == 12
    assert (first_output / "formulation-primer.json").read_bytes() == (
        second_output / "formulation-primer.json"
    ).read_bytes()
    assert manifest_payload["sources"] == {
        "path": "sources.json",
        "version": "1.0.0",
    }
    assert manifest_payload["implementation_claims"] == {
        "path": "implementation-claims.json",
        "version": "1.0.0",
    }
    assert manifest_payload["benchmark_contexts"] == {
        "path": "benchmark-contexts.json",
        "version": "1.0.0",
    }
    assert manifest_payload["failure_modes"] == {
        "path": "failure-modes.json",
        "version": "1.0.0",
    }
    assert manifest_payload["search_index"] == {"path": "search-index.json", "version": "1.0.0"}
    assert manifest_payload["retrieval_documents"] == {
        "path": "retrieval-documents.json",
        "version": "1.0.0",
    }
    assert manifest_payload["search_benchmark"] == {
        "path": "search-benchmark.json",
        "version": "1.0.0",
    }
    assert (first_output / "search-index.json").read_bytes() == (
        second_output / "search-index.json"
    ).read_bytes()
    assert (first_output / "retrieval-documents.json").read_bytes() == (
        second_output / "retrieval-documents.json"
    ).read_bytes()
    claim_payload = json.loads((first_output / "implementation-claims.json").read_bytes())
    assert len(claim_payload["claims"]) == 64 * 7 + 1
    assert claim_payload["freshness"]["claim_count"] == 64 * 7
    context_payload = json.loads((first_output / "benchmark-contexts.json").read_bytes())
    assert {item["category"] for item in context_payload["contexts"]} == {
        "LP",
        "QP",
        "NLP",
        "MIP",
        "DFO",
        "BO",
    }
    assert all(
        item["ranking_eligibility"]["ranking_eligible"] for item in context_payload["contexts"]
    )
    failure_payload = json.loads((first_output / "failure-modes.json").read_bytes())
    assert len(failure_payload["failure_modes"]) == 12
    assert sum(bool(item["scenario_ids"]) for item in failure_payload["failure_modes"]) == 4
    assert all(item["diagnostics"] for item in failure_payload["failure_modes"])
    source_payload = json.loads((first_output / "sources.json").read_bytes())
    assert len(source_payload["sources"]) == 96
    assert sum(len(source["evidence_targets"]) for source in source_payload["sources"]) == 4202
    link_payload = json.loads((first_output / "entity-links.json").read_bytes())
    search_trace = next(
        entity
        for entity in link_payload["entities"]
        if entity["entity_type"] == "trace"
        and entity["entity_id"] == "binary-knapsack-bnb-complete"
    )
    assert search_trace["canonical_url"] == ("/theater/search-tree/binary-knapsack-bnb-complete")
    assert {relation["relation_type"] for relation in search_trace["relations"]} >= {
        "evidence",
        "related_map",
        "visualizes",
    }
    learning_slices = {
        entity["entity_id"]: entity
        for entity in link_payload["entities"]
        if entity["entity_type"] == "trace"
        and entity["entity_id"]
        in {"constrained-disk-feasible-region", "biobjective-quadratic-pareto-front"}
    }
    assert {
        artifact_id: artifact["canonical_url"] for artifact_id, artifact in learning_slices.items()
    } == {
        "constrained-disk-feasible-region": ("/theater/learning/SCENARIO_CONSTRAINED_DISK"),
        "biobjective-quadratic-pareto-front": ("/theater/learning/SCENARIO_BIOBJECTIVE_QUADRATIC"),
    }
    assert all(
        {relation["relation_type"] for relation in artifact["relations"]}
        >= {"evidence", "related_map", "visualizes"}
        for artifact in learning_slices.values()
    )
    source_by_id = {source["source_id"]: source for source in source_payload["sources"]}
    assert any(
        target["target_id"] == "constrained-disk-feasible-region"
        and target["canonical_url"] == "/theater/learning/SCENARIO_CONSTRAINED_DISK"
        for target in source_by_id["S017"]["evidence_targets"]
    )
    assert any(
        target["target_id"] == "biobjective-quadratic-pareto-front"
        and target["canonical_url"] == "/theater/learning/SCENARIO_BIOBJECTIVE_QUADRATIC"
        for target in source_by_id["S039"]["evidence_targets"]
    )
    nelder_mead = next(
        entity
        for entity in link_payload["entities"]
        if entity["entity_type"] == "method" and entity["entity_id"] == "M_NELDER_MEAD"
    )
    assert nelder_mead["canonical_url"] == "/methods/M_NELDER_MEAD"
    assert nelder_mead["aliases"] == ["/learn/method.nelder-mead"]
    relation_targets = {
        (relation["relation_type"], relation["target_type"], relation["target_id"])
        for relation in nelder_mead["relations"]
    }
    assert ("learning", "content", "method.nelder-mead") in relation_targets
    assert ("visualization", "trace", "nelder-mead-quadratic") in relation_targets
    assert ("comparison", "comparison", "COMPARE_GRADIENT_FAMILY") in relation_targets
    assert ("evidence", "source", "S001") in relation_targets
    source_entity = next(
        entity
        for entity in link_payload["entities"]
        if entity["entity_type"] == "source" and entity["entity_id"] == "S001"
    )
    assert source_entity["canonical_url"] == "/sources/S001"
    assert manifest_payload["licenses"] == {
        "code": {"path": "licenses/LICENSE.txt", "spdx_id": "MIT"},
        "content": {"path": "licenses/CONTENT_LICENSE.txt", "spdx_id": "CC-BY-4.0"},
        "data": {"path": "licenses/DATA_LICENSE.txt", "spdx_id": "CC-BY-4.0"},
        "legal_code_path": "licenses/CC-BY-4.0.txt",
        "notice_path": "licenses/NOTICE.txt",
        "attribution": (
            "Optimization Compass, Copyright 2026 TAKUYA OTANI and Optimization Compass "
            "contributors"
        ),
    }


def test_exporter_writes_canonical_three_frame_dummy_trace_and_index(
    tmp_path: Path, repository: KnowledgeRepository
) -> None:
    first_output = tmp_path / "first"
    second_output = tmp_path / "second"
    export_site_data(first_output, repository)
    export_site_data(second_output, repository)

    trace_path = Path("traces/dummy-educational.json")
    index_path = Path("traces/index.json")
    trace_bytes = (first_output / trace_path).read_bytes()
    index_bytes = (first_output / index_path).read_bytes()
    assert trace_bytes == (second_output / trace_path).read_bytes()
    assert index_bytes == (second_output / index_path).read_bytes()

    trace = AlgorithmTrace.model_validate_json(trace_bytes)
    index = TraceIndex.model_validate_json(index_bytes)
    scenario_index = VisualizationScenarioIndex.model_validate_json(
        (first_output / "visualization-scenarios.json").read_bytes()
    )
    assert trace_bytes == canonical_trace_bytes(trace)
    assert trace.dataset_version == repository.dataset_version()
    assert trace.implementation_mapping_status == "not_applicable"
    assert trace.implementation_id is None
    assert [frame.frame_index for frame in trace.frames] == [0, 1, 2]
    assert [frame.oracle_evaluations for frame in trace.frames] == [3, 4, 4]
    assert [frame.event_type for frame in trace.frames] == ["initialize", "reflect", "stop"]
    assert index.dataset_version == trace.dataset_version
    assert index.traces[0].trace_id == trace.trace_id
    assert index.traces[0].path == "dummy-educational.json"
    trace_scenarios = [
        scenario
        for scenario in scenario_index.scenarios
        if scenario.artifact.artifact_contract == "AlgorithmTrace"
    ]
    scenario_by_artifact = {
        run.artifact_id: scenario for scenario in trace_scenarios for run in scenario.runs
    }
    search_scenario = scenario_by_artifact["binary-knapsack-bnb-complete"]
    assert search_scenario.purpose == "mechanism"
    assert search_scenario.artifact.renderer_family == "search_tree"
    assert search_scenario.problem_instance_id == "INSTANCE_BINARY_KNAPSACK_4"
    assert len(trace_scenarios) == len(index.traces) - 1
    assert set(scenario_by_artifact) == {
        entry.trace_id for entry in index.traces if entry.trace_id != "dummy-educational"
    }
    assert (
        scenario_by_artifact["nelder-mead-quadratic"].artifact.renderer_family == "simplex_geometry"
    )
    assert (
        scenario_by_artifact["gradient_descent-quadratic"].artifact.renderer_family
        == "continuous_trajectory"
    )
    surrogate_scenarios = [
        scenario
        for scenario in scenario_index.scenarios
        if scenario.artifact.renderer_family == "surrogate_uncertainty"
    ]
    assert len(surrogate_scenarios) == 4
    assert {scenario.purpose for scenario in surrogate_scenarios} == {"mechanism", "sensitivity"}
    for scenario in surrogate_scenarios:
        payload = (first_output / scenario.artifact.payload_path).read_bytes()
        assert len(payload) == scenario.artifact.payload_bytes
        assert sha256(payload).hexdigest() == scenario.artifact.payload_sha256
        decoded = json.loads(payload)
        assert "title_ja" not in decoded
        assert "method_id" not in decoded
        assert "evaluation_budget" not in decoded
        assert "source_ids" not in decoded
        assert "limitations_ja" not in decoded
    shrink_trace = AlgorithmTrace.model_validate_json(
        (first_output / "traces/nelder-mead-rosenbrock-shifted.json").read_bytes()
    )
    assert any(
        frame.event_type == "shrink"
        and frame.decision == "rejected"
        and any(point.role == "trial-point" for point in frame.points)
        for frame in shrink_trace.frames
    )

    staged = json.loads(Path("data/seeds/atlas_metadata.json").read_text(encoding="utf-8"))
    profile = next(
        row
        for row in staged["method_visualization_profiles"]
        if row["profile_id"] == trace.profile_id
    )
    problem_suite = json.loads(
        Path("src/optimization_compass/resources/problem-suite.json").read_text(encoding="utf-8")
    )
    objective = next(
        row
        for row in problem_suite["instances"]
        if row["problem_instance_id"] == trace.objective_id
    )
    scenario = next(
        row for row in staged["demo_scenarios"] if row["scenario_id"] == trace.scenario_id
    )
    preset = next(
        row for row in staged["view_presets"] if row["preset_id"] == trace.preset["preset_id"]
    )
    assert profile["method_id"] == trace.method_id
    assert profile["generator_id"] == trace.generator_id
    assert profile["implementation_status"] == trace.implementation_mapping_status
    assert profile["implementation_id"] == trace.implementation_id
    assert objective["registry_key"] == trace.objective["generator_id"]
    assert scenario["method_id"] == trace.method_id
    assert scenario["profile_id"] == trace.profile_id
    assert scenario["problem_instance_id"] == trace.objective_id
    assert scenario["budget"] == trace.evaluation_budget
    assert scenario["parameters"] == trace.parameters
    assert scenario["stopping"] == trace.stopping
    assert scenario["initial_point"] == trace.initial_state["point"]
    assert {frame.event_type for frame in trace.frames} <= set(profile["event_types"])
    assert preset["root_entity_id"] == trace.method_id
    assert set(trace.source_ids) == set(profile["source_ids"]) | set(objective["source_ids"])
