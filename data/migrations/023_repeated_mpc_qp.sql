-- Canonical exact context for the EC025 repeated-MPC warm-start teaching contrast.
-- The executable instance is owned by problem-suite.json; this row owns only
-- the fixed comparison contract and explicitly avoids a hardware performance claim.

PRAGMA foreign_keys = OFF;

INSERT INTO benchmark_contexts (
  context_id, context_version, category, problem_instance_id, problem_variant, dimension,
  sparsity_json, hardware_json, runtime_json, oracle_budget_json, evaluation_budget,
  time_budget_seconds, tolerance_json, stopping_json, initialization_json, seed_status,
  seed_value, tuning_policy, implementation_versions_json, outcome_metrics_json,
  status_mapping_json, source_ids_json, last_verified
) VALUES (
  'BENCH_REPEATED_MPC_QP_EC025_4', '1.0.0', 'QP',
  'INSTANCE_REPEATED_MPC_QP_EC025',
  'fixed scalar repeated MPC QP; warm-start sensitivity under an educational timing ledger', 8,
  '{"horizon":4,"state_dimension":1,"control_dimension":1,"structure":"banded_linear_dynamics"}',
  '{"reason":"deterministic educational iteration-to-latency ledger; no CPU or wall-clock benchmark","status":"not_applicable"}',
  '{"comparison_scope":"exact","generator_id":"educational.repeated_mpc_qp.v1","generator_version":"1.0.0","precision":"float64","runtime":"deterministic_educational_ledger"}',
  '{"limit":4,"unit":"oracle_evaluations"}', 4, NULL,
  '{"primal_residual":0.00001,"dual_residual":0.00001,"deadline_ms":3.0}',
  '{"policy":"four_control_cycles","value":4}',
  '{"policy":"same_initial_state_each_member","points":[0.0],"reference":1.0}',
  'not_applicable', NULL,
  'horizon, dynamics, reference, bounds, residual ledger, deadline policy, and iteration-to-latency model fixed before comparing warm-start reuse',
  '{"generator_id":"educational.repeated_mpc_qp.v1","generator_version":"1.0.0","implementation_mapping_status":"not_applicable"}',
  '["tracking_error","primal_residual","dual_residual","solver_iterations","solve_time_ms","deadline_margin_ms"]',
  '{"deadline":"educational_ledger_only","ranking":"forbidden","hardware_measurement":"not_applicable"}',
  '["S012","S043","S076"]', '2026-07-24'
);

PRAGMA foreign_keys = ON;
