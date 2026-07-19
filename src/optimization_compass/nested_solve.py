from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from optimization_compass.trace_models import AlgorithmTrace, TraceFrame, TraceMetric

BILEVEL_EXACT_TRACE_ID = "bilevel-regression-exact-inner"
BILEVEL_RELAXED_TRACE_ID = "bilevel-regression-relaxed-complementarity"
BILEVEL_EXACT_SCENARIO_ID = "SCENARIO_BILEVEL_REGRESSION_EXACT"
BILEVEL_RELAXED_SCENARIO_ID = "SCENARIO_BILEVEL_REGRESSION_RELAXED"
BILEVEL_PROBLEM_DEFINITION_ID = "PROBLEM_BILEVEL_REGRESSION"
BILEVEL_PROBLEM_INSTANCE_ID = "INSTANCE_BILEVEL_REGRESSION_2COEF"
BILEVEL_BENCHMARK_CONTEXT_ID = "BENCH_BILEVEL_REGRESSION_EDUCATIONAL_6"
BILEVEL_GENERATOR_ID = "educational.bilevel_regression_ledger.v1"
BILEVEL_GENERATOR_VERSION = "1.0.0"
HYBRID_CHATTERING_TRACE_ID = "hybrid-mode-chattering-ledger"
HYBRID_CHATTERING_SCENARIO_ID = "SCENARIO_HYBRID_MODE_CHATTERING"
HYBRID_PROBLEM_DEFINITION_ID = "PROBLEM_HYBRID_MODE_DISCOVERY"
HYBRID_PROBLEM_INSTANCE_ID = "INSTANCE_HYBRID_CHATTERING_LEDGER"

_BILEVEL_COMMON_PARAMETERS: dict[str, object] = {
    "outer_step_policy": "fixed_teaching_sequence",
    "inner_policy": "warm_started_slsqp",
    "inner_tolerance": 1e-8,
    "inner_max_iterations": 100,
    "derivative_route": "implicit_active_set",
}


def generate_bilevel_regression_traces(*, dataset_version: str) -> list[AlgorithmTrace]:
    exact_values = [
        (0.128, 0.940, 8e-9, 31, 7e-10, 6e-9),
        (0.096, 0.701, 7e-9, 28, 6e-10, 5e-9),
        (0.071, 0.542, 6e-9, 24, 5e-10, 4e-9),
        (0.059, 0.491, 5e-9, 21, 4e-10, 3e-9),
        (0.052, 0.458, 4e-9, 19, 3e-10, 2e-9),
        (0.049, 0.447, 3e-9, 17, 2e-10, 1e-9),
        (0.048, 0.444, 2e-9, 16, 1e-10, 8e-10),
    ]
    relaxed_values = [
        (0.128, 0.940, 8e-9, 31, 9e-3, 6e-9),
        (0.087, 0.684, 7e-9, 27, 8e-3, 5e-9),
        (0.058, 0.521, 6e-9, 23, 7e-3, 4e-9),
        (0.043, 0.469, 5e-9, 20, 6e-3, 3e-9),
        (0.038, 0.441, 4e-9, 18, 5e-3, 2e-9),
        (0.035, 0.431, 3e-9, 16, 4e-3, 1e-9),
        (0.034, 0.428, 2e-9, 15, 4e-3, 8e-10),
    ]
    return [
        _bilevel_trace(
            dataset_version=dataset_version,
            trace_id=BILEVEL_EXACT_TRACE_ID,
            scenario_id=BILEVEL_EXACT_SCENARIO_ID,
            treatment="exact_kkt_complementarity",
            relaxation_parameter=0.0,
            values=exact_values,
            terminal_status="converged",
        ),
        _bilevel_trace(
            dataset_version=dataset_version,
            trace_id=BILEVEL_RELAXED_TRACE_ID,
            scenario_id=BILEVEL_RELAXED_SCENARIO_ID,
            treatment="finite_relaxation",
            relaxation_parameter=1e-2,
            values=relaxed_values,
            terminal_status="stopped",
        ),
    ]


