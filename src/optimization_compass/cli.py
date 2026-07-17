from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer
import uvicorn

from optimization_compass.coverage import CoverageReport, diff_coverage
from optimization_compass.db import KnowledgeRepository
from optimization_compass.engine import RecommendationEngine
from optimization_compass.models import RecommendationRequest
from optimization_compass.site_export import export_site_data
from optimization_compass.validation_tasks import (
    TASKS,
    CheckResult,
    UnknownTaskError,
    ValidationCheck,
    find_repository_root,
    run_task,
    task_plan,
)

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


@app.command()
def validate(
    task: Annotated[
        str,
        typer.Argument(
            help="Validation task: " + ", ".join(sorted(TASKS)),
        ),
    ],
    format: Annotated[str, typer.Option(help="human or json")] = "human",
    list_only: Annotated[
        bool,
        typer.Option("--list", help="Print the task's checks without executing them."),
    ] = False,
) -> None:
    """Run a documented validation task or tier (AGENTS.md, ADR 0012)."""
    if format not in {"human", "json"}:
        raise typer.BadParameter("format must be human or json")
    try:
        plan = task_plan(task)
    except UnknownTaskError as error:
        raise typer.BadParameter(str(error)) from error

    if list_only:
        if format == "json":
            typer.echo(plan.model_dump_json(indent=2))
        else:
            typer.echo(f"task {plan.task} (PR gate: {plan.gate})")
            for check in plan.checks:
                typer.echo(f"  {check.code}: {check.display_command}")
        return

    root = find_repository_root()
    if format == "json":
        result = run_task(task, root, capture=True)
        typer.echo(result.model_dump_json(indent=2))
    else:
        typer.echo(f"task {plan.task} (PR gate: {plan.gate}) in {root}")

        def _announce(check: ValidationCheck) -> None:
            typer.echo(f"\n=== {check.code}: {check.display_command}")

        def _report(outcome: CheckResult) -> None:
            typer.echo(f"{outcome.status.upper():>5}  {outcome.code} ({outcome.duration_seconds}s)")
            if outcome.status not in {"pass", "skip"}:
                typer.echo(f"next action: {outcome.next_action}")

        result = run_task(task, root, capture=False, on_start=_announce, on_finish=_report)
        typer.echo(f"\nresult: {result.status} (task {result.task}, PR gate {result.gate})")
        if result.task != result.gate and result.status == "pass":
            typer.echo(
                f"note: {result.task} is an iteration subset;"
                f" run `optimization-compass validate {result.gate}` before the PR."
            )
    if result.status != "pass":
        raise typer.Exit(code=1)


@app.command("export-site-data")
def export_site_data_command(
    output: Annotated[Path, typer.Option(help="Directory for generated site data.")],
) -> None:
    """Export deterministic, versioned JSON for the static atlas."""
    manifest = export_site_data(output, KnowledgeRepository())
    typer.echo(manifest.model_dump_json(indent=2))


@app.command("coverage-diff")
def coverage_diff_command(
    before: Annotated[Path, typer.Option(exists=True, readable=True)],
    after: Annotated[Path, typer.Option(exists=True, readable=True)],
    format: Annotated[str, typer.Option(help="json or markdown")] = "json",
) -> None:
    """Compare two explicit coverage snapshots for release notes."""
    if format not in {"json", "markdown"}:
        raise typer.BadParameter("format must be json or markdown")
    delta = diff_coverage(
        CoverageReport.model_validate_json(before.read_text(encoding="utf-8")),
        CoverageReport.model_validate_json(after.read_text(encoding="utf-8")),
    )
    if format == "json":
        typer.echo(delta.model_dump_json(indent=2))
        return
    typer.echo(
        f"## Coverage delta ({delta.before_dataset_version} → {delta.after_dataset_version})\n\n"
        f"- Available: {delta.available_delta:+d}\n"
        f"- Added expectations: {len(delta.added_expectation_ids)}\n"
        f"- Removed expectations: {len(delta.removed_expectation_ids)}\n"
        f"- Status transitions: {sum(delta.transitions.values())}"
    )


@app.command()
def serve(
    host: Annotated[str, typer.Option()] = "127.0.0.1",
    port: Annotated[int, typer.Option(min=1, max=65535)] = 8000,
    reload: Annotated[bool, typer.Option()] = False,
) -> None:
    """Run the REST API, OpenAPI docs, and Atlas migration landing page."""
    uvicorn.run("optimization_compass.api:app", host=host, port=port, reload=reload)


if __name__ == "__main__":
    app()
