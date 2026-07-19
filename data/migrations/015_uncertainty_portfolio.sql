PRAGMA foreign_keys = ON;

INSERT INTO sources (
  source_id, source_type, title, author_or_organization, publication_date,
  accessed_date, url, supported_claim, source_quality, notes, currentness_status
) VALUES (
  'S102', 'original_paper',
  'Optimization of Conditional Value-at-Risk',
  'R. Tyrrell Rockafellar and Stanislav Uryasev', '2000-01-01', '2026-07-19',
  'https://uryasev.ams.stonybrook.edu/wp-content/uploads/2019/03/optimization_cvar.pdf',
  'CVaR optimization representation and its use in portfolio selection.',
  'primary',
  'Original CVaR optimization paper. The fixed Atlas scenarios do not inherit a population or out-of-sample guarantee from this source.',
  'historical_primary'
);

PRAGMA foreign_keys = OFF;

INSERT INTO benchmark_contexts (
  context_id, context_version, category, problem_instance_id, problem_variant, dimension,
  sparsity_json, hardware_json, runtime_json, oracle_budget_json, evaluation_budget,
  time_budget_seconds, tolerance_json, stopping_json, initialization_json, seed_status,
  seed_value, tuning_policy, implementation_versions_json, outcome_metrics_json,
  status_mapping_json, source_ids_json, last_verified
) VALUES (
  'BENCH_PORTFOLIO_CVAR_FIXED_8_4', '1.0.0', 'LP',
  'INSTANCE_PORTFOLIO_CVAR_FIXED_8_4',
  'fixed_four_asset_capped_simplex_with_disjoint_training_and_held_out_returns', 4,
  '{"decision":"dense_four_asset_vector","scenario_loss_matrix":"12x4"}',
  '{"reason":"deterministic educational generator; no wall-clock comparison","status":"not_applicable"}',
  '{"comparison_scope":"exact","generator_id":"educational.portfolio_uncertainty.v1","generator_version":"1.0.0","precision":"float64","runtime":"deterministic_educational_grid"}',
  '{"limit":12,"unit":"oracle_evaluations"}', 12, NULL,
  '{"alpha":0.75,"confidence_target":"not_applicable_no_probability_guarantee","grid_step":0.05,"max_asset_weight":0.6}',
  '{"policy":"fixed_training_then_held_out","value":12}',
  '{"policy":"member_initial_points","points":[[0.45,0.0,0.0,0.55],[0.3,0.4,0.0,0.3]],"training_sample_count":8,"held_out_sample_count":4,"sample_policy":"fixed_disjoint_8_training_4_held_out"}',
  'not_applicable', NULL,
  'alpha=0.75, CVaR weight=0.5, 0.05 grid, and samples fixed before held-out evaluation',
  '{"generator_id":"educational.portfolio_uncertainty.v1","generator_version":"1.0.0","implementation_mapping_status":"not_applicable"}',
  '["mean_loss","cvar_75","worst_loss","best_loss"]',
  '{"completed":"empirical_training_and_held_out_summary","ranking":"forbidden","probability_guarantee":"not_applicable"}',
  '["S055","S102"]', '2026-07-19'
);

PRAGMA foreign_keys = ON;
