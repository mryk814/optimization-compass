PRAGMA foreign_keys = ON;

CREATE TABLE advanced_view (
  problem_id TEXT NOT NULL,
  problem_name_ja TEXT,
  method_id TEXT NOT NULL,
  method_name_ja TEXT,
  method_family_id TEXT,
  fit_level TEXT CHECK (fit_level IS NULL OR fit_level IN ('conditional', 'default_choice', 'generally_unsuitable', 'incompatible', 'last_resort', 'recommended', 'specialized', 'strongly_recommended', 'unknown', 'viable')),
  beginner_priority TEXT CHECK (beginner_priority IS NULL OR beginner_priority IN ('avoid_as_default', 'expert_guidance_recommended', 'expert_only', 'first_try', 'second_try')),
  variable_type TEXT,
  objective_structure TEXT,
  constraint_structure TEXT,
  convexity TEXT,
  smoothness TEXT,
  derivative_access TEXT,
  dimension_context TEXT,
  evaluation_cost TEXT,
  noise TEXT,
  solution_requirement TEXT,
  required_conditions TEXT,
  exclusion_conditions TEXT,
  guarantee_notes TEXT,
  budget_notes TEXT,
  representative_implementation_ids TEXT,
  evidence_source_ids TEXT,
  confidence TEXT CHECK (confidence IS NULL OR confidence IN ('high', 'low', 'medium', 'unverified')),
  last_verified DATE,
  PRIMARY KEY (problem_id, method_id),
  FOREIGN KEY (problem_id) REFERENCES problem_archetypes(problem_id),
  FOREIGN KEY (method_id) REFERENCES methods(method_id)
);

CREATE TABLE alternative_solution_checks (
  alternative_id TEXT NOT NULL PRIMARY KEY,
  name_ja TEXT,
  name_en TEXT,
  trigger_conditions TEXT,
  preferred_approach TEXT,
  why_before_generic_optimization TEXT,
  false_positive_warning TEXT,
  related_problem_ids TEXT,
  representative_implementations TEXT,
  source_ids TEXT,
  confidence TEXT CHECK (confidence IS NULL OR confidence IN ('high', 'low', 'medium', 'unverified')),
  last_verified DATE
);

CREATE TABLE atomic_predicates (
  predicate_id TEXT NOT NULL PRIMARY KEY CHECK (trim(predicate_id) <> ''),
  schema_version TEXT NOT NULL CHECK (schema_version = '1.0.0'),
  subject_type TEXT NOT NULL CHECK (subject_type IN ('method', 'method_family', 'implementation')),
  subject_id TEXT NOT NULL CHECK (trim(subject_id) <> ''),
  predicate_kind TEXT NOT NULL CHECK (predicate_kind IN ('assumption', 'capability', 'incompatibility', 'recommendation_guard')),
  feature_id TEXT NOT NULL,
  operator TEXT NOT NULL CHECK (operator IN ('eq', 'neq', 'in', 'not_in', 'lt', 'lte', 'gt', 'gte', 'contains')),
  value_json TEXT NOT NULL CHECK (json_valid(value_json)),
  value_type TEXT NOT NULL CHECK (value_type IN ('controlled_code', 'number', 'string', 'boolean', 'list')),
  rationale_key TEXT NOT NULL CHECK (trim(rationale_key) <> ''),
  source_ids_json TEXT NOT NULL CHECK (json_valid(source_ids_json) AND json_type(source_ids_json) = 'array' AND json_array_length(source_ids_json) > 0),
  confidence TEXT NOT NULL CHECK (confidence IN ('high', 'medium', 'low')),
  last_verified DATE NOT NULL,
  UNIQUE (subject_type, subject_id, predicate_id),
  FOREIGN KEY (feature_id) REFERENCES problem_features(feature_id),
  CHECK (subject_type <> 'implementation' OR predicate_kind = 'capability')
);

CREATE TABLE backlog (
  backlog_id TEXT NOT NULL PRIMARY KEY,
  area TEXT,
  priority TEXT CHECK (priority IS NULL OR priority IN ('critical', 'high', 'low', 'medium')),
  issue TEXT,
  proposed_action TEXT,
  acceptance_criteria TEXT,
  dependencies TEXT,
  status TEXT CHECK (status IS NULL OR status IN ('deferred', 'done', 'in_progress', 'open')),
  target_version TEXT,
  owner TEXT,
  source_ids TEXT,
  notes TEXT,
  created_date DATE
);

CREATE TABLE beginner_view (
  view_id TEXT NOT NULL PRIMARY KEY,
  case_id TEXT NOT NULL,
  scenario TEXT,
  first_method TEXT,
  first_method_id TEXT NOT NULL,
  second_method TEXT,
  second_method_id TEXT NOT NULL,
  why TEXT,
  check_before_use TEXT,
  common_failure TEXT,
  switch_condition TEXT,
  representative_implementations TEXT,
  additional_question TEXT,
  confidence TEXT CHECK (confidence IS NULL OR confidence IN ('high', 'low', 'medium', 'unverified')),
  last_verified DATE,
  FOREIGN KEY (case_id) REFERENCES example_cases(case_id),
  FOREIGN KEY (first_method_id) REFERENCES methods(method_id),
  FOREIGN KEY (second_method_id) REFERENCES methods(method_id)
);

CREATE TABLE case_alternative_map (
  case_alternative_map_id TEXT NOT NULL PRIMARY KEY,
  case_id TEXT NOT NULL,
  alternative_id TEXT NOT NULL,
  sequence INTEGER,
  rationale TEXT,
  source_ids TEXT,
  confidence TEXT CHECK (confidence IS NULL OR confidence IN ('high', 'low', 'medium', 'unverified')),
  last_verified DATE,
  FOREIGN KEY (case_id) REFERENCES example_cases(case_id),
  FOREIGN KEY (alternative_id) REFERENCES alternative_solution_checks(alternative_id)
);

CREATE TABLE case_feature_map (
  case_feature_map_id TEXT NOT NULL PRIMARY KEY,
  case_id TEXT NOT NULL,
  feature_id TEXT NOT NULL,
  feature_value_id TEXT,
  value_text TEXT,
  truth_status TEXT CHECK (truth_status IS NULL OR truth_status IN ('conditional', 'implementation_dependent', 'no', 'not_applicable', 'unknown', 'yes')),
  notes TEXT,
  source_ids TEXT,
  confidence TEXT CHECK (confidence IS NULL OR confidence IN ('high', 'low', 'medium', 'unverified')),
  last_verified DATE,
  FOREIGN KEY (case_id) REFERENCES example_cases(case_id),
  FOREIGN KEY (feature_id) REFERENCES problem_features(feature_id),
  FOREIGN KEY (feature_value_id) REFERENCES feature_values(feature_value_id)
);

