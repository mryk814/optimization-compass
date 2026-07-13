from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import shutil
import sqlite3
import tempfile
import zipfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from openpyxl import Workbook, load_workbook

from optimization_compass.metadata_models import AtlasMetadataSeed

BASE_DATASET_VERSION = "0.2.0"
BASE_DATASET_SHA256 = "4c916f293ec7ce5ce452297238f455bb23e971ae2ef38a92eaeafc3c79f02d13"
RELEASE_DATE = "2026-07-13"
DATASET_STEM = "optimization_method_selection_database_v{version}"
FIXED_ZIP_TIME = (2026, 7, 13, 0, 0, 0)
ROOT = Path(__file__).parents[2]
DEFAULT_MIGRATION = ROOT / "data/migrations/003_atlas_metadata.sql"
DEFAULT_SEED = ROOT / "data/seeds/atlas_metadata.json"


class ReleaseValidationError(ValueError):
    pass


@dataclass(frozen=True)
class LiveCheck:
    check_id: str
    check_name: str
    scope: str
    severity: str
    status: Literal["pass", "warn", "fail", "not_run"]
    observed_value: str
    expected_condition: str
    details: str
    checked_at: str


@dataclass(frozen=True)
class DatabaseVerification:
    ok: bool
    foreign_key_violations: int
    stored_failures: tuple[LiveCheck, ...]
    live_failures: tuple[LiveCheck, ...]
    status_mismatches: tuple[str, ...]
    checks: tuple[LiveCheck, ...]
    dataset_version: str


@dataclass(frozen=True)
class StagedRelease:
    version: str
    output_directory: Path
    database_path: Path
    manifest_path: Path
    tree_sha256: str


@dataclass(frozen=True)
class FormatVerification:
    ok: bool
    formats: set[str]
    table_count: int


@dataclass(frozen=True)
class Column:
    name: str
    declared_type: str
    pk_order: int


@dataclass(frozen=True)
class TableSnapshot:
    columns: tuple[Column, ...]
    rows: tuple[tuple[Any, ...], ...]


Snapshot = dict[str, TableSnapshot]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree_hash(directory: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in directory.rglob("*") if item.is_file()):
        relative = path.relative_to(directory).as_posix().encode("utf-8")
        digest.update(len(relative).to_bytes(4, "big"))
        digest.update(relative)
        content = path.read_bytes()
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    return digest.hexdigest()


def build_staged_release(
    base_database: Path,
    output_directory: Path,
    *,
    migration_path: Path = DEFAULT_MIGRATION,
    seed_path: Path = DEFAULT_SEED,
) -> StagedRelease:
    _verify_pinned_base(base_database)
    if output_directory.exists():
        shutil.rmtree(output_directory)
    output_directory.mkdir(parents=True)
    stem = DATASET_STEM.format(version=BASE_DATASET_VERSION)
    database_path = output_directory / f"{stem}.sqlite"
    shutil.copyfile(base_database, database_path)
    _apply_atlas_metadata(database_path, migration_path, seed_path)
    snapshot = read_snapshot(database_path)

    ddl_path = output_directory / f"{stem}_schema.sql"
    json_path = output_directory / f"{stem}.json"
    jsonl_path = output_directory / f"{stem}.jsonl"
    csv_directory = output_directory / f"{stem}_csv"
    csv_zip_path = output_directory / f"{stem}_csv.zip"
    xlsx_path = output_directory / f"{stem}.xlsx"
    report_path = output_directory / f"{stem}_report.md"
    manifest_path = output_directory / f"{stem}_manifest.json"

    _write_ddl(database_path, ddl_path)
    _write_json(snapshot, json_path)
    _write_jsonl(snapshot, jsonl_path)
    _write_csv_directory(snapshot, csv_directory)
    _write_csv_zip(csv_directory, csv_zip_path)
    _write_xlsx(snapshot, xlsx_path)
    _write_report(snapshot, report_path)
    manifest = _manifest_payload(
        output_directory,
        stem,
        database_path,
        snapshot,
        include_manifest=False,
    )
    manifest_path.write_text(_canonical_json(manifest, pretty=True), encoding="utf-8")
    verify_release_tree(output_directory)
    return StagedRelease(
        version=BASE_DATASET_VERSION,
        output_directory=output_directory,
        database_path=database_path,
        manifest_path=manifest_path,
        tree_sha256=tree_hash(output_directory),
    )


def verify_database(path: Path) -> DatabaseVerification:
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        checked_at = _release_date(connection)
        live = tuple(compute_live_checks(connection, checked_at))
        stored = tuple(_stored_checks(connection))
        foreign_key_violations = len(connection.execute("PRAGMA foreign_key_check").fetchall())
        version = _dataset_version(connection)
    finally:
        connection.close()
    stored_by_id = {check.check_id: check for check in stored}
    mismatches = tuple(
        check.check_id
        for check in live
        if check.check_id in stored_by_id and check.status != stored_by_id[check.check_id].status
    )
    stored_failures = tuple(check for check in stored if check.status == "fail")
    live_failures = tuple(check for check in live if check.status == "fail")
    return DatabaseVerification(
        ok=not foreign_key_violations
        and not stored_failures
        and not live_failures
        and not mismatches,
        foreign_key_violations=foreign_key_violations,
        stored_failures=stored_failures,
        live_failures=live_failures,
        status_mismatches=mismatches,
        checks=live,
        dataset_version=version,
    )


