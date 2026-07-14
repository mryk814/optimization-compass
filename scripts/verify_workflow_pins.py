from __future__ import annotations

import argparse
import re
from pathlib import Path

USES_LINE = re.compile(r"^\s*(?:-\s*)?uses:\s*(?P<reference>\S+)(?:\s+#\s*(?P<comment>.+))?\s*$")
EXACT_ACTION = re.compile(
    r"^(?P<repository>[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*)@"
    r"(?P<sha>[0-9a-f]{40})$"
)
VERSION_COMMENT = re.compile(r"^v\d+(?:\.\d+){0,2}(?:[-+][A-Za-z0-9_.-]+)?$")


def validate_workflow(path: Path) -> list[str]:
    errors: list[str] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        match = USES_LINE.match(line)
        if match is None:
            continue
        reference = match.group("reference")
        if reference.startswith("./"):
            continue
        action = EXACT_ACTION.fullmatch(reference)
        if action is None:
            errors.append(f"{path}:{line_number}: external action is not pinned to a 40-char SHA")
            continue
        comment = (match.group("comment") or "").strip()
        if VERSION_COMMENT.fullmatch(comment) is None:
            errors.append(f"{path}:{line_number}: pinned action needs an exact version comment")
    return errors


def validate_workflows(workflows_directory: Path) -> list[str]:
    workflows = sorted([*workflows_directory.glob("*.yml"), *workflows_directory.glob("*.yaml")])
    if not workflows:
        return [f"{workflows_directory}: no workflow files found"]
    return [error for workflow in workflows for error in validate_workflow(workflow)]


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate immutable GitHub Action references.")
    parser.add_argument(
        "--workflows",
        type=Path,
        default=Path(".github/workflows"),
        help="Directory containing GitHub Actions workflows.",
    )
    args = parser.parse_args()
    errors = validate_workflows(args.workflows)
    if errors:
        for error in errors:
            print(error)
        return 1
    print(f"validated immutable action pins in {args.workflows}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
