from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from optimization_compass.content_models import load_content
from optimization_compass.content_quality import formulation_skeleton_gaps, is_formulation_article
from optimization_compass.db import KnowledgeRepository
from optimization_compass.formulation_atlas import (
    FormulationAtlasSeed,
    LearningPathSeed,
    build_formulation_atlas_index,
    build_learning_path_index,
    load_formulation_atlas_seed,
    load_learning_path_seed,
    validate_formulation_atlas,
    validate_learning_paths,
)

ROOT = Path(__file__).parents[1]
ATLAS_SEED = ROOT / "data/seeds/formulation_atlas.json"
PATH_SEED = ROOT / "data/seeds/learning_paths.json"


@pytest.fixture(scope="module")
def repository() -> KnowledgeRepository:
    return KnowledgeRepository(ROOT / "src/optimization_compass/resources/knowledge.sqlite")


@pytest.fixture(scope="module")
def archetype_ids(repository: KnowledgeRepository) -> set[str]:
    return {
        str(row["problem_id"])
        for row in repository.fetch_all("SELECT problem_id FROM problem_archetypes")
    }


@pytest.fixture(scope="module")
def pages():  # type: ignore[no-untyped-def]
    return [page for page in load_content(ROOT / "content") if page.status == "published"]


def _raw_atlas() -> dict[str, object]:
    return json.loads(ATLAS_SEED.read_text(encoding="utf-8"))


def test_seed_covers_every_archetype_once(archetype_ids: set[str], pages) -> None:  # type: ignore[no-untyped-def]
    seed = load_formulation_atlas_seed(ATLAS_SEED)
    validate_formulation_atlas(seed, archetype_ids=archetype_ids, content_pages=pages)
    assert {entry.problem_id for entry in seed.formulations} == archetype_ids


def test_missing_archetype_is_rejected(archetype_ids: set[str]) -> None:
    raw = _raw_atlas()
    raw["formulations"] = [
        item
        for item in raw["formulations"]
        if item["problem_id"] != "PA017"  # type: ignore[attr-defined]
    ]
    seed = FormulationAtlasSeed.model_validate(raw)
    with pytest.raises(ValueError, match="missing=\\['PA017'\\]"):
        validate_formulation_atlas(seed, archetype_ids=archetype_ids)


def test_special_case_cycle_is_rejected(archetype_ids: set[str]) -> None:
    raw = _raw_atlas()
    raw["relations"] = [
        *raw["relations"],  # type: ignore[misc]
        {"from": "PA022", "to": "PA017", "type": "special_case_of", "note_ja": "循環"},
    ]
    seed = FormulationAtlasSeed.model_validate(raw)
    with pytest.raises(ValueError, match="cycle"):
        validate_formulation_atlas(seed, archetype_ids=archetype_ids)


def test_relation_to_unknown_archetype_is_rejected(archetype_ids: set[str]) -> None:
    raw = _raw_atlas()
    raw["relations"] = [{"from": "PA017", "to": "PA999", "type": "contrasts_with", "note_ja": "x"}]
    seed = FormulationAtlasSeed.model_validate(raw)
    with pytest.raises(ValueError, match="unknown problem archetype: PA999"):
        validate_formulation_atlas(seed, archetype_ids=archetype_ids)


def test_two_articles_for_one_archetype_are_rejected(archetype_ids: set[str], pages) -> None:  # type: ignore[no-untyped-def]
    article = next(page for page in pages if page.canonical_entity_id == "PA017")
    duplicate = replace(article, content_id="concept.linear-program-copy")
    with pytest.raises(ValueError, match="more than one article"):
        validate_formulation_atlas(
            load_formulation_atlas_seed(ATLAS_SEED),
            archetype_ids=archetype_ids,
            content_pages=[*pages, duplicate],
        )


def test_index_merges_database_seed_and_articles(repository: KnowledgeRepository, pages) -> None:  # type: ignore[no-untyped-def]
    index = build_formulation_atlas_index(
        repository,
        load_formulation_atlas_seed(ATLAS_SEED),
        dataset_version="test",
        content_pages=pages,
    )
    by_id = {item["problem_id"]: item for item in index["formulations"]}
    lp = by_id["PA017"]
    assert lp["name_ja"] == "線形計画"
    assert lp["content_id"] == "concept.linear-program"
    assert lp["maturity"] == "article_with_figure"
    assert "<math" in lp["standard_form_html"]
    assert lp["methods"][0]["fit_level"] == "default_choice"
    assert any(method["role"] == "avoid" for method in lp["methods"])
    assert by_id["PA034"]["maturity"] == "article"
    assert by_id["PA054"]["maturity"] == "skeleton"
    assert index["summary"]["formulations"] == len(by_id)
    assert all(family["problem_ids"] for family in index["families"])


