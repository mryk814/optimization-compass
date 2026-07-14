from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime
from typing import Literal
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from optimization_compass.db import KnowledgeRepository

SOURCE_FRESHNESS_DAYS: dict[str, int] = {
    "official_documentation": 90,
    "official_issue": 90,
    "official_repository": 90,
    "vendor_manual": 90,
    "standard": 365,
    "original_paper": 730,
    "textbook": 730,
    "university_material": 730,
}


class EvidenceModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class FreshnessRule(EvidenceModel):
    source_type: str = Field(min_length=1)
    max_age_days: int = Field(gt=0)


class EvidenceTarget(EvidenceModel):
    evidence_link_id: str = Field(min_length=1)
    target_table: str = Field(min_length=1)
    target_id: str = Field(min_length=1)
    target_type: str = Field(min_length=1)
    label: str = Field(min_length=1)
    canonical_url: str | None = None
    external_url: str | None = None
    supported_field: str
    claim_summary: str
    evidence_role: str
    confidence: str
    last_verified: date


class SourceRecord(EvidenceModel):
    source_id: str = Field(min_length=1)
    source_type: str = Field(min_length=1)
    title: str = Field(min_length=1)
    publisher: str = Field(min_length=1)
    publication_date: str | None = None
    last_verified: date
    official_url: str
    license: Literal["unknown"] = "unknown"
    access_note: str = Field(min_length=1)
    supported_claim: str
    source_quality: str
    currentness_status: str
    evidence_targets: list[EvidenceTarget]

    @field_validator("official_url")
    @classmethod
    def validate_official_url(cls, value: str) -> str:
        parsed = urlparse(value)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("official_url must be an absolute HTTP(S) URL")
        if parsed.username or parsed.password:
            raise ValueError("official_url must not contain credentials")
        return value


class SourceEvidenceIndex(EvidenceModel):
    contract_version: Literal["1.0.0"] = "1.0.0"
    dataset_version: str = Field(min_length=1)
    generated_at: datetime
    freshness_policy: list[FreshnessRule]
    sources: list[SourceRecord]

    @model_validator(mode="after")
    def validate_references(self) -> SourceEvidenceIndex:
        source_ids = [source.source_id for source in self.sources]
        if len(source_ids) != len(set(source_ids)):
            raise ValueError("duplicate source ID")
        evidence_ids = [
            target.evidence_link_id for source in self.sources for target in source.evidence_targets
        ]
        if len(evidence_ids) != len(set(evidence_ids)):
            raise ValueError("duplicate evidence link ID")
        policy_types = {rule.source_type for rule in self.freshness_policy}
        missing_policy = sorted({source.source_type for source in self.sources} - policy_types)
        if missing_policy:
            raise ValueError(f"missing freshness policy: {', '.join(missing_policy)}")
        return self


def build_source_evidence_index(
    repository: KnowledgeRepository,
    *,
    dataset_version: str,
    generated_at: datetime,
) -> SourceEvidenceIndex:
    descriptors = _target_descriptors(repository)
    targets_by_source: defaultdict[str, list[EvidenceTarget]] = defaultdict(list)
    for row in repository.fetch_all("SELECT * FROM evidence_links ORDER BY evidence_link_id"):
        key = (str(row["target_table"]), str(row["target_id"]))
        target_type, label, canonical_url, external_url = descriptors[key]
        targets_by_source[str(row["source_id"])].append(
            EvidenceTarget(
                evidence_link_id=str(row["evidence_link_id"]),
                target_table=key[0],
                target_id=key[1],
                target_type=target_type,
                label=label,
                canonical_url=canonical_url,
                external_url=external_url,
                supported_field=str(row["supported_field"] or ""),
                claim_summary=str(row["claim_summary"] or ""),
                evidence_role=str(row["evidence_role"] or ""),
                confidence=str(row["confidence"] or "unverified"),
                last_verified=date.fromisoformat(str(row["last_verified"])),
            )
        )

    sources = []
    for row in repository.fetch_all("SELECT * FROM sources ORDER BY source_id"):
        notes = str(row["notes"] or "").strip()
        sources.append(
            SourceRecord(
                source_id=str(row["source_id"]),
                source_type=str(row["source_type"]),
                title=str(row["title"]),
                publisher=str(row["author_or_organization"] or "unknown"),
                publication_date=str(row["publication_date"]) or None,
                last_verified=date.fromisoformat(str(row["accessed_date"])),
                official_url=str(row["url"]),
                access_note=notes or "公開条件・再利用条件は公式公開元で確認してください。",
                supported_claim=str(row["supported_claim"] or ""),
                source_quality=str(row["source_quality"] or ""),
                currentness_status=str(row["currentness_status"] or ""),
                evidence_targets=targets_by_source[str(row["source_id"])],
            )
        )
    return SourceEvidenceIndex(
        dataset_version=dataset_version,
        generated_at=generated_at,
        freshness_policy=[
            FreshnessRule(source_type=source_type, max_age_days=max_age_days)
            for source_type, max_age_days in sorted(SOURCE_FRESHNESS_DAYS.items())
        ],
        sources=sources,
    )


