"""Quality contracts for published concepts and the article language check."""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass

from optimization_compass.content_models import ContentPage

MINIMUM_CONCEPT_SUMMARY_CHARACTERS = 35
MINIMUM_CONCEPT_BODY_CHARACTERS = 1_200
MINIMUM_CONCEPT_TOC_ENTRIES = 4

_NEXT_SECTION_PATTERN = re.compile(
    r"(?:\A|\n)## (?:次に読む|困りごとから関連する(?:問題|手法)へ)\s*\n(?P<body>.*?)(?=\n## |\Z)",
    re.DOTALL,
)
_LINK_PATTERN = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
_FENCED_CODE_PATTERN = re.compile(r"^```.*?^```$", re.MULTILINE | re.DOTALL)
_DISPLAY_MATH_PATTERN = re.compile(r"^\$\$.*?^\$\$$", re.MULTILINE | re.DOTALL)
_MARKDOWN_LINK_PATTERN = re.compile(r"\[([^\]]+)\]\([^)]+\)")
_BARE_ENGLISH_PARTICLE_PATTERN = re.compile(
    r"\b(?:cost|model|state|design|mesh|solver|tolerance|field|objective|constraint|"
    r"gradient|residual|failure|success|boundary|load|scale|iteration|policy|reason|"
    r"status|update|quality|parameter|geometry|physics|optimization|progress|valid|"
    r"unknown|time|storage)(?:を|は|が|の|に|で|へ|と|も|だけ|した|する|しない|"
    r"まで|から|より)"
)
_GLUED_ENGLISH_PATTERN = re.compile(
    r"(?:statefield|designfield|statevariable|designvariable|"
    r"失敗status|失敗theater|状態field|状態status|設計field|設計status)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ConceptQualityRow:
    content_id: str
    summary_characters: int
    body_characters: int
    toc_entries: int
    valid_next_links: tuple[str, ...]
    invalid_next_links: tuple[str, ...]

    @property
    def meets_floor(self) -> bool:
        return (
            self.summary_characters >= MINIMUM_CONCEPT_SUMMARY_CHARACTERS
            and self.body_characters >= MINIMUM_CONCEPT_BODY_CHARACTERS
            and self.toc_entries >= MINIMUM_CONCEPT_TOC_ENTRIES
            and bool(self.valid_next_links)
            and not self.invalid_next_links
        )


@dataclass(frozen=True)
class StyleWarning:
    content_id: str
    code: str
    line: int
    detail: str


def public_content_routes(
    pages: Iterable[ContentPage],
    *,
    gallery_ids: Iterable[str] = (),
    comparison_ids: Iterable[str] = (),
    formulation_ids: Iterable[str] = (),
    path_ids: Iterable[str] = (),
) -> frozenset[str]:
    """Return public routes that can be proven from canonical authoring inputs."""
    routes: set[str] = set()
    for page in pages:
        if page.status != "published":
            continue
        routes.add(f"#/learn/{page.content_id}")
        routes.update(f"#{alias}" for alias in page.aliases)
        if page.method_id:
            routes.add(f"#/methods/{page.method_id}")
    routes.update(f"#/gallery/{case_id}" for case_id in gallery_ids)
    routes.update(f"#/compare/{comparison_id}" for comparison_id in comparison_ids)
    # Every problem archetype has a formulation page, with or without an article.
    routes.update(f"#/formulations/{problem_id}" for problem_id in formulation_ids)
    routes.update(f"#/paths/{path_id}" for path_id in path_ids)
    return frozenset(routes)


def inspect_concept(page: ContentPage, known_routes: frozenset[str]) -> ConceptQualityRow:
    """Measure the hard publication floor for one concept page."""
    if page.kind != "concept":
        raise ValueError(f"{page.content_id} is not a concept page")
    match = _NEXT_SECTION_PATTERN.search(page.body)
    links = tuple(_LINK_PATTERN.findall(match.group("body"))) if match else ()
    internal_links = tuple(link for link in links if link.startswith("#/"))
    valid = tuple(link for link in internal_links if link in known_routes)
    invalid = tuple(link for link in internal_links if link not in known_routes)
    return ConceptQualityRow(
        content_id=page.content_id,
        summary_characters=len(page.summary),
        body_characters=len(page.body),
        toc_entries=len(page.toc),
        valid_next_links=valid,
        invalid_next_links=invalid,
    )


def require_published_concept_quality(
    pages: Iterable[ContentPage], known_routes: frozenset[str]
) -> tuple[ConceptQualityRow, ...]:
    """Reject published concepts that expose a visibly incomplete learning surface."""
    published = [page for page in pages if page.kind == "concept" and page.status == "published"]
    rows = tuple(inspect_concept(page, known_routes) for page in published)
    failures = [row for row in rows if not row.meets_floor]
    if failures:
        detail = "; ".join(
            f"{row.content_id} (summary={row.summary_characters}, body={row.body_characters}, "
            f"toc={row.toc_entries}, next={len(row.valid_next_links)}, "
            f"invalid={','.join(row.invalid_next_links) or '-'})"
            for row in failures
        )
        raise ValueError(f"published concept quality floor is not met: {detail}")
    return rows


def language_contract_warnings(page: ContentPage) -> tuple[StyleWarning, ...]:
    """Detect clear Japanese/English prose mixing in the article being prepared.

    Canonical English terms, proper names, code, formulas, and identifiers remain allowed.
    This check targets only English ordinary words joined directly to Japanese grammar or
    glued into Japanese compounds. It is intentionally target-specific so legacy pages are
    not made to fail merely because an unrelated article is being changed.
    """
    body = _FENCED_CODE_PATTERN.sub("", page.body)
    body = _DISPLAY_MATH_PATTERN.sub("", body)
    warnings: list[StyleWarning] = []
    for line_number, raw_line in enumerate(body.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith(("|", ":::", "![")):
            continue
        visible = _MARKDOWN_LINK_PATTERN.sub(r"\1", line)
        visible = re.sub(r"`[^`]+`", "code", visible)
        matches = [
            *_BARE_ENGLISH_PARTICLE_PATTERN.finditer(visible),
            *_GLUED_ENGLISH_PATTERN.finditer(visible),
        ]
        for match in matches:
            warnings.append(
                StyleWarning(
                    page.content_id,
                    "prose.language-mixing",
                    line_number,
                    match.group(0),
                )
            )
    return tuple(warnings)
