from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlencode, urljoin, urlsplit
from urllib.request import Request, urlopen

DEFAULT_BASE_URL = "https://mryk814.github.io/optimization-compass/"
DEFAULT_WORKFLOW = "ci.yml"
SHA_PATTERN = re.compile(r"[0-9a-f]{40}")
VERSION_PATTERN = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+")


class CheckpointError(RuntimeError):
    pass


@dataclass(frozen=True)
class RepositoryState:
    branch: str
    head_sha: str
    origin_main_sha: str
    clean: bool
    ahead: int
    behind: int


@dataclass(frozen=True)
class WorkflowGate:
    name: str
    status: str
    conclusion: str


@dataclass(frozen=True)
class WorkflowState:
    run_id: int
    head_sha: str
    status: str
    conclusion: str
    url: str
    gates: tuple[WorkflowGate, ...]


@dataclass(frozen=True)
class PublicState:
    base_url: str
    root_status: int
    commit_sha: str
    dataset_version: str
    release_dataset_version: str


def collect_checkpoint(
    repo: Path,
    *,
    base_url: str = DEFAULT_BASE_URL,
    workflow: str = DEFAULT_WORKFLOW,
    run_id: int | None = None,
    fetch: bool = True,
    timeout_seconds: float = 20,
    command_runner: Callable[[list[str], Path], str] | None = None,
    json_fetcher: Callable[[str, float], dict[str, Any]] | None = None,
    status_fetcher: Callable[[str, float], int] | None = None,
) -> dict[str, Any]:
    resolved_repo = repo.resolve()
    run_command = command_runner or _run_command
    fetch_json = json_fetcher or _fetch_json
    fetch_status = status_fetcher or _fetch_status
    if fetch:
        run_command(["git", "fetch", "origin", "--prune"], resolved_repo)

    repository = _repository_state(resolved_repo, run_command)
    workflow_state = _workflow_state(
        resolved_repo,
        repository.head_sha,
        workflow=workflow,
        run_id=run_id,
        run_command=run_command,
    )
    public = _public_state(
        base_url,
        repository.head_sha,
        timeout_seconds=timeout_seconds,
        fetch_json=fetch_json,
        fetch_status=fetch_status,
    )
    state, remaining = classify_checkpoint(repository, workflow_state, public)
    return {
        "schema_version": 1,
        "recorded_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "state": state,
        "remaining": remaining,
        "repository": asdict(repository),
        "workflow": _workflow_payload(workflow_state),
        "public": asdict(public),
    }


def classify_checkpoint(
    repository: RepositoryState,
    workflow: WorkflowState | None,
    public: PublicState,
) -> tuple[str, list[str]]:
    if not repository.clean:
        return "local-changes", ["Commit or isolate the current worktree changes."]
    if repository.ahead and repository.behind:
        return "diverged", ["Reconcile HEAD with origin/main before publishing."]
    if repository.behind:
        return "local-behind", ["Fast-forward the local checkout from origin/main."]
    if repository.ahead or repository.head_sha != repository.origin_main_sha:
        return "not-pushed", ["Push the validated coherent slice to main once."]
    if workflow is None:
        return "workflow-missing", ["Locate or start the main Pages workflow for this commit."]
    if workflow.head_sha != repository.head_sha:
        return "workflow-mismatch", ["Locate the workflow run for the exact HEAD commit."]
    if workflow.status != "completed":
        pending = [
            gate.name for gate in workflow.gates if gate.status not in {"completed", "skipped"}
        ]
        suffix = f": {', '.join(pending)}" if pending else ""
        return "workflow-running", [f"Monitor the current workflow without rerunning it{suffix}."]
    if workflow.conclusion != "success":
        return "workflow-failed", ["Inspect the failed gate and fix its owning authority."]
    if public.root_status != 200:
        return "public-unavailable", ["Wait for or repair the public Pages root."]
    if public.commit_sha != repository.head_sha:
        return "public-stale", ["Wait for Pages propagation or inspect the deploy gate."]
    if public.dataset_version != public.release_dataset_version:
        return "public-identity-mismatch", [
            "Repair the mismatch between deployment.json and data/release.json."
        ]
    return "published", []


def render_markdown(checkpoint: dict[str, Any]) -> str:
    repository = checkpoint["repository"]
    workflow = checkpoint["workflow"]
    public = checkpoint["public"]
    lines = [
        "# Pages publication checkpoint",
        "",
        f"- Recorded: `{checkpoint['recorded_at']}`",
        f"- State: `{checkpoint['state']}`",
        (
            f"- Git: `{repository['branch']}` at `{repository['head_sha']}`; "
            f"clean `{str(repository['clean']).lower()}`; "
            f"ahead `{repository['ahead']}` / behind `{repository['behind']}`"
        ),
    ]
    if workflow is None:
        lines.append("- Workflow: no exact run found")
    else:
        lines.append(
            f"- Workflow: [run {workflow['run_id']}]({workflow['url']}) "
            f"`{workflow['status']}` / `{workflow['conclusion'] or 'pending'}`"
        )
        lines.extend(
            f"  - [{'x' if gate['status'] == 'completed' else ' '}] "
            f"{gate['name']}: `{gate['status']}` / `{gate['conclusion'] or 'pending'}`"
            for gate in workflow["gates"]
        )
    lines.append(
        f"- Public: HTTP `{public['root_status']}`, commit `{public['commit_sha']}`, "
        f"dataset `{public['dataset_version']}`"
    )
    if checkpoint["remaining"]:
        lines.append("- Resume:")
        lines.extend(f"  - {item}" for item in checkpoint["remaining"])
    else:
        lines.append("- Resume: publication is complete; no gate remains.")
    return "\n".join(lines) + "\n"


