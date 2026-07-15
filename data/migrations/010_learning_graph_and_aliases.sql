PRAGMA foreign_keys = OFF;

DROP TABLE learning_edges;

CREATE TABLE learning_edges (
  edge_id TEXT NOT NULL PRIMARY KEY CHECK (trim(edge_id) <> ''),
  source_type TEXT NOT NULL CHECK (source_type IN ('method', 'problem', 'feature', 'case', 'implementation', 'scenario', 'comparison', 'view_preset')),
  source_id TEXT NOT NULL CHECK (trim(source_id) <> ''),
  target_type TEXT NOT NULL CHECK (target_type IN ('method', 'problem', 'feature', 'case', 'implementation', 'scenario', 'comparison', 'view_preset')),
  target_id TEXT NOT NULL CHECK (trim(target_id) <> ''),
  relation TEXT NOT NULL CHECK (relation IN ('prerequisite_for', 'next_step', 'contrast_with', 'special_case_of', 'generalizes', 'applied_in', 'common_misconception_for', 'see_visualization', 'see_comparison', 'see_case', 'implemented_by')),
  rationale TEXT NOT NULL CHECK (trim(rationale) <> ''),
  difficulty TEXT NOT NULL CHECK (difficulty IN ('beginner', 'intermediate', 'advanced', 'all')),
  audience TEXT NOT NULL CHECK (audience IN ('learner', 'practitioner', 'researcher', 'all')),
  display_order INTEGER NOT NULL CHECK (display_order >= 1),
  source_ids_json TEXT NOT NULL CHECK (json_valid(source_ids_json) AND json_type(source_ids_json) = 'array' AND json_array_length(source_ids_json) > 0),
  last_verified DATE NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('current', 'deprecated', 'draft')),
  UNIQUE (source_type, source_id, target_type, target_id, relation),
  CHECK (source_type <> target_type OR source_id <> target_id)
);

CREATE TABLE terminology_aliases (
  term_id TEXT NOT NULL PRIMARY KEY CHECK (trim(term_id) <> ''),
  target_type TEXT NOT NULL CHECK (target_type IN ('method', 'problem', 'feature', 'implementation')),
  target_id TEXT NOT NULL CHECK (trim(target_id) <> ''),
  label_ja TEXT NOT NULL CHECK (trim(label_ja) <> ''),
  label_en TEXT NOT NULL CHECK (trim(label_en) <> ''),
  abbreviations_json TEXT NOT NULL CHECK (json_valid(abbreviations_json) AND json_type(abbreviations_json) = 'array'),
  synonyms_json TEXT NOT NULL CHECK (json_valid(synonyms_json) AND json_type(synonyms_json) = 'array'),
  domain_terms_json TEXT NOT NULL CHECK (json_valid(domain_terms_json) AND json_type(domain_terms_json) = 'array'),
  misspellings_json TEXT NOT NULL CHECK (json_valid(misspellings_json) AND json_type(misspellings_json) = 'array'),
  deprecated_terms_json TEXT NOT NULL CHECK (json_valid(deprecated_terms_json) AND json_type(deprecated_terms_json) = 'array'),
  disambiguation_note TEXT CHECK (disambiguation_note IS NULL OR trim(disambiguation_note) <> ''),
  locale TEXT NOT NULL CHECK (trim(locale) <> ''),
  rationale TEXT NOT NULL CHECK (trim(rationale) <> ''),
  source_ids_json TEXT NOT NULL CHECK (json_valid(source_ids_json) AND json_type(source_ids_json) = 'array' AND json_array_length(source_ids_json) > 0),
  last_verified DATE NOT NULL,
  UNIQUE (target_type, target_id)
);

PRAGMA foreign_keys = ON;
