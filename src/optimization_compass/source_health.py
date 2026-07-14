from __future__ import annotations

import ssl
import time
from collections.abc import Callable
from datetime import date
from http.client import HTTPResponse
from typing import Any, Literal
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from pydantic import BaseModel, ConfigDict, Field

from optimization_compass.db import KnowledgeRepository
from optimization_compass.evidence import SOURCE_FRESHNESS_DAYS

LinkStatus = Literal[
    "healthy",
    "redirect",
    "broken",
    "rate_limited",
    "access_restricted",
    "transient",
    "tls_error",
]
TRANSIENT_STATUS_CODES = {408, 425, 500, 502, 503, 504}
BROKEN_STATUS_CODES = {404, 410}


class HealthModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class LinkCheck(HealthModel):
    source_id: str
    requested_url: str
    final_url: str | None
    http_status: int | None
    status: LinkStatus
    attempts: int = Field(ge=1)
    detail: str


class StaleCandidate(HealthModel):
    entity_type: Literal["source", "implementation"]
    entity_id: str
    stale_fields: list[str]
    last_verified: date
    age_days: int = Field(ge=0)
    max_age_days: int = Field(gt=0)


class SourceHealthReport(HealthModel):
    schema_version: Literal[1] = 1
    generated_on: date
    network_checked: bool
    freshness_policy_days: dict[str, int]
    structural_errors: list[str]
    links: list[LinkCheck]
    stale_candidates: list[StaleCandidate]


ResponseOpener = Callable[..., HTTPResponse]


def check_source_url(
    source_id: str,
    url: str,
    *,
    attempts: int = 3,
    timeout_seconds: float = 15,
    opener: ResponseOpener = urlopen,
    sleeper: Callable[[float], None] = time.sleep,
) -> LinkCheck:
    """Check one URL without treating redirects, throttling, or transient failures as broken."""
    last_status: int | None = None
    last_detail = ""
    for attempt in range(1, attempts + 1):
        request = Request(
            url, method="HEAD", headers={"User-Agent": "optimization-compass-health/1"}
        )
        try:
            with opener(request, timeout=timeout_seconds) as response:
                http_status = int(response.status)
                final_url = response.geturl()
                if http_status == 429:
                    link_status: LinkStatus = "rate_limited"
                    detail = "remote service rate-limited the check"
                elif http_status == 403:
                    link_status = "access_restricted"
                    detail = "automated access is restricted"
                elif http_status in TRANSIENT_STATUS_CODES:
                    link_status = "transient"
                    detail = f"transient HTTP {http_status}"
                elif http_status in BROKEN_STATUS_CODES or http_status >= 400:
                    link_status = "broken"
                    detail = f"HTTP {http_status}"
                elif final_url != url:
                    return LinkCheck(
                        source_id=source_id,
                        requested_url=url,
                        final_url=final_url,
                        http_status=http_status,
                        status="redirect",
                        attempts=attempt,
                        detail="redirected; review the canonical official URL",
                    )
                else:
                    return LinkCheck(
                        source_id=source_id,
                        requested_url=url,
                        final_url=final_url,
                        http_status=http_status,
                        status="healthy",
                        attempts=attempt,
                        detail="HTTP request succeeded",
                    )
                last_status, last_detail = http_status, detail
                if link_status not in {"rate_limited", "transient"} or attempt == attempts:
                    return LinkCheck(
                        source_id=source_id,
                        requested_url=url,
                        final_url=final_url,
                        http_status=http_status,
                        status=link_status,
                        attempts=attempt,
                        detail=detail,
                    )
        except HTTPError as error:
            if error.code == 405:
                get_request = Request(
                    url,
                    method="GET",
                    headers={
                        "User-Agent": "optimization-compass-health/1",
                        "Range": "bytes=0-0",
                    },
                )
                try:
                    with opener(get_request, timeout=timeout_seconds) as response:
                        final_url = response.geturl()
                        return LinkCheck(
                            source_id=source_id,
                            requested_url=url,
                            final_url=final_url,
                            http_status=int(response.status),
                            status="redirect" if final_url != url else "healthy",
                            attempts=attempt,
                            detail=(
                                "redirected; review the canonical official URL"
                                if final_url != url
                                else "GET fallback succeeded after HEAD was rejected"
                            ),
                        )
                except HTTPError as get_error:
                    error = get_error
            last_status = error.code
            if error.code == 429:
                status: LinkStatus = "rate_limited"
                last_detail = "remote service rate-limited the check"
            elif error.code == 403:
                status = "access_restricted"
                last_detail = "automated access is restricted"
            elif error.code in TRANSIENT_STATUS_CODES:
                status = "transient"
                last_detail = f"transient HTTP {error.code}"
            else:
                status = "broken"
                last_detail = f"HTTP {error.code}"
            if status not in {"rate_limited", "transient"} or attempt == attempts:
                return LinkCheck(
                    source_id=source_id,
                    requested_url=url,
                    final_url=error.geturl(),
                    http_status=error.code,
                    status=status,
                    attempts=attempt,
                    detail=last_detail,
                )
        except (URLError, TimeoutError) as error:
            reason = error.reason if isinstance(error, URLError) else error
            if isinstance(reason, (ssl.SSLError, ssl.CertificateError)):
                return LinkCheck(
                    source_id=source_id,
                    requested_url=url,
                    final_url=None,
                    http_status=None,
                    status="tls_error",
                    attempts=attempt,
                    detail=str(reason),
                )
            last_detail = str(reason)
            if attempt == attempts:
                return LinkCheck(
                    source_id=source_id,
                    requested_url=url,
                    final_url=None,
                    http_status=last_status,
                    status="transient",
                    attempts=attempt,
                    detail=f"network failure after {attempts} attempts: {last_detail}",
                )
        if attempt < attempts:
            sleeper(float(2 ** (attempt - 1)))
    raise AssertionError("unreachable")


