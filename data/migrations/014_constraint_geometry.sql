PRAGMA foreign_keys = ON;

INSERT INTO sources (
  source_id, source_type, title, author_or_organization, publication_date,
  accessed_date, url, supported_claim, source_quality, notes, currentness_status
) VALUES
(
  'S107', 'original_paper',
  'Rotation Averaging',
  'Richard Hartley, Jochen Trumpf, Yuchao Dai, and Hongdong Li',
  '2013-07-01', '2026-07-19',
  'https://doi.org/10.1007/s11263-012-0601-0',
  'SO(3) rotation averaging, chordal and geodesic distance choices, and near-pi geometry limitations.',
  'primary',
  'Primary rotation-averaging paper. The Atlas fixed three-correspondence trace is a teaching instance and does not inherit general convergence or robustness guarantees.',
  'historical_primary'
),
(
  'S108', 'original_paper',
  'A Riemannian Framework for Tensor Computing',
  'Xavier Pennec, Pierre Fillard, and Nicholas Ayache',
  '2006-01-01', '2026-07-19',
  'https://doi.org/10.1007/s11263-005-3222-z',
  'Riemannian treatment of symmetric positive-definite tensors and intrinsic statistics.',
  'primary',
  'Primary SPD-geometry source. Cholesky, log-Euclidean, and affine-invariant choices remain distinct modeling contracts.',
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
  'BENCH_SO3_ATTITUDE_FIXED_12', '1.0.0', 'NLP',
  'INSTANCE_SO3_ATTITUDE_FIXED_3',
  'fixed_noiseless_three_correspondence_near_pi_attitude_alignment', 9,
  '{"ambient_matrix":"3x3_dense","intrinsic_degrees_of_freedom":3}',
  '{"reason":"deterministic educational generator; no wall-clock comparison","status":"not_applicable"}',
  '{"artifact_profile_ids":["PROFILE_SO3_ATTITUDE_ALIGNMENT"],"comparison_scope":"exact","generator_id":"educational.so3_attitude.v1","generator_version":"1.0.0","precision":"float64","runtime":"deterministic_educational"}',
  '{"limit":12,"unit":"oracle_evaluations"}', 12, NULL,
  '{"determinant_error":1e-10,"geodesic_residual_radians":0.05,"orthogonality_error":1e-10}',
  '{"policy":"fixed_oracle_budget","value":12}',
  '{"policy":"fixed_matrix","points":[1.0,0.0,0.0,0.0,1.0,0.0,0.0,0.0,1.0],"target_angle_radians":2.8,"target_axis":[0.2672612419124244,0.5345224838248488,0.8017837257372732]}',
  'not_applicable', NULL,
  'step size 0.35, target, initialization, objective, budget, and diagnostics fixed before execution',
  '{"artifact_profile_ids":["PROFILE_SO3_ATTITUDE_ALIGNMENT"],"generator_id":"educational.so3_attitude.v1","generator_version":"1.0.0","implementation_mapping_status":"not_applicable"}',
  '["objective_value","geodesic_residual","orthogonality_error","determinant_error"]',
  '{"completed":"fixed_budget_history","feasible_iterate":"structure_residuals_only","ranking":"forbidden"}',
  '["S044","S045","S071","S107"]', '2026-07-19'
);

PRAGMA foreign_keys = ON;