CREATE TABLE case_implementation_map (
  case_implementation_map_id TEXT NOT NULL PRIMARY KEY,
  case_id TEXT NOT NULL,
  implementation_id TEXT NOT NULL,
  role TEXT CHECK (role IS NULL OR role IN ('representative')),
  sequence INTEGER,
  notes TEXT,
  source_ids TEXT,
  confidence TEXT CHECK (confidence IS NULL OR confidence IN ('high', 'low', 'medium', 'unverified')),
  last_verified DATE,
  FOREIGN KEY (case_id) REFERENCES example_cases(case_id),
  FOREIGN KEY (implementation_id) REFERENCES implementations(implementation_id)
);

CREATE TABLE case_method_map (
  case_method_map_id TEXT NOT NULL PRIMARY KEY,
  case_id TEXT NOT NULL,
  method_id TEXT NOT NULL,
  role TEXT CHECK (role IS NULL OR role IN ('avoid', 'first_choice', 'second_choice')),
  fit_id TEXT,
  rationale TEXT,
  source_ids TEXT,
  confidence TEXT CHECK (confidence IS NULL OR confidence IN ('high', 'low', 'medium', 'unverified')),
  last_verified DATE,
  FOREIGN KEY (case_id) REFERENCES example_cases(case_id),
  FOREIGN KEY (method_id) REFERENCES methods(method_id),
  FOREIGN KEY (fit_id) REFERENCES problem_method_fit(fit_id)
);

CREATE TABLE comparison_set_members (
  comparison_set_id TEXT NOT NULL,
  member_id TEXT NOT NULL CHECK (trim(member_id) <> ''),
  method_id TEXT NOT NULL,
  profile_id TEXT NOT NULL,
  label TEXT NOT NULL CHECK (trim(label) <> ''),
  display_order INTEGER NOT NULL CHECK (display_order >= 1),
  parameters_json TEXT NOT NULL CHECK (json_valid(parameters_json) AND json_type(parameters_json) = 'object'),
  PRIMARY KEY (comparison_set_id, member_id),
  UNIQUE (comparison_set_id, display_order),
  UNIQUE (comparison_set_id, method_id),
  FOREIGN KEY (comparison_set_id) REFERENCES comparison_sets(comparison_set_id),
  FOREIGN KEY (method_id, profile_id) REFERENCES method_visualization_profiles(method_id, profile_id)
);

CREATE TABLE comparison_sets (
  comparison_set_id TEXT NOT NULL PRIMARY KEY CHECK (trim(comparison_set_id) <> ''),
  problem_instance_id TEXT NOT NULL,
  name_ja TEXT NOT NULL CHECK (trim(name_ja) <> ''),
  name_en TEXT NOT NULL CHECK (trim(name_en) <> ''),
  initial_point_json TEXT NOT NULL CHECK (json_valid(initial_point_json) AND json_type(initial_point_json) = 'array' AND json_array_length(initial_point_json) > 0),
  seed_status TEXT NOT NULL CHECK (seed_status IN ('fixed', 'not_applicable', 'unknown')),
  seed_value INTEGER,
  budget INTEGER NOT NULL CHECK (budget > 0),
  stopping_json TEXT NOT NULL CHECK (json_valid(stopping_json) AND json_type(stopping_json) = 'object'),
  synchronization TEXT NOT NULL CHECK (synchronization = 'oracle_evaluations'),
  fairness_note TEXT NOT NULL CHECK (trim(fairness_note) <> ''),
  source_ids_json TEXT NOT NULL CHECK (json_valid(source_ids_json) AND json_type(source_ids_json) = 'array' AND json_array_length(source_ids_json) > 0),
  last_verified DATE NOT NULL,
  FOREIGN KEY (problem_instance_id) REFERENCES problem_instances(problem_instance_id),
  CHECK ((seed_status = 'fixed' AND seed_value IS NOT NULL) OR (seed_status <> 'fixed' AND seed_value IS NULL))
);

CREATE TABLE controlled_vocab (
  vocab_name TEXT NOT NULL,
  value_code TEXT NOT NULL,
  label_ja TEXT,
  definition TEXT,
  sort_order INTEGER,
  deprecated TEXT,
  notes TEXT,
  PRIMARY KEY (vocab_name, value_code)
);

CREATE TABLE decision_questions (
  question_id TEXT NOT NULL PRIMARY KEY,
  sequence INTEGER,
  parent_question_id TEXT,
  question_ja TEXT,
  question_en TEXT,
  beginner_wording TEXT,
  answer_type TEXT,
  allowed_answers TEXT,
  mapped_feature_id TEXT NOT NULL,
  why_asked TEXT,
  show_conditions TEXT,
  expert_note TEXT,
  required TEXT,
  source_ids TEXT,
  confidence TEXT CHECK (confidence IS NULL OR confidence IN ('high', 'low', 'medium', 'unverified')),
  last_verified DATE,
  FOREIGN KEY (mapped_feature_id) REFERENCES problem_features(feature_id)
);

CREATE TABLE decision_rule_target_retirements (
  retirement_id TEXT NOT NULL PRIMARY KEY CHECK (trim(retirement_id) <> ''),
  rule_id TEXT NOT NULL,
  method_id TEXT NOT NULL,
  policy_id TEXT NOT NULL,
  reason TEXT NOT NULL CHECK (trim(reason) <> ''),
  source_ids_json TEXT NOT NULL CHECK (json_valid(source_ids_json) AND json_type(source_ids_json) = 'array' AND json_array_length(source_ids_json) > 0),
  last_verified DATE NOT NULL,
  UNIQUE (rule_id, method_id),
  FOREIGN KEY (rule_id) REFERENCES decision_rules(rule_id),
  FOREIGN KEY (method_id) REFERENCES methods(method_id),
  FOREIGN KEY (policy_id) REFERENCES predicate_policies(policy_id)
);

CREATE TABLE decision_rules (
  rule_id TEXT NOT NULL PRIMARY KEY,
  question_id TEXT NOT NULL,
  answer_condition TEXT,
  condition_expression TEXT,
  action_type TEXT CHECK (action_type IS NULL OR action_type IN ('ask_followup', 'demote_method', 'exclude_method', 'exclude_problem', 'include_problem', 'promote_method', 'recommend_alternative', 'warn')),
  action_target_type TEXT NOT NULL CHECK (action_target_type IN ('alternative', 'feature', 'method', 'none', 'problem')),
  action_target_ids TEXT,
  priority_effect TEXT,
  explanation TEXT,
  warnings TEXT,
  next_question_id TEXT,
  stop_or_continue TEXT,
  source_ids TEXT,
  confidence TEXT CHECK (confidence IS NULL OR confidence IN ('high', 'low', 'medium', 'unverified')),
  last_verified DATE,
  FOREIGN KEY (question_id) REFERENCES decision_questions(question_id)
);

