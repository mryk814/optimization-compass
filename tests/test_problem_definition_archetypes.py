from __future__ import annotations

import pytest

from optimization_compass.problem_registry import load_problem_suite


@pytest.mark.parametrize(
    ("definition_id", "expected_archetypes"),
    [
        # The outer problem is bilevel; the inner solve is a linear (ridge) least squares.
        ("PROBLEM_BILEVEL_REGRESSION", ["PA046", "PA005"]),
        # The lesson is about crash/timeout/nonphysical evaluations, not experimental design.
        ("PROBLEM_FAILED_SIMULATION", ["PA016"]),
        # Finite-scenario CVaR is a sampled stochastic program over a capped simplex.
        ("PROBLEM_PORTFOLIO_UNCERTAINTY", ["PA049", "PA036"]),
    ],
)
def test_problem_definition_links_its_formulation_archetype_first(
    definition_id: str, expected_archetypes: list[str]
) -> None:
    definitions = {item.problem_definition_id: item for item in load_problem_suite().definitions}

    assert definitions[definition_id].related_problem_ids == expected_archetypes
