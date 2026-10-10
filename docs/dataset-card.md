<!-- Generated publication metadata; do not edit release facts. -->
<!-- Run `uv run python scripts/dataset_publication.py check` before committing. -->

# Optimization Compass Optimization Atlas Dataset

最適化問題の構造、候補・除外手法、実装、事例、比較、教材可視化を根拠付きで接続する、版管理されたデータセットです。

A versioned, evidence-linked dataset that connects optimization problem structure, candidate and excluded methods, implementations, examples, comparisons, and educational visualizations.

## Release identity

| Field | Value |
|---|---|
| Dataset version | `0.18.23` |
| Release date | `2026-10-10` |
| Source commit | [`f353246ad11813536b653fc86ef4fb04ae4356d9`](https://github.com/mryk814/optimization-compass/commit/f353246ad11813536b653fc86ef4fb04ae4356d9) |
| Source tag | [`v0.18.23`](https://github.com/mryk814/optimization-compass/releases/tag/v0.18.23) |
| Database SHA-256 | `1bc4b246c11477a33735aa1eb292a916fea4627302e913251da195763fb8d95b` |
| Manifest SHA-256 | `b333d335f00981dd7ee8fd3cfee13fa62c37df33e2529b7bed581a2a0856b437` |
| Complete bundle | [download](https://github.com/mryk814/optimization-compass/releases/download/v0.18.23/optimization_method_selection_database_v0.18.23_bundle.zip) (6,306,363 bytes) |
| Bundle SHA-256 | `46e7cd81d37f342ae69de393ce352767f73ed2fe60dac33d76cacf8f55328891` |
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
  [https://github.com/mryk814/optimization-compass/blob/f353246ad11813536b653fc86ef4fb04ae4356d9/THIRD_PARTY_SOURCE_AUDIT.md](https://github.com/mryk814/optimization-compass/blob/f353246ad11813536b653fc86ef4fb04ae4356d9/THIRD_PARTY_SOURCE_AUDIT.md).

## Citation

Use the repository `CITATION.cff`. It is generated from the same publication authority
and release catalog as this card, so version, release date, source commit, download URL,
and registered DOI cannot drift independently.
