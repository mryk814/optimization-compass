from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from optimization_compass.db import KnowledgeRepository
from optimization_compass.evidence import (
    SOURCE_FRESHNESS_DAYS,
    SourceRecord,
    build_source_evidence_index,
)


def test_source_evidence_index_exports_every_source_and_canonical_link(
    repository: KnowledgeRepository,
) -> None:
    index = build_source_evidence_index(
        repository,
        dataset_version=repository.dataset_version(),
        generated_at=datetime(2026, 7, 13, tzinfo=UTC),
    )

    assert len(index.sources) == 97
    assert sum(len(source.evidence_targets) for source in index.sources) == 4193
    assert {rule.source_type for rule in index.freshness_policy} == set(SOURCE_FRESHNESS_DAYS)
    scipy = next(source for source in index.sources if source.source_id == "S001")
    assert scipy.title == "SciPy Optimization and root finding"
    assert scipy.last_verified.isoformat() == "2026-07-13"
    assert scipy.license == "unknown"
    assert scipy.official_url.startswith("https://")

    method_target = next(
        target
        for source in index.sources
        for target in source.evidence_targets
        if target.target_table == "methods"
    )
    assert method_target.canonical_url == f"/methods/{method_target.target_id}"

    rule_target = next(
        target
        for source in index.sources
        for target in source.evidence_targets
        if target.target_table == "decision_rules"
    )
    assert rule_target.canonical_url == "/diagnose"


def test_source_record_rejects_non_http_official_url() -> None:
    with pytest.raises(ValidationError, match="absolute HTTP"):
        SourceRecord(
            source_id="S-test",
            source_type="official_documentation",
            title="Test",
            publisher="Test",
            last_verified="2026-07-13",
            official_url="javascript:alert(1)",
            access_note="Check publisher terms.",
            supported_claim="Test",
            source_quality="primary",
            currentness_status="verified_current",
            evidence_targets=[],
        )
