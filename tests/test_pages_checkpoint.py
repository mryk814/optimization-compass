from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from scripts.pages_checkpoint import (
    PublicState,
    RepositoryState,
    WorkflowGate,
    WorkflowState,
    classify_checkpoint,
    collect_checkpoint,
    render_markdown,
)

COMMIT_SHA = "a" * 40
RUN_URL = "https://github.com/example/project/actions/runs/123"
BASE_URL = "https://example.github.io/project/"


def _repository(**overrides: object) -> RepositoryState:
    values: dict[str, object] = {
        "branch": "main",
        "head_sha": COMMIT_SHA,
        "origin_main_sha": COMMIT_SHA,
        "clean": True,
        "ahead": 0,
        "behind": 0,
    }
    values.update(overrides)
    return RepositoryState(**values)  # type: ignore[arg-type]


def _workflow(**overrides: object) -> WorkflowState:
    values: dict[str, object] = {
        "run_id": 123,
        "head_sha": COMMIT_SHA,
        "status": "completed",
        "conclusion": "success",
        "url": RUN_URL,
        "gates": (
            WorkflowGate("Validate and build Pages artifact", "completed", "success"),
            WorkflowGate("Browser E2E and accessibility", "completed", "success"),
            WorkflowGate("Deploy validated artifact and smoke it", "completed", "success"),
        ),
    }
    values.update(overrides)
    return WorkflowState(**values)  # type: ignore[arg-type]


def _public(**overrides: object) -> PublicState:
    values: dict[str, object] = {
        "base_url": BASE_URL,
        "root_status": 200,
        "commit_sha": COMMIT_SHA,
        "dataset_version": "1.2.3",
        "release_dataset_version": "1.2.3",
    }
    values.update(overrides)
    return PublicState(**values)  # type: ignore[arg-type]


def test_collect_checkpoint_proves_one_exact_publication(tmp_path: Path) -> None:
    def run_command(arguments: list[str], cwd: Path) -> str:
        assert cwd == tmp_path.resolve()
        command = tuple(arguments)
        outputs = {
            ("git", "fetch", "origin", "--prune"): "",
            ("git", "branch", "--show-current"): "main\n",
            ("git", "rev-parse", "HEAD"): f"{COMMIT_SHA}\n",
            ("git", "rev-parse", "origin/main"): f"{COMMIT_SHA}\n",
            ("git", "status", "--porcelain"): "",
            ("git", "rev-list", "--left-right", "--count", "origin/main...HEAD"): "0 0\n",
        }
        if command in outputs:
            return outputs[command]
        if command[:4] == ("gh", "run", "list", "--workflow"):
            return json.dumps(
                [
                    {
                        "databaseId": 123,
                        "headSha": COMMIT_SHA,
                        "status": "completed",
                        "conclusion": "success",
                        "url": RUN_URL,
                    }
                ]
            )
        if command[:3] == ("gh", "run", "view"):
            return json.dumps(
                {
                    "databaseId": 123,
                    "headSha": COMMIT_SHA,
                    "status": "completed",
                    "conclusion": "success",
                    "url": RUN_URL,
                    "jobs": [
                        {
                            "name": "Validate and build Pages artifact",
                            "status": "completed",
                            "conclusion": "success",
                        },
                        {
                            "name": "Browser E2E and accessibility",
                            "status": "completed",
                            "conclusion": "success",
                        },
                        {
                            "name": "Deploy validated artifact and smoke it",
                            "status": "completed",
                            "conclusion": "success",
                        },
                    ],
                }
            )
        raise AssertionError(f"unexpected command: {arguments}")

    def fetch_json(url: str, timeout_seconds: float) -> dict[str, Any]:
        assert timeout_seconds == 3
        if "deployment.json" in url:
            return {"commit_sha": COMMIT_SHA, "dataset_version": "1.2.3"}
        if "data/release.json" in url:
            return {"dataset_version": "1.2.3"}
        raise AssertionError(f"unexpected URL: {url}")

    checkpoint = collect_checkpoint(
        tmp_path,
        base_url=BASE_URL,
        timeout_seconds=3,
        command_runner=run_command,
        json_fetcher=fetch_json,
        status_fetcher=lambda url, timeout: 200,
    )

    assert checkpoint["state"] == "published"
    assert checkpoint["remaining"] == []
    assert checkpoint["workflow"]["run_id"] == 123
    assert checkpoint["public"]["commit_sha"] == COMMIT_SHA


def test_running_checkpoint_names_only_the_remaining_gate() -> None:
    workflow = _workflow(
        status="in_progress",
        conclusion="",
        gates=(
            WorkflowGate("Validate and build Pages artifact", "completed", "success"),
            WorkflowGate("Browser E2E and accessibility", "in_progress", ""),
        ),
    )

    state, remaining = classify_checkpoint(_repository(), workflow, _public())

    assert state == "workflow-running"
    assert remaining == [
        "Monitor the current workflow without rerunning it: Browser E2E and accessibility."
    ]


def test_unpushed_commit_takes_precedence_over_the_previous_publication() -> None:
    state, remaining = classify_checkpoint(
        _repository(head_sha="b" * 40, ahead=1),
        _workflow(),
        _public(),
    )

    assert state == "not-pushed"
    assert remaining == ["Push the validated coherent slice to main once."]


def test_successful_workflow_does_not_hide_a_stale_public_commit() -> None:
    state, remaining = classify_checkpoint(
        _repository(),
        _workflow(),
        _public(commit_sha="c" * 40),
    )

    assert state == "public-stale"
    assert remaining == ["Wait for Pages propagation or inspect the deploy gate."]


def test_markdown_checkpoint_is_a_copyable_handoff() -> None:
    checkpoint = {
        "recorded_at": "2026-07-26T06:00:00+00:00",
        "state": "published",
        "remaining": [],
        "repository": {
            "branch": "main",
            "head_sha": COMMIT_SHA,
            "origin_main_sha": COMMIT_SHA,
            "clean": True,
            "ahead": 0,
            "behind": 0,
        },
        "workflow": {
            "run_id": 123,
            "head_sha": COMMIT_SHA,
            "status": "completed",
            "conclusion": "success",
            "url": RUN_URL,
            "gates": [
                {
                    "name": "Deploy validated artifact and smoke it",
                    "status": "completed",
                    "conclusion": "success",
                }
            ],
        },
        "public": {
            "base_url": BASE_URL,
            "root_status": 200,
            "commit_sha": COMMIT_SHA,
            "dataset_version": "1.2.3",
            "release_dataset_version": "1.2.3",
        },
    }

    rendered = render_markdown(checkpoint)

    assert "# Pages publication checkpoint" in rendered
    assert f"[run 123]({RUN_URL})" in rendered
    assert "publication is complete; no gate remains" in rendered
