"""Editorial scope: the planning denominator of the Atlas and how it maps onto canonical rows.

``data/seeds/editorial_scope.json`` lists what the Atlas intends to cover and, for every member,
how it relates to rows and articles that already exist. Scope IDs (``TOPIC_*``, ``STRUCTURE_*``) are
planning IDs only: they are never written into the released database and never used as routes.
This module deliberately produces counts, never ratios; coverage is a separate concern.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from optimization_compass.content_models import ContentPage
from optimization_compass.db import KnowledgeRepository

CONTRACT_VERSION = "1.0.0"
SCOPE_SEED_PATH = Path("data/seeds/editorial_scope.json")

Unit = Literal["knowledge_topic", "problem_structure"]
EntityKind = Literal[
    "algorithm",
    "variant",
    "strategy",
    "primitive",
    "problem_archetype",
    "modeling_profile",
    "neighboring_problem",
]
Tier = Literal["core", "applied", "frontier"]
Decision = Literal["include", "merge", "hold", "exclude"]
Relation = Literal[
    "same_entity",
    "alias_of",
    "variant_of",
    "primitive_in",
    "covered_by_family",
    "concept_content",
    "unrepresented",
    "unknown",
]
Review = Literal["candidate", "reviewed"]
Reviewer = Literal["owner", "claude", "codex", "human"]
RefType = Literal[
    "method", "problem", "problem_definition", "feature", "glossary", "term", "content"
]
Status = Literal["proposed", "approved"]

_UNIT_PREFIX: dict[str, str] = {"knowledge_topic": "TOPIC_", "problem_structure": "STRUCTURE_"}
_UNIT_KINDS: dict[str, frozenset[str]] = {
    "knowledge_topic": frozenset({"algorithm", "variant", "strategy", "primitive"}),
    "problem_structure": frozenset(
        {"problem_archetype", "modeling_profile", "neighboring_problem"}
    ),
}
_SCOPE_ID = re.compile(r"(TOPIC|STRUCTURE)_[A-Z0-9_]+")
_EMPTY_REF_RELATIONS = frozenset({"unrepresented", "unknown"})
_DUPLICATE_GUARDED_RELATIONS = frozenset({"same_entity", "alias_of"})
_NOTE_REQUIRED = frozenset({"merge", "hold", "exclude"})
_APPROVERS = frozenset({"owner", "human"})

_REF_QUERIES: dict[str, str] = {
    "method": "SELECT method_id AS id FROM methods",
    "problem": "SELECT problem_id AS id FROM problem_archetypes",
    "problem_definition": "SELECT problem_definition_id AS id FROM problem_definitions",
    "feature": "SELECT feature_id AS id FROM problem_features",
    "glossary": "SELECT term_id AS id FROM glossary",
    "term": "SELECT term_id AS id FROM terminology_aliases",
}


class _Frozen(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class ScopeSource(_Frozen):
    source_ref: str = Field(min_length=1)
    title: str = Field(min_length=1)
    url: str = Field(pattern=r"^https?://")
    checked_on: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")


class ScopeRef(_Frozen):
    type: RefType
    id: str = Field(min_length=1)


class ScopeMapping(_Frozen):
    relation: Relation
    refs: tuple[ScopeRef, ...] = ()
    review: Review
    reviewer: Reviewer | None = None
    reviewed_on: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    note_ja: str | None = None


class ScopeMember(_Frozen):
    scope_id: str
    unit: Unit
    title_ja: str = Field(min_length=1)
    title_en: str | None = Field(default=None, min_length=1)
    entity_kind: EntityKind
    tier: Tier
    decision: Decision
    merged_into: str | None = None
    decision_note_ja: str | None = None
    mapping: ScopeMapping
    source_refs: tuple[str, ...] = ()


class EditorialScope(_Frozen):
    contract_version: Literal["1.0.0"]
    scope_version: str = Field(min_length=1)
    status: Status
    approved_by: str | None = None
    approved_on: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    based_on: str = Field(min_length=1)
    sources: tuple[ScopeSource, ...] = ()
    members: tuple[ScopeMember, ...]


def load_editorial_scope(path: Path) -> EditorialScope:
    return EditorialScope.model_validate(json.loads(path.read_text(encoding="utf-8")))


def known_ref_ids(
    repository: KnowledgeRepository, pages: Iterable[ContentPage]
) -> dict[str, set[str]]:
    """Existing canonical IDs per ref type; read-only."""
    known = {
        ref_type: {str(row["id"]) for row in repository.fetch_all(sql)}
        for ref_type, sql in _REF_QUERIES.items()
    }
    known["content"] = {page.content_id for page in pages}
    return known


def validate_editorial_scope(scope: EditorialScope, *, known_refs: Mapping[str, set[str]]) -> None:
    """Collect every integrity problem and raise one ValueError listing them."""
    problems: list[str] = []
    by_id: dict[str, ScopeMember] = {}
    for member in scope.members:
        if member.scope_id in by_id:
            problems.append(f"duplicate scope_id: {member.scope_id}")
        by_id.setdefault(member.scope_id, member)

    source_refs = [source.source_ref for source in scope.sources]
    for ref in sorted({r for r in source_refs if source_refs.count(r) > 1}):
        problems.append(f"duplicate source_ref: {ref}")
    known_sources = set(source_refs)

    for member in scope.members:
        problems.extend(_member_problems(member, by_id, known_refs, known_sources))

    # A planning ID must never shadow a canonical ID (stable IDs are never repurposed).
    canonical_ids = set().union(*known_refs.values()) if known_refs else set()
    for sid in sorted(by_id):
        if sid in canonical_ids:
            problems.append(f"{sid}: scope_id collides with an existing canonical or content ID")

    # Denominators are per unit, so double counting is checked within a unit.
    includes_by_ref: dict[tuple[str, str, str], list[str]] = {}
    for member in scope.members:
        if member.decision == "include" and member.mapping.relation in _DUPLICATE_GUARDED_RELATIONS:
            for ref_type, ref_id in {(r.type, r.id) for r in member.mapping.refs}:
                key = (member.unit, ref_type, ref_id)
                includes_by_ref.setdefault(key, []).append(member.scope_id)
    for (_unit, guarded_type, guarded_id), owners in sorted(includes_by_ref.items()):
        if len(owners) > 1:
            problems.append(
                f"double counting of {guarded_type}:{guarded_id} by included members "
                f"{', '.join(sorted(owners))}; merge one into the other"
            )

    if scope.status == "approved":
        if scope.approved_by not in _APPROVERS:
            problems.append("approved scope requires approved_by of owner or human")
        if not scope.approved_on:
            problems.append("approved scope requires approved_on")

    if problems:
        raise ValueError("editorial scope is malformed: " + "; ".join(problems))


def _member_problems(
    member: ScopeMember,
    by_id: Mapping[str, ScopeMember],
    known_refs: Mapping[str, set[str]],
    known_sources: set[str],
) -> list[str]:
    sid = member.scope_id
    out: list[str] = []
    prefix = _UNIT_PREFIX[member.unit]
    if not _SCOPE_ID.fullmatch(sid):
        out.append(f"{sid}: scope_id must match ^(TOPIC|STRUCTURE)_[A-Z0-9_]+$")
    elif not sid.startswith(prefix):
        out.append(f"{sid}: unit {member.unit} requires the {prefix} prefix")
    if member.entity_kind not in _UNIT_KINDS[member.unit]:
        out.append(f"{sid}: entity_kind {member.entity_kind} is not allowed for {member.unit}")

    mapping = member.mapping
    seen: set[tuple[str, str]] = set()
    for ref in mapping.refs:
        key = (ref.type, ref.id)
        if key in seen:
            out.append(f"{sid}: duplicate ref {ref.type}:{ref.id}")
        seen.add(key)
        if ref.id not in known_refs.get(ref.type, set()):
            out.append(f"{sid}: unknown {ref.type} ref {ref.id}")
    if mapping.relation in _EMPTY_REF_RELATIONS and mapping.refs:
        out.append(f"{sid}: relation {mapping.relation} must have no refs")
    if mapping.relation not in _EMPTY_REF_RELATIONS and not mapping.refs:
        out.append(f"{sid}: relation {mapping.relation} requires at least one ref")
    if mapping.relation == "unknown" and mapping.review != "candidate":
        out.append(f"{sid}: relation unknown requires review candidate")
    if mapping.review == "reviewed" and (not mapping.reviewer or not mapping.reviewed_on):
        out.append(f"{sid}: reviewed mapping requires reviewer and reviewed_on")

    if member.decision == "merge":
        target = by_id.get(member.merged_into or "")
        if not member.merged_into:
            out.append(f"{sid}: merge requires merged_into")
        elif member.merged_into == sid:
            out.append(f"{sid}: cannot merge into itself")
        elif target is None:
            out.append(f"{sid}: merged_into {member.merged_into} does not exist")
        elif target.decision != "include":
            out.append(
                f"{sid}: merged_into {member.merged_into} must be an included member "
                "(no merge chains)"
            )
    elif member.merged_into is not None:
        out.append(f"{sid}: merged_into is only allowed when decision is merge")
    if member.decision in _NOTE_REQUIRED and not (member.decision_note_ja or "").strip():
        out.append(f"{sid}: decision {member.decision} requires decision_note_ja")

    for ref_name in member.source_refs:
        if ref_name not in known_sources:
            out.append(f"{sid}: unknown source_ref {ref_name}")
    return out


def require_scope_integrity(
    root: Path, repository: KnowledgeRepository, pages: Iterable[ContentPage]
) -> int | None:
    """Validate the scope seed if present; return its member count, or None when absent."""
    path = root / SCOPE_SEED_PATH
    if not path.exists():
        return None
    scope = load_editorial_scope(path)
    validate_editorial_scope(scope, known_refs=known_ref_ids(repository, pages))
    return len(scope.members)


def pending_members(scope: EditorialScope) -> tuple[ScopeMember, ...]:
    return tuple(
        m for m in scope.members if m.mapping.review == "candidate" or m.decision == "hold"
    )


def scope_summary(scope: EditorialScope) -> dict[str, Any]:
    """Counts only. There is intentionally no ratio or percentage field."""
    units: dict[str, Any] = {}
    for unit in _UNIT_PREFIX:
        members = [m for m in scope.members if m.unit == unit]
        included = [m for m in members if m.decision == "include"]
        units[unit] = {
            "members": len(members),
            "decision": _counts(m.decision for m in members),
            "included": {
                "entity_kind": _counts(m.entity_kind for m in included),
                "tier": _counts(m.tier for m in included),
                "relation": _counts(m.mapping.relation for m in included),
                "review": _counts(m.mapping.review for m in included),
            },
            "unreconciled": sum(1 for m in included if m.mapping.relation == "unknown"),
            "unrepresented": sum(1 for m in included if m.mapping.relation == "unrepresented"),
        }
    return {
        "scope_version": scope.scope_version,
        "status": scope.status,
        "based_on": scope.based_on,
        "members": len(scope.members),
        "units": units,
    }


def _counts(values: Iterable[str]) -> dict[str, int]:
    return dict(sorted(Counter(values).items()))
