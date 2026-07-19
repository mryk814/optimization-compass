-- Canonical exact context for the #137 pendulum mesh-sensitivity teaching contrast.
-- The problem instance itself is owned by problem-suite.json; this row only owns
-- the synchronized comparison context.

INSERT INTO sources (
  source_id, source_type, title, author_or_organization, publication_date,
  accessed_date, url, supported_claim, source_quality, notes, currentness_status
) VALUES (
  'S102', 'university_material', 'Trajectory Optimization',
  'MIT Underactuated Robotics', NULL, '2026-07-19',
  'https://underactuated.mit.edu/trajopt.html',
  'Direct collocation formulation, pendulum swing-up example, trajectory reconstruction, mesh refinement, and limits of local finite-dimensional solves.',
  'primary',
  'Official MIT course material; no figure, code, or prose is copied into this repository.',
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
  'BENCH_PENDULUM_COLLOCATION_MESH_8', '1.0.0', 'NLP',
  'INSTANCE_PENDULUM_SWING_UP_EC020',
  'fixed two-second torque-limited pendulum swing-up; mesh sensitivity only', 60,
  '{"coarse_mesh_nodes":20,"refined_mesh_nodes":40,"structure":"block_sparse_collocation"}',
  '{"reason":"deterministic educational generator; no wall-clock comparison","status":"not_applicable"}',
  '{"comparison_scope":"exact","generator_id":"educational.optimal_control.v1","generator_version":"1.1.0","precision":"float64","runtime":"deterministic_educational_generator"}',
  '{"limit":8,"unit":"oracle_evaluations"}', 8, NULL,
  '{"dynamics_defect":0.001,"node_path_violation":0.0001,"terminal_error":0.001}',
  '{"policy":"fixed_oracle_budget_and_common_tolerances","value":8}',
  '{"policy":"fixed_state_and_control_guess","points":[0.0,0.0]}',
  'fixed', 2026,
  'same dynamics, horizon, boundary/path constraints, initial guess, budget, and tolerances; mesh intervals only change',
  '{"generator_id":"educational.optimal_control.v1","generator_version":"1.1.0","implementation_mapping_status":"not_applicable"}',
  '["objective_value","dynamics_defect","node_path_violation","reconstructed_path_violation","terminal_error"]',
  '{"feasibility":"node_and_collocation_only","ranking":"forbidden","terminal_status":"teaching_trace"}',
  '["S042","S050","S102"]', '2026-07-19'
);

PRAGMA foreign_keys = ON;
