# Library default method audit

A library default is not a universal algorithm ranking. It records what an API selects when the caller omits an explicit method, under the documented conditions and library version.

## Verified SciPy defaults

| API | Condition | Selected method | Canonical Atlas method | Source |
|---|---|---|---|---|
| `scipy.optimize.least_squares` | `method` omitted | Trust Region Reflective (`trf`) | `M_TRUST_REGION_REFLECTIVE` | `S003` |
| `scipy.optimize.curve_fit` | no bounds | Levenberg–Marquardt (`lm`) | `M_LEVENBERG_MARQUARDT` | `S003` |
| `scipy.optimize.curve_fit` | finite bounds supplied | Trust Region Reflective (`trf`) | `M_TRUST_REGION_REFLECTIVE` | `S003` |
| `scipy.optimize.minimize` | no constraints and no bounds, `method=None` | BFGS | `M_BFGS` | `S002` |
| `scipy.optimize.minimize` | bounds and no general constraints, `method=None` | L-BFGS-B | `M_LBFGSB` | `S002` |
| `scipy.optimize.minimize` | constraints supplied, `method=None` | SLSQP | `M_SLSQP` | `S002` |
| `scipy.optimize.linprog` | `method` omitted | HiGHS | implementation-dependent LP method selection | `S004` |

## Recording policy

- Record API, condition, selected method, library release, verification date, and official source.
- Keep conditional defaults separate from unconditional defaults.
- Do not convert an API default directly into a Diagnose promotion or a global score.
- Explain why the default is broad or robust, and list the conditions that justify an override.
- Reverify defaults when the implementation release claim becomes stale or the API signature changes.
- Keep modeling layers, wrapper APIs, and underlying algorithms distinct.

## TRF pilot

`I_SCIPY_LEAST_SQUARES_TRF` owns the current SciPy implementation facts. Its versioned `important_option_defaults` claim records that:

- `least_squares` selects `trf` when `method` is omitted;
- `curve_fit` selects `trf` when bounds are supplied and `lm` otherwise;
- the trust-region subsolver is selected from Jacobian representation unless overridden.

The claim describes library behavior. Applicability remains governed by the method assumptions, diagnostics, and the user's problem.