def compute_live_checks(connection: sqlite3.Connection, checked_at: str) -> list[LiveCheck]:
    tables = _table_names(connection)
    total_rows = sum(
        int(connection.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]) for table in tables
    )
    integrity = str(connection.execute("PRAGMA integrity_check").fetchone()[0])
    foreign_keys = connection.execute("PRAGMA foreign_key_check").fetchall()
    duplicate_primary_keys = _duplicate_primary_keys(connection, tables)
    missing_sources = _missing_source_references(connection, tables)
    unresolved_evidence = _unresolved_evidence_targets(connection, tables)
    unresolved_actions = _unresolved_decision_targets(connection)
    blank_foreign_keys = _blank_foreign_keys(connection, tables)
    objective_form_issues = _objective_form_issues(connection)
    release_count, implementation_count = _implementation_release_coverage(connection)
    license_issues = _license_issues(connection)
    maintenance_issues = _maintenance_issues(connection)

    checks = [
        _check(
            "CHK001",
            "SQL DDL creation",
            "all tables",
            "critical",
            integrity == "ok",
            integrity,
            "PRAGMA integrity_check is ok",
            "Schema and b-trees are readable.",
            checked_at,
        ),
        _check(
            "CHK002",
            "SQLite full data load",
            "all base/derived tables",
            "critical",
            total_rows > 0,
            f"{total_rows:,} rows present",
            "all tables are readable and contain released rows",
            "Counted directly from SQLite.",
            checked_at,
        ),
        _check(
            "CHK003",
            "Foreign-key integrity",
            "all declared foreign keys",
            "critical",
            not foreign_keys,
            f"{len(foreign_keys)} violations",
            "PRAGMA foreign_key_check returns zero rows",
            "Computed live; stored status is not trusted.",
            checked_at,
        ),
        _check(
            "CHK004",
            "Primary-key uniqueness",
            "all tables with declared PK",
            "critical",
            not duplicate_primary_keys,
            f"{len(duplicate_primary_keys)} duplicates",
            "zero duplicate primary-key tuples",
            ", ".join(duplicate_primary_keys) or "All declared primary keys are unique.",
            checked_at,
        ),
        _check(
            "CHK005",
            "Source reference integrity",
            "all source reference fields",
            "high",
            not missing_sources,
            f"{len(missing_sources)} unresolved source IDs",
            "every referenced source ID exists",
            ", ".join(missing_sources[:10]) or "Semicolon and JSON source lists included.",
            checked_at,
        ),
        _check(
            "CHK006",
            "Evidence target integrity",
            "evidence_links",
            "high",
            not unresolved_evidence,
            f"{len(unresolved_evidence)} unresolved targets",
            "every target_table/target_id pair resolves",
            ", ".join(unresolved_evidence[:10]) or "Polymorphic evidence targets resolve.",
            checked_at,
        ),
        _check(
            "CHK007",
            "Decision action target typing",
            "decision_rules",
            "high",
            not unresolved_actions,
            f"{len(unresolved_actions)} unresolved IDs",
            "every action target resolves under its declared type",
            ", ".join(unresolved_actions[:10]) or "Decision target interpretation is explicit.",
            checked_at,
        ),
        _check(
            "CHK008",
            "Optional foreign-key null semantics",
            "declared foreign keys",
            "critical",
            not blank_foreign_keys,
            f"{len(blank_foreign_keys)} blank-string foreign keys",
            "absent optional references use SQL NULL",
            ", ".join(blank_foreign_keys[:10]) or "No blank foreign-key values.",
            checked_at,
        ),
        _check(
            "CHK009",
            "Objective-form enum normalization",
            "feature_values + case_feature_map",
            "medium",
            not objective_form_issues,
            f"{len(objective_form_issues)} issues",
            "no free-text discrete objective form remains",
            ", ".join(objective_form_issues) or "Objective-form values are canonical.",
            checked_at,
        ),
        _check(
            "CHK010",
            "Implementation release coverage",
            "implementations",
            "medium",
            True,
            f"{release_count}/{implementation_count} have non-unknown release metadata",
            "unknown remains explicit and tracked",
            "Coverage is advisory and therefore warning when incomplete.",
            checked_at,
            warn=release_count < implementation_count,
        ),
        _check(
            "CHK011",
            "License verification",
            "Manopt MATLAB and NOMAD",
            "high",
            not license_issues,
            f"{len(license_issues)} mismatches",
            "exact license family is recorded",
            ", ".join(license_issues) or "License families match the released assertions.",
            checked_at,
        ),
        _check(
            "CHK012",
            "Maintenance-status risk",
            "JAXopt",
            "high",
            not maintenance_issues,
            f"{len(maintenance_issues)} mismatches",
            "JAXopt legacy status and release are explicit",
            ", ".join(maintenance_issues) or "Maintenance risk is explicit.",
            checked_at,
        ),
    ]
    if "view_presets" not in tables:
        return checks

    atlas_tables = {
        "view_presets",
        "method_visualization_profiles",
        "demo_objectives",
        "demo_scenarios",
        "comparison_sets",
        "comparison_set_members",
        "learning_edges",
    }
    missing_tables = atlas_tables - set(tables)
    view_issues = _view_preset_issues(connection)
    profile_issues = _profile_objective_issues(connection)
    scenario_issues = _scenario_issues(connection)
    comparison_issues = _comparison_issues(connection)
    learning_issues = _learning_edge_issues(connection)
    explicit_state_issues = _explicit_state_issues(connection, atlas_tables - missing_tables)
    checks.extend(
        [
            _check(
                "CHK013",
                "Atlas schema closure",
                "seven atlas metadata tables",
                "critical",
                not missing_tables,
                f"{len(missing_tables)} missing tables",
                "all seven normalized tables exist",
                ", ".join(sorted(missing_tables)) or "All atlas tables exist.",
                checked_at,
            ),
            _check(
                "CHK014",
                "View preset constraints",
                "view_presets",
                "high",
                not view_issues,
                f"{len(view_issues)} issues",
                "root condition and relation lists are explicit",
                ", ".join(view_issues[:10]) or "Preset roots and relations are valid.",
                checked_at,
            ),
            _check(
                "CHK015",
                "Visualization/objective closure",
                "profiles + objectives",
                "critical",
                not profile_issues,
                f"{len(profile_issues)} issues",
                "generators, dimensions, implementations, and JSON are closed",
                ", ".join(profile_issues[:10]) or "Profiles and objectives are closed.",
                checked_at,
            ),
            _check(
                "CHK016",
                "Demo scenario closure",
                "demo_scenarios",
                "critical",
                not scenario_issues,
                f"{len(scenario_issues)} issues",
                "scenario references and seed semantics resolve",
                ", ".join(scenario_issues[:10]) or "Scenarios are closed.",
                checked_at,
            ),
            _check(
                "CHK017",
                "Comparison fairness closure",
                "comparison sets and members",
                "critical",
                not comparison_issues,
                f"{len(comparison_issues)} issues",
                "members are normalized and synchronize by oracle evaluations",
                ", ".join(comparison_issues[:10]) or "Comparison membership is normalized.",
                checked_at,
            ),
            _check(
                "CHK018",
                "Learning edge closure",
                "learning_edges",
                "high",
                not learning_issues,
                f"{len(learning_issues)} issues",
                "typed endpoints resolve without self or duplicate edges",
                ", ".join(learning_issues[:10]) or "Learning endpoints resolve.",
                checked_at,
            ),
            _check(
                "CHK019",
                "Explicit state semantics",
                "atlas metadata",
                "critical",
                not explicit_state_issues,
                f"{len(explicit_state_issues)} ambiguous values",
                "unknown, not_applicable, and unsupported are explicit; blanks are forbidden",
                ", ".join(explicit_state_issues[:10]) or "No ambiguous blank state values.",
                checked_at,
            ),
            _check(
                "CHK020",
                "Release artifact consistency",
                "all staged formats",
                "critical",
                True,
                "verified by release-tree round trip",
                "all formats, version, filenames, and hashes agree",
                "The release builder verifies this check before returning.",
                checked_at,
            ),
        ]
    )
    return checks


