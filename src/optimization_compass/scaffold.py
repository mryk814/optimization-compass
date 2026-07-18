"""Safe, review-first templates for task-oriented knowledge authoring."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from optimization_compass.validation_tasks import find_repository_root

CONTRACT_VERSION = "1.0.0"
GALLERY_AUTHORITY = "data/seeds/site_gallery.json"
_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


class ScaffoldError(ValueError):
    """A requested scaffold cannot be created safely."""


def _validate_id(requested_id: str) -> None:
    if not _ID_PATTERN.fullmatch(requested_id):
        raise ScaffoldError(
            "--id must start with a letter or number and contain only letters,"
            " numbers, '.', '_' or '-'; stable IDs are supplied by the author"
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


def gallery_case_template(requested_id: str) -> dict[str, Any]:
    """Return an intentionally incomplete Gallery entry with no invented facts."""
    _validate_id(requested_id)
    placeholder = "TODO: replace with a reviewed value"
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


def gallery_case_manifest(
    requested_id: str,
    *,
    existing_id: bool,
    write: bool,
    output_directory: Path | None,
) -> dict[str, Any]:
    """Build the stable machine-readable plan printed by the CLI."""
    return {
        "contract_version": CONTRACT_VERSION,
        "task": "gallery-case",
        "requested_id": requested_id,
        "existing_id": existing_id,
        "write": write,
        "output_directory": str(output_directory) if output_directory else None,
        "files_to_create": ["gallery-case.json", "README.md"] if write else [],
        "planned_authority_entry": f"{GALLERY_AUTHORITY}#cases/{requested_id}",
        "editable_authorities": [GALLERY_AUTHORITY],
        "forbidden_outputs": [
            "src/optimization_compass/resources/knowledge.sqlite",
            "site/public/data/**",
            "data/optimization_method_selection_database_v*",
        ],
        "required_inputs": [
            "problem_archetype_id",
            "feature_values and Diagnose question_answers",
            "candidate, conditional, and excluded method IDs with reasons",
            "implementation_ids, source_ids, and optional visualization/comparison IDs",
            "a minimal compilable python_example and explicit limitations",
        ],
        "validation": "optimization-compass validate gallery",
        "pr_checklist": "docs/knowledge-change-checklist.md",
    }


def _readme(requested_id: str) -> str:
    return f"""# Gallery case scaffold: `{requested_id}`

This directory is a review-first template, not canonical knowledge. Replace every
`TODO` value after checking existing IDs and authoritative sources. The requested
case ID was supplied by the author; this scaffold does not allocate stable IDs.

## Files and authority

- `gallery-case.json` is a draft entry to review and then copy into
  `{GALLERY_AUTHORITY}`.
- The editable authority is `{GALLERY_AUTHORITY}`. Do not edit generated site data.
- Forbidden generated outputs include `site/public/data/**`, the released SQLite
  database, and versioned distributions.

Before copying the entry, verify that candidate, conditional, and excluded method
sets are disjoint, `map_node_id` follows from `question_answers`, every source and
canonical ID exists, and the Python example compiles. State the fixed educational
instance separately from real-world applicability.

## Validation

```bash
uv run optimization-compass validate gallery
```

This is an iteration subset; run the `tier-b` PR gate before opening the PR. Use
`docs/knowledge-change-checklist.md` for the review checklist.
"""


def _ensure_safe_output(root: Path, output_directory: Path) -> None:
    resolved = output_directory.resolve()
    protected = (
        root / "data" / "seeds",
        root / "site" / "public" / "data",
        root / "src" / "optimization_compass" / "resources",
    )
    if any(resolved == path.resolve() or path.resolve() in resolved.parents for path in protected):
        raise ScaffoldError(
            "scaffold output must be a separate draft directory; generated and canonical "
            "paths are forbidden"
        )
    data_root = (root / "data").resolve()
    if data_root in resolved.parents and any(
        part.startswith("optimization_method_selection_database_v")
        for part in resolved.relative_to(data_root).parts
    ):
        raise ScaffoldError(
            "scaffold output must be a separate draft directory; generated and canonical "
            "paths are forbidden"
        )
    if resolved == root.resolve():
        raise ScaffoldError("scaffold output must not be the repository root")


def write_gallery_case_scaffold(root: Path, requested_id: str, output_directory: Path) -> None:
    """Write the two review files after all safety checks have passed."""
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
    (output_directory / "gallery-case.json").write_text(
        json.dumps(gallery_case_template(requested_id), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (output_directory / "README.md").write_text(_readme(requested_id), encoding="utf-8")


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
    if output_directory is None and write:
        output_directory = root / "scaffolds" / "gallery-case" / requested_id
    if not write and output_directory is not None:
        raise ScaffoldError("--output requires --write")
    if write and output_directory is None:
        raise ScaffoldError("--write requires an output directory")
    if write:
        assert output_directory is not None
        write_gallery_case_scaffold(root, requested_id, output_directory)
    return gallery_case_manifest(
        requested_id,
        existing_id=False,
        write=write,
        output_directory=output_directory,
    )
