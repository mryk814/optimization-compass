            """
            SELECT * FROM implementation_claims
            WHERE valid_from <= ? AND (valid_to IS NULL OR valid_to >= ?)
            ORDER BY subject_id, predicate, claim_id
            """,
            (selected_date, selected_date),
        )
        for row in rows:
            row["value"] = json.loads(str(row.pop("value_json")))
        return rows
'''
new_db = '''    def implementation_claims(
        self,
        as_of: date | None = None,
        *,
        subject_id: str | None = None,
        predicate: str | None = None,
    ) -> list[dict[str, Any]]:
        selected_date = (as_of or date.today()).isoformat()
        clauses = ["valid_from <= ?", "(valid_to IS NULL OR valid_to >= ?)"]
        parameters: list[Any] = [selected_date, selected_date]
        if subject_id is not None:
            clauses.append("subject_id = ?")
            parameters.append(subject_id)
        if predicate is not None:
            clauses.append("predicate = ?")
            parameters.append(predicate)
        rows = self.fetch_all(
            "SELECT * FROM implementation_claims WHERE "
            + " AND ".join(clauses)
            + " ORDER BY subject_id, predicate, claim_id",
            parameters,
        )
        for row in rows:
            row["value"] = json.loads(str(row.pop("value_json")))
        return rows
'''
if db.count(old_db) != 1:
    raise SystemExit('db.py: implementation_claims block changed')
db_path.write_text(db.replace(old_db, new_db, 1), encoding='utf-8', newline='\n')

api_path = ROOT / 'src/optimization_compass/api.py'
api = api_path.read_text(encoding='utf-8')
if api.count('from __future__ import annotations\n\n') != 1:
    raise SystemExit('api.py: import anchor changed')
api = api.replace(
    'from __future__ import annotations\n\n',
    'from __future__ import annotations\n\nfrom datetime import date\n\n',
    1,
)
api_anchor = '''@app.get("/v1/sources/{source_id}")
def source(source_id: str) -> dict[str, object]:
'''
endpoint = '''@app.get("/v1/implementations/{implementation_id}/claims")
def implementation_claims(
    implementation_id: str,
    predicate: str | None = None,
    as_of: date | None = None,
) -> list[dict[str, object]]:
    if repository.implementation(implementation_id) is None:
        raise HTTPException(status_code=404, detail="implementation not found")
    return repository.implementation_claims(
        as_of=as_of,
        subject_id=implementation_id,
        predicate=predicate,
    )


@app.get("/v1/sources/{source_id}")
def source(source_id: str) -> dict[str, object]:
'''
if api.count(api_anchor) != 1:
    raise SystemExit('api.py: endpoint anchor changed')
api_path.write_text(api.replace(api_anchor, endpoint, 1), encoding='utf-8', newline='\n')

tests_path = ROOT / 'tests/test_versioned_claims.py'
tests = tests_path.read_text(encoding='utf-8')
for old, new in [
    (
        'from optimization_compass.versioned_claims import (\n'
        '    HIGH_USAGE_IMPLEMENTATION_IDS,\n',
        'from optimization_compass.versioned_claims import (\n'
        '    CLAIM_PREDICATES,\n'
        '    DEFAULT_METHOD_CLAIM_PREDICATES,\n'
        '    HIGH_USAGE_IMPLEMENTATION_IDS,\n',
    ),
    (
        '    assert active_claims == implementation_count * 7\n',
        '    assert active_claims == implementation_count * len(CLAIM_PREDICATES) + len(\n'
        '        DEFAULT_METHOD_CLAIM_PREDICATES\n'
        '    )\n',
    ),
    (
        '    freshness = claim_freshness_report(connection, as_of=date(2026, 7, 15))\n',
        '    freshness = claim_freshness_report(connection, as_of=date(2026, 7, 17))\n',
    ),
]:
    if tests.count(old) != 1:
        raise SystemExit(f'test_versioned_claims.py: anchor changed: {old!r}')
    tests = tests.replace(old, new, 1)

test_anchor = '\n\ndef test_superseded_release_is_reproducible_as_of_date'
typed_test = '''

def test_scipy_defaults_are_separate_typed_versioned_claims(
    connection: sqlite3.Connection,
) -> None:
    rows = connection.execute(
        """
        SELECT * FROM implementation_claims
        WHERE subject_id = 'I_SCIPY_LEAST_SQUARES_TRF'
          AND predicate IN (?, ?)
          AND valid_to IS NULL
        ORDER BY predicate
        """,
