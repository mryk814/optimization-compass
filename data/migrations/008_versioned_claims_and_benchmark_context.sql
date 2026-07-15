PRAGMA foreign_keys = ON;

CREATE TABLE implementation_claims (
  claim_id TEXT NOT NULL PRIMARY KEY CHECK (trim(claim_id) <> ''),
  subject_id TEXT NOT NULL,
  predicate TEXT NOT NULL CHECK (predicate IN (
    'current_release', 'maintenance_status', 'license_spdx', 'platform_architecture',
    'gpu_distributed_support', 'supported_problem_classes', 'important_option_defaults'
  )),
  value_json TEXT NOT NULL CHECK (json_valid(value_json)),
  value_status TEXT NOT NULL CHECK (value_status IN ('verified', 'explicit_unknown')),
  valid_from DATE NOT NULL,
  valid_to DATE,
  replaced_by TEXT,
  source_id TEXT NOT NULL,
  source_date DATE NOT NULL,
  last_verified DATE NOT NULL,
  confidence TEXT NOT NULL CHECK (confidence IN ('high', 'medium', 'low', 'unverified')),
  verification_status TEXT NOT NULL CHECK (
    verification_status IN ('verified', 'source_pending', 'superseded')
  ),
  product_version TEXT,
  commit_sha TEXT,
  release_tag TEXT,
  FOREIGN KEY (subject_id) REFERENCES implementations(implementation_id),
  FOREIGN KEY (source_id) REFERENCES sources(source_id),
  FOREIGN KEY (replaced_by) REFERENCES implementation_claims(claim_id),
  CHECK (valid_to IS NULL OR valid_to >= valid_from),
  CHECK ((value_status = 'explicit_unknown') = (verification_status = 'source_pending'))
);

CREATE UNIQUE INDEX implementation_claim_active_unique
  ON implementation_claims(subject_id, predicate)
  WHERE valid_to IS NULL;

CREATE TABLE benchmark_contexts (
  context_id TEXT NOT NULL PRIMARY KEY CHECK (trim(context_id) <> ''),
  context_version TEXT NOT NULL CHECK (trim(context_version) <> ''),
  category TEXT NOT NULL CHECK (category IN ('LP', 'QP', 'NLP', 'MIP', 'DFO', 'BO')),
  problem_instance_id TEXT NOT NULL,
  problem_variant TEXT NOT NULL CHECK (trim(problem_variant) <> ''),
  dimension INTEGER NOT NULL CHECK (dimension > 0),
  sparsity_json TEXT NOT NULL CHECK (json_valid(sparsity_json)),
  hardware_json TEXT NOT NULL CHECK (json_valid(hardware_json)),
  runtime_json TEXT NOT NULL CHECK (json_valid(runtime_json)),
  oracle_budget_json TEXT NOT NULL CHECK (json_valid(oracle_budget_json)),
  evaluation_budget INTEGER NOT NULL CHECK (evaluation_budget > 0),
  time_budget_seconds REAL CHECK (time_budget_seconds IS NULL OR time_budget_seconds > 0),
  tolerance_json TEXT NOT NULL CHECK (json_valid(tolerance_json)),
  stopping_json TEXT NOT NULL CHECK (json_valid(stopping_json)),
  initialization_json TEXT NOT NULL CHECK (json_valid(initialization_json)),
  seed_status TEXT NOT NULL CHECK (seed_status IN ('fixed', 'not_applicable')),
  seed_value INTEGER,
  tuning_policy TEXT NOT NULL CHECK (trim(tuning_policy) <> ''),
  implementation_versions_json TEXT NOT NULL CHECK (json_valid(implementation_versions_json)),
  outcome_metrics_json TEXT NOT NULL CHECK (json_valid(outcome_metrics_json)),
  status_mapping_json TEXT NOT NULL CHECK (json_valid(status_mapping_json)),
  source_ids_json TEXT NOT NULL CHECK (
    json_valid(source_ids_json) AND json_array_length(source_ids_json) > 0
  ),
  last_verified DATE NOT NULL,
  FOREIGN KEY (problem_instance_id) REFERENCES problem_instances(problem_instance_id),
  CHECK ((seed_status = 'fixed' AND seed_value IS NOT NULL)
      OR (seed_status = 'not_applicable' AND seed_value IS NULL))
);

ALTER TABLE comparison_sets ADD COLUMN benchmark_context_id TEXT
  REFERENCES benchmark_contexts(context_id);
