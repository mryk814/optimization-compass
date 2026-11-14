# Content authoring guide

Lessons live under `content/methods` and `content/concepts`. They are CommonMark files
with strict YAML frontmatter. Run the exporter before committing; unsupported or unsafe
content must fail the build.

## Frontmatter

All pages require `content_id`, `kind`, `title_ja`, `title_en`, `summary`, `source_ids`,
`status`, and `last_reviewed`. `summary` is the one- or two-sentence description shown on cards,
in search, and as the page description; it is written separately from the body's opening.
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
summary: カードと検索に出る1〜2文の説明です。
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

For short case descriptions and other structured explanatory text, write Japanese as the sentence
language. Keep an academic English term only when it improves searchability or disambiguation, and
put it at first use in parentheses after the Japanese term: `制約（constraint）`, `追従誤差（tracking
error）`. Do not switch languages mid-sentence for ordinary words or write bare fragments such as
`costを最小化する`; use `コスト（cost）を最小化する` instead. Variables, sets, objectives, and
constraints must be enclosed in inline TeX `$...$`; the site export converts them through the same
MathML renderer used by lesson pages. Keep the raw TeX in the seed/source file and never hand-edit
the generated site data.

## Body style

What an article should achieve, how it is built around its moving figure, and the writing
conventions are in [`docs/writing-articles.md`](writing-articles.md). The rules below cover the
Markdown format only.

- The page shell owns `h1`; start sections with `##` and do not skip heading levels.
- Ordered/unordered lists, blockquotes, tables, inline code, emphasis, and links use
  standard Markdown.
- Inline math uses `$...$`; display math uses a `$$` block. The site's LaTeX→MathML conversion
  does not support alignment environments (`aligned`, `&`, `\\` line breaks); use separate `$$`
  blocks instead. Validation rejects them.
- Fenced code requires one supported language: `python`, `bash`, `json`, `yaml`, or
  `text`.
- Callouts use `::: note`, `::: tip`, or `::: warning`, closed by `:::`.
- A figure uses `![alt text](./media/file.svg "visible caption")`. Store its file at
  `site/public/media/file.svg`; both alt text and caption are required.
- An interactive figure uses `::: explorable <id>` with exactly one caption paragraph, closed by
  `:::`. The id must be a figure folder `site/src/features/explorable/figures/<id>/`; see
  [`docs/explorables.md`](explorables.md) for when to use one and how to add a new figure.
- External links must be HTTPS. App routes use `#/path`, site files use `/path`, and a
  heading link uses its generated slug such as `#python`.
- Raw HTML is never allowed. Add a supported construct to the pipeline instead.

## What publication checks

There is no length floor and no required section list. A published article must parse, reference
known sources and content IDs, have every internal app link (`#/...`) resolve to a public route,
use display math the site can render, and keep ordinary English words out of Japanese sentences.

## Verification

```powershell
uv run python scripts/check_article.py content/concepts/<file>.md
uv run optimization-compass validate content
```

For a visible correction, check the rendered GitHub Pages preview or deployed page. Run the site
build or browser checks only when the renderer, route, interaction, or generated artifact contract
changed.
