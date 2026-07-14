from __future__ import annotations

from pathlib import Path


def test_pages_has_one_validated_artifact_and_no_independent_workflow() -> None:
    root = Path(__file__).parents[1]
    workflows = root / ".github/workflows"
    workflow = (workflows / "ci.yml").read_text(encoding="utf-8")

    assert not (workflows / "pages.yml").exists()
    assert workflow.count("actions/upload-pages-artifact@") == 1
    assert workflow.count("actions/deploy-pages@") == 1
    assert "branches: [main]" in workflow
    assert "name: github-pages" in workflow
    assert "needs: [validate_pages_artifact, python_compatibility]" in workflow
    assert "github.event_name == 'push' && github.ref == 'refs/heads/main'" in workflow


def test_validated_artifact_pipeline_contains_every_required_gate() -> None:
    workflow = (Path(__file__).parents[1] / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    required_commands = (
        "uv run ruff check .",
        "uv lock --check",
        "scripts/verify_workflow_pins.py",
        "npm --prefix site install --package-lock-only --ignore-scripts",
        "uv run --frozen pip-audit --skip-editable",
        "npm --prefix site audit --audit-level=high",
        "scripts/dependency_report.py",
        "uv run ruff format --check .",
        "uv run mypy src",
        "uv run pytest --cov=optimization_compass --cov-report=term-missing",
        "uv run optimization-compass export-site-data --output site/public/data",
        "git diff --exit-code -- site/public/data",
        "uv run optimization-compass verify-data",
        "uv run python scripts/verify_content.py",
        "uv run python scripts/verify_licensing.py",
        "uv run python scripts/rebuild_dataset.py --stage",
        "npm run parity",
        "npm run typecheck",
        "npm test -- --run",
        "npm run build",
        "scripts/pages_artifact.py stamp",
        "scripts/pages_artifact.py verify-local",
        "scripts/pages_artifact.py smoke-remote",
    )

    for command in required_commands:
        assert command in workflow


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
    assert "downloads the `github-pages` artifact" in documentation
    assert "same workflow run" in documentation
    assert "artifact.tar" in documentation
    assert "#18 owns browser-level route semantics" in documentation