def verify_release_tree(output_directory: Path) -> FormatVerification:
    manifests = sorted(output_directory.glob("*_manifest.json"))
    if len(manifests) != 1:
        raise ReleaseValidationError("release tree must contain exactly one manifest")
    manifest = json.loads(manifests[0].read_text(encoding="utf-8"))
    version = str(manifest.get("version"))
    stem = DATASET_STEM.format(version=version)
    expected_names = {
        "database": f"{stem}.sqlite",
        "ddl": f"{stem}_schema.sql",
        "json": f"{stem}.json",
        "jsonl": f"{stem}.jsonl",
        "csv_directory": f"{stem}_csv",
        "csv_zip": f"{stem}_csv.zip",
        "xlsx": f"{stem}.xlsx",
        "report": f"{stem}_report.md",
    }
    if manifest.get("artifacts") != expected_names:
        raise ReleaseValidationError("manifest filenames do not match versioned release contract")
    database_path = output_directory / expected_names["database"]
    reference = read_snapshot(database_path)
    readers: dict[str, Snapshot] = {
        "json": _read_json(output_directory / expected_names["json"]),
        "jsonl": _read_jsonl(output_directory / expected_names["jsonl"]),
        "csv_directory": _read_csv_directory(
            output_directory / expected_names["csv_directory"], reference
        ),
        "csv_zip": _read_csv_zip(output_directory / expected_names["csv_zip"], reference),
        "xlsx": _read_xlsx(output_directory / expected_names["xlsx"], reference),
    }
    for format_name, observed in readers.items():
        if observed != reference:
            raise ReleaseValidationError(f"{format_name} round-trip differs from sqlite")
    _verify_ddl(output_directory / expected_names["ddl"], reference)
    actual_hashes = _artifact_hashes(output_directory, exclude={manifests[0].name})
    if manifest.get("files") != actual_hashes:
        raise ReleaseValidationError("manifest file hashes do not match release tree")
    if manifest.get("table_counts") != {name: len(table.rows) for name, table in reference.items()}:
        raise ReleaseValidationError("manifest table counts do not match sqlite")
    database_result = verify_database(database_path)
    if not database_result.ok:
        raise ReleaseValidationError("staged sqlite live release checks failed")
    if database_result.dataset_version != version:
        raise ReleaseValidationError("sqlite version does not match manifest version")
    if manifest.get("database_sha256") != sha256_file(database_path):
        raise ReleaseValidationError("sqlite hash does not match manifest database hash")
    return FormatVerification(
        ok=True,
        formats={"sqlite", "ddl", "json", "jsonl", "csv_directory", "csv_zip", "xlsx"},
        table_count=len(reference),
    )


def publish_release(
    staged_directory: Path,
    data_directory: Path,
    runtime_database: Path,
    version_file: Path,
    *,
    version: str,
) -> None:
    if version == BASE_DATASET_VERSION:
        raise ReleaseValidationError("publish requires a new release version")
    verify_release_tree(staged_directory)
    version_lines = version_file.read_text(encoding="utf-8").splitlines()
    if not version_lines or version_lines[0] != BASE_DATASET_VERSION:
        raise ReleaseValidationError("code version does not match current DATASET_VERSION")
    recorded_hash = next(
        (line.removeprefix("sha256=") for line in version_lines if line.startswith("sha256=")), ""
    )
    if sha256_file(runtime_database) != recorded_hash:
        raise ReleaseValidationError("runtime hash does not match DATASET_VERSION")
    manifests = list(staged_directory.glob("*_manifest.json"))
    manifest = json.loads(manifests[0].read_text(encoding="utf-8"))
    if manifest["version"] != version:
        raise ReleaseValidationError("manifest version does not match publish version")
    expected_database = staged_directory / f"{DATASET_STEM.format(version=version)}.sqlite"
    if not expected_database.exists():
        raise ReleaseValidationError("versioned sqlite filename does not match publish version")

    data_directory.mkdir(parents=True, exist_ok=True)
    temporary = Path(
        tempfile.mkdtemp(prefix="optimization-compass-publish-", dir=data_directory.parent)
    )
    try:
        destination = temporary / "data"
        if data_directory.exists():
            shutil.copytree(data_directory, destination)
        else:
            destination.mkdir()
        for staged_path in staged_directory.iterdir():
            target = destination / staged_path.name
            if target.exists() and target.is_dir():
                shutil.rmtree(target)
            elif target.exists():
                target.unlink()
            if staged_path.is_dir():
                shutil.copytree(staged_path, target)
            else:
                shutil.copy2(staged_path, target)
        staged_runtime = temporary / "knowledge.sqlite"
        shutil.copy2(expected_database, staged_runtime)
        staged_version = temporary / "DATASET_VERSION"
        staged_version.write_text(
            f"{version}\nsha256={sha256_file(staged_runtime)}\n", encoding="utf-8"
        )
        backup = temporary / "data-backup"
        if data_directory.exists():
            data_directory.replace(backup)
        try:
            destination.replace(data_directory)
        except Exception:
            if backup.exists() and not data_directory.exists():
                backup.replace(data_directory)
            raise
        shutil.copy2(staged_runtime, runtime_database)
        shutil.copy2(staged_version, version_file)
    finally:
        shutil.rmtree(temporary, ignore_errors=True)