def _repository_state(
    repo: Path,
    run_command: Callable[[list[str], Path], str],
) -> RepositoryState:
    branch = run_command(["git", "branch", "--show-current"], repo).strip() or "(detached)"
    head_sha = _sha(run_command(["git", "rev-parse", "HEAD"], repo).strip(), "HEAD")
    origin_main_sha = _sha(
        run_command(["git", "rev-parse", "origin/main"], repo).strip(), "origin/main"
    )
    status = run_command(["git", "status", "--porcelain"], repo)
    counts = run_command(
        ["git", "rev-list", "--left-right", "--count", "origin/main...HEAD"], repo
    ).split()
    if len(counts) != 2 or any(not value.isdigit() for value in counts):
        raise CheckpointError("git ahead/behind output is invalid")
    behind, ahead = (int(value) for value in counts)
    return RepositoryState(
        branch=branch,
        head_sha=head_sha,
        origin_main_sha=origin_main_sha,
        clean=not status.strip(),
        ahead=ahead,
        behind=behind,
    )


def _workflow_state(
    repo: Path,
    head_sha: str,
    *,
    workflow: str,
    run_id: int | None,
    run_command: Callable[[list[str], Path], str],
) -> WorkflowState | None:
    selected_run_id = run_id
    if selected_run_id is None:
        raw_runs = run_command(
            [
                "gh",
                "run",
                "list",
                "--workflow",
                workflow,
                "--branch",
                "main",
                "--limit",
                "30",
                "--json",
                "databaseId,headSha,status,conclusion,url",
            ],
            repo,
        )
        runs = _json_list(raw_runs, "GitHub workflow list")
        match = next((item for item in runs if item.get("headSha") == head_sha), None)
        if match is None:
            return None
        selected_run_id = _positive_int(match.get("databaseId"), "workflow run ID")

    raw_run = run_command(
        [
            "gh",
            "run",
            "view",
            str(selected_run_id),
            "--json",
            "databaseId,headSha,status,conclusion,url,jobs",
        ],
        repo,
    )
    payload = _json_object(raw_run, "GitHub workflow run")
    jobs = payload.get("jobs")
    if not isinstance(jobs, list):
        raise CheckpointError("GitHub workflow jobs are invalid")
    gates = tuple(
        WorkflowGate(
            name=_text(job.get("name"), "workflow job name"),
            status=_text(job.get("status"), "workflow job status"),
            conclusion=_optional_text(job.get("conclusion"), "workflow job conclusion"),
        )
        for job in jobs
        if isinstance(job, dict)
    )
    return WorkflowState(
        run_id=_positive_int(payload.get("databaseId"), "workflow run ID"),
        head_sha=_sha(payload.get("headSha"), "workflow head SHA"),
        status=_text(payload.get("status"), "workflow status"),
        conclusion=_optional_text(payload.get("conclusion"), "workflow conclusion"),
        url=_http_url(payload.get("url"), "workflow URL"),
        gates=gates,
    )


def _public_state(
    base_url: str,
    cache_key: str,
    *,
    timeout_seconds: float,
    fetch_json: Callable[[str, float], dict[str, Any]],
    fetch_status: Callable[[str, float], int],
) -> PublicState:
    normalized_base = _base_url(base_url)
    query = "?" + urlencode({"checkpoint": cache_key})
    root_status = fetch_status(normalized_base + query, timeout_seconds)
    deployment = fetch_json(urljoin(normalized_base, "deployment.json") + query, timeout_seconds)
    release = fetch_json(urljoin(normalized_base, "data/release.json") + query, timeout_seconds)
    return PublicState(
        base_url=normalized_base,
        root_status=root_status,
        commit_sha=_sha(deployment.get("commit_sha"), "public deployment commit SHA"),
        dataset_version=_version(
            deployment.get("dataset_version"), "public deployment dataset version"
        ),
        release_dataset_version=_version(
            release.get("dataset_version"), "public release dataset version"
        ),
    )


def _workflow_payload(workflow: WorkflowState | None) -> dict[str, Any] | None:
    if workflow is None:
        return None
    payload = asdict(workflow)
    payload["gates"] = [asdict(gate) for gate in workflow.gates]
    return payload


