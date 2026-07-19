from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from optimization_compass.content_authoring import (
    ContentAuthoringError,
    author_method_draft,
    require_publish_ready,
    validate_content_iteration,
)
from optimization_compass.content_models import load_content, parse_content
from optimization_compass.db import KnowledgeRepository


class _MethodRepository:
    def fetch_all(self, query: str) -> list[dict[str, Any]]:
        assert "FROM methods" in query
        return [{"method_id": "M_EXISTING"}]


def test_author_method_creates_one_parseable_canonical_draft(tmp_path: Path) -> None:
    (tmp_path / "content/methods").mkdir(parents=True)

    destination = author_method_draft(
        "example-method",
        "M_EXISTING",
        root=tmp_path,
        repository=_MethodRepository(),  # type: ignore[arg-type]
    )

    assert destination == tmp_path / "content/methods/example-method.md"
    page = parse_content(destination)
    assert page.content_id == "example-method"
    assert page.method_id == "M_EXISTING"
    assert page.status == "draft"
    assert page.source_ids == ()
    assert page.last_reviewed is None


def test_author_method_refuses_unknown_identity_and_overwrite(tmp_path: Path) -> None:
    (tmp_path / "content/methods").mkdir(parents=True)
    with pytest.raises(ContentAuthoringError, match="unknown canonical method"):
        author_method_draft(
            "example-method",
            "M_UNKNOWN",
            root=tmp_path,
            repository=_MethodRepository(),  # type: ignore[arg-type]
        )
    author_method_draft(
        "example-method",
        "M_EXISTING",
        root=tmp_path,
        repository=_MethodRepository(),  # type: ignore[arg-type]
    )
    with pytest.raises(ContentAuthoringError, match="already exists"):
        author_method_draft(
            "example-method",
            "M_EXISTING",
            root=tmp_path,
            repository=_MethodRepository(),  # type: ignore[arg-type]
        )


def test_publish_ready_contract_accepts_a_complete_existing_method() -> None:
    root = Path(__file__).parents[1]
    page = next(
        item
        for item in load_content(root / "content")
        if item.status == "published" and item.kind == "method"
    )
    source = root / "content/methods" / f"{page.content_id}.md"

    require_publish_ready(
        page,
        source.read_text(encoding="utf-8"),
        KnowledgeRepository(root / "src/optimization_compass/resources/knowledge.sqlite"),
    )


def test_publish_ready_contract_rejects_draft_and_placeholders() -> None:
    root = Path(__file__).parents[1]
    page = next(item for item in load_content(root / "content") if item.kind == "method")
    with pytest.raises(ContentAuthoringError, match="status must be published"):
        require_publish_ready(
            replace(page, status="draft"),
            page.body + "\nTODO: unfinished",
            KnowledgeRepository(root / "src/optimization_compass/resources/knowledge.sqlite"),
        )


def test_target_iteration_validation_accepts_a_canonical_draft() -> None:
    root = Path(__file__).parents[1]
    draft = next(item for item in load_content(root / "content") if item.status == "draft")

    report = validate_content_iteration(draft.content_id, root=root)

    assert report.status == "draft"
    assert report.canonical_entity_id == draft.canonical_entity_id
    assert report.next_command.endswith(draft.content_id)
