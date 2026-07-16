# Library default methods

Optimization Compass treats a library default as an implementation claim, not as a context-free recommendation or performance ranking.

## Why defaults receive priority

A default method may run even when the user did not choose an algorithm explicitly. It therefore has high practical exposure and a high risk of being misunderstood. For every default, record:

- library and API;
- condition under which the default is selected;
- selected method or backend;
- version and verification date;
- user override;
- fallback or alternative condition;
- source;
- whether the claim changes recommendation behavior.

Default claims are versioned implementation facts. They do not make the selected method globally preferable.

## SciPy pilot

Verified against the official SciPy documentation on 2026-07-16.

| API | Condition | Implicit selection | User override | Canonical interpretation | Source |
|---|---|---|---|---|---|
| `scipy.optimize.least_squares` | `method` omitted | `trf` | `method` | Trust Region Reflective for nonlinear least squares | S003 |
| `scipy.optimize.curve_fit` | no bounds and `method` omitted | `lm` | `method` | Levenberg–Marquardt through the least-squares wrapper | S003 |
| `scipy.optimize.curve_fit` | bounds provided and `method` omitted | `trf` | `method` | Trust Region Reflective | S003 |
| `scipy.optimize.minimize` | no bounds or constraints and `method` omitted | `BFGS` | `method` | BFGS implementation choice | S002 |
| `scipy.optimize.minimize` | bounds provided, no general constraints, `method` omitted | `L-BFGS-B` | `method` | Bound-constrained L-BFGS implementation choice | S002 |
| `scipy.optimize.minimize` | constraints provided and `method` omitted | `SLSQP` | `method` | SLSQP implementation choice | S002 |
| `scipy.optimize.linprog` | `method` omitted | `highs` | `method` | HiGHS chooses an appropriate LP algorithm internally | S004 |

The v0.11.0 pilot stores the two TRF-facing conditions as separate active implementation claims:

1. `least_squares`: method omitted;
2. `curve_fit`: bounds supplied and method omitted.

The unconstrained `curve_fit` LM condition remains documented here and on the least-squares learning path. The remaining defaults should be promoted to structured claims only when their canonical method/backend identity and validity window can be represented without ambiguity.

## Review rules

- Do not infer a default from examples; use the official API documentation or source.
- Do not merge conditions that select different methods.
- Do not equate a modeling layer, wrapper, backend, and algorithm.
- Preserve explicit unknowns when a backend makes a secondary internal choice.
- Reverify defaults when the library release or API signature changes.
- Keep recommendation rules unchanged unless separate problem-level evidence supports a change.
