from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

_REQUIRED = {"content_id", "kind", "title_ja", "title_en", "source_ids", "status", "last_reviewed"}


@dataclass(frozen=True)
class ContentPage:
    content_id: str
    kind: str
    title_ja: str
    title_en: str
    source_ids: tuple[str, ...]
    related_ids: tuple[str, ...]
    visualization_ids: tuple[str, ...]
    comparison_ids: tuple[str, ...]
    status: str
    last_reviewed: str
    body: str


def load_content(directory: Path) -> list[ContentPage]:
    pages = [parse_content(path) for path in sorted(directory.rglob("*.md"))]
    ids = {page.content_id for page in pages}
    if len(ids) != len(pages):
        raise ValueError("content IDs must be unique")
    for page in pages:
        for related_id in (*page.related_ids, *page.visualization_ids, *page.comparison_ids):
            if not related_id.strip():
                raise ValueError(f"blank related ID in {page.content_id}")
    return pages


def parse_content(path: Path) -> ContentPage:
    raw = path.read_text(encoding="utf-8")
    if not raw.startswith("---\n"):
        raise ValueError(f"{path}: frontmatter must start with ---")
    try:
        end = raw.index("\n---\n", 4)
    except ValueError as error:
        raise ValueError(f"{path}: missing frontmatter terminator") from error
    fields: dict[str, str] = {}
    for line in raw[4:end].splitlines():
        key, separator, value = line.partition(":")
        if not separator:
            raise ValueError(f"{path}: malformed frontmatter line")
        fields[key.strip()] = value.strip()
    missing = _REQUIRED - fields.keys()
    if missing:
        raise ValueError(f"{path}: missing frontmatter fields: {', '.join(sorted(missing))}")
    kind = fields["kind"]
    if kind not in {"method", "concept"}:
        raise ValueError(f"{path}: unsupported content kind {kind}")
    if fields["status"] not in {"published", "draft"}:
        raise ValueError(f"{path}: unsupported content status {fields['status']}")
    return ContentPage(
        content_id=_nonblank(fields["content_id"], path),
        kind=kind,
        title_ja=_nonblank(fields["title_ja"], path),
        title_en=_nonblank(fields["title_en"], path),
        source_ids=_list(fields["source_ids"]),
        related_ids=_list(fields.get("related_ids", "[]")),
        visualization_ids=_list(fields.get("visualization_ids", "[]")),
        comparison_ids=_list(fields.get("comparison_ids", "[]")),
        status=fields["status"],
        last_reviewed=_nonblank(fields["last_reviewed"], path),
        body=raw[end + 5 :].strip(),
    )


def _list(value: str) -> tuple[str, ...]:
    if not re.fullmatch(r"\[.*\]", value):
        raise ValueError(f"frontmatter list is invalid: {value}")
    return tuple(item.strip().strip("\"'") for item in value[1:-1].split(",") if item.strip())


def _nonblank(value: str, path: Path) -> str:
    if not value.strip():
        raise ValueError(f"{path}: frontmatter value must not be blank")
    return value