CREATE TABLE demo_scenarios (
  scenario_id TEXT NOT NULL PRIMARY KEY CHECK (trim(scenario_id) <> ''),
  method_id TEXT NOT NULL,
  profile_id TEXT NOT NULL,
  problem_instance_id TEXT NOT NULL,
  name_ja TEXT NOT NULL CHECK (trim(name_ja) <> ''),
  name_en TEXT NOT NULL CHECK (trim(name_en) <> ''),
  initial_point_json TEXT NOT NULL CHECK (json_valid(initial_point_json) AND json_type(initial_point_json) = 'array' AND json_array_length(initial_point_json) > 0),
  parameters_json TEXT NOT NULL CHECK (json_valid(parameters_json) AND json_type(parameters_json) = 'object'),
  stopping_json TEXT NOT NULL CHECK (json_valid(stopping_json) AND json_type(stopping_json) = 'object'),
  seed_status TEXT NOT NULL CHECK (seed_status IN ('fixed', 'not_applicable', 'unknown')),
  seed_value INTEGER,
  budget INTEGER NOT NULL CHECK (budget > 0),
  source_ids_json TEXT NOT NULL CHECK (json_valid(source_ids_json) AND json_type(source_ids_json) = 'array' AND json_array_length(source_ids_json) > 0),
  last_verified DATE NOT NULL,
  FOREIGN KEY (method_id, profile_id) REFERENCES method_visualization_profiles(method_id, profile_id),
  FOREIGN KEY (problem_instance_id) REFERENCES problem_instances(problem_instance_id),
  CHECK ((seed_status = 'fixed' AND seed_value IS NOT NULL) OR (seed_status <> 'fixed' AND seed_value IS NULL))
);

CREATE TABLE diagnostics (
  diagnostic_id TEXT NOT NULL PRIMARY KEY,
  name_ja TEXT,
  name_en TEXT,
  category TEXT,
  metric_name TEXT,
  definition_or_formula TEXT,
  interpretation TEXT,
  warning_threshold TEXT,
  recommended_action TEXT,
  collection_cost TEXT,
  applicable_method_ids TEXT,
  applicable_problem_ids TEXT,
  related_failure_mode_ids TEXT,
  source_ids TEXT,
  confidence TEXT CHECK (confidence IS NULL OR confidence IN ('high', 'low', 'medium', 'unverified')),
  last_verified DATE
);

CREATE TABLE evidence_links (
  evidence_link_id TEXT NOT NULL PRIMARY KEY,
  source_id TEXT NOT NULL,
  target_table TEXT,
  target_id TEXT,
  supported_field TEXT,
  claim_summary TEXT,
  evidence_role TEXT,
  confidence TEXT CHECK (confidence IS NULL OR confidence IN ('high', 'low', 'medium', 'unverified')),
  last_verified DATE,
  FOREIGN KEY (source_id) REFERENCES sources(source_id)
);

CREATE TABLE example_cases (
  case_id TEXT NOT NULL PRIMARY KEY,
  title_ja TEXT,
  problem_id TEXT NOT NULL,
  problem_features_summary TEXT,
  alternative_solution_ids TEXT,
  first_choice_method_id TEXT NOT NULL,
  second_choice_method_id TEXT NOT NULL,
  avoid_method_id TEXT NOT NULL,
  decision_reason TEXT,
  additional_information_needed TEXT,
  representative_implementation_ids TEXT,
  expected_failures TEXT,
  switch_decision TEXT,
  validation_result TEXT CHECK (validation_result IS NULL OR validation_result IN ('fail', 'partial', 'pass')),
  model_revision_notes TEXT,
  source_ids TEXT,
  confidence TEXT CHECK (confidence IS NULL OR confidence IN ('high', 'low', 'medium', 'unverified')),
  last_verified DATE,
  FOREIGN KEY (problem_id) REFERENCES problem_archetypes(problem_id),
  FOREIGN KEY (first_choice_method_id) REFERENCES methods(method_id),
  FOREIGN KEY (second_choice_method_id) REFERENCES methods(method_id),
  FOREIGN KEY (avoid_method_id) REFERENCES methods(method_id)
);

CREATE TABLE failure_modes (
  failure_mode_id TEXT NOT NULL PRIMARY KEY,
  name_ja TEXT,
  name_en TEXT,
  category TEXT,
  applies_to_method_ids TEXT,
  applies_to_problem_ids TEXT,
  symptoms TEXT,
  root_causes TEXT,
  diagnostic_ids TEXT,
  severity TEXT CHECK (severity IS NULL OR severity IN ('critical', 'high', 'info', 'warning')),
  impact TEXT,
  prevention TEXT,
  remediation TEXT,
  switch_condition TEXT,
  source_ids TEXT,
  confidence TEXT CHECK (confidence IS NULL OR confidence IN ('high', 'low', 'medium', 'unverified')),
  last_verified DATE
);

CREATE TABLE feature_values (
  feature_value_id TEXT NOT NULL PRIMARY KEY,
  feature_id TEXT NOT NULL,
  value_code TEXT,
  label_ja TEXT,
  label_en TEXT,
  sort_order INTEGER,
  definition TEXT,
  lower_bound TEXT,
  upper_bound TEXT,
  unit TEXT,
  conditions TEXT,
  notes TEXT,
  FOREIGN KEY (feature_id) REFERENCES problem_features(feature_id)
);

CREATE TABLE glossary (
  term_id TEXT NOT NULL PRIMARY KEY,
  term_ja TEXT,
  term_en TEXT,
  definition TEXT,
  common_confusion TEXT,
  related_entity_ids TEXT,
  source_ids TEXT,
  confidence TEXT CHECK (confidence IS NULL OR confidence IN ('high', 'low', 'medium', 'unverified')),
  last_verified DATE
);

