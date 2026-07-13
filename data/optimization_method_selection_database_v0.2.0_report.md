# Optimization Method Selection Database v0.2.0

Generated: 2026-07-13  
Language: Japanese + English  
Source policy: official documentation/repositories, original papers, trusted textbooks; Qiita/Zenn excluded.

## 1. Release intent

v0.2.0 is a quality-and-metadata release. The optimization recommendations were not bulk-expanded without evidence. Instead, the release makes the dataset executable as a relational database, clarifies ambiguous relations, refreshes risk-sensitive implementation metadata, and records the validation result as data.

## 2. Main improvements

### 2.1 Relational integrity

- The complete schema and all **8,099 rows across 33 tables** load into SQLite with foreign keys enabled.
- `PRAGMA foreign_key_check` returns zero violations.
- Optional references now use `NULL` rather than empty strings:
  - `methods.parent_method_id` for root method families
  - `problem_feature_map.feature_value_id` for boolean/truth-status features
  - `case_feature_map.feature_value_id` where the value is not applicable
  - `case_method_map.fit_id` for scenario-specific relations without a canonical archetype fit

### 2.2 Controlled meaning

- Added `decision_rules.action_target_type` so polymorphic `action_target_ids` are interpretable as `problem`, `method`, `alternative`, `feature`, or `none`.
- Added `FV0093` (`F_OBJECTIVE_FORM=discrete`) and normalized three existing scenario values from free text.
- Repaired six malformed `evidence_links` rows for model revisions.

### 2.3 Implementation metadata

Official primary sources were used to refresh selected high-use or risk-sensitive implementations:

| Implementation | v0.2.0 metadata |
|---|---|
| SciPy implementations | SciPy 1.18.0 |
| HiGHS native | 1.15.1 |
| OSQP | core 1.0.0; Python wrapper 1.1.3 |
| CVXPY | 1.9.1 |
| Ipopt | 3.14.19 |
| OR-Tools | 9.15 |
| SCIP | 10.0.0 |
| Nevergrad | 1.0.12 |
| Pymanopt | 2.2.1 |
| Manopt MATLAB | 8.0; GPL-3.0-or-later |
| NOMAD | 4.5.1; LGPL-3.0-or-later |
| JAXopt | 0.8.5; maintenance status changed to `legacy` |
| Manopt.jl | new implementation row; 0.6.1; MIT |

Release versions are point-in-time metadata, not compatibility guarantees. For SciPy/HiGHS rows, the bundled backend version follows the SciPy distribution and is not assumed to equal the latest standalone HiGHS version.

## 3. Added quality-control table

`release_checks` stores executable release gates. v0.2.0 contains 12 checks covering DDL creation, full row insertion, foreign keys, primary keys, source references, evidence targets, decision target typing, optional FK null semantics, enum normalization, release coverage, license verification, and maintenance status.

Result summary:

- Pass: 11
- Warn: 1
- Fail: 0

The warning is intentional: 25 of 64 implementation rows still retain `last_release=unknown`. This is preferable to inserting unverified or incomparable version claims.

## 4. Compatibility notes

Schema changes in v0.2.0:

1. Added `decision_rules.action_target_type`.
2. Added table `release_checks`.
3. Four optional foreign-key columns became nullable.
4. JSON/JSONL use `null` for absent optional foreign keys.
5. Added one implementation, two method-implementation mappings, one case-implementation mapping, fourteen official source records, and associated evidence links.

Consumers that hard-code the v0.1.0 decision-rule column order should migrate using `schema_dictionary`.

## 5. Known limitations

- The dataset remains representative rather than exhaustive.
- Software release/version fields are volatile and should be rechecked before procurement, deployment, or reproducibility claims.
- Semicolon-separated ID lists are convenience fields. Canonical many-to-many relations should use bridge tables when available.
- Method suitability is conditional on modeling assumptions, scaling, derivative reliability, budget, and solution requirements; a database match is not a substitute for validation on the actual problem.
- Commercial solver licensing and edition-specific capability must be checked directly with the vendor.

## 6. Verification performed

- SQLite DDL execution: pass
- Full data insertion: pass (8,099 rows)
- Foreign-key check: pass (0 violations)
- Duplicate primary keys: pass (0)
- Unresolved source IDs: pass (0)
- Unresolved evidence targets: pass (0)
- Unresolved decision action targets: pass (0)
- Blank-string optional foreign keys: pass (0)

See `32_release_checks` in the workbook and the `release_checks` table in JSON/CSV/SQLite for machine-readable details.
