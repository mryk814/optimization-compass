"""Canonical content authoring and publish-readiness workflow."""

from __future__ import annotations

import json
import re
import subprocess
from datetime import date
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from optimization_compass.content_models import ContentPage, load_content, parse_content
from optimization_compass.db import KnowledgeRepository
from optimization_compass.method_content_density import inspect_page, render_report
from optimization_compass.site_export import export_site_data
from optimization_compass.validation_tasks import run_task, validation_task_for_paths

_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_PLACEHOLDER_PATTERN = re.compile(r"\b(?:TODO|TBD|FIXME|PLACEHOLDER)\b", re.IGNORECASE)
_CONTENT_ID_PATTERN = re.compile(r"^content_id:\s*[\"']?([^\s\"']+)", re.MULTILINE)


class ContentAuthoringError(ValueError):
    """The requested authoring transition is unsafe or incomplete."""


class ReadyContentReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    contract_version: str = "1.0.0"
    content_id: str
    canonical_path: str
    public_routes: tuple[str, ...]
    generated_paths: tuple[str, ...]
    changed_paths: tuple[str, ...]
    required_pr_gate: str
    after_merge: tuple[str, ...]


class ContentIterationReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    contract_version: str = "1.0.0"
    content_id: str
    canonical_path: str
    status: str
    canonical_entity_id: str
    source_ids: tuple[str, ...]
    next_command: str