def generate_hybrid_chattering_trace(*, dataset_version: str) -> AlgorithmTrace:
    values = [
        (3.20, 0.0, 0.0, 1.00, 0.20),
        (2.91, 1.0, 1.0, 0.50, 0.13),
        (2.69, 0.0, 2.0, 0.25, 0.09),
        (2.52, 1.0, 3.0, 0.12, 0.06),
        (2.39, 0.0, 4.0, 0.06, 0.04),
        (2.29, 1.0, 5.0, 0.03, 0.028),
        (2.21, 0.0, 6.0, 0.015, 0.019),
        (2.15, 1.0, 7.0, 0.008, 0.013),
    ]
    frames = [
        TraceFrame(
            frame_index=index,
            iteration=index,
            oracle_evaluations=index,
            elapsed_steps=index,
            elapsed_time_ms=float(index * 80),
            event_type="initialize" if index == 0 else "mode_switch" if index < 7 else "stop",
            decision="not_applicable" if index in {0, 7} else "accepted",
            explanation_key=(
                "initial_mode"
                if index == 0
                else "relaxed_mode_switch"
                if index < 7
                else "chattering_stop"
            ),
            event_label_ja=(
                "初期mode"
                if index == 0
                else "relaxed indicatorがmodeを切替"
                if index < 7
                else "switch間隔が縮まり停止"
            ),
            event_label_en=(
                "Initial mode"
                if index == 0
                else "Relaxed indicator switches mode"
                if index < 7
                else "Stop as switch intervals shrink"
            ),
            keyframe=index in {0, 3, 7},
            points=[],
            vectors=[],
            metrics=[
                _metric("objective_value", "目的関数値", "objective value", objective),
                _metric("mode_sequence", "active mode", "active mode", mode),
                _metric("mode_switch_count", "mode切替数", "mode switch count", switches),
                _metric(
                    "switching_interval",
                    "切替間隔",
                    "switching interval",
                    interval,
                    "normalized time",
                ),
                _metric("dynamics_defect", "dynamics defect", "dynamics defect", defect),
            ],
            payload={
                "mode_policy": "relaxed_mode_discovery",
                "active_mode": int(mode),
                "minimum_dwell_time": 0.0,
                "contact_model": "not_applicable",
            },
        )
        for index, (objective, mode, switches, interval, defect) in enumerate(values)
    ]
    return AlgorithmTrace(
        contract_version="1.0.0",
        dataset_version=dataset_version,
        data_version="1.0.0",
        trace_id=HYBRID_CHATTERING_TRACE_ID,
        method_id="M_DIRECT_COLLOCATION",
        profile_id="PROFILE_HYBRID_MODE_LEDGER",
        objective_id=HYBRID_PROBLEM_INSTANCE_ID,
        scenario_id=HYBRID_CHATTERING_SCENARIO_ID,
        generator_id="educational.hybrid_mode_ledger.v1",
        generator_version="1.0.0",
        implementation_mapping_status="not_applicable",
        implementation_id=None,
        objective={"kind": "tracking_with_relaxed_mode_discovery"},
        preset={"preset_id": "VIEW_HYBRID_MODE_CHATTERING", "contact_model": "not_applicable"},
        parameters={
            "mode_policy": "relaxed_mode_discovery",
            "minimum_dwell_time": 0.0,
            "switch_penalty": 0.0,
        },
        initial_state={"point": [0.0, 0.0], "mode": 0},
        seed={"status": "not_applicable", "value": None},
        evaluation_budget=len(values) - 1,
        stopping={"max_oracle_evaluations": len(values) - 1, "minimum_switch_interval": 0.01},
        environment={"runtime": "deterministic_teaching_ledger", "version": "1.0.0"},
        fairness_statement=(
            "固定したmode indicator履歴でchatteringの読み方だけを示す。"
            "contact/friction solverやhybrid手法の一般性能を比較しない。"
        ),
        frames=frames,
        terminal_status="stopped",
        terminal_summary_ja=(
            "目的関数とdynamics defectは下がったが、mode切替間隔が縮み続けたため、"
            "可解なhybrid trajectoryとは扱わず停止した。"
        ),
        terminal_summary_en=(
            "The objective and dynamics defect decreased, but shrinking mode-switch intervals "
            "triggered a stop rather than a claim of a valid hybrid trajectory."
        ),
        source_ids=["S042", "S043", "S056", "S076"],
    )


