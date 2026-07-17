from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Self
from urllib.parse import quote

from pydantic import BaseModel, ConfigDict, Field, model_validator

from optimization_compass.db import KnowledgeRepository


class FailureDiscoveryModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class FailureMitigation(FailureDiscoveryModel):
    action: str = Field(min_length=1)
    applicability: str = Field(min_length=1)
    tradeoff: str = Field(min_length=1)


class CaseContext(FailureDiscoveryModel):
    question: str = Field(min_length=1)
    decision_variables: str = Field(min_length=1)
    objective: str = Field(min_length=1)
    constraints: str = Field(min_length=1)


class FailureDiscoveryEntry(FailureDiscoveryModel):
    entry_id: str = Field(min_length=3)
    entry_kind: Literal["structured_failure", "case_exclusion"]
    disposition: Literal["excluded", "warning", "conditional", "observed_failure", "unsupported"]
    title_ja: str = Field(min_length=1)
    title_en: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    scope: Literal["method_theory", "implementation_specific", "mixed", "case_specific"]
    severity: Literal["critical", "high", "warning", "info", "not_applicable"]
    recoverability: Literal["recoverable", "conditional", "fatal", "not_applicable"]
    confidence: Literal["high", "medium", "low", "unverified", "not_applicable"]
    failure_mode_id: str | None
    case_id: str | None
    method_ids: list[str]
    implementation_ids: list[str]
    feature_ids: list[str]
    scenario_ids: list[str]
    source_ids: list[str]
    symptoms: list[str]
    diagnostics: list[str]
    mitigations: list[FailureMitigation]
    related_failure_mode_ids: list[str]
    case_context: CaseContext | None
    canonical_route: str = Field(pattern=r"^/failures\?entry=")
    last_verified: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_semantics(self) -> Self:
        list_fields = (
            self.method_ids,
            self.implementation_ids,
            self.feature_ids,
            self.scenario_ids,
            self.source_ids,
            self.symptoms,
            self.diagnostics,
            self.related_failure_mode_ids,
        )
        if any(values != sorted(set(values)) for values in list_fields):
            raise ValueError("failure discovery lists must be unique and sorted")
        if self.entry_kind == "structured_failure":
            if (
                self.failure_mode_id is None
                or self.case_id is not None
                or self.case_context is not None
            ):
                raise ValueError("structured failure identity is inconsistent")
            if not self.symptoms or not self.diagnostics or not self.mitigations:
                raise ValueError(
                    "structured failures require symptoms, diagnostics, and mitigations"
                )
            if self.scope == "case_specific" or self.severity == "not_applicable":
                raise ValueError("structured failure scope/severity is inconsistent")
        else:
            if (
                self.case_id is None
                or self.failure_mode_id is not None
                or self.case_context is None
            ):
                raise ValueError("case exclusion identity is inconsistent")
            if len(self.method_ids) != 1 or self.disposition != "excluded":
                raise ValueError("case exclusions require one excluded method")
            if self.scope != "case_specific":
                raise ValueError("case exclusions must use case_specific scope")
            if any(
                value != "not_applicable"
                for value in (self.severity, self.recoverability, self.confidence)
            ):
                raise ValueError(
                    "case exclusions do not infer severity, recoverability, or confidence"
                )
        return self


class FailureDiscoverySummary(FailureDiscoveryModel):
    total_entries: int = Field(ge=0)
    structured_failure_count: int = Field(ge=0)
    case_exclusion_count: int = Field(ge=0)
    entries_with_scenarios: int = Field(ge=0)


class FailureDiscoveryIndex(FailureDiscoveryModel):
    contract_version: Literal["1.0.0"] = "1.0.0"
    dataset_version: str = Field(min_length=1)
    generated_at: datetime
    summary: FailureDiscoverySummary
    entries: list[FailureDiscoveryEntry]

    @model_validator(mode="after")
    def validate_index(self) -> Self:
        ids = [entry.entry_id for entry in self.entries]
        if ids != sorted(ids) or len(ids) != len(set(ids)):
            raise ValueError("failure discovery entries must be unique and sorted")
        structured_ids = {
            entry.failure_mode_id for entry in self.entries if entry.failure_mode_id is not None
        }
        dangling = {
            related
            for entry in self.entries
            for related in entry.related_failure_mode_ids
            if related not in structured_ids
        }
        if dangling:
            raise ValueError(f"failure discovery has dangling failure links: {sorted(dangling)}")
        expected = FailureDiscoverySummary(
            total_entries=len(self.entries),
            structured_failure_count=sum(
                entry.entry_kind == "structured_failure" for entry in self.entries
            ),
            case_exclusion_count=sum(
                entry.entry_kind == "case_exclusion" for entry in self.entries
            ),
            entries_with_scenarios=sum(bool(entry.scenario_ids) for entry in self.entries),
        )
        if self.summary != expected:
            raise ValueError("failure discovery summary must be derived from entries")
        return self


