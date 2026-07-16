# Content authoring guide

Lessons live under `content/methods` and `content/concepts`. They are CommonMark files
with strict YAML frontmatter. Run the exporter before committing; unsupported or unsafe
content must fail the build.

## Frontmatter

All pages require `content_id`, `kind`, `title_ja`, `title_en`, `summary`, `source_ids`,
`status`, and `last_reviewed`. `summary` must exactly match the first prose paragraph.
`kind` is `method` or `concept`; method pages also require `method_id`. Unknown fields,
duplicate list items, blank IDs, and concept pages with a `method_id` are errors.

Optional relation lists are `prerequisites`, `related_ids`, `visualization_ids`, and
`comparison_ids`. Routing metadata uses `aliases`, `visualization_aliases`, and
`comparison_aliases`; a relation alias is written as `target-id|/route`. These frontmatter
fields contain URL routes only. They are not terminology aliases and do not add words to lexical
search.

```yaml
---
content_id: method.example
kind: method
method_id: M_EXAMPLE
title_ja: Example
title_en: Example
summary: 最初の本文段落と同じ要約です。
source_ids: [S001]
status: draft
last_reviewed: 2026-07-15
---
```

## Language and publication

The public Atlas is Japanese-first and English-term-aware. The authoritative decision is
[ADR 0013](adr/0013-japanese-first-language-strategy.md).

| Field or surface | Language responsibility | Requirement for `published` |
|---|---|---|
| `title_ja` | Japanese public title | Required and complete |
| `summary` | Japanese card, search-result, and SEO explanation | Required; must match the first body paragraph |
| Markdown body | Japanese explanatory prose | Required and understandable without an English article |
| `title_en` | Canonical English term and retrieval metadata | Required by the current schema; not a translated article |
| frontmatter `aliases`, `visualization_aliases`, `comparison_aliases` | Alternate URL routes | Add routes only; never put lexical terms or abbreviations here |
| canonical `terminology_aliases` records and abbreviations | Japanese/English retrieval terms from structured knowledge | Add through the canonical terminology authority, never content frontmatter; they do not satisfy prose completeness |
| code, formulas, product/API names, source titles | Authoritative original notation | Preserve spelling; do not translate identifiers |

`status: published` therefore means that the Japanese learning surface is publishable. It does not
claim that a full English version exists. Do not add silent machine-translated prose or treat an English
title or terminology alias as a locale fallback. The current search index intentionally combines
Japanese prose with English canonical terms and canonical terminology records, including abbreviations
and synonyms. This is cross-language retrieval, not locale selection. Content frontmatter route aliases
only redirect URLs and are not lexical search metadata.

UI instructions and generated explanatory text follow the same boundary: their canonical authoring
input supplies Japanese prose, and generators do not translate it. Stable IDs, URL identifiers, schema
keys, and API fields remain unlocalized.

## Body style

Prose style — sentence tone, terminology spelling, and canonical section headings — is
defined in [`.agents/skills/article-style/SKILL.md`](../.agents/skills/article-style/SKILL.md).
Read it before writing or revising article text. The rules below cover structure only.

- The page shell owns `h1`; start sections with `##` and do not skip heading levels.
- Keep the first paragraph short enough to work as a card and SEO description.
- Ordered/unordered lists, blockquotes, tables, inline code, emphasis, and links use
  standard Markdown.
- Inline math uses `$...$`; display math uses a `$$` block.
- Fenced code requires one supported language: `python`, `bash`, `json`, `yaml`, or
  `text`.
- Callouts use `::: note`, `::: tip`, or `::: warning`, closed by `:::`.
- A figure uses `![alt text](./media/file.svg "visible caption")`. Store its file at
  `site/public/media/file.svg`; both alt text and caption are required.
- External links must be HTTPS. App routes use `#/path`, site files use `/path`, and a
  heading link uses its generated slug such as `#python`.
- Raw HTML is never allowed. Add a supported construct to the pipeline instead.

## Verification

```powershell
uv run --extra dev pytest tests/test_content_models.py
uv run optimization-compass export-site-data --output site/public/data
uv run python scripts/verify_content.py
cd site
npm.cmd run typecheck
npm.cmd test -- --run
npm.cmd run build
```

Inspect at least one lesson containing math, Python, a table, a callout, a figure, and
an external link at desktop and narrow viewport sizes. Tab through the TOC and links;
focus must move to the selected heading without changing the app route.
