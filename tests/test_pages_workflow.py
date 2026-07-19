from __future__ import annotations

import json
from pathlib import Path

PR_AND_MAIN_CONDITION = (
    "github.event_name == 'pull_request' || "
    "(github.event_name == 'push' && github.ref == 'refs/heads/main')"
)
MAIN_ONLY_CONDITION = "github.event_name == 'push' && github.ref == 'refs/heads/main'"


def _workflow_step(workflow: str, name: str) -> str:
    marker = f"      - name: {name}\n"
    start = workflow.index(marker)
    next_step = workflow.find("\n      - name: ", start + len(marker))
    end = next_step if next_step != -1 else len(workflow)
    return workflow[start:end]


def test_pages_has_one_validated_artifact_and_no_independent_workflow() -> None:
    root = Path(__file__).parents[1]
    workflows = root / ".github/workflows"
    workflow = (workflows / "ci.yml").read_text(encoding="utf-8")

    assert not (workflows / "pages.yml").exists()
    assert workflow.count("actions/upload-pages-artifact@") == 1
    assert workflow.count("actions/deploy-pages@") == 1
    assert "branches: [main]" in workflow
    assert "name: github-pages" in workflow
    assert "needs: [validate_pages_artifact, browser_e2e]" in workflow
    assert "python_compatibility:" not in workflow
    assert 'python-version: "3.13"' not in workflow
    assert "github.event_name == 'push' && github.ref == 'refs/heads/main'" in workflow


def test_browser_e2e_consumes_validated_artifacts_without_rebuilding() -> None:
    workflow = (Path(__file__).parents[1] / ".github/workflows/ci.yml").read_text(encoding="utf-8")

    assert "browser_e2e:" in workflow
    assert "needs: validate_pages_artifact" in workflow
    assert "actions/download-artifact@3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c # v8.0.1" in workflow
    assert "name: validated-site-${{ github.sha }}" in workflow
    assert "name: github-pages" in workflow
    assert "tar -xf .pages-artifact/artifact.tar -C site/dist" in workflow
    assert "npm run test:e2e:critical" in workflow
    assert "npm run test:e2e:artifact" in workflow
    assert "full_browser_regression:" in workflow
    assert 'cron: "30 17 * * *"' in workflow
    browser_job = workflow[workflow.index("  browser_e2e:\n") : workflow.index("  deploy:\n")]
    assert "npm run build" not in browser_job
    assert "actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a # v7.0.1" in workflow
    assert "if: failure()" in workflow


def test_vitest_exclude_is_shell_safe_on_linux_and_windows() -> None:
    package = json.loads(
        (Path(__file__).parents[1] / "site/package.json").read_text(encoding="utf-8")
    )

    assert "--exclude=e2e/**" in package["scripts"]["test"]


def test_validated_artifact_pipeline_contains_every_required_gate() -> None:
    workflow = (Path(__file__).parents[1] / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    required_commands = (
        "uv lock --check",
        "scripts/verify_workflow_pins.py",
        "npm --prefix site install --package-lock-only --ignore-scripts",
        "uv run --frozen pip-audit --skip-editable",
        "npm --prefix site audit --audit-level=high",
        "scripts/dependency_report.py",
        "uv run optimization-compass select-validation-task",
        'uv run optimization-compass validate "${{ steps.validation.outputs.task }}"',
        "uv run python scripts/sync_readme_facts.py --check",
        "uv run optimization-compass export-site-data --output site/public/data",
        "git diff --exit-code -- site/public/data",
        "uv run python scripts/repository_size.py --check",
        "uv run python scripts/source_health.py",
        "scripts/pages_artifact.py stamp",
        "scripts/pages_artifact.py verify-local",
        "scripts/pages_artifact.py smoke-remote",
    )

    for command in required_commands:
        assert command in workflow

    assert "Run Python smoke tests" not in workflow
    assert "tests/test_api.py" not in workflow
    assert "uv run pytest --cov" not in workflow


def test_risk_selected_validation_and_generated_drift_share_one_authority() -> None:
    workflow = (Path(__file__).parents[1] / ".github/workflows/ci.yml").read_text(encoding="utf-8")

    regeneration = _workflow_step(workflow, "Regenerate site data from the validated database")
    assert "steps.validation.outputs.task == 'tier-b'" in regeneration
    assert "steps.validation.outputs.task == 'content-ready'" in regeneration
    assert "rm -rf site/public/data" in regeneration
    assert "uv run optimization-compass export-site-data --output site/public/data" in regeneration
    assert "git diff --exit-code -- site/public/data" in regeneration

    selection = _workflow_step(workflow, "Select the authoritative validation task")
    assert 'TASK="tier-b"' in selection
    assert "select-validation-task" in selection

    selected_gate = _workflow_step(workflow, "Run the selected authoritative validation task")
    assert (
        'uv run optimization-compass validate "${{ steps.validation.outputs.task }}"'
        in selected_gate
    )
    assert "Fast-fail stale content reports" not in workflow

    drift = _workflow_step(workflow, "Verify source health and generated drift")
    assert "if: steps.validation.outputs.task == 'tier-b'" in drift
    assert (
        "git diff --exit-code -- data site/public/data src/optimization_compass/resources" in drift
    )


def test_publication_and_deployment_steps_remain_main_only() -> None:
    workflow = (Path(__file__).parents[1] / ".github/workflows/ci.yml").read_text(encoding="utf-8")

    for step_name in (
        "Stamp deployment identity",
        "Verify the exact Pages directory to upload",
        "Upload the single validated Pages artifact",
    ):
        step = _workflow_step(workflow, step_name)
        assert f"if: {MAIN_ONLY_CONDITION}" in step

    browser_job = workflow[workflow.index("  browser_e2e:\n") : workflow.index("  deploy:\n")]
    assert PR_AND_MAIN_CONDITION in browser_job
    assert "needs.validate_pages_artifact.outputs.validation_task != 'docs'" in browser_job
    assert "name: Run pull-request critical journeys" in browser_job
    assert "name: Run main critical journeys and axe scans" in browser_job

    nightly_job = workflow[
        workflow.index("  full_browser_regression:\n") : workflow.index("  deploy:\n")
    ]
    assert (
        "github.event_name == 'schedule' || github.event_name == 'workflow_dispatch'" in nightly_job
    )
    assert "npm run test:e2e:artifact" in nightly_job
    assert "playwright-nightly-failure-${{ github.sha }}" in nightly_job

    deploy_job = workflow[workflow.index("  deploy:\n") :]
    assert f"if: {MAIN_ONLY_CONDITION}" in deploy_job


def test_supply_chain_reports_are_part_of_the_validated_artifact_job() -> None:
    workflow = (Path(__file__).parents[1] / ".github/workflows/ci.yml").read_text(encoding="utf-8")

    assert "name: dependency-license-inventory" in workflow
    assert "dependency-reports/dependency-licenses.json" in workflow
    assert "if-no-files-found: error" in workflow


def test_e2e_follow_up_can_consume_the_same_generic_artifact() -> None:
    documentation = (Path(__file__).parents[1] / "docs/pages-deployment.md").read_text(
        encoding="utf-8"
    )

    assert "needs: validate_pages_artifact" in documentation
    assert "`validated-site-<commit SHA>`" in documentation
    assert "Pages-format `github-pages` artifact" in documentation
    assert "artifact.tar" in documentation
    assert "#18 owns browser-level route semantics" in documentation