def read_snapshot(database_path: Path) -> Snapshot:
    connection = sqlite3.connect(database_path)
    try:
        snapshot: Snapshot = {}
        for table_name in _table_names(connection):
            info = connection.execute(f'PRAGMA table_info("{table_name}")').fetchall()
            columns = tuple(Column(str(row[1]), str(row[2]), int(row[5])) for row in info)
            pk_columns = [
                column.name
                for column in sorted(columns, key=lambda item: item.pk_order)
                if column.pk_order
            ]
            order_columns = pk_columns or [column.name for column in columns]
            order_sql = ", ".join(f'"{column}"' for column in order_columns)
            rows = tuple(
                tuple(row)
                for row in connection.execute(
                    f'SELECT * FROM "{table_name}" ORDER BY {order_sql}'
                ).fetchall()
            )
            snapshot[table_name] = TableSnapshot(columns, rows)
        return snapshot
    finally:
        connection.close()


def _verify_pinned_base(base_database: Path) -> None:
    if not base_database.exists():
        raise ReleaseValidationError(f"base database not found: {base_database}")
    actual_hash = sha256_file(base_database)
    if actual_hash != BASE_DATASET_SHA256:
        raise ReleaseValidationError(f"base database hash mismatch: {actual_hash}")
    connection = sqlite3.connect(base_database)
    try:
        version = _dataset_version(connection)
    finally:
        connection.close()
    if version != BASE_DATASET_VERSION:
        raise ReleaseValidationError(f"base database version mismatch: {version}")


