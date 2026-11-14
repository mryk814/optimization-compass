from __future__ import annotations

import json
from dataclasses import replace
from datetime import date
from pathlib import Path

import pytest

from optimization_compass.content_models import ContentPage, load_content
from optimization_compass.owner_approvals import (
    APPROVALS_PATH,
    approval_state,
    body_hash,
    load_owner_approvals,
    record_owner_approval,
    require_owner_approvals,
)

ROOT = Path(__file__).parents[1]


def _page() -> ContentPage:
    return next(page for page in load_content(ROOT / "content") if page.status == "published")


def test_body_hash_ignores_line_endings_and_trailing_spaces_only() -> None:
    body = "## 見出し\n\n本文です。\n"
    assert body_hash(body) == body_hash("## 見出し  \r\n\r\n本文です。\r\n")
    assert body_hash(body) != body_hash("## 見出し\n\n本文でした。\n")
    assert len(body_hash(body)) == 12


def test_an_edited_body_reads_as_changed_and_never_fails(tmp_path: Path) -> None:
    page = _page()
    record_owner_approval(tmp_path, page, approved_on=date(2026, 11, 14))
    approvals = load_owner_approvals(tmp_path)

    assert approvals[page.content_id].approved_on == date(2026, 11, 14)
    assert approval_state(page, approvals) == "approved"
    edited = replace(page, body=page.body + "\n\n追記した段落です。")
    assert approval_state(edited, approvals) == "changed"
    assert approval_state(replace(page, content_id="not-approved"), approvals) is None
    # A stale approval is information for the owner, not a validation failure.
    require_owner_approvals(tmp_path, [page.content_id])


def test_approvals_must_name_known_articles_and_be_well_formed(tmp_path: Path) -> None:
    path = tmp_path / APPROVALS_PATH
    path.parent.mkdir(parents=True)
    approval = {"body_sha256": "0123456789ab", "approved_on": "2026-10-03"}
    path.write_text(
        json.dumps({"contract_version": "1.0.0", "approvals": {"gone": approval}}), "utf-8"
    )
    with pytest.raises(ValueError, match="unknown articles: gone"):
        require_owner_approvals(tmp_path, ["adam"])

    path.write_text(
        json.dumps({"contract_version": "1.0.0", "approvals": {"adam": {**approval, "note": "x"}}}),
        "utf-8",
    )
    with pytest.raises(ValueError, match="malformed"):
        load_owner_approvals(tmp_path)

    path.write_text(
        json.dumps(
            {"contract_version": "1.0.0", "approvals": {"adam": {**approval, "body_sha256": "x"}}}
        ),
        "utf-8",
    )
    with pytest.raises(ValueError, match="malformed"):
        load_owner_approvals(tmp_path)


def test_committed_approvals_name_published_articles() -> None:
    approvals = load_owner_approvals(ROOT)
    published = {
        page.content_id: page
        for page in load_content(ROOT / "content")
        if page.status == "published"
    }

    assert approvals
    assert set(approvals) <= set(published)
    assert all(approval_state(published[key], approvals) for key in approvals)
