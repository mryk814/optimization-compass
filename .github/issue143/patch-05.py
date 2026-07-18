`fallback`, `user_override`, and `recommendation_effect`. Source, product version, verification
date, and validity window remain typed columns on `implementation_claims`.

The seven generic predicates remain present for every implementation. These two predicates are
additive only for the SciPy TRF implementation, so the active-claim contract is
`implementation_count × 7 + 2`. The generic `important_option_defaults` claim now contains
tunable options rather than acting as the authority for conditional method selection.

The partial unique index on `(subject_id, predicate)` permits at most one active row per typed
fact. A later verification must close the old row with `valid_to`, set `replaced_by`, and mark it
`superseded` before inserting the replacement.

SQL:

```sql
SELECT predicate, value_json, source_id, product_version, valid_from, valid_to
FROM implementation_claims
WHERE subject_id = 'I_SCIPY_LEAST_SQUARES_TRF'
  AND predicate IN (
    'default_method_least_squares',
    'default_method_curve_fit_bounds'
  )
  AND valid_to IS NULL
ORDER BY predicate;
```

HTTP API:

```text
GET /v1/implementations/I_SCIPY_LEAST_SQUARES_TRF/claims
    ?predicate=default_method_least_squares
```

These claims describe versioned library behavior. They do not promote TRF in Diagnose, alter a
global score, or establish universal performance superiority.
'''
if audit.count(old_audit) != 1:
    raise SystemExit('docs/default-method-audit.md: pilot block changed')
audit_path.write_text(audit.replace(old_audit, new_audit, 1), encoding='utf-8', newline='\n')

authority_path = ROOT / 'src/optimization_compass/resources/release-authority.json'
authority = json.loads(authority_path.read_text(encoding='utf-8'))
if authority['dataset_version'] != '0.15.1':
    raise SystemExit('release authority no longer points to 0.15.1')
authority['dataset_version'] = '0.16.0'
authority['release_date'] = '2026-07-17'
authority_path.write_text(
    json.dumps(authority, ensure_ascii=False, indent=2) + '\n',
    encoding='utf-8',
    newline='\n',
)

replace_once(
    'tests/test_release_identity.py',
    '    assert authority.dataset_version == "0.15.1"',
    '    assert authority.dataset_version == "0.16.0"',
)
fixture_path = ROOT / 'tests/fixtures/recommendation_cases.json'
fixture = fixture_path.read_text(encoding='utf-8')
fixture_count = fixture.count('"dataset_version": "0.15.1"')
if fixture_count != 10:
    raise SystemExit(
        f'recommendation fixture expected ten 0.15.1 identities, found {fixture_count}'
    )
fixture_path.write_text(
    fixture.replace('"dataset_version": "0.15.1"', '"dataset_version": "0.16.0"'),
    encoding='utf-8',
    newline='\n',
)

(ROOT / 'docs/releases/0.16.0.md').write_text(
    '''# Dataset 0.16.0

- Split the SciPy `least_squares` and bounded `curve_fit` defaults into typed,
  independently queryable versioned claims.
- Added an HTTP implementation-claim endpoint with optional predicate and as-of filters.
- Preserved the seven generic implementation claims while adding two SciPy-specific defaults.
- Kept library defaults descriptive: no Diagnose promotion, score, or ranking behavior changed.
- Published source, product-version, verification-date, validity-window, and supersession
  contracts for conditional defaults.
''',
    encoding='utf-8',
    newline='\n',
)
(ROOT / 'docs/migrations/0.15.1-to-0.16.0.md').write_text(
    '''# Dataset migration 0.15.1 → 0.16.0

Dataset 0.16.0 extends the `implementation_claims.predicate` vocabulary with
`default_method_least_squares` and `default_method_curve_fit_bounds`.

Existing consumers that enumerate predicates must accept these two new values. The seven
generic predicates remain unchanged and continue to exist once per implementation. The two new
predicates are additive only for `I_SCIPY_LEAST_SQUARES_TRF`, so the active row count becomes
`implementation_count × 7 + 2`.

The new claim values expose API, condition, selected method and canonical method ID, fallback,
user override, and the explicit `recommendation_effect: none` boundary. Provenance and time
semantics continue to use the existing `source_id`, `source_date`, `product_version`,
`last_verified`, `valid_from`, `valid_to`, `replaced_by`, and `verification_status` columns.

The partial unique index still permits only one active claim for each `(subject_id, predicate)`.
Consumers should query active rows with `valid_to IS NULL`, or pass an `as_of` date to the HTTP
endpoint. Dataset 0.15.1 remains immutable and is superseded by 0.16.0.
''',
    encoding='utf-8',
    newline='\n',
)

# Rerun after aligning the product-version assertion with canonical implementation data.
