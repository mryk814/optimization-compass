-- Canonical source and benchmark context for the #135 simulation-constrained
-- state/adjoint tolerance and failed-evaluation teaching journey.

INSERT INTO sources (
  source_id, source_type, title, author_or_organization, publication_date,
  accessed_date, url, supported_claim, source_quality, notes, currentness_status
) VALUES
(
  'S110', 'official_documentation', 'KSPConvergedReason',
  'PETSc', NULL, '2026-07-19',
  'https://petsc.org/release/manualpages/KSP/KSPConvergedReason/',
  'PETSc distinguishes positive convergence reasons from explicit divergence reasons including iteration limit, breakdown, NaN/Inf, and preconditioner failure.',
  'primary',
  'Official PETSc manual page; no prose or examples are copied into this repository.',
  'verified_current'
),
(
  'S111', 'official_documentation', 'FEniCS Adjoint Documentation',
  'dolfin-adjoint project', NULL, '2026-07-19',
  'https://www.dolfin-adjoint.org/_/downloads/en/stable/pdf/',
  'Time-dependent adjoints may use checkpointing to trade storage for forward recomputation, and adjoint correctness requires explicit verification.',
  'primary',
  'Official project documentation; no prose, figures, or examples are copied into this repository.',
  'verified_current'
);

PRAGMA foreign_keys = OFF;

INSERT INTO benchmark_contexts (
  context_id, context_version, category, problem_instance_id, problem_variant, dimension,
  sparsity_json, hardware_json, runtime_json, oracle_budget_json, evaluation_budget,
  time_budget_seconds, tolerance_json, stopping_json, initialization_json, seed_status,
  seed_value, tuning_policy, implementation_versions_json, outcome_metrics_json,
  status_mapping_json, source_ids_json, last_verified
) VALUES (
  'BENCH_PDE_STATE_TOLERANCE_6', '1.0.0', 'NLP', 'INSTANCE_TOPOLOGY_CANTILEVER_2D',
  'fixed 8x4 cantilever; reduced-space state/adjoint tolerance sensitivity only', 32,
  '{"field_grid":"8x4","state_solve":"deterministic_teaching_ledger"}',
  '{"status":"not_applicable","reason":"no wall-clock comparison"}',
  '{"comparison_scope":"exact","generator_id":"educational.simulation_constrained.v1","generator_version":"1.0.0","implementation_mapping_status":"not_applicable","precision":"float64"}',
  '{"limit":6,"unit":"oracle_evaluations"}', 6, NULL,
  '{"changed_factor":"state_and_adjoint_relative_tolerance","tight":1e-8,"loose":1e-3}',
  '{"policy":"fixed_state_solve_call_budget","value":6}',
  '{"policy":"fixed_density_field_and_design_update_sequence","points":[0.5,0.0]}',
  'not_applicable', NULL,
  'tolerances fixed before the run; no post-run or per-member tuning',
  '{"generator_id":"educational.simulation_constrained.v1","generator_version":"1.0.0","implementation_mapping_status":"not_applicable"}',
  '["objective_value","state_residual","adjoint_residual","state_linear_iterations","adjoint_linear_iterations","evaluation_status"]',
  '{"converged":"eligible_teaching_frame","diverged_pc_failed":"failed_evaluation_no_objective_penalty","ranking":"forbidden"}',
  '["S019","S097","S101","S110"]', '2026-07-19'
);

PRAGMA foreign_keys = ON;
