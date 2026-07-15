from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from typing import Any

STRUCTURED_FAILURE_IDS = (
    "FM003",
    "FM007",
    "FM009",
    "FM011",
    "FM014",
    "FM015",
    "FM016",
    "FM022",
    "FM024",
    "FM025",
    "FM033",
    "FM037",
)

OBSERVABLE_IDS = frozenset(
    {
        "gradient",
        "objective_value",
        "update_vector",
        "constraint_violation",
        "search_nodes",
        "posterior_uncertainty",
    }
)

TRIGGERS: dict[str, tuple[str | None, str | None, str, object]] = {
    "FM003": ("P_M_BFGS_LARGE_NOISE", None, "eq", "large_noise"),
    "FM007": (None, "F_DIMENSION_CONTEXT", "eq", "huge_sparse_or_distributed"),
    "FM009": (None, "F_DIMENSION_CONTEXT", "eq", "over_10000"),
    "FM011": (None, "F_CONSTRAINT_CLASS", "eq", "nonlinear"),
    "FM014": (None, "F_CONSTRAINT_CLASS", "eq", "implicit_or_failure"),
    "FM015": (None, "F_CONSTRAINT_CLASS", "eq", "nonlinear"),
    "FM016": (None, "F_GUARANTEE_GLOBAL_CERTIFICATE", "eq", "multiple_distinct_solutions"),
    "FM022": ("P_M_NELDER_MEAD_SCALE_LIMIT", None, "eq", "over_10000"),
    "FM024": (None, "F_EVALUATION_RELIABILITY", "eq", "large_noise"),
    "FM025": (None, "F_GUARANTEE_GLOBAL_CERTIFICATE", "eq", "approximation_guarantee"),
    "FM033": ("P_M_BAYESIAN_OPT_GP_SCALE_LIMIT", None, "eq", "over_10000"),
    "FM037": ("P_M_CMA_ES_SCALE_LIMIT", None, "eq", "over_10000"),
}

SYMPTOMS = {
    "FM003": ("gradient", None),
    "FM007": ("objective_value", None),
    "FM009": ("update_vector", None),
    "FM011": ("constraint_violation", None),
    "FM014": (None, "model_infeasible"),
    "FM015": ("constraint_violation", None),
    "FM016": ("objective_value", None),
    "FM022": ("search_nodes", None),
    "FM024": ("objective_value", None),
    "FM025": (None, "solver_status"),
    "FM033": ("posterior_uncertainty", None),
    "FM037": (None, "population_diversity"),
}

SCENARIOS = {
    "FM009": "SCENARIO_GRADIENT_DESCENT_QUADRATIC_DIVERGENCE",
    "FM007": "SCENARIO_MOMENTUM_QUADRATIC_DIVERGENCE",
    "FM024": "SCENARIO_ADAM_QUADRATIC_DIVERGENCE",
    "FM022": "SCENARIO_BINARY_KNAPSACK_BNB_BUDGET",
}


@dataclass(frozen=True)
class FailureGuidance:
    failure_mode_id: str
    method_id: str
    name: str
    warning: str
    disposition: str
    severity: str
    source_ids: tuple[str, ...]


