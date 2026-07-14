# Licensing and attribution

Optimization Compass separates software, structured data, and educational
content so that a license grant never appears broader than the project has the
right to make.

## License map

| Scope | License | Canonical notice |
|---|---|---|
| Python, TypeScript, CSS, HTML, workflows, build and validation scripts | MIT | [`LICENSE`](../LICENSE) |
| Canonical knowledge records and distributed structured-data representations | CC BY 4.0 | [`DATA_LICENSE`](../DATA_LICENSE) |
| Educational Markdown, case prose, generated figures, AlgorithmTrace JSON, and screenshots | CC BY 4.0 | [`CONTENT_LICENSE`](../CONTENT_LICENSE) |
| Cross-scope notices and third-party boundary | Project notice | [`NOTICE`](../NOTICE) |

The CC BY 4.0 reference and links to the authoritative Creative Commons legal
code are in [`CC-BY-4.0`](../CC-BY-4.0).

## Scope details

### Code

The MIT license covers software expression: source code, tests, configuration,
workflows, schemas as executable build logic, and rendering or export code. It
does not change the license of data or educational prose processed by the code.

### Data

CC BY 4.0 covers project-authored canonical database records and the released
SQLite, JSON, JSONL, CSV, ZIP, XLSX, ViewSpec, recommendation, and equivalent
structured-data representations derived from them. SQL migrations and JSON
seeds are data-licensed insofar as they express those records; executable
migration machinery remains MIT-licensed.

### Educational content

CC BY 4.0 covers original educational Markdown, case descriptions, explanatory
copy, generated figures, generated AlgorithmTrace JSON, screenshots, and other
learning media. Generator and renderer code remains MIT-licensed.

An artifact may mix structured fields and educational prose, for example a
Gallery JSON record. Both applicable scopes use CC BY 4.0, so the attribution
obligation is the same.

## How to attribute

For data:

> Optimization Compass dataset, Copyright 2026 TAKUYA OTANI and Optimization
> Compass contributors, licensed under CC BY 4.0,
> https://github.com/mryk814/optimization-compass

For educational content:

> Optimization Compass educational content, Copyright 2026 TAKUYA OTANI and
> Optimization Compass contributors, licensed under CC BY 4.0,
> https://github.com/mryk814/optimization-compass

Include a CC BY 4.0 link and indicate modifications. A combined attribution may
be used when data and content are shared together.

## Third-party boundary

The project licenses only rights held by its contributors. A source title,
author name, URL, identifier, short factual summary, trademark, quotation, or
link does not place the referenced third-party work under MIT or CC BY 4.0.

- Linked papers, books, documentation, repositories, standards, software, and
  vendor material retain their original terms.
- Patent, trademark, publicity, and privacy rights are not granted by these
  project licenses.
- Official names may identify a source but do not imply sponsorship.
- Third-party quotations, figures, logos, or screenshots require a local
  exception notice naming the rights holder, source, applicable terms, and
  exact material covered.

The current source-type and field audit is recorded in
[`THIRD_PARTY_SOURCE_AUDIT.md`](../THIRD_PARTY_SOURCE_AUDIT.md).

## Distribution paths

- Dataset release manifests declare code/data/content SPDX identifiers and
  paths to bundled notices.
- Dataset release directories contain all project notices; deterministic CSV
  ZIP files additionally contain the data notice, CC BY 4.0 reference, and
  project `NOTICE`.
- GitHub Pages publishes the same notices under `licenses/`; the site manifest
  declares those paths. `LicenseLinks` is the footer-ready component.

The tracked v0.2.0 release predates this policy and remains immutable. Dataset v0.3.0 is produced
by the updated staged release path, bundles the declared notices, and must pass the public release
checklist before publication.

## Contribution policy

The project uses Developer Certificate of Origin 1.1 sign-off and does not
require a separate CLA. See [`CONTRIBUTING.md`](../CONTRIBUTING.md). A sign-off
confirms that a contributor has the right to submit the contribution under the
license applicable to its scope; it does not grant rights in unrelated
third-party material.
