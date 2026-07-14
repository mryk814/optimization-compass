from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from optimization_compass.search_tree import (
    SearchTreeArtifact,
    SearchTreeFramePayload,
    generate_search_tree_artifact,
    render_search_tree_svg,
)


def test_search_tree_is_deterministic_and_replays_required_events() -> None:
    first = generate_search_tree_artifact(dataset_version="0.3.0")
    second = generate_search_tree_artifact(dataset_version="0.3.0")

    assert first == second
    assert first.trace.model_dump_json() == second.trace.model_dump_json()
    events = {frame.event_type for frame in first.trace.frames}
    assert {
        "branch",
        "relax",
        "propagate",
        "incumbent_update",
        "bound_update",
        "infeasible_prune",
        "bound_prune",
        "optimality_proven",
    } <= events
    final = SearchTreeFramePayload.model_validate(first.trace.frames[-1].payload)
    assert first.trace.terminal_status == "completed"
    assert final.terminal_state == "optimality_proven"
    assert final.best_feasible_value == 15
    assert final.global_bound == 15
    assert final.absolute_gap == 0
    prune_reasons = {node.prune_reason for node in final.nodes if node.prune_reason}
    assert prune_reasons == {"capacity_exceeded", "bound_not_better"}
    assert all(
        node.prune_explanation_ja
        for node in final.nodes
        if node.state in {"infeasible_pruned", "bound_pruned"}
    )


def test_budget_exhaustion_keeps_candidate_without_claiming_proof() -> None:
    artifact = generate_search_tree_artifact(dataset_version="0.3.0", node_budget=4)
    final = SearchTreeFramePayload.model_validate(artifact.trace.frames[-1].payload)

    assert artifact.scenario_id == "SCENARIO_BINARY_KNAPSACK_BNB_BUDGET"
    assert artifact.trace.terminal_status == "budget_exhausted"
    assert final.terminal_state == "budget_exhausted"
    assert final.best_feasible_value == 13
    assert final.global_bound == 15
    assert final.absolute_gap == 2
    assert "未証明" in artifact.trace.terminal_summary_ja


def test_search_tree_contract_rejects_unknown_fields_and_inconsistent_gap() -> None:
    artifact = generate_search_tree_artifact(dataset_version="0.3.0")
    payload = artifact.model_dump(mode="json")
    payload["legacy_renderer"] = True
    with pytest.raises(ValidationError, match="Extra inputs"):
        SearchTreeArtifact.model_validate(payload)

    final = artifact.trace.frames[-1].payload
    assert isinstance(final, dict)
    inconsistent = json.loads(json.dumps(final))
    inconsistent["absolute_gap"] = 1.0
    with pytest.raises(ValidationError, match="absolute_gap"):
        SearchTreeFramePayload.model_validate(inconsistent)


def test_static_fallback_describes_terminal_search_tree() -> None:
    artifact = generate_search_tree_artifact(dataset_version="0.3.0")
    svg = render_search_tree_svg(artifact)
    assert svg.startswith('<svg xmlns="http://www.w3.org/2000/svg"')
    assert "最適性証明" in svg
    assert "infeasible_pruned" in svg
    assert "bound_pruned" in svg
