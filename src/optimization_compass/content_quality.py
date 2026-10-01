"""Quality contracts for published concepts and review-oriented prose warnings."""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass

from optimization_compass.content_models import ContentPage
from optimization_compass.content_skeletons import SKELETONS, skeleton_gaps, skeleton_kind

FORMULATION_SECTIONS = SKELETONS["formulation"]

MINIMUM_CONCEPT_SUMMARY_CHARACTERS = 35
MINIMUM_CONCEPT_BODY_CHARACTERS = 1_200
MINIMUM_CONCEPT_TOC_ENTRIES = 4

_NEXT_SECTION_PATTERN = re.compile(
    r"(?:\A|\n)## 次に読む\s*\n(?P<body>.*?)(?=\n## |\Z)",
    re.DOTALL,
)
_LINK_PATTERN = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
_FENCED_CODE_PATTERN = re.compile(r"^```.*?^```$", re.MULTILINE | re.DOTALL)
_DISPLAY_MATH_PATTERN = re.compile(r"^\$\$.*?^\$\$$", re.MULTILINE | re.DOTALL)
_MARKDOWN_LINK_PATTERN = re.compile(r"\[([^\]]+)\]\([^)]+\)")
_SENTENCE_PATTERN = re.compile(r"[^。！？]+[。！？]")
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
_NONCANONICAL_HEADINGS = {
    "Python例": "Python",
    "見るべき診断値": "診断値",
    "失敗の兆候": "失敗・切替の兆候",
    "失敗したときに確認する": "失敗・切替の兆候",
    "向いている問題": "向いている条件",
    "向いている／避ける条件": "向く条件・避ける条件",
    "次に見る": "次に読む",
}
_META_PHRASES = ("本稿では", "このページでは", "要するに")
# Author work reports: readers need the result and how to check it, not what the author did.
_WORK_REPORT_PHRASES = ("確かめました", "検算", "確認しました", "実行した値", "この教材のため")
# Pasted program output such as 2.500000; meaningful digits are enough in prose and tables.
_OVERPRECISE_NUMBER_PATTERN = re.compile(r"(?<![\d.])\d+\.\d{5,}(?![\d.])")
_INLINE_MATH_PATTERN = re.compile(r"\$[^$]+\$")
# Starting a line with one of these ties it to the previous sentence, so it breaks a choppy run.
_CONNECTIVES = (
    "だから",
    "ところが",
    "つまり",
    "しかし",
    "ただし",
    "そのため",
    "したがって",
    "一方",
    "すると",
    "このため",
    "なぜなら",
    "逆に",
)
CHOPPY_RUN_LINES = 6


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


def is_formulation_article(page: ContentPage) -> bool:
    return skeleton_kind(page) == "formulation"


def formulation_skeleton_gaps(page: ContentPage) -> tuple[str, ...]:
    """Return the problems with a formulation article's section skeleton, or an empty tuple."""
    return skeleton_gaps(page) if is_formulation_article(page) else ()


def require_published_concept_quality(
    pages: Iterable[ContentPage], known_routes: frozenset[str]
) -> tuple[ConceptQualityRow, ...]:
    """Reject published concepts that expose a visibly incomplete learning surface."""
    published = [page for page in pages if page.kind == "concept" and page.status == "published"]
    skeleton_failures = [
        f"{page.content_id} ({', '.join(gaps)})"
        for page in published
        if (gaps := formulation_skeleton_gaps(page))
    ]
    if skeleton_failures:
        raise ValueError(
            "formulation articles must follow the formulation skeleton: "
            + "; ".join(skeleton_failures)
        )
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


