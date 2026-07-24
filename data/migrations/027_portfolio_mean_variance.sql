PRAGMA foreign_keys = OFF;
INSERT INTO benchmark_contexts (
  context_id, context_version, category, problem_instance_id, problem_variant, dimension,
  sparsity_json, hardware_json, runtime_json, oracle_budget_json, evaluation_budget,
  time_budget_seconds, tolerance_json, stopping_json, initialization_json, seed_status,
  seed_value, tuning_policy, implementation_versions_json, outcome_metrics_json,
  status_mapping_json, source_ids_json, last_verified
) VALUES (
  'BENCH_PORTFOLIO_MEAN_VARIANCE_FIXED_4', '1.0.0', 'QP',
  'INSTANCE_PORTFOLIO_MEAN_VARIANCE_FIXED_4', 'fixed_four_asset_mean_variance_capped_simplex', 4,
  '{"decision":"dense_four_asset_vector"}',
  '{"reason":"deterministic educational ledger; no wall-clock benchmark","status":"not_applicable"}',
  '{"comparison_scope":"parameter_sensitivity","generator_id":"educational.portfolio_mean_variance.v1","generator_version":"1.0.0","runtime":"deterministic_educational_grid"}',
  '{"limit":1,"unit":"oracle_evaluations"}', 1, NULL,
  '{"max_asset_weight":0.6,"simplex_sum":1.0}',
  '{"policy":"record_fixed_allocation_snapshot","value":1}',
  '{"policy":"uniform_initial_point","points":[0.25,0.25,0.25,0.25]}',
  'not_applicable', NULL,
  'mean, covariance, capped simplex, and 0.05 grid fixed before gamma sensitivity contrast',
  '{"generator_id":"educational.portfolio_mean_variance.v1","generator_version":"1.0.0","implementation_mapping_status":"not_applicable"}',
  '["expected_return","variance","mean_variance_objective","maximum_weight","simplex_residual"]',
  '{"ranking":"forbidden","future_return_guarantee":"not_applicable"}',
  '["S010","S055"]', '2026-07-24'
);
PRAGMA foreign_keys = ON;
