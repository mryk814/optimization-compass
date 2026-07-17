# MCP tool-contract backlog

This note records the staged public surface proposed by #153. Phase A implements only the shared,
transport-independent service boundary; it is not a hosted-service or MCP compatibility promise.

| Stage | Service/tool concept | Input | Output authority | Main guardrail |
|---|---|---|---|---|
| A | capabilities | optional expected dataset version | release identity and service contract | mismatch is explicit |
| A | Diagnose questions | `ja`/`en`, expected version | canonical question rows | preserve unknown states |
| A | recommend methods | validated structured answers, expected version | deterministic engine result | no model-authored disposition |
| B | explain recommendation | request/result identity | fired rules, predicates, sources | explanation cannot change result |
| B | get entity | stable type and ID | canonical records | bounded response, explicit missing ID |
| B | search Cases | query, filters, pagination | generated Search/Gallery indexes | no improvised recommendations |
| B | search failures | query, filters, pagination | generated failure index | distinguish exclusion from failure |
| C | remote deployment | authenticated transport policy | same service payloads | separate operations review |

Before Stage B, each bulk operation needs stable pagination, maximum response size, version mismatch,
unsupported-state, and attribution behavior. Before Stage C, document authorization, rate limiting,
logs, retention, cancellation, origin validation, and incident/rollback procedures. Review and pin the
official MCP SDK and supported protocol version only when the adapter is introduced.
