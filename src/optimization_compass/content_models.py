from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Literal, Self

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from optimization_compass.content_markdown import ContentHeading, render_markdown


class _Frontmatter(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    content_id: str = Field(min_length=1)
    kind: Literal["method", "concept"]
    method_id: str | None = None
    title_ja: str = Field(min_length=1)
    title_en: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    source_ids: list[str] = Field(min_length=1)
    prerequisites: list[str] = Field(default_factory=list)
    related_ids: list[str] = Field(default_factory=list)
    visualization_ids: list[str] = Field(default_factory=list)
    comparison_ids: list[str] = Field(default_factory=list)
    aliases: list[str] = Field(default_factory=list)
    visualization_aliases: list[str] = Field(default_factory=list)
    comparison_aliases: list[str] = Field(default_factory=list)
    status: Literal["published", "draft"]
    last_reviewed: date

    @field_validator(
        "content_id",
        "method_id",
        "title_ja",
        "title_en",
        "summary",
        mode="before",
    )
    @classmethod
    def strings_must_not_be_blank(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            raise ValueError("value must not be blank")
        return value

    @field_validator(
        "source_ids",
        "prerequisites",
        "related_ids",
        "visualization_ids",
        "comparison_ids",
        "aliases",
        "visualization_aliases",
        "comparison_aliases",
    )
    @classmethod
    def lists_must_be_unique_and_nonblank(cls, values: list[str]) -> list[str]:
        if any(not isinstance(value, str) or not value.strip() for value in values):
            raise ValueError("list values must be non-empty strings")
        if len(values) != len(set(values)):
            raise ValueError("list values must be unique")
        return values

    @model_validator(mode="after")
    def validate_kind_identity(self) -> Self:
        if self.kind == "method" and self.method_id is None:
            raise ValueError("method content requires method_id")
        if self.kind == "concept" and self.method_id is not None:
            raise ValueError("concept content must not define method_id")
        return self


@dataclass(frozen=True)
class ContentPage:
    content_id: str
    kind: str
    method_id: str | None
    title_ja: str
    title_en: str
    summary: str
    source_ids: tuple[str, ...]
    prerequisites: tuple[str, ...]
    related_ids: tuple[str, ...]
    visualization_ids: tuple[str, ...]
    comparison_ids: tuple[str, ...]
    aliases: tuple[str, ...]
    visualization_aliases: tuple[tuple[str, str], ...]
    comparison_aliases: tuple[tuple[str, str], ...]
    status: str
    last_reviewed: str
    body: str
    html: str
    toc: tuple[ContentHeading, ...]


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
    try:
        loaded = yaml.safe_load(raw[4:end])
    except yaml.YAMLError as error:
        raise ValueError(f"{path}: invalid YAML frontmatter: {error}") from error
    if not isinstance(loaded, dict):
        raise ValueError(f"{path}: frontmatter must be a YAML mapping")
    try:
        fields = _Frontmatter.model_validate(loaded)
    except ValueError as error:
        raise ValueError(f"{path}: invalid frontmatter: {error}") from error
    body = raw[end + 5 :].strip()
    rendered = render_markdown(body, path=path)
    if rendered.summary != fields.summary:
        raise ValueError(f"{path}: frontmatter summary must match the first body paragraph exactly")
    return ContentPage(
        content_id=fields.content_id,
        kind=fields.kind,
        method_id=fields.method_id,
        title_ja=fields.title_ja,
        title_en=fields.title_en,
        summary=fields.summary,
        source_ids=tuple(fields.source_ids),
        prerequisites=tuple(fields.prerequisites),
        related_ids=tuple(fields.related_ids),
        visualization_ids=tuple(fields.visualization_ids),
        comparison_ids=tuple(fields.comparison_ids),
        aliases=tuple(fields.aliases),
        visualization_aliases=_pairs(fields.visualization_aliases),
        comparison_aliases=_pairs(fields.comparison_aliases),
        status=fields.status,
        last_reviewed=fields.last_reviewed.isoformat(),
        body=body,
        html=rendered.html,
        toc=rendered.toc,
    )


def _pairs(values: list[str]) -> tuple[tuple[str, str], ...]:
    pairs: list[tuple[str, str]] = []
    for item in values:
        target_id, separator, route = item.partition("|")
        if not separator or not target_id.strip() or not route.startswith("/"):
            raise ValueError(f"frontmatter relation alias is invalid: {item}")
        pairs.append((target_id.strip(), route.strip()))
    return tuple(pairs)
