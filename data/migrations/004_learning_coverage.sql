PRAGMA foreign_keys = ON;

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
