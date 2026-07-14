from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
PIN_SCRIPT = ROOT / "scripts/verify_workflow_pins.py"
REPORT_SCRIPT = ROOT / "scripts/dependency_report.py"


def test_repository_workflows_pin_every_external_action() -> None:
    result = subprocess.run(
        [sys.executable, str(PIN_SCRIPT)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "validated immutable action pins" in result.stdout


def test_dependabot_covers_python_site_and_actions_on_grouped_weekly_schedules() -> None:
    configuration = (ROOT / ".github/dependabot.yml").read_text(encoding="utf-8")

    assert configuration.count("interval: weekly") == 3
    assert "package-ecosystem: uv" in configuration
    assert "package-ecosystem: npm" in configuration
    assert "package-ecosystem: github-actions" in configuration
    assert "directory: /site" in configuration
    for group in ("python-dependencies", "site-dependencies", "github-actions"):
        assert f"{group}:" in configuration


def test_workflow_pin_validator_rejects_mutable_refs_and_missing_versions(tmp_path: Path) -> None:
    workflow_directory = tmp_path / "workflows"
    workflow_directory.mkdir()
    (workflow_directory / "ci.yml").write_text(
        "steps:\n"
        "  - uses: actions/checkout@v7\n"
        "  - uses: actions/setup-node@" + "a" * 40 + "\n"
        "  - uses: ./local-action\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(PIN_SCRIPT), "--workflows", str(workflow_directory)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "external action is not pinned to a 40-char SHA" in result.stdout
    assert "pinned action needs an exact version comment" in result.stdout


def test_dependency_report_inventory_is_sorted_and_keeps_duplicate_lock_paths(
    tmp_path: Path,
) -> None:
    lockfile = tmp_path / "package-lock.json"
    output = tmp_path / "dependency-licenses.json"
    lockfile.write_text(
        json.dumps(
            {
                "packages": {
                    "": {"name": "site"},
                    "node_modules/zeta": {"version": "2.0.0", "license": "MIT"},
                    "node_modules/@scope/alpha": {
                        "version": "1.0.0",
                        "license": "Apache-2.0",
                        "dev": True,
                    },
                    "node_modules/parent/node_modules/zeta": {
                        "version": "1.0.0",
                        "license": "BSD-3-Clause",
                        "optional": True,
                    },
                }
            }
        ),
        encoding="utf-8",
    )

    subprocess.run(
        [
            sys.executable,
            str(REPORT_SCRIPT),
            "--node-lock",
            str(lockfile),
            "--output",
            str(output),
        ],
        cwd=ROOT,
        check=True,
    )
    report = json.loads(output.read_text(encoding="utf-8"))

    packages = report["node"]["packages"]
    assert [(package["name"], package["version"]) for package in packages] == [
        ("@scope/alpha", "1.0.0"),
        ("zeta", "1.0.0"),
        ("zeta", "2.0.0"),
    ]
    assert packages[0]["development"] is True
    assert packages[1]["optional"] is True
    assert report["python"]["package_count"] > 0
