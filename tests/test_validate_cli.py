"""Contract tests for the task-oriented validation CLI (ADR 0012, phase 2)."""

from __future__ import annotations

import json
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
        for code in task.check_codes:
            assert code in codes, f"task {task.name} references unknown check {code}"


def test_every_task_names_a_known_gate() -> None:
    for task in TASKS.values():
        assert task.gate in TASKS, f"task {task.name} declares unknown gate {task.gate}"


def test_tier_compositions_match_agents_documentation() -> None:
    assert TASKS["tier-a"].check_codes == ("content.pages", "content.licensing", "site.unit")
    assert TASKS["tier-b"].check_codes == (
        "content.report-drift",
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
        "site.types",
        "site.e2e",
    )
    assert TASKS["all"].check_codes == TASKS["tier-c"].check_codes


def test_tiers_are_strictly_nested() -> None:
    tier_a = set(TASKS["tier-a"].check_codes)
    tier_b = set(TASKS["tier-b"].check_codes)
    tier_c = set(TASKS["tier-c"].check_codes)
    assert tier_a < tier_b < tier_c


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
                "docs/method-content-density-report.md",
                "docs/content-quality-report.md",
            ],
            "content-ready",
        ),
        (["site/public/data/content.json"], "tier-b"),
        (["site/src/App.tsx", ".github/workflows/ci.yml"], "pr-fast"),
        (["tests/test_validate_cli.py", "tests/test_pages_workflow.py"], "pr-fast"),
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


def test_content_ready_task_owns_public_indexes_without_the_full_python_suite() -> None:
    task = TASKS["content-ready"]
    assert task.gate == "content-ready"
    assert task.check_codes[0] == "content.report-drift"
    assert "content.publish-ready-tests" in task.check_codes
    assert "site.build" in task.check_codes
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
        "site.unit": "skip",
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
