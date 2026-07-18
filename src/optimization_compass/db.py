from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from datetime import date
from importlib.resources import as_file, files
from pathlib import Path
from typing import Any

from optimization_compass.dataset_release import verify_database
from optimization_compass.failure_modes import (
    FailureGuidance,
    export_failure_modes,
    failure_guidance,
)
from optimization_compass.metadata_models import ViewPresetSeed
from optimization_compass.predicates import (
    PredicateCatalog,
    PredicateContractError,
    PredicateFact,
    SubjectKey,
    evaluate_eligibility,
)
from optimization_compass.problem_instances import (
    ProblemCatalog,
    ProblemDefinition,
    ProblemInstance,
)
from optimization_compass.problem_registry import get_runtime_problem, load_problem_suite
from optimization_compass.versioned_claims import claim_freshness_report, comparison_eligibility


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
        rows = self.fetch_all("SELECT * FROM decision_rules ORDER BY rule_id")
        return self._without_retired_rule_targets(rows, normalized=False)

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

    def implementation_claims(
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

    def implementation_claim_history(self) -> list[dict[str, Any]]:
        rows = self.fetch_all(
            "SELECT * FROM implementation_claims "
            "ORDER BY subject_id, predicate, valid_from, claim_id"
        )
        for row in rows:
            row["value"] = json.loads(str(row.pop("value_json")))
        return rows

    def implementation_claim_freshness(self, as_of: date) -> dict[str, Any]:
        with self.connect() as connection:
            return claim_freshness_report(connection, as_of=as_of)

    def benchmark_contexts(self) -> list[dict[str, Any]]:
        rows = self.fetch_all("SELECT * FROM benchmark_contexts ORDER BY category, context_id")
        json_columns = (
            "sparsity_json",
            "hardware_json",
            "runtime_json",
            "oracle_budget_json",
            "tolerance_json",
            "stopping_json",
            "initialization_json",
            "implementation_versions_json",
            "outcome_metrics_json",
            "status_mapping_json",
            "source_ids_json",
        )
        for row in rows:
            for column in json_columns:
                row[column.removesuffix("_json")] = json.loads(str(row.pop(column)))
            row["ranking_eligibility"] = comparison_eligibility(
                {
                    **row,
                    **{column: "present" for column in json_columns},
                }
            ).__dict__
        return rows

    def failure_guidance(
        self, method_ids: list[str], feature_answers: dict[str, set[str]]
    ) -> list[FailureGuidance]:
        with self.connect() as connection:
            return failure_guidance(connection, method_ids, feature_answers)

    def structured_failure_modes(self) -> list[dict[str, Any]]:
        with self.connect() as connection:
            return export_failure_modes(connection)

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

    def problem_catalog(self) -> ProblemCatalog:
        definitions = [
            ProblemDefinition(
                **_decode_json_columns(
                    row,
                    {
                        "available_oracles_json": "available_oracles",
                        "dimensionality_policy_json": "dimensionality_policy",
                        "related_problem_ids_json": "related_problem_ids",
                        "feature_ids_json": "feature_ids",
                        "source_ids_json": "source_ids",
                    },
                )
            )
            for row in self.fetch_all(
                "SELECT * FROM problem_definitions ORDER BY problem_definition_id"
            )
        ]
        instances = [
            ProblemInstance(
                **_decode_json_columns(
                    row,
                    {
                        "parameters_json": "parameters",
                        "bounds_json": "bounds",
                        "constraints_json": "constraints",
                        "initialization_candidates_json": "initialization_candidates",
                        "known_reference_json": "known_reference",
                        "display_json": "display",
                        "intended_phenomena_json": "intended_phenomena",
                        "source_ids_json": "source_ids",
                    },
                )
            )
            for row in self.fetch_all(
                "SELECT * FROM problem_instances ORDER BY problem_instance_id"
            )
        ]
        canonical = load_problem_suite()
        if definitions != sorted(
            canonical.definitions, key=lambda item: item.problem_definition_id
        ) or instances != sorted(canonical.instances, key=lambda item: item.problem_instance_id):
            raise ValueError("SQLite problem catalog differs from the versioned problem-suite seed")
        for instance in instances:
            get_runtime_problem(instance.problem_instance_id)
        return ProblemCatalog(
            dataset_version=self.dataset_version(), definitions=definitions, instances=instances
        )

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

    def semantic_view_presets(self) -> list[ViewPresetSeed]:
        rows = self.fetch_all(
            """
            SELECT preset_id, view_id, family, name_ja, name_en,
                   description_ja, description_en, root_support_status,
                   root_entity_type, root_entity_id, axis, relation_types_json,
                   max_depth, filter_policy_json, limitations_ja, limitations_en,
                   focus_fallback_entity_types_json, source_ids_json, last_verified
            FROM view_presets
            WHERE family = 'semantic_tree'
            ORDER BY rowid
            """
        )
        presets: list[ViewPresetSeed] = []
        for row in rows:
            relation_types = json.loads(str(row.pop("relation_types_json")))
            filter_policy = json.loads(str(row.pop("filter_policy_json")))
            focus_fallback_entity_types = json.loads(
                str(row.pop("focus_fallback_entity_types_json"))
            )
            source_ids = json.loads(str(row.pop("source_ids_json")))
            presets.append(
                ViewPresetSeed.model_validate(
                    {
                        **row,
                        "relation_types": relation_types,
                        "filter_policy": filter_policy,
                        "focus_fallback_entity_types": focus_fallback_entity_types,
                        "source_ids": source_ids,
                    }
                )
            )
        return presets

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
        return self._without_retired_rule_targets(rows, normalized=True)

    def predicate_catalog(self) -> PredicateCatalog:
        predicates = self.fetch_all("SELECT * FROM atomic_predicates ORDER BY predicate_id")
        for row in predicates:
            row["value"] = json.loads(str(row.pop("value_json")))
            row["source_ids"] = json.loads(str(row.pop("source_ids_json")))

        policies = self.fetch_all("SELECT * FROM predicate_policies ORDER BY policy_id")
        for row in policies:
            expression_json = row.pop("expression_json")
            row["expression"] = (
                json.loads(str(expression_json)) if expression_json is not None else None
            )
            row["source_ids"] = json.loads(str(row.pop("source_ids_json")))

        coverage = self.fetch_all(
            "SELECT * FROM predicate_coverage ORDER BY subject_type, subject_id"
        )
        for row in coverage:
            row["source_ids"] = json.loads(str(row.pop("source_ids_json")))

        retirements = self.fetch_all(
            "SELECT * FROM decision_rule_target_retirements ORDER BY retirement_id"
        )
        for row in retirements:
            row["source_ids"] = json.loads(str(row.pop("source_ids_json")))

        return PredicateCatalog.model_validate(
            {
                "predicates": predicates,
                "policies": policies,
                "coverage": coverage,
                "rule_target_retirements": retirements,
            }
        )

    def predicate_parent_map(self) -> dict[SubjectKey, SubjectKey | None]:
        rows = self.fetch_all(
            """
            SELECT method_id, method_family_id
            FROM methods
            ORDER BY method_id
            """
        )
        result: dict[SubjectKey, SubjectKey | None] = {}
        family_ids = {str(row["method_family_id"]) for row in rows if row["method_family_id"]}
        for family_id in family_ids:
            result[("method_family", family_id)] = None
        for row in rows:
            method_id = str(row["method_id"])
            family_id = row["method_family_id"]
            result[("method", method_id)] = ("method_family", str(family_id)) if family_id else None
        return result

    def predicate_facts(self, answers: dict[str, tuple[str, ...]]) -> dict[str, PredicateFact]:
        question_rows = self.fetch_all(
            "SELECT question_id, answer_type, mapped_feature_id FROM decision_questions"
        )
        facts: dict[str, PredicateFact] = {}
        for row in question_rows:
            question_id = str(row["question_id"])
            values = answers.get(question_id)
            if values is None:
                continue
            value: object = list(values) if row["answer_type"] == "multi_choice" else values[0]
            facts[str(row["mapped_feature_id"])] = PredicateFact(status="known", value=value)
        return facts

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

    def _without_retired_rule_targets(
        self, rows: list[dict[str, Any]], *, normalized: bool
    ) -> list[dict[str, Any]]:
        retirement_rows = self.fetch_all(
            "SELECT rule_id, method_id FROM decision_rule_target_retirements"
        )
        retired = {(str(row["rule_id"]), str(row["method_id"])) for row in retirement_rows}
        if not retired:
            return rows
        catalog = self.predicate_catalog()
        parent_map = self.predicate_parent_map()
        feature_by_question = {
            str(row["question_id"]): str(row["mapped_feature_id"])
            for row in self.fetch_all(
                "SELECT question_id, mapped_feature_id FROM decision_questions"
            )
        }
        active: list[dict[str, Any]] = []
        for row in rows:
            targets = (
                [str(item) for item in row["action_target_ids"]]
                if normalized
                else split_ids(row.get("action_target_ids"))
            )
            rule_id = str(row["rule_id"])
            retired_targets = [target for target in targets if (rule_id, target) in retired]
            for method_id in retired_targets:
                feature_id = feature_by_question[str(row["question_id"])]
                result = evaluate_eligibility(
                    catalog,
                    {feature_id: PredicateFact(status="known", value=str(row["answer_condition"]))},
                    subject_type="method",
                    subject_id=method_id,
                    parent_by_subject=parent_map,
                )
                if result.status != "excluded":
                    raise PredicateContractError(
                        f"retired target does not compile back to exclusion: {rule_id}/{method_id}"
                    )
            # Retired targets are removed from the legacy authority, then compiled from
            # the validated predicate policy. Preserve order and the public rule trace.
            compiled = set(retired_targets)
            remaining = [
                target
                for target in targets
                if (rule_id, target) not in retired or target in compiled
            ]
            if not remaining:
                continue
            row["action_target_ids"] = remaining if normalized else ";".join(remaining)
            active.append(row)
        return active


def _decode_json_columns(row: dict[str, Any], columns: dict[str, str]) -> dict[str, Any]:
    values = dict(row)
    for source, target in columns.items():
        raw = values.pop(source)
        values[target] = json.loads(str(raw)) if raw is not None else None
    return values
