<!-- Generated publication metadata; do not edit release facts. -->
<!-- Run `uv run python scripts/dataset_publication.py check` before committing. -->

# Optimization Compass Optimization Atlas Dataset

最適化問題の構造、候補・除外手法、実装、事例、比較、教材可視化を根拠付きで接続する、版管理されたデータセットです。

A versioned, evidence-linked dataset that connects optimization problem structure, candidate and excluded methods, implementations, examples, comparisons, and educational visualizations.

## Release identity

| Field | Value |
|---|---|
| Dataset version | `0.18.18` |
| Release date | `2026-07-26` |
| Source commit | [`df9a949e86459712d9e03447ce3afe43a94f6340`](https://github.com/mryk814/optimization-compass/commit/df9a949e86459712d9e03447ce3afe43a94f6340) |
| Source tag | [`v0.18.18`](https://github.com/mryk814/optimization-compass/releases/tag/v0.18.18) |
| Database SHA-256 | `2af0922fc3771935350fef25abc29b571a3caf1163fd5215101d2352a61b8830` |
| Manifest SHA-256 | `a6a6e3e20416cdbf22a51d78303397da1fa309e763a6b6382c5d0d3dcaf4d996` |
| Complete bundle | [download](https://github.com/mryk814/optimization-compass/releases/download/v0.18.18/optimization_method_selection_database_v0.18.18_bundle.zip) (4,939,063 bytes) |
| Bundle SHA-256 | `da319c44b99343f6f3745bf384b3626cb274cde8573e171b55e74efb80f974e6` |
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
  [https://github.com/mryk814/optimization-compass/blob/df9a949e86459712d9e03447ce3afe43a94f6340/THIRD_PARTY_SOURCE_AUDIT.md](https://github.com/mryk814/optimization-compass/blob/df9a949e86459712d9e03447ce3afe43a94f6340/THIRD_PARTY_SOURCE_AUDIT.md).

## Citation

Use the repository `CITATION.cff`. It is generated from the same publication authority
and release catalog as this card, so version, release date, source commit, download URL,
and registered DOI cannot drift independently.
