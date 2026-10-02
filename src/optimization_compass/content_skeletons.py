"""Section skeletons that published articles must follow (ADR 0017, learning-atlas.md §4).

An article is judged by whether a learner can walk a fixed order of questions, not by length.
Each kind of article has one skeleton: the listed level-2 headings must all appear, in this
order. Other sections (a `コラム: …`, an explorable walkthrough) may sit between them.

Existing articles that predate a skeleton are listed in
``data/seeds/content_skeleton_pending.json``. The list only shrinks: an article outside it must
conform, and a pending article that already conforms is reported so it can be removed.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterable
from pathlib import Path
from typing import Literal

from optimization_compass.content_models import ContentPage

SkeletonKind = Literal["formulation", "method", "family"]

SKELETONS: dict[SkeletonKind, tuple[str, ...]] = {
    # What the form is → how to read it → a checkable instance → how to spot it → neighbours →
    # how it is solved → where people go wrong → where to go next.
    "formulation": (
        "30秒でつかむ",
        "標準形を読む",
        "小さな例",
        "見分け方",
        "近い定式化",
        "解き方の系統",
        "つまずきやすい点",
        "次に読む",
    ),
    # The feeling → what one iteration does → a few iterations by hand → when to use or avoid →
    # runnable code → what to watch → when to switch → where to go next.
    "method": (
        "30秒でつかむ",
        "一手の意味",
        "小さな例",
        "向く条件・避ける条件",
        "Python",
        "診断値",
        "失敗・切替の兆候",
        "次に読む",
    ),
    # Family choice guides compare methods under stated conditions; they never rank.
    "family": (
        "30秒でつかむ",
        "まず確認すること",
        "条件付きの選び分け",
        "うまくいったサインと切替サイン",
        "小さな比較の型",
        "次に読む",
    ),
}

# An alternative complete reading order: understand, inspect limitations, then choose.
# Legacy articles retain their existing skeleton; this is not a pending-list exemption.
FORMULATION_LEARNER_FIRST = (
    "30秒でつかむ",
    "標準形を読む",
    "小さな例",
    "つまずきやすい点",
    "課題から定式化する",
    "困りごとから関連する問題へ",
    "数値計算の方法を選ぶ",
)

PENDING_PATH = Path("data/seeds/content_skeleton_pending.json")
_ARCHETYPE_ID_PATTERN = re.compile(r"^PA\d{3}$")


def skeleton_kind(page: ContentPage) -> SkeletonKind | None:
    if page.canonical_entity_type == "problem" and _ARCHETYPE_ID_PATTERN.match(
        page.canonical_entity_id
    ):
        return "formulation"
    if page.kind == "method":
        return "family" if page.content_id.startswith("family.") else "method"
    return None


def skeleton_gaps(page: ContentPage) -> tuple[str, ...]:
    """Return ``missing:<section>`` entries, or ``("order",)``, or an empty tuple."""
    kind = skeleton_kind(page)
    if kind is None:
        return ()
    headings = [heading.label for heading in page.toc if heading.level == 2]
    sections = (
        FORMULATION_LEARNER_FIRST
        if kind == "formulation" and "課題から定式化する" in headings
        else SKELETONS[kind]
    )
    missing = tuple(f"missing:{section}" for section in sections if section not in headings)
    if missing:
        return missing
    order = [headings.index(section) for section in sections]
    return () if order == sorted(order) else ("order",)


def load_pending(root: Path) -> frozenset[str]:
    path = root / PENDING_PATH
    if not path.exists():
        return frozenset()
    raw = json.loads(path.read_text(encoding="utf-8"))
    if raw.get("contract_version") != "1.0.0" or not isinstance(raw.get("pending"), list):
        raise ValueError(f"{PENDING_PATH} must be contract 1.0.0 with a pending list")
    ids = [str(item) for item in raw["pending"]]
    if len(ids) != len(set(ids)):
        raise ValueError(f"{PENDING_PATH} lists an article twice")
    return frozenset(ids)


def require_content_skeletons(
    pages: Iterable[ContentPage], pending: frozenset[str]
) -> tuple[str, ...]:
    """Reject published articles outside the pending list that break their skeleton.

    Returns pending article IDs that already conform and can be removed from the list.
    Formulation articles are never exempt.
    """
    failures: list[str] = []
    prunable: list[str] = []
    known: set[str] = set()
    for page in pages:
        if page.status != "published" or skeleton_kind(page) is None:
            continue
        known.add(page.content_id)
        gaps = skeleton_gaps(page)
        exempt = page.content_id in pending and skeleton_kind(page) != "formulation"
        if gaps and not exempt:
            failures.append(f"{page.content_id} [{skeleton_kind(page)}] ({', '.join(gaps)})")
        if not gaps and page.content_id in pending:
            prunable.append(page.content_id)
    unknown = sorted(pending - known)
    if unknown:
        failures.append(f"pending list names unknown articles: {', '.join(unknown)}")
    if failures:
        raise ValueError("articles must follow their section skeleton: " + "; ".join(failures))
    return tuple(sorted(prunable))
