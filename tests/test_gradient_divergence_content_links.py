import re
from pathlib import Path

from optimization_compass.content_models import load_content


def test_gradient_method_guides_connect_each_failure_trace_and_shared_compare() -> None:
    pages = {page.content_id: page for page in load_content(Path("content"))}
    expected = {
        "method.gradient-descent": (
            "gradient_descent-quadratic-divergence",
            "SCENARIO_GRADIENT_DESCENT_QUADRATIC_DIVERGENCE",
        ),
        "momentum-sgd": (
            "momentum-quadratic-divergence",
            "SCENARIO_MOMENTUM_QUADRATIC_DIVERGENCE",
        ),
        "adam": (
            "adam-quadratic-divergence",
            "SCENARIO_ADAM_QUADRATIC_DIVERGENCE",
        ),
    }

    for content_id, (artifact_id, scenario_id) in expected.items():
        page = pages[content_id]
        assert page.visualization_ids == (artifact_id,)
        assert page.comparison_ids == (
            "COMPARE_GRADIENT_FAMILY",
            "COMPARE_GRADIENT_DIVERGENCE",
        )
        assert f"#/theater/learning/{scenario_id}" in page.body
        assert "#/compare/COMPARE_GRADIENT_DIVERGENCE" in page.body
        assert re.search(r"良い(parameter|パラメータ|設定)を探索する比較でも", page.body)
        assert re.search(r"一般(的な)?性能(ranking|ランキング)", page.body)