def _run_command(arguments: list[str], cwd: Path) -> str:
    try:
        completed = subprocess.run(
            arguments,
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
    except FileNotFoundError as error:
        raise CheckpointError(f"required command is unavailable: {arguments[0]}") from error
    except subprocess.CalledProcessError as error:
        detail = (error.stderr or error.stdout or "").strip()
        raise CheckpointError(f"command failed: {' '.join(arguments)}: {detail}") from error
    return completed.stdout


def _fetch_json(url: str, timeout_seconds: float) -> dict[str, Any]:
    payload = _fetch(url, timeout_seconds)
    try:
        decoded = json.loads(payload)
    except json.JSONDecodeError as error:
        raise CheckpointError(f"public JSON is invalid: {url}") from error
    if not isinstance(decoded, dict):
        raise CheckpointError(f"public JSON must be an object: {url}")
    return decoded


def _fetch_status(url: str, timeout_seconds: float) -> int:
    request = Request(
        url,
        headers={"Cache-Control": "no-cache", "User-Agent": "oc-pages-checkpoint/1"},
    )
    with urlopen(request, timeout=timeout_seconds) as response:
        return int(response.status)


def _fetch(url: str, timeout_seconds: float) -> bytes:
    request = Request(
        url,
        headers={"Cache-Control": "no-cache", "User-Agent": "oc-pages-checkpoint/1"},
    )
    with urlopen(request, timeout=timeout_seconds) as response:
        if response.status != 200:
            raise CheckpointError(f"public asset returned HTTP {response.status}: {url}")
        return response.read()


def _json_list(value: str, field: str) -> list[dict[str, Any]]:
    try:
        payload = json.loads(value)
    except json.JSONDecodeError as error:
        raise CheckpointError(f"{field} is invalid JSON") from error
    if not isinstance(payload, list) or any(not isinstance(item, dict) for item in payload):
        raise CheckpointError(f"{field} must be a list of objects")
    return payload


def _json_object(value: str, field: str) -> dict[str, Any]:
    try:
        payload = json.loads(value)
    except json.JSONDecodeError as error:
        raise CheckpointError(f"{field} is invalid JSON") from error
    if not isinstance(payload, dict):
        raise CheckpointError(f"{field} must be an object")
    return payload


def _sha(value: object, field: str) -> str:
    if not isinstance(value, str) or SHA_PATTERN.fullmatch(value) is None:
        raise CheckpointError(f"{field} must be a 40-character lowercase commit SHA")
    return value


def _version(value: object, field: str) -> str:
    if not isinstance(value, str) or VERSION_PATTERN.fullmatch(value) is None:
        raise CheckpointError(f"{field} must be semantic version X.Y.Z")
    return value


def _text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise CheckpointError(f"{field} must be non-empty text")
    return value


def _optional_text(value: object, field: str) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        raise CheckpointError(f"{field} must be text")
    return value


def _positive_int(value: object, field: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise CheckpointError(f"{field} must be a positive integer")
    return value


def _http_url(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise CheckpointError(f"{field} must be an HTTP(S) URL")
    parts = urlsplit(value)
    if parts.scheme not in {"http", "https"} or not parts.netloc:
        raise CheckpointError(f"{field} must be an HTTP(S) URL")
    return value


def _base_url(value: str) -> str:
    parts = urlsplit(value)
    if parts.scheme not in {"http", "https"} or not parts.netloc or parts.query or parts.fragment:
        raise CheckpointError("base URL must be HTTP(S) without query or fragment")
    return value.rstrip("/") + "/"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Capture an interruption-safe GitHub Pages publication checkpoint."
    )
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--workflow", default=DEFAULT_WORKFLOW)
    parser.add_argument("--run-id", type=int)
    parser.add_argument("--no-fetch", dest="fetch", action="store_false")
    parser.add_argument("--timeout-seconds", type=float, default=20)
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--require-published",
        action="store_true",
        help="Exit with status 2 unless the checkpoint proves the exact commit is published.",
    )
    return parser


def main() -> None:
    parser = _parser()
    args = parser.parse_args()
    if args.timeout_seconds <= 0:
        parser.error("--timeout-seconds must be greater than zero")
    try:
        checkpoint = collect_checkpoint(
            args.repo,
            base_url=args.base_url,
            workflow=args.workflow,
            run_id=args.run_id,
            fetch=args.fetch,
            timeout_seconds=args.timeout_seconds,
        )
    except (CheckpointError, OSError) as error:
        parser.exit(1, f"Pages checkpoint failed: {error}\n")
    rendered = (
        json.dumps(checkpoint, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        if args.format == "json"
        else render_markdown(checkpoint)
    )
    if args.output is not None:
        try:
            args.output.write_text(rendered, encoding="utf-8", newline="\n")
        except OSError as error:
            parser.exit(1, f"Pages checkpoint could not be written: {error}\n")
    sys.stdout.write(rendered)
    if args.require_published and checkpoint["state"] != "published":
        parser.exit(2, f"Pages checkpoint state is {checkpoint['state']}, not published.\n")


if __name__ == "__main__":
    main()
