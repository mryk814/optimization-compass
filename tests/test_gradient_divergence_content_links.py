import re
from pathlib import Path

from optimization_compass.content_models import load_content


def test_gradient_method_guides_connect_each_failure_trace_and_shared_compare() -> None:
    pages = {page.content_id: page for page in load_content(Path("content"))}
    expected = {
        "method.gradient-descent": "gradient_descent-quadratic-divergence",
        "momentum-sgd": "momentum-quadratic-divergence",
        "adam": "adam-quadratic-divergence",
    }

    for content_id, artifact_id in expected.items():
        page = pages[content_id]
        assert page.visualization_ids == (artifact_id,)
        assert page.comparison_ids == (
            "COMPARE_GRADIENT_FAMILY",
            "COMPARE_GRADIENT_DIVERGENCE",
        )
        # The failure run opens on its trace page; /theater/learning/ shows only learning slices.
        assert f"#/traces/{artifact_id}" in page.body
        assert "#/compare/COMPARE_GRADIENT_DIVERGENCE" in page.body
        if content_id == "adam":
            assert "同じ目的関数・初期点・40回の評価予算" in page.body
            assert "手法の一般的な順位ではありません" in page.body
        else:
            assert re.search(r"良い(parameter|パラメータ|設定)を探索する比較でも", page.body)
            assert re.search(r"一般(的な)?性能(の)?(ranking|ランキング|順位)", page.body)
