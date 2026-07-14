from pathlib import Path

import pytest
from pydantic import ValidationError

from optimization_compass.visualization_scenarios import VisualizationScenarioIndex

FIXTURE = Path("site/src/contracts/visualization-scenarios.fixture.json")


def test_shared_visualization_scenario_fixture_is_valid() -> None:
    index = VisualizationScenarioIndex.model_validate_json(FIXTURE.read_bytes())

    assert index.contract_version == "1.0.0"
    assert index.scenarios[0].artifact.renderer_family == "simplex_geometry"
    assert index.scenarios[0].lesson.limitations_ja == "2次元の教育用決定論的実行"


def test_visualization_scenario_rejects_unknown_envelope_fields() -> None:
    payload = VisualizationScenarioIndex.model_validate_json(FIXTURE.read_bytes()).model_dump(
        mode="json"
    )
    payload["renderer_registry"] = {}

    with pytest.raises(ValidationError, match="extra_forbidden"):
        VisualizationScenarioIndex.model_validate(payload)
