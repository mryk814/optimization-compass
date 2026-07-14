from __future__ import annotations

import hashlib
import os
import sqlite3
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from importlib.resources import as_file, files
from pathlib import Path
from typing import Any

from optimization_compass.dataset_release import verify_database


def split_ids(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(";") if item.strip()]


class KnowledgeRepository:
    def __init__(self, database_path: str | Path | None = None) -> None:
        env_path = os.getenv("OPTIMIZATION_COMPASS_DB")
        selected_path = database_path if database_path is not None else env_path
        self._explicit_path = Path(selected_path) if selected_path is not None else None

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        if self._explicit_path is not None:
            with self._connect_path(self._explicit_path) as connection:
                yield connection
            return

        resource = files("optimization_compass").joinpath("resources/knowledge.sqlite")
        with as_file(resource) as database_path, self._connect_path(database_path) as connection:
            yield connection

    @contextmanager
    def _connect_path(self, database_path: Path) -> Iterator[sqlite3.Connection]:
        if not database_path.exists():
            raise FileNotFoundError(f"knowledge database not found: {database_path}")
        uri = f"file:{database_path.resolve()}?mode=ro"
        connection = sqlite3.connect(uri, uri=True, check_same_thread=False)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            yield connection
        finally:
            connection.close()

    def fetch_all(self, sql: str, parameters: Sequence[Any] = ()) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute(sql, parameters).fetchall()
        return [dict(row) for row in rows]

    def fetch_one(self, sql: str, parameters: Sequence[Any] = ()) -> dict[str, Any] | None:
        with self.connect() as connection:
            row = connection.execute(sql, parameters).fetchone()
        return dict(row) if row else None

    def questions(self, language: str = "ja") -> list[dict[str, Any]]:
        question_column = "question_ja" if language == "ja" else "question_en"
        rows = self.fetch_all(
            f"""
            SELECT question_id, sequence, {question_column} AS question,
                   beginner_wording, answer_type, allowed_answers,
                   why_asked, required, confidence
            FROM decision_questions
            ORDER BY sequence
            """
        )
        for row in rows:
            row["allowed_answers"] = split_ids(row["allowed_answers"])
            row["required"] = str(row["required"]).lower() == "yes"
        return rows

    def rules(self) -> list[dict[str, Any]]:
        return self.fetch_all("SELECT * FROM decision_rules ORDER BY rule_id")

    def methods(self, method_ids: list[str]) -> dict[str, dict[str, Any]]:
        return self._fetch_by_ids("methods", "method_id", method_ids)

    def alternatives(self, alternative_ids: list[str]) -> dict[str, dict[str, Any]]:
        return self._fetch_by_ids("alternative_solution_checks", "alternative_id", alternative_ids)

    def problems(self, problem_ids: list[str]) -> dict[str, dict[str, Any]]:
        return self._fetch_by_ids("problem_archetypes", "problem_id", problem_ids)

    def method_implementations(
        self, method_ids: list[str], limit_per_method: int
    ) -> dict[str, list[dict[str, Any]]]:
        if not method_ids or limit_per_method <= 0:
            return {}
        placeholders = ",".join("?" for _ in method_ids)
        rows = self.fetch_all(
            f"""
            SELECT mim.method_id, mim.support_level, mim.implementation_notes,
                   i.implementation_id, i.library_name, i.solver_name, i.language,
                   i.license, i.maintenance_status, i.last_release,
                   i.official_docs_url, i.official_repo_url, i.notes
            FROM method_implementation_map AS mim
            JOIN implementations AS i USING (implementation_id)
            WHERE mim.method_id IN ({placeholders})
            ORDER BY
              CASE mim.support_level WHEN 'native' THEN 0 ELSE 1 END,
              CASE i.maintenance_status
                WHEN 'active' THEN 0
                WHEN 'maintained' THEN 0
                WHEN 'legacy' THEN 3
                ELSE 1
              END,
              i.implementation_id
            """,
            method_ids,
        )
        grouped: dict[str, list[dict[str, Any]]] = {}
        for row in rows:
            items = grouped.setdefault(str(row["method_id"]), [])
            if len(items) < limit_per_method:
                items.append(row)
        return grouped

    def source(self, source_id: str) -> dict[str, Any] | None:
        return self.fetch_one("SELECT * FROM sources WHERE source_id = ?", (source_id,))

    def implementation(self, implementation_id: str) -> dict[str, Any] | None:
        return self.fetch_one(
            "SELECT * FROM implementations WHERE implementation_id = ?", (implementation_id,)
        )

    def method(self, method_id: str) -> dict[str, Any] | None:
        return self.fetch_one("SELECT * FROM methods WHERE method_id = ?", (method_id,))

    def dataset_version(self) -> str:
        row = self.fetch_one(
            "SELECT version FROM version_history ORDER BY release_date DESC, version DESC LIMIT 1"
        )
        return str(row["version"]) if row else "unknown"

    def database_sha256(self) -> str:
        if self._explicit_path is not None:
            return hashlib.sha256(self._explicit_path.read_bytes()).hexdigest()
        resource = files("optimization_compass").joinpath("resources/knowledge.sqlite")
        with as_file(resource) as database_path:
            return hashlib.sha256(database_path.read_bytes()).hexdigest()

    def latest_release(self) -> dict[str, str]:
        row = self.fetch_one(
            """
            SELECT version, release_date
            FROM version_history
            WHERE release_date IS NOT NULL
            ORDER BY release_date DESC, version DESC
            LIMIT 1
            """
        )
        if row is None:
            raise ValueError("version_history has no dated release")
        return {"version": str(row["version"]), "release_date": str(row["release_date"])}

    def atlas_questions(self) -> list[dict[str, Any]]:
        rows = self.fetch_all(
            """
            SELECT question_id, sequence, question_ja, question_en, answer_type,
                   allowed_answers, mapped_feature_id, why_asked, source_ids
            FROM decision_questions
            ORDER BY sequence, question_id
            """
        )
        for row in rows:
            row["allowed_answers"] = split_ids(row["allowed_answers"])
            row["source_ids"] = split_ids(row["source_ids"])
        return rows

    def atlas_rules(self) -> list[dict[str, Any]]:
        rows = self.fetch_all(
            """
            SELECT rule_id, question_id, answer_condition, action_target_type,
                   action_target_ids, explanation, source_ids
            FROM decision_rules
            ORDER BY rule_id
            """
        )
        for row in rows:
            row["action_target_ids"] = split_ids(row["action_target_ids"])
            row["source_ids"] = split_ids(row["source_ids"])
        return rows

    def atlas_feature_values(self, feature_ids: list[str]) -> list[dict[str, Any]]:
        if not feature_ids:
            return []
        placeholders = ",".join("?" for _ in feature_ids)
        return self.fetch_all(
            f"""
            SELECT feature_id, value_code, label_ja, label_en, sort_order
            FROM feature_values
            WHERE feature_id IN ({placeholders})
            ORDER BY feature_id, sort_order, value_code
            """,
            feature_ids,
        )

    def atlas_features(self, feature_ids: list[str]) -> list[dict[str, Any]]:
        if not feature_ids:
            return []
        placeholders = ",".join("?" for _ in feature_ids)
        rows = self.fetch_all(
            f"""
            SELECT feature_id, name_ja, name_en, definition, source_ids
            FROM problem_features
            WHERE feature_id IN ({placeholders})
            ORDER BY feature_id
            """,
            feature_ids,
        )
        for row in rows:
            row["source_ids"] = split_ids(row["source_ids"])
        return rows

    def atlas_methods(self, method_ids: list[str]) -> list[dict[str, Any]]:
        if not method_ids:
            return []
        placeholders = ",".join("?" for _ in method_ids)
        rows = self.fetch_all(
            f"""
            SELECT method_id, name_ja, name_en, summary, variable_types,
                   solution_scope, optimality_certificate, exactness,
                   reference_source_ids AS source_ids
            FROM methods
            WHERE method_id IN ({placeholders})
            ORDER BY method_id
            """,
            method_ids,
        )
        for row in rows:
            row["source_ids"] = split_ids(row["source_ids"])
        return rows

    def atlas_problems(self, problem_ids: list[str]) -> list[dict[str, Any]]:
        if not problem_ids:
            return []
        placeholders = ",".join("?" for _ in problem_ids)
        rows = self.fetch_all(
            f"""
            SELECT problem_id, name_ja, name_en, summary, source_ids
            FROM problem_archetypes
            WHERE problem_id IN ({placeholders})
            ORDER BY problem_id
            """,
            problem_ids,
        )
        for row in rows:
            row["source_ids"] = split_ids(row["source_ids"])
        return rows

    def atlas_alternatives(self) -> list[dict[str, Any]]:
        rows = self.fetch_all(
            """
            SELECT alternative_id, name_ja, name_en,
                   why_before_generic_optimization, preferred_approach,
                   false_positive_warning, source_ids
            FROM alternative_solution_checks
            ORDER BY alternative_id
            """
        )
        for row in rows:
            row["source_ids"] = split_ids(row["source_ids"])
        return rows

    def atlas_sources(self, source_ids: list[str]) -> list[dict[str, Any]]:
        if not source_ids:
            return []
        unique_ids = sorted(set(source_ids))
        placeholders = ",".join("?" for _ in unique_ids)
        return self.fetch_all(
            f"""
            SELECT source_id, title, supported_claim, url
            FROM sources
            WHERE source_id IN ({placeholders})
            ORDER BY source_id
            """,
            unique_ids,
        )

    def recommendation_questions(self) -> list[dict[str, Any]]:
        rows = self.fetch_all(
            """
            SELECT question_id, sequence, question_ja, question_en, beginner_wording,
                   answer_type, allowed_answers, mapped_feature_id, why_asked,
                   required, confidence, source_ids
            FROM decision_questions
            ORDER BY sequence, question_id
            """
        )
        for row in rows:
            row["allowed_answers"] = split_ids(row["allowed_answers"])
            row["source_ids"] = split_ids(row["source_ids"])
            row["required"] = str(row["required"]).lower() == "yes"
        return rows

    def recommendation_rules(self) -> list[dict[str, Any]]:
        rows = self.fetch_all(
            """
            SELECT rule_id, question_id, answer_condition, action_type,
                   action_target_type, action_target_ids, priority_effect,
                   explanation, warnings, source_ids
            FROM decision_rules
            ORDER BY rule_id
            """
        )
        for row in rows:
            row["action_target_ids"] = split_ids(row["action_target_ids"])
            row["source_ids"] = split_ids(row["source_ids"])
        return rows

    def recommendation_implementations(
        self, method_ids: list[str]
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        if not method_ids:
            return [], []
        placeholders = ",".join("?" for _ in method_ids)
        mappings = self.fetch_all(
            f"""
            SELECT method_id, implementation_id, support_level, implementation_notes
            FROM method_implementation_map
            WHERE method_id IN ({placeholders})
            ORDER BY method_id,
              CASE support_level WHEN 'native' THEN 0 ELSE 1 END,
              implementation_id
            """,
            method_ids,
        )
        implementation_ids = sorted({str(mapping["implementation_id"]) for mapping in mappings})
        if not implementation_ids:
            return [], mappings
        implementation_placeholders = ",".join("?" for _ in implementation_ids)
        implementations = self.fetch_all(
            f"""
            SELECT implementation_id, library_name, solver_name, language, license,
                   maintenance_status, last_release, official_docs_url,
                   official_repo_url, notes
            FROM implementations
            WHERE implementation_id IN ({implementation_placeholders})
            ORDER BY implementation_id
            """,
            implementation_ids,
        )
        return implementations, mappings

    def verify(self) -> dict[str, Any]:
        if self._explicit_path is not None:
            result = verify_database(self._explicit_path)
        else:
            resource = files("optimization_compass").joinpath("resources/knowledge.sqlite")
            with as_file(resource) as database_path:
                result = verify_database(database_path)
        checks = [
            {
                "check_id": check.check_id,
                "check_name": check.check_name,
                "scope": check.scope,
                "severity": check.severity,
                "status": check.status,
                "observed_value": check.observed_value,
                "expected_condition": check.expected_condition,
                "details": check.details,
                "checked_at": check.checked_at,
            }
            for check in result.checks
        ]
        failed = [check for check in result.checks if check.status == "fail"]
        warned = [check for check in result.checks if check.status == "warn"]
        return {
            "ok": result.ok,
            "foreign_key_violations": result.foreign_key_violations,
            "failed_release_checks": len(failed),
            "warning_release_checks": len(warned),
            "total_release_checks": len(checks),
            "dataset_version": result.dataset_version,
            "stored_status_mismatches": list(result.status_mismatches),
            "details": checks,
        }

    def _fetch_by_ids(
        self, table: str, id_column: str, ids: list[str]
    ) -> dict[str, dict[str, Any]]:
        if not ids:
            return {}
        unique_ids = list(dict.fromkeys(ids))
        placeholders = ",".join("?" for _ in unique_ids)
        rows = self.fetch_all(
            f"SELECT * FROM {table} WHERE {id_column} IN ({placeholders})", unique_ids
        )
        return {str(row[id_column]): row for row in rows}
