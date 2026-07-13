from __future__ import annotations

import json
from pathlib import Path

from optimization_compass.db import KnowledgeRepository
from optimization_compass.site_export import export_site_data
from optimization_compass.view_spec import SiteManifest, ViewSpec

EXPECTED_BRANCHES = [
    "alternative-first",
    "variable domain",
    "objective information",
    "constraint structure",
    "required outcome / guarantee",
]


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

    assert first_view_bytes == second_view_bytes
    assert first_manifest_bytes == second_manifest_bytes
    assert first_manifest == second_manifest
    assert first_view_bytes.endswith(b"\n")
    assert first_manifest_bytes.endswith(b"\n")

    view = ViewSpec.model_validate_json(first_view_bytes)
    roots = {node.node_id: node for node in view.nodes}
    assert [roots[node_id].label for node_id in view.root_node_ids] == EXPECTED_BRANCHES
    assert view.root_node_ids == [
        "branch:alternative-first",
        "branch:variable-domain",
        "branch:objective-information",
        "branch:constraint-structure",
        "branch:required-outcome-guarantee",
    ]
    assert view.generated_at.isoformat() == "2026-07-13T00:00:00+00:00"
    assert view.dataset_version == repository.dataset_version()

    question_nodes = [node for node in view.nodes if node.node_type == "question"]
    assert {node.question_id for node in question_nodes} == {
        f"Q{number:02d}" for number in range(1, 13)
    }
    assert {node.answer_type for node in question_nodes} == {
        "single_choice",
        "multi_choice",
    }
    assert all(node.allowed_answers for node in question_nodes)

    bindings = [
        binding
        for node in view.nodes
        for binding in node.answer_bindings
    ]
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
