from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from optimization_compass.content_models import load_content
from optimization_compass.db import KnowledgeRepository
from optimization_compass.release_identity import load_dataset_release_identity

MINIMUM_PUBLISHED_CONTENT_PAGES = 12
MINIMUM_GALLERY_CASES = 10
MINIMUM_COMPARISONS = 1


def verify_content(root: Path) -> dict[str, int | str]:
    data_root = root / "site/public/data"
    identity = load_dataset_release_identity(data_root / "release.json")
    content_index = _load_index(data_root / "content.json", "pages", identity.dataset_version)
    gallery_index = _load_index(data_root / "gallery.json", "cases", identity.dataset_version)
    if gallery_index.get("contract_version") != "2.0.0":
        raise ValueError("gallery.json must use contract version 2.0.0")
    comparison_index = _load_index(
        data_root / "comparisons.json", "comparisons", identity.dataset_version
    )
    _load_payload(data_root / "recommendation/site-data.json", identity.dataset_version)
    trace_index = _load_payload(data_root / "traces/index.json", identity.dataset_version)
    _load_payload(data_root / "coverage.json", identity.dataset_version)

    source_pages = [page for page in load_content(root / "content") if page.status == "published"]
    generated_pages = content_index["pages"]
    source_ids = {page.content_id for page in source_pages}
    generated_ids = _unique_ids(generated_pages, "content_id", "content pages")
    if source_ids != generated_ids:
        raise ValueError("generated content IDs do not match published Markdown sources")
    _require_minimum(
        "published content pages", len(generated_pages), MINIMUM_PUBLISHED_CONTENT_PAGES
    )

    case_ids = _unique_ids(gallery_index["cases"], "case_id", "gallery cases")
    _require_minimum("gallery cases", len(case_ids), MINIMUM_GALLERY_CASES)
    comparison_ids = _unique_ids(
        comparison_index["comparisons"], "comparison_id", "comparison sets"
    )
    _require_minimum("comparison sets", len(comparison_ids), MINIMUM_COMPARISONS)

    repository = KnowledgeRepository(root / "src/optimization_compass/resources/knowledge.sqlite")
    known_sources = {
        str(row["source_id"]) for row in repository.fetch_all("SELECT source_id FROM sources")
    }
    known_methods = {
        str(row["method_id"]) for row in repository.fetch_all("SELECT method_id FROM methods")
    }
    known_implementations = {
        str(row["implementation_id"])
        for row in repository.fetch_all("SELECT implementation_id FROM implementations")
    }
    known_problems = {
        str(row["problem_id"])
        for row in repository.fetch_all("SELECT problem_id FROM problem_archetypes")
    }
    canonical_cases = {
        str(row["case_id"]): str(row["problem_id"])
        for row in repository.fetch_all("SELECT case_id, problem_id FROM example_cases")
    }
    feature_values = {
        (str(row["feature_id"]), str(row["value_code"]))
        for row in repository.fetch_all("SELECT feature_id, value_code FROM feature_values")
    }
    questions = {
        str(row["question_id"]): (
            str(row["mapped_feature_id"]),
            set(row["allowed_answers"]),
        )
        for row in repository.recommendation_questions()
    }
    _unique_ids(trace_index["traces"], "trace_id", "traces")
    known_content = generated_ids

    for page in generated_pages:
        page_id = str(page["content_id"])
        _require_references(page_id, page.get("source_ids"), known_sources, "source")
        _require_references(page_id, page.get("prerequisites"), known_content, "prerequisite")
        _string_list(page.get("related_ids"), page_id)
        _string_list(page.get("visualization_ids"), page_id)
        _string_list(page.get("comparison_ids"), page_id)

    for case in gallery_index["cases"]:
        case_id = str(case["case_id"])
        if "candidate_method_ids" in case:
            raise ValueError(
                f"{case_id} candidate_method_ids has been replaced by candidate_methods"
            )
        problem_id = str(case["problem_archetype_id"])
        if problem_id not in known_problems:
            raise ValueError(f"{case_id} references unknown problem: {problem_id}")
        if case_id.startswith("EC") and canonical_cases.get(case_id) != problem_id:
            raise ValueError(f"{case_id} does not match its canonical example/problem row")
        _require_references(case_id, case.get("source_ids"), known_sources, "source")
        candidates = _method_reasons(case_id, case.get("candidate_methods"), "candidate")
        _require_references(
            case_id,
            [item["method_id"] for item in candidates],
            known_methods,
            "candidate method",
        )
        _require_references(
            case_id, case.get("implementation_ids"), known_implementations, "implementation"
        )
        conditional = _method_reasons(case_id, case.get("conditional_methods"), "conditional")
        _require_references(
            case_id,
            [item["method_id"] for item in conditional],
            known_methods,
            "conditional method",
        )
        _require_references(case_id, case.get("comparison_ids"), comparison_ids, "comparison")
        excluded = case.get("excluded_methods")
        excluded = _method_reasons(case_id, excluded, "excluded")
        _require_references(
            case_id,
            [item.get("method_id") for item in excluded if isinstance(item, dict)],
            known_methods,
            "excluded method",
        )
        candidate_ids = {item["method_id"] for item in candidates}
        conditional_ids = {item["method_id"] for item in conditional}
        excluded_ids = {item["method_id"] for item in excluded}
        if (
            candidate_ids & conditional_ids
            or candidate_ids & excluded_ids
            or conditional_ids & excluded_ids
        ):
            raise ValueError(f"{case_id} method dispositions must not overlap")
        answers = case.get("question_answers")
        if not isinstance(answers, dict):
            raise ValueError(f"{case_id} question_answers must be an object")
        for question_id, answer in answers.items():
            if question_id not in questions or answer not in questions[question_id][1]:
                raise ValueError(f"{case_id} has invalid answer: {question_id}={answer}")
        if case_id.startswith("EC") and set(answers) != set(questions):
            raise ValueError(f"{case_id} must answer every Diagnose question")
        valid_nodes = {f"answer:{question_id}:{answer}" for question_id, answer in answers.items()}
        if case.get("map_node_id") not in valid_nodes:
            raise ValueError(f"{case_id} map_node_id is not backed by its question answers")
        for feature in case.get("feature_values", []):
            if (
                not isinstance(feature, dict)
                or (str(feature.get("feature_id")), str(feature.get("value"))) not in feature_values
            ):
                raise ValueError(f"{case_id} references unknown feature value: {feature}")
        example = case.get("python_example")
        if not isinstance(example, str) or not example.strip():
            raise ValueError(f"{case_id} python_example must not be blank")
        compile(example, f"gallery:{case_id}", "exec")
        limitations = _string_list(case.get("limitations"), case_id)
        if not limitations:
            raise ValueError(f"{case_id} limitations must be a non-empty list")

    return {
        "dataset_version": identity.dataset_version,
        "content_pages": len(generated_pages),
        "gallery_cases": len(case_ids),
        "comparisons": len(comparison_ids),
    }