CREATE TABLE implementations (
  implementation_id TEXT NOT NULL PRIMARY KEY,
  library_name TEXT,
  solver_name TEXT,
  api_name TEXT,
  method_selector TEXT,
  language TEXT,
  license TEXT,
  commercial_model TEXT CHECK (commercial_model IS NULL OR commercial_model IN ('commercial', 'commercial_with_free_tiers', 'freeware', 'modeling_layer', 'open_source', 'unknown')),
  free_use_conditions TEXT,
  open_source TEXT CHECK (open_source IS NULL OR open_source IN ('conditional', 'implementation_dependent', 'no', 'not_applicable', 'unknown', 'yes')),
  os_support TEXT,
  problem_formats TEXT,
  variable_support TEXT,
  constraint_support TEXT,
  analytic_derivatives TEXT,
  autodiff TEXT,
  numerical_diff TEXT,
  sparse_support TEXT,
  parallelism TEXT,
  gpu_support TEXT,
  warm_start TEXT,
  callback TEXT,
  termination_controls TEXT,
  initialization TEXT,
  constraint_violation_reporting TEXT,
  optimality_info TEXT,
  dual_variables TEXT,
  optimality_gap TEXT,
  sensitivity_info TEXT,
  status_codes TEXT,
  major_options TEXT,
  default_safety TEXT,
  documentation_quality TEXT,
  beginner_usability TEXT,
  maintenance_status TEXT CHECK (maintenance_status IS NULL OR maintenance_status IN ('active', 'active_docs_verified', 'legacy', 'limited_support', 'mature', 'unknown')),
  last_release TEXT,
  last_verified DATE,
  official_docs_url TEXT,
  official_repo_url TEXT,
  usage_example TEXT,
  notes TEXT,
  supported_method_ids TEXT,
  implementation_differences TEXT,
  source_ids TEXT,
  confidence TEXT CHECK (confidence IS NULL OR confidence IN ('high', 'low', 'medium', 'unverified'))
);

CREATE TABLE learning_coverage_expectations (
  expectation_id TEXT NOT NULL PRIMARY KEY CHECK (trim(expectation_id) <> ''),
  subject_type TEXT NOT NULL CHECK (subject_type IN ('method', 'problem', 'feature_family')),
  subject_id TEXT NOT NULL CHECK (trim(subject_id) <> ''),
  purpose TEXT NOT NULL CHECK (purpose IN ('mechanism', 'comparison', 'failure_contrast', 'sensitivity', 'application_result', 'schematic')),
  artifact_kind TEXT NOT NULL CHECK (artifact_kind IN ('executable_trace', 'schematic_animation', 'static_diagram', 'result_visualization')),
  renderer_family TEXT NOT NULL CHECK (trim(renderer_family) <> ''),
  applicability TEXT NOT NULL CHECK (applicability IN ('expected', 'not_applicable')),
  rationale TEXT NOT NULL CHECK (trim(rationale) <> ''),
  source_ids_json TEXT NOT NULL CHECK (json_valid(source_ids_json) AND json_type(source_ids_json) = 'array' AND json_array_length(source_ids_json) > 0),
  last_verified DATE NOT NULL,
  slice_id TEXT,
  UNIQUE (subject_type, subject_id, purpose, artifact_kind, renderer_family),
  FOREIGN KEY (slice_id) REFERENCES learning_slice_priorities(slice_id)
);

CREATE TABLE learning_edges (
  edge_id TEXT NOT NULL PRIMARY KEY CHECK (trim(edge_id) <> ''),
  source_type TEXT NOT NULL CHECK (source_type IN ('method', 'view_preset', 'visualization_profile', 'objective', 'scenario', 'comparison')),
  source_id TEXT NOT NULL CHECK (trim(source_id) <> ''),
  target_type TEXT NOT NULL CHECK (target_type IN ('method', 'view_preset', 'visualization_profile', 'objective', 'scenario', 'comparison')),
  target_id TEXT NOT NULL CHECK (trim(target_id) <> ''),
  relation TEXT NOT NULL CHECK (relation IN ('prerequisite', 'next', 'related', 'contrast')),
  rationale TEXT NOT NULL CHECK (trim(rationale) <> ''),
  display_order INTEGER NOT NULL CHECK (display_order >= 1),
  source_ids_json TEXT NOT NULL CHECK (json_valid(source_ids_json) AND json_type(source_ids_json) = 'array' AND json_array_length(source_ids_json) > 0),
  last_verified DATE NOT NULL,
  UNIQUE (source_type, source_id, target_type, target_id, relation),
  CHECK (source_type <> target_type OR source_id <> target_id)
);

CREATE TABLE learning_slice_priorities (
  slice_id TEXT NOT NULL PRIMARY KEY CHECK (trim(slice_id) <> ''),
  title_ja TEXT NOT NULL CHECK (trim(title_ja) <> ''),
  title_en TEXT NOT NULL CHECK (trim(title_en) <> ''),
  classification_score INTEGER NOT NULL CHECK (classification_score BETWEEN 0 AND 3),
  classification_reason TEXT NOT NULL CHECK (trim(classification_reason) <> ''),
  misconception_score INTEGER NOT NULL CHECK (misconception_score BETWEEN 0 AND 3),
  misconception_reason TEXT NOT NULL CHECK (trim(misconception_reason) <> ''),
  visualization_score INTEGER NOT NULL CHECK (visualization_score BETWEEN 0 AND 3),
  visualization_reason TEXT NOT NULL CHECK (trim(visualization_reason) <> ''),
  demand_score INTEGER NOT NULL CHECK (demand_score BETWEEN 0 AND 3),
  demand_reason TEXT NOT NULL CHECK (trim(demand_reason) <> ''),
  proposed_scope TEXT NOT NULL CHECK (trim(proposed_scope) <> ''),
  source_ids_json TEXT NOT NULL CHECK (json_valid(source_ids_json) AND json_type(source_ids_json) = 'array' AND json_array_length(source_ids_json) > 0),
  last_verified DATE NOT NULL
);

CREATE TABLE method_hierarchy (
  hierarchy_id TEXT NOT NULL PRIMARY KEY,
  parent_method_id TEXT NOT NULL,
  child_method_id TEXT NOT NULL,
  relation_type TEXT CHECK (relation_type IS NULL OR relation_type IN ('hybrid_of', 'implementation_alias_of', 'is_a', 'related', 'uses_subroutine', 'variant_of')),
  depth INTEGER,
  is_primary_parent TEXT,
  rationale TEXT,
  source_ids TEXT,
  confidence TEXT CHECK (confidence IS NULL OR confidence IN ('high', 'low', 'medium', 'unverified')),
  last_verified DATE,
  FOREIGN KEY (parent_method_id) REFERENCES methods(method_id),
  FOREIGN KEY (child_method_id) REFERENCES methods(method_id)
);

CREATE TABLE method_implementation_map (
  method_implementation_map_id TEXT NOT NULL PRIMARY KEY,
  method_id TEXT NOT NULL,
  implementation_id TEXT NOT NULL,
  support_level TEXT CHECK (support_level IS NULL OR support_level IN ('emulated', 'experimental', 'native', 'not_supported', 'partial', 'unknown', 'via_wrapper')),
  api_name TEXT,
  method_selector TEXT,
  implementation_notes TEXT,
  limitations TEXT,
  source_ids TEXT,
  confidence TEXT CHECK (confidence IS NULL OR confidence IN ('high', 'low', 'medium', 'unverified')),
  last_verified DATE,
  FOREIGN KEY (method_id) REFERENCES methods(method_id),
  FOREIGN KEY (implementation_id) REFERENCES implementations(implementation_id)
);

