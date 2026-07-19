from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Annotated, Any

import typer
import uvicorn

from optimization_compass.agent_service import (
    DatasetVersionMismatch,
    DeterministicGuidanceService,
    UnsupportedLanguage,
)
from optimization_compass.content_authoring import (
    ContentAuthoringError,
    author_method_draft,
    prepare_content_for_pr,
    validate_content_iteration,
)
from optimization_compass.coverage import CoverageReport, diff_coverage
from optimization_compass.db import KnowledgeRepository
from optimization_compass.scaffold import (
    ScaffoldError,
    scaffold_comparison,
    scaffold_content_method,
    scaffold_gallery_case,
    scaffold_method,
    scaffold_problem_instance,
    scaffold_scenario,
)
from optimization_compass.site_export import export_site_data
from optimization_compass.validation_tasks import (
    TASKS,
    CheckResult,
    UnknownTaskError,
    ValidationCheck,
    changed_paths_from_git,
    find_repository_root,
    run_task,
    task_plan,
    validation_task_for_paths,
)

app = typer.Typer(no_args_is_help=True, help="Traceable optimization-method guidance.")
scaffold_app = typer.Typer(no_args_is_help=True, help="Create review-first authoring templates.")
content_scaffold_app = typer.Typer(no_args_is_help=True, help="Create content article templates.")
author_app = typer.Typer(no_args_is_help=True, help="Create canonical authoring drafts.")
author_content_app = typer.Typer(no_args_is_help=True, help="Author canonical content drafts.")
ready_app = typer.Typer(no_args_is_help=True, help="Prepare one change for a publishable PR.")
app.add_typer(scaffold_app, name="scaffold")
scaffold_app.add_typer(content_scaffold_app, name="content")
app.add_typer(author_app, name="author")
author_app.add_typer(author_content_app, name="content")
app.add_typer(ready_app, name="ready")
service = DeterministicGuidanceService()


def _service_parameter_error(error: ValueError) -> typer.BadParameter:
    return typer.BadParameter(str(error))


@app.command()
def capabilities(
    expected_dataset_version: Annotated[str | None, typer.Option()] = None,
) -> None:
    """Print versioned read-only service capabilities as JSON."""
    try:
        response = service.get_capabilities(expected_dataset_version=expected_dataset_version)
    except DatasetVersionMismatch as error:
        raise _service_parameter_error(error) from error
    typer.echo(response.model_dump_json(indent=2))


@app.command()
def questions(
    language: Annotated[str, typer.Option()] = "ja",
    expected_dataset_version: Annotated[str | None, typer.Option()] = None,
) -> None:
    """Print diagnostic questions as JSON."""
    try:
        response = service.list_diagnose_questions(
            language=language,
            expected_dataset_version=expected_dataset_version,
        )
    except (DatasetVersionMismatch, UnsupportedLanguage) as error:
        raise _service_parameter_error(error) from error
    rows = [question.model_dump(mode="json") for question in response.questions]
    typer.echo(json.dumps(rows, ensure_ascii=False, indent=2))


@app.command()
def recommend(
    input_file: Annotated[Path, typer.Argument(exists=True, readable=True)],
    expected_dataset_version: Annotated[str | None, typer.Option()] = None,
) -> None:
    """Recommend methods from a JSON answer file."""
    payload = json.loads(input_file.read_text(encoding="utf-8"))
    try:
        response = service.recommend_methods(
            payload,
            expected_dataset_version=expected_dataset_version,
        )
    except DatasetVersionMismatch as error:
        raise _service_parameter_error(error) from error
    typer.echo(response.recommendation.model_dump_json(indent=2))


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
    target_id: Annotated[
        str | None,
        typer.Argument(help="Optional target ID for a focused content iteration check."),
    ] = None,
    format: Annotated[str, typer.Option(help="human or json")] = "human",
    list_only: Annotated[
        bool,
        typer.Option("--list", help="Print the task's checks without executing them."),
    ] = False,
) -> None:
    """Run a documented validation task or tier (AGENTS.md, ADR 0012)."""
    if format not in {"human", "json"}:
        raise typer.BadParameter("format must be human or json")
    if target_id is not None:
        if task != "content" or list_only:
            raise typer.BadParameter("a target ID is supported only by `validate content <id>`")
        try:
            report = validate_content_iteration(target_id, root=find_repository_root())
        except ContentAuthoringError as error:
            typer.echo(f"FAIL: {error}", err=True)
            raise typer.Exit(code=1) from error
        if format == "json":
            typer.echo(report.model_dump_json(indent=2))
        else:
            typer.echo(
                f"PASS: {report.content_id} ({report.status}) at {report.canonical_path}\n"
                f"Next publish handoff: `{report.next_command}`"
            )
        return
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


@app.command("select-validation-task")
def select_validation_task(
    base_ref: Annotated[str, typer.Option(help="Git base ref used for a three-dot diff")],
    format: Annotated[str, typer.Option(help="task, human, or json")] = "human",
) -> None:
    """Select the authoritative PR validation task from changed repository paths."""
    if format not in {"task", "human", "json"}:
        raise typer.BadParameter("format must be task, human, or json")
    root = find_repository_root()
    try:
        plan = validation_task_for_paths(changed_paths_from_git(base_ref, root))
    except RuntimeError as error:
        raise typer.BadParameter(str(error)) from error
    if format == "task":
        typer.echo(plan.task)
    elif format == "json":
        typer.echo(plan.model_dump_json(indent=2))
    else:
        typer.echo(f"selected {plan.task}: {', '.join(plan.reason_codes)}")
        for path in plan.changed_paths:
            typer.echo(f"  {path}")


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


