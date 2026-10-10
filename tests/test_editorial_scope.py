from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from optimization_compass.editorial_scope import (
    SCOPE_SEED_PATH,
    EditorialScope,
    known_ref_ids,
    load_editorial_scope,
    pending_members,
    scope_summary,
    validate_editorial_scope,
)

ROOT = Path(__file__).parents[1]
KNOWN = {
    "method": {"M_GD", "M_ADAM"},
    "problem": {"PA001"},
    "feature": {"F_X"},
    "glossary": {"G_X"},
    "term": {"T_X"},
    "content": {"method.gd"},
}


def _member(scope_id: str = "TOPIC_GD", **overrides: Any) -> dict[str, Any]:
    member: dict[str, Any] = {
        "scope_id": scope_id,
        "unit": "knowledge_topic",
        "title_ja": "勾配降下法",
        "title_en": "Gradient descent",
        "entity_kind": "algorithm",
        "tier": "core",
        "decision": "include",
        "merged_into": None,
        "decision_note_ja": None,
        "mapping": {
            "relation": "same_entity",
            "refs": [{"type": "method", "id": "M_GD"}],
            "review": "reviewed",
            "reviewer": "claude",
            "reviewed_on": "2026-10-10",
            "note_ja": "対応する。",
        },
        "source_refs": ["E01"],
    }
    member.update(overrides)
    return member


def _scope(*members: dict[str, Any], **overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "contract_version": "1.0.0",
        "scope_version": "editorial-scope-test",
        "status": "proposed",
        "approved_by": None,
        "approved_on": None,
        "based_on": "draft",
        "sources": [
            {
                "source_ref": "E01",
                "title": "t",
                "url": "https://example.org",
                "checked_on": "2026-10-10",
            }
        ],
        "members": list(members) or [_member()],
    }
    payload.update(overrides)
    return payload


def _check(payload: dict[str, Any]) -> None:
    validate_editorial_scope(EditorialScope.model_validate(payload), known_refs=KNOWN)


def _mapping(**changes: Any) -> dict[str, Any]:
    mapping = copy.deepcopy(_member()["mapping"])
    mapping.update(changes)
    return mapping


def test_valid_scope_passes() -> None:
    merged = _member(
        "TOPIC_GD2",
        decision="merge",
        merged_into="TOPIC_GD",
        decision_note_ja="同じ内容のため統合する。",
        mapping=_mapping(relation="alias_of"),
    )
    _check(_scope(_member(), merged))


@pytest.mark.parametrize(
    ("member", "needle"),
    [
        (_member("TOPIC_gd"), "scope_id must match"),
        (_member("STRUCTURE_GD"), "requires the TOPIC_ prefix"),
        (_member(entity_kind="problem_archetype"), "not allowed for knowledge_topic"),
        (_member(mapping=_mapping(refs=[{"type": "method", "id": "M_NOPE"}])), "unknown method"),
        (
            _member(
                mapping=_mapping(
                    refs=[{"type": "method", "id": "M_GD"}, {"type": "method", "id": "M_GD"}]
                )
            ),
            "duplicate ref",
        ),
        (_member(mapping=_mapping(relation="unrepresented")), "must have no refs"),
        (_member(mapping=_mapping(refs=[])), "requires at least one ref"),
        (
            _member(mapping=_mapping(relation="unknown", refs=[], review="reviewed")),
            "unknown requires review candidate",
        ),
        (_member(mapping=_mapping(reviewer=None)), "requires reviewer and reviewed_on"),
        (_member(mapping=_mapping(reviewed_on=None)), "requires reviewer and reviewed_on"),
        (_member(decision="merge", decision_note_ja="x"), "merge requires merged_into"),
        (
            _member(decision="merge", merged_into="TOPIC_GD", decision_note_ja="x"),
            "cannot merge into itself",
        ),
        (
            _member(decision="merge", merged_into="TOPIC_MISSING", decision_note_ja="x"),
            "does not exist",
        ),
        (_member(merged_into="TOPIC_OTHER"), "only allowed when decision is merge"),
        (_member(decision="hold"), "requires decision_note_ja"),
        (_member(decision="exclude", decision_note_ja="  "), "requires decision_note_ja"),
        (_member(source_refs=["E99"]), "unknown source_ref"),
    ],
)
def test_member_integrity_failures(member: dict[str, Any], needle: str) -> None:
    with pytest.raises(ValueError, match=needle):
        _check(_scope(member))


def test_duplicate_scope_id_and_source_ref() -> None:
    payload = _scope(
        _member(), _member(mapping=_mapping(refs=[{"type": "method", "id": "M_ADAM"}]))
    )
    payload["sources"].append(copy.deepcopy(payload["sources"][0]))
    with pytest.raises(ValueError) as error:
        _check(payload)
    assert "duplicate scope_id" in str(error.value)
    assert "duplicate source_ref" in str(error.value)


def test_merge_target_must_be_included_no_chains() -> None:
    held = _member("TOPIC_B", decision="hold", decision_note_ja="保留。")
    merged = _member("TOPIC_C", decision="merge", merged_into="TOPIC_B", decision_note_ja="統合。")
    with pytest.raises(ValueError, match="no merge chains"):
        _check(_scope(_member(), held, merged))


def test_double_counting_requires_merge() -> None:
    other = _member("TOPIC_GD_ALIAS", mapping=_mapping(relation="alias_of"))
    with pytest.raises(ValueError, match="double counting.*merge one into the other"):
        _check(_scope(_member(), other))


