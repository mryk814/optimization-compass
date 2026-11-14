"""Articles the owner approved on screen, and whether their body changed since.

``data/seeds/owner_approvals.json`` keeps, per content ID, the hash of the article body the owner
approved and the date of the approval. It is information, never a gate: an edited article simply
reads as ``changed`` until the owner looks at it again. Validation only rejects a malformed file
and approvals that name no article.

Approvals are recorded with ``scripts/article_inventory.py --approve <content_id>``, and only after
the owner says they approved that article on screen.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping
from datetime import date
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from optimization_compass.content_models import ContentPage

APPROVALS_PATH = Path("data/seeds/owner_approvals.json")
CONTRACT_VERSION = "1.0.0"
ApprovalState = Literal["approved", "changed"]


class OwnerApproval(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    body_sha256: str = Field(pattern=r"^[0-9a-f]{12}$")
    approved_on: date


class _ApprovalFile(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    contract_version: Literal["1.0.0"]
    approvals: dict[str, OwnerApproval]


def body_hash(body: str) -> str:
    """Short hash of an article body (frontmatter excluded).

    Line endings and trailing spaces do not count, so only an edit a reader could see changes it.
    This is the definition the retired article quality ledger used, so its recorded hashes still
    compare equal.
    """
    normalized = "\n".join(line.rstrip() for line in body.replace("\r\n", "\n").splitlines())
    return hashlib.sha256(normalized.strip().encode("utf-8")).hexdigest()[:12]


def load_owner_approvals(root: Path) -> dict[str, OwnerApproval]:
    path = root / APPROVALS_PATH
    if not path.exists():
        return {}
    try:
        parsed = _ApprovalFile.model_validate_json(path.read_text(encoding="utf-8"))
    except ValidationError as error:
        raise ValueError(f"{APPROVALS_PATH} is malformed: {error}") from error
    return dict(parsed.approvals)


def approval_state(
    page: ContentPage, approvals: Mapping[str, OwnerApproval]
) -> ApprovalState | None:
    """``approved`` while the body is the one approved, ``changed`` after an edit, else None."""
    approval = approvals.get(page.content_id)
    if approval is None:
        return None
    return "approved" if approval.body_sha256 == body_hash(page.body) else "changed"


def require_owner_approvals(root: Path, content_ids: Iterable[str]) -> None:
    """Reject a malformed file or approvals of unknown articles; a stale approval is fine."""
    unknown = sorted(set(load_owner_approvals(root)) - set(content_ids))
    if unknown:
        raise ValueError(f"{APPROVALS_PATH} names unknown articles: {', '.join(unknown)}")


def record_owner_approval(root: Path, page: ContentPage, *, approved_on: date) -> OwnerApproval:
    """Record that the owner approved the current body of ``page``, replacing an older approval."""
    approvals = load_owner_approvals(root)
    approval = OwnerApproval(body_sha256=body_hash(page.body), approved_on=approved_on)
    approvals[page.content_id] = approval
    payload = {
        "contract_version": CONTRACT_VERSION,
        "approvals": {
            content_id: {
                "body_sha256": approvals[content_id].body_sha256,
                "approved_on": approvals[content_id].approved_on.isoformat(),
            }
            for content_id in sorted(approvals)
        },
    }
    (root / APPROVALS_PATH).parent.mkdir(parents=True, exist_ok=True)
    (root / APPROVALS_PATH).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    return approval
