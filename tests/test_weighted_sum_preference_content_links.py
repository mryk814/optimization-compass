from pathlib import Path

from optimization_compass.content_models import load_content


def test_weighted_sum_guide_separates_front_generation_from_preference() -> None:
    pages = {page.content_id: page for page in load_content(Path("content"))}
    weighted_sum = pages["weighted-sum"]

    assert "S068" in weighted_sum.source_ids
    assert weighted_sum.visualization_ids == ("biobjective-quadratic-pareto-front",)
    assert weighted_sum.comparison_ids == ("COMPARE_PARETO_PREFERENCE",)
    assert "#/theater/learning/SCENARIO_BIOBJECTIVE_PREFERENCE_SENSITIVITY" in weighted_sum.body
    assert "#/compare/COMPARE_PARETO_PREFERENCE" in weighted_sum.body
    assert "front上の選択点だけを動かします" in weighted_sum.body
    assert "solverを再実行してfrontを改善する実験ではありません" in weighted_sum.body
    assert "一般性能ranking" in weighted_sum.body