def test_paths_resolve_routes_and_stubs(pages, archetype_ids: set[str]) -> None:  # type: ignore[no-untyped-def]
    names = dict.fromkeys(archetype_ids, "x")
    articles = {
        page.canonical_entity_id: page.content_id
        for page in pages
        if page.canonical_entity_type == "problem" and page.canonical_entity_id in archetype_ids
    }
    index = build_learning_path_index(
        load_learning_path_seed(PATH_SEED),
        dataset_version="test",
        archetypes=names,
        content_pages=pages,
        formulation_articles=articles,
    )
    steps = {step["target_id"]: step for path in index["paths"] for step in path["steps"]}
    assert steps["PA017"]["route"] == "/formulations/PA017"
    assert steps["PA017"]["has_article"] is True
    assert steps["PA034"]["has_article"] is True
    assert steps["primal-simplex"]["route"] == "/methods/M_SIMPLEX"
    assert steps["concept.convexity"]["route"] == "/learn/concept.convexity"

    stub_index = build_learning_path_index(
        load_learning_path_seed(PATH_SEED),
        dataset_version="test",
        archetypes=names,
        content_pages=[page for page in pages if page.canonical_entity_id != "PA034"],
        formulation_articles={key: value for key, value in articles.items() if key != "PA034"},
    )
    stub = next(
        step
        for path in stub_index["paths"]
        for step in path["steps"]
        if step["target_id"] == "PA034"
    )
    assert stub["has_article"] is False
    assert stub["route"] == "/formulations/PA034"


def test_step_before_its_prerequisite_is_rejected(pages, archetype_ids: set[str]) -> None:  # type: ignore[no-untyped-def]
    seed = LearningPathSeed.model_validate(
        {
            "contract_version": "1.0.0",
            "paths": [
                {
                    "path_id": "wrong-order",
                    "title_ja": "t",
                    "summary_ja": "s",
                    "goal_ja": "g",
                    "audience_ja": "a",
                    "steps": [
                        {
                            "target_type": "content",
                            "target_id": "primal-simplex",
                            "question_ja": "先に手法を読む。",
                        },
                        {
                            "target_type": "content",
                            "target_id": "concept.convexity",
                            "question_ja": "後から前提を読む。",
                        },
                    ],
                }
            ],
        }
    )
    with pytest.raises(ValueError, match="before its prerequisite concept.convexity"):
        validate_learning_paths(seed, archetype_ids=archetype_ids, content_pages=pages)


def test_formulation_articles_follow_the_skeleton(pages) -> None:  # type: ignore[no-untyped-def]
    articles = [page for page in pages if is_formulation_article(page)]
    assert len(articles) >= 5
    assert all(formulation_skeleton_gaps(page) == () for page in articles)

    lsq = next(page for page in articles if page.canonical_entity_id == "PA005")
    from optimization_compass.content_skeletons import skeleton_gaps

    assert skeleton_gaps(lsq) == ()
    headings = list(lsq.toc)
    limits = next(i for i, h in enumerate(headings) if h.label == "つまずきやすい点")
    related = next(i for i, h in enumerate(headings) if h.label == "困りごとから関連する問題へ")
    headings[limits], headings[related] = headings[related], headings[limits]
    assert skeleton_gaps(replace(lsq, toc=tuple(headings))) == ("order",)

    lp = next(page for page in articles if page.canonical_entity_id == "PA017")
    reordered = replace(lp, toc=(lp.toc[1], lp.toc[0], *lp.toc[2:]))
    assert formulation_skeleton_gaps(reordered) == ("order",)
    trimmed = replace(lp, toc=tuple(h for h in lp.toc if h.label != "小さな例"))
    assert formulation_skeleton_gaps(trimmed) == ("missing:小さな例",)


def test_articles_outside_the_pending_list_follow_their_skeleton(pages) -> None:  # type: ignore[no-untyped-def]
    from optimization_compass.content_skeletons import load_pending, require_content_skeletons

    pending = load_pending(ROOT)
    assert require_content_skeletons(pages, pending) == ()  # the pending list is pruned
    method = next(page for page in pages if page.content_id == "primal-simplex")
    broken = replace(method, toc=tuple(h for h in method.toc if h.label != "小さな例"))
    with pytest.raises(ValueError, match="primal-simplex \\[method\\] \\(missing:小さな例\\)"):
        require_content_skeletons([broken], frozenset())
    # A pending article may still break the skeleton, and becomes prunable once it conforms.
    assert require_content_skeletons([broken], frozenset({"primal-simplex"})) == ()
    assert require_content_skeletons([method], frozenset({"primal-simplex"})) == ("primal-simplex",)
    with pytest.raises(ValueError, match="unknown articles: no-such-article"):
        require_content_skeletons(pages, frozenset({"no-such-article"}))


def test_method_articles_may_close_with_a_trouble_route(pages) -> None:  # type: ignore[no-untyped-def]
    from optimization_compass.content_skeletons import METHOD_TROUBLE_ROUTE, skeleton_gaps

    method = next(page for page in pages if page.content_id == "adam")
    routed = replace(
        method,
        toc=tuple(
            replace(h, label=METHOD_TROUBLE_ROUTE) if h.label == "次に読む" else h
            for h in method.toc
        ),
    )
    assert skeleton_gaps(routed) == ()
    misplaced = replace(routed, toc=(*routed.toc[-1:], *routed.toc[:-1]))
    assert skeleton_gaps(misplaced) == ("order",)
