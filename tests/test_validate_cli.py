"""Contract tests for the task-oriented validation CLI (ADR 0012, phase 2)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

from optimization_compass import cli as cli_module
from optimization_compass import validation_tasks
from optimization_compass.cli import app
from optimization_compass.validation_tasks import (
    CHECKS,
    CONTRACT_VERSION,
    TASKS,
    CheckResult,
    UnknownTaskError,
    ValidationCheck,
    find_repository_root,
    run_task,
    task_plan,
    validation_task_for_paths,
)

runner = CliRunner()


def test_check_codes_are_unique_and_resolvable() -> None:
    codes = [check.code for check in CHECKS]
    assert len(codes) == len(set(codes))
    for task in TASKS.values():
        assert len(task.check_codes) == len(set(task.check_codes))
        for code in task.check_codes:
            assert code in codes, f"task {task.name} references unknown check {code}"


def test_every_task_names_a_known_gate() -> None:
    for task in TASKS.values():
        assert task.gate in TASKS, f"task {task.name} declares unknown gate {task.gate}"


def test_tier_compositions_keep_the_required_checks() -> None:
    assert TASKS["tier-a"].check_codes == ("content.pages", "content.licensing")
    assert TASKS["tier-b"].check_codes == (
        "python.lint",
        "python.format",
        "python.types",
        "python.tests",
        "data.integrity",
        "data.manifest",
        "content.pages",
        "content.licensing",
        "data.stage",
        "site.parity",
        "site.unit",
        "site.build",
    )
    assert TASKS["tier-c"].check_codes == (
        *TASKS["tier-b"].check_codes,
        "site.e2e-artifact",
    )
    assert TASKS["all"].check_codes == TASKS["tier-c"].check_codes


def test_tiers_are_strictly_nested() -> None:
    tier_a = set(TASKS["tier-a"].check_codes)
    tier_b = set(TASKS["tier-b"].check_codes)
    tier_c = set(TASKS["tier-c"].check_codes)
    assert tier_a < tier_b < tier_c


@pytest.mark.parametrize("task", ["tier-c", "all"])
@pytest.mark.parametrize("build_succeeds", [True, False])
def test_browser_gate_requires_this_runs_successful_build(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, task: str, build_succeeds: bool
) -> None:
    artifact = tmp_path / "site/dist/index.html"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("stale artifact", encoding="utf-8")
    commands: list[list[str]] = []
    original_execute = validation_tasks.execute_check

    def fake_subprocess(argv: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        assert kwargs["cwd"] == tmp_path
        commands.append(argv[1:])
        if argv[-1] == "build":
            if not build_succeeds:
                return subprocess.CompletedProcess(argv, 1, "", "build failed")
            artifact.write_text("fresh artifact", encoding="utf-8")
        else:
            assert argv[-1] == "test:e2e:artifact"
            assert artifact.read_text(encoding="utf-8") == "fresh artifact"
        return subprocess.CompletedProcess(argv, 0, "", "")

    def execute(check: ValidationCheck, root: Path, capture: bool) -> CheckResult:
        if check.code.startswith("site.") and check.code not in {"site.unit", "site.parity"}:
            return original_execute(check, root, capture)
        return CheckResult(
            code=check.code,
            status="pass",
            command=check.display_command,
            duration_seconds=0.0,
            message="",
            next_action="",
        )

    monkeypatch.setattr(validation_tasks.shutil, "which", lambda _name: "/tools/npm")
    monkeypatch.setattr(validation_tasks.subprocess, "run", fake_subprocess)
    monkeypatch.setattr(validation_tasks, "execute_check", execute)
    result = run_task(task, tmp_path, capture=True)
    expected_commands = [["--prefix", "site", "run", "build"]]
    if build_succeeds:
        expected_commands.append(["--prefix", "site", "run", "test:e2e:artifact"])
    assert commands == expected_commands
    assert result.status == ("pass" if build_succeeds else "fail")
    assert result.checks[-1].status == ("pass" if build_succeeds else "skip")


def test_independent_browser_check_still_builds_and_build_still_typechecks() -> None:
    checks = {check.code: check for check in CHECKS}
    assert checks["site.e2e"].command == ("{npm}", "--prefix", "site", "run", "test:e2e")
    scripts = json.loads(
        (Path(__file__).parents[1] / "site/package.json").read_text(encoding="utf-8")
    )["scripts"]
    assert "--exclude=e2e/**" in scripts["test"]
    assert scripts["build"] == "npm run typecheck && vite build"
    assert scripts["test:e2e"] == "npm run build && npm run test:e2e:artifact"
    assert scripts["test:e2e:artifact"] == "playwright test"


@pytest.mark.parametrize("task", ["tier-c", "all"])
def test_cli_plan_exposes_the_commands_used_for_artifact_reuse(task: str) -> None:
    result = runner.invoke(app, ["validate", task, "--list", "--format", "json"])
    assert result.exit_code == 0
    checks = json.loads(result.stdout)["checks"]
    assert [check["code"] for check in checks][-2:] == ["site.build", "site.e2e-artifact"]
    assert checks[-2]["command"] == ["{npm}", "--prefix", "site", "run", "build"]
    assert checks[-1]["command"] == ["{npm}", "--prefix", "site", "run", "test:e2e:artifact"]


def test_main_fast_keeps_the_publishable_site_gate_without_full_python_regression() -> None:
    task = TASKS["main-fast"]
    assert task.check_codes == TASKS["pr-fast"].check_codes
    assert "site.build" in task.check_codes
    assert "python.tests" not in task.check_codes


def test_problem_task_gate_is_tier_c() -> None:
    assert TASKS["problem"].gate == "tier-c"


@pytest.mark.parametrize(
    ("paths", "expected"),
    [
        (["README.md", "docs/pages-deployment.md"], "docs"),
        (["content/methods/example.md"], "tier-a"),
        (
            [
                "content/methods/example.md",
                "site/public/data/content.json",
                "site/public/media/example-figure.png",
                "docs/method-content-density-report.md",
                "docs/content-quality-report.md",
            ],
            "content-ready",
        ),
        (["site/public/data/content.json"], "tier-b"),
        (["site/src/App.tsx", ".github/workflows/ci.yml"], "pr-fast"),
        (["tests/test_validate_cli.py", "tests/test_pages_checkpoint.py"], "pr-fast"),
        (
            [
                "scripts/pages_checkpoint.py",
                "src/optimization_compass/validation_tasks.py",
                "tests/test_pages_checkpoint.py",
            ],
            "pr-fast",
        ),
        (["tests/test_engine.py"], "tier-b"),
        (["src/optimization_compass/engine.py"], "tier-b"),
        (["data/seeds/site_gallery.json"], "tier-b"),
        (["unclassified.file"], "tier-b"),
    ],
)
def test_changed_paths_select_the_smallest_safe_pr_gate(paths: list[str], expected: str) -> None:
    plan = validation_task_for_paths(paths)
    assert plan.task == expected
    assert plan.gate == expected


def test_mixed_changes_escalate_to_the_highest_required_gate() -> None:
    plan = validation_task_for_paths(
        ["content/methods/example.md", "site/src/App.tsx", "src/optimization_compass/engine.py"]
    )
    assert plan.task == "tier-b"
    assert set(plan.reason_codes) == {
        "backend_or_data_authority",
        "content_authority",
        "site_or_repository_contract",
    }


@pytest.mark.parametrize(
    ("deleted_paths", "expected_task"),
    [
        (["content/methods/removed.md"], "tier-a"),
        (["src/optimization_compass/removed.py"], "tier-b"),
        (["content/methods/removed.md", "src/optimization_compass/removed.py"], "tier-b"),
    ],
)
def test_deleted_authority_paths_are_included_in_git_task_selection(
    tmp_path: Path, deleted_paths: list[str], expected_task: str
) -> None:
    def git(*args: str) -> str:
        return subprocess.run(
            ["git", *args], cwd=tmp_path, capture_output=True, text=True, check=True
        ).stdout.strip()

    git("init")
    for path in deleted_paths:
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("tracked input", encoding="utf-8")
    git("add", ".")
    identity = ("-c", "user.name=Validation Test", "-c", "user.email=test@example.invalid")
    git(*identity, "commit", "-m", "base")
    base = git("rev-parse", "HEAD")
    for path in deleted_paths:
        (tmp_path / path).unlink()
    git("add", "-u")
    git(*identity, "commit", "-m", "delete authority inputs")
    paths = validation_tasks.changed_paths_from_git(base, tmp_path)
    assert set(paths) == set(deleted_paths)
    assert validation_task_for_paths(paths).task == expected_task


def test_repository_contract_gate_runs_publication_checkpoint_tests() -> None:
    check = next(check for check in CHECKS if check.code == "repository.contract-tests")

    assert "tests/test_pages_checkpoint.py" in check.command
    assert check.command == (
        "{python}",
        "-m",
        "pytest",
        "tests/test_validate_cli.py",
        "tests/test_pages_checkpoint.py",
    )


def test_content_ready_task_owns_public_indexes_without_the_full_python_suite() -> None:
    task = TASKS["content-ready"]
    assert task.gate == "content-ready"
    assert task.check_codes == (
        "content.pages",
        "content.licensing",
        "content.publish-ready-tests",
    )
    assert "content.publish-ready-tests" in task.check_codes
    assert "site.build" not in task.check_codes
    assert "content.report-drift" not in task.check_codes
    assert "python.tests" not in task.check_codes


def test_select_validation_task_cli_is_machine_readable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        cli_module,
        "changed_paths_from_git",
        lambda _base_ref, _root: ["site/src/App.tsx"],
    )
    result = runner.invoke(
        app,
        ["select-validation-task", "--base-ref", "origin/main", "--format", "json"],
    )
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["task"] == "pr-fast"
    assert payload["changed_paths"] == ["site/src/App.tsx"]


def test_manifest_task_is_a_focused_tier_b_check() -> None:
    assert TASKS["manifest"].check_codes == ("data.manifest",)
    assert TASKS["manifest"].gate == "tier-b"


def test_content_report_preflight_has_a_stable_machine_readable_rule_code() -> None:
    task = TASKS["content-reports"]
    assert task.check_codes == ("content.report-drift",)
    assert task.gate == "tier-b"

    result = runner.invoke(
        app,
        ["validate", "content-reports", "--list", "--format", "json"],
    )
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["task"] == "content-reports"
    assert payload["gate"] == "tier-b"
    assert [check["code"] for check in payload["checks"]] == ["content.report-drift"]


def test_manifest_validation_returns_machine_readable_result() -> None:
    result = runner.invoke(app, ["validate", "manifest", "--format", "json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["contract_version"] == CONTRACT_VERSION
    assert payload["task"] == "manifest"
    assert payload["status"] == "pass"
    assert payload["checks"][0]["code"] == "data.manifest"
    assert payload["checks"][0]["status"] == "pass"
    assert '"schema_migrations"' in payload["checks"][0]["message"]


def test_unknown_task_raises_and_exits_with_usage_error() -> None:
    with pytest.raises(UnknownTaskError):
        task_plan("no-such-task")

    result = runner.invoke(app, ["validate", "no-such-task", "--list"])
    assert result.exit_code == 2


def test_list_outputs_machine_readable_plan() -> None:
    result = runner.invoke(app, ["validate", "tier-b", "--list", "--format", "json"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["contract_version"] == CONTRACT_VERSION
    assert payload["task"] == "tier-b"
    assert payload["gate"] == "tier-b"
    assert [check["code"] for check in payload["checks"]] == list(TASKS["tier-b"].check_codes)
    for check in payload["checks"]:
        assert check["next_action"]
        assert check["description"]


def test_commands_are_platform_neutral() -> None:
    for check in CHECKS:
        if check.command is None:
            continue
        assert check.command[0] in {"{python}", "{npm}"}, check.code
        for token in check.command:
            assert "/tmp" not in token and token != "make", check.code


def test_find_repository_root_locates_checkout() -> None:
    root = find_repository_root(Path(__file__).parent)
    assert (root / "pyproject.toml").is_file()
    assert (root / "scripts" / "verify_content.py").is_file()


def test_run_task_stops_after_first_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    executed: list[str] = []

    def fake_execute(check: ValidationCheck, root: Path, capture: bool) -> CheckResult:
        executed.append(check.code)
        return CheckResult(
            code=check.code,
            status="fail" if check.code == "content.licensing" else "pass",
            command=check.display_command,
            duration_seconds=0.0,
            message="",
            next_action=check.next_action,
        )

    monkeypatch.setattr(validation_tasks, "execute_check", fake_execute)
    result = run_task("tier-a", Path.cwd())

    assert result.status == "fail"
    assert executed == ["content.pages", "content.licensing"]
    statuses = {check.code: check.status for check in result.checks}
    assert statuses == {
        "content.pages": "pass",
        "content.licensing": "fail",
    }


def test_cli_reports_failure_with_exit_code_one(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_execute(check: ValidationCheck, root: Path, capture: bool) -> CheckResult:
        return CheckResult(
            code=check.code,
            status="fail",
            command=check.display_command,
            duration_seconds=0.0,
            message="synthetic failure",
            next_action=check.next_action,
        )

    monkeypatch.setattr(validation_tasks, "execute_check", fake_execute)
    result = runner.invoke(app, ["validate", "content", "--format", "json"])

    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert payload["status"] == "fail"
    assert payload["checks"][0]["status"] == "fail"
    assert payload["checks"][0]["next_action"]
