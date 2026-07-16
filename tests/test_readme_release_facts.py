from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "scripts/sync_readme_facts.py"
README = ROOT / "README.md"


def test_readme_release_facts_are_current() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "README release facts are current" in result.stdout


def test_readme_has_one_generated_release_facts_block() -> None:
    readme = README.read_text(encoding="utf-8")

    assert readme.count("<!-- BEGIN GENERATED DATASET FACTS -->") == 1
    assert readme.count("<!-- END GENERATED DATASET FACTS -->") == 1
    assert "v0.5.1" not in readme


def test_readme_release_facts_are_reproducible_from_staged_release(tmp_path: Path) -> None:
    root = tmp_path / "repository"
    root.mkdir()
    (root / "README.md").write_text(
        "# Test\n\n"
        "<!-- BEGIN GENERATED DATASET FACTS -->\nold\n"
        "<!-- END GENERATED DATASET FACTS -->\n",
        encoding="utf-8",
    )
    staged = tmp_path / "staged"
    staged.mkdir()
    manifest = {
        "version": "0.12.0",
        "artifacts": {
            "report": "release_report.md",
            "release_identity": "release_identity.json",
        },
    }
    (staged / "release_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (staged / "release_identity.json").write_text(
        json.dumps({"dataset_version": "0.12.0", "release_date": "2026-07-17"}),
        encoding="utf-8",
    )
    table_counts = {
        "methods": 101,
        "problem_archetypes": 57,
        "implementations": 65,
        "sources": 97,
        "example_cases": 29,
        "decision_rules": 79,
        "evidence_links": 4_200,
    }
    report_rows = "\n".join(f"| `{table}` | {count:,} |" for table, count in table_counts.items())
    (staged / "release_report.md").write_text(
        "# Release report\n\n"
        "- Version: `0.12.0`\n"
        "- Release date: `2026-07-17`\n"
        "- Tables: `60`\n"
        "- Rows: `9,100`\n\n"
        f"{report_rows}\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--root",
            str(root),
            "--release-directory",
            str(staged),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "updated README release facts" in result.stdout

    readme = (root / "README.md").read_text(encoding="utf-8")
    assert "**0.12.0**" in readme
    assert "| Methods | 101 |" in readme
    assert "| Evidence links | 4,200 |" in readme