def author_method_draft(
    content_id: str,
    method_id: str,
    *,
    root: Path,
    repository: KnowledgeRepository | None = None,
) -> Path:
    """Create one parseable draft directly in the canonical content authority."""
    if not _ID_PATTERN.fullmatch(content_id):
        raise ContentAuthoringError(
            "content ID must start with a letter or number and contain only letters, numbers, "
            "'.', '_' or '-'"
        )
    repository = repository or KnowledgeRepository(
        root / "src/optimization_compass/resources/knowledge.sqlite"
    )
    known_methods = {
        str(row["method_id"]) for row in repository.fetch_all("SELECT method_id FROM methods")
    }
    if method_id not in known_methods:
        raise ContentAuthoringError(f"unknown canonical method ID: {method_id}")
    destination = root / "content" / "methods" / f"{content_id}.md"
    if destination.exists():
        raise ContentAuthoringError(f"canonical content already exists: {destination}")
    existing_ids = {page.content_id for page in load_content(root / "content")}
    if content_id in existing_ids:
        raise ContentAuthoringError(f"content ID already exists: {content_id}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(_method_draft(content_id, method_id), encoding="utf-8", newline="\n")
    parse_content(destination)
    return destination


def require_publish_ready(
    page: ContentPage,
    raw: str,
    repository: KnowledgeRepository,
    *,
    today: date | None = None,
) -> None:
    """Validate the target-specific contract that precedes public generation."""
    errors: list[str] = []
    if page.status != "published":
        errors.append("status must be published")
    if _PLACEHOLDER_PATTERN.search(raw):
        errors.append("TODO/TBD/FIXME/PLACEHOLDER text remains")
    if not page.source_ids:
        errors.append("at least one source ID is required")
    reviewed = date.fromisoformat(page.last_reviewed) if page.last_reviewed else None
    if reviewed is None:
        errors.append("last_reviewed is required")
    elif reviewed > (today or date.today()):
        errors.append("last_reviewed must not be in the future")

    known_sources = {
        str(row["source_id"]) for row in repository.fetch_all("SELECT source_id FROM sources")
    }
    missing_sources = sorted(set(page.source_ids) - known_sources)
    if missing_sources:
        errors.append("unknown source IDs: " + ", ".join(missing_sources))
    if page.kind == "method":
        known_methods = {
            str(row["method_id"]) for row in repository.fetch_all("SELECT method_id FROM methods")
        }
        if page.method_id not in known_methods:
            errors.append(f"unknown canonical method ID: {page.method_id}")
        density = inspect_page(page)
        if not density.meets_floor:
            errors.append(
                "method explanation floor is not met "
                f"(summary={density.summary_characters}, body={density.body_characters}, "
                f"toc={density.toc_entries}, python={density.python_blocks})"
            )
    if errors:
        raise ContentAuthoringError(f"{page.content_id} is not publish-ready: " + "; ".join(errors))


def validate_content_iteration(content_id: str, *, root: Path) -> ContentIterationReport:
    """Run the fast, target-specific structural checks used while writing."""
    page, source_path = _find_content(content_id, root)
    repository = KnowledgeRepository(root / "src/optimization_compass/resources/knowledge.sqlite")
    if page.kind == "method":
        known_methods = {
            str(row["method_id"]) for row in repository.fetch_all("SELECT method_id FROM methods")
        }
        if page.method_id not in known_methods:
            raise ContentAuthoringError(f"unknown canonical method ID: {page.method_id}")
    known_sources = {
        str(row["source_id"]) for row in repository.fetch_all("SELECT source_id FROM sources")
    }
    missing_sources = sorted(set(page.source_ids) - known_sources)
    if missing_sources:
        raise ContentAuthoringError("unknown source IDs: " + ", ".join(missing_sources))
    known_content = _content_ids(root / "content")
    missing_relations = sorted(set((*page.prerequisites, *page.related_ids)) - known_content)
    if missing_relations:
        raise ContentAuthoringError(
            "unknown prerequisite/related content IDs: " + ", ".join(missing_relations)
        )
    return ContentIterationReport(
        content_id=page.content_id,
        canonical_path=source_path.relative_to(root).as_posix(),
        status=page.status,
        canonical_entity_id=page.canonical_entity_id,
        source_ids=page.source_ids,
        next_command=f"optimization-compass ready content {page.content_id}",
    )


def prepare_content_for_pr(content_id: str, *, root: Path) -> ReadyContentReport:
    """Generate public artifacts, run the owning gate, and report the exact PR handoff."""
    page, source_path = _find_content(content_id, root)
    repository = KnowledgeRepository(root / "src/optimization_compass/resources/knowledge.sqlite")
    require_publish_ready(page, source_path.read_text(encoding="utf-8"), repository)
    branch_paths = _branch_change_paths(root)
    unrelated = [
        path
        for path in branch_paths
        if not path.startswith(("content/", "docs/"))
        and path not in {"README.md", "CONTRIBUTING.md", "CHANGELOG.md"}
    ]
    if unrelated:
        raise ContentAuthoringError(
            "content-ready requires a content-only branch; split unrelated changes: "
            + ", ".join(unrelated)
        )

    output = root / "site/public/data"
    export_site_data(output, repository)
    if page.kind == "method":
        published_methods = [
            item
            for item in load_content(root / "content")
            if item.status == "published" and item.kind == "method"
        ]
        rows = [
            inspect_page(item)
            for item in sorted(published_methods, key=lambda item: item.content_id)
        ]
        (root / "docs/method-content-density-report.md").write_text(
            render_report(rows), encoding="utf-8", newline="\n"
        )

    routes = _require_public_artifacts(page, output)
    result = run_task("content-ready", root, capture=False)
    if result.status != "pass":
        raise ContentAuthoringError(
            "content-ready validation failed; inspect the check output above"
        )
    changed = tuple(_branch_change_paths(root))
    selected = validation_task_for_paths(changed)
    if selected.task != "content-ready":
        raise ContentAuthoringError(
            f"generated change set selected unexpected PR gate {selected.task}; "
            "split unrelated changes"
        )
    generated = tuple(
        path
        for path in changed
        if path.startswith("site/public/data/") or path == "docs/method-content-density-report.md"
    )
    return ReadyContentReport(
        content_id=content_id,
        canonical_path=source_path.relative_to(root).as_posix(),
        public_routes=routes,
        generated_paths=generated,
        changed_paths=changed,
        required_pr_gate=selected.task,
        after_merge=(
            "GitHub Pages deploys automatically from main",
            *(f"verify /#{route}" for route in routes),
        ),
    )


def _find_content(content_id: str, root: Path) -> tuple[ContentPage, Path]:
    for directory in ("methods", "concepts"):
        candidate = root / "content" / directory / f"{content_id}.md"
        if candidate.exists():
            page = parse_content(candidate)
            if page.content_id != content_id:
                raise ContentAuthoringError(
                    f"filename candidate has content_id {page.content_id}, expected {content_id}"
                )
            return page, candidate
    matches: list[tuple[ContentPage, Path]] = []
    for path in sorted((root / "content").rglob("*.md")):
        raw = path.read_text(encoding="utf-8")
        match = _CONTENT_ID_PATTERN.search(raw)
        if match and match.group(1) == content_id:
            matches.append((parse_content(path), path))
    if len(matches) != 1:
        raise ContentAuthoringError(
            f"expected one canonical content page for {content_id}; observed {len(matches)}"
        )
    return matches[0]


def _content_ids(directory: Path) -> set[str]:
    result: set[str] = set()
    for path in directory.rglob("*.md"):
        match = _CONTENT_ID_PATTERN.search(path.read_text(encoding="utf-8"))
        if match:
            result.add(match.group(1))
    return result


def _require_public_artifacts(page: ContentPage, output: Path) -> tuple[str, ...]:
    content = json.loads((output / "content.json").read_text(encoding="utf-8"))
    if not any(item.get("content_id") == page.content_id for item in content["pages"]):
        raise ContentAuthoringError("generated content index does not contain the target page")
    links = json.loads((output / "entity-links.json").read_text(encoding="utf-8"))
    content_entity = next(
        (
            item
            for item in links["entities"]
            if item["entity_type"] == "content" and item["entity_id"] == page.content_id
        ),
        None,
    )
    if content_entity is None:
        raise ContentAuthoringError("generated entity-link index does not contain the target page")
    routes = (
        (f"/methods/{page.method_id}", f"/learn/{page.content_id}")
        if page.method_id
        else (f"/learn/{page.content_id}",)
    )
    search = json.loads((output / "search-index.json").read_text(encoding="utf-8"))
    document = next(
        (
            item
            for item in search["documents"]
            if item["entity_type"] == "content" and item["entity_id"] == page.content_id
        ),
        None,
    )
    if document is None or document["canonical_route"] not in routes:
        raise ContentAuthoringError("generated search index does not expose the target route")
    retrieval = json.loads((output / "retrieval-documents.json").read_text(encoding="utf-8"))
    if not any(chunk["document_id"] == document["document_id"] for chunk in retrieval["chunks"]):
        raise ContentAuthoringError("generated retrieval export does not contain the target page")
    return routes


def _working_tree_paths(root: Path) -> list[str]:
    completed = subprocess.run(
        ["git", "status", "--short", "--untracked-files=all"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise ContentAuthoringError(completed.stderr.strip() or "git status failed")
    return sorted(line[3:].replace("\\", "/") for line in completed.stdout.splitlines() if line)


def _branch_change_paths(root: Path, base_ref: str = "origin/main") -> list[str]:
    completed = subprocess.run(
        ["git", "diff", "--name-only", "--diff-filter=ACMR", f"{base_ref}...HEAD"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise ContentAuthoringError(
            completed.stderr.strip() or f"could not compare the content branch with {base_ref}"
        )
    committed = {line.replace("\\", "/") for line in completed.stdout.splitlines() if line}
    return sorted(committed | set(_working_tree_paths(root)))


def _method_draft(content_id: str, method_id: str) -> str:
    summary = "TODO: 最初の本文段落と完全に一致する、レビュー済みの日本語summaryに置き換える。"
    return f'''---
content_id: {content_id}
kind: method
method_id: {method_id}
title_ja: "TODO: 日本語タイトル"
title_en: "TODO: English title"
summary: "{summary}"
source_ids: []
prerequisites: []
related_ids: []
visualization_ids: []
comparison_ids: []
status: draft
last_reviewed: null
---

{summary}

## 30秒でつかむ

- **見るもの**: TODO
- **動かすもの**: TODO
- **前進の判断**: TODO

## まず確認すること

TODO: 変数、目的、制約、利用できる情報、評価コストを書く。

## 仕組み

TODO: method theoryとimplementation固有挙動を分けて説明する。

## 向く条件・避ける条件

TODO: 適用条件と保証範囲を書く。

## うまくいったサインと切替サイン

TODO: 成功、失敗、切替の観測可能なsignalを書く。

## Python

```python
# TODO: copy可能で構文的に正しい最小例へ置き換える
pass
```

## 限界

TODO: limitationsと実問題へ一般化できない範囲を書く。
'''
