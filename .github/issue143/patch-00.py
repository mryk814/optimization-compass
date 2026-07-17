from __future__ import annotations

import json
from pathlib import Path

ROOT = Path('.')


def replace_once(path: str, old: str, new: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding='utf-8')
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{path}: expected one replacement, found {count}: {old!r}')
    target.write_text(text.replace(old, new, 1), encoding='utf-8', newline='\n')


migration = ROOT / 'data/migrations/012_typed_default_method_claims.sql'
migration.write_text(
    """PRAGMA foreign_keys = OFF;

DROP INDEX IF EXISTS implementation_claim_active_unique;
ALTER TABLE implementation_claims RENAME TO implementation_claims_v011;

CREATE TABLE implementation_claims (
  claim_id TEXT NOT NULL PRIMARY KEY CHECK (trim(claim_id) <> ''),
  subject_id TEXT NOT NULL,
  predicate TEXT NOT NULL CHECK (predicate IN (
    'current_release', 'maintenance_status', 'license_spdx', 'platform_architecture',
    'gpu_distributed_support', 'supported_problem_classes', 'important_option_defaults',
    'default_method_least_squares', 'default_method_curve_fit_bounds'
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

INSERT INTO implementation_claims (
  claim_id, subject_id, predicate, value_json, value_status, valid_from, valid_to,
  replaced_by, source_id, source_date, last_verified, confidence,
  verification_status, product_version, commit_sha, release_tag
)
SELECT
  claim_id, subject_id, predicate, value_json, value_status, valid_from, valid_to,
  replaced_by, source_id, source_date, last_verified, confidence,
  verification_status, product_version, commit_sha, release_tag
FROM implementation_claims_v011;

DROP TABLE implementation_claims_v011;

CREATE UNIQUE INDEX implementation_claim_active_unique
  ON implementation_claims(subject_id, predicate)
  WHERE valid_to IS NULL;

PRAGMA foreign_keys = ON;
""",
    encoding='utf-8',
    newline='\n',
)

claims_path = ROOT / 'src/optimization_compass/versioned_claims.py'
claims = claims_path.read_text(encoding='utf-8')
anchor = ")\n\n# High usage means currently exposed by the published Gallery, not raw method-map fan-out.\n"
constants = """\n)

DEFAULT_METHOD_CLAIM_SPECS: tuple[tuple[str, str, dict[str, object]], ...] = (
    (
        "CLAIM_SCIPY_LEAST_SQUARES_TRF_DEFAULT_LEAST_SQUARES",
        "default_method_least_squares",
        {
            "api": "scipy.optimize.least_squares",
            "condition": "method omitted",
            "selected_method": "trf",
            "selected_method_id": "M_TRUST_REGION_REFLECTIVE",
            "fallback": None,
            "user_override": "method",
            "recommendation_effect": "none",
        },
    ),
    (
        "CLAIM_SCIPY_LEAST_SQUARES_TRF_DEFAULT_CURVE_FIT_BOUNDS",
        "default_method_curve_fit_bounds",
        {
            "api": "scipy.optimize.curve_fit",
            "condition": "bounds supplied and method omitted",
            "selected_method": "trf",
            "selected_method_id": "M_TRUST_REGION_REFLECTIVE",
            "fallback": {
                "condition": "bounds omitted and method omitted",
                "selected_method": "lm",
                "selected_method_id": "M_LEVENBERG_MARQUARDT",
            },
            "user_override": "method",
            "recommendation_effect": "none",
        },
    ),
)
DEFAULT_METHOD_CLAIM_PREDICATES: tuple[str, ...] = tuple(
