from pathlib import Path

from optimization_compass.content_models import load_content


def test_bfgs_guide_foregrounds_constraint_failure_before_line_search() -> None:
    pages = {page.content_id: page for page in load_content(Path("content"))}
    bfgs = pages["bfgs"]

    assert {"S017", "S055", "S064"} <= set(bfgs.source_ids)
    assert bfgs.visualization_ids == ("constrained-disk-feasible-region",)
    assert bfgs.comparison_ids == ("COMPARE_CONSTRAINED_FAILURE",)
    assert "#/theater/learning/SCENARIO_CONSTRAINED_DISK" in bfgs.body
    assert "#/compare/COMPARE_CONSTRAINED_FAILURE" in bfgs.body
    assert "目的関数値が下がっても、制約違反が残る点は解ではありません" in bfgs.body
    assert "ソルバーの一般的な性能ランキングにも使いません" in bfgs.body
