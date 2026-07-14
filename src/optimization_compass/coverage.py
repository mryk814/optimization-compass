from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from typing import Any, Literal, cast

from pydantic import BaseModel, ConfigDict, Field

from optimization_compass.db import KnowledgeRepository
from optimization_compass.visualization_scenarios import VisualizationScenarioIndex

CoverageStatus = Literal["available", "partial", "missing", "not_applicable"]
InventoryState = Literal["connected", "absent", "broken"]
DIMENSIONS = (
    "map",
    "recommendation",
    "content",
    "visualization",
    "comparison",
    "gallery",
    "implementation",
    "source",
)


class CoverageModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class InventoryDimension(CoverageModel):
    state: InventoryState
    count: int = Field(ge=0)
    target_ids: list[str]
    reason_codes: list[str]


class CoverageSubject(CoverageModel):
    subject_type: Literal["method", "problem", "feature_family"]
    subject_id: str
    label: str
    dimensions: dict[str, InventoryDimension]


class CoverageExpectation(CoverageModel):
    expectation_id: str
    subject_type: Literal["method", "problem", "feature_family"]
    subject_id: str
    purpose: Literal[
        "mechanism",
        "comparison",
        "failure_contrast",
        "sensitivity",
        "application_result",
        "schematic",
    ]
    artifact_kind: Literal[
        "executable_trace", "schematic_animation", "static_diagram", "result_visualization"
    ]
    renderer_family: str
    applicability: Literal["expected", "not_applicable"]
    status: CoverageStatus
    rationale: str
    reason_codes: list[str]
    scenario_ids: list[str]
    artifact_ids: list[str]
    route_ids: list[str]
    source_ids: list[str]
    slice_id: str | None


class PriorityFactor(CoverageModel):
    score: int = Field(ge=0, le=3)
    reason: str


class CoveragePriority(CoverageModel):
    slice_id: str
    title_ja: str
    title_en: str
    rank: int = Field(ge=1)
    total: int = Field(ge=0, le=12)
    factors: dict[str, PriorityFactor]
    proposed_scope: str
    source_ids: list[str]


class IntegrityIssue(CoverageModel):
    code: str
    severity: Literal["warning", "error"]
    entity_type: str
    entity_id: str
    detail: str


class CoverageSummary(CoverageModel):
    subject_counts: dict[str, int]
    status_counts: dict[str, int]
    baseline: Literal["not_provided"] = "not_provided"


class CoverageReport(CoverageModel):
    contract_version: Literal["1.0.0"] = "1.0.0"
    dataset_version: str
    generated_at: datetime
    summary: CoverageSummary
    subjects: list[CoverageSubject]
    expectations: list[CoverageExpectation]
    priorities: list[CoveragePriority]
    integrity_issues: list[IntegrityIssue]


class CoverageDelta(CoverageModel):
    contract_version: Literal["1.0.0"] = "1.0.0"
    before_dataset_version: str
    after_dataset_version: str
    transitions: dict[str, int]
    added_expectation_ids: list[str]
    removed_expectation_ids: list[str]
    subject_count_delta: dict[str, int]
    available_delta: int


def build_coverage_report(
    repository: KnowledgeRepository,
    artifact_root: Path,
    *,
    dataset_version: str,
    generated_at: datetime,
) -> CoverageReport:
    artifacts = _load_artifacts(artifact_root)
    subjects, membership = _build_inventory(repository, artifacts)
    integrity = _integrity_issues(repository, artifacts)
    expectations = _derive_expectations(repository, artifacts, membership, integrity)
    priorities = _priorities(repository)
    counts = Counter(item.status for item in expectations)
    return CoverageReport(
        dataset_version=dataset_version,
        generated_at=generated_at,
        summary=CoverageSummary(
            subject_counts=dict(Counter(item.subject_type for item in subjects)),
            status_counts={
                status: counts.get(status, 0)
                for status in ("available", "partial", "missing", "not_applicable")
            },
        ),
        subjects=subjects,
        expectations=expectations,
        priorities=priorities,
        integrity_issues=integrity,
    )


