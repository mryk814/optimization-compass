# ADR 0003: Optimization Atlas is the canonical browser experience

- Status: Accepted
- Date: 2026-07-15
- Decision owners: Optimization Compass maintainers
- Related issue: #27

## Context

The repository previously shipped two independently implemented browser experiences: an inline,
dependency-free diagnosis form at the FastAPI root and the static React Optimization Atlas. Both
rendered diagnosis copy and result concepts, so every wording, accessibility, and navigation change
risked creating a second authority.

The FastAPI application remains valuable as a local REST service. That value does not require a
second interactive browser product.

## Decision

Optimization Atlas is the only canonical browser experience from application version 0.2.0.

The interactive FastAPI diagnosis page was supported through 0.1.x and is removed in 0.2.0. The
FastAPI root remains as a small, script-free migration landing page that links to Atlas, OpenAPI,
the OpenAPI JSON document, and the health check. It is not a fallback diagnosis UI and has no
feature-parity commitment with Atlas.

The REST API, OpenAPI schema, health check, and CLI remain supported. The Python package does not
embed the Atlas production artifact; local/offline Atlas use is a separate static-app process.

## Supported feature matrix

| Capability | Optimization Atlas | FastAPI service | CLI |
|---|---:|---:|---:|
| Canonical browser navigation and learning experience | Supported | Not supported | Not applicable |
| Interactive diagnosis and shareable browser state | Supported | Not supported | Not applicable |
| Map, Gallery, Learn, Theater, and comparison views | Supported | Not supported | Not applicable |
| REST recommendation and entity lookup | Not its runtime dependency | Supported | Not applicable |
| OpenAPI documentation | Not applicable | Supported | Not applicable |
| JSON-file recommendation | Not applicable | Not applicable | Supported |
| Data verification and export commands | Not applicable | REST verification only | Supported |
| Migration guidance at `/` | Not applicable | Supported through the 0.2.x line | Not applicable |

“Not supported” is intentional. It does not mean that feature parity is deferred.

## Copy and contract authority

- Canonical question IDs, answer values, evidence, and decision records live in the versioned
  SQLite dataset and its validated build inputs.
- Atlas diagnosis labels are exported in versioned `SiteData`; the React app consumes that data.
- REST request and response shapes are owned by the Pydantic models and the OpenAPI schema.
- Browser navigation, result headings, accessibility labels, and educational copy are owned only
  by Atlas components and content.
- `web.py` owns only service-boundary and migration copy. It must not contain question labels,
  answer labels, result bands, or a recommendation client.

Adding a second handwritten mapping or copy table for the same concept is a contract violation.
Parity between the Python evaluator and the static evaluator is tested with shared fixtures rather
than by maintaining two browser renderers.

## Migration

- Users opening the former local diagnosis URL, including `/` with an old query string, receive the
  migration landing page and can continue to `/docs` or Atlas.
- Browser users move to the published Atlas or run `cd site && npm ci && npm run dev` locally.
- API clients keep using `/v1/*`; no endpoint or response contract is removed by this decision.
- CLI users keep using `questions`, `recommend`, `verify-data`, `export-site-data`, and `serve`.
- Canonical entity aliases and deprecated Atlas hash routes are owned by the entity-link work in
  #19, not by the FastAPI service.

## Test responsibilities

- FastAPI tests verify the migration landing links, absence of an interactive diagnosis client,
  and continued OpenAPI/REST availability.
- Atlas unit and browser tests own its navigation, responsive behavior, accessibility, and user
  journeys.
- Recommendation parity tests own equality between Python and TypeScript evaluation results.

## Consequences

- Diagnosis UI changes happen once, in Atlas.
- The Python service remains dependency-light and useful for local automation.
- Offline browser use requires building or serving the static Atlas separately.
- The FastAPI root is a deliberate migration surface, not a promise to restore the legacy form.

## Rejected alternatives

- **Keep a minimal interactive fallback:** this retains the duplicated copy and accessibility
  burden without preserving Atlas state, sources, or navigation.
- **Embed the Atlas build in the Python wheel:** this couples Node artifacts and Python releases,
  increases package size, and creates a second deployment path for the same static application.
