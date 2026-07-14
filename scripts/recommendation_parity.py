from __future__ import annotations

import argparse
import json
from pathlib import Path

from optimization_compass.engine import RecommendationEngine
from optimization_compass.models import RecommendationRequest
from optimization_compass.site_recommendation import recommendation_projection


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "fixture", type=Path, nargs="?", default=Path("tests/fixtures/recommendation_cases.json")
    )
    parser.add_argument("--update", action="store_true")
    args = parser.parse_args()
    payload = json.loads(args.fixture.read_text(encoding="utf-8"))
    engine = RecommendationEngine()
    payload["dataset_version"] = engine.repository.dataset_version()
    results = []
    for case in payload["cases"]:
        request = RecommendationRequest.model_validate(case["request"])
        expected = recommendation_projection(engine.recommend(request))
        case["expected"] = expected
        results.append({"case_id": case["case_id"], "result": expected})
    if args.update:
        args.fixture.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    else:
        print(json.dumps(results, ensure_ascii=False))


if __name__ == "__main__":
    main()
