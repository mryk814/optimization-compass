        '            DEFAULT_TRF_DEFAULTS_MIGRATION,\n'
        '            DEFAULT_TYPED_DEFAULT_CLAIMS_MIGRATION,\n'
        '            seed_path,',
    ),
    (
        '        connection.executescript(DEFAULT_TRF_DEFAULTS_MIGRATION.read_text(encoding="utf-8"))\n',
        '        connection.executescript(DEFAULT_TRF_DEFAULTS_MIGRATION.read_text(encoding="utf-8"))\n'
        '        connection.executescript(\n'
        '            DEFAULT_TYPED_DEFAULT_CLAIMS_MIGRATION.read_text(encoding="utf-8")\n'
        '        )\n',
    ),
    (
        '            "Published canonical Trust Region Reflective defaults and guidance.",',
        '            "Published typed, independently queryable SciPy default-method claims.",',
    ),
    (
        '            "A widely used SciPy default was represented only through broad adjacent methods.",',
        '            "Conditional SciPy API defaults were consolidated in one generic option claim.",',
    ),
    (
        '                "Added a canonical Trust Region Reflective method, primary source, "\n'
        '                "implementation mapping, and API-default metadata."',
        '                "Added typed least_squares and bounded curve_fit default-method predicates, "\n'
        '                "versioned claim rows, and an implementation-claim API filter."',
    ),
    (
        '                "Separate library default behavior from method recommendation priority, "\n'
        '                "and connect the dedicated guide to generated search and retrieval."',
        '                "Keep API condition, selected method, fallback, override, source, product "\n'
        '                "version, and validity independently queryable without changing ranking."',
    ),
    (
        '    expected = implementation_count * 7\n',
        '    expected = implementation_count * len(CLAIM_PREDICATES) + len(\n'
        '        DEFAULT_METHOD_CLAIM_PREDICATES\n'
        '    )\n',
    ),
]
for old, new in replace_map:
    count = dataset.count(old)
    if count != 1:
        raise SystemExit(f'dataset_release.py: expected one replacement, found {count}: {old!r}')
    dataset = dataset.replace(old, new, 1)

validation_anchor = '    issues.extend(f"active-duplicate:{row[0]}:{row[1]}" for row in duplicates)\n'
validation = '''    issues.extend(f"active-duplicate:{row[0]}:{row[1]}" for row in duplicates)
    placeholders = ",".join("?" for _ in DEFAULT_METHOD_CLAIM_PREDICATES)
    default_rows = connection.execute(
        f"""
        SELECT claim_id, predicate, value_json, source_id, product_version,
               valid_from, valid_to, verification_status
        FROM implementation_claims
        WHERE subject_id = 'I_SCIPY_LEAST_SQUARES_TRF'
          AND predicate IN ({placeholders})
          AND valid_to IS NULL
        ORDER BY predicate
        """,
        DEFAULT_METHOD_CLAIM_PREDICATES,
    ).fetchall()
    if len(default_rows) != len(DEFAULT_METHOD_CLAIM_PREDICATES):
        issues.append(
            f"typed-default-count:{len(default_rows)}/"
            f"{len(DEFAULT_METHOD_CLAIM_PREDICATES)}"
        )
    required_fields = {
        "api",
        "condition",
        "selected_method",
        "selected_method_id",
        "fallback",
        "user_override",
        "recommendation_effect",
    }
    for row in default_rows:
        claim_id = str(row["claim_id"])
        try:
            value = json.loads(str(row["value_json"]))
        except json.JSONDecodeError:
            issues.append(f"typed-default-json:{claim_id}")
            continue
        if not isinstance(value, dict) or not required_fields <= set(value):
            issues.append(f"typed-default-contract:{claim_id}")
            continue
        if (
            value["selected_method_id"] != "M_TRUST_REGION_REFLECTIVE"
            or value["user_override"] != "method"
            or value["recommendation_effect"] != "none"
        ):
            issues.append(f"typed-default-semantics:{claim_id}")
        if row["predicate"] == "default_method_least_squares":
            if value["fallback"] is not None:
                issues.append(f"typed-default-fallback:{claim_id}")
        elif not isinstance(value["fallback"], dict) or value["fallback"].get(
            "selected_method_id"
        ) != "M_LEVENBERG_MARQUARDT":
            issues.append(f"typed-default-fallback:{claim_id}")
        if (
            row["source_id"] != "S003"
            or not str(row["product_version"] or "").strip()
            or not str(row["valid_from"] or "").strip()
            or row["valid_to"] is not None
            or row["verification_status"] != "verified"
        ):
            issues.append(f"typed-default-provenance:{claim_id}")
'''
if dataset.count(validation_anchor) != 1:
    raise SystemExit('dataset_release.py: validation anchor changed')
dataset = dataset.replace(validation_anchor, validation, 1)
dataset_path.write_text(dataset, encoding='utf-8', newline='\n')

db_path = ROOT / 'src/optimization_compass/db.py'
db = db_path.read_text(encoding='utf-8')
old_db = '''    def implementation_claims(self, as_of: date | None = None) -> list[dict[str, Any]]:
        selected_date = (as_of or date.today()).isoformat()
        rows = self.fetch_all(
