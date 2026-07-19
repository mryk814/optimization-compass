from __future__ import annotations

from datetime import date
from urllib.error import HTTPError

from optimization_compass.db import KnowledgeRepository
from optimization_compass.source_health import (
    LinkCheck,
    build_source_health_report,
    check_source_url,
)


def test_health_report_keeps_chk010_unknowns_as_stale_candidates(
    repository: KnowledgeRepository,
) -> None:
    report = build_source_health_report(repository, as_of=date(2026, 7, 15), check_network=False)
    implementation_candidates = [
        candidate
        for candidate in report.stale_candidates
        if candidate.entity_type == "implementation"
    ]
    assert report.structural_errors == []
    assert len(implementation_candidates) == 25
    assert all("last_release" in candidate.stale_fields for candidate in implementation_candidates)


def test_rate_limit_is_advisory_after_retries() -> None:
    calls = 0

    def opener(request: object, *, timeout: float) -> object:
        nonlocal calls
        calls += 1
        raise HTTPError("https://example.com", 429, "rate limited", {}, None)

    result = check_source_url("S001", "https://example.com", opener=opener, sleeper=lambda _: None)
    assert calls == 3
    assert result.status == "rate_limited"
    assert result.attempts == 3


def test_transient_network_result_is_not_reported_as_broken(
    repository: KnowledgeRepository,
) -> None:
    def checker(source_id: str, url: str) -> LinkCheck:
        return LinkCheck(
            source_id=source_id,
            requested_url=url,
            final_url=None,
            http_status=503,
            status="transient",
            attempts=3,
            detail="transient HTTP 503",
        )

    report = build_source_health_report(
        repository, as_of=date(2026, 7, 15), check_network=True, checker=checker
    )
    assert len(report.links) == 110
    assert {item.status for item in report.links} == {"transient"}