CREATE TABLE method_visualization_profiles (
  profile_id TEXT NOT NULL PRIMARY KEY CHECK (trim(profile_id) <> ''),
  method_id TEXT NOT NULL,
  family TEXT NOT NULL CHECK (family IN ('simplex_2d', 'first_order_trajectory_2d')),
  support_status TEXT NOT NULL CHECK (support_status IN ('supported', 'unsupported', 'unknown', 'not_applicable')),
  min_dimension INTEGER NOT NULL CHECK (min_dimension >= 1),
  max_dimension INTEGER NOT NULL CHECK (max_dimension >= min_dimension),
  generator_id TEXT NOT NULL CHECK (trim(generator_id) <> ''),
  implementation_status TEXT NOT NULL CHECK (implementation_status IN ('supported', 'unsupported', 'unknown', 'not_applicable')),
  implementation_id TEXT,
  state_fields_json TEXT NOT NULL CHECK (json_valid(state_fields_json) AND json_type(state_fields_json) = 'array' AND json_array_length(state_fields_json) > 0),
  event_types_json TEXT NOT NULL CHECK (json_valid(event_types_json) AND json_type(event_types_json) = 'array' AND json_array_length(event_types_json) > 0),
  source_ids_json TEXT NOT NULL CHECK (json_valid(source_ids_json) AND json_type(source_ids_json) = 'array' AND json_array_length(source_ids_json) > 0),
  last_verified DATE NOT NULL,
  UNIQUE (method_id, profile_id),
  FOREIGN KEY (method_id) REFERENCES methods(method_id),
  FOREIGN KEY (implementation_id) REFERENCES implementations(implementation_id),
  CHECK (
    (implementation_status = 'supported' AND implementation_id IS NOT NULL AND trim(implementation_id) <> '')
    OR
    (implementation_status <> 'supported' AND implementation_id IS NULL)
  )
);

CREATE TABLE methods (
  method_id TEXT NOT NULL PRIMARY KEY,
  name_ja TEXT,
  name_en TEXT,
  aliases TEXT,
  method_family_id TEXT NOT NULL,
  method_level TEXT CHECK (method_level IS NULL OR method_level IN ('family', 'general_algorithm', 'implementation_alias', 'variant')),
  summary TEXT,
  problem_classes TEXT,
  required_assumptions TEXT,
  derivative_information TEXT,
  variable_types TEXT,
  constraint_support TEXT,
  convex_fit TEXT,
  nonconvex_applicability TEXT,
  solution_scope TEXT CHECK (solution_scope IS NULL OR solution_scope IN ('anytime', 'convex_global', 'feasible_only', 'global_candidate', 'global_certificate', 'local', 'pareto')),
  determinism TEXT CHECK (determinism IS NULL OR determinism IN ('deterministic', 'hybrid', 'implementation_dependent', 'stochastic')),
  exactness TEXT CHECK (exactness IS NULL OR exactness IN ('approximation', 'exact_with_tolerance', 'heuristic', 'local_numerical', 'metaheuristic', 'statistical')),
  theoretical_guarantee TEXT,
  optimality_certificate TEXT,
  scalability TEXT,
  memory_tendency TEXT,
  per_iteration_cost TEXT,
  evaluation_pattern TEXT,
  parallelism TEXT,
  initialization_sensitivity TEXT,
  hyperparameter_sensitivity TEXT,
  scaling_sensitivity TEXT,
  noise_robustness TEXT,
  discontinuity_robustness TEXT,
  constraint_violation_handling TEXT,
  warm_start TEXT,
  online_use TEXT,
  strengths TEXT,
  weaknesses TEXT,
  typical_failures TEXT,
  avoid_conditions TEXT,
  first_choice_conditions TEXT,
  second_choice_conditions TEXT,
  switch_signals TEXT,
  beginner_level TEXT,
  tuning_difficulty TEXT,
  implementation_difficulty TEXT,
  explainability TEXT,
  stopping_criteria TEXT,
  diagnostic_metrics TEXT,
  related_method_ids TEXT,
  parent_method_id TEXT,
  child_method_ids TEXT,
  reference_source_ids TEXT,
  confidence TEXT CHECK (confidence IS NULL OR confidence IN ('high', 'low', 'medium', 'unverified')),
  last_verified DATE,
  FOREIGN KEY (method_family_id) REFERENCES methods(method_id),
  FOREIGN KEY (parent_method_id) REFERENCES methods(method_id)
);

CREATE TABLE model_revisions (
  revision_id TEXT NOT NULL PRIMARY KEY,
  trigger_case_ids TEXT,
  issue_found TEXT,
  schema_change TEXT,
  reason TEXT,
  version TEXT,
  date DATE
);

CREATE TABLE predicate_coverage (
  subject_type TEXT NOT NULL CHECK (subject_type IN ('method', 'implementation')),
  subject_id TEXT NOT NULL CHECK (trim(subject_id) <> ''),
  status TEXT NOT NULL CHECK (status IN ('complete', 'partial', 'not_started', 'not_applicable')),
  rationale TEXT NOT NULL CHECK (trim(rationale) <> ''),
  source_ids_json TEXT NOT NULL CHECK (json_valid(source_ids_json) AND json_type(source_ids_json) = 'array' AND json_array_length(source_ids_json) > 0),
  last_verified DATE NOT NULL,
  PRIMARY KEY (subject_type, subject_id)
);

CREATE TABLE predicate_policies (
  policy_id TEXT NOT NULL PRIMARY KEY CHECK (trim(policy_id) <> ''),
  schema_version TEXT NOT NULL CHECK (schema_version = '1.0.0'),
  subject_type TEXT NOT NULL CHECK (subject_type IN ('method', 'method_family', 'implementation')),
  subject_id TEXT NOT NULL CHECK (trim(subject_id) <> ''),
  effect TEXT NOT NULL CHECK (effect IN ('require', 'exclude')),
  expression_json TEXT CHECK (expression_json IS NULL OR json_valid(expression_json)),
  inheritance_mode TEXT NOT NULL CHECK (inheritance_mode IN ('inheritable', 'local_only')),
  override_action TEXT NOT NULL CHECK (override_action IN ('add', 'replace', 'suppress')),
  overrides_policy_id TEXT,
  rationale_key TEXT NOT NULL CHECK (trim(rationale_key) <> ''),
  source_ids_json TEXT NOT NULL CHECK (json_valid(source_ids_json) AND json_type(source_ids_json) = 'array' AND json_array_length(source_ids_json) > 0),
  confidence TEXT NOT NULL CHECK (confidence IN ('high', 'medium', 'low')),
  last_verified DATE NOT NULL,
  FOREIGN KEY (overrides_policy_id) REFERENCES predicate_policies(policy_id),
  CHECK (subject_type <> 'implementation' OR effect = 'require'),
  CHECK (
    (override_action = 'add' AND overrides_policy_id IS NULL AND expression_json IS NOT NULL)
    OR (override_action = 'replace' AND overrides_policy_id IS NOT NULL AND expression_json IS NOT NULL)
    OR (override_action = 'suppress' AND overrides_policy_id IS NOT NULL AND expression_json IS NULL AND inheritance_mode = 'local_only')
  )
);

