import json
from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from optimization_compass import cli as cli_module
from optimization_compass.cli import app
from optimization_compass.content_authoring import ContentIterationReport, ReadyContentReport


def test_supported_cli_surface_remains_registered() -> None:
    result = CliRunner().invoke(app, ["--help"])

    assert result.exit_code == 0
    for command in (
        "capabilities",
        "questions",
        "recommend",
        "verify-data",
        "validate",
        "export-site-data",
        "serve",
    ):
        assert command in result.stdout
    assert "scaffold" in result.stdout
    assert "author" in result.stdout
    assert "ready" in result.stdout

    scaffold_help = CliRunner().invoke(app, ["scaffold", "--help"])
    assert scaffold_help.exit_code == 0
    for command in ("gallery-case", "problem-instance", "comparison", "method", "scenario"):
        assert command in scaffold_help.stdout
    content_help = CliRunner().invoke(app, ["scaffold", "content", "--help"])
    assert content_help.exit_code == 0
    assert "method" in content_help.stdout


def test_author_content_method_reports_the_canonical_handoff(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    destination = tmp_path / "content/methods/example.md"
    destination.parent.mkdir(parents=True)
    destination.write_text("draft", encoding="utf-8")
    monkeypatch.setattr(cli_module, "find_repository_root", lambda: tmp_path)
    monkeypatch.setattr(
        cli_module,
        "author_method_draft",
        lambda _content_id, _method_id, *, root: destination,
    )

    result = CliRunner().invoke(
        app,
        ["author", "content", "method", "--id", "example", "--method-id", "M_EXAMPLE"],
    )

    assert result.exit_code == 0
    assert "content/methods/example.md" in result.stdout
    assert "ready content example" in result.stdout


def test_ready_content_prints_the_pr_and_pages_handoff(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(cli_module, "find_repository_root", lambda: tmp_path)
    monkeypatch.setattr(
        cli_module,
        "prepare_content_for_pr",
        lambda _content_id, *, root: ReadyContentReport(
            content_id="example",
            canonical_path="content/methods/example.md",
            public_routes=("/methods/M_EXAMPLE", "/learn/example"),
            generated_paths=("site/public/data/content.json",),
            changed_paths=("content/methods/example.md", "site/public/data/content.json"),
            required_pr_gate="content-ready",
            after_merge=("GitHub Pages deploys automatically from main", "verify /#/learn/example"),
        ),
    )

    result = CliRunner().invoke(app, ["ready", "content", "example"])

    assert result.exit_code == 0
    assert "Ready for PR" in result.stdout
    assert "content-ready" in result.stdout
    assert "/#/learn/example" in result.stdout


def test_validate_content_target_uses_the_short_iteration_contract(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        cli_module,
        "validate_content_iteration",
        lambda _content_id, *, root: ContentIterationReport(
            content_id="example",
            canonical_path="content/methods/example.md",
            status="draft",
            canonical_entity_id="M_EXAMPLE",
            source_ids=(),
            next_command="optimization-compass ready content example",
        ),
    )

    result = CliRunner().invoke(app, ["validate", "content", "example"])

    assert result.exit_code == 0
    assert "PASS: example (draft)" in result.stdout
    assert "ready content example" in result.stdout


def test_gallery_scaffold_plans_without_writing(tmp_path: Path) -> None:
    result = CliRunner().invoke(app, ["scaffold", "gallery-case", "--id", "new-case"])

    assert result.exit_code == 0
    body = json.loads(result.stdout)
    assert body["contract_version"] == "1.0.0"
    assert body["task"] == "gallery-case"
    assert body["requested_id"] == "new-case"
    assert body["write"] is False
    assert body["files_to_create"] == []
    assert body["planned_authority_entry"].endswith("#cases/new-case")
    assert "site/public/data/**" in body["forbidden_outputs"]
    assert not any(tmp_path.iterdir())


def test_gallery_scaffold_writes_review_files_only_to_separate_directory(tmp_path: Path) -> None:
    output = tmp_path / "gallery-draft"
    result = CliRunner().invoke(
        app,
        ["scaffold", "gallery-case", "--id", "new-case", "--write", "--output", str(output)],
    )

    assert result.exit_code == 0
    body = json.loads(result.stdout)
    assert body["write"] is True
    assert sorted(body["files_to_create"]) == ["README.md", "gallery-case.json"]
    template = json.loads((output / "gallery-case.json").read_text(encoding="utf-8"))
    assert template["case_id"] == "new-case"
    assert template["status"] == "draft"
    assert template["source_ids"] == []
    assert "TODO" in template["title_ja"]
    readme = (output / "README.md").read_text(encoding="utf-8")
    assert "data/seeds/site_gallery.json" in readme
    assert "optimization-compass validate gallery" in readme


def test_gallery_scaffold_rejects_existing_id() -> None:
    result = CliRunner().invoke(app, ["scaffold", "gallery-case", "--id", "budget-allocation"])

    assert result.exit_code == 2
    assert "already exists" in result.output


def test_gallery_scaffold_rejects_generated_output(tmp_path: Path) -> None:
    output = Path(__file__).parents[1] / "site" / "public" / "data" / "draft"
    result = CliRunner().invoke(
        app,
        ["scaffold", "gallery-case", "--id", "new-case", "--write", "--output", str(output)],
    )

    assert result.exit_code == 2
    assert "generated and canonical paths are forbidden" in result.output


@pytest.mark.parametrize(
    ("arguments", "task", "authority", "validation", "pr_gate"),
    [
        (
            ["scaffold", "content", "method", "--id", "article-draft"],
            "content-method",
            "content/methods/<content-id>.md",
            "optimization-compass validate content",
            "optimization-compass validate tier-a",
        ),
        (
            ["scaffold", "problem-instance", "--id", "problem-draft"],
            "problem-instance",
            "src/optimization_compass/resources/problem-suite.json",
            "optimization-compass validate problem",
            "optimization-compass validate tier-c",
        ),
        (
            ["scaffold", "comparison", "--id", "comparison-draft"],
            "comparison",
            "data/seeds/site_comparisons.json",
            "optimization-compass validate comparison",
            "optimization-compass validate tier-b",
        ),
        (
            ["scaffold", "method", "--id", "method-draft"],
            "method",
            "registered dataset migration/build inputs",
            "optimization-compass validate tier-c",
            "optimization-compass validate tier-c",
        ),
        (
            ["scaffold", "scenario", "--id", "scenario-draft"],
            "scenario",
            "src/optimization_compass/visualization_scenarios.py and scenario generation code",
            "optimization-compass validate tier-c",
            "optimization-compass validate tier-c",
        ),
    ],
)
def test_review_scaffolds_plan_without_writing(
    arguments: list[str],
    task: str,
    authority: str,
    validation: str,
    pr_gate: str,
) -> None:
    result = CliRunner().invoke(app, arguments)

    assert result.exit_code == 0
    body = json.loads(result.stdout)
    assert body["contract_version"] == "1.0.0"
    assert body["task"] == task
    assert body["write"] is False
    assert body["files_to_create"] == []
    assert authority in body["editable_authorities"]
    assert body["validation"] == validation
    assert body["pr_gate"] == pr_gate
    assert "site/public/data/**" in body["forbidden_outputs"]


@pytest.mark.parametrize(
    ("arguments", "expected_files", "json_file", "id_field"),
    [
        (
            ["scaffold", "content", "method", "--id", "article-draft"],
            {"README.md", "method-article.md"},
            None,
            None,
        ),
        (
            ["scaffold", "problem-instance", "--id", "problem-draft"],
            {
                "README.md",
                "problem-instance.json",
                "problem-registry.py",
                "test-problem-instance.py",
            },
            "problem-instance.json",
            "problem_instance_id",
        ),
        (
            ["scaffold", "comparison", "--id", "comparison-draft"],
            {"README.md", "comparison.json", "test-comparison.py"},
            "comparison.json",
            "comparison_id",
        ),
        (
            ["scaffold", "method", "--id", "method-draft"],
            {"README.md", "method-record.json", "migration-plan.md"},
            "method-record.json",
            "method_id",
        ),
        (
            ["scaffold", "scenario", "--id", "scenario-draft"],
            {"README.md", "scenario-generator.py", "scenario.json", "test-scenario.py"},
            "scenario.json",
            "scenario_id",
        ),
    ],
)
def test_review_scaffolds_write_only_to_separate_draft_directory(
    tmp_path: Path,
    arguments: list[str],
    expected_files: set[str],
    json_file: str | None,
    id_field: str | None,
) -> None:
    output = tmp_path / "review-pack"
    result = CliRunner().invoke(app, [*arguments, "--write", "--output", str(output)])

    assert result.exit_code == 0
    body = json.loads(result.stdout)
    assert body["write"] is True
    assert set(body["files_to_create"]) == expected_files
    assert {path.name for path in output.iterdir()} == expected_files
    readme = (output / "README.md").read_text(encoding="utf-8")
    assert "docs/knowledge-change-checklist.md" in readme
    assert "site/public/data/**" in readme
    if json_file is not None and id_field is not None:
        payload = json.loads((output / json_file).read_text(encoding="utf-8"))
        assert payload[id_field].endswith("draft")


def test_content_method_scaffold_keeps_frontmatter_parseable_and_summary_aligned(
    tmp_path: Path,
) -> None:
    output = tmp_path / "article-draft"
    result = CliRunner().invoke(
        app,
        [
            "scaffold",
            "content",
            "method",
            "--id",
            "article-draft",
            "--write",
            "--output",
            str(output),
        ],
    )

    assert result.exit_code == 0
    article = (output / "method-article.md").read_text(encoding="utf-8")
    _, frontmatter, body = article.split("---", 2)
    metadata = yaml.safe_load(frontmatter)
    first_paragraph = body.strip().split("\n\n", 1)[0]
    assert metadata["status"] == "draft"
    assert metadata["summary"] == first_paragraph
    assert metadata["method_id"].startswith("TODO:")


def test_cli_capabilities_uses_the_versioned_service_contract() -> None:
    result = CliRunner().invoke(app, ["capabilities"])

    assert result.exit_code == 0
    body = json.loads(result.stdout)
    assert body["metadata"]["dataset_version"]
    assert body["capabilities"]["read_only"] is True


def test_cli_questions_uses_shared_service_and_keeps_list_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = cli_module.service.list_diagnose_questions
    calls: list[str] = []

    def tracked(*, language: str, expected_dataset_version: str | None = None):
        calls.append(language)
        return original(
            language=language,
            expected_dataset_version=expected_dataset_version,
        )

    monkeypatch.setattr(cli_module.service, "list_diagnose_questions", tracked)

    result = CliRunner().invoke(app, ["questions", "--language", "en"])

    assert result.exit_code == 0
    assert isinstance(json.loads(result.stdout), list)
    assert calls == ["en"]


def test_cli_recommend_uses_shared_service_and_keeps_recommendation_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = cli_module.service.recommend_methods
    calls: list[object] = []

    def tracked(payload: object, *, expected_dataset_version: str | None = None):
        calls.append(payload)
        return original(
            payload,  # type: ignore[arg-type]
            expected_dataset_version=expected_dataset_version,
        )

    monkeypatch.setattr(cli_module.service, "recommend_methods", tracked)
    request_path = Path(__file__).parents[1] / "examples/binary_linear.json"

    result = CliRunner().invoke(app, ["recommend", str(request_path)])

    assert result.exit_code == 0
    assert "metadata" not in json.loads(result.stdout)
    assert len(calls) == 1
