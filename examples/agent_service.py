from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from optimization_compass.agent_service import DeterministicGuidanceService

root = Path(__file__).parents[1]
request: dict[str, Any] = json.loads(
    (root / "examples/binary_linear.json").read_text(encoding="utf-8")
)
service = DeterministicGuidanceService()
capabilities = service.get_capabilities()
response = service.recommend_methods(
    request,
    expected_dataset_version=capabilities.metadata.dataset_version,
)
print(response.model_dump_json(indent=2))
