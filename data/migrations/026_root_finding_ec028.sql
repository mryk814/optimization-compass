-- Exact teaching context for EC028. The auxiliary squared residual does not redefine a root.
PRAGMA foreign_keys = OFF;
INSERT INTO benchmark_contexts (
  context_id, context_version, category, problem_instance_id, problem_variant, dimension,
  sparsity_json, hardware_json, runtime_json, oracle_budget_json, evaluation_budget,
  time_budget_seconds, tolerance_json, stopping_json, initialization_json, seed_status,
  seed_value, tuning_policy, implementation_versions_json, outcome_metrics_json,
  status_mapping_json, source_ids_json, last_verified
) VALUES (
  'BENCH_ROOT_FINDING_EC028_3', '1.0.0', 'NLP',
  'INSTANCE_ROOT_FINDING_EC028', 'fixed two-equation root residual ledger', 2,
  '{"residual_dimension":2}',
  '{"reason":"deterministic teaching ledger; no wall-clock benchmark","status":"not_applicable"}',
  '{"comparison_scope":"exact","generator_id":"educational.root_finding.v1","generator_version":"1.0.0","runtime":"deterministic_educational_root_ledger"}',
  '{"limit":2,"unit":"oracle_evaluations"}', 2, NULL,
  '{"component_max_abs":0.02,"scalar_squared_residual":0.003}',
  '{"policy":"component_max_abs_residual_or_scalar_squared_residual_only"}',
  '{"policy":"same_initial_state_each_member","points":[0.7,0.7]}',
  'not_applicable', NULL,
  'equations, initial point, residual scale, Jacobian availability, and tolerances fixed before contrast',
  '{"generator_id":"educational.root_finding.v1","generator_version":"1.0.0","implementation_mapping_status":"not_applicable"}',
  '["residual_1","residual_2","residual_max_abs","squared_residual"]',
  '{"ranking":"forbidden","root_definition":"componentwise_residual_tolerance"}',
  '["S002","S003","S041","S056","S080"]', '2026-07-24'
);
PRAGMA foreign_keys = ON;
