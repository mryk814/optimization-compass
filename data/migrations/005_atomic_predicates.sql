PRAGMA foreign_keys = ON;

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

CREATE TABLE predicate_coverage (
  subject_type TEXT NOT NULL CHECK (subject_type IN ('method', 'implementation')),
  subject_id TEXT NOT NULL CHECK (trim(subject_id) <> ''),
  status TEXT NOT NULL CHECK (status IN ('complete', 'partial', 'not_started', 'not_applicable')),
  rationale TEXT NOT NULL CHECK (trim(rationale) <> ''),
  source_ids_json TEXT NOT NULL CHECK (json_valid(source_ids_json) AND json_type(source_ids_json) = 'array' AND json_array_length(source_ids_json) > 0),
  last_verified DATE NOT NULL,
  PRIMARY KEY (subject_type, subject_id)
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

CREATE INDEX atomic_predicates_subject_idx
  ON atomic_predicates (subject_type, subject_id, predicate_id);
CREATE INDEX predicate_policies_subject_idx
  ON predicate_policies (subject_type, subject_id, policy_id);
