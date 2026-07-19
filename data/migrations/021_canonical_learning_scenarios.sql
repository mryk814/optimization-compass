-- Register generated primary scenarios as canonical dataset entities.
-- Derived variants may point only to scenario IDs that resolve in demo_scenarios.

INSERT INTO method_visualization_profiles (
  profile_id, method_id, family, support_status, min_dimension, max_dimension,
  generator_id, implementation_status, implementation_id, state_fields_json,
  event_types_json, source_ids_json, last_verified
) VALUES
(
  'PROFILE_OPTIMAL_CONTROL_GENERIC', 'M_DIRECT_COLLOCATION', 'first_order_trajectory_2d',
  'supported', 60, 60, 'educational.optimal_control.v1', 'not_applicable', NULL,
  '["state_norm","control_effort","dynamics_defect","node_path_violation","reconstructed_path_violation","terminal_error","objective_value"]',
  '["initialize","update","stop"]', '["S042","S050","S102"]', '2026-07-19'
),
(
  'PROFILE_SIMULATION_CONSTRAINED_LEDGER', 'M_ADJOINT_SENSITIVITY',
  'field_evolution', 'supported', 32, 32,
  'educational.simulation_constrained.v1', 'not_applicable', NULL,
  '["objective_value","state_residual","adjoint_residual","state_linear_iterations","adjoint_linear_iterations"]',
  '["design_state_adjoint","state_solve_failed"]',
  '["S019","S097","S101","S110"]', '2026-07-19'
),
(
  'PROFILE_SHAPE_DIFFUSER_GENERIC', 'M_SLSQP', 'feasible_region',
  'supported', 3, 3, 'educational.shape_optimization.v1', 'not_applicable', NULL,
  '["parameter_update_norm","geometry_min_gap","mesh_min_quality","inverted_cells","state_residual","objective_value","representation_freedom"]',
  '["initialize","update","geometry-failure","stop"]',
  '["S097","S101","S104","S105","S106"]', '2026-07-19'
),
(
  'PROFILE_SO3_ATTITUDE_ALIGNMENT', 'M_RIEMANNIAN_GRADIENT',
  'first_order_trajectory_2d', 'supported', 9, 9,
  'educational.so3_attitude.v1', 'not_applicable', NULL,
  '["objective_value","geodesic_residual","orthogonality_error","determinant_error","update_norm","map_correction_norm"]',
  '["initialize","update"]', '["S044","S045","S071","S107"]', '2026-07-19'
);

PRAGMA foreign_keys = OFF;

INSERT INTO demo_scenarios (
  scenario_id, method_id, profile_id, problem_instance_id, name_ja, name_en,
  initial_point_json, parameters_json, stopping_json, seed_status, seed_value,
  budget, source_ids_json, last_verified
) VALUES
(
  'SCENARIO_PENDULUM_SWING_UP_MESH_20', 'M_DIRECT_COLLOCATION',
  'PROFILE_OPTIMAL_CONTROL_GENERIC', 'INSTANCE_PENDULUM_SWING_UP_EC020',
  'Pendulum swing-up・N=20 mesh診断', 'Pendulum swing-up - N=20 mesh diagnostics',
  '[0.0,0.0]',
  '{"oracle_policy":["objective_value","constraint_value","constraint_jacobian"],"parameter_preset_id":"VIEW_OPTIMAL_CONTROL_HISTORY","tuning_policy":"fixed_preset"}',
  '{"dynamics_defect_tolerance":0.001,"max_oracle_evaluations":8}',
  'fixed', 2026, 8, '["S042","S050","S102"]', '2026-07-19'
),
(
  'SCENARIO_PDE_STATE_TOLERANCE_TIGHT', 'M_ADJOINT_SENSITIVITY',
  'PROFILE_SIMULATION_CONSTRAINED_LEDGER', 'INSTANCE_TOPOLOGY_CANTILEVER_2D',
  'PDE state solve・tight tolerance', 'PDE state solve - tight tolerance',
  '[0.5,0.0]',
  '{"oracle_policy":["state_solve","adjoint_solve"],"parameter_preset_id":"PDE_STATE_TOLERANCE_TIGHT","tuning_policy":"fixed_preset"}',
  '{"state_solve_calls":6,"state_tolerance":1e-08}',
  'not_applicable', NULL, 6, '["S019","S097","S101","S110"]', '2026-07-19'
),
(
  'SCENARIO_SHAPE_DIFFUSER_VALID_UPDATE', 'M_SLSQP',
  'PROFILE_SHAPE_DIFFUSER_GENERIC', 'INSTANCE_DIFFUSER_SHAPE_3P',
  '2D diffuser・有効なshape更新', '2D diffuser - valid shape update',
  '[1.15,0.0,0.0]',
  '{"oracle_policy":["objective_value","gradient","constraint_value","constraint_jacobian"],"parameter_preset_id":"PRESET_SHAPE_DIFFUSER_3P","tuning_policy":"fixed_preset"}',
  '{"geometry_min_gap":0.4,"max_oracle_evaluations":6,"mesh_min_quality":0.2,"state_residual_tolerance":1e-06}',
  'fixed', 134, 6, '["S097","S101","S104","S105","S106"]', '2026-07-19'
),
(
  'SCENARIO_SO3_RIEMANNIAN_ALIGNMENT', 'M_RIEMANNIAN_GRADIENT',
  'PROFILE_SO3_ATTITUDE_ALIGNMENT', 'INSTANCE_SO3_ATTITUDE_FIXED_3',
  'Lie algebra stepによるattitude alignment',
  'Attitude alignment by a Lie-algebra step',
  '[1.0,0.0,0.0,0.0,1.0,0.0,0.0,0.0,1.0]',
  '{"oracle_policy":["objective_value","gradient","constraint_value"],"parameter_preset_id":"SO3_RIEMANNIAN_FIXED","tuning_policy":"fixed_preset"}',
  '{"max_oracle_evaluations":12}',
  'not_applicable', NULL, 12, '["S044","S045","S071","S107"]', '2026-07-19'
);

PRAGMA foreign_keys = ON;