def test_double_counting_ignores_non_include_and_other_relations() -> None:
    variant = _member("TOPIC_V", entity_kind="variant", mapping=_mapping(relation="variant_of"))
    held = _member(
        "TOPIC_H", decision="hold", decision_note_ja="保留。", mapping=_mapping(relation="alias_of")
    )
    _check(_scope(_member(), variant, held))


def test_double_counting_is_per_unit() -> None:
    structure = _member(
        "STRUCTURE_GD",
        unit="problem_structure",
        entity_kind="problem_archetype",
    )
    _check(_scope(_member(), structure))


def test_scope_id_must_not_shadow_a_canonical_id() -> None:
    known = {**KNOWN, "problem_definition": {"STRUCTURE_LP", "TOPIC_GD"}}
    with pytest.raises(ValueError, match="TOPIC_GD: scope_id collides"):
        validate_editorial_scope(EditorialScope.model_validate(_scope()), known_refs=known)


def test_problem_definition_refs_are_checked() -> None:
    known = {**KNOWN, "problem_definition": {"PROBLEM_LP"}}
    ok = _mapping(refs=[{"type": "problem_definition", "id": "PROBLEM_LP"}])
    validate_editorial_scope(
        EditorialScope.model_validate(_scope(_member(mapping=ok))), known_refs=known
    )
    bad = _mapping(refs=[{"type": "problem_definition", "id": "PROBLEM_NOPE"}])
    with pytest.raises(ValueError, match="unknown problem_definition ref PROBLEM_NOPE"):
        validate_editorial_scope(
            EditorialScope.model_validate(_scope(_member(mapping=bad))), known_refs=known
        )


def test_approval_requires_approver_and_date() -> None:
    with pytest.raises(ValueError, match="approved_by.*approved_on|approved_on"):
        _check(_scope(status="approved"))
    with pytest.raises(ValueError, match="approved_by"):
        _check(_scope(status="approved", approved_by="claude", approved_on="2026-10-10"))
    _check(_scope(status="approved", approved_by="owner", approved_on="2026-10-10"))


def test_all_problems_are_collected() -> None:
    bad = _member("TOPIC_gd", source_refs=["E99"], decision="hold")
    with pytest.raises(ValueError) as error:
        _check(_scope(bad))
    message = str(error.value)
    assert "scope_id must match" in message
    assert "unknown source_ref" in message
    assert "requires decision_note_ja" in message


def test_summary_has_counts_and_no_ratios() -> None:
    unknown = _member(
        "TOPIC_U",
        mapping=_mapping(relation="unknown", refs=[], review="candidate", reviewer=None),
    )
    gone = _member("TOPIC_N", mapping=_mapping(relation="unrepresented", refs=[]))
    problem = _member(
        "STRUCTURE_LP", unit="problem_structure", entity_kind="problem_archetype", tier="applied"
    )
    problem["mapping"] = _mapping(refs=[{"type": "problem", "id": "PA001"}])
    scope = EditorialScope.model_validate(_scope(_member(), unknown, gone, problem))
    summary = scope_summary(scope)
    topic = summary["units"]["knowledge_topic"]
    assert topic["members"] == 3
    assert topic["decision"] == {"include": 3}
    assert topic["included"]["relation"] == {"same_entity": 1, "unknown": 1, "unrepresented": 1}
    assert topic["included"]["review"] == {"candidate": 1, "reviewed": 2}
    assert (topic["unreconciled"], topic["unrepresented"]) == (1, 1)
    assert summary["units"]["problem_structure"]["included"]["tier"] == {"applied": 1}
    text = json.dumps(summary)
    assert "ratio" not in text and "percent" not in text and "%" not in text


def test_pending_members() -> None:
    unknown = _member(
        "TOPIC_U",
        mapping=_mapping(relation="unknown", refs=[], review="candidate", reviewer=None),
    )
    held = _member("TOPIC_H", decision="hold", decision_note_ja="保留。", tier="frontier")
    held["mapping"] = _mapping(refs=[{"type": "method", "id": "M_ADAM"}])
    scope = EditorialScope.model_validate(_scope(_member(), unknown, held))
    assert [m.scope_id for m in pending_members(scope)] == ["TOPIC_U", "TOPIC_H"]


def test_unknown_fields_are_rejected() -> None:
    payload = _scope()
    payload["members"][0]["coverage_percent"] = 50
    with pytest.raises(ValueError):
        EditorialScope.model_validate(payload)


def test_real_seed_validates() -> None:
    path = ROOT / SCOPE_SEED_PATH
    if not path.exists():
        pytest.skip("editorial scope seed is not authored yet")
    from optimization_compass.content_models import load_content
    from optimization_compass.db import KnowledgeRepository

    repository = KnowledgeRepository(ROOT / "src/optimization_compass/resources/knowledge.sqlite")
    pages = [p for p in load_content(ROOT / "content") if p.status == "published"]
    validate_editorial_scope(
        load_editorial_scope(path), known_refs=known_ref_ids(repository, pages)
    )


def test_known_ref_ids_reads_existing_rows() -> None:
    from optimization_compass.db import KnowledgeRepository

    repository = KnowledgeRepository(ROOT / "src/optimization_compass/resources/knowledge.sqlite")
    known = known_ref_ids(repository, [])
    assert set(known) == {
        "method",
        "problem",
        "problem_definition",
        "feature",
        "glossary",
        "term",
        "content",
    }
    assert known["method"] and known["problem"]
