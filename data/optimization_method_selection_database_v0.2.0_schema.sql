-- Optimization Method Selection Database
-- Version 0.2.0; generated 2026-07-13
-- Semicolon ID lists are convenience columns; canonical many-to-many relations use bridge tables.
PRAGMA foreign_keys = ON;

-- 利用範囲、設計原則、source policy、使い方、KPI dashboard。
CREATE TABLE readme (
  section TEXT NOT NULL,
  item TEXT NOT NULL,
  value TEXT,
  notes TEXT,
  PRIMARY KEY (section, item)
);

-- 代表的な問題class/アーキタイプ。
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

-- 問題を記述する正規化feature定義。
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

-- enum featureの許容値。
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
CREATE INDEX idx_feature_values_feature_id ON feature_values(feature_id);

-- 手法family・一般algorithm・具体変種。
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
CREATE INDEX idx_methods_method_family_id ON methods(method_family_id);
CREATE INDEX idx_methods_parent_method_id ON methods(parent_method_id);

-- 手法間の階層・派生関係。
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
CREATE INDEX idx_method_hierarchy_parent_method_id ON method_hierarchy(parent_method_id);
CREATE INDEX idx_method_hierarchy_child_method_id ON method_hierarchy(child_method_id);

-- library/solver/API実装情報。
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

-- problemとfeature/valueのmany-to-many。
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
CREATE INDEX idx_problem_feature_map_problem_id ON problem_feature_map(problem_id);
CREATE INDEX idx_problem_feature_map_feature_id ON problem_feature_map(feature_id);
CREATE INDEX idx_problem_feature_map_feature_value_id ON problem_feature_map(feature_value_id);

-- 問題と手法の条件付き適合関係。
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
CREATE INDEX idx_problem_method_fit_problem_or_feature_id ON problem_method_fit(problem_or_feature_id);
CREATE INDEX idx_problem_method_fit_method_id ON problem_method_fit(method_id);

-- 手法とsoftware実装の対応。
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
CREATE INDEX idx_method_implementation_map_method_id ON method_implementation_map(method_id);
CREATE INDEX idx_method_implementation_map_implementation_id ON method_implementation_map(implementation_id);

-- 初心者向け12問の診断質問。
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
CREATE INDEX idx_decision_questions_mapped_feature_id ON decision_questions(mapped_feature_id);

-- 質問回答から候補/除外/警告を導く条件付きrule。
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
CREATE INDEX idx_decision_rules_question_id ON decision_rules(question_id);

-- 典型的な失敗patternと修復・切替。
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

-- 収束・可行性・保証・数値性の診断指標。
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

-- 28の具体的検証scenario。
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
CREATE INDEX idx_example_cases_problem_id ON example_cases(problem_id);
CREATE INDEX idx_example_cases_first_choice_method_id ON example_cases(first_choice_method_id);
CREATE INDEX idx_example_cases_second_choice_method_id ON example_cases(second_choice_method_id);
CREATE INDEX idx_example_cases_avoid_method_id ON example_cases(avoid_method_id);

-- 公式資料・原著・教科書等のprovenance。
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

-- 用語定義と混同しやすい境界。
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

-- scenario別の第一/第二候補、注意、切替条件。
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
CREATE INDEX idx_beginner_view_case_id ON beginner_view(case_id);
CREATE INDEX idx_beginner_view_first_method_id ON beginner_view(first_method_id);
CREATE INDEX idx_beginner_view_second_method_id ON beginner_view(second_method_id);

-- 問題特徴×手法×fit×実装をflat表示する専門家view。
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
CREATE INDEX idx_advanced_view_problem_id ON advanced_view(problem_id);
CREATE INDEX idx_advanced_view_method_id ON advanced_view(method_id);

-- 調査不足・追加対象・maintenance計画。
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

-- fit/status/confidence等の統制語彙。
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

-- 汎用最適化前に検討する代替解法。
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

-- problemと代替解法checkのmany-to-many。
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
CREATE INDEX idx_problem_alternative_map_problem_id ON problem_alternative_map(problem_id);
CREATE INDEX idx_problem_alternative_map_alternative_id ON problem_alternative_map(alternative_id);

-- scenarioとfeature/valueのmany-to-many。
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
CREATE INDEX idx_case_feature_map_case_id ON case_feature_map(case_id);
CREATE INDEX idx_case_feature_map_feature_id ON case_feature_map(feature_id);
CREATE INDEX idx_case_feature_map_feature_value_id ON case_feature_map(feature_value_id);

-- scenarioと第一/第二/回避手法の関係。
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
CREATE INDEX idx_case_method_map_case_id ON case_method_map(case_id);
CREATE INDEX idx_case_method_map_method_id ON case_method_map(method_id);
CREATE INDEX idx_case_method_map_fit_id ON case_method_map(fit_id);

-- scenarioと代表実装の関係。
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
CREATE INDEX idx_case_implementation_map_case_id ON case_implementation_map(case_id);
CREATE INDEX idx_case_implementation_map_implementation_id ON case_implementation_map(implementation_id);

-- scenarioと事前代替checkの関係。
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
CREATE INDEX idx_case_alternative_map_case_id ON case_alternative_map(case_id);
CREATE INDEX idx_case_alternative_map_alternative_id ON case_alternative_map(alternative_id);

-- sourceと主張対象のcanonical provenance relation。
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
CREATE INDEX idx_evidence_links_source_id ON evidence_links(source_id);

-- scenario検証で判明したmodel変更と理由。
CREATE TABLE model_revisions (
  revision_id TEXT NOT NULL PRIMARY KEY,
  trigger_case_ids TEXT,
  issue_found TEXT,
  schema_change TEXT,
  reason TEXT,
  version TEXT,
  date DATE
);

-- dataset release/version履歴。
CREATE TABLE version_history (
  version TEXT NOT NULL PRIMARY KEY,
  release_date DATE,
  status TEXT,
  summary TEXT,
  breaking_changes TEXT,
  source_policy TEXT,
  notes TEXT
);

-- 全列のdata dictionary。
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

-- 全sheet/table catalog。
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

-- Releaseごとの実行可能な品質検証結果。
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