def write_coverage_report(report: CoverageReport, json_path: Path, markdown_path: Path) -> None:
    json_path.write_text(
        json.dumps(report.model_dump(mode="json"), ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    lines = [
        "# Atlas learning coverage",
        "",
        f"- Dataset: `{report.dataset_version}`",
        f"- Generated: `{report.generated_at.isoformat()}`",
        "- Baseline: not provided (this initial snapshot does not claim a release delta)",
        "",
        "## Expected learning artifacts",
        "",
        "| Status | Count |",
        "|---|---:|",
    ]
    lines.extend(
        f"| {status} | {count} |" for status, count in report.summary.status_counts.items()
    )
    lines.extend(
        ["", "## Priority slices", "", "| Rank | Slice | Score | Why now |", "|---:|---|---:|---|"]
    )
    lines.extend(
        f"| {item.rank} | {item.title_en} | {item.total}/12 | "
        f"{item.factors['classification'].reason} |"
        for item in report.priorities
    )
    lines.extend(["", "## Integrity issues", ""])
    lines.extend(
        f"- `{item.code}` `{item.entity_id}`: {item.detail}" for item in report.integrity_issues
    )
    if not report.integrity_issues:
        lines.append("- None")
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def diff_coverage(before: CoverageReport, after: CoverageReport) -> CoverageDelta:
    before_by_id = {item.expectation_id: item for item in before.expectations}
    after_by_id = {item.expectation_id: item for item in after.expectations}
    shared = sorted(before_by_id.keys() & after_by_id.keys())
    transitions = Counter(
        f"{before_by_id[item_id].status}->{after_by_id[item_id].status}"
        for item_id in shared
        if before_by_id[item_id].status != after_by_id[item_id].status
    )
    subject_types = set(before.summary.subject_counts) | set(after.summary.subject_counts)
    return CoverageDelta(
        before_dataset_version=before.dataset_version,
        after_dataset_version=after.dataset_version,
        transitions=dict(sorted(transitions.items())),
        added_expectation_ids=sorted(after_by_id.keys() - before_by_id.keys()),
        removed_expectation_ids=sorted(before_by_id.keys() - after_by_id.keys()),
        subject_count_delta={
            item: after.summary.subject_counts.get(item, 0)
            - before.summary.subject_counts.get(item, 0)
            for item in sorted(subject_types)
        },
        available_delta=(
            after.summary.status_counts.get("available", 0)
            - before.summary.status_counts.get("available", 0)
        ),
    )


def _load_artifacts(root: Path) -> dict[str, Any]:
    paths = {
        "links": "entity-links.json",
        "traces": "traces/index.json",
        "content": "content.json",
        "comparisons": "comparisons.json",
        "gallery": "gallery.json",
        "sources": "sources.json",
        "recommendation": "recommendation/site-data.json",
        "visualization_scenarios": "visualization-scenarios.json",
    }
    artifacts = {
        key: json.loads((root / relative).read_text(encoding="utf-8"))
        for key, relative in paths.items()
    }
    artifacts["scenario_contracts"] = _load_scenario_contracts(root, artifacts)
    return artifacts


def _load_scenario_contracts(root: Path, artifacts: dict[str, Any]) -> list[dict[str, Any]]:
    """Expand the canonical scenario index into method-level coverage contracts."""
    index = VisualizationScenarioIndex.model_validate(artifacts["visualization_scenarios"])
    routes = {
        str(entity["entity_id"]): str(entity["canonical_url"])
        for entity in artifacts["links"]["entities"]
        if entity.get("entity_type") == "trace" and entity.get("canonical_url")
    }
    contracts: list[dict[str, Any]] = []
    for scenario in index.scenarios:
        payload_path = root / scenario.artifact.payload_path
        payload_complete = (
            payload_path.is_file()
            and payload_path.stat().st_size == scenario.artifact.payload_bytes
            and sha256(payload_path.read_bytes()).hexdigest() == scenario.artifact.payload_sha256
        )
        for run in scenario.runs:
            route = routes.get(run.artifact_id) or _scenario_route(
                scenario.artifact.renderer_family, scenario.scenario_id, run.artifact_id
            )
            contracts.append(
                {
                    "scenario_id": scenario.scenario_id,
                    "identity_status": scenario.identity_status,
                    "canonical_scenario_id": scenario.canonical_scenario_id,
                    "subject_id": run.method_id,
                    "purpose": scenario.purpose,
                    "artifact_kind": scenario.artifact.artifact_kind,
                    "renderer_family": scenario.artifact.renderer_family,
                    "artifact_id": run.artifact_id,
                    "payload_path": scenario.artifact.payload_path,
                    "payload_complete": payload_complete,
                    "route": route,
                    "source_ids": list(scenario.source_ids),
                }
            )
    return contracts


def _scenario_route(renderer_family: str, scenario_id: str, artifact_id: str) -> str | None:
    if renderer_family == "search_tree":
        return f"/theater/search-tree/{artifact_id}"
    if renderer_family == "surrogate_uncertainty":
        return f"/theater/bayesian-optimization/{scenario_id}"
    if renderer_family == "simplex_geometry":
        return "/theater/nelder-mead"
    if renderer_family == "continuous_trajectory":
        return "/compare/first-order"
    return None


def _build_inventory(
    repository: KnowledgeRepository, artifacts: dict[str, Any]
) -> tuple[list[CoverageSubject], dict[str, set[str]]]:
    methods = repository.fetch_all(
        "SELECT method_id, name_en, method_family_id FROM methods ORDER BY method_id"
    )
    problems = repository.fetch_all(
        "SELECT problem_id, name_en FROM problem_archetypes ORDER BY problem_id"
    )
    features = repository.fetch_all(
        "SELECT feature_id, category FROM problem_features ORDER BY feature_id"
    )
    members: dict[str, set[str]] = defaultdict(set)
    for row in methods:
        members[str(row["method_family_id"])].add(str(row["method_id"]))
    for row in features:
        members[str(row["category"])].add(str(row["feature_id"]))
    rows = (
        [
            ("method", str(row["method_id"]), str(row["name_en"]), {str(row["method_id"])})
            for row in methods
        ]
        + [
            ("problem", str(row["problem_id"]), str(row["name_en"]), {str(row["problem_id"])})
            for row in problems
        ]
        + [
            ("feature_family", category, category.replace("_", " ").title(), ids)
            for category, ids in sorted(members.items())
            if not category.startswith("MF_")
        ]
    )
    links = artifacts["links"]["entities"]
    link_targets: dict[tuple[str, str], dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    relation_dimensions = {
        "content": "content",
        "trace": "visualization",
        "comparison": "comparison",
        "case": "gallery",
        "implementation": "implementation",
        "source": "source",
    }
    for entity in links:
        subject = (str(entity["entity_type"]), str(entity["entity_id"]))
        for relation in entity.get("relations", []):
            target_id = str(relation["target_id"])
            link_targets[subject]["map"].add(target_id)
            dimension = relation_dimensions.get(str(relation["target_type"]))
            if dimension is not None:
                link_targets[subject][dimension].add(target_id)
        link_targets[subject]["map"].add(str(entity["canonical_url"]))
    recommendation = artifacts["recommendation"]
    for rule in recommendation["rules"]:
        target_type = str(rule["action_target_type"])
        for target_id in rule["action_target_ids"]:
            link_targets[(target_type, str(target_id))]["recommendation"].add(str(rule["rule_id"]))
    for implementation in repository.fetch_all(
        "SELECT method_id, implementation_id FROM method_implementation_map"
    ):
        link_targets[("method", str(implementation["method_id"]))]["implementation"].add(
            str(implementation["implementation_id"])
        )
    evidence_types = {
        "methods": "method",
        "problem_archetypes": "problem",
        "problem_features": "feature",
    }
    for evidence in repository.fetch_all(
        "SELECT target_table, target_id, source_id FROM evidence_links"
    ):
        entity_type = evidence_types.get(str(evidence["target_table"]))
        if entity_type is not None:
            link_targets[(entity_type, str(evidence["target_id"]))]["source"].add(
                str(evidence["source_id"])
            )
    for trace in artifacts["traces"]["traces"]:
        link_targets[("method", str(trace["method_id"]))]["visualization"].add(
            str(trace["trace_id"])
        )
    for artifact in artifacts["scenario_contracts"]:
        artifact_id = str(
            artifact.get("artifact_id") or artifact.get("trace_id") or artifact["scenario_id"]
        )
        link_targets[("method", str(artifact["subject_id"]))]["visualization"].add(artifact_id)
    for comparison in artifacts["comparisons"]["comparisons"]:
        for member in comparison["members"]:
            link_targets[("method", str(member["method_id"]))]["comparison"].add(
                str(comparison["comparison_id"])
            )
    for case in artifacts["gallery"]["cases"]:
        for method_id in case.get("candidate_method_ids", []):
            link_targets[("method", str(method_id))]["gallery"].add(str(case["case_id"]))
        for feature_id in case.get("feature_values", []):
            if isinstance(feature_id, dict) and "feature_id" in feature_id:
                link_targets[("feature", str(feature_id["feature_id"]))]["gallery"].add(
                    str(case["case_id"])
                )
    result: list[CoverageSubject] = []
    for subject_type, subject_id, label, own_ids in rows:
        expanded = set(own_ids) | members.get(subject_id, set())
        targets: dict[str, set[str]] = defaultdict(set)
        entity_type = "feature" if subject_type == "feature_family" else subject_type
        for item_id in expanded:
            for dimension, ids in link_targets[(entity_type, item_id)].items():
                targets[dimension].update(ids)
        dimensions = {
            dimension: InventoryDimension(
                state="connected" if targets[dimension] else "absent",
                count=len(targets[dimension]),
                target_ids=sorted(targets[dimension]),
                reason_codes=[] if targets[dimension] else ["no_inventory_connection"],
            )
            for dimension in DIMENSIONS
        }
        result.append(
            CoverageSubject(
                subject_type=cast(Literal["method", "problem", "feature_family"], subject_type),
                subject_id=subject_id,
                label=label,
                dimensions=dimensions,
            )
        )
    return result, members


def _derive_expectations(
    repository: KnowledgeRepository,
    artifacts: dict[str, Any],
    membership: dict[str, set[str]],
    integrity: list[IntegrityIssue],
) -> list[CoverageExpectation]:
    rows = repository.fetch_all(
        "SELECT * FROM learning_coverage_expectations ORDER BY expectation_id"
    )
    traces = artifacts["traces"]["traces"]
    scenario_contracts = artifacts["scenario_contracts"]
    broken_scenarios = {item.entity_id for item in integrity if item.code == "broken_scenario_id"}
    result: list[CoverageExpectation] = []
    for row in rows:
        subject_id = str(row["subject_id"])
        eligible = {subject_id} | membership.get(subject_id, set())
        legacy_candidates = [item for item in traces if str(item.get("method_id")) in eligible]
        contracted_candidates = [
            item for item in scenario_contracts if str(item.get("subject_id")) in eligible
        ]
        explicit = [
            item
            for item in contracted_candidates
            if item.get("purpose") == row["purpose"]
            and item.get("artifact_kind") == row["artifact_kind"]
            and item.get("renderer_family") == row["renderer_family"]
        ]
        applicability = str(row["applicability"])
        if applicability == "not_applicable":
            status: CoverageStatus = "not_applicable"
            reasons = ["explicit_policy"]
        elif not legacy_candidates and not contracted_candidates:
            status = "missing"
            reasons = ["scenario_not_built"]
        elif not explicit:
            status = "partial"
            reasons = ["scenario_contract_incomplete"]
        else:
            broken = [item for item in explicit if str(item.get("scenario_id")) in broken_scenarios]
            incomplete = [
                item
                for item in explicit
                if not item.get("artifact_id")
                or not item.get("payload_complete")
                or not (item.get("canonical_url") or item.get("route"))
                or not item.get("source_ids")
            ]
            if broken or incomplete:
                status = "partial"
                reasons = [
                    "artifact_reference_broken" if broken else "scenario_contract_incomplete"
                ]
            else:
                status = "available"
                reasons = []
        result.append(
            CoverageExpectation(
                expectation_id=str(row["expectation_id"]),
                subject_type=row["subject_type"],
                subject_id=subject_id,
                purpose=row["purpose"],
                artifact_kind=row["artifact_kind"],
                renderer_family=str(row["renderer_family"]),
                applicability=row["applicability"],
                status=status,
                rationale=str(row["rationale"]),
                reason_codes=reasons,
                scenario_ids=sorted(
                    {
                        str(item["scenario_id"])
                        for item in [*legacy_candidates, *contracted_candidates]
                    }
                ),
                artifact_ids=sorted(
                    {
                        str(item.get("artifact_id") or item.get("trace_id"))
                        for item in explicit
                        if item.get("artifact_id") or item.get("trace_id")
                    }
                ),
                route_ids=sorted(
                    {
                        str(item.get("canonical_url") or item.get("route"))
                        for item in explicit
                        if item.get("canonical_url") or item.get("route")
                    }
                ),
                source_ids=json.loads(str(row["source_ids_json"])),
                slice_id=row["slice_id"],
            )
        )
    return result


def _priorities(repository: KnowledgeRepository) -> list[CoveragePriority]:
    rows = repository.fetch_all("SELECT * FROM learning_slice_priorities")
    scored: list[tuple[int, str, dict[str, Any]]] = []
    for row in rows:
        total = sum(
            int(row[f"{name}_score"])
            for name in ("classification", "misconception", "visualization", "demand")
        )
        scored.append((total, str(row["slice_id"]), row))
    scored.sort(key=lambda item: (-item[0], item[1]))
    return [
        CoveragePriority(
            slice_id=slice_id,
            title_ja=str(row["title_ja"]),
            title_en=str(row["title_en"]),
            rank=rank,
            total=total,
            factors={
                name: PriorityFactor(
                    score=int(row[f"{name}_score"]), reason=str(row[f"{name}_reason"])
                )
                for name in ("classification", "misconception", "visualization", "demand")
            },
            proposed_scope=str(row["proposed_scope"]),
            source_ids=json.loads(str(row["source_ids_json"])),
        )
        for rank, (total, slice_id, row) in enumerate(scored, start=1)
    ]


def _integrity_issues(
    repository: KnowledgeRepository, artifacts: dict[str, Any]
) -> list[IntegrityIssue]:
    database_scenarios = {
        str(row["scenario_id"])
        for row in repository.fetch_all("SELECT scenario_id FROM demo_scenarios")
    }
    scenario_contracts = artifacts["scenario_contracts"]
    canonical_scenarios = {
        str(item.get("canonical_scenario_id") or item["scenario_id"])
        for item in scenario_contracts
        if item.get("identity_status") in {"canonical", "derived"}
    }
    broken_aliases = sorted(
        {
            str(item["canonical_scenario_id"])
            for item in scenario_contracts
            if item.get("identity_status") == "derived"
            and item.get("canonical_scenario_id") not in database_scenarios
        }
    )
    database_comparisons = {
        str(row["comparison_set_id"])
        for row in repository.fetch_all("SELECT comparison_set_id FROM comparison_sets")
    }
    comparison_records = artifacts["comparisons"]["comparisons"]
    canonical_comparisons = {
        str(item.get("canonical_comparison_id") or item["comparison_id"])
        for item in comparison_records
        if item.get("identity_status") in {"canonical", "derived"}
    }
    broken_comparison_aliases = sorted(
        {
            str(item["canonical_comparison_id"])
            for item in comparison_records
            if item.get("identity_status") == "derived"
            and item.get("canonical_comparison_id") not in database_comparisons
        }
    )
    issues = [
        IntegrityIssue(
            code="broken_scenario_id",
            severity="error",
            entity_type="scenario",
            entity_id=item,
            detail="The canonical database scenario has no generated trace with the same ID.",
        )
        for item in sorted(database_scenarios - canonical_scenarios)
    ]
    issues.extend(
        IntegrityIssue(
            code="broken_scenario_alias",
            severity="error",
            entity_type="scenario",
            entity_id=item,
            detail=(
                "A derived generated scenario points to a canonical scenario "
                "missing from the database."
            ),
        )
        for item in broken_aliases
    )
    issues.extend(
        IntegrityIssue(
            code="orphan_comparison",
            severity="error",
            entity_type="comparison",
            entity_id=item,
            detail=(
                "The canonical database comparison has no generated comparison with the same ID."
            ),
        )
        for item in sorted(database_comparisons - canonical_comparisons)
    )
    issues.extend(
        IntegrityIssue(
            code="broken_comparison_alias",
            severity="error",
            entity_type="comparison",
            entity_id=item,
            detail=(
                "A derived generated comparison points to a canonical comparison "
                "missing from the database."
            ),
        )
        for item in broken_comparison_aliases
    )
    return issues