CREATE TABLE problem_alternative_map (
  problem_alternative_map_id TEXT NOT NULL PRIMARY KEY,
  problem_id TEXT NOT NULL,
  alternative_id TEXT NOT NULL,
  priority TEXT CHECK (priority IS NULL OR priority IN ('precheck')),
  sequence INTEGER,
  rationale TEXT,
  source_ids TEXT,
  confidence TEXT CHECK (confidence IS NULL OR confidence IN ('high', 'low', 'medium', 'unverified')),
  last_verified DATE,
  FOREIGN KEY (problem_id) REFERENCES problem_archetypes(problem_id),
  FOREIGN KEY (alternative_id) REFERENCES alternative_solution_checks(alternative_id)
);

CREATE TABLE problem_archetypes (
  problem_id TEXT NOT NULL PRIMARY KEY,
  name_ja TEXT,
  name_en TEXT,
  summary TEXT,
  domain_group TEXT,
  canonical_form TEXT,
  primary_variable_type TEXT,
  objective_structure TEXT,
  constraint_structure TEXT,
  convexity TEXT,
  smoothness TEXT,
  derivative_access TEXT,
  typical_dimension TEXT,
  typical_evaluation_cost TEXT,
  typical_noise TEXT,
  evaluation_reliability TEXT,
  solution_requirement TEXT,
  special_structure TEXT,
  repeated_solve_mode TEXT,
  parallel_budget TEXT,
  generic_optimization_appropriate TEXT,
  alternative_check_ids TEXT,
  example_domains TEXT,
  first_questions TEXT,
  source_ids TEXT,
  confidence TEXT CHECK (confidence IS NULL OR confidence IN ('high', 'low', 'medium', 'unverified')),
  last_verified DATE
);

CREATE TABLE problem_definition_archetypes (
  problem_definition_id TEXT NOT NULL,
  problem_id TEXT NOT NULL,
  PRIMARY KEY (problem_definition_id, problem_id),
  FOREIGN KEY (problem_definition_id) REFERENCES problem_definitions(problem_definition_id),
  FOREIGN KEY (problem_id) REFERENCES problem_archetypes(problem_id)
);

CREATE TABLE problem_definition_features (
  problem_definition_id TEXT NOT NULL,
  feature_id TEXT NOT NULL,
  PRIMARY KEY (problem_definition_id, feature_id),
  FOREIGN KEY (problem_definition_id) REFERENCES problem_definitions(problem_definition_id),
  FOREIGN KEY (feature_id) REFERENCES problem_features(feature_id)
);

CREATE TABLE problem_definitions (
  problem_definition_id TEXT NOT NULL PRIMARY KEY CHECK (trim(problem_definition_id) <> ''),
  name_ja TEXT NOT NULL CHECK (trim(name_ja) <> ''),
  name_en TEXT NOT NULL CHECK (trim(name_en) <> ''),
  mathematical_family TEXT NOT NULL CHECK (trim(mathematical_family) <> ''),
  variable_domain TEXT NOT NULL CHECK (trim(variable_domain) <> ''),
  objective_form TEXT NOT NULL CHECK (trim(objective_form) <> ''),
  objective_direction TEXT NOT NULL CHECK (objective_direction IN ('minimize', 'maximize', 'multiobjective')),
  available_oracles_json TEXT NOT NULL CHECK (json_valid(available_oracles_json) AND json_type(available_oracles_json) = 'array' AND json_array_length(available_oracles_json) > 0),
  constraint_class TEXT NOT NULL CHECK (trim(constraint_class) <> ''),
  dimensionality_policy_json TEXT NOT NULL CHECK (json_valid(dimensionality_policy_json) AND json_type(dimensionality_policy_json) = 'object'),
  known_reference_semantics TEXT NOT NULL CHECK (trim(known_reference_semantics) <> ''),
  related_problem_ids_json TEXT NOT NULL CHECK (json_valid(related_problem_ids_json) AND json_type(related_problem_ids_json) = 'array' AND json_array_length(related_problem_ids_json) > 0),
  feature_ids_json TEXT NOT NULL CHECK (json_valid(feature_ids_json) AND json_type(feature_ids_json) = 'array' AND json_array_length(feature_ids_json) > 0),
  source_ids_json TEXT NOT NULL CHECK (json_valid(source_ids_json) AND json_type(source_ids_json) = 'array' AND json_array_length(source_ids_json) > 0),
  last_verified DATE NOT NULL
);

CREATE TABLE problem_feature_map (
  problem_feature_map_id TEXT NOT NULL PRIMARY KEY,
  problem_id TEXT NOT NULL,
  feature_id TEXT NOT NULL,
  feature_value_id TEXT,
  value_numeric TEXT,
  value_text TEXT,
  truth_status TEXT CHECK (truth_status IS NULL OR truth_status IN ('conditional', 'implementation_dependent', 'no', 'not_applicable', 'unknown', 'yes')),
  is_defining TEXT,
  conditions TEXT,
  confidence TEXT CHECK (confidence IS NULL OR confidence IN ('high', 'low', 'medium', 'unverified')),
  source_ids TEXT,
  last_verified DATE,
  FOREIGN KEY (problem_id) REFERENCES problem_archetypes(problem_id),
  FOREIGN KEY (feature_id) REFERENCES problem_features(feature_id),
  FOREIGN KEY (feature_value_id) REFERENCES feature_values(feature_value_id)
);

CREATE TABLE problem_features (
  feature_id TEXT NOT NULL PRIMARY KEY,
  feature_code TEXT,
  category TEXT,
  name_ja TEXT,
  name_en TEXT,
  value_type TEXT,
  unit TEXT,
  allowed_vocab_id TEXT,
  definition TEXT,
  why_it_matters TEXT,
  boundary_notes TEXT,
  source_ids TEXT,
  confidence TEXT CHECK (confidence IS NULL OR confidence IN ('high', 'low', 'medium', 'unverified')),
  last_verified DATE
);