def _target_descriptors(
    repository: KnowledgeRepository,
) -> dict[tuple[str, str], tuple[str, str, str | None, str | None]]:
    descriptors: dict[tuple[str, str], tuple[str, str, str | None, str | None]] = {}

    def add(
        table: str,
        identifier: str,
        target_type: str,
        label: str,
        canonical_url: str | None = None,
        external_url: str | None = None,
    ) -> None:
        descriptors[(table, identifier)] = (
            target_type,
            label or identifier,
            canonical_url,
            external_url,
        )

    specs = {
        "alternative_solution_checks": ("alternative_id", "name_ja", "alternative"),
        "decision_rules": ("rule_id", "explanation", "rule"),
        "diagnostics": ("diagnostic_id", "name_ja", "diagnostic"),
        "example_cases": ("case_id", "title_ja", "case"),
        "failure_modes": ("failure_mode_id", "name_ja", "failure_mode"),
        "glossary": ("term_id", "term_ja", "glossary"),
        "methods": ("method_id", "name_ja", "method"),
        "model_revisions": ("revision_id", "reason", "model_revision"),
        "problem_archetypes": ("problem_id", "name_ja", "problem"),
        "problem_features": ("feature_id", "name_ja", "feature"),
    }
    for table, (id_column, label_column, target_type) in specs.items():
        for row in repository.fetch_all(
            f"SELECT {id_column} AS id, {label_column} AS label FROM {table} ORDER BY {id_column}"
        ):
            identifier = str(row["id"])
            canonical_url = (
                f"/methods/{identifier}"
                if target_type == "method"
                else "/diagnose"
                if target_type == "rule"
                else None
            )
            add(table, identifier, target_type, str(row["label"] or identifier), canonical_url)

    for row in repository.fetch_all(
        "SELECT implementation_id, library_name, solver_name, official_docs_url "
        "FROM implementations ORDER BY implementation_id"
    ):
        identifier = str(row["implementation_id"])
        add(
            "implementations",
            identifier,
            "implementation",
            str(row["library_name"] or row["solver_name"] or identifier),
            external_url=str(row["official_docs_url"] or "") or None,
        )
    for row in repository.fetch_all(
        "SELECT method_implementation_map_id, method_id, implementation_id "
        "FROM method_implementation_map ORDER BY method_implementation_map_id"
    ):
        identifier = str(row["method_implementation_map_id"])
        add(
            "method_implementation_map",
            identifier,
            "method_implementation",
            f"{row['method_id']} → {row['implementation_id']}",
            canonical_url=f"/methods/{row['method_id']}",
        )
    for row in repository.fetch_all(
        "SELECT fit_id, method_id, problem_or_feature_id FROM problem_method_fit ORDER BY fit_id"
    ):
        identifier = str(row["fit_id"])
        add(
            "problem_method_fit",
            identifier,
            "problem_method_fit",
            f"{row['problem_or_feature_id']} → {row['method_id']}",
            canonical_url=f"/methods/{row['method_id']}",
        )
    return descriptors
