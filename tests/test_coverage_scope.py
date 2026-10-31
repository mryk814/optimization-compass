from __future__ import annotations

from pathlib import Path
from typing import Any

from optimization_compass.article_quality import Article, ArticleReport, CheckResult, State
from optimization_compass.content_models import ContentPage
from optimization_compass.coverage import (
    CoverageReport,
    build_scope_coverage,
    diff_coverage,
)
from optimization_compass.editorial_scope import EditorialScope

ROOT = Path(__file__).parents[1]


def member(
    sid: str,
    relation: str = "same_entity",
    refs: list[dict[str, str]] | None = None,
    *,
    unit: str = "knowledge_topic",
    decision: str = "include",
    review: str = "reviewed",
    merged_into: str | None = None,
) -> dict[str, Any]:
    return {
        "scope_id": sid,
        "unit": unit,
        "title_ja": sid,
        "entity_kind": "algorithm" if unit == "knowledge_topic" else "problem_archetype",
        "tier": "core",
        "decision": decision,
        "merged_into": merged_into,
        "decision_note_ja": "理由" if decision != "include" else None,
        "mapping": {
            "relation": relation,
            "refs": refs or [],
            "review": review,
            "reviewer": "claude" if review == "reviewed" else None,
            "reviewed_on": "2026-10-10" if review == "reviewed" else None,
        },
    }


def scope_of(*members: dict[str, Any]) -> EditorialScope:
    return EditorialScope.model_validate(
        {
            "contract_version": "1.0.0",
            "scope_version": "test-v1",
            "status": "proposed",
            "based_on": "test",
            "members": list(members),
        }
    )


def report(
    content_id: str,
    *states: State,
    method_id: str | None = None,
    entity_id: str = "X",
    visual: str = "none",
) -> ArticleReport:
    page = ContentPage(
        content_id=content_id,
        kind="method" if method_id else "concept",
        method_id=method_id,
        canonical_entity_type="method",
        canonical_entity_id=entity_id,
        title_ja="t",
        title_en="t",
        summary="s",
        source_ids=("S",),
        prerequisites=(),
        related_ids=(),
        visualization_ids=(),
        comparison_ids=(),
        aliases=(),
        visualization_aliases=(),
        comparison_aliases=(),
        status="published",
        last_reviewed="2026-10-10",
        body="",
        html="",
        toc=(),
    )
    article = Article(page, Path(f"content/{content_id}.md"), "method", False)
    results = tuple(CheckResult(f"c{i}", s) for i, s in enumerate(states))
    return ArticleReport(article, results, None, 0, visual)


M = {"type": "method", "id": "M_A"}
P = {"type": "problem", "id": "PA1"}


def test_counts_per_axis_and_state() -> None:
    scope = scope_of(
        member("TOPIC_A", refs=[M, {"type": "content", "id": "method.a"}]),
        member("TOPIC_B", "unknown", review="candidate"),
        member("TOPIC_C", "unrepresented"),
        member("TOPIC_D", refs=[{"type": "method", "id": "M_D"}], review="candidate"),
        member("TOPIC_E", "concept_content", [{"type": "content", "id": "concept.e"}]),
        member("TOPIC_F", decision="exclude"),
        member("TOPIC_G", decision="hold"),
        member("STRUCTURE_P", refs=[P], unit="problem_structure"),
    )
    reports = [
        report("method.a", "pass", method_id="M_A", entity_id="M_A", visual="explorable"),
        report("concept.e", "pass", "stale", entity_id="PA9"),
    ]
    cov = build_scope_coverage(scope, reports)
    topic = cov.units["knowledge_topic"]
    assert (topic.denominator, topic.excluded, topic.held, topic.merged) == (5, 1, 1, 0)
    identity = topic.axes["identity"]
    assert (identity.eligible, identity.complete) == (5, 2)
    assert identity.states == {"candidate": 1, "unrepresented": 1, "unknown": 1}
    claims = topic.axes["claims"]
    assert (claims.eligible, claims.complete) == (5, 2)
    assert claims.states == {"no_canonical_row": 3}
    lesson = topic.axes["lesson"]
    assert lesson.complete == 1
    assert lesson.states == {"stale": 1, "in_progress": 0, "no_article": 3}
    assert topic.axes["experience"].eligible == 0
    assert topic.axes["experience"].states == {"undecided": 5}
    assert topic.axes["experience"].info == {"has_interactive": 1}
    assert topic.axes["transfer"].states == {"undecided": 5}
    assert cov.units["problem_structure"].denominator == 1


def test_alias_pair_merged_is_counted_once() -> None:
    scope = scope_of(
        member("TOPIC_A", refs=[M]),
        member("TOPIC_A2", "alias_of", [M], decision="merge", merged_into="TOPIC_A"),
    )
    topic = build_scope_coverage(scope, []).units["knowledge_topic"]
    assert topic.denominator == 1
    assert topic.merged == 1
    assert topic.axes["identity"].eligible == 1
    assert topic.axes["identity"].complete == 1


def test_lesson_state_priority() -> None:
    scope = scope_of(
        member("TOPIC_A", refs=[M]),
        member("TOPIC_B", refs=[{"type": "method", "id": "M_B"}]),
        member("TOPIC_C", refs=[{"type": "method", "id": "M_C"}]),
    )
    reports = [
        report("a1", "stale", method_id="M_A", entity_id="M_A"),
        report("a2", "pass", method_id="M_A", entity_id="M_A"),
        report("b1", "unreviewed", method_id="M_B", entity_id="M_B"),
        report("c1", "new", method_id="M_C", entity_id="M_C"),
    ]
    lesson = build_scope_coverage(scope, reports).units["knowledge_topic"].axes["lesson"]
    assert lesson.complete == 1
    assert lesson.states == {"stale": 1, "in_progress": 1, "no_article": 0}


def test_diff_reports_denominator_and_completion_separately() -> None:
    before = build_scope_coverage(scope_of(member("TOPIC_A", refs=[M])), [])
    after = build_scope_coverage(
        scope_of(member("TOPIC_A", refs=[M]), member("TOPIC_B", "unknown", review="candidate")),
        [report("a", "pass", method_id="M_A", entity_id="M_A")],
    )
    base = CoverageReport.model_validate_json(
        (ROOT / "site/public/data/coverage.json").read_text(encoding="utf-8")
    )
    delta = diff_coverage(
        base.model_copy(update={"scope": before}), base.model_copy(update={"scope": after})
    )
    assert delta.scope_delta is not None
    topic = delta.scope_delta["knowledge_topic"]
    assert (topic["identity"].denominator_delta, topic["identity"].complete_delta) == (1, 0)
    assert (topic["lesson"].denominator_delta, topic["lesson"].complete_delta) == (1, 1)
    no_scope = diff_coverage(base.model_copy(update={"scope": None}), base)
    assert no_scope.scope_delta is None


def test_absent_seed_means_no_scope(tmp_path: Path) -> None:
    from optimization_compass.coverage import _scope_from_repository

    assert _scope_from_repository(tmp_path) is None
