from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README_PATH = ROOT / "README.md"
RELEASE_AUTHORITY_PATH = ROOT / "src/optimization_compass/resources/release-authority.json"
BEGIN_MARKER = "<!-- BEGIN GENERATED DATASET FACTS -->"
END_MARKER = "<!-- END GENERATED DATASET FACTS -->"


class ReadmeFactsError(ValueError):
    pass


@dataclass(frozen=True)
class ReleaseFacts:
    version: str
    release_date: str
    table_count: int
    row_count: int
    method_count: int
    problem_archetype_count: int
    implementation_count: int
    source_count: int
    example_case_count: int
    decision_rule_count: int
    evidence_link_count: int


def load_release_facts(root: Path = ROOT) -> ReleaseFacts:
    authority_path = root / RELEASE_AUTHORITY_PATH.relative_to(ROOT)
    authority = _load_json(authority_path)
    version = _require_string(authority, "dataset_version", authority_path)
    release_date = _require_string(authority, "release_date", authority_path)
    report_path = root / "data" / f"optimization_method_selection_database_v{version}_report.md"
    report = report_path.read_text(encoding="utf-8")

    header = _parse_report_header(report, report_path)
    if header["version"] != version:
        raise ReadmeFactsError(
            f"release report version {header['version']} does not match authority {version}"
        )
    if header["release_date"] != release_date:
        raise ReadmeFactsError(
            f"release report date {header['release_date']} does not match authority {release_date}"
        )

    table_counts = _parse_report_table_counts(report)
    return ReleaseFacts(
        version=version,
        release_date=release_date,
        table_count=int(header["tables"]),
        row_count=int(header["rows"]),
        method_count=_require_table_count(table_counts, "methods", report_path),
        problem_archetype_count=_require_table_count(
            table_counts, "problem_archetypes", report_path
        ),
        implementation_count=_require_table_count(table_counts, "implementations", report_path),
        source_count=_require_table_count(table_counts, "sources", report_path),
        example_case_count=_require_table_count(table_counts, "example_cases", report_path),
        decision_rule_count=_require_table_count(table_counts, "decision_rules", report_path),
        evidence_link_count=_require_table_count(table_counts, "evidence_links", report_path),
    )


def render_release_facts(facts: ReleaseFacts) -> str:
    rows = (
        ("Tables", facts.table_count),
        ("Rows", facts.row_count),
        ("Methods", facts.method_count),
        ("Problem archetypes", facts.problem_archetype_count),
        ("Implementations", facts.implementation_count),
        ("Sources", facts.source_count),
        ("Example cases", facts.example_case_count),
        ("Decision rules", facts.decision_rule_count),
        ("Evidence links", facts.evidence_link_count),
    )
    table = "\n".join(f"| {label} | {value:,} |" for label, value in rows)
    return (
        f"{BEGIN_MARKER}\n"
        f"現在の公開データセットは **{facts.version}** "
        f"（{facts.release_date} release）です。\n\n"
        "| 項目 | 件数 |\n"
        "|---|---:|\n"
        f"{table}\n\n"
        "このブロックはrelease authorityと生成reportから生成します。"
        "手作業で件数を変更しません。\n"
        f"{END_MARKER}"
    )


def update_readme(*, root: Path = ROOT, check: bool = False) -> bool:
    readme_path = root / README_PATH.relative_to(ROOT)
    current = readme_path.read_text(encoding="utf-8")
    facts = load_release_facts(root)
    expected = replace_generated_block(current, render_release_facts(facts))
    _reject_stale_dataset_versions(expected, facts.version)

    if current == expected:
        return False
    if check:
        raise ReadmeFactsError(
            "README release facts are stale; run `uv run python scripts/sync_readme_facts.py`"
        )
    readme_path.write_text(expected, encoding="utf-8", newline="\n")
    return True


def replace_generated_block(readme: str, block: str) -> str:
    if readme.count(BEGIN_MARKER) != 1 or readme.count(END_MARKER) != 1:
        raise ReadmeFactsError("README must contain exactly one generated release-facts block")
    start = readme.index(BEGIN_MARKER)
    end = readme.index(END_MARKER, start) + len(END_MARKER)
    return readme[:start] + block + readme[end:]


def _parse_report_header(report: str, path: Path) -> dict[str, str | int]:
    patterns = {
        "version": r"^- Version: `([^`]+)`$",
        "release_date": r"^- Release date: `([^`]+)`$",
        "tables": r"^- Tables: `([0-9,]+)`$",
        "rows": r"^- Rows: `([0-9,]+)`$",
    }
    values: dict[str, str | int] = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, report, flags=re.MULTILINE)
        if match is None:
            raise ReadmeFactsError(f"{path} is missing report field: {key}")
        raw = match.group(1)
        values[key] = _parse_int(raw) if key in {"tables", "rows"} else raw
    return values


def _parse_report_table_counts(report: str) -> dict[str, int]:
    return {
        table: _parse_int(count)
        for table, count in re.findall(
            r"^\| `([^`]+)` \| ([0-9,]+) \|$",
            report,
            re.MULTILINE,
        )
    }


def _load_json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ReadmeFactsError(f"{path} must contain a JSON object")
    return payload


def _require_string(payload: dict[str, object], field: str, path: Path) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not value:
        raise ReadmeFactsError(f"{path} field {field} must be a non-empty string")
    return value


def _require_table_count(counts: dict[str, int], table: str, path: Path) -> int:
    try:
        return counts[table]
    except KeyError as error:
        raise ReadmeFactsError(f"{path} is missing table count: {table}") from error


def _parse_int(value: str) -> int:
    return int(value.replace(",", ""))


def _reject_stale_dataset_versions(readme: str, current_version: str) -> None:
    outside = re.sub(
        re.escape(BEGIN_MARKER) + r".*?" + re.escape(END_MARKER),
        "",
        readme,
        flags=re.DOTALL,
    )
    stale = sorted(
        {
            match.group(0)
            for match in re.finditer(r"\bv?0\.\d+\.\d+\b", outside)
            if match.group(0).removeprefix("v") != current_version
        }
    )
    if stale:
        raise ReadmeFactsError(
            "README contains dataset-looking versions outside the generated block: "
            + ", ".join(stale)
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Synchronize README release identity and counts.")
    parser.add_argument("--check", action="store_true", help="Fail instead of updating README.")
    args = parser.parse_args()
    changed = update_readme(check=args.check)
    if args.check:
        print("README release facts are current")
    elif changed:
        print("updated README release facts")
    else:
        print("README release facts already current")


if __name__ == "__main__":
    main()