def insert_structured_failure_modes(connection: sqlite3.Connection, *, release_date: str) -> None:
    rows = {
        str(row["failure_mode_id"]): row
        for row in connection.execute(
            "SELECT * FROM failure_modes WHERE failure_mode_id IN "
            f"({','.join('?' for _ in STRUCTURED_FAILURE_IDS)})",
            STRUCTURED_FAILURE_IDS,
        )
    }
    if set(rows) != set(STRUCTURED_FAILURE_IDS):
        raise ValueError("structured failure migration references missing legacy rows")
    for failure_id in STRUCTURED_FAILURE_IDS:
        row = rows[failure_id]
        category = str(row["category"])
        source_ids = _split(str(row["source_ids"] or ""))
        scope = "implementation_specific" if failure_id == "FM025" else "method_theory"
        connection.execute(
            """INSERT INTO failure_mode_profiles VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                failure_id,
                category,
                scope,
                "fatal" if str(row["severity"]) == "critical" else "recoverable",
                "exclude" if failure_id in {"FM003", "FM014"} else "warning",
                row["severity"],
                row["confidence"],
                _json(source_ids),
                release_date,
            ),
        )
        predicate_id, feature_id, operator, value = TRIGGERS[failure_id]
        connection.execute(
            "INSERT INTO failure_mode_triggers VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                f"TRIGGER_{failure_id}",
                failure_id,
                predicate_id,
                feature_id,
                operator,
                _json(value),
                f"Canonical condition for {failure_id}.",
            ),
        )
        observable_id, non_visual_state = SYMPTOMS[failure_id]
        connection.execute(
            "INSERT INTO failure_mode_symptoms VALUES (?, ?, ?, ?, ?)",
            (f"SYMPTOM_{failure_id}", failure_id, observable_id, non_visual_state, row["symptoms"]),
        )
        diagnostics = _split(str(row["diagnostic_ids"] or ""))
        for index, diagnostic_id in enumerate(diagnostics, start=1):
            connection.execute(
                "INSERT INTO failure_mode_diagnostics VALUES (?, ?, ?, ?)",
                (failure_id, index, diagnostic_id, str(row["prevention"] or row["symptoms"])),
            )
        connection.execute(
            "INSERT INTO failure_mode_mitigations VALUES (?, ?, 1, ?, ?, ?)",
            (
                f"MITIGATION_{failure_id}",
                failure_id,
                row["remediation"],
                str(row["switch_condition"] or "trigger confirmed"),
                "May change runtime, guarantees, or solution interpretation.",
            ),
        )
        method_ids = [
            item
            for item in _split(str(row["applies_to_method_ids"] or ""))
            if item.startswith("M_")
        ]
        for method_id in method_ids:
            connection.execute(
                "INSERT INTO failure_mode_affected_entities VALUES (?, 'method', ?, ?)",
                (
                    failure_id,
                    method_id,
                    "implementation_only" if scope == "implementation_specific" else "theoretical",
                ),
            )
        implementation_ids: list[str] = []
        if scope == "implementation_specific":
            implementation_ids = [
                str(item[0])
                for item in connection.execute(
                    "SELECT implementation_id FROM implementations ORDER BY implementation_id"
                )
            ]
            for implementation_id in implementation_ids:
                connection.execute(
                    "INSERT INTO failure_mode_affected_entities VALUES "
                    "(?, 'implementation', ?, 'implementation_only')",
                    (failure_id, implementation_id),
                )
        if not method_ids and not implementation_ids:
            affected_feature_id = feature_id
            if affected_feature_id is None and predicate_id is not None:
                affected_feature_id = str(
                    connection.execute(
                        "SELECT feature_id FROM atomic_predicates WHERE predicate_id = ?",
                        (predicate_id,),
                    ).fetchone()[0]
                )
            connection.execute(
                "INSERT INTO failure_mode_affected_entities VALUES (?, 'feature', ?, 'contextual')",
                (failure_id, affected_feature_id),
            )
        if failure_id in SCENARIOS:
            connection.execute(
                "INSERT INTO failure_mode_scenarios VALUES (?, ?, 'failure_contrast')",
                (failure_id, SCENARIOS[failure_id]),
            )


def failure_guidance(
    connection: sqlite3.Connection,
    method_ids: list[str],
    feature_answers: dict[str, set[str]],
) -> list[FailureGuidance]:
    if not method_ids:
        return []
    rows = connection.execute(
        f"""
        SELECT profile.failure_mode_id, affected.entity_id AS method_id,
               legacy.name_ja, legacy.symptoms, profile.diagnose_disposition,
               profile.severity, profile.source_ids_json, trigger.feature_id,
               predicate.feature_id AS predicate_feature_id, trigger.operator,
               trigger.value_json
        FROM failure_mode_profiles AS profile
        JOIN failure_modes AS legacy USING (failure_mode_id)
        JOIN failure_mode_affected_entities AS affected USING (failure_mode_id)
        JOIN failure_mode_triggers AS trigger USING (failure_mode_id)
        LEFT JOIN atomic_predicates AS predicate USING (predicate_id)
        WHERE affected.entity_type = 'method'
          AND affected.entity_id IN ({",".join("?" for _ in method_ids)})
        ORDER BY profile.failure_mode_id, affected.entity_id
        """,
        method_ids,
    ).fetchall()
    result = []
    for row in rows:
        feature_id = str(row["feature_id"] or row["predicate_feature_id"])
        expected = json.loads(str(row["value_json"]))
        answers = feature_answers.get(feature_id, set())
        matched = expected in answers if row["operator"] == "eq" else bool(set(expected) & answers)
        if matched:
            result.append(
                FailureGuidance(
                    failure_mode_id=str(row["failure_mode_id"]),
                    method_id=str(row["method_id"]),
                    name=str(row["name_ja"]),
                    warning=f"{row['name_ja']}: {row['symptoms']}",
                    disposition=str(row["diagnose_disposition"]),
                    severity=str(row["severity"]),
                    source_ids=tuple(json.loads(str(row["source_ids_json"]))),
                )
            )
    return result


def export_failure_modes(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    profiles = connection.execute(
        """SELECT profile.*, legacy.name_ja, legacy.name_en
           FROM failure_mode_profiles AS profile
           JOIN failure_modes AS legacy USING (failure_mode_id)
           ORDER BY failure_mode_id"""
    ).fetchall()
    result = []
    for profile in profiles:
        failure_id = str(profile["failure_mode_id"])
        result.append(
            {
                **dict(profile),
                "source_ids": json.loads(str(profile["source_ids_json"])),
                "triggers": [
                    dict(row)
                    for row in connection.execute(
                        "SELECT * FROM failure_mode_triggers WHERE failure_mode_id = ? "
                        "ORDER BY trigger_id",
                        (failure_id,),
                    )
                ],
                "symptoms": [
                    dict(row)
                    for row in connection.execute(
                        "SELECT * FROM failure_mode_symptoms WHERE failure_mode_id = ? "
                        "ORDER BY symptom_id",
                        (failure_id,),
                    )
                ],
                "diagnostics": [
                    dict(row)
                    for row in connection.execute(
                        "SELECT * FROM failure_mode_diagnostics WHERE failure_mode_id = ? "
                        "ORDER BY sequence",
                        (failure_id,),
                    )
                ],
                "mitigations": [
                    dict(row)
                    for row in connection.execute(
                        "SELECT * FROM failure_mode_mitigations WHERE failure_mode_id = ? "
                        "ORDER BY priority",
                        (failure_id,),
                    )
                ],
                "affected_entities": [
                    dict(row)
                    for row in connection.execute(
                        "SELECT * FROM failure_mode_affected_entities WHERE failure_mode_id = ? "
                        "ORDER BY entity_type, entity_id",
                        (failure_id,),
                    )
                ],
                "scenario_ids": [
                    str(row[0])
                    for row in connection.execute(
                        "SELECT scenario_id FROM failure_mode_scenarios WHERE failure_mode_id = ? "
                        "ORDER BY scenario_id",
                        (failure_id,),
                    )
                ],
            }
        )
        result[-1].pop("source_ids_json")
    return result


def _split(value: str) -> list[str]:
    return [item.strip() for item in value.split(";") if item.strip()]


def _json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