def main() -> None:
    result = verify_content(Path(__file__).resolve().parents[1])
    print(
        "validated "
        f"{result['content_pages']} content pages, "
        f"{result['gallery_cases']} gallery cases, and "
        f"{result['comparisons']} comparisons for dataset {result['dataset_version']}"
    )


def _load_index(path: Path, collection: str, version: str) -> dict[str, Any]:
    payload = _load_payload(path, version)
    if not isinstance(payload.get(collection), list):
        raise ValueError(f"{path.name} field must be a list: {collection}")
    return payload


def _load_payload(path: Path, version: str) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path.name} must contain an object")
    if payload.get("dataset_version") != version:
        raise ValueError(f"{path.name} dataset version does not match release identity")
    return payload


def _unique_ids(items: object, field: str, label: str) -> set[str]:
    if not isinstance(items, list):
        raise ValueError(f"{label} must be a list")
    values = [str(item[field]) for item in items if isinstance(item, dict) and item.get(field)]
    if len(values) != len(items) or len(values) != len(set(values)):
        raise ValueError(f"{label} contain missing or duplicate IDs")
    return set(values)


def _require_minimum(label: str, observed: int, minimum: int) -> None:
    if observed < minimum:
        raise ValueError(f"{label} must contain at least {minimum}; observed {observed}")


def _require_references(owner: str, values: object, known: set[str], relation: str) -> None:
    for value in _string_list(values, owner):
        if value not in known:
            raise ValueError(f"{owner} references unknown {relation}: {value}")


def _string_list(value: object, owner: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
        raise ValueError(f"{owner} relation must be a list of non-empty IDs")
    return value


def _method_reasons(owner: str, value: object, disposition: str) -> list[dict[str, str]]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{owner} {disposition}_methods must be a non-empty list")
    result = []
    for item in value:
        if not isinstance(item, dict):
            raise ValueError(f"{owner} {disposition} method must be an object")
        method_id = item.get("method_id")
        reason = item.get("reason")
        if (
            not isinstance(method_id, str)
            or not method_id
            or not isinstance(reason, str)
            or not reason
        ):
            raise ValueError(f"{owner} {disposition} method requires method_id and reason")
        result.append({"method_id": method_id, "reason": reason})
    return result


if __name__ == "__main__":
    main()
