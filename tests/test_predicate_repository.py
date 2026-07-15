from __future__ import annotations

from pathlib import Path

from optimization_compass.dataset_release import TARGET_DATASET_VERSION
from optimization_compass.db import KnowledgeRepository
from optimization_compass.predicates import PredicateFact, evaluate_eligibility


def test_released_catalog_migrates_fifteen_methods(repository: KnowledgeRepository) -> None:
    catalog = repository.predicate_catalog()
    method_coverage = [row for row in catalog.coverage if row.subject_type == "method"]

    assert len({row.subject_id for row in method_coverage}) == 15
    assert {row.status for row in method_coverage} == {"complete", "partial"}
    assert len(catalog.rule_target_retirements) == 7


def test_retired_targets_compile_from_excluding_policies(
    repository: KnowledgeRepository,
) -> None:
    rules = {str(row["rule_id"]): row for row in repository.rules()}
    assert rules["R034"]["action_target_ids"] == "M_NEWTON;M_BFGS;M_INTERIOR_POINT_NLP"
    assert rules["R042"]["action_target_ids"] == "M_BFGS;M_NEWTON;M_SLSQP"
    assert rules["R050"]["action_target_ids"] == ("M_NELDER_MEAD;M_CMA_ES;M_BAYESIAN_OPT_GP")

    catalog = repository.predicate_catalog()
    bfgs = evaluate_eligibility(
        catalog,
        {"F_DERIVATIVE_ACCESS": PredicateFact(status="known", value="not_differentiable")},
        subject_type="method",
        subject_id="M_BFGS",
        parent_by_subject=repository.predicate_parent_map(),
    )
    assert bfgs.status == "excluded"


def test_release_report_lists_remaining_free_text_conditions() -> None:
    report = Path(
        f"data/optimization_method_selection_database_v{TARGET_DATASET_VERSION}_report.md"
    ).read_text(encoding="utf-8")
    assert "## Free-text-only method conditions" in report
    assert "without complete atomic-predicate coverage" in report
    assert "`M_GRADIENT_DESCENT`" in report
    assert "`required_assumptions`" in report