def build_failure_discovery_index(
    repository: KnowledgeRepository,
    *,
    dataset_version: str,
    generated_at: datetime,
    gallery_index: dict[str, Any],
    learning_journeys: Any,
) -> FailureDiscoveryIndex:
    methods = {
        str(row["method_id"]): row
        for row in repository.fetch_all(
            "SELECT method_id, name_ja, name_en FROM methods ORDER BY method_id"
        )
    }
    failures = repository.structured_failure_modes()
    failure_ids_by_method: dict[str, set[str]] = {}
    for failure in failures:
        failure_id = str(failure["failure_mode_id"])
        for affected in failure["affected_entities"]:
            if affected["entity_type"] == "method":
                failure_ids_by_method.setdefault(str(affected["entity_id"]), set()).add(failure_id)

    journeys_by_case = {str(journey.case_id): journey for journey in learning_journeys.journeys}
    entries: list[FailureDiscoveryEntry] = []
    for failure in failures:
        affected = list(failure["affected_entities"])
        method_ids = sorted(
            str(item["entity_id"]) for item in affected if item["entity_type"] == "method"
        )
        implementation_ids = sorted(
            str(item["entity_id"]) for item in affected if item["entity_type"] == "implementation"
        )
        feature_ids = sorted(
            str(item["entity_id"]) for item in affected if item["entity_type"] == "feature"
        )
        failure_id = str(failure["failure_mode_id"])
        entries.append(
            FailureDiscoveryEntry(
                entry_id=f"structured:{failure_id}",
                entry_kind="structured_failure",
                disposition=(
                    "excluded" if str(failure["diagnose_disposition"]) == "exclude" else "warning"
                ),
                title_ja=str(failure["name_ja"]),
                title_en=str(failure["name_en"]),
                summary=str(failure["symptoms"][0]["description"]),
                scope=failure["failure_scope"],
                severity=failure["severity"],
                recoverability=failure["recoverability"],
                confidence=failure["confidence"],
                failure_mode_id=failure_id,
                case_id=None,
                method_ids=method_ids,
                implementation_ids=implementation_ids,
                feature_ids=feature_ids,
                scenario_ids=sorted(map(str, failure["scenario_ids"])),
                source_ids=sorted(map(str, failure["source_ids"])),
                symptoms=sorted(str(item["description"]) for item in failure["symptoms"]),
                diagnostics=sorted(str(item["check_text"]) for item in failure["diagnostics"]),
                mitigations=[
                    FailureMitigation(
                        action=str(item["action"]),
                        applicability=str(item["applicability"]),
                        tradeoff=str(item["tradeoff"]),
                    )
                    for item in sorted(
                        failure["mitigations"], key=lambda item: (item["priority"], item["action"])
                    )
                ],
                related_failure_mode_ids=[],
                case_context=None,
                canonical_route=f"/failures?entry={quote(f'structured:{failure_id}', safe='')}",
                last_verified=str(failure["last_verified"]),
            )
        )

    for case in sorted(gallery_index["cases"], key=lambda item: str(item["case_id"])):
        if case.get("status") != "published":
            continue
        case_id = str(case["case_id"])
        journey = journeys_by_case.get(case_id)
        scenario_ids = (
            sorted(str(item.scenario_id) for item in journey.scenarios)
            if journey is not None
            else []
        )
        context = CaseContext(
            question=str(case["question"]),
            decision_variables=str(case["decision_variables"]),
            objective=str(case["objective"]),
            constraints=str(case["constraints"]),
        )
        for exclusion in sorted(case["excluded_methods"], key=lambda item: str(item["method_id"])):
            method_id = str(exclusion["method_id"])
            method = methods.get(method_id)
            if method is None:
                raise ValueError(f"case exclusion references unknown method: {method_id}")
            entry_id = f"case:{case_id}:{method_id}"
            entries.append(
                FailureDiscoveryEntry(
                    entry_id=entry_id,
                    entry_kind="case_exclusion",
                    disposition="excluded",
                    title_ja=f"{case['title_ja']}では{method['name_ja']}を選ばない",
                    title_en=f"Why {method['name_en']} is excluded for {case['title_en']}",
                    summary=str(exclusion["reason"]),
                    scope="case_specific",
                    severity="not_applicable",
                    recoverability="not_applicable",
                    confidence="not_applicable",
                    failure_mode_id=None,
                    case_id=case_id,
                    method_ids=[method_id],
                    implementation_ids=[],
                    feature_ids=sorted(
                        {
                            str(item["feature_id"])
                            for item in case.get("feature_values", [])
                            if isinstance(item, dict) and item.get("feature_id")
                        }
                    ),
                    scenario_ids=scenario_ids,
                    source_ids=sorted(map(str, case["source_ids"])),
                    symptoms=[],
                    diagnostics=[],
                    mitigations=[],
                    related_failure_mode_ids=sorted(failure_ids_by_method.get(method_id, set())),
                    case_context=context,
                    canonical_route=f"/failures?entry={quote(entry_id, safe='')}",
                    last_verified=str(case["last_reviewed"]),
                )
            )

    entries.sort(key=lambda entry: entry.entry_id)
    return FailureDiscoveryIndex(
        dataset_version=dataset_version,
        generated_at=generated_at,
        summary=FailureDiscoverySummary(
            total_entries=len(entries),
            structured_failure_count=sum(
                entry.entry_kind == "structured_failure" for entry in entries
            ),
            case_exclusion_count=sum(entry.entry_kind == "case_exclusion" for entry in entries),
            entries_with_scenarios=sum(bool(entry.scenario_ids) for entry in entries),
        ),
        entries=entries,
    )