CREATE TABLE problem_instances (
  problem_instance_id TEXT NOT NULL PRIMARY KEY CHECK (trim(problem_instance_id) <> ''),
  problem_definition_id TEXT NOT NULL,
  name_ja TEXT NOT NULL CHECK (trim(name_ja) <> ''),
  name_en TEXT NOT NULL CHECK (trim(name_en) <> ''),
  registry_key TEXT NOT NULL UNIQUE CHECK (trim(registry_key) <> ''),
  dimension INTEGER NOT NULL CHECK (dimension >= 1),
  parameters_json TEXT NOT NULL CHECK (json_valid(parameters_json) AND json_type(parameters_json) = 'object'),
  bounds_json TEXT NOT NULL CHECK (json_valid(bounds_json) AND json_type(bounds_json) = 'object'),
  constraints_json TEXT NOT NULL CHECK (json_valid(constraints_json) AND json_type(constraints_json) = 'array'),
  initialization_candidates_json TEXT NOT NULL CHECK (json_valid(initialization_candidates_json) AND json_type(initialization_candidates_json) = 'array' AND json_array_length(initialization_candidates_json) > 0),
  seed_status TEXT NOT NULL CHECK (seed_status IN ('fixed', 'not_applicable', 'unknown')),
  seed_value INTEGER,
  known_reference_status TEXT NOT NULL CHECK (known_reference_status IN ('known_exact', 'known_reference', 'best_known', 'unknown', 'not_meaningful')),
  known_reference_json TEXT CHECK (known_reference_json IS NULL OR (json_valid(known_reference_json) AND json_type(known_reference_json) = 'object')),
  display_json TEXT NOT NULL CHECK (json_valid(display_json) AND json_type(display_json) = 'object'),
  intended_phenomena_json TEXT NOT NULL CHECK (json_valid(intended_phenomena_json) AND json_type(intended_phenomena_json) = 'array' AND json_array_length(intended_phenomena_json) > 0),
  limitations_ja TEXT NOT NULL CHECK (trim(limitations_ja) <> ''),
  limitations_en TEXT NOT NULL CHECK (trim(limitations_en) <> ''),
  source_ids_json TEXT NOT NULL CHECK (json_valid(source_ids_json) AND json_type(source_ids_json) = 'array' AND json_array_length(source_ids_json) > 0),
  last_verified DATE NOT NULL,
  FOREIGN KEY (problem_definition_id) REFERENCES problem_definitions(problem_definition_id),
  CHECK ((seed_status = 'fixed' AND seed_value IS NOT NULL) OR (seed_status <> 'fixed' AND seed_value IS NULL)),
  CHECK (
    (known_reference_status IN ('known_exact', 'known_reference', 'best_known') AND known_reference_json IS NOT NULL)
    OR (known_reference_status IN ('unknown', 'not_meaningful') AND known_reference_json IS NULL)
  )
);

CREATE TABLE problem_method_fit (
  fit_id TEXT NOT NULL PRIMARY KEY,
  problem_or_feature_id TEXT NOT NULL,
  target_type TEXT CHECK (target_type IS NULL OR target_type IN ('implementation', 'method', 'problem')),
  method_id TEXT NOT NULL,
  fit_level TEXT CHECK (fit_level IS NULL OR fit_level IN ('conditional', 'default_choice', 'generally_unsuitable', 'incompatible', 'last_resort', 'recommended', 'specialized', 'strongly_recommended', 'unknown', 'viable')),
  beginner_priority TEXT CHECK (beginner_priority IS NULL OR beginner_priority IN ('avoid_as_default', 'expert_guidance_recommended', 'expert_only', 'first_try', 'second_try')),
  applicable_conditions TEXT,
  required_conditions TEXT,
  favorable_conditions TEXT,
  unfavorable_conditions TEXT,
  exclusion_conditions TEXT,
  expected_strengths TEXT,
  expected_weaknesses TEXT,
  evaluation_budget_notes TEXT,
  dimensionality_notes TEXT,
  noise_notes TEXT,
  constraint_notes TEXT,
  initialization_notes TEXT,
  guarantee_notes TEXT,
  tuning_notes TEXT,
  rationale TEXT,
  evidence_source_ids TEXT,
  confidence TEXT CHECK (confidence IS NULL OR confidence IN ('high', 'low', 'medium', 'unverified')),
  last_verified DATE,
  FOREIGN KEY (problem_or_feature_id) REFERENCES problem_archetypes(problem_id),
  FOREIGN KEY (method_id) REFERENCES methods(method_id)
);

CREATE TABLE readme (
  section TEXT NOT NULL,
  item TEXT NOT NULL,
  value TEXT,
  notes TEXT,
  PRIMARY KEY (section, item)
);

CREATE TABLE release_checks (
  check_id TEXT NOT NULL PRIMARY KEY,
  check_name TEXT NOT NULL,
  scope TEXT NOT NULL,
  severity TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('pass', 'warn', 'fail', 'not_run')),
  observed_value TEXT,
  expected_condition TEXT NOT NULL,
  details TEXT,
  checked_at DATE NOT NULL
);

CREATE TABLE schema_dictionary (
  schema_field_id TEXT NOT NULL PRIMARY KEY,
  sheet_name TEXT NOT NULL,
  table_name TEXT NOT NULL,
  column_order INTEGER NOT NULL,
  column_name TEXT NOT NULL,
  display_name_ja TEXT NOT NULL,
  data_type TEXT NOT NULL,
  required TEXT NOT NULL,
  primary_key TEXT NOT NULL,
  foreign_key TEXT NOT NULL,
  foreign_key_target TEXT NOT NULL,
  controlled_vocabulary TEXT NOT NULL,
  example_value TEXT NOT NULL,
  definition TEXT NOT NULL,
  notes TEXT NOT NULL
);

CREATE TABLE sheet_catalog (
  sheet_name TEXT NOT NULL PRIMARY KEY,
  table_name TEXT NOT NULL,
  purpose TEXT NOT NULL,
  primary_key TEXT NOT NULL,
  foreign_keys TEXT NOT NULL,
  row_count INTEGER NOT NULL,
  column_count INTEGER NOT NULL,
  normalization_role TEXT NOT NULL,
  derived_or_base TEXT NOT NULL,
  update_frequency TEXT NOT NULL,
  notes TEXT NOT NULL
);

CREATE TABLE sources (
  source_id TEXT NOT NULL PRIMARY KEY,
  source_type TEXT CHECK (source_type IS NULL OR source_type IN ('official_documentation', 'official_issue', 'official_repository', 'original_paper', 'standard', 'textbook', 'university_material', 'vendor_manual')),
  title TEXT,
  author_or_organization TEXT,
  publication_date DATE,
  accessed_date DATE,
  url TEXT,
  supported_claim TEXT,
  source_quality TEXT CHECK (source_quality IS NULL OR source_quality IN ('high', 'primary', 'supporting')),
  notes TEXT,
  currentness_status TEXT CHECK (currentness_status IS NULL OR currentness_status IN ('historical_primary', 'not_time_sensitive', 'verified_current'))
);

