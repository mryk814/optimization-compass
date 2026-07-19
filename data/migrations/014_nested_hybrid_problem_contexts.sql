PRAGMA foreign_keys = OFF;

INSERT INTO benchmark_contexts (
  context_id, context_version, category, problem_instance_id, problem_variant, dimension,
  sparsity_json, hardware_json, runtime_json, oracle_budget_json, evaluation_budget,
  time_budget_seconds, tolerance_json, stopping_json, initialization_json, seed_status,
  seed_value, tuning_policy, implementation_versions_json, outcome_metrics_json,
  status_mapping_json, source_ids_json, last_verified
) VALUES (
  'BENCH_BILEVEL_REGRESSION_EDUCATIONAL_6', '1.0.0', 'NLP',
  'INSTANCE_BILEVEL_REGRESSION_2COEF', 'exact_kkt_vs_finite_relaxation_teaching_ledger', 1,
  '{"outer_dimension":1,"inner_dimension":2,"inner_structure":"dense"}',
  '{"os":"platform-neutral","precision":"float64","hardware":"educational"}',
  '{"comparison_scope":"exact","generator_id":"educational.bilevel_regression_ledger.v1","generator_version":"1.0.0","implementation_mapping_status":"not_applicable"}',
  '{"limit":6,"unit":"oracle_evaluations"}', 6, NULL,
  '{"inner_residual":1e-8,"stationarity_residual":1e-8,"exact_complementarity_residual":1e-8}',
  '{"policy":"fixed_outer_budget","value":6}',
  '{"policy":"fixed_outer_initialization","points":[0.8]}',
  'not_applicable', NULL,
  'fixed outer sequence, warm-started inner policy, tolerance, and derivative route; no post-run tuning',
  '{"generator_id":"educational.bilevel_regression_ledger.v1","generator_version":"1.0.0","implementation_mapping_status":"not_applicable"}',
  '["outer_objective","inner_residual","stationarity_residual","complementarity_residual","relaxation_parameter"]',
  '{"exact":"fixed teaching residual checks passed","finite_relaxation":"stopped without exact-complementarity claim"}',
  '["S055","S056","S064"]', '2026-07-19'
);

PRAGMA foreign_keys = ON;
