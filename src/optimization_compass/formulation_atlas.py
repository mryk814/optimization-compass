"""Formulation atlas and learning paths: the learner-facing spine of the Atlas (ADR 0017).

Two authored seeds feed this module:

- ``data/seeds/formulation_atlas.json`` gives every canonical problem archetype a family, a
  standard form in LaTeX, a plain-Japanese reading, recognition cues, and typed pedagogical
  relations to other archetypes. It must cover every archetype in the released database, so
  the dictionary is complete from the start even where no article exists yet.
- ``data/seeds/learning_paths.json`` orders existing formulations and content pages into
  step-by-step paths, each step carrying the question it answers.

The released database stays the authority for archetype identity, names, descriptors, method
fit, and alternatives. The seeds add only the teaching structure; articles stay in
``content/**/*.md`` as concept pages whose canonical entity is the archetype.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any, Literal

from latex2mathml.converter import convert as latex_to_mathml
from pydantic import BaseModel, ConfigDict, Field, field_validator

from optimization_compass.content_models import ContentPage
from optimization_compass.db import KnowledgeRepository

CONTRACT_VERSION = "1.0.0"
LEARNING_PATH_CONTRACT_VERSION = "1.0.0"

RelationType = Literal["special_case_of", "relaxes_to", "reformulates_to", "contrasts_with"]
Lens = Literal["form", "oracle", "application"]
Maturity = Literal["skeleton", "article", "article_with_figure"]

# Directed relations whose cycles would make the teaching order meaningless.
_ACYCLIC_RELATIONS: tuple[RelationType, ...] = ("special_case_of", "relaxes_to")

_FIT_ORDER = (
    "default_choice",
    "strongly_recommended",
    "recommended",
    "viable",
    "conditional",
    "specialized",
    "last_resort",
    "generally_unsuitable",
    "incompatible",
    "unknown",
)
_AVOID_FIT_LEVELS = frozenset({"generally_unsuitable", "incompatible"})

# Descriptor labels are display text for codes that the released database already stores.
_DESCRIPTOR_FIELDS: tuple[tuple[str, str], ...] = (
    ("primary_variable_type", "決めるもの"),
    ("objective_structure", "目的の形"),
    ("constraint_structure", "制約の形"),
    ("convexity", "凸性"),
    ("solution_requirement", "得られる保証"),
)
_DESCRIPTOR_LABELS: dict[str, str] = {
    "continuous": "連続値",
    "matrix": "行列",
    "mixed": "連続と整数の混在",
    "psd_matrix": "半正定値行列",
    "binary": "0-1",
    "graph": "グラフ上の選択",
    "manifold": "多様体上の点",
    "trajectory": "時間軌道",
    "shape": "形状",
    "general_nonlinear": "一般の非線形",
    "equation_residual": "方程式の残差",
    "quadratic": "二次",
    "sum_of_squares": "二乗和",
    "composite": "滑らか＋非滑らかの和",
    "simulation": "simulationの出力",
    "linear": "線形",
    "discrete": "離散的な評価",
    "multiobjective": "複数の目的",
    "unconstrained": "制約なし",
    "bounds": "上下限",
    "implicit": "暗黙（評価の成否）",
    "conic": "錐制約",
    "semidefinite": "半正定値制約",
    "combinatorial": "組合せ構造",
    "logical": "論理制約",
    "dynamics": "運動方程式",
    "nonlinear": "非線形",
    "geometry;mesh;state;bounds": "形状・mesh・状態・上下限",
    "unknown": "不明",
    "convex": "凸",
    "nonconvex": "非凸",
    "global_proof": "大域最適の証明",
    "local_stationary": "局所停留点",
    "convex_global": "凸性による大域解",
    "global_candidate": "大域解の候補",
    "feasible_only": "実行可能解",
    "optimality_gap": "最適性gapつきの解",
    "pareto_set": "Pareto集合",
}


_FIELD_DESCRIPTOR_LABELS: dict[tuple[str, str], str] = {
    ("constraint_structure", "mixed"): "等式・不等式の混在",
    ("constraint_structure", "linear"): "線形",
    ("objective_structure", "discrete"): "離散的な評価",
}


class _Frozen(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class FormulationFamily(_Frozen):
    family_id: str = Field(pattern=r"^[a-z][a-z_]*$")
    lens: Lens
    title_ja: str = Field(min_length=1)
    summary_ja: str = Field(min_length=1)
    problem_ids: tuple[str, ...] = Field(min_length=1)


class FormulationEntry(_Frozen):
    problem_id: str = Field(pattern=r"^PA\d{3}$")
    standard_form: str = Field(min_length=1)
    reading_ja: str = Field(min_length=1)
    cues_ja: tuple[str, ...] = Field(min_length=1)

    @field_validator("reading_ja")
    @classmethod
    def _sentence(cls, value: str) -> str:
        if not value.endswith("。"):
            raise ValueError("reading_ja must be a complete Japanese sentence ending with 。")
        return value


class FormulationRelation(_Frozen):
    from_id: str = Field(alias="from", pattern=r"^PA\d{3}$")
    to_id: str = Field(alias="to", pattern=r"^PA\d{3}$")
    type: RelationType
    note_ja: str = Field(min_length=1)

    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True)


class FormulationAtlasSeed(_Frozen):
    contract_version: Literal["1.0.0"]
    families: tuple[FormulationFamily, ...]
    formulations: tuple[FormulationEntry, ...]
    relations: tuple[FormulationRelation, ...]


class LearningPathStep(_Frozen):
    target_type: Literal["formulation", "content"]
    target_id: str = Field(min_length=1)
    question_ja: str = Field(min_length=1)

    @field_validator("question_ja")
    @classmethod
    def _sentence(cls, value: str) -> str:
        if not value.endswith("。"):
            raise ValueError("question_ja must end with 。")
        return value


class LearningPath(_Frozen):
    path_id: str = Field(pattern=r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
    title_ja: str = Field(min_length=1)
    summary_ja: str = Field(min_length=1)
    goal_ja: str = Field(min_length=1)
    audience_ja: str = Field(min_length=1)
    steps: tuple[LearningPathStep, ...] = Field(min_length=2)


class LearningPathSeed(_Frozen):
    contract_version: Literal["1.0.0"]
    paths: tuple[LearningPath, ...]


def load_formulation_atlas_seed(path: Path) -> FormulationAtlasSeed:
    return FormulationAtlasSeed.model_validate(json.loads(path.read_text(encoding="utf-8")))


def load_learning_path_seed(path: Path) -> LearningPathSeed:
    return LearningPathSeed.model_validate(json.loads(path.read_text(encoding="utf-8")))


def validate_formulation_atlas(
    seed: FormulationAtlasSeed,
    *,
    archetype_ids: Iterable[str],
    content_pages: Iterable[ContentPage] = (),
) -> None:
    """Reject a seed that would make the dictionary incomplete or the relation graph misleading."""

    known = set(archetype_ids)
    entries = [entry.problem_id for entry in seed.formulations]
    _require_unique(entries, "formulation problem_id")
    if set(entries) != known:
        missing = sorted(known - set(entries))
        unknown = sorted(set(entries) - known)
        raise ValueError(
            "formulation atlas must cover every problem archetype exactly once "
            f"(missing={missing or '-'}, unknown={unknown or '-'})"
        )
    _require_unique([family.family_id for family in seed.families], "family_id")
    family_members = [problem_id for family in seed.families for problem_id in family.problem_ids]
    _require_unique(family_members, "family member")
    if set(family_members) != known:
        raise ValueError(
            "every problem archetype must belong to exactly one family "
            f"(unassigned={sorted(known - set(family_members)) or '-'})"
        )

    seen: set[tuple[str, str, str]] = set()
    for relation in seed.relations:
        for endpoint in (relation.from_id, relation.to_id):
            if endpoint not in known:
                raise ValueError(f"relation references unknown problem archetype: {endpoint}")
        if relation.from_id == relation.to_id:
            raise ValueError(f"relation must not point to itself: {relation.from_id}")
        key = (relation.from_id, relation.to_id, relation.type)
        undirected = (relation.to_id, relation.from_id, relation.type)
        if key in seen or (relation.type == "contrasts_with" and undirected in seen):
            raise ValueError(
                f"duplicate relation: {relation.from_id} {relation.type} {relation.to_id}"
            )
        seen.add(key)
    for relation_type in _ACYCLIC_RELATIONS:
        _require_acyclic(
            [(r.from_id, r.to_id) for r in seed.relations if r.type == relation_type],
            relation_type,
        )

    articles: dict[str, str] = {}
    for page in content_pages:
        # Problem definitions (PROBLEM_*) share the entity type but are not archetypes.
        if (
            page.status != "published"
            or page.canonical_entity_type != "problem"
            or page.canonical_entity_id not in known
        ):
            continue
        if page.canonical_entity_id in articles:
            raise ValueError(
                f"problem archetype {page.canonical_entity_id} has more than one article "
                f"({articles[page.canonical_entity_id]}, {page.content_id})"
            )
        articles[page.canonical_entity_id] = page.content_id


def validate_learning_paths(
    seed: LearningPathSeed,
    *,
    archetype_ids: Iterable[str],
    content_pages: Iterable[ContentPage],
) -> None:
    """Reject paths that point nowhere or ask for a prerequisite after the step that needs it."""

    known_formulations = set(archetype_ids)
    published = {page.content_id: page for page in content_pages if page.status == "published"}
    articles = {
        page.canonical_entity_id: page
        for page in published.values()
        if page.canonical_entity_type == "problem"
        and page.canonical_entity_id in known_formulations
    }
    _require_unique([path.path_id for path in seed.paths], "path_id")
    for path in seed.paths:
        keys = [(step.target_type, step.target_id) for step in path.steps]
        _require_unique([f"{kind}:{target}" for kind, target in keys], f"{path.path_id} step")
        # A step is reachable under its own ID and under the content ID of its article.
        position: dict[str, int] = {}
        step_pages: dict[int, ContentPage] = {}
        for index, step in enumerate(path.steps):
            if step.target_type == "formulation" and step.target_id not in known_formulations:
                raise ValueError(f"{path.path_id} references unknown formulation {step.target_id}")
            if step.target_type == "content" and step.target_id not in published:
                raise ValueError(f"{path.path_id} references unpublished content {step.target_id}")
            page = (
                published[step.target_id]
                if step.target_type == "content"
                else articles.get(step.target_id)
            )
            position[step.target_id] = index
            if page is not None:
                position[page.content_id] = index
                step_pages[index] = page
        for index, page in step_pages.items():
            step = path.steps[index]
            for prerequisite in page.prerequisites:
                if position.get(prerequisite, -1) > index:
                    raise ValueError(
                        f"{path.path_id}: {step.target_id} appears before its prerequisite "
                        f"{prerequisite}"
                    )


def build_formulation_atlas_index(
    repository: KnowledgeRepository,
    seed: FormulationAtlasSeed,
    *,
    dataset_version: str,
    content_pages: Iterable[ContentPage],
    gallery_cases: Iterable[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    archetypes = {
        str(row["problem_id"]): row
        for row in repository.fetch_all("SELECT * FROM problem_archetypes ORDER BY problem_id")
    }
    validate_formulation_atlas(seed, archetype_ids=archetypes, content_pages=content_pages)
    methods = {
        str(row["method_id"]): row
        for row in repository.fetch_all("SELECT method_id, name_ja, name_en FROM methods")
    }
    alternatives = {
        str(row["alternative_id"]): str(row["name_ja"] or row["alternative_id"])
        for row in repository.fetch_all(
            "SELECT alternative_id, name_ja FROM alternative_solution_checks"
        )
    }
    fits: dict[str, list[dict[str, Any]]] = {}
    for row in repository.fetch_all(
        "SELECT problem_or_feature_id, method_id, fit_level, beginner_priority "
        "FROM problem_method_fit ORDER BY fit_id"
    ):
        fits.setdefault(str(row["problem_or_feature_id"]), []).append(row)
    fit_labels = {
        str(row["value_code"]): str(row["label_ja"])
        for row in repository.fetch_all(
            "SELECT value_code, label_ja FROM controlled_vocab WHERE vocab_name = 'fit_level'"
        )
    }
    pages = [page for page in content_pages if page.status == "published"]
    article_by_problem = {
        page.canonical_entity_id: page
        for page in pages
        if page.canonical_entity_type == "problem" and page.canonical_entity_id in archetypes
    }
    cases_by_problem: dict[str, list[dict[str, str]]] = {}
    for case in gallery_cases:
        if case.get("status") != "published":
            continue
        problem_id = case.get("problem_archetype_id")
        if isinstance(problem_id, str):
            cases_by_problem.setdefault(problem_id, []).append(
                {"case_id": str(case["case_id"]), "title_ja": str(case.get("title_ja") or "")}
            )
    family_of = {
        problem_id: family for family in seed.families for problem_id in family.problem_ids
    }

    formulations: list[dict[str, Any]] = []
    for entry in sorted(seed.formulations, key=lambda item: item.problem_id):
        row = archetypes[entry.problem_id]
        family = family_of[entry.problem_id]
        page = article_by_problem.get(entry.problem_id)
        method_rows = sorted(
            fits.get(entry.problem_id, []),
            key=lambda item: (_fit_rank(item["fit_level"]), str(item["method_id"])),
        )
        formulations.append(
            {
                "problem_id": entry.problem_id,
                "name_ja": str(row["name_ja"] or entry.problem_id),
                "name_en": str(row["name_en"] or entry.problem_id),
                "family_id": family.family_id,
                "lens": family.lens,
                "standard_form": entry.standard_form,
                "standard_form_html": _block_math(entry.standard_form),
                "reading_ja": entry.reading_ja,
                "cues_ja": list(entry.cues_ja),
                "descriptors": [
                    {
                        "field": field,
                        "label_ja": label,
                        "value": str(row[field] or "unknown"),
                        "value_label_ja": _descriptor_label(field, str(row[field] or "unknown")),
                    }
                    for field, label in _DESCRIPTOR_FIELDS
                ],
                "alternatives": [
                    {"alternative_id": alternative_id, "name_ja": alternatives[alternative_id]}
                    for alternative_id in _split(row["alternative_check_ids"])
                    if alternative_id in alternatives
                ],
                "methods": [
                    {
                        "method_id": str(item["method_id"]),
                        "name_ja": str(
                            methods[str(item["method_id"])]["name_ja"] or item["method_id"]
                        ),
                        "fit_level": str(item["fit_level"] or "unknown"),
                        "fit_label_ja": fit_labels.get(str(item["fit_level"] or "unknown"), "不明"),
                        "role": (
                            "avoid" if item["fit_level"] in _AVOID_FIT_LEVELS else "candidate"
                        ),
                    }
                    for item in method_rows
                    if str(item["method_id"]) in methods
                ],
                "content_id": page.content_id if page else None,
                "maturity": _maturity(page),
                "cases": sorted(
                    cases_by_problem.get(entry.problem_id, []), key=lambda item: item["case_id"]
                ),
                "source_ids": sorted(
                    set(_split(row["source_ids"])) | set(page.source_ids if page else ())
                ),
            }
        )

    relations = [
        {
            "from": relation.from_id,
            "to": relation.to_id,
            "type": relation.type,
            "note_ja": relation.note_ja,
        }
        for relation in sorted(
            seed.relations, key=lambda item: (item.type, item.from_id, item.to_id)
        )
    ]
    return {
        "contract_version": CONTRACT_VERSION,
        "dataset_version": dataset_version,
        "families": [family.model_dump(mode="json") for family in seed.families],
        "formulations": formulations,
        "relations": relations,
        "summary": {
            "formulations": len(formulations),
            "with_article": sum(1 for item in formulations if item["maturity"] != "skeleton"),
            "relations": len(relations),
        },
    }


def build_learning_path_index(
    seed: LearningPathSeed,
    *,
    dataset_version: str,
    archetypes: Mapping[str, str],
    content_pages: Iterable[ContentPage],
    formulation_articles: Mapping[str, str],
) -> dict[str, Any]:
    """Resolve each step to a title and a route; stubs stay visible as ``has_article = false``."""

    pages = {page.content_id: page for page in content_pages if page.status == "published"}
    validate_learning_paths(seed, archetype_ids=archetypes, content_pages=pages.values())
    paths: list[dict[str, Any]] = []
    for path in seed.paths:
        steps: list[dict[str, Any]] = []
        for index, step in enumerate(path.steps, start=1):
            if step.target_type == "formulation":
                title = archetypes[step.target_id]
                route = f"/formulations/{step.target_id}"
                content_id = formulation_articles.get(step.target_id)
                has_article = content_id is not None
            else:
                page = pages[step.target_id]
                title = page.title_ja
                content_id = page.content_id
                route = (
                    f"/methods/{page.method_id}"
                    if page.method_id
                    else f"/formulations/{page.canonical_entity_id}"
                    if page.canonical_entity_type == "problem"
                    and page.canonical_entity_id in archetypes
                    else f"/learn/{page.content_id}"
                )
                has_article = True
            steps.append(
                {
                    "step": index,
                    "target_type": step.target_type,
                    "target_id": step.target_id,
                    "content_id": content_id,
                    "title_ja": title,
                    "route": route,
                    "question_ja": step.question_ja,
                    "has_article": has_article,
                }
            )
        paths.append(
            {
                "path_id": path.path_id,
                "title_ja": path.title_ja,
                "summary_ja": path.summary_ja,
                "goal_ja": path.goal_ja,
                "audience_ja": path.audience_ja,
                "route": f"/paths/{path.path_id}",
                "steps": steps,
            }
        )
    return {
        "contract_version": LEARNING_PATH_CONTRACT_VERSION,
        "dataset_version": dataset_version,
        "paths": paths,
    }


def _descriptor_label(field: str, value: str) -> str:
    # The same code can mean different things per column ("mixed" variables vs constraints).
    return _FIELD_DESCRIPTOR_LABELS.get((field, value)) or _DESCRIPTOR_LABELS.get(value, value)


def _block_math(latex: str) -> str:
    return f'<div class="math-block" tabindex="0">{latex_to_mathml(latex, display="block")}</div>'


def _maturity(page: ContentPage | None) -> Maturity:
    if page is None:
        return "skeleton"
    return "article_with_figure" if "::: explorable" in page.body else "article"


def _fit_rank(level: object) -> int:
    try:
        return _FIT_ORDER.index(str(level))
    except ValueError:
        return len(_FIT_ORDER)


def _split(value: object) -> list[str]:
    return [item.strip() for item in str(value or "").split(";") if item.strip()]


def _require_unique(values: list[str], label: str) -> None:
    if len(values) != len(set(values)):
        duplicates = sorted({value for value in values if values.count(value) > 1})
        raise ValueError(f"duplicate {label}: {', '.join(duplicates)}")


def _require_acyclic(edges: list[tuple[str, str]], label: str) -> None:
    graph: dict[str, list[str]] = {}
    for source, target in edges:
        graph.setdefault(source, []).append(target)
    state: dict[str, int] = {}

    def visit(node: str, trail: list[str]) -> None:
        if state.get(node) == 1:
            raise ValueError(f"{label} relations contain a cycle: {' -> '.join([*trail, node])}")
        if state.get(node) == 2:
            return
        state[node] = 1
        for target in graph.get(node, []):
            visit(target, [*trail, node])
        state[node] = 2

    for node in sorted(graph):
        visit(node, [])


def authored_route_ids(root: Path) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Return formulation and path IDs whose public routes the seeds prove to exist."""

    atlas = load_formulation_atlas_seed(root / "data/seeds/formulation_atlas.json")
    paths = load_learning_path_seed(root / "data/seeds/learning_paths.json")
    return (
        tuple(entry.problem_id for entry in atlas.formulations),
        tuple(path.path_id for path in paths.paths),
    )
