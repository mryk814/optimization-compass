from __future__ import annotations

import sqlite3
from pathlib import Path

from optimization_compass.db import KnowledgeRepository
from optimization_compass.engine import RecommendationEngine
from optimization_compass.models import RecommendationRequest

ROOT = Path(__file__).parents[1]
DATABASE = ROOT / "src/optimization_compass/resources/knowledge.sqlite"


def test_structured_failure_modes_are_closed_and_exportable() -> None:
    repository = KnowledgeRepository(DATABASE)
    failures = repository.structured_failure_modes()

    assert len(failures) == 12
    assert all(item["triggers"] for item in failures)
    assert all(item["symptoms"] for item in failures)
    assert all(item["diagnostics"] for item in failures)
    assert all(item["mitigations"] for item in failures)
    assert sum(bool(item["scenario_ids"]) for item in failures) == 4
    assert all(item["source_ids"] and item["last_verified"] for item in failures)
    implementation_failure = next(item for item in failures if item["failure_mode_id"] == "FM025")
    assert implementation_failure["failure_scope"] == "implementation_specific"
    assert {item["entity_type"] for item in implementation_failure["affected_entities"]} == {
        "implementation"
    }
    assert all(
        item["specificity"] == "implementation_only"
        for item in implementation_failure["affected_entities"]
    )


def test_diagnose_uses_failure_relation_for_exclusion() -> None:
    engine = RecommendationEngine(KnowledgeRepository(DATABASE))
    result = engine.recommend(
        RecommendationRequest(
            answers={
                "Q01": ["continuous"],
                "Q02": ["explicit_algebraic"],
                "Q03": ["general_nonlinear"],
                "Q04": ["none"],
                "Q05": ["analytic_gradient"],
                "Q07": ["large_noise"],
                "Q09": ["local_is_fine"],
                "Q10": ["no_certificate_needed"],
            },
            language="ja",
        )
    )

    bfgs = next(item for item in result.excluded_methods if item.entity_id == "M_BFGS")
    assert bfgs.warnings
    assert "S059" in bfgs.source_ids
    assert any("failure mode" in warning for warning in result.warnings)


def test_release_check_24_passes() -> None:
    connection = sqlite3.connect(DATABASE)
    try:
        assert (
            connection.execute(
                "SELECT status FROM release_checks WHERE check_id = 'CHK024'"
            ).fetchone()[0]
            == "pass"
        )
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
    finally:
        connection.close()
