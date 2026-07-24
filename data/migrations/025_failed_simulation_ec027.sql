-- Exact teaching context for EC027. This records simulation status without a synthetic penalty.
PRAGMA foreign_keys = OFF;
INSERT INTO benchmark_contexts (
  context_id, context_version, category, problem_instance_id, problem_variant, dimension,
  sparsity_json, hardware_json, runtime_json, oracle_budget_json, evaluation_budget,
  time_budget_seconds, tolerance_json, stopping_json, initialization_json, seed_status,
  seed_value, tuning_policy, implementation_versions_json, outcome_metrics_json,
  status_mapping_json, source_ids_json, last_verified
) VALUES (
  'BENCH_FAILED_SIMULATION_EC027_6', '1.0.0', 'DFO',
  'INSTANCE_FAILED_SIMULATION_EC027', 'fixed six-call mixed-domain failure ledger', 3,
  '{"continuous_dimension":2,"binary_dimension":1}',
  '{"reason":"deterministic teaching ledger; no wall-clock benchmark","status":"not_applicable"}',
  '{"comparison_scope":"exact","generator_id":"educational.failed_simulation.v1","generator_version":"1.0.0","runtime":"deterministic_educational_failure_ledger"}',
  '{"limit":6,"unit":"oracle_evaluations"}', 6, NULL,
  '{"implicit_failure_region":"u1+u2<0.25"}',
  '{"policy":"six_fixed_evaluation_rows","value":6}',
  '{"policy":"same_initial_state_each_member","points":[0.65,0.35,0.0]}',
  'not_applicable', NULL,
  'candidate order, domain, failure taxonomy, status-without-penalty policy, and budget fixed before contrast',
  '{"generator_id":"educational.failed_simulation.v1","generator_version":"1.0.0","implementation_mapping_status":"not_applicable"}',
  '["feasible_rate","successful_evaluations","failed_evaluations","best_feasible_objective"]',
  '{"failure":"explicit_status_no_penalty","ranking":"forbidden"}',
  '["S002","S018","S031","S034","S035","S060","S063"]', '2026-07-24'
);
PRAGMA foreign_keys = ON;
