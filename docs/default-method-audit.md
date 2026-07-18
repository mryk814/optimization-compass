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

`I_SCIPY_LEAST_SQUARES_TRF` owns the current SciPy implementation facts. Conditional API
selection is stored in two independently queryable predicates:

- `default_method_least_squares`: `least_squares` selects `trf` when `method` is omitted;
- `default_method_curve_fit_bounds`: `curve_fit` selects `trf` when bounds are supplied and
  `method` is omitted, with unbounded `lm` recorded as the fallback condition.

Each value records `api`, `condition`, `selected_method`, canonical `selected_method_id`,
`fallback`, `user_override`, and `recommendation_effect`. Source, product version, verification
date, and validity window remain typed columns on `implementation_claims`.

The seven generic predicates remain present for every implementation. These two predicates are
additive only for the SciPy TRF implementation, so the active-claim contract is
`implementation_count × 7 + 2`. The generic `important_option_defaults` claim now contains
tunable options rather than acting as the authority for conditional method selection.

The partial unique index on `(subject_id, predicate)` permits at most one active row per typed
fact. A later verification must close the old row with `valid_to`, set `replaced_by`, and mark it
`superseded` before inserting the replacement.

SQL:

```sql
SELECT predicate, value_json, source_id, product_version, valid_from, valid_to
FROM implementation_claims
WHERE subject_id = 'I_SCIPY_LEAST_SQUARES_TRF'
  AND predicate IN (
    'default_method_least_squares',
    'default_method_curve_fit_bounds'
  )
  AND valid_to IS NULL
ORDER BY predicate;
```

HTTP API:

```text
GET /v1/implementations/I_SCIPY_LEAST_SQUARES_TRF/claims
    ?predicate=default_method_least_squares
```

These claims describe versioned library behavior. They do not promote TRF in Diagnose, alter a
global score, or establish universal performance superiority.
