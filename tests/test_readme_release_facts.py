from __future__ import annotations

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
