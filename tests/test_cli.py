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
