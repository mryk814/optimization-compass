from __future__ import annotations

import os
import sqlite3
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from importlib.resources import as_file, files
from pathlib import Path
from typing import Any


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

    def verify(self) -> dict[str, Any]:
        with self.connect() as connection:
            foreign_key_rows = connection.execute("PRAGMA foreign_key_check").fetchall()
            checks = [
                dict(row)
                for row in connection.execute(
                    "SELECT * FROM release_checks ORDER BY check_id"
                ).fetchall()
            ]
        failed = [row for row in checks if row.get("status") == "fail"]
        warned = [row for row in checks if row.get("status") == "warn"]
        return {
            "ok": not foreign_key_rows and not failed,
            "foreign_key_violations": len(foreign_key_rows),
            "failed_release_checks": len(failed),
            "warning_release_checks": len(warned),
            "total_release_checks": len(checks),
            "dataset_version": self.dataset_version(),
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
