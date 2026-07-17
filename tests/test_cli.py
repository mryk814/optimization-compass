from typer.testing import CliRunner

from optimization_compass.cli import app


def test_supported_cli_surface_remains_registered() -> None:
    result = CliRunner().invoke(app, ["--help"])

    assert result.exit_code == 0
    for command in (
        "questions",
        "recommend",
        "verify-data",
        "validate",
        "export-site-data",
        "serve",
    ):
        assert command in result.stdout
