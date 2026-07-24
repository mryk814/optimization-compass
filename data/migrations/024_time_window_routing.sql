-- Canonical exact context for EC019's fixed time-window routing teaching contrast.
-- This is a route-feasibility ledger, not an OR-Tools or local-search benchmark.

PRAGMA foreign_keys = OFF;

INSERT INTO benchmark_contexts (
  context_id, context_version, category, problem_instance_id, problem_variant, dimension,
  sparsity_json, hardware_json, runtime_json, oracle_budget_json, evaluation_budget,
  time_budget_seconds, tolerance_json, stopping_json, initialization_json, seed_status,
  seed_value, tuning_policy, implementation_versions_json, outcome_metrics_json,
  status_mapping_json, source_ids_json, last_verified
) VALUES (
  'BENCH_TIME_WINDOW_ROUTING_EC019_4', '1.0.0', 'MIP',
  'INSTANCE_TIME_WINDOW_ROUTING_EC019',
  'fixed depot, four-stop, one-vehicle route; stop-4 time-window hard-constraint contrast', 4,
  '{"stops":4,"vehicle_count":1,"travel_time_matrix":"5x5_minutes","route":"0-1-2-3-4-0"}',
  '{"reason":"deterministic route ledger; no CPU, wall-clock, or traffic measurement","status":"not_applicable"}',
  '{"comparison_scope":"exact","generator_id":"educational.time_window_routing.v1","generator_version":"1.0.0","runtime":"deterministic_educational_route_ledger"}',
  '{"limit":6,"unit":"oracle_evaluations"}', 6, NULL,
  '{"time_window_violation_minutes":0.0,"return_deadline_minutes":30.0}',
  '{"policy":"record_depot_departure_four_stops_and_return","route_legs":5}',
  '{"policy":"fixed_route","points":[1.0,2.0,3.0,4.0],"start_time_minutes":0}',
  'not_applicable', NULL,
  'route, travel-time matrix, vehicle count, start time, service time, return deadline, and all windows except stop-4 end fixed before comparison',
  '{"generator_id":"educational.time_window_routing.v1","generator_version":"1.0.0","implementation_mapping_status":"not_applicable"}',
  '["arrival_time","window_end","window_violation","cumulative_travel_time","route_feasibility"]',
  '{"time_window":"hard_constraint","ranking":"forbidden","solver_benchmark":"not_applicable"}',
  '["S022","S023","S024","S079"]', '2026-07-24'
);

PRAGMA foreign_keys = ON;