def build_source_health_report(
    repository: KnowledgeRepository,
    *,
    as_of: date,
    check_network: bool,
    checker: Callable[[str, str], LinkCheck] = check_source_url,
) -> SourceHealthReport:
    structural_errors: list[str] = []
    links: list[LinkCheck] = []
    stale: list[StaleCandidate] = []
    source_rows = repository.fetch_all("SELECT * FROM sources ORDER BY source_id")
    source_ids = {str(row["source_id"]) for row in source_rows}
    for row in source_rows:
        source_id = str(row["source_id"])
        source_type = str(row["source_type"])
        url = str(row["url"] or "")
        if not url.startswith(("http://", "https://")):
            structural_errors.append(f"{source_id}: invalid absolute HTTP(S) URL")
        verified = _date(row["accessed_date"], f"{source_id}.accessed_date", structural_errors)
        max_age = SOURCE_FRESHNESS_DAYS.get(source_type)
        if max_age is None:
            structural_errors.append(f"{source_id}: no freshness policy for {source_type}")
        elif verified is not None and (age := (as_of - verified).days) > max_age:
            stale.append(
                StaleCandidate(
                    entity_type="source",
                    entity_id=source_id,
                    stale_fields=["last_verified"],
                    last_verified=verified,
                    age_days=age,
                    max_age_days=max_age,
                )
            )
        if check_network and url.startswith(("http://", "https://")):
            links.append(checker(source_id, url))

    for row in repository.fetch_all(
        "SELECT evidence_link_id, source_id FROM evidence_links ORDER BY evidence_link_id"
    ):
        if str(row["source_id"]) not in source_ids:
            structural_errors.append(
                f"{row['evidence_link_id']}: dangling source {row['source_id']}"
            )

    for row in repository.fetch_all("SELECT * FROM implementations ORDER BY implementation_id"):
        identifier = str(row["implementation_id"])
        verified = _date(row["last_verified"], f"{identifier}.last_verified", structural_errors)
        if verified is None:
            continue
        stale_fields = [
            field
            for field in ("last_release", "maintenance_status", "license")
            if str(row[field] or "unknown") == "unknown"
        ]
        age = (as_of - verified).days
        if age > 90:
            stale_fields.extend(["last_release", "maintenance_status", "license"])
        if stale_fields:
            stale.append(
                StaleCandidate(
                    entity_type="implementation",
                    entity_id=identifier,
                    stale_fields=sorted(set(stale_fields)),
                    last_verified=verified,
                    age_days=max(0, age),
                    max_age_days=90,
                )
            )
    return SourceHealthReport(
        generated_on=as_of,
        network_checked=check_network,
        freshness_policy_days=dict(sorted(SOURCE_FRESHNESS_DAYS.items())),
        structural_errors=structural_errors,
        links=links,
        stale_candidates=stale,
    )


def _date(value: Any, field: str, errors: list[str]) -> date | None:
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        errors.append(f"{field}: invalid date")
        return None
