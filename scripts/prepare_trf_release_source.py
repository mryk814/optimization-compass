from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label} did not match exactly once: {count}")
    return text.replace(old, new, 1)


release_path = Path("src/optimization_compass/dataset_release.py")
text = release_path.read_text(encoding="utf-8")
text = replace_once(
    text,
    'DEFAULT_LEARNING_GRAPH_MIGRATION = ROOT / "data/migrations/010_learning_graph_and_aliases.sql"\n',
    'DEFAULT_LEARNING_GRAPH_MIGRATION = ROOT / "data/migrations/010_learning_graph_and_aliases.sql"\n'
    'DEFAULT_TRF_MIGRATION = ROOT / "data/migrations/011_trust_region_reflective.sql"\n'
    'DEFAULT_DEFAULT_CLAIMS_MIGRATION = ROOT / "data/migrations/012_default_method_claims.sql"\n',
    "migration constants",
)
text = replace_once(
    text,
    "            DEFAULT_FAILURE_MODE_MIGRATION,\n            seed_path,\n",
    "            DEFAULT_FAILURE_MODE_MIGRATION,\n"
    "            DEFAULT_LEARNING_GRAPH_MIGRATION,\n"
    "            DEFAULT_TRF_MIGRATION,\n"
    "            DEFAULT_DEFAULT_CLAIMS_MIGRATION,\n"
    "            seed_path,\n",
    "protected migrations",
)
text = replace_once(
    text,
    '        connection.executescript(DEFAULT_LEARNING_GRAPH_MIGRATION.read_text(encoding="utf-8"))\n'
    "        _insert_problem_seed(connection, problem_seed)\n",
    '        connection.executescript(DEFAULT_LEARNING_GRAPH_MIGRATION.read_text(encoding="utf-8"))\n'
    '        connection.executescript(DEFAULT_TRF_MIGRATION.read_text(encoding="utf-8"))\n'
    '        connection.executescript(DEFAULT_DEFAULT_CLAIMS_MIGRATION.read_text(encoding="utf-8"))\n'
    "        _insert_problem_seed(connection, problem_seed)\n",
    "migration execution",
)
text = replace_once(
    text,
    "    expected = implementation_count * 7\n",
    "    expected = implementation_count * 7 + 2\n",
    "active claim expectation",
)
text = replace_once(
    text,
    '            "Published constrained-continuous and multi-objective learning slices.",\n',
    '            "Added canonical Trust Region Reflective guidance and SciPy default-method claims.",\n',
    "release summary",
)
text = replace_once(
    text,
    '            "Constrained and multi-objective concepts lacked canonical executable visuals.",\n',
    '            "A common implicit SciPy least-squares default lacked a canonical method identity.",\n',
    "revision issue",
)
text = replace_once(
    text,
    '                "Added renderer-family contracts for feasible regions and Pareto fronts, "\n'
    '                "with canonical scenarios, references, and failure contrast."\n',
    '                "Added M_TRUST_REGION_REFLECTIVE, its primary source, hierarchy, aliases, "\n'
    '                "implementation mapping, and typed versioned default claims."\n',
    "revision schema",
)
text = replace_once(
    text,
    '                "Connect canonical problems to artifacts, routes, content, Gallery, "\n'
    '                "Map, and sources."\n',
    '                "Make an implicit default inspectable and distinct from Gauss-Newton, "\n'
    '                "Levenberg-Marquardt, and generic trust-region methods."\n',
    "revision reason",
)
release_path.write_text(text, encoding="utf-8")

claims_path = Path("src/optimization_compass/versioned_claims.py")
claims_text = claims_path.read_text(encoding="utf-8")
claims_text = replace_once(
    claims_text,
    '            "CLAIM_SCIPY_LEAST_SQUARES_TRF_DEFAULT_LEAST_SQUARES",\n            {\n',
    '            "CLAIM_SCIPY_LEAST_SQUARES_TRF_DEFAULT_LEAST_SQUARES",\n'
    '            "default_method_least_squares",\n'
    "            {\n",
    "least_squares predicate",
)
claims_text = replace_once(
    claims_text,
    '            "CLAIM_SCIPY_LEAST_SQUARES_TRF_DEFAULT_CURVE_FIT_BOUNDS",\n            {\n',
    '            "CLAIM_SCIPY_LEAST_SQUARES_TRF_DEFAULT_CURVE_FIT_BOUNDS",\n'
    '            "default_method_curve_fit_bounds",\n'
    "            {\n",
    "curve_fit predicate",
)
claims_text = replace_once(
    claims_text,
    "    for claim_id, value in claims:\n",
    "    for claim_id, predicate, value in claims:\n",
    "claim tuple unpacking",
)
claims_text = replace_once(
    claims_text,
    "              ?, 'I_SCIPY_LEAST_SQUARES_TRF', 'important_option_defaults', ?, 'verified', ?,\n",
    "              ?, 'I_SCIPY_LEAST_SQUARES_TRF', ?, ?, 'verified', ?,\n",
    "claim predicate placeholder",
)
claims_text = replace_once(
    claims_text,
    "                claim_id,\n                _json(value),\n",
    "                claim_id,\n                predicate,\n                _json(value),\n",
    "claim predicate parameter",
)
claims_path.write_text(claims_text, encoding="utf-8")

test_path = Path("tests/test_versioned_claims.py")
test_text = test_path.read_text(encoding="utf-8")
test_text = replace_once(
    test_text,
    "          AND predicate = 'important_option_defaults'\n          AND claim_id LIKE '%DEFAULT_%'\n",
    "          AND predicate LIKE 'default_method_%'\n          AND claim_id LIKE '%DEFAULT_%'\n",
    "default claim test query",
)
test_path.write_text(test_text, encoding="utf-8")

docs = Path("docs/method-content-density.md")
docs_text = docs.read_text(encoding="utf-8")
marker = "## Audit report\n"
section = """## Default-method pilot

Issue #111 adds Trust Region Reflective as the 99th canonical method and the 67th published method guide. The guide is prioritized because SciPy selects TRF implicitly in common least-squares calls, not because a library default is a universal recommendation.

The pilot also establishes a versioned default-method audit in [`library-defaults.md`](library-defaults.md). It records the API, selection condition, override, fallback, version, and source separately from problem-level recommendation data.

"""
docs_text = replace_once(docs_text, marker, section + marker, "density section")
docs_text = replace_once(
    docs_text,
    "After the second beginner method tranche, all 66 published method guides must meet the Level 2 floor. This does not imply that all 98 registered methods have full guides;",
    "After the TRF pilot, all 67 published method guides must meet the Level 2 floor. This does not imply that all 99 registered methods have full guides;",
    "density floor",
)
docs.write_text(docs_text, encoding="utf-8")
