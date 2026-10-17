<!-- Generated publication metadata; do not edit release facts. -->
<!-- Run `uv run python scripts/dataset_publication.py check` before committing. -->

# Optimization Compass Optimization Atlas Dataset

最適化問題の構造、候補・除外手法、実装、事例、比較、教材可視化を根拠付きで接続する、版管理されたデータセットです。

A versioned, evidence-linked dataset that connects optimization problem structure, candidate and excluded methods, implementations, examples, comparisons, and educational visualizations.

## Release identity

| Field | Value |
|---|---|
| Dataset version | `0.18.25` |
| Release date | `2026-10-14` |
| Source commit | [`8b11e62c4153d383caac67c184f2fc2be2d3278f`](https://github.com/mryk814/optimization-compass/commit/8b11e62c4153d383caac67c184f2fc2be2d3278f) |
| Source tag | [`v0.18.25`](https://github.com/mryk814/optimization-compass/releases/tag/v0.18.25) |
| Database SHA-256 | `54386be76adb2e9b859d75328ba80695fbbaa5fe508ac7e68836d7c5bff823f4` |
| Manifest SHA-256 | `e4fe3c70dc9d82460b7b11c8221bb0757570e2629075f9a5cc9bb632cc197de6` |
| Complete bundle | [download](https://github.com/mryk814/optimization-compass/releases/download/v0.18.25/optimization_method_selection_database_v0.18.25_bundle.zip) (6,787,658 bytes) |
| Bundle SHA-256 | `e19ec94c441d2f06063a0afcdbf115bd34b75011fa968fe039345474f38cba2b` |
| Citable archive | 未登録（この版はGitHub Release bundleでhash検証できます） |

The complete bundle contains the released SQLite, JSON, JSONL, CSV, Excel, SQL schema,
release report, site-data, manifest, and license/notice files. Its `bundle-index.json` and
canonical release manifest fix the byte count and SHA-256 of every member.

## Scope and evidence model

Optimization Compass records problem structure, methods, implementations, examples,
comparisons, learning artifacts, sources, evidence links, and explicit support states.
It preserves the distinction between a method and an implementation, and between
`unknown`, `not_applicable`, and `unsupported`.
It is intended for research, education, and traceable exploration rather than context-free ranking.

## Language position

Japanese (`ja`) is the primary explanatory language.
Canonical English (`en`) technical terms, aliases,
source titles, APIs, and stable IDs remain visible and searchable. English metadata does not
imply complete English-language articles.

## Coverage limits

- The catalog is curated and incomplete; absence is not evidence that a method, implementation, or problem class does not exist.
- Recommendation relations are conditional on recorded problem features, available information, budgets, and evidence scope.
- Linked third-party sources are identified by metadata and URLs; the referenced works are not redistributed or relicensed.

## Non-guarantees

- The Atlas does not guarantee that a listed method finds a global or local optimum.
- The Atlas does not guarantee feasibility, robustness, or safety in a real system.
- Educational examples and comparisons do not establish universal rankings or performance guarantees.

## Licensing and attribution

- Dataset and distributed structured data: `CC-BY-4.0`.
- Creator metadata: TAKUYA OTANI.
- Attribution: Optimization Compass dataset, Copyright 2026 TAKUYA OTANI and Optimization Compass contributors, licensed under CC BY 4.0, https://github.com/mryk814/optimization-compass
- Third-party papers, documentation, repositories, standards, product names, and linked works retain
  their own rights. See the bundle's `licenses/NOTICE.txt` and the source audit at
  [https://github.com/mryk814/optimization-compass/blob/8b11e62c4153d383caac67c184f2fc2be2d3278f/THIRD_PARTY_SOURCE_AUDIT.md](https://github.com/mryk814/optimization-compass/blob/8b11e62c4153d383caac67c184f2fc2be2d3278f/THIRD_PARTY_SOURCE_AUDIT.md).

## Citation

Use the repository `CITATION.cff`. It is generated from the same publication authority
and release catalog as this card, so version, release date, source commit, download URL,
and registered DOI cannot drift independently.