def _bilevel_trace(
    *,
    dataset_version: str,
    trace_id: str,
    scenario_id: str,
    treatment: str,
    relaxation_parameter: float,
    values: Sequence[tuple[float, float, float, int, float, float]],
    terminal_status: Literal["converged", "stopped"],
) -> AlgorithmTrace:
    frames = [
        TraceFrame(
            frame_index=index,
            iteration=index,
            oracle_evaluations=index,
            elapsed_steps=index,
            elapsed_time_ms=float(index * 100),
            event_type="initialize" if index == 0 else "outer_update" if index < 6 else "stop",
            decision="not_applicable" if index in {0, 6} else "accepted",
            explanation_key=(
                "initial_inner_solve"
                if index == 0
                else "implicit_outer_update"
                if index < 6
                else "residual_check"
            ),
            event_label_ja=(
                "inner solveを検証"
                if index == 0
                else "implicit derivativeでouterを更新"
                if index < 6
                else "保証範囲を確認して停止"
            ),
            event_label_en=(
                "Validate the inner solve"
                if index == 0
                else "Update the outer variable with an implicit derivative"
                if index < 6
                else "Stop after checking the guarantee boundary"
            ),
            keyframe=index in {0, 3, 6},
            points=[],
            vectors=[],
            metrics=[
                _metric("outer_objective", "outer objective", "outer objective", outer),
                _metric("inner_objective", "inner objective", "inner objective", inner),
                _metric("inner_residual", "inner residual", "inner residual", residual),
                _metric("inner_iterations", "inner iteration数", "inner iterations", iterations),
                _metric(
                    "complementarity_residual",
                    "complementarity residual",
                    "complementarity residual",
                    complementarity,
                ),
                _metric(
                    "stationarity_residual",
                    "stationarity residual",
                    "stationarity residual",
                    stationarity,
                ),
                _metric(
                    "relaxation_parameter",
                    "relaxation parameter",
                    "relaxation parameter",
                    relaxation_parameter,
                ),
            ],
            payload={
                "outer_iteration": index,
                "inner_status": "tolerance_met",
                "inner_policy": _BILEVEL_COMMON_PARAMETERS["inner_policy"],
                "inner_tolerance": _BILEVEL_COMMON_PARAMETERS["inner_tolerance"],
                "derivative_route": _BILEVEL_COMMON_PARAMETERS["derivative_route"],
                "complementarity_treatment": treatment,
                "relaxation_parameter": relaxation_parameter,
            },
        )
        for index, (outer, inner, residual, iterations, complementarity, stationarity) in enumerate(
            values
        )
    ]
    return AlgorithmTrace(
        contract_version="1.0.0",
        dataset_version=dataset_version,
        data_version="1.0.0",
        trace_id=trace_id,
        method_id="M_SLSQP",
        profile_id="PROFILE_BILEVEL_REGRESSION_LEDGER",
        objective_id=BILEVEL_PROBLEM_INSTANCE_ID,
        scenario_id=scenario_id,
        generator_id=BILEVEL_GENERATOR_ID,
        generator_version=BILEVEL_GENERATOR_VERSION,
        implementation_mapping_status="not_applicable",
        implementation_id=None,
        objective={
            "kind": "validation_loss_after_inner_nonnegative_regression",
            "inner_constraint": "nonnegative_coefficients",
        },
        preset={"preset_id": "VIEW_BILEVEL_REGRESSION_HISTORY"},
        parameters={
            **_BILEVEL_COMMON_PARAMETERS,
            "complementarity_treatment": treatment,
            "relaxation_parameter": relaxation_parameter,
        },
        initial_state={"point": [0.8], "outer_lambda": 0.8},
        seed={"status": "not_applicable", "value": None},
        evaluation_budget=len(values) - 1,
        stopping={
            "max_oracle_evaluations": len(values) - 1,
            "inner_tolerance": 1e-8,
            "outer_step_tolerance": 1e-4,
        },
        environment={"runtime": "deterministic_teaching_ledger", "version": "1.0.0"},
        fairness_statement=(
            "固定data・outer budget・inner policy・tolerance・implicit derivative routeを共有し、"
            "complementarity treatmentだけを変えるcontrast-only教材である。"
        ),
        frames=frames,
        terminal_status=terminal_status,
        terminal_summary_ja=(
            "inner toleranceとstationarity residualは満たした。"
            + (
                "exact KKT complementarityの固定教材判定も満たした。"
                if relaxation_parameter == 0.0
                else "有限relaxationで残差が残るため、exact complementarityとは判定しない。"
            )
        ),
        terminal_summary_en=(
            "The inner tolerance and stationarity residual passed. "
            + (
                "The fixed teaching check for exact KKT complementarity also passed."
                if relaxation_parameter == 0.0
                else (
                    "A finite-relaxation residual remains, so exact complementarity is not claimed."
                )
            )
        ),
        source_ids=["S055", "S056", "S064"],
    )


def _metric(
    metric_id: str,
    label_ja: str,
    label_en: str,
    value: float,
    unit: str | None = None,
) -> TraceMetric:
    return TraceMetric(
        metric_id=metric_id,
        label_ja=label_ja,
        label_en=label_en,
        value=float(value),
        unit=unit,
    )