@author_content_app.command("method")
def author_content_method_command(
    content_id: Annotated[str, typer.Option("--id", help="New canonical content ID.")],
    method_id: Annotated[str, typer.Option("--method-id", help="Existing canonical method ID.")],
) -> None:
    """Create a parseable draft directly under content/methods/."""
    root = find_repository_root()
    try:
        destination = author_method_draft(content_id, method_id, root=root)
    except ContentAuthoringError as error:
        raise typer.BadParameter(str(error)) from error
    typer.echo(f"Created canonical draft: {destination.relative_to(root).as_posix()}")
    typer.echo("Next: fill the placeholders, then run `optimization-compass validate content`.")
    typer.echo(f"Publish handoff: `optimization-compass ready content {content_id}`.")


@ready_app.command("content")
def ready_content_command(
    content_id: Annotated[str, typer.Argument(help="Canonical content ID to publish.")],
    format: Annotated[str, typer.Option(help="human or json")] = "human",
) -> None:
    """Generate public indexes and prove one article is ready for a PR."""
    if format not in {"human", "json"}:
        raise typer.BadParameter("format must be human or json")
    try:
        report = prepare_content_for_pr(content_id, root=find_repository_root())
    except ContentAuthoringError as error:
        typer.echo(f"Not ready: {error}", err=True)
        raise typer.Exit(code=1) from error
    if format == "json":
        typer.echo(report.model_dump_json(indent=2))
        return
    typer.echo("Ready for PR.\n")
    typer.echo("Commit:")
    for path in report.changed_paths:
        typer.echo(f"- {path}")
    typer.echo(f"\nRequired PR gate: {report.required_pr_gate}")
    typer.echo("\nAfter merge:")
    for instruction in report.after_merge:
        typer.echo(f"- {instruction}")


@scaffold_app.command("gallery-case")
def scaffold_gallery_case_command(
    requested_id: Annotated[str, typer.Option("--id", help="Reviewed Gallery case ID.")],
    write: Annotated[bool, typer.Option(help="Write the draft files after planning.")] = False,
    output: Annotated[
        Path | None,
        typer.Option(
            "--output", file_okay=False, help="Separate draft directory (requires --write)."
        ),
    ] = None,
) -> None:
    """Plan or write a Gallery case scaffold without inventing facts."""
    _run_scaffold(scaffold_gallery_case, requested_id, write=write, output=output)


def _run_scaffold(
    builder: Callable[..., dict[str, Any]],
    requested_id: str,
    *,
    write: bool,
    output: Path | None,
) -> None:
    """Print one shared scaffold result and preserve safe error semantics."""
    try:
        manifest = builder(
            requested_id,
            write=write,
            output_directory=output,
        )
    except ScaffoldError as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(code=2) from error
    typer.echo(json.dumps(manifest, ensure_ascii=False, indent=2))


@content_scaffold_app.command("method")
def scaffold_content_method_command(
    requested_id: Annotated[str, typer.Option("--id", help="Reviewed content ID.")],
    write: Annotated[bool, typer.Option(help="Write the draft files after planning.")] = False,
    output: Annotated[
        Path | None,
        typer.Option(
            "--output", file_okay=False, help="Separate draft directory (requires --write)."
        ),
    ] = None,
) -> None:
    """Plan or write an existing-method article scaffold."""
    _run_scaffold(scaffold_content_method, requested_id, write=write, output=output)


@scaffold_app.command("problem-instance")
def scaffold_problem_instance_command(
    requested_id: Annotated[str, typer.Option("--id", help="Reviewed problem instance ID.")],
    write: Annotated[bool, typer.Option(help="Write the draft files after planning.")] = False,
    output: Annotated[
        Path | None,
        typer.Option(
            "--output", file_okay=False, help="Separate draft directory (requires --write)."
        ),
    ] = None,
) -> None:
    """Plan or write a problem-instance review scaffold."""
    _run_scaffold(scaffold_problem_instance, requested_id, write=write, output=output)


@scaffold_app.command("comparison")
def scaffold_comparison_command(
    requested_id: Annotated[str, typer.Option("--id", help="Reviewed comparison ID.")],
    write: Annotated[bool, typer.Option(help="Write the draft files after planning.")] = False,
    output: Annotated[
        Path | None,
        typer.Option(
            "--output", file_okay=False, help="Separate draft directory (requires --write)."
        ),
    ] = None,
) -> None:
    """Plan or write a comparison review scaffold."""
    _run_scaffold(scaffold_comparison, requested_id, write=write, output=output)


@scaffold_app.command("method")
def scaffold_method_command(
    requested_id: Annotated[str, typer.Option("--id", help="Reviewed canonical method ID.")],
    write: Annotated[bool, typer.Option(help="Write the draft files after planning.")] = False,
    output: Annotated[
        Path | None,
        typer.Option(
            "--output", file_okay=False, help="Separate draft directory (requires --write)."
        ),
    ] = None,
) -> None:
    """Plan or write a canonical-method review scaffold."""
    _run_scaffold(scaffold_method, requested_id, write=write, output=output)


@scaffold_app.command("scenario")
def scaffold_scenario_command(
    requested_id: Annotated[str, typer.Option("--id", help="Reviewed scenario ID.")],
    write: Annotated[bool, typer.Option(help="Write the draft files after planning.")] = False,
    output: Annotated[
        Path | None,
        typer.Option(
            "--output", file_okay=False, help="Separate draft directory (requires --write)."
        ),
    ] = None,
) -> None:
    """Plan or write a visualization-scenario review scaffold."""
    _run_scaffold(scaffold_scenario, requested_id, write=write, output=output)


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
