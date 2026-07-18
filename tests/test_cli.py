import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from optimization_compass import cli as cli_module
from optimization_compass.cli import app


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
