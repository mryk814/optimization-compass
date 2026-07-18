"""Safe, review-first templates for task-oriented knowledge authoring."""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from optimization_compass.validation_tasks import find_repository_root

CONTRACT_VERSION = "1.0.0"
GALLERY_AUTHORITY = "data/seeds/site_gallery.json"
_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


class ScaffoldError(ValueError):
    """A requested scaffold cannot be created safely."""


@dataclass(frozen=True)
class ScaffoldSpec:
    """The shared safety and review contract for one authoring task."""

    task: str
    title: str
    authorities: tuple[str, ...]
    authority_entry: str
    validation_task: str
    pr_gate: str
    required_inputs: tuple[str, ...]
    template_files: tuple[str, ...]
    template_builder: Callable[[str], dict[str, str]]
    notes: tuple[str, ...]


def _validate_id(requested_id: str) -> None:
    if not _ID_PATTERN.fullmatch(requested_id):
        raise ScaffoldError(
            "--id must start with a letter or number and contain only letters,"
            " numbers, '.', '_' or '-'; stable IDs are supplied by the author"
        )


def _todo(label: str) -> str:
    return f"TODO: replace with a reviewed {label}; do not infer or copy blindly"


def _json_template(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def _yaml_scalar(value: str) -> str:
    """Quote a placeholder so generated review YAML remains parseable."""
    return json.dumps(value, ensure_ascii=False)


def _content_method_files(requested_id: str) -> dict[str, str]:
    summary = _todo("Japanese summary whose first body paragraph matches exactly")
    article = f"""---
content_id: {requested_id}
kind: method
method_id: {_yaml_scalar(_todo("existing canonical method ID"))}
title_ja: {_yaml_scalar(_todo("Japanese title"))}
title_en: {_yaml_scalar(_todo("English method name"))}
summary: {_yaml_scalar(summary)}
source_ids: []
prerequisites: []
related_ids: []
visualization_ids: []
comparison_ids: []
status: draft
last_reviewed: null
---

{summary}

## 直感

{_todo("method intuition")}

## 適用範囲と診断

- 変数・目的・制約: {_todo("scope")}
- 利用できる情報と評価コスト: {_todo("available information and evaluation cost")}
- 成功シグナルと切替シグナル: {_todo("diagnostic signals")}

## 限界

{_todo("limitations")}
"""
    readme = _generic_readme(
        CONTENT_METHOD_SPEC,
        requested_id,
        extra=(
            "`method_id` は既存canonical methodを確認してから埋める。content IDと"
            "canonical method IDが同じだとは仮定しない。",
            "published記事はsummaryと最初の本文段落を完全一致させ、日本語だけで説明を完結させる。",
        ),
    )
    return {"method-article.md": article, "README.md": readme}


def _gallery_case_files(requested_id: str) -> dict[str, str]:
    return {
        "gallery-case.json": _json_template(gallery_case_template(requested_id)),
        "README.md": _generic_readme(
            GALLERY_CASE_SPEC,
            requested_id,
            extra=(
                "candidate、conditional、excludedのmethod集合を重複させない。",
                "固定された教育用instanceが実問題への性能保証ではないことをlimitationsに書く。",
            ),
        ),
    }


def _problem_instance_files(requested_id: str) -> dict[str, str]:
    payload: dict[str, Any] = {
        "problem_definition_id": _todo("existing or explicitly reviewed problem definition ID"),
        "problem_instance_id": requested_id,
        "registry_key": _todo("matching problem registry key"),
        "mathematical_family": _todo("mathematical family"),
        "variable_domain": _todo("variable domain"),
        "objective_direction": _todo("objective direction"),
        "constraint_class": _todo("constraint class"),
        "dimension_and_parameters": {},
        "available_oracles": [],
        "initialization_policy": _todo("initialization and seed policy"),
        "known_reference_semantics": _todo("reference status and optimizer visibility"),
        "source_ids": [],
        "last_verified": None,
    }
    registry = f'''"""Review-only executable skeleton for problem instance `{requested_id}`."""


def evaluate_instance(*args: object, **kwargs: object) -> object:
    """Implement and test the registry contract after reviewing the metadata."""
    raise NotImplementedError("TODO: implement the reviewed problem instance")
'''
    test = f'''"""Focused test skeleton for problem instance `{requested_id}`."""


def test_{_safe_python_suffix(requested_id)}_contract() -> None:
    """TODO: validate dimensions, objective, constraints, reference, and infeasible behavior."""
    raise NotImplementedError("TODO: add focused executable tests")
'''
    return {
        "problem-instance.json": _json_template(payload),
        "problem-registry.py": registry,
        "test-problem-instance.py": test,
        "README.md": _generic_readme(
            PROBLEM_INSTANCE_SPEC,
            requested_id,
            extra=(
                "problem-suite metadataとproblem_registry.pyは必ず同じinstanceを指す"
                "ペアとしてレビューする。",
                "既知のreferenceをoptimizerが利用できる情報と混同しない。",
            ),
        ),
    }


def _comparison_files(requested_id: str) -> dict[str, str]:
    payload: dict[str, Any] = {
        "comparison_id": requested_id,
        "identity_status": _todo("canonical or derived identity"),
        "canonical_comparison_id": None,
        "mode": _todo("validated comparison mode"),
        "problem_definition_id": _todo("existing problem definition ID"),
        "problem_instance_id": _todo("existing problem instance ID"),
        "question": _todo("comparison question"),
        "fixed_factors": [],
        "changed_factors": [],
        "seed_policy": _todo("seed policy"),
        "budget": {},
        "stopping_policy": _todo("stopping policy"),
        "tuning_policy": _todo("tuning policy"),
        "synchronization_axis": _todo("synchronization axis"),
        "metrics": [],
        "members": [],
        "fairness_note": _todo("fairness note"),
        "caveat": _todo("comparability caveat"),
        "ranking_eligible": _todo("ranking eligibility after benchmark review"),
        "source_ids": [],
    }
    test = f'''"""Focused test skeleton for comparison `{requested_id}`."""


def test_{_safe_python_suffix(requested_id)}_contract() -> None:
    """TODO: validate fixed/changed factors, fairness, metrics, and ranking eligibility."""
    raise NotImplementedError("TODO: add focused comparison contract tests")
'''
    return {
        "comparison.json": _json_template(payload),
        "test-comparison.py": test,
        "README.md": _generic_readme(
            COMPARISON_SPEC,
            requested_id,
            extra=(
                "既存trace・problem・method・rendererを先に解決し、新しいrendererをこの作業に隠して追加しない。",
                "failure contrastやcontext不足の比較はranking eligibleにしない。",
            ),
        ),
    }


def _method_files(requested_id: str) -> dict[str, str]:
    payload: dict[str, Any] = {
        "method_id": requested_id,
        "name_ja": _todo("Japanese method name"),
        "name_en": _todo("English method name"),
        "method_family_id": _todo("existing or reviewed method family ID"),
        "aliases": [],
        "summary": _todo("method summary"),
        "variable_types": [],
        "objective_structures": [],
        "constraint_structures": [],
        "required_conditions": [],
        "exclusion_conditions": [],
        "implementation_ids": [],
        "source_ids": [],
        "evidence_claims": [],
        "status": "draft",
    }
    return {
        "method-record.json": _json_template(payload),
        "migration-plan.md": f"""# Canonical method migration plan: `{requested_id}`

This is a review note only. It is not a migration and must not be copied into the
repository's registered migration sequence without maintainer review.

## Identity

- method ID: `{requested_id}` (supplied by the author; not allocated by this scaffold)
- duplicate/alias/implementation check: {_todo("identity review")}
- method-versus-implementation boundary: {_todo("boundary")}

## Evidence and relations

- authoritative source records: {_todo("source IDs and URLs")}
- evidence claims and targets: {_todo("evidence review")}
- family and implementation mappings: {_todo("relation review")}

## Required follow-up

- choose the canonical migration/build input after identity review;
- add content separately under `content/methods/`;
- add focused identity, relation, recommendation, and release tests;
- run the full validation tier before proposing a dataset release.
""",
        "README.md": _generic_readme(
            METHOD_SPEC,
            requested_id,
            extra=(
                "これは高リスクのcanonical method追加のreview packであり、"
                "migrationやSQLiteへは書き込まない。",
                "source/evidenceとmethod-versus-implementation境界を確定できない場合は停止する。",
            ),
        ),
    }


def _scenario_files(requested_id: str) -> dict[str, str]:
    payload: dict[str, Any] = {
        "scenario_id": requested_id,
        "identity_status": _todo("canonical, derived, or generated-only identity"),
        "canonical_scenario_id": None,
        "title_ja": _todo("Japanese title"),
        "title_en": _todo("English title"),
        "purpose": _todo("learning purpose"),
        "problem_definition_id": _todo("existing problem definition ID"),
        "problem_instance_id": _todo("existing problem instance ID"),
        "method_and_profile": [],
        "experiment": {
            "oracle_policy": [],
            "initial_condition": _todo("initial condition"),
            "parameter_preset_id": _todo("parameter preset"),
            "seed": {"status": _todo("fixed or not_applicable"), "value": None},
            "budget": {"metric": _todo("budget metric"), "value": None},
            "stopping": {},
            "tuning_policy": _todo("tuning policy"),
        },
        "runs": [],
        "artifact": {
            "artifact_kind": _todo("artifact kind"),
            "artifact_contract": _todo("artifact contract"),
            "renderer_family": _todo("existing renderer family"),
            "observable_ids": [],
            "payload_path": _todo("generated payload path"),
            "generator_entrypoint": _todo("deterministic generator entrypoint"),
        },
        "observables": [],
        "success_signals": [],
        "failure_signals": [],
        "learning_objective": {
            "ja": _todo("Japanese learning objective"),
            "en": _todo("English learning objective"),
        },
        "static_summary": {
            "ja": _todo("Japanese static summary"),
            "en": _todo("English static summary"),
        },
        "text_alternative": {
            "ja": _todo("Japanese text alternative"),
            "en": _todo("English text alternative"),
        },
        "sources": [],
        "limitations": {"ja": _todo("Japanese limitations"), "en": _todo("English limitations")},
    }
    test = f'''"""Focused test skeleton for visualization scenario `{requested_id}`."""


def test_{_safe_python_suffix(requested_id)}_contract() -> None:
    """TODO: validate scenario identity, artifact, observables, summaries, and signals."""
    raise NotImplementedError("TODO: add focused scenario and artifact tests")
'''
    return {
        "scenario.json": _json_template(payload),
        "scenario-generator.py": (
            f'''"""Review-only generator skeleton for scenario `{requested_id}`."""


def generate_scenario() -> object:
    """TODO: implement deterministic generation using an existing artifact contract."""
    raise NotImplementedError("TODO: implement the reviewed scenario generator")
'''
        ),
        "test-scenario.py": test,
        "README.md": _generic_readme(
            SCENARIO_SPEC,
            requested_id,
            extra=(
                "既存problem・profile・artifact contract・renderer familyを優先し、"
                "新しいcontractを暗黙に作らない。",
                "visualizationにはstatic summaryとtext alternativeを必ず対応させ、"
                "成功だけでなくfailure signalも記録する。",
            ),
        ),
    }


def _safe_python_suffix(requested_id: str) -> str:
    """Make a readable, non-authoritative placeholder test function suffix."""
    suffix = re.sub(r"[^A-Za-z0-9_]", "_", requested_id)
    if suffix[0].isdigit():
        suffix = f"id_{suffix}"
    return suffix


def gallery_case_template(requested_id: str) -> dict[str, Any]:
    """Return an intentionally incomplete Gallery entry with no invented facts."""
    _validate_id(requested_id)
    placeholder = _todo("reviewed value")
    method_placeholder = {"method_id": placeholder, "reason": placeholder}
    return {
        "case_id": requested_id,
        "title_ja": placeholder,
        "title_en": placeholder,
        "domain": placeholder,
        "problem_archetype_id": placeholder,
        "feature_values": [{"feature_id": placeholder, "value": placeholder}],
        "question_answers": {},
        "candidate_methods": [method_placeholder],
        "conditional_methods": [method_placeholder.copy()],
        "excluded_methods": [method_placeholder.copy()],
        "implementation_ids": [],
        "visualization_ids": [],
        "comparison_ids": [],
        "source_ids": [],
        "difficulty": placeholder,
        "status": "draft",
        "last_reviewed": None,
        "question": placeholder,
        "variable_domain": placeholder,
        "decision_variables": placeholder,
        "objective": placeholder,
        "constraints": placeholder,
        "map_node_id": placeholder,
        "python_example": "# TODO: add a minimal, syntactically valid example",
        "practical_notes": placeholder,
        "limitations": [placeholder],
    }


def _generic_readme(spec: ScaffoldSpec, requested_id: str, *, extra: tuple[str, ...] = ()) -> str:
    authorities = "\n".join(f"- `{authority}`" for authority in spec.authorities)
    required = "\n".join(f"- {item}" for item in spec.required_inputs)
    notes = "\n".join(f"- {item}" for item in (*spec.notes, *extra))
    validation_note = (
        "This command is also the required PR gate."
        if spec.validation_task == spec.pr_gate
        else "The focused task is not the PR gate; run the gate below before opening the PR."
    )
    return f"""# {spec.title}: `{requested_id}`

This directory is a review-first template, not canonical knowledge. The requested
ID was supplied by the author; this scaffold does not allocate stable IDs or invent
facts, sources, relations, defaults, or benchmark results.

## Editable authority (after review)

{authorities}

The files in this directory are drafts only. Do not copy them into the authority
until every placeholder, ID, source, relation, and claim has been independently
reviewed. This command never writes the authority or generated artifacts.

Forbidden outputs include:

- `src/optimization_compass/resources/knowledge.sqlite`
- `site/public/data/**`
- `data/optimization_method_selection_database_v*`

## Required review inputs

{required}

## Task-specific cautions

{notes}

## Validation and PR checklist

```bash
uv run optimization-compass validate {spec.validation_task}
```

{validation_note} Run:

```bash
uv run optimization-compass validate {spec.pr_gate}
```

Before opening a PR, complete `docs/knowledge-change-checklist.md` from the
repository root
and state the authority, evidence, generated impact, and exact validation results.
"""


def _ensure_safe_output(root: Path, output_directory: Path) -> None:
    resolved = output_directory.resolve()
    protected = (
        root / ".git",
        root / "content",
        root / "data",
        root / "site" / "public",
        root / "src" / "optimization_compass",
    )
    if any(resolved == path.resolve() or path.resolve() in resolved.parents for path in protected):
        raise ScaffoldError(
            "scaffold output must be a separate draft directory; generated and canonical "
            "paths are forbidden"
        )
    if resolved == root.resolve():
        raise ScaffoldError("scaffold output must not be the repository root")


def _write_files(root: Path, output_directory: Path, files: dict[str, str]) -> None:
    _ensure_safe_output(root, output_directory)
    if output_directory.exists():
        if not output_directory.is_dir():
            raise ScaffoldError(f"output path is not a directory: {output_directory}")
        if any(output_directory.iterdir()):
            raise ScaffoldError(
                f"output directory is not empty: {output_directory}; choose another path"
                " or remove it deliberately before retrying"
            )
    output_directory.mkdir(parents=True, exist_ok=False)
    for filename, content in files.items():
        (output_directory / filename).write_text(content, encoding="utf-8")


def _manifest(
    spec: ScaffoldSpec,
    requested_id: str,
    *,
    write: bool,
    output_directory: Path | None,
    existing_id: bool | None = None,
) -> dict[str, Any]:
    return {
        "contract_version": CONTRACT_VERSION,
        "task": spec.task,
        "requested_id": requested_id,
        "existing_id": existing_id,
        "write": write,
        "output_directory": str(output_directory) if output_directory else None,
        "files_to_create": list(spec.template_files) if write else [],
        "planned_authority_entry": spec.authority_entry.format(id=requested_id),
        "editable_authorities": list(spec.authorities),
        "forbidden_outputs": [
            "src/optimization_compass/resources/knowledge.sqlite",
            "site/public/data/**",
            "data/optimization_method_selection_database_v*",
        ],
        "required_inputs": list(spec.required_inputs),
        "validation": f"optimization-compass validate {spec.validation_task}",
        "pr_gate": f"optimization-compass validate {spec.pr_gate}",
        "pr_checklist": "docs/knowledge-change-checklist.md",
    }


def _scaffold(
    spec: ScaffoldSpec,
    requested_id: str,
    *,
    write: bool = False,
    output_directory: Path | None = None,
    existing_id: bool | None = None,
) -> dict[str, Any]:
    _validate_id(requested_id)
    root = find_repository_root()
    if output_directory is None and write:
        output_directory = root / "scaffolds" / spec.task / requested_id
    if not write and output_directory is not None:
        raise ScaffoldError("--output requires --write")
    if write and output_directory is None:
        raise ScaffoldError("--write requires an output directory")
    if write:
        assert output_directory is not None
        _write_files(root, output_directory, spec.template_builder(requested_id))
    return _manifest(
        spec,
        requested_id,
        write=write,
        output_directory=output_directory,
        existing_id=existing_id,
    )


CONTENT_METHOD_SPEC = ScaffoldSpec(
    task="content-method",
    title="Method article scaffold",
    authorities=("content/methods/<content-id>.md",),
    authority_entry="content/methods/{id}.md",
    validation_task="content",
    pr_gate="tier-a",
    required_inputs=(
        "an existing canonical method ID (do not assume it equals content_id)",
        "authoritative source IDs and a Japanese summary",
        "intuition, scope, diagnostics, switch signals, limitations, and valid relation IDs",
    ),
    template_files=("method-article.md", "README.md"),
    template_builder=_content_method_files,
    notes=("既存entityへの記事追加（Recipe B）として扱う。",),
)

GALLERY_CASE_SPEC = ScaffoldSpec(
    task="gallery-case",
    title="Gallery case scaffold",
    authorities=(GALLERY_AUTHORITY,),
    authority_entry=f"{GALLERY_AUTHORITY}#cases/{{id}}",
    validation_task="gallery",
    pr_gate="tier-b",
    required_inputs=(
        "problem_archetype_id and valid feature values",
        "Diagnose question answers and disjoint candidate/conditional/excluded method IDs "
        "with reasons",
        "implementation_ids, source_ids, optional visualization/comparison IDs",
        "a minimal compilable python_example and explicit limitations",
    ),
    template_files=("gallery-case.json", "README.md"),
    template_builder=_gallery_case_files,
    notes=("既存canonical entityのみを参照する低リスクのstructured-data追加。",),
)

PROBLEM_INSTANCE_SPEC = ScaffoldSpec(
    task="problem-instance",
    title="Problem instance scaffold",
    authorities=(
        "src/optimization_compass/resources/problem-suite.json",
        "src/optimization_compass/problem_registry.py",
    ),
    authority_entry="problem-suite.json#instances/{id}",
    validation_task="problem",
    pr_gate="tier-c",
    required_inputs=(
        "existing definition or reviewed new problem identity",
        "matching registry_key, dimension/parameter and objective/constraint semantics",
        "oracle availability, initialization/seed policy, and reference visibility",
        "authoritative source IDs and focused evaluator/gradient tests",
    ),
    template_files=(
        "problem-instance.json",
        "problem-registry.py",
        "test-problem-instance.py",
        "README.md",
    ),
    template_builder=_problem_instance_files,
    notes=("metadataとexecutable behaviorを片方だけ変更しない。",),
)

COMPARISON_SPEC = ScaffoldSpec(
    task="comparison",
    title="Comparison scaffold",
    authorities=("data/seeds/site_comparisons.json",),
    authority_entry="data/seeds/site_comparisons.json#comparisons/{id}",
    validation_task="comparison",
    pr_gate="tier-b",
    required_inputs=(
        "existing traces/artifacts, problem instance, methods, and renderer family",
        "comparison question, fixed/changed factors, seed, budget, and stopping policy",
        "synchronization axis, metrics, member parameters, fairness, caveat, and "
        "ranking eligibility",
        "source IDs and canonical-versus-derived identity",
    ),
    template_files=("comparison.json", "test-comparison.py", "README.md"),
    template_builder=_comparison_files,
    notes=("existing validated comparison fields and renderer familiesを再利用する。",),
)

METHOD_SPEC = ScaffoldSpec(
    task="method",
    title="Canonical method scaffold",
    authorities=(
        "registered dataset migration/build inputs",
        "content/methods/<content-id>.md (separate article)",
    ),
    authority_entry="canonical method inputs#methods/{id}",
    validation_task="tier-c",
    pr_gate="tier-c",
    required_inputs=(
        "proof that the ID is not an alias, variant, implementation, or duplicate",
        "method family, aliases, support scope, and method-versus-implementation boundary",
        "authoritative source rows, evidence claims, mappings, and relation targets",
        "identity, relation, recommendation, and release regression tests",
    ),
    template_files=("method-record.json", "migration-plan.md", "README.md"),
    template_builder=_method_files,
    notes=("Recipe F相当のmaintainer-reviewed high-risk change。",),
)

SCENARIO_SPEC = ScaffoldSpec(
    task="scenario",
    title="Visualization scenario scaffold",
    authorities=(
        "src/optimization_compass/visualization_scenarios.py and scenario generation code",
        "existing canonical problem/profile/artifact/renderer inputs",
    ),
    authority_entry="scenario contracts#scenarios/{id}",
    validation_task="tier-c",
    pr_gate="tier-c",
    required_inputs=(
        "canonical problem instance, method/profile, purpose, and identity status",
        "experiment policy: oracle, initial condition, seed, budget, tuning, and stopping",
        "deterministic generator, artifact contract, renderer family, and observables",
        "learning objective, success/failure signals, static summary, text alternative, "
        "sources, and limitations",
    ),
    template_files=("scenario.json", "scenario-generator.py", "test-scenario.py", "README.md"),
    template_builder=_scenario_files,
    notes=("新renderer/artifact contractをこのscaffoldから暗黙に導入しない。",),
)


def _existing_gallery_ids(root: Path) -> set[str]:
    source = root / GALLERY_AUTHORITY
    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ScaffoldError(f"could not inspect {GALLERY_AUTHORITY}: {error}") from error
    cases = payload.get("cases")
    if not isinstance(cases, list):
        raise ScaffoldError(f"{GALLERY_AUTHORITY} does not contain a cases list")
    return {
        str(case["case_id"])
        for case in cases
        if isinstance(case, dict) and isinstance(case.get("case_id"), str)
    }


def scaffold_gallery_case(
    requested_id: str,
    *,
    write: bool = False,
    output_directory: Path | None = None,
) -> dict[str, Any]:
    """Plan or write a Gallery-case scaffold without touching canonical inputs."""
    _validate_id(requested_id)
    root = find_repository_root()
    existing_id = requested_id in _existing_gallery_ids(root)
    if existing_id:
        raise ScaffoldError(
            f"Gallery case ID {requested_id!r} already exists in {GALLERY_AUTHORITY};"
            " choose a new reviewed ID"
        )
    return _scaffold(
        GALLERY_CASE_SPEC,
        requested_id,
        write=write,
        output_directory=output_directory,
        existing_id=False,
    )


def scaffold_content_method(
    requested_id: str,
    *,
    write: bool = False,
    output_directory: Path | None = None,
) -> dict[str, Any]:
    """Plan or write an existing-method article scaffold."""
    return _scaffold(
        CONTENT_METHOD_SPEC,
        requested_id,
        write=write,
        output_directory=output_directory,
    )


def scaffold_problem_instance(
    requested_id: str,
    *,
    write: bool = False,
    output_directory: Path | None = None,
) -> dict[str, Any]:
    """Plan or write a problem-instance review scaffold."""
    return _scaffold(
        PROBLEM_INSTANCE_SPEC,
        requested_id,
        write=write,
        output_directory=output_directory,
    )


def scaffold_comparison(
    requested_id: str,
    *,
    write: bool = False,
    output_directory: Path | None = None,
) -> dict[str, Any]:
    """Plan or write a comparison review scaffold."""
    return _scaffold(
        COMPARISON_SPEC,
        requested_id,
        write=write,
        output_directory=output_directory,
    )


def scaffold_method(
    requested_id: str,
    *,
    write: bool = False,
    output_directory: Path | None = None,
) -> dict[str, Any]:
    """Plan or write a canonical-method review scaffold."""
    return _scaffold(
        METHOD_SPEC,
        requested_id,
        write=write,
        output_directory=output_directory,
    )


def scaffold_scenario(
    requested_id: str,
    *,
    write: bool = False,
    output_directory: Path | None = None,
) -> dict[str, Any]:
    """Plan or write a visualization-scenario review scaffold."""
    return _scaffold(
        SCENARIO_SPEC,
        requested_id,
        write=write,
        output_directory=output_directory,
    )
