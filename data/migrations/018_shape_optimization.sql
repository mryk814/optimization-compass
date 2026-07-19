-- Canonical shape-optimization archetype, evidence, and exact educational
-- 0.18.7 context for Issue #134. The executable problem definition and instance are
-- owned by problem-suite.json.

PRAGMA foreign_keys = ON;

INSERT INTO sources (
  source_id, source_type, title, author_or_organization, publication_date,
  accessed_date, url, supported_claim, source_quality, notes, currentness_status
) VALUES
(
  'S104', 'original_paper',
  'cashocs: A Computational, Adjoint-Based Shape Optimization and Optimal Control Software',
  'Sebastian Blauth', '2020-10-05', '2026-07-19',
  'https://arxiv.org/abs/2010.02048',
  'PDE-constrained shape optimization, automated adjoint systems, and shape derivatives.',
  'primary', 'Original software paper; no figure, code, or prose is copied.',
  'historical_primary'
),
(
  'S105', 'original_paper',
  'Version 2.0 -- cashocs: A Computational, Adjoint-Based Shape Optimization and Optimal Control Software',
  'Sebastian Blauth', '2023-06-16', '2026-07-19',
  'https://arxiv.org/abs/2306.09828',
  'Level-set topology optimization and the distinction between shape and topology workflows.',
  'primary', 'Original version 2.0 paper; no figure, code, or prose is copied.',
  'verified_current'
),
(
  'S106', 'official_documentation',
  'Remeshing with cashocs',
  'cashocs project', NULL, '2026-07-19',
  'https://cashocs.readthedocs.io/en/stable/user/demos/shape_optimization/demo_remeshing/',
  'Shape-optimization remeshing workflow and explicit mesh-quality monitoring.',
  'primary', 'Official project documentation; no example code or media is copied.',
  'verified_current'
);

INSERT INTO problem_archetypes (
  problem_id, name_ja, name_en, summary, domain_group, canonical_form,
  primary_variable_type, objective_structure, constraint_structure, convexity,
  smoothness, derivative_access, typical_dimension, typical_evaluation_cost,
  typical_noise, evaluation_reliability, solution_requirement, special_structure,
  repeated_solve_mode, parallel_budget, generic_optimization_appropriate,
  alternative_check_ids, example_domains, first_questions, source_ids,
  confidence, last_verified
) VALUES (
  'PA057', '形状依存領域の最適化', 'Shape optimization on a parameterized domain',
  'parameterからgeometryとmeshを作り、shape-dependentなstate equationを解く最適化。',
  'scientific',
  'min J(u(q),Omega(q)) subject to R(u(q),Omega(q))=0 and geometry/mesh constraints',
  'shape', 'simulation', 'geometry;mesh;state;bounds', 'nonconvex', 'smooth_piecewise',
  'finite_difference;analytic_gradient;adjoint;shape_derivative', 'low_to_field',
  'expensive', 'deterministic', 'failure_possible', 'local_stationary',
  'parameter_geometry_mesh_state_pipeline', 'repeated_similar', 'parallel_state_solves',
  'conditional', 'ALT_SPECIALIZED;ALT_DECOMPOSITION',
  'structural;CFD;thermal;acoustic;photonic',
  'parameter、geometry、mesh、state、sensitivity、topology-changeの許否を分けて確認する。',
  'S101;S104;S105;S106', 'high', '2026-07-19'
);

PRAGMA foreign_keys = OFF;

INSERT INTO benchmark_contexts (
  context_id, context_version, category, problem_instance_id, problem_variant, dimension,
  sparsity_json, hardware_json, runtime_json, oracle_budget_json, evaluation_budget,
  time_budget_seconds, tolerance_json, stopping_json, initialization_json, seed_status,
  seed_value, tuning_policy, implementation_versions_json, outcome_metrics_json,
  status_mapping_json, source_ids_json, last_verified
) VALUES (
  'BENCH_SHAPE_TOPOLOGY_REPRESENTATION_6', '1.0.0', 'NLP',
  'INSTANCE_DIFFUSER_SHAPE_3P',
  'fixed reduced diffuser brief; representation contrast only', 3,
  '{"geometry_samples":21,"mesh":"deterministic educational quality proxy","state":"reduced loss proxy"}',
  '{"reason":"deterministic educational generator; no wall-clock comparison","status":"not_applicable"}',
  '{"comparison_scope":"exact","generator_id":"educational.shape_optimization.v1","generator_version":"1.0.0","precision":"float64","runtime":"deterministic_educational_generator"}',
  '{"limit":6,"unit":"oracle_evaluations"}', 6, NULL,
  '{"geometry_min_gap":0.4,"mesh_min_quality":0.2,"state_residual":0.000001}',
  '{"policy":"fixed_representation_audit_budget","value":6}',
  '{"policy":"fixed_shape_parameters","points":[1.15,0.0,0.0]}',
  'fixed', 134,
  'same physical brief, envelope, initial outer boundary, budget, diagnostics, tolerances, and seed; design representation only changes',
  '{"generator_id":"educational.shape_optimization.v1","generator_version":"1.0.0","implementation_mapping_status":"not_applicable"}',
  '["objective_value","geometry_min_gap","mesh_min_quality","state_residual","representation_freedom"]',
  '{"ranking":"forbidden","shape_feasibility":"discrete_geometry_and_mesh_only","terminal_status":"teaching_trace"}',
  '["S097","S101","S104","S105","S106"]', '2026-07-19'
);

PRAGMA foreign_keys = ON;
