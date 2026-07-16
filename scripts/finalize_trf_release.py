from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).parents[1]


def replace_if_needed(path: Path, old: str, new: str, *, count: int = 1) -> None:
    text = path.read_text(encoding="utf-8")
    if old in text:
        if count == 1 and text.count(old) != 1:
            raise SystemExit(f"{path}: expected one occurrence of {old[:80]!r}")
        path.write_text(text.replace(old, new, count), encoding="utf-8")
        return
    if new not in text:
        raise SystemExit(f"{path}: neither old nor finalized fragment is present: {old[:80]!r}")


def finalize_dataset_release() -> None:
    path = ROOT / "src/optimization_compass/dataset_release.py"
    text = path.read_text(encoding="utf-8")
    learning = (
        "DEFAULT_LEARNING_GRAPH_MIGRATION = "
        'ROOT / "data/migrations/010_learning_graph_and_aliases.sql"'
    )
    trf = (
        "DEFAULT_TRF_DEFAULTS_MIGRATION = "
        'ROOT / "data/migrations/011_trust_region_reflective_defaults.sql"'
    )
    if trf not in text:
        if text.count(learning) != 1:
            raise SystemExit("learning-graph migration constant did not resolve exactly once")
        text = text.replace(learning, learning + "\n" + trf, 1)

    protected_old = "            DEFAULT_FAILURE_MODE_MIGRATION,\n            seed_path,\n"
    protected_new = (
        "            DEFAULT_FAILURE_MODE_MIGRATION,\n"
        "            DEFAULT_LEARNING_GRAPH_MIGRATION,\n"
        "            DEFAULT_TRF_DEFAULTS_MIGRATION,\n"
        "            seed_path,\n"
    )
    if protected_old in text:
        text = text.replace(protected_old, protected_new, 1)
    elif protected_new not in text:
        raise SystemExit("protected migration inputs were not in the expected state")

    execution = (
        "        connection.executescript(DEFAULT_LEARNING_GRAPH_MIGRATION.read_text("
        'encoding="utf-8"))\n'
    )
    trf_execution = (
        "        connection.executescript(DEFAULT_TRF_DEFAULTS_MIGRATION.read_text("
        'encoding="utf-8"))\n'
    )
    if trf_execution not in text:
        if text.count(execution) != 1:
            raise SystemExit("learning-graph execution did not resolve exactly once")
        text = text.replace(execution, execution + trf_execution, 1)

    text = text.replace(
        '"Published constrained-continuous and multi-objective learning slices."',
        '"Published canonical Trust Region Reflective defaults and guidance."',
        1,
    )
    text = text.replace(
        '"Constrained and multi-objective concepts lacked canonical executable visuals."',
        '"A widely used SciPy default was represented only through broad adjacent methods."',
        1,
    )
    text = text.replace(
        '"Added renderer-family contracts for feasible regions and Pareto fronts, "\n'
        '                "with canonical scenarios, references, and failure contrast."',
        '"Added a canonical Trust Region Reflective method, primary source, "\n'
        '                "implementation mapping, and API-default metadata."',
        1,
    )
    text = text.replace(
        '"Connect canonical problems to artifacts, routes, content, Gallery, "\n'
        '                "Map, and sources."',
        '"Separate library default behavior from method recommendation priority, "\n'
        '                "and connect the dedicated guide to generated search and retrieval."',
        1,
    )
    path.write_text(text, encoding="utf-8")


def finalize_authority_and_content() -> None:
    authority = ROOT / "src/optimization_compass/resources/release-authority.json"
    payload = json.loads(authority.read_text(encoding="utf-8"))
    payload["dataset_version"] = "0.11.0"
    payload["release_date"] = "2026-07-16"
    authority.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    least_squares = ROOT / "content/methods/least-squares.md"
    text = least_squares.read_text(encoding="utf-8")
    text = text.replace(
        "related_ids: [method.gradient-descent, trust-region-newton-cg]",
        "related_ids: [method.gradient-descent, trust-region-newton-cg, trust-region-reflective]",
        1,
    )
    text = text.replace(
        "- bounds中心・大規模 → trust-region reflective",
        "- bounds中心・大規模 → [Trust Region Reflective](#/learn/trust-region-reflective)",
        1,
    )
    least_squares.write_text(text, encoding="utf-8")

    density_doc = ROOT / "docs/method-content-density.md"
    text = density_doc.read_text(encoding="utf-8")
    if "## Default-method pilot" not in text:
        marker = "## Audit report\n"
        if marker not in text:
            raise SystemExit("method density audit marker is missing")
        text = text.replace(
            marker,
            "## Default-method pilot\n\n"
            "Issue #111 adds a dedicated Trust Region Reflective guide because it is "
            "selected implicitly by a high-use SciPy API. This raises the published "
            "method-guide baseline to 67 while keeping library defaults separate from "
            "recommendation priority.\n\n" + marker,
            1,
        )
    density_doc.write_text(text, encoding="utf-8")


def finalize_test_goldens() -> None:
    replacements = {
        "tests/test_method_content_density.py": [
            ("MINIMUM_PUBLISHED_METHOD_GUIDES = 66", "MINIMUM_PUBLISHED_METHOD_GUIDES = 67"),
        ],
        "tests/test_derived_media.py": [
            ('manifest.dataset_version == "0.10.0"', 'manifest.dataset_version == "0.11.0"'),
        ],
        "tests/test_evidence.py": [("len(index.sources) == 95", "len(index.sources) == 96")],
        "tests/test_release_identity.py": [
            ('authority.dataset_version == "0.10.0"', 'authority.dataset_version == "0.11.0"'),
        ],
        "tests/test_site_export.py": [
            ('len(source_payload["sources"]) == 95', 'len(source_payload["sources"]) == 96'),
        ],
        "site/src/contracts/learning-slices.test.ts": [
            (
                'expect(feasible.dataset_version).toBe("0.10.0")',
                'expect(feasible.dataset_version).toBe("0.11.0")',
            ),
            (
                'expect(pareto.dataset_version).toBe("0.10.0")',
                'expect(pareto.dataset_version).toBe("0.11.0")',
            ),
        ],
        "site/src/contracts/coverage.test.ts": [
            (
                "expect(report.subjects).toHaveLength(164)",
                "expect(report.subjects).toHaveLength(165)",
            ),
        ],
    }
    for relative, changes in replacements.items():
        path = ROOT / relative
        for old, new in changes:
            replace_if_needed(path, old, new)

    fixture = ROOT / "tests/fixtures/recommendation_cases.json"
    fixture.write_text(
        fixture.read_text(encoding="utf-8").replace(
            '"dataset_version": "0.10.0"',
            '"dataset_version": "0.11.0"',
        ),
        encoding="utf-8",
    )


def main() -> None:
    finalize_dataset_release()
    finalize_authority_and_content()
    finalize_test_goldens()


if __name__ == "__main__":
    main()
