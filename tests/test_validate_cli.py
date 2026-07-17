"""Contract tests for the task-oriented validation CLI (ADR 0012, phase 2)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

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
        "python.lint",
        "python.format",
        "python.types",
        "python.tests",
        "data.integrity",
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
