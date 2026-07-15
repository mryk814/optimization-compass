PRAGMA foreign_keys = ON;

CREATE TABLE failure_mode_profiles (
  failure_mode_id TEXT NOT NULL PRIMARY KEY,
  failure_category TEXT NOT NULL CHECK (failure_category IN (
    'derivative', 'noise', 'numerical', 'constraint', 'guarantee', 'budget',
    'stopping', 'reporting', 'surrogate', 'evolutionary'
  )),
  failure_scope TEXT NOT NULL CHECK (
    failure_scope IN ('method_theory', 'implementation_specific', 'mixed')
  ),
  recoverability TEXT NOT NULL CHECK (recoverability IN ('recoverable', 'conditional', 'fatal')),
  diagnose_disposition TEXT NOT NULL CHECK (diagnose_disposition IN ('warning', 'exclude')),
  severity TEXT NOT NULL CHECK (severity IN ('critical', 'high', 'warning', 'info')),
  confidence TEXT NOT NULL CHECK (confidence IN ('high', 'medium', 'low', 'unverified')),
  source_ids_json TEXT NOT NULL CHECK (
    json_valid(source_ids_json) AND json_array_length(source_ids_json) > 0
  ),
  last_verified DATE NOT NULL,
  FOREIGN KEY (failure_mode_id) REFERENCES failure_modes(failure_mode_id)
);

CREATE TABLE failure_mode_triggers (
  trigger_id TEXT NOT NULL PRIMARY KEY,
  failure_mode_id TEXT NOT NULL,
  predicate_id TEXT,
  feature_id TEXT,
  operator TEXT NOT NULL CHECK (operator IN ('eq', 'in')),
  value_json TEXT NOT NULL CHECK (json_valid(value_json)),
  rationale TEXT NOT NULL CHECK (trim(rationale) <> ''),
  FOREIGN KEY (failure_mode_id) REFERENCES failure_mode_profiles(failure_mode_id),
  FOREIGN KEY (predicate_id) REFERENCES atomic_predicates(predicate_id),
  FOREIGN KEY (feature_id) REFERENCES problem_features(feature_id),
  CHECK ((predicate_id IS NOT NULL) <> (feature_id IS NOT NULL))
);

CREATE TABLE failure_mode_symptoms (
  symptom_id TEXT NOT NULL PRIMARY KEY,
  failure_mode_id TEXT NOT NULL,
  observable_id TEXT,
  non_visual_state TEXT,
  description TEXT NOT NULL CHECK (trim(description) <> ''),
  FOREIGN KEY (failure_mode_id) REFERENCES failure_mode_profiles(failure_mode_id),
  CHECK ((observable_id IS NOT NULL) <> (non_visual_state IS NOT NULL))
);

CREATE TABLE failure_mode_diagnostics (
  failure_mode_id TEXT NOT NULL,
  sequence INTEGER NOT NULL CHECK (sequence > 0),
  diagnostic_id TEXT NOT NULL,
  check_text TEXT NOT NULL CHECK (trim(check_text) <> ''),
  PRIMARY KEY (failure_mode_id, sequence),
  FOREIGN KEY (failure_mode_id) REFERENCES failure_mode_profiles(failure_mode_id),
  FOREIGN KEY (diagnostic_id) REFERENCES diagnostics(diagnostic_id)
);

CREATE TABLE failure_mode_mitigations (
  mitigation_id TEXT NOT NULL PRIMARY KEY,
  failure_mode_id TEXT NOT NULL,
  priority INTEGER NOT NULL CHECK (priority > 0),
  action TEXT NOT NULL CHECK (trim(action) <> ''),
  applicability TEXT NOT NULL CHECK (trim(applicability) <> ''),
  tradeoff TEXT NOT NULL CHECK (trim(tradeoff) <> ''),
  FOREIGN KEY (failure_mode_id) REFERENCES failure_mode_profiles(failure_mode_id),
  UNIQUE (failure_mode_id, priority)
);

CREATE TABLE failure_mode_affected_entities (
  failure_mode_id TEXT NOT NULL,
  entity_type TEXT NOT NULL CHECK (entity_type IN ('method', 'implementation', 'feature')),
  entity_id TEXT NOT NULL CHECK (trim(entity_id) <> ''),
  specificity TEXT NOT NULL CHECK (specificity IN ('theoretical', 'implementation_only', 'contextual')),
  PRIMARY KEY (failure_mode_id, entity_type, entity_id),
  FOREIGN KEY (failure_mode_id) REFERENCES failure_mode_profiles(failure_mode_id)
);

CREATE TABLE failure_mode_scenarios (
  failure_mode_id TEXT NOT NULL,
  scenario_id TEXT NOT NULL CHECK (trim(scenario_id) <> ''),
  relation_type TEXT NOT NULL CHECK (relation_type = 'failure_contrast'),
  PRIMARY KEY (failure_mode_id, scenario_id),
  FOREIGN KEY (failure_mode_id) REFERENCES failure_mode_profiles(failure_mode_id)
);
