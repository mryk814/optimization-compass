# ADR 0015: Agent access is read-only and delegates to deterministic guidance

- Status: proposed
- Date: 2026-07-17
- Issue: #153
- Scope: Phase A service boundary; no MCP transport in this phase

## Context

Optimization Compass already exposes canonical knowledge through a Python engine, CLI, FastAPI,
static site data, and retrieval exports. An MCP server could make those capabilities available to
external agents, but a protocol-specific implementation could accidentally create a second
recommendation path, hide unknown values, or imply that guidance is a solver result.

The boundary must also account for untrusted text. Case prose, source titles, content, and returned
descriptions are serialized data. They are not instructions to execute code, fetch arbitrary URLs, or
modify canonical data.

## Decision

Introduce `DeterministicGuidanceService` as a transport-independent, read-only application boundary
above `KnowledgeRepository` and `RecommendationEngine`.

The service:

- obtains dataset identity from the canonical repository;
- validates the optional expected dataset version consistently for every operation;
- validates supported languages explicitly as `ja` or `en`;
- returns canonical Diagnose questions without rewriting allowed or unknown states;
- validates the existing `RecommendationRequest` and delegates entirely to
  `RecommendationEngine`;
- returns the canonical `RecommendationResponse` without rewriting dispositions, fired rules, or
  source IDs;
- wraps every service response in typed metadata containing contract version, dataset version,
  attribution, and an explicit non-guarantee;
- advertises an explicit allowlist of read-only operations.

Existing CLI and FastAPI question and recommendation commands call this service, then unwrap the
canonical payload so their established public JSON response shapes do not change. A new capabilities
operation exposes the full versioned service response.

## Phase A operations

1. `get_capabilities`
   - optional expected dataset version;
   - metadata, authority, unknown policy, and the exact operation allowlist.
2. `list_diagnose_questions`
   - `ja` or `en` and optional expected dataset version;
   - typed canonical question records.
3. `recommend_methods`
   - existing `RecommendationRequest` or an equivalent mapping;
   - optional expected dataset version;
   - the unchanged canonical recommendation result.

These are service operation names, not a promise that later MCP tool names or schemas will be
identical.

## Authority boundary

`KnowledgeRepository` remains authoritative for released dataset identity and question records.
`RecommendationEngine` remains the only recommendation authority. The service owns metadata,
validation at its public edge, and transport-neutral response models only. CLI, FastAPI, and future
MCP adapters must not duplicate rule evaluation, exclusion precedence, fallback behavior, or source
aggregation.

## Security boundary

The operation surface is an allowlist and is read-only. It does not expose operations that:

- execute a solver, Python, shell, SQL, or plugin code;
- follow a client-supplied URL;
- treat returned text as an instruction;
- change recommendation rules, canonical data, or release identity;
- silently coerce `unknown` into yes/no or a guessed feature value;
- present guidance as a guarantee of optimality, feasibility, safety, or fitness for use.

Phase A adds no hosted service, network listener, authentication system, or MCP SDK dependency.

## Version, errors, and attribution

Every service response carries the active dataset version. Every operation accepts the same optional
expected dataset version, and a mismatch raises `DatasetVersionMismatch` rather than upgrading
silently. Unsupported language is explicit rather than falling back to English.

The existing API keeps its response body shapes. It maps dataset drift to HTTP 409 and invalid
language or recommendation input to HTTP 422. Future transports should define stable error codes,
preserve field-level validation detail, and avoid leaking stack traces or local paths.

Every service response states the CC BY 4.0 structured-data attribution and tells clients to preserve
cited source IDs. It also states that guidance is not a solver result or a guarantee.

## Planned MCP phase

A follow-up may add a thin adapter after the current official protocol and maintained SDK are
reviewed and pinned. Local standard I/O is the preferred first transport because it requires no
hosted credential or public service. Remote HTTP requires a separate authorization and operations
review.

Entity retrieval, search, pagination, payload limits, cancellation, hosted authorization, and client
protocol examples remain follow-up work. #153 stays open after Phase A.

## Validation

Phase A tests cover:

- exact equality with the direct canonical engine response for the same request;
- preservation of unknown, dispositions, fired rules, and source IDs;
- canonical question reuse and explicit language validation;
- metadata and dataset-version mismatch behavior on every operation;
- the read-only operation allowlist and untrusted-text serialization;
- CLI and FastAPI delegation through the shared service without changing existing payload shapes.

Future MCP work additionally needs protocol-contract, transport, cancellation, payload-limit, and
client compatibility tests.

## Primary references

- Model Context Protocol specification: https://modelcontextprotocol.io/specification/
- Tools specification: https://modelcontextprotocol.io/specification/2025-11-25/server/tools
- Transports specification: https://modelcontextprotocol.io/specification/2025-11-25/basic/transports
- Official Python SDK: https://github.com/modelcontextprotocol/python-sdk
