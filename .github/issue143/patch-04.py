        DEFAULT_METHOD_CLAIM_PREDICATES,
    ).fetchall()

    assert [row["predicate"] for row in rows] == sorted(DEFAULT_METHOD_CLAIM_PREDICATES)
    assert all(row["source_id"] == "S003" for row in rows)
    assert all(row["product_version"] for row in rows)
    assert all(row["valid_from"] == "2026-07-16" for row in rows)
    assert all(row["valid_to"] is None for row in rows)
    assert all(row["verification_status"] == "verified" for row in rows)

    values = {row["predicate"]: json.loads(row["value_json"]) for row in rows}
    least_squares = values["default_method_least_squares"]
    assert least_squares == {
        "api": "scipy.optimize.least_squares",
        "condition": "method omitted",
        "fallback": None,
        "recommendation_effect": "none",
        "selected_method": "trf",
        "selected_method_id": "M_TRUST_REGION_REFLECTIVE",
        "user_override": "method",
    }
    curve_fit = values["default_method_curve_fit_bounds"]
    assert curve_fit["api"] == "scipy.optimize.curve_fit"
    assert curve_fit["condition"] == "bounds supplied and method omitted"
    assert curve_fit["selected_method_id"] == "M_TRUST_REGION_REFLECTIVE"
    assert curve_fit["fallback"] == {
        "condition": "bounds omitted and method omitted",
        "selected_method": "lm",
        "selected_method_id": "M_LEVENBERG_MARQUARDT",
    }
    assert curve_fit["recommendation_effect"] == "none"

    generic = connection.execute(
        """
        SELECT value_json FROM implementation_claims
        WHERE subject_id = 'I_SCIPY_LEAST_SQUARES_TRF'
          AND predicate = 'important_option_defaults'
          AND valid_to IS NULL
        """
    ).fetchone()
    assert generic is not None
    generic_value = json.loads(generic["value_json"])
    assert "least_squares" not in generic_value
    assert "curve_fit" not in generic_value


def test_superseded_release_is_reproducible_as_of_date'''
if tests.count(test_anchor) != 1:
    raise SystemExit('test_versioned_claims.py: test anchor changed')
tests_path.write_text(tests.replace(test_anchor, typed_test, 1), encoding='utf-8', newline='\n')

api_tests_path = ROOT / 'tests/test_api.py'
api_tests = api_tests_path.read_text(encoding='utf-8')
api_test_anchor = '\n\ndef test_invalid_answer_returns_422() -> None:\n'
api_test = '''

def test_typed_default_method_claims_are_filterable_by_implementation_and_predicate() -> None:
    response = client.get(
        "/v1/implementations/I_SCIPY_LEAST_SQUARES_TRF/claims",
        params={"predicate": "default_method_least_squares"},
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["predicate"] == "default_method_least_squares"
    assert body[0]["source_id"] == "S003"
    assert body[0]["product_version"]
    assert body[0]["valid_to"] is None
    assert body[0]["value"]["selected_method_id"] == "M_TRUST_REGION_REFLECTIVE"
    assert body[0]["value"]["recommendation_effect"] == "none"


def test_unknown_implementation_claim_path_returns_404() -> None:
    response = client.get("/v1/implementations/I_NOT_REAL/claims")
    assert response.status_code == 404


def test_invalid_answer_returns_422() -> None:
'''
if api_tests.count(api_test_anchor) != 1:
    raise SystemExit('test_api.py: test anchor changed')
api_tests = api_tests.replace(api_test_anchor, api_test, 1)
openapi_anchor = '    assert "/v1/implementations/{implementation_id}" in paths\n'
if api_tests.count(openapi_anchor) != 1:
    raise SystemExit('test_api.py: OpenAPI anchor changed')
api_tests = api_tests.replace(
    openapi_anchor,
    openapi_anchor + '    assert "/v1/implementations/{implementation_id}/claims" in paths\n',
    1,
)
api_tests_path.write_text(api_tests, encoding='utf-8', newline='\n')

audit_path = ROOT / 'docs/default-method-audit.md'
audit = audit_path.read_text(encoding='utf-8')
old_audit = '''## TRF pilot

`I_SCIPY_LEAST_SQUARES_TRF` owns the current SciPy implementation facts. Its versioned `important_option_defaults` claim records that:

- `least_squares` selects `trf` when `method` is omitted;
- `curve_fit` selects `trf` when bounds are supplied and `lm` otherwise;
- the trust-region subsolver is selected from Jacobian representation unless overridden.

The claim describes library behavior. Applicability remains governed by the method assumptions, diagnostics, and the user's problem.
'''
new_audit = '''## TRF pilot

`I_SCIPY_LEAST_SQUARES_TRF` owns the current SciPy implementation facts. Conditional API
selection is stored in two independently queryable predicates:

- `default_method_least_squares`: `least_squares` selects `trf` when `method` is omitted;
- `default_method_curve_fit_bounds`: `curve_fit` selects `trf` when bounds are supplied and
  `method` is omitted, with unbounded `lm` recorded as the fallback condition.

Each value records `api`, `condition`, `selected_method`, canonical `selected_method_id`,
