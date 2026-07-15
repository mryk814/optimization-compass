PRAGMA foreign_keys = ON;

DROP TABLE comparison_set_members;
DROP TABLE comparison_sets;
DROP TABLE demo_scenarios;
DROP TABLE demo_objectives;

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

CREATE INDEX problem_instances_definition_idx
  ON problem_instances (problem_definition_id, problem_instance_id);
