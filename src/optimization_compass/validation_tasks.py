"""Task-oriented validation registry and runner (ADR 0012, phase 2).

This module is the single shared authority for which checks compose each
validation task and tier. The CLI (``optimization-compass validate``), the
Makefile convenience targets, and repository skills all call this registry
instead of maintaining their own command lists.

Checks orchestrate the repository's existing validation entry points
(``scripts/verify_content.py``, ``scripts/rebuild_dataset.py``, ruff, mypy,
pytest, npm scripts); they never re-implement repository rules.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict

CONTRACT_VERSION = "1.0.0"

_PYTHON_TOKEN = "{python}"
_NPM_TOKEN = "{npm}"

_OUTPUT_TAIL_CHARACTERS = 4_000


class _FrozenModel(BaseModel):
    model_config = ConfigDict(frozen=True)


class ValidationCheck(_FrozenModel):
    """One named check with a stable rule code.

    ``command`` uses symbolic ``{python}`` / ``{npm}`` tokens so the registry
    stays platform independent; the runner resolves them at execution time.
    A check without a command runs in process (see ``_CALLABLE_CHECKS``).
    """

    code: str
    description: str
    next_action: str
    command: tuple[str, ...] | None = None

    @property
    def display_command(self) -> str:
        if self.command is None:
            return "(in-process)"
        return " ".join(self.command)


class ValidationTask(_FrozenModel):
    name: str
    description: str
    gate: str
    check_codes: tuple[str, ...]


class CheckResult(_FrozenModel):
    code: str
    status: Literal["pass", "fail", "skip", "error"]
    command: str
    duration_seconds: float
    message: str
    next_action: str


class TaskResult(_FrozenModel):
    contract_version: str
    task: str
    gate: str
    status: Literal["pass", "fail"]
    checks: tuple[CheckResult, ...]


class TaskPlan(_FrozenModel):
    contract_version: str
    task: str
    gate: str
    checks: tuple[ValidationCheck, ...]


class ChangeValidationPlan(_FrozenModel):
    contract_version: str
    task: str
    gate: str
    changed_paths: tuple[str, ...]
    reason_codes: tuple[str, ...]


CHECKS: tuple[ValidationCheck, ...] = (
    ValidationCheck(
        code="python.lint",
        description="Ruff lint over the repository.",
        next_action="Fix the reported lint findings (uv run ruff check . --fix helps).",
        command=(_PYTHON_TOKEN, "-m", "ruff", "check", "."),
    ),
    ValidationCheck(
        code="python.format",
        description="Ruff formatting check.",
        next_action="Run uv run ruff format . and re-check.",
        command=(_PYTHON_TOKEN, "-m", "ruff", "format", "--check", "."),
    ),
    ValidationCheck(
        code="python.types",
        description="Mypy strict type check of the package.",
        next_action="Fix the reported type errors in src/optimization_compass.",
        command=(_PYTHON_TOKEN, "-m", "mypy", "src"),
    ),
    ValidationCheck(
        code="python.tests",
        description="Full Python test suite.",
        next_action="Fix the failing tests; do not weaken repository invariants.",
        command=(_PYTHON_TOKEN, "-m", "pytest"),
    ),
    ValidationCheck(
        code="python.export-tests",
        description="Focused site-export contract tests (Gallery, comparisons).",
        next_action="Fix the seed entry named in the failure; the site UI is generated from data.",
        command=(_PYTHON_TOKEN, "-m", "pytest", "tests/test_site_export.py"),
    ),
    ValidationCheck(
        code="python.problem-tests",
        description="Focused problem-instance and engine tests.",
        next_action=(
            "Keep problem-suite.json and problem_registry.py registry keys in exact"
            " correspondence and fix the failing evaluator behavior."
        ),
        command=(
            _PYTHON_TOKEN,
            "-m",
            "pytest",
            "tests/test_problem_instances.py",
            "tests/test_engine.py",
        ),
    ),
    ValidationCheck(
        code="repository.contract-tests",
        description="Validation-registry and workflow contract tests.",
        next_action="Fix the validation authority or workflow contract; do not duplicate gates.",
        command=(
            _PYTHON_TOKEN,
            "-m",
            "pytest",
            "tests/test_validate_cli.py",
            "tests/test_pages_workflow.py",
        ),
    ),
    ValidationCheck(
        code="content.publish-ready-tests",
        description="Published content, density-report, and authoring-contract tests.",
        next_action="Complete the target article and regenerate it through `ready content`.",
        command=(
            _PYTHON_TOKEN,
            "-m",
            "pytest",
            "tests/test_content_models.py",
            "tests/test_method_content_density.py",
            "tests/test_content_authoring.py",
        ),
    ),
    ValidationCheck(
        code="content.pages",
        description="Content frontmatter, relations, and generated-index consistency.",
        next_action="Fix the reported content/** page; never edit generated site data.",
        command=(_PYTHON_TOKEN, "scripts/verify_content.py"),
    ),
    ValidationCheck(
        code="content.licensing",
        description="License notices and source-record checks.",
        next_action="Follow docs/licensing.md and NOTICE for the flagged material.",
        command=(_PYTHON_TOKEN, "scripts/verify_licensing.py"),
    ),
    ValidationCheck(
        code="data.integrity",
        description="SQLite and release-gate checks (verify-data).",
        next_action=(
            "Inspect the failing CHK checks and fix canonical inputs;"
            " never edit knowledge.sqlite directly."
        ),
        command=None,
    ),
    ValidationCheck(
        code="data.manifest",
        description="Declarative migration and specialized-input manifest validation.",
        next_action=(
            "Update data/build-manifest.json from the canonical repository inputs;"
            " do not edit generated release artifacts."
        ),
        command=None,
    ),
    ValidationCheck(
        code="data.stage",
        description="Deterministic staged dataset rebuild.",
        next_action=(
            "Inspect the staged-build error; unexpected unrelated generated diffs"
            " are a stop signal (AGENTS.md)."
        ),
        command=(_PYTHON_TOKEN, "scripts/rebuild_dataset.py", "--stage"),
    ),
    ValidationCheck(
        code="site.unit",
        description="Site unit tests.",
        next_action="Fix the failing site test; check npm --prefix site test output.",
        command=(_NPM_TOKEN, "--prefix", "site", "test", "--", "--run"),
    ),
    ValidationCheck(
        code="site.parity",
        description="Python/TypeScript recommendation parity.",
        next_action=(
            "Regenerate parity fixtures from canonical inputs instead of editing fixture text."
        ),
        command=(_NPM_TOKEN, "--prefix", "site", "run", "parity"),
    ),
    ValidationCheck(
        code="site.build",
        description="Production site build.",
        next_action="Fix the reported build error under site/.",
        command=(_NPM_TOKEN, "--prefix", "site", "run", "build"),
    ),
    ValidationCheck(
        code="site.types",
        description="Site TypeScript type check.",
        next_action="Fix the reported type errors under site/src.",
        command=(_NPM_TOKEN, "--prefix", "site", "run", "typecheck"),
    ),
    ValidationCheck(
        code="site.e2e",
        description="Browser E2E and accessibility tests.",
        next_action="Inspect the Playwright report under site/ for the failing journey.",
        command=(_NPM_TOKEN, "--prefix", "site", "run", "test:e2e"),
    ),
)

_CHECKS_BY_CODE: dict[str, ValidationCheck] = {check.code: check for check in CHECKS}

_TIER_A_CODES: tuple[str, ...] = ("content.pages", "content.licensing", "site.unit")
_TIER_B_CODES: tuple[str, ...] = (
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
_TIER_C_CODES: tuple[str, ...] = (*_TIER_B_CODES, "site.types", "site.e2e")
_PR_FAST_CODES: tuple[str, ...] = (
    "python.lint",
    "python.format",
    "python.types",
    "repository.contract-tests",
    "content.pages",
    "content.licensing",
    "site.unit",
    "site.build",
)
_CONTENT_READY_CODES: tuple[str, ...] = (
    "content.pages",
    "content.licensing",
    "content.publish-ready-tests",
    "site.unit",
    "site.build",
)

TASKS: dict[str, ValidationTask] = {
    task.name: task
    for task in (
        ValidationTask(
            name="tier-a",
            description="AGENTS.md Tier A: prose or existing-content correction.",
            gate="tier-a",
            check_codes=_TIER_A_CODES,
        ),
        ValidationTask(
            name="tier-b",
            description=(
                "AGENTS.md Tier B: Gallery, comparison, relations, or canonical"
                " data using existing contracts."
            ),
            gate="tier-b",
            check_codes=_TIER_B_CODES,
        ),
        ValidationTask(
            name="tier-c",
            description=(
                "AGENTS.md Tier C: executable problem, scenario, generator,"
                " renderer, schema, or release change."
            ),
            gate="tier-c",
            check_codes=_TIER_C_CODES,
        ),
        ValidationTask(
            name="all",
            description="The authoritative full gate (identical to tier-c).",
            gate="all",
            check_codes=_TIER_C_CODES,
        ),
        ValidationTask(
            name="docs",
            description="Fast documentation and repository-policy contract checks.",
            gate="docs",
            check_codes=("repository.contract-tests",),
        ),
        ValidationTask(
            name="pr-fast",
            description="Fast PR gate for site, E2E, workflow, and test-contract changes.",
            gate="pr-fast",
            check_codes=_PR_FAST_CODES,
        ),
        ValidationTask(
            name="content-ready",
            description="Publish-ready gate for content plus deterministic public indexes.",
            gate="content-ready",
            check_codes=_CONTENT_READY_CODES,
        ),
        ValidationTask(
            name="content",
            description="Iteration checks for content/** article work. PR gate: tier-a.",
            gate="tier-a",
            check_codes=_TIER_A_CODES,
        ),
        ValidationTask(
            name="gallery",
            description="Iteration checks for Gallery case edits. PR gate: tier-b.",
            gate="tier-b",
            check_codes=("content.pages", "data.integrity", "python.export-tests"),
        ),
        ValidationTask(
            name="comparison",
            description="Iteration checks for comparison edits. PR gate: tier-b.",
            gate="tier-b",
            check_codes=("content.pages", "python.export-tests", "site.parity"),
        ),
        ValidationTask(
            name="problem",
            description="Iteration checks for executable problem instances. PR gate: tier-c.",
            gate="tier-c",
            check_codes=("python.lint", "python.types", "python.problem-tests"),
        ),
        ValidationTask(
            name="manifest",
            description="Build-input manifest and migration registration checks. PR gate: tier-b.",
            gate="tier-b",
            check_codes=("data.manifest",),
        ),
    )
}


class UnknownTaskError(ValueError):
    def __init__(self, task: str) -> None:
        super().__init__(f"unknown validation task {task!r}; available: {', '.join(sorted(TASKS))}")


def task_plan(task_name: str) -> TaskPlan:
    task = TASKS.get(task_name)
    if task is None:
        raise UnknownTaskError(task_name)
    return TaskPlan(
        contract_version=CONTRACT_VERSION,
        task=task.name,
        gate=task.gate,
        checks=tuple(_CHECKS_BY_CODE[code] for code in task.check_codes),
    )


def validation_task_for_paths(paths: list[str] | tuple[str, ...]) -> ChangeValidationPlan:
    """Select the smallest authoritative PR gate for a set of repository paths."""
    normalized_paths: set[str] = set()
    for raw_path in paths:
        path = raw_path.replace("\\", "/")
        normalized_paths.add(path[2:] if path.startswith("./") else path)
    normalized = tuple(sorted(normalized_paths))
    content_paths = {path for path in normalized if path.startswith("content/")}
    generated_content_paths = {
        path
        for path in normalized
        if path.startswith("site/public/data/") or path == "docs/method-content-density-report.md"
    }
    content_lane_support_paths = {
        path
        for path in normalized
        if path.startswith("docs/") or path in {"README.md", "CONTRIBUTING.md", "CHANGELOG.md"}
    }
    if (
        content_paths
        and generated_content_paths
        and set(normalized) <= content_paths | generated_content_paths | content_lane_support_paths
    ):
        return ChangeValidationPlan(
            contract_version=CONTRACT_VERSION,
            task="content-ready",
            gate=TASKS["content-ready"].gate,
            changed_paths=normalized,
            reason_codes=("published_content_with_generated_indexes",),
        )
    task = "docs"
    reasons: set[str] = set()
    for path in normalized:
        if (
            path.startswith("site/public/data/")
            or path.startswith(("src/", "data/", "scripts/"))
            or path in {"pyproject.toml", "uv.lock", "Makefile"}
        ):
            task = "tier-b"
            reasons.add("backend_or_data_authority")
            continue
        if path in {
            "tests/test_validate_cli.py",
            "tests/test_pages_workflow.py",
        } or path.startswith(("site/", ".github/")):
            if task != "tier-b":
                task = "pr-fast"
            reasons.add("site_or_repository_contract")
            continue
        if path.startswith("tests/"):
            task = "tier-b"
            reasons.add("backend_test_authority")
            continue
        if path.startswith("content/"):
            if task not in {"tier-b", "pr-fast"}:
                task = "tier-a"
            reasons.add("content_authority")
            continue
        if path.startswith("docs/") or path in {
            "README.md",
            "CONTRIBUTING.md",
            "CHANGELOG.md",
        }:
            reasons.add("documentation_only")
            continue
        task = "tier-b"
        reasons.add("unknown_path_safe_default")
    if not normalized:
        reasons.add("no_changed_paths")
    return ChangeValidationPlan(
        contract_version=CONTRACT_VERSION,
        task=task,
        gate=TASKS[task].gate,
        changed_paths=normalized,
        reason_codes=tuple(sorted(reasons)),
    )


def changed_paths_from_git(base_ref: str, root: Path) -> list[str]:
    completed = subprocess.run(
        ["git", "diff", "--name-only", "--diff-filter=ACMR", f"{base_ref}...HEAD"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or f"git diff failed for {base_ref}")
    return [line for line in completed.stdout.splitlines() if line]


def find_repository_root(start: Path | None = None) -> Path:
    """Locate the repository root by walking up from ``start`` (default: cwd)."""
    current = (start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if (candidate / "pyproject.toml").is_file() and (
            candidate / "scripts" / "verify_content.py"
        ).is_file():
            return candidate
    raise FileNotFoundError(
        "could not locate the optimization-compass repository root from"
        f" {current}; run inside the repository checkout"
    )


def _run_data_integrity() -> tuple[bool, str]:
    from optimization_compass.db import KnowledgeRepository

    result = KnowledgeRepository().verify()
    return bool(result["ok"]), json.dumps(result, ensure_ascii=False)


def _run_build_manifest() -> tuple[bool, str]:
    from optimization_compass.build_manifest import BuildManifestError, validate_build_manifest

    try:
        manifest = validate_build_manifest()
    except BuildManifestError as error:
        return False, str(error)
    return True, json.dumps(
        {
            "manifest_version": manifest.manifest_version,
            "schema_migrations": [migration.id for migration in manifest.schema_migrations],
            "specialized_inputs": list(manifest.specialized_inputs),
        },
        ensure_ascii=False,
    )


_CALLABLE_CHECKS: dict[str, Callable[[], tuple[bool, str]]] = {
    "data.integrity": _run_data_integrity,
    "data.manifest": _run_build_manifest,
}


def _tail(text: str) -> str:
    text = text.strip()
    if len(text) <= _OUTPUT_TAIL_CHARACTERS:
        return text
    return text[-_OUTPUT_TAIL_CHARACTERS:]


def execute_check(check: ValidationCheck, root: Path, capture: bool) -> CheckResult:
    """Run one check and report its outcome without raising on failure."""
    started = time.monotonic()

    def finish(status: Literal["pass", "fail", "error"], message: str) -> CheckResult:
        return CheckResult(
            code=check.code,
            status=status,
            command=check.display_command,
            duration_seconds=round(time.monotonic() - started, 3),
            message=_tail(message),
            next_action="" if status == "pass" else check.next_action,
        )

    if check.command is None:
        runner = _CALLABLE_CHECKS.get(check.code)
        if runner is None:
            return finish("error", f"no in-process runner registered for {check.code}")
        try:
            ok, message = runner()
        except Exception as error:  # report the failure instead of crashing the gate
            return finish("error", f"{type(error).__name__}: {error}")
        return finish("pass" if ok else "fail", message)

    argv: list[str] = []
    for token in check.command:
        if token == _PYTHON_TOKEN:
            argv.append(sys.executable)
        elif token == _NPM_TOKEN:
            npm = shutil.which("npm")
            if npm is None:
                return finish(
                    "error",
                    "npm was not found on PATH; install Node.js to run site checks",
                )
            argv.append(npm)
        else:
            argv.append(token)

    try:
        completed = subprocess.run(  # fixed registry commands only, never user input
            argv,
            cwd=root,
            capture_output=capture,
            text=True,
            check=False,
        )
    except OSError as error:
        return finish("error", f"failed to start {argv[0]}: {error}")

    message = ""
    if capture:
        message = "\n".join(part for part in (completed.stdout, completed.stderr) if part)
    if completed.returncode != 0:
        return finish("fail", message or f"exit code {completed.returncode}")
    return finish("pass", message)


def run_task(
    task_name: str,
    root: Path,
    capture: bool = False,
    on_start: Callable[[ValidationCheck], None] | None = None,
    on_finish: Callable[[CheckResult], None] | None = None,
) -> TaskResult:
    """Run a task's checks in order, stopping at the first failure."""
    plan = task_plan(task_name)
    results: list[CheckResult] = []
    failed = False
    for check in plan.checks:
        if failed:
            skipped = CheckResult(
                code=check.code,
                status="skip",
                command=check.display_command,
                duration_seconds=0.0,
                message="skipped after an earlier failure",
                next_action="",
            )
            results.append(skipped)
            if on_finish is not None:
                on_finish(skipped)
            continue
        if on_start is not None:
            on_start(check)
        result = execute_check(check, root, capture)
        results.append(result)
        if on_finish is not None:
            on_finish(result)
        if result.status != "pass":
            failed = True
    return TaskResult(
        contract_version=CONTRACT_VERSION,
        task=plan.task,
        gate=plan.gate,
        status="fail" if failed else "pass",
        checks=tuple(results),
    )
