# ADR 0013: The public Atlas is Japanese-first and English-term-aware

- Status: accepted
- Date: 2026-07-17
- Issue: #152
- Related: #66, #97, #123, #145

## Context

Optimization Compass explains optimization mainly in Japanese while retaining English method names,
technical terms, terminology aliases, source titles, stable IDs, and fields such as `title_en`. This
combination is useful for readers who learn in Japanese and later search papers, documentation, or APIs
in English.

The product has not previously stated whether those English fields are terminology metadata or a promise
of a complete English edition. Treating them as an implicit bilingual promise would make publication and
Coverage ambiguous. Filling the gap with unreviewed machine translation would also weaken the source,
review, and terminology guarantees applied to authored content.

## Decision

Adopt **Japanese-first, English-term-aware** as the current public language contract.

Japanese is the required primary language for explanatory prose, learner-facing instructions, and
published learning journeys. Canonical English terminology remains visible and searchable so that readers
can connect Japanese explanations to papers, documentation, libraries, APIs, and established method names.

Stable IDs, schema keys, contract fields, code, formulas, and API identifiers remain language-neutral or
retain their authoritative spelling. Source titles and proper names retain the form used by the source or
rights holder.

### Publication requirements

For a Markdown lesson with `status: published`:

- `title_ja`, `summary`, and the article body must provide a complete Japanese explanation;
- required relations, sources, review metadata, and ordinary content validation must pass;
- `title_en` must identify the canonical English term, but it is terminology and retrieval metadata;
- `title_en`, English terminology aliases, or abbreviations do not constitute a translated article.

Other public surfaces follow the same rule: Japanese owns explanatory copy and task instructions;
English fields identify canonical terminology where their existing contracts require them. A Gallery,
comparison, scenario, or Coverage row is not bilingual merely because it contains `title_en`.

### Search and terminology aliases

The existing generated lexical search remains one cross-language index. It can match Japanese titles and
prose together with English titles, canonical `terminology_aliases` records, abbreviations, canonical
names, and related terms. Search results may therefore be found with either language, while their
explanatory summary remains Japanese.

Content frontmatter fields named `aliases`, `visualization_aliases`, and `comparison_aliases` are a
different contract: they contain alternate URL routes. They do not author terminology, synonyms, or
lexical-search terms.

This behavior is terminology-aware retrieval, not a locale switch and not proof that an English article
exists. Search metadata continues to be generated from canonical inputs; a second hand-maintained English
index is not introduced.

### Missing translations and fallback

The current product has no separate English publication surface, so missing full English prose does not
block Japanese publication. The UI must not label Japanese pages as English pages or silently generate,
store, or serve machine-translated prose as an authored translation.

If a future locale-specific surface requests content that has not been translated, it must expose that
absence explicitly. Showing reviewed Japanese content as Japanese may be offered as an explicit user
choice, but it must not be presented as an English fallback.

### Coverage semantics

Current Coverage measures the completeness of the Japanese primary-language learning contract and its
artifact connections. `title_en`, terminology aliases, and optional translated fragments neither satisfy
nor reduce a Coverage status. Current `coverage.json` and learning-journey contracts do not gain locale
fields as part of this decision.

Per-language completeness becomes a separate versioned Coverage concern only when the project commits to
a full additional-language publication surface.

### Authored and generated UI strings

- Learner-facing labels and instructions authored in React, Markdown, or validated seeds use Japanese.
- Canonical English method names, product/API names, code, formulas, units, and source titles keep their
  authoritative spelling.
- Generated UI copy inherits the language responsibility of its canonical input; generators do not
  translate prose.
- Stable IDs, URL identifiers, schema keys, and API fields are not localized.

## Full-i18n trigger

A full internationalization initiative begins only after an explicit product decision to publish and
maintain another complete language surface, supported by user demand or a concrete distribution partner.
That initiative must jointly define:

- locale selection and canonical URL behavior;
- translated field and article contracts;
- translator/reviewer provenance and freshness rules;
- missing-locale presentation without silent fallback;
- locale-aware search evaluation and per-language Coverage;
- validation, accessibility, release, and maintenance ownership.

Until then, ad hoc full-article translation, locale routing, translation-memory infrastructure, and
machine-translation fallback are non-goals.

## Consequences

Contributors can publish a complete reviewed Japanese article without creating a full English duplicate.
They must still supply canonical English terminology where the existing schema requires it. Readers can
search established English terms and abbreviations without the product overstating its English coverage.

This ADR does not translate existing content, remove English terminology, localize stable IDs, change the
search schema, or change the Coverage JSON contract.
