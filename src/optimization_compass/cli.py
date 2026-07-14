from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer
import uvicorn

from optimization_compass.db import KnowledgeRepository
from optimization_compass.engine import RecommendationEngine
from optimization_compass.models import RecommendationRequest
from optimization_compass.site_export import export_site_data

app = typer.Typer(no_args_is_help=True, help="Traceable optimization-method guidance.")


@app.command()
def questions(language: Annotated[str, typer.Option()] = "ja") -> None:
    """Print diagnostic questions as JSON."""
    rows = KnowledgeRepository().questions(language)
    typer.echo(json.dumps(rows, ensure_ascii=False, indent=2))


@app.command()
def recommend(
    input_file: Annotated[Path, typer.Argument(exists=True, readable=True)],
) -> None:
    """Recommend methods from a JSON answer file."""
    payload = json.loads(input_file.read_text(encoding="utf-8"))
    request = RecommendationRequest.model_validate(payload)
    result = RecommendationEngine().recommend(request)
    typer.echo(result.model_dump_json(indent=2))


@app.command("verify-data")
def verify_data() -> None:
    """Run SQLite and release-gate checks."""
    result = KnowledgeRepository().verify()
    typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
    if not result["ok"]:
        raise typer.Exit(code=1)


@app.command("export-site-data")
def export_site_data_command(
    output: Annotated[Path, typer.Option(help="Directory for generated site data.")],
) -> None:
    """Export deterministic, versioned JSON for the static atlas."""
    manifest = export_site_data(output, KnowledgeRepository())
    typer.echo(manifest.model_dump_json(indent=2))


@app.command()
def serve(
    host: Annotated[str, typer.Option()] = "127.0.0.1",
    port: Annotated[int, typer.Option(min=1, max=65535)] = 8000,
    reload: Annotated[bool, typer.Option()] = False,
) -> None:
    """Run the API and browser UI."""
    uvicorn.run("optimization_compass.api:app", host=host, port=port, reload=reload)


if __name__ == "__main__":
    app()