def style_warnings(page: ContentPage) -> tuple[StyleWarning, ...]:
    """Return review warnings without turning the repository's legacy prose red."""
    body = _FENCED_CODE_PATTERN.sub("", page.body)
    body = _DISPLAY_MATH_PATTERN.sub("", body)
    warnings: list[StyleWarning] = []

    def warn(code: str, line_number: int, detail: str) -> None:
        warnings.append(StyleWarning(page.content_id, code, line_number, detail))

    choppy_run: list[int] = []

    def close_choppy_run() -> None:
        if len(choppy_run) >= CHOPPY_RUN_LINES:
            warn("prose.choppy", choppy_run[0], f"{len(choppy_run)} one-sentence lines")
        choppy_run.clear()

    for line_number, raw_line in enumerate(body.splitlines(), start=1):
        line = raw_line.strip()
        visible = _MARKDOWN_LINK_PATTERN.sub(r"\1", line)
        visible = re.sub(r"`[^`]+`", "code", visible)
        if line.startswith("|"):
            # Tables are skipped by the prose checks, but pasted output digits still show there.
            for number in _overprecise_numbers(visible):
                warn("number.overprecise", line_number, number)
        if not line or line.startswith(("|", ":::", "![")):
            close_choppy_run()
            continue
        if line.startswith("## "):
            close_choppy_run()
            heading = line.removeprefix("## ").strip()
            replacement = _NONCANONICAL_HEADINGS.get(heading)
            if replacement:
                warn("heading.noncanonical", line_number, f"{heading} -> {replacement}")
            continue
        for number in _overprecise_numbers(visible):
            warn("number.overprecise", line_number, number)
        sentences = [sentence.strip() for sentence in _SENTENCE_PATTERN.findall(visible)]
        for sentence in sentences:
            if len(sentence) > 90:
                warn("sentence.long", line_number, f"{len(sentence)} characters")
            comma_count = sentence.count("、")
            if comma_count >= 3:
                warn("sentence.commas", line_number, f"{comma_count} Japanese commas")
            for phrase in _META_PHRASES:
                if phrase in sentence:
                    warn("prose.meta", line_number, phrase)
            for phrase in _WORK_REPORT_PHRASES:
                if phrase in sentence:
                    warn("prose.work-report", line_number, phrase)
        is_paragraph = not line.startswith(("#", "-", "*", ">")) and not re.match(r"\d+\. ", line)
        if not is_paragraph or len(sentences) != 1:
            close_choppy_run()
            continue
        if visible.startswith(_CONNECTIVES):
            # A connective ties this line to the previous one; it may still open the next run.
            close_choppy_run()
        choppy_run.append(line_number)
    close_choppy_run()
    return tuple(sorted(warnings, key=lambda warning: warning.line))


def _overprecise_numbers(visible: str) -> list[str]:
    return _OVERPRECISE_NUMBER_PATTERN.findall(_INLINE_MATH_PATTERN.sub("", visible))


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


def render_content_quality_report(
    concept_rows: Iterable[ConceptQualityRow], pages: Iterable[ContentPage]
) -> str:
    """Render a stable review report; warnings are debt visibility, not a global gate."""
    concepts = tuple(sorted(concept_rows, key=lambda row: row.content_id))
    page_list = tuple(sorted(pages, key=lambda page: page.content_id))
    warnings = tuple(warning for page in page_list for warning in style_warnings(page))
    warning_counts: dict[str, int] = {}
    for warning in warnings:
        warning_counts[warning.code] = warning_counts.get(warning.code, 0) + 1
    lines = [
        "# Content quality report",
        "",
        f"- Published concept guides: `{len(concepts)}`",
        f"- Meeting the concept floor: `{sum(row.meets_floor for row in concepts)}`",
        f"- Below the concept floor: `{sum(not row.meets_floor for row in concepts)}`",
        f"- Prose review warnings: `{len(warnings)}`",
        "",
        "## Concept publication floor",
        "",
        "| Content | Summary | Body | TOC | Valid next links | Invalid next links | Result |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in concepts:
        lines.append(
            f"| `{row.content_id}` | {row.summary_characters} | {row.body_characters} | "
            f"{row.toc_entries} | {len(row.valid_next_links)} | "
            f"{len(row.invalid_next_links)} | {'pass' if row.meets_floor else 'fail'} |"
        )
    lines.extend(["", "## Prose warning summary", ""])
    if warning_counts:
        lines.extend(f"- `{code}`: {count}" for code, count in sorted(warning_counts.items()))
    else:
        lines.append("- No warnings.")
    lines.extend(
        [
            "",
            "| Content | Warnings |",
            "|---|---:|",
        ]
    )
    for page in page_list:
        count = sum(warning.content_id == page.content_id for warning in warnings)
        lines.append(f"| `{page.content_id}` | {count} |")
    lines.extend(
        [
            "",
            "## Contract",
            "",
            "- Published concepts require a 35-character summary, 1,200-character body, "
            "four table-of-contents entries, and a valid internal link under `次に読む`.",
            "- The concept floor is a hard publication gate.",
            "- Sentence length, comma density, meta prose, and legacy headings are "
            "review warnings.",
            "- Author work reports, over-precise pasted numbers (five or more decimals), and "
            f"runs of {CHOPPY_RUN_LINES}+ unconnected one-sentence lines are review warnings.",
            "- Existing warnings remain visible without failing unrelated changes.",
            "- `ready content` rejects warnings on the article being prepared, so changed articles "
            "do not add new prose debt.",
            "",
        ]
    )
    return "\n".join(lines)
