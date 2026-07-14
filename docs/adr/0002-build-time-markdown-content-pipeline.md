# ADR 0002: Build-time CommonMark content pipeline

- Status: Accepted
- Date: 2026-07-15
- Decision owners: Optimization Compass maintainers
- Related: #20

## Context

The site previously shipped raw lesson bodies and split lines in React. That renderer
understood only level-2 headings, blockquotes, fenced code, and plain paragraphs. It
could not validate frontmatter, heading order, links, figures, tables, math, or code
languages, and each new construct would have enlarged a bespoke runtime parser.

Educational content is maintained by repository contributors and built before it is
published. It does not need arbitrary JavaScript components inside prose.

## Decision

Lessons use **CommonMark Markdown**, not MDX. A Python build pipeline uses
`markdown-it-py` and its maintained plugins to parse Markdown, Pygments to highlight
fenced code, and `latex2mathml` to emit accessible MathML. PyYAML reads frontmatter and
Pydantic validates an exact schema. The exporter writes only compiled `html` and a
validated `toc` to content contract `2.0.0`; raw Markdown is not shipped as a browser
rendering contract.

The React client renders that build artifact and never parses Markdown. The former
line-splitting renderer is deleted. Generated HTML is trusted only because the build
pipeline rejects raw HTML, unsafe or unsupported URLs, invalid heading structure,
unknown code languages, unclosed fences, missing figure text/captions, broken local
assets, and broken heading anchors before publication.

### Safety and accessibility policy

- Raw HTML in Markdown is forbidden.
- External links must use HTTPS and are emitted with `target="_blank"` plus
  `rel="noopener noreferrer"`.
- Site links use absolute paths or HashRouter paths. Local heading links are validated
  and intercepted by the client so HashRouter state is not changed.
- A page title owns `h1`. Lesson bodies start at `h2` and may not skip levels.
- Generated headings receive stable IDs and programmatic focus targets. The TOC uses
  native buttons so it is keyboard operable without changing the route hash.
- Every figure requires alt text and a title caption. Relative assets must exist under
  `site/public` at build time.
- Display math is keyboard-focusable and emitted as MathML. Tables use Markdown header
  rows. Callouts use labelled `aside` elements.

## Consequences

Content errors fail the export and CI instead of appearing as malformed production UI.
The site bundle carries no Markdown parser, syntax highlighter, or math renderer. The
tradeoff is that adding syntax, callout types, or code languages requires an explicit
pipeline change and test rather than an MDX component import.

Copy-code controls are not included: the initial lessons contain short examples and a
control would add runtime behavior without solving a current reading problem. Heading
anchors and a compact TOC are included because longer lessons need navigation.

## Rejected alternatives

- **MDX:** permits arbitrary component/JavaScript execution in content and couples
  lessons to the React build.
- **React Markdown at runtime:** ships parser cost and defers authoring failures until a
  reader opens the page.
- **Extend the line splitter:** continues an incomplete parser with no robust syntax or
  safety model.
