from optimization_compass.root_finding import (
    ROOT_SCENARIO_ID,
    SQUARED_SCENARIO_ID,
    generate_root_finding_traces,
)


def test_ec028_keeps_component_tolerance_separate_from_squared_residual() -> None:
    root, scalar_only = generate_root_finding_traces(dataset_version="0.18.16")

    assert root.scenario_id == ROOT_SCENARIO_ID
    assert root.terminal_status == "converged"
    assert max(abs(metric.value) for metric in root.frames[-1].metrics[:2]) < 0.02

    assert scalar_only.scenario_id == SQUARED_SCENARIO_ID
    assert scalar_only.terminal_status == "stopped"
    final_metrics = {metric.metric_id: metric.value for metric in scalar_only.frames[-1].metrics}
    assert final_metrics["squared_residual"] < 0.003
    assert final_metrics["residual_max_abs"] > 0.02
