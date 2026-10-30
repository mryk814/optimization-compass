"""Ordinary English words inside Japanese reader-facing data text (ADR 0013, article-style §2).

Articles already have ``prose.no-language-mixing``. Gallery cases, comparisons, and the lesson text
of visualization scenarios are written in seeds and Python contracts instead, and they reach the
reader just as directly. This check finds lowercase English words inside their Japanese strings.

What stays allowed: capitalised names and acronyms (Newton, BFGS, QR), code and identifiers,
formulas, a short ASCII gloss in parentheses after a Japanese term, and the few lowercase tokens
in ``ALLOWED_WORDS`` (math function names and units). Everything else is an ordinary word that
article-style §2.1 asks to write in Japanese (ソルバー, ブラックボックス, 信頼領域 included).

Items written before this check are listed in ``data/seeds/language_mixing_pending.json``. The list
only shrinks: an item outside it must have no hits, and a pending item without hits is reported so
it can be removed.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

Surface = Literal["gallery", "comparison", "scenario"]

PENDING_PATH = Path("data/seeds/language_mixing_pending.json")
# Where each surface's reader-facing text is authored or, for scenarios, exported.
SURFACES: dict[Surface, tuple[Path, str, str]] = {
    "gallery": (Path("data/seeds/site_gallery.json"), "cases", "case_id"),
    "comparison": (Path("data/seeds/site_comparisons.json"), "comparisons", "comparison_id"),
    "scenario": (
        Path("site/public/data/visualization-scenarios.json"),
        "scenarios",
        "scenario_id",
    ),
}
# Math function names and units read as notation, not as English prose.
ALLOWED_WORDS = frozenset(
    {"exp", "log", "det", "max", "min", "sin", "cos", "tan", "arg", "argmin", "argmax", "diag"}
    | {"rad", "deg"}
)
_SKIPPED_KEYS = frozenset({"python_example", "canonical_url", "aliases"})

_JAPANESE = re.compile(r"[ぁ-んァ-ヶ一-龠]")
_INLINE_MATH = re.compile(r"\$[^$]*\$")
_INLINE_CODE = re.compile(r"`[^`]*`")
_LINK_TARGET = re.compile(r"\]\([^)]*\)")
_URL = re.compile(r"https?://\S+")
# "目的関数（objective function）": an ASCII gloss right after Japanese text is allowed.
_GLOSS = re.compile(r"(?<=[ぁ-んァ-ヶ一-龠ー])\s?[（(][A-Za-z][A-Za-z \-/']*[)）]")
# A lowercase word of three or more letters, optionally hyphenated, that is not part of code.
_WORD = re.compile(r"(?<![A-Za-z0-9_./\\-])([a-z]{3,}(?:-[a-z]+)*)(?![A-Za-z0-9_(])")


@dataclass(frozen=True)
class MixingHit:
    surface: Surface
    item_id: str
    field: str
    word: str


def mixed_words(text: str) -> list[str]:
    """Return the ordinary English words in one Japanese string, in reading order."""
    if not _JAPANESE.search(text):
        return []
    visible = _INLINE_MATH.sub(" ", text)
    visible = _INLINE_CODE.sub(" ", visible)
    visible = _LINK_TARGET.sub("]", visible)
    visible = _URL.sub(" ", visible)
    visible = _GLOSS.sub(" ", visible)
    return [word for word in _WORD.findall(visible) if word not in ALLOWED_WORDS]


def _strings(value: Any, field: str) -> Iterator[tuple[str, str]]:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in _SKIPPED_KEYS or key.endswith(("_en", "_id", "_ids")):
                continue
            yield from _strings(child, f"{field}.{key}" if field else key)
    elif isinstance(value, list):
        for child in value:
            yield from _strings(child, field)
    elif isinstance(value, str):
        yield field, value


def surface_hits(root: Path, surface: Surface) -> dict[str, list[MixingHit]]:
    """Hits per item of one surface; every item appears, with an empty list when it is clean."""
    path, collection, id_key = SURFACES[surface]
    items = json.loads((root / path).read_text(encoding="utf-8"))[collection]
    result: dict[str, list[MixingHit]] = {}
    for item in items:
        item_id = str(item[id_key])
        result[item_id] = [
            MixingHit(surface, item_id, field, word)
            for field, text in _strings(item, "")
            for word in mixed_words(text)
        ]
    return result


def all_hits(root: Path) -> dict[tuple[Surface, str], list[MixingHit]]:
    return {
        (surface, item_id): hits
        for surface in SURFACES
        for item_id, hits in surface_hits(root, surface).items()
    }


def load_pending(root: Path) -> frozenset[tuple[Surface, str]]:
    path = root / PENDING_PATH
    if not path.exists():
        return frozenset()
    raw = json.loads(path.read_text(encoding="utf-8"))
    pending = raw.get("pending")
    if raw.get("contract_version") != "1.0.0" or not isinstance(pending, dict):
        raise ValueError(f"{PENDING_PATH} must be contract 1.0.0 with a pending object")
    unknown = sorted(set(pending) - set(SURFACES))
    if unknown:
        raise ValueError(f"{PENDING_PATH} names unknown surfaces: {', '.join(unknown)}")
    keys: list[tuple[Surface, str]] = []
    for surface in SURFACES:
        ids = [str(item) for item in pending.get(surface, [])]
        if len(ids) != len(set(ids)):
            raise ValueError(f"{PENDING_PATH} lists a {surface} item twice")
        keys.extend((surface, item_id) for item_id in ids)
    return frozenset(keys)


def require_language_contract(root: Path) -> tuple[tuple[Surface, str], ...]:
    """Reject mixed text outside the pending list; return pending items that are now clean."""
    hits = all_hits(root)
    pending = load_pending(root)
    unknown = sorted(f"{surface}:{item_id}" for surface, item_id in pending - set(hits))
    if unknown:
        raise ValueError(f"language-mixing pending list names unknown items: {', '.join(unknown)}")
    failures = [
        f"{surface}:{item_id} ({', '.join(sorted({hit.word for hit in item_hits})[:6])})"
        for (surface, item_id), item_hits in sorted(hits.items())
        if item_hits and (surface, item_id) not in pending
    ]
    if failures:
        raise ValueError(
            "Japanese reader-facing text mixes in ordinary English words; write them in Japanese "
            "(docs/article-style.md §2.1): " + "; ".join(failures)
        )
    return tuple(sorted(key for key in pending if not hits[key]))


def pending_document(keys: set[tuple[Surface, str]]) -> dict[str, Any]:
    return {
        "contract_version": "1.0.0",
        "pending": {
            surface: sorted(item_id for key_surface, item_id in keys if key_surface == surface)
            for surface in SURFACES
        },
    }