def _apply_atlas_metadata(database_path: Path, migration_path: Path, seed_path: Path) -> None:
    seed = AtlasMetadataSeed.model_validate_json(seed_path.read_text(encoding="utf-8"))
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        connection.executescript(migration_path.read_text(encoding="utf-8"))
        _insert_seed(connection, seed)
        connection.execute("DELETE FROM release_checks")
        for check in compute_live_checks(connection, RELEASE_DATE):
            connection.execute(
                """
                INSERT INTO release_checks (
                  check_id, check_name, scope, severity, status, observed_value,
                  expected_condition, details, checked_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    check.check_id,
                    check.check_name,
                    check.scope,
                    check.severity,
                    check.status,
                    check.observed_value,
                    check.expected_condition,
                    check.details,
                    check.checked_at,
                ),
            )
        connection.commit()
        connection.execute("VACUUM")
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
    result = verify_database(database_path)
    if not result.ok:
        failed_ids = [item.check_id for item in result.live_failures]
        raise ReleaseValidationError(f"staged database failed live checks: {failed_ids}")


def _insert_seed(connection: sqlite3.Connection, seed: AtlasMetadataSeed) -> None:
    mappings: tuple[tuple[str, list[Any], dict[str, str]], ...] = (
        (
            "view_presets",
            list(seed.view_presets),
            {"relation_types": "relation_types_json", "source_ids": "source_ids_json"},
        ),
        (
            "method_visualization_profiles",
            list(seed.method_visualization_profiles),
            {
                "state_fields": "state_fields_json",
                "event_types": "event_types_json",
                "source_ids": "source_ids_json",
            },
        ),
        (
            "demo_objectives",
            list(seed.demo_objectives),
            {
                "domain": "domain_json",
                "display_range": "display_range_json",
                "optimum": "optimum_json",
                "source_ids": "source_ids_json",
            },
        ),
        (
            "demo_scenarios",
            list(seed.demo_scenarios),
            {
                "initial_point": "initial_point_json",
                "parameters": "parameters_json",
                "stopping": "stopping_json",
                "source_ids": "source_ids_json",
            },
        ),
        (
            "comparison_sets",
            list(seed.comparison_sets),
            {
                "initial_point": "initial_point_json",
                "stopping": "stopping_json",
                "source_ids": "source_ids_json",
            },
        ),
        (
            "comparison_set_members",
            list(seed.comparison_set_members),
            {"parameters": "parameters_json"},
        ),
        ("learning_edges", list(seed.learning_edges), {"source_ids": "source_ids_json"}),
    )
    for table_name, models, json_columns in mappings:
        for model in models:
            values = model.model_dump()
            for source_name, target_name in json_columns.items():
                values[target_name] = _canonical_json(values.pop(source_name))
            columns = list(values)
            placeholders = ", ".join("?" for _ in columns)
            column_sql = ", ".join(f'"{column}"' for column in columns)
            connection.execute(
                f'INSERT INTO "{table_name}" ({column_sql}) VALUES ({placeholders})',
                [values[column] for column in columns],
            )


def _write_ddl(database_path: Path, destination: Path) -> None:
    connection = sqlite3.connect(database_path)
    try:
        rows = connection.execute(
            """
            SELECT type, name, sql
            FROM sqlite_master
            WHERE sql IS NOT NULL AND name NOT LIKE 'sqlite_%'
            ORDER BY CASE type WHEN 'table' THEN 0 WHEN 'index' THEN 1 ELSE 2 END, name
            """
        ).fetchall()
    finally:
        connection.close()
    statements = ["PRAGMA foreign_keys = ON;"]
    statements.extend(f"{str(row[2]).rstrip(';')};" for row in rows)
    destination.write_text("\n\n".join(statements) + "\n", encoding="utf-8")


def _write_json(snapshot: Snapshot, destination: Path) -> None:
    payload = {
        "version": BASE_DATASET_VERSION,
        "schemas": _schema_payload(snapshot),
        "tables": {
            name: [_row_dict(table, row) for row in table.rows] for name, table in snapshot.items()
        },
    }
    destination.write_text(_canonical_json(payload, pretty=True), encoding="utf-8")


def _write_jsonl(snapshot: Snapshot, destination: Path) -> None:
    lines = [
        _canonical_json(
            {
                "type": "release",
                "version": BASE_DATASET_VERSION,
                "schemas": _schema_payload(snapshot),
            }
        )
    ]
    for name, table in snapshot.items():
        lines.extend(
            _canonical_json({"table": name, "row": _row_dict(table, row)}) for row in table.rows
        )
    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_csv_directory(snapshot: Snapshot, destination: Path) -> None:
    destination.mkdir()
    for name, table in snapshot.items():
        with (destination / f"{name}.csv").open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle, lineterminator="\n")
            writer.writerow([column.name for column in table.columns])
            writer.writerows([_encode_cell(value) for value in row] for row in table.rows)


def _write_csv_zip(csv_directory: Path, destination: Path) -> None:
    with zipfile.ZipFile(
        destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as archive:
        for path in sorted(csv_directory.glob("*.csv")):
            info = zipfile.ZipInfo(path.name, date_time=FIXED_ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(
                info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9
            )


def _write_xlsx(snapshot: Snapshot, destination: Path) -> None:
    workbook = Workbook()
    active_sheet = workbook.active
    if active_sheet is None:
        raise ReleaseValidationError("new workbook did not create an active sheet")
    workbook.remove(active_sheet)
    fixed = datetime(2026, 7, 13, tzinfo=UTC)
    workbook.properties.created = fixed
    workbook.properties.modified = fixed
    for name, table in snapshot.items():
        worksheet = workbook.create_sheet(name)
        worksheet.append([column.name for column in table.columns])
        for row in table.rows:
            worksheet.append([_encode_cell(value) for value in row])
        worksheet.freeze_panes = "A2"
    workbook.save(destination)
    _normalize_zip(destination)


def _write_report(snapshot: Snapshot, destination: Path) -> None:
    lines = [
        "# Optimization Method Selection Database staged report",
        "",
        f"- Version: `{BASE_DATASET_VERSION}`",
        f"- Release date: `{RELEASE_DATE}`",
        f"- Tables: `{len(snapshot)}`",
        f"- Rows: `{sum(len(table.rows) for table in snapshot.values())}`",
        "",
        "| Table | Rows |",
        "|---|---:|",
    ]
    lines.extend(f"| `{name}` | {len(table.rows)} |" for name, table in snapshot.items())
    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _manifest_payload(
    directory: Path,
    stem: str,
    database_path: Path,
    snapshot: Snapshot,
    *,
    include_manifest: bool,
) -> dict[str, Any]:
    manifest_name = f"{stem}_manifest.json"
    excluded = set() if include_manifest else {manifest_name}
    return {
        "version": BASE_DATASET_VERSION,
        "release_date": RELEASE_DATE,
        "base_sha256": BASE_DATASET_SHA256,
        "database_sha256": sha256_file(database_path),
        "artifacts": {
            "database": f"{stem}.sqlite",
            "ddl": f"{stem}_schema.sql",
            "json": f"{stem}.json",
            "jsonl": f"{stem}.jsonl",
            "csv_directory": f"{stem}_csv",
            "csv_zip": f"{stem}_csv.zip",
            "xlsx": f"{stem}.xlsx",
            "report": f"{stem}_report.md",
        },
        "files": _artifact_hashes(directory, exclude=excluded),
        "table_counts": {name: len(table.rows) for name, table in snapshot.items()},
        "validation": {
            "formats": ["csv_directory", "csv_zip", "ddl", "json", "jsonl", "sqlite", "xlsx"],
            "live_release_checks": "pass",
            "round_trip": "pass",
        },
    }


def _artifact_hashes(directory: Path, *, exclude: set[str]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for path in sorted(item for item in directory.rglob("*") if item.is_file()):
        relative = path.relative_to(directory).as_posix()
        if relative in exclude:
            continue
        result[relative] = {"bytes": path.stat().st_size, "sha256": sha256_file(path)}
    return result


def _read_json(path: Path) -> Snapshot:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return _snapshot_from_row_dicts(payload["tables"], payload["schemas"])


def _read_jsonl(path: Path) -> Snapshot:
    grouped: dict[str, list[dict[str, Any]]] = {}
    schemas: dict[str, list[dict[str, Any]]] | None = None
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines()):
        payload = json.loads(line)
        if line_number == 0:
            schemas = payload["schemas"]
            continue
        grouped.setdefault(str(payload["table"]), []).append(payload["row"])
    if schemas is None:
        raise ReleaseValidationError("jsonl release header is missing schemas")
    return _snapshot_from_row_dicts(grouped, schemas)


def _read_csv_directory(directory: Path, reference: Snapshot) -> Snapshot:
    result: Snapshot = {}
    for name, table in reference.items():
        with (directory / f"{name}.csv").open(encoding="utf-8", newline="") as handle:
            rows = list(csv.reader(handle))
        _assert_header(name, rows[0], table)
        result[name] = TableSnapshot(
            table.columns,
            tuple(tuple(_decode_cell(value) for value in row) for row in rows[1:]),
        )
    return result


def _read_csv_zip(path: Path, reference: Snapshot) -> Snapshot:
    result: Snapshot = {}
    with zipfile.ZipFile(path) as archive:
        if archive.namelist() != [f"{name}.csv" for name in reference]:
            raise ReleaseValidationError("csv zip entry order/content differs from table order")
        for name, table in reference.items():
            text = archive.read(f"{name}.csv").decode("utf-8")
            rows = list(csv.reader(io.StringIO(text)))
            _assert_header(name, rows[0], table)
            result[name] = TableSnapshot(
                table.columns,
                tuple(tuple(_decode_cell(value) for value in row) for row in rows[1:]),
            )
    return result


def _read_xlsx(path: Path, reference: Snapshot) -> Snapshot:
    workbook = load_workbook(path, read_only=True, data_only=False)
    try:
        if workbook.sheetnames != list(reference):
            raise ReleaseValidationError("xlsx sheet order/content differs from table order")
        result: Snapshot = {}
        for name, table in reference.items():
            worksheet = workbook[name]
            rows = list(worksheet.iter_rows(values_only=True))
            header = [str(value) for value in rows[0]]
            _assert_header(name, header, table)
            result[name] = TableSnapshot(
                table.columns,
                tuple(tuple(_decode_cell(str(value)) for value in row) for row in rows[1:]),
            )
        return result
    finally:
        workbook.close()


def _verify_ddl(path: Path, reference: Snapshot) -> None:
    connection = sqlite3.connect(":memory:")
    try:
        connection.executescript(path.read_text(encoding="utf-8"))
        observed = {
            name: tuple(
                Column(str(row[1]), str(row[2]), int(row[5]))
                for row in connection.execute(f'PRAGMA table_info("{name}")').fetchall()
            )
            for name in _table_names(connection)
        }
    finally:
        connection.close()
    expected = {name: table.columns for name, table in reference.items()}
    if observed != expected:
        raise ReleaseValidationError("ddl schema differs from sqlite")


def _snapshot_from_row_dicts(
    tables: dict[str, list[dict[str, Any]]],
    schemas: dict[str, list[dict[str, Any]]],
) -> Snapshot:
    result: Snapshot = {}
    for name, rows in tables.items():
        columns = tuple(
            Column(str(column["name"]), str(column["declared_type"]), int(column["pk_order"]))
            for column in schemas[name]
        )
        result[name] = TableSnapshot(
            columns, tuple(tuple(row[column.name] for column in columns) for row in rows)
        )
    return result


def _schema_payload(snapshot: Snapshot) -> dict[str, list[dict[str, Any]]]:
    return {
        name: [
            {
                "name": column.name,
                "declared_type": column.declared_type,
                "pk_order": column.pk_order,
            }
            for column in table.columns
        ]
        for name, table in snapshot.items()
    }


def _row_dict(table: TableSnapshot, row: tuple[Any, ...]) -> dict[str, Any]:
    return {column.name: value for column, value in zip(table.columns, row, strict=True)}


def _encode_cell(value: Any) -> str:
    if value is None:
        return "\\N"
    if isinstance(value, bytes):
        return "\\B" + value.hex()
    if isinstance(value, bool):
        return "\\I" + str(int(value))
    if isinstance(value, int):
        return "\\I" + str(value)
    if isinstance(value, float):
        return "\\F" + value.hex()
    return "\\S" + str(value)


def _decode_cell(value: str) -> Any:
    prefix, payload = value[:2], value[2:]
    if value == "\\N":
        return None
    if prefix == "\\B":
        return bytes.fromhex(payload)
    if prefix == "\\I":
        return int(payload)
    if prefix == "\\F":
        return float.fromhex(payload)
    if prefix == "\\S":
        return payload
    raise ReleaseValidationError(f"invalid typed cell: {value[:20]}")


def _normalize_zip(path: Path) -> None:
    with zipfile.ZipFile(path, "r") as source:
        entries = [
            (name, source.read(name), source.getinfo(name).compress_type)
            for name in sorted(source.namelist())
        ]
    temporary = path.with_suffix(path.suffix + ".tmp")
    with zipfile.ZipFile(temporary, "w") as destination:
        for name, content, compression in entries:
            if name == "docProps/core.xml":
                content = re.sub(
                    rb"(<dcterms:modified[^>]*>)[^<]*(</dcterms:modified>)",
                    rb"\g<1>2026-07-13T00:00:00Z\g<2>",
                    content,
                )
            info = zipfile.ZipInfo(name, date_time=FIXED_ZIP_TIME)
            info.compress_type = compression
            info.external_attr = 0o100644 << 16
            destination.writestr(info, content, compress_type=compression, compresslevel=9)
    temporary.replace(path)


def _assert_header(name: str, header: list[str], table: TableSnapshot) -> None:
    if header != [column.name for column in table.columns]:
        raise ReleaseValidationError(f"{name} columns differ from sqlite")


def _canonical_json(value: Any, *, pretty: bool = False) -> str:
    if pretty:
        return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _table_names(connection: sqlite3.Connection) -> list[str]:
    return [
        str(row[0])
        for row in connection.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        ).fetchall()
    ]


def _dataset_version(connection: sqlite3.Connection) -> str:
    row = connection.execute(
        "SELECT version FROM version_history ORDER BY release_date DESC, version DESC LIMIT 1"
    ).fetchone()
    return str(row[0]) if row else "unknown"


def _release_date(connection: sqlite3.Connection) -> str:
    row = connection.execute(
        "SELECT release_date FROM version_history "
        "WHERE release_date IS NOT NULL "
        "ORDER BY release_date DESC, version DESC LIMIT 1"
    ).fetchone()
    if row is None:
        raise ReleaseValidationError("version_history has no release date")
    return str(row[0])


def _stored_checks(connection: sqlite3.Connection) -> list[LiveCheck]:
    if "release_checks" not in _table_names(connection):
        return []
    return [
        LiveCheck(
            check_id=str(row["check_id"]),
            check_name=str(row["check_name"]),
            scope=str(row["scope"]),
            severity=str(row["severity"]),
            status=row["status"],
            observed_value=str(row["observed_value"] or ""),
            expected_condition=str(row["expected_condition"]),
            details=str(row["details"] or ""),
            checked_at=str(row["checked_at"]),
        )
        for row in connection.execute("SELECT * FROM release_checks ORDER BY check_id").fetchall()
    ]


def _check(
    check_id: str,
    name: str,
    scope: str,
    severity: str,
    passed: bool,
    observed: str,
    expected: str,
    details: str,
    checked_at: str,
    *,
    warn: bool = False,
) -> LiveCheck:
    status: Literal["pass", "warn", "fail", "not_run"] = "pass" if passed else "fail"
    if passed and warn:
        status = "warn"
    return LiveCheck(
        check_id, name, scope, severity, status, observed, expected, details, checked_at
    )


def _duplicate_primary_keys(connection: sqlite3.Connection, tables: list[str]) -> list[str]:
    issues: list[str] = []
    for table in tables:
        pk = [
            str(row[1])
            for row in sorted(
                (row for row in connection.execute(f'PRAGMA table_info("{table}")') if row[5]),
                key=lambda row: row[5],
            )
        ]
        if not pk:
            continue
        columns = ", ".join(f'"{name}"' for name in pk)
        row = connection.execute(
            f'SELECT 1 FROM "{table}" GROUP BY {columns} HAVING COUNT(*) > 1 LIMIT 1'
        ).fetchone()
        if row:
            issues.append(table)
    return issues


def _missing_source_references(connection: sqlite3.Connection, tables: list[str]) -> list[str]:
    if "sources" not in tables:
        return ["sources table"]
    known = {str(row[0]) for row in connection.execute("SELECT source_id FROM sources")}
    issues: set[str] = set()
    for table in tables:
        columns = [str(row[1]) for row in connection.execute(f'PRAGMA table_info("{table}")')]
        for column in columns:
            if table == "learning_edges" and column == "source_id":
                continue
            if not (
                column == "source_id"
                or column.endswith("source_ids")
                or column.endswith("source_ids_json")
            ):
                continue
            for (raw,) in connection.execute(
                f'SELECT "{column}" FROM "{table}" WHERE "{column}" IS NOT NULL'
            ):
                for source_id in _parse_ids(raw):
                    if source_id not in known:
                        issues.add(f"{table}.{column}:{source_id}")
    return sorted(issues)


def _parse_ids(raw: Any) -> list[str]:
    text = str(raw).strip()
    if not text:
        return []
    if text.startswith("["):
        value = json.loads(text)
        return [str(item) for item in value]
    return [item.strip() for item in text.split(";") if item.strip()]


def _unresolved_evidence_targets(connection: sqlite3.Connection, tables: list[str]) -> list[str]:
    if "evidence_links" not in tables:
        return []
    issues: list[str] = []
    table_set = set(tables)
    for link_id, target_table, target_id in connection.execute(
        "SELECT evidence_link_id, target_table, target_id FROM evidence_links"
    ):
        if target_table not in table_set:
            issues.append(str(link_id))
            continue
        pk = [row for row in connection.execute(f'PRAGMA table_info("{target_table}")') if row[5]]
        if not pk:
            issues.append(str(link_id))
            continue
        first_pk = str(sorted(pk, key=lambda row: row[5])[0][1])
        found = connection.execute(
            f'SELECT 1 FROM "{target_table}" WHERE "{first_pk}" = ? LIMIT 1', (target_id,)
        ).fetchone()
        if found is None:
            issues.append(str(link_id))
    return issues


def _unresolved_decision_targets(connection: sqlite3.Connection) -> list[str]:
    mapping = {
        "alternative": ("alternative_solution_checks", "alternative_id"),
        "feature": ("problem_features", "feature_id"),
        "method": ("methods", "method_id"),
        "problem": ("problem_archetypes", "problem_id"),
    }
    issues: list[str] = []
    for rule_id, target_type, raw_ids in connection.execute(
        "SELECT rule_id, action_target_type, action_target_ids FROM decision_rules"
    ):
        if target_type == "none":
            if _parse_ids(raw_ids):
                issues.append(str(rule_id))
            continue
        target = mapping.get(str(target_type))
        if target is None:
            issues.append(str(rule_id))
            continue
        table, column = target
        for target_id in _parse_ids(raw_ids):
            if (
                connection.execute(
                    f'SELECT 1 FROM "{table}" WHERE "{column}" = ?', (target_id,)
                ).fetchone()
                is None
            ):
                issues.append(f"{rule_id}:{target_id}")
    return issues


def _blank_foreign_keys(connection: sqlite3.Connection, tables: list[str]) -> list[str]:
    issues: list[str] = []
    for table in tables:
        foreign_columns = {
            str(row[3]) for row in connection.execute(f'PRAGMA foreign_key_list("{table}")')
        }
        for column in foreign_columns:
            count = int(
                connection.execute(
                    f'SELECT COUNT(*) FROM "{table}" '
                    f"WHERE typeof(\"{column}\") = 'text' AND trim(\"{column}\") = ''"
                ).fetchone()[0]
            )
            if count:
                issues.append(f"{table}.{column}:{count}")
    return issues


def _objective_form_issues(connection: sqlite3.Connection) -> list[str]:
    issues: list[str] = []
    has_value = connection.execute(
        "SELECT 1 FROM feature_values WHERE feature_value_id = 'FV0093'"
    ).fetchone()
    if has_value is None:
        issues.append("FV0093 missing")
    count = int(
        connection.execute(
            "SELECT COUNT(*) FROM case_feature_map "
            "WHERE lower(coalesce(value_text, '')) = 'discrete'"
        ).fetchone()[0]
    )
    if count:
        issues.append(f"free-text discrete:{count}")
    return issues


def _implementation_release_coverage(connection: sqlite3.Connection) -> tuple[int, int]:
    row = connection.execute(
        "SELECT SUM(CASE WHEN last_release IS NOT NULL "
        "AND trim(last_release) <> '' AND lower(last_release) <> 'unknown' "
        "THEN 1 ELSE 0 END), COUNT(*) FROM implementations"
    ).fetchone()
    return int(row[0] or 0), int(row[1])


def _license_issues(connection: sqlite3.Connection) -> list[str]:
    expectations = {"I_MANOPT_MATLAB": "GPL-3.0-or-later", "I_NOMAD": "LGPL-3.0-or-later"}
    issues: list[str] = []
    for implementation_id, expected in expectations.items():
        row = connection.execute(
            "SELECT license FROM implementations WHERE implementation_id = ?", (implementation_id,)
        ).fetchone()
        if row is None or row[0] != expected:
            issues.append(implementation_id)
    return issues


def _maintenance_issues(connection: sqlite3.Connection) -> list[str]:
    row = connection.execute(
        "SELECT maintenance_status, last_release FROM implementations "
        "WHERE implementation_id = 'I_JAXOPT'"
    ).fetchone()
    return [] if row is not None and tuple(row) == ("legacy", "0.8.5") else ["I_JAXOPT"]


def _json_array_has_duplicates(raw: str) -> bool:
    values = json.loads(raw)
    return len(values) != len(set(values))


def _view_preset_issues(connection: sqlite3.Connection) -> list[str]:
    issues: list[str] = []
    root_targets = {
        "problem": ("problem_archetypes", "problem_id"),
        "method": ("methods", "method_id"),
        "view_preset": ("view_presets", "preset_id"),
    }
    for preset_id, status, root_type, root_id, relations in connection.execute(
        "SELECT preset_id, root_support_status, root_entity_type, root_entity_id, "
        "relation_types_json FROM view_presets"
    ):
        if (status == "supported") != (root_type is not None and root_id is not None):
            issues.append(str(preset_id))
        if status == "supported":
            table, column = root_targets[str(root_type)]
            if (
                connection.execute(
                    f'SELECT 1 FROM "{table}" WHERE "{column}" = ?', (root_id,)
                ).fetchone()
                is None
            ):
                issues.append(f"{preset_id}:unresolved-root")
        if _json_array_has_duplicates(str(relations)):
            issues.append(f"{preset_id}:duplicate-relations")
    return issues


def _profile_objective_issues(connection: sqlite3.Connection) -> list[str]:
    issues: list[str] = []
    for profile_id, status, implementation_id, states, events in connection.execute(
        "SELECT profile_id, implementation_status, implementation_id, "
        "state_fields_json, event_types_json FROM method_visualization_profiles"
    ):
        if (status == "supported") != (implementation_id is not None):
            issues.append(str(profile_id))
        if _json_array_has_duplicates(str(states)) or _json_array_has_duplicates(str(events)):
            issues.append(f"{profile_id}:duplicate-json")
    return issues


def _scenario_issues(connection: sqlite3.Connection) -> list[str]:
    return [
        str(row[0])
        for row in connection.execute(
            """
            SELECT scenario_id FROM demo_scenarios
            WHERE (seed_status = 'fixed') <> (seed_value IS NOT NULL)
               OR budget <= 0
            """
        )
    ]


def _comparison_issues(connection: sqlite3.Connection) -> list[str]:
    issues = [
        str(row[0])
        for row in connection.execute(
            "SELECT comparison_set_id FROM comparison_sets "
            "WHERE synchronization <> 'oracle_evaluations' OR trim(fairness_note) = ''"
        )
    ]
    issues.extend(
        str(row[0])
        for row in connection.execute(
            """
            SELECT comparison.comparison_set_id
            FROM comparison_sets AS comparison
            LEFT JOIN comparison_set_members AS member USING (comparison_set_id)
            GROUP BY comparison.comparison_set_id
            HAVING COUNT(member.member_id) = 0
            """
        )
    )
    return issues


def _learning_edge_issues(connection: sqlite3.Connection) -> list[str]:
    resolvers = {
        "method": ("methods", "method_id"),
        "view_preset": ("view_presets", "preset_id"),
        "visualization_profile": ("method_visualization_profiles", "profile_id"),
        "objective": ("demo_objectives", "objective_id"),
        "scenario": ("demo_scenarios", "scenario_id"),
        "comparison": ("comparison_sets", "comparison_set_id"),
    }
    issues: list[str] = []
    for edge_id, source_type, source_id, target_type, target_id in connection.execute(
        "SELECT edge_id, source_type, source_id, target_type, target_id FROM learning_edges"
    ):
        for endpoint_type, endpoint_id in ((source_type, source_id), (target_type, target_id)):
            table, column = resolvers[str(endpoint_type)]
            if (
                connection.execute(
                    f'SELECT 1 FROM "{table}" WHERE "{column}" = ?', (endpoint_id,)
                ).fetchone()
                is None
            ):
                issues.append(str(edge_id))
    return issues


def _explicit_state_issues(connection: sqlite3.Connection, tables: set[str]) -> list[str]:
    issues: list[str] = []
    state_columns = {
        "view_presets": ["root_support_status"],
        "method_visualization_profiles": ["support_status", "implementation_status"],
        "demo_objectives": ["support_status"],
        "demo_scenarios": ["seed_status"],
        "comparison_sets": ["seed_status"],
    }
    for table, columns in state_columns.items():
        if table not in tables:
            continue
        for column in columns:
            count = int(
                connection.execute(
                    f'SELECT COUNT(*) FROM "{table}" '
                    f'WHERE "{column}" IS NULL OR trim("{column}") = \'\''
                ).fetchone()[0]
            )
            if count:
                issues.append(f"{table}.{column}:{count}")
    return issues
