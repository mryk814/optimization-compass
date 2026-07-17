# ADR 0015: MCP and other agent adapters wrap one deterministic read-only service

- Status: proposed
- Date: 2026-07-17
- Issue: #153

## Context

Optimization Compass already exposes the recommendation engine through the CLI and FastAPI. A future
Model Context Protocol (MCP) server could make the same deterministic guidance available to external
agents, but adding protocol handlers directly around the database or duplicating recommendation logic
would create several risks:

- CLI, REST, and MCP could disagree about candidate, conditional, and excluded dispositions;
- an adapter could silently convert `unknown` into a guessed yes/no answer;
- prose-only responses could omit fired rule IDs, source IDs, and dataset identity;
- remote protocol concerns could leak into the canonical engine;
- a changing SDK could become a required runtime dependency before the product boundary is stable.

The official MCP specification is maintained at
<https://github.com/modelcontextprotocol/modelcontextprotocol>. The official Python SDK is maintained at
<https://github.com/modelcontextprotocol/python-sdk>. At the time of this decision, the SDK documents a
stable v1 line while v2 is still being prepared. Optimization Compass therefore should not make an alpha
adapter library part of the core recommendation path merely to begin MCP work.

## Decision

Introduce `optimization_compass.agent_service.AgentService` as the protocol-neutral, read-only service
boundary for human-facing and agent-facing interfaces.

The service owns one `KnowledgeRepository` and one `RecommendationEngine`. It delegates all recommendation
behavior to that existing engine and exposes only validated operations:

- `get_capabilities`
- `list_diagnose_questions`
- `recommend_methods`
- `explain_recommendation`
- `get_entity`
- `verify_data` for existing maintenance interfaces

The service does not implement ranking, rule matching, failure guidance, entity storage, or evidence
resolution itself. It coordinates existing authorities and returns stable structured models.

FastAPI is moved onto this service in the first slice. CLI migration may use the same service in a small
follow-up if changing its import path independently keeps review clearer. An MCP adapter must call this
service; it may not instantiate a separate recommendation implementation.

## Contract rules

### Dataset identity

Every capabilities and explanation response includes the canonical dataset version. A later MCP adapter
must also return the service contract version and reject an explicit incompatible requested dataset
version rather than silently using another release.

### Unknown and disposition semantics

- allowed Diagnose answers are returned exactly as authored, including `unknown`;
- `unknown` is never converted to yes/no by the service or adapter;
- candidate, conditional, excluded, and alternative bands remain separate;
- exclusion precedence remains owned by the recommendation engine;
- no response may imply a universal ranking or guaranteed optimality.

### Explanation

`explain_recommendation` returns stable IDs needed for verification:

- fired rule IDs;
- source IDs referenced by those rules;
- excluded method IDs;
- global warnings;
- answered-question count;
- dataset version and disclaimer.

This compact explanation is a projection of the full canonical `RecommendationResponse`; it is not a
second explanation engine.

### Entity access

The first service slice exposes canonical Method, Implementation, and Source lookup only. Search, Case,
Failure, and richer evidence projections should be added after their generated public contracts are
stable. Unknown entity IDs fail explicitly.

### Read-only and trust boundary

- no operation executes arbitrary solver code, shell commands, plugins, or user-supplied Python;
- source titles, educational prose, and external text are returned as data, never interpreted as tool
  instructions;
- protocol prompts cannot change canonical dispositions or bypass validation;
- an adapter may limit payload size and paginate, but must not silently truncate evidence IDs;
- hosted deployment, authentication, rate limiting, and network policy remain separate decisions.

## Proposed MCP mapping

A later adapter should map MCP tools to the service without changing semantics:

| MCP-facing tool | Service operation | Notes |
|---|---|---|
| `get_capabilities` | `get_capabilities` | Version, operations, attribution, limitations |
| `list_diagnose_questions` | `list_diagnose_questions` | Japanese or English authored questions |
| `recommend_methods` | `recommend_methods` | Full deterministic recommendation response |
| `explain_recommendation` | `explain_recommendation` | Stable rule/source/exclusion IDs |
| `get_entity` | `get_entity` | Explicit entity type and stable ID |

Future `search_cases` and `search_failures` tools should consume the same generated search/failure
contracts used by the site rather than add adapter-only queries.

## SDK and transport policy

The core package does not depend on an MCP SDK in this slice. Before adding the adapter:

1. verify the current official specification and Python SDK release status;
2. choose one supported SDK major and pin it as an optional dependency;
3. begin with local stdio for the smallest trust surface;
4. add Streamable HTTP only with explicit origin/authentication/rate-limit policy;
5. test structured output, pagination, version mismatch, cancellation, and protocol errors;
6. keep protocol conformance tests separate from deterministic service parity tests.

This avoids coupling the canonical engine to a transitional adapter while making the eventual adapter
small and mechanical.

## Consequences

- REST and future MCP can share one deterministic service path.
- Agent responses have stable IDs, version identity, attribution, and explicit limitations.
- The service is independently testable without an MCP transport.
- An actual MCP endpoint is not delivered by this ADR; #153 remains open until adapter, integration,
  protocol/security tests, and deployment documentation are complete.
- Adding new agent operations requires first establishing or reusing a canonical public data contract.
