PRAGMA foreign_keys = ON;

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
  last_verified DATE NOT NULL,
  CHECK (
    (root_support_status = 'supported' AND root_entity_type IS NOT NULL AND trim(root_entity_id) <> '')
    OR
    (root_support_status <> 'supported' AND root_entity_type IS NULL AND root_entity_id IS NULL)
  )
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

CREATE TABLE demo_objectives (
  objective_id TEXT NOT NULL PRIMARY KEY CHECK (trim(objective_id) <> ''),
  name_ja TEXT NOT NULL CHECK (trim(name_ja) <> ''),
  name_en TEXT NOT NULL CHECK (trim(name_en) <> ''),
  family TEXT NOT NULL CHECK (family IN ('quadratic', 'rosenbrock')),
  support_status TEXT NOT NULL CHECK (support_status IN ('supported', 'unsupported', 'unknown', 'not_applicable')),
  dimensions INTEGER NOT NULL CHECK (dimensions >= 1),
  generator_id TEXT NOT NULL CHECK (trim(generator_id) <> ''),
  domain_json TEXT NOT NULL CHECK (json_valid(domain_json) AND json_type(domain_json) = 'object'),
  display_range_json TEXT NOT NULL CHECK (json_valid(display_range_json) AND json_type(display_range_json) = 'object'),
  display_expression TEXT NOT NULL CHECK (trim(display_expression) <> ''),
  optimum_json TEXT NOT NULL CHECK (json_valid(optimum_json) AND json_type(optimum_json) = 'object'),
  source_ids_json TEXT NOT NULL CHECK (json_valid(source_ids_json) AND json_type(source_ids_json) = 'array' AND json_array_length(source_ids_json) > 0),
  last_verified DATE NOT NULL
);

CREATE TABLE demo_scenarios (
  scenario_id TEXT NOT NULL PRIMARY KEY CHECK (trim(scenario_id) <> ''),
  method_id TEXT NOT NULL,
  profile_id TEXT NOT NULL,
  objective_id TEXT NOT NULL,
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
  FOREIGN KEY (objective_id) REFERENCES demo_objectives(objective_id),
  CHECK ((seed_status = 'fixed' AND seed_value IS NOT NULL) OR (seed_status <> 'fixed' AND seed_value IS NULL))
);

CREATE TABLE comparison_sets (
  comparison_set_id TEXT NOT NULL PRIMARY KEY CHECK (trim(comparison_set_id) <> ''),
  objective_id TEXT NOT NULL,
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
  FOREIGN KEY (objective_id) REFERENCES demo_objectives(objective_id),
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
