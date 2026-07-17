    predicate for _, predicate, _ in DEFAULT_METHOD_CLAIM_SPECS
)

# High usage means currently exposed by the published Gallery, not raw method-map fan-out.
"""
if claims.count(anchor) != 1:
    raise SystemExit('versioned_claims.py: predicate anchor changed')
claims = claims.replace(anchor, constants, 1)
claims = claims.replace(
    'HIGH_USAGE_IMPLEMENTATION_IDS = frozenset({"I_ORTOOLS_CPSAT", "I_OPTUNA", "I_CVXPY"})',
    'HIGH_USAGE_IMPLEMENTATION_IDS = frozenset('
    '{"I_ORTOOLS_CPSAT", "I_OPTUNA", "I_CVXPY", "I_SCIPY_LEAST_SQUARES_TRF"}'
    ')',
    1,
)
claims = claims.replace(
    '    _insert_historical_release_fixture(connection)\n',
    '    _insert_scipy_default_method_claims(connection, release_date=release_date)\n'
    '    _insert_historical_release_fixture(connection)\n',
    1,
)
helper_anchor = 'def _insert_historical_release_fixture(connection: sqlite3.Connection) -> None:\n'
helper = '''def _insert_scipy_default_method_claims(
    connection: sqlite3.Connection, *, release_date: str
) -> None:
    implementation = connection.execute(
        """
        SELECT last_release, last_verified, confidence
        FROM implementations
        WHERE implementation_id = 'I_SCIPY_LEAST_SQUARES_TRF'
        """
    ).fetchone()
    source = connection.execute(
        """
        SELECT publication_date, accessed_date
        FROM sources
        WHERE source_id = 'S003'
        """
    ).fetchone()
    if implementation is None or source is None:
        raise ValueError("SciPy TRF default-method claim prerequisites are missing")

    product_version = str(implementation["last_release"] or "").strip()
    if not product_version or product_version.lower() == "unknown":
        raise ValueError("SciPy TRF default-method claims require a product version")
    last_verified = str(implementation["last_verified"] or release_date)
    source_date = str(source["publication_date"] or source["accessed_date"] or last_verified)
    confidence = str(implementation["confidence"] or "unverified")

    for claim_id, predicate, value in DEFAULT_METHOD_CLAIM_SPECS:
        connection.execute(
            """
            INSERT INTO implementation_claims (
              claim_id, subject_id, predicate, value_json, value_status, valid_from,
              valid_to, replaced_by, source_id, source_date, last_verified, confidence,
              verification_status, product_version, commit_sha, release_tag
            ) VALUES (
              ?, 'I_SCIPY_LEAST_SQUARES_TRF', ?, ?, 'verified', ?, NULL, NULL,
              'S003', ?, ?, ?, 'verified', ?, NULL, NULL
            )
            """,
            (
                claim_id,
                predicate,
                _json(value),
                last_verified,
                source_date,
                last_verified,
                confidence,
                product_version,
            ),
        )


'''
if claims.count(helper_anchor) != 1:
    raise SystemExit('versioned_claims.py: helper anchor changed')
claims = claims.replace(helper_anchor, helper + helper_anchor, 1)
claims_path.write_text(claims, encoding='utf-8', newline='\n')

replace_once(
    'data/migrations/011_trust_region_reflective_defaults.sql',
    "  major_options = 'least_squares: method=trf is the default; curve_fit: trf is selected when bounds are supplied and lm otherwise; tr_solver; jac_sparsity; x_scale; loss; ftol; xtol; gtol; max_nfev',",
    "  major_options = 'tr_solver; jac_sparsity; x_scale; loss; ftol; xtol; gtol; max_nfev',",
)
replace_once(
    'data/migrations/011_trust_region_reflective_defaults.sql',
    "  notes = 'least_squares defaults to trf. curve_fit delegates bounded problems to least_squares and defaults to trf when bounds are supplied.',",
    "  notes = 'SciPy Trust Region Reflective implementation for least_squares and bounded curve_fit; API selection conditions are stored in typed versioned claims.',",
)

dataset_path = ROOT / 'src/optimization_compass/dataset_release.py'
dataset = dataset_path.read_text(encoding='utf-8')
replace_map = [
    (
        "from optimization_compass.versioned_claims import (\n"
        "    HIGH_USAGE_IMPLEMENTATION_IDS,\n"
        "    insert_versioned_claims_and_contexts,\n"
        ")",
        "from optimization_compass.versioned_claims import (\n"
        "    CLAIM_PREDICATES,\n"
        "    DEFAULT_METHOD_CLAIM_PREDICATES,\n"
        "    HIGH_USAGE_IMPLEMENTATION_IDS,\n"
        "    insert_versioned_claims_and_contexts,\n"
        ")",
    ),
    (
        'DEFAULT_TRF_DEFAULTS_MIGRATION = ROOT / "data/migrations/011_trust_region_reflective_defaults.sql"\n',
        'DEFAULT_TRF_DEFAULTS_MIGRATION = ROOT / "data/migrations/011_trust_region_reflective_defaults.sql"\n'
        'DEFAULT_TYPED_DEFAULT_CLAIMS_MIGRATION = (\n'
        '    ROOT / "data/migrations/012_typed_default_method_claims.sql"\n'
        ')\n',
    ),
    (
        '            DEFAULT_TRF_DEFAULTS_MIGRATION,\n            seed_path,',