CREATE TABLE version_history (
  version TEXT NOT NULL PRIMARY KEY,
  release_date DATE,
  status TEXT,
  summary TEXT,
  breaking_changes TEXT,
  source_policy TEXT,
  notes TEXT
);

CREATE TABLE view_presets (
  preset_id TEXT NOT NULL PRIMARY KEY CHECK (trim(preset_id) <> ''),
  family TEXT NOT NULL CHECK (family IN ('semantic_tree', 'algorithm_theater', 'comparison')),
  name_ja TEXT NOT NULL CHECK (trim(name_ja) <> ''),
  name_en TEXT NOT NULL CHECK (trim(name_en) <> ''),
  description_ja TEXT NOT NULL CHECK (trim(description_ja) <> ''),
  description_en TEXT NOT NULL CHECK (trim(description_en) <> ''),
  root_support_status TEXT NOT NULL CHECK (root_support_status IN ('supported', 'unsupported', 'unknown', 'not_applicable')),
  root_entity_type TEXT CHECK (root_entity_type IN ('problem', 'method', 'view_preset')),
  root_entity_id TEXT,
  axis TEXT NOT NULL CHECK (trim(axis) <> ''),
  relation_types_json TEXT NOT NULL CHECK (json_valid(relation_types_json) AND json_type(relation_types_json) = 'array' AND json_array_length(relation_types_json) > 0),
  max_depth INTEGER NOT NULL CHECK (max_depth >= 1),
  source_ids_json TEXT NOT NULL CHECK (json_valid(source_ids_json) AND json_type(source_ids_json) = 'array' AND json_array_length(source_ids_json) > 0),
  last_verified DATE NOT NULL, view_id TEXT NOT NULL
  CHECK (trim(view_id) <> ''), filter_policy_json TEXT NOT NULL
  CHECK (
    json_valid(filter_policy_json)
    AND json_type(filter_policy_json) = 'object'
    AND json_array_length(filter_policy_json, '$.groups') > 0
  ), limitations_ja TEXT NOT NULL
  CHECK (trim(limitations_ja) <> ''), limitations_en TEXT NOT NULL
  CHECK (trim(limitations_en) <> ''), focus_fallback_entity_types_json TEXT NOT NULL
  CHECK (
    json_valid(focus_fallback_entity_types_json)
    AND json_type(focus_fallback_entity_types_json) = 'array'
    AND json_array_length(focus_fallback_entity_types_json) > 0
  ),
  CHECK (
    (root_support_status = 'supported' AND root_entity_type IS NOT NULL AND trim(root_entity_id) <> '')
    OR
    (root_support_status <> 'supported' AND root_entity_type IS NULL AND root_entity_id IS NULL)
  )
);

CREATE INDEX atomic_predicates_subject_idx
  ON atomic_predicates (subject_type, subject_id, predicate_id);

CREATE INDEX idx_advanced_view_method_id ON advanced_view(method_id);

CREATE INDEX idx_advanced_view_problem_id ON advanced_view(problem_id);

CREATE INDEX idx_beginner_view_case_id ON beginner_view(case_id);

CREATE INDEX idx_beginner_view_first_method_id ON beginner_view(first_method_id);

CREATE INDEX idx_beginner_view_second_method_id ON beginner_view(second_method_id);

CREATE INDEX idx_case_alternative_map_alternative_id ON case_alternative_map(alternative_id);

CREATE INDEX idx_case_alternative_map_case_id ON case_alternative_map(case_id);

CREATE INDEX idx_case_feature_map_case_id ON case_feature_map(case_id);

CREATE INDEX idx_case_feature_map_feature_id ON case_feature_map(feature_id);

CREATE INDEX idx_case_feature_map_feature_value_id ON case_feature_map(feature_value_id);

CREATE INDEX idx_case_implementation_map_case_id ON case_implementation_map(case_id);

CREATE INDEX idx_case_implementation_map_implementation_id ON case_implementation_map(implementation_id);

CREATE INDEX idx_case_method_map_case_id ON case_method_map(case_id);

CREATE INDEX idx_case_method_map_fit_id ON case_method_map(fit_id);

CREATE INDEX idx_case_method_map_method_id ON case_method_map(method_id);

CREATE INDEX idx_decision_questions_mapped_feature_id ON decision_questions(mapped_feature_id);

CREATE INDEX idx_decision_rules_question_id ON decision_rules(question_id);

CREATE INDEX idx_evidence_links_source_id ON evidence_links(source_id);

CREATE INDEX idx_example_cases_avoid_method_id ON example_cases(avoid_method_id);

CREATE INDEX idx_example_cases_first_choice_method_id ON example_cases(first_choice_method_id);

CREATE INDEX idx_example_cases_problem_id ON example_cases(problem_id);

CREATE INDEX idx_example_cases_second_choice_method_id ON example_cases(second_choice_method_id);

CREATE INDEX idx_feature_values_feature_id ON feature_values(feature_id);

CREATE INDEX idx_method_hierarchy_child_method_id ON method_hierarchy(child_method_id);

CREATE INDEX idx_method_hierarchy_parent_method_id ON method_hierarchy(parent_method_id);

CREATE INDEX idx_method_implementation_map_implementation_id ON method_implementation_map(implementation_id);

CREATE INDEX idx_method_implementation_map_method_id ON method_implementation_map(method_id);

CREATE INDEX idx_methods_method_family_id ON methods(method_family_id);

CREATE INDEX idx_methods_parent_method_id ON methods(parent_method_id);

CREATE INDEX idx_problem_alternative_map_alternative_id ON problem_alternative_map(alternative_id);

CREATE INDEX idx_problem_alternative_map_problem_id ON problem_alternative_map(problem_id);

CREATE INDEX idx_problem_feature_map_feature_id ON problem_feature_map(feature_id);

CREATE INDEX idx_problem_feature_map_feature_value_id ON problem_feature_map(feature_value_id);

CREATE INDEX idx_problem_feature_map_problem_id ON problem_feature_map(problem_id);

CREATE INDEX idx_problem_method_fit_method_id ON problem_method_fit(method_id);

CREATE INDEX idx_problem_method_fit_problem_or_feature_id ON problem_method_fit(problem_or_feature_id);

CREATE INDEX predicate_policies_subject_idx
  ON predicate_policies (subject_type, subject_id, policy_id);

CREATE INDEX problem_instances_definition_idx
  ON problem_instances (problem_definition_id, problem_instance_id);

CREATE UNIQUE INDEX view_presets_view_id_unique ON view_presets(view_id);
