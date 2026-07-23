from pathlib import Path

from optimization_compass.content_models import load_content


def test_slsqp_guide_keeps_the_general_feasibility_lesson_primary() -> None:
    pages = {page.content_id: page for page in load_content(Path("content"))}
    slsqp = pages["slsqp"]

    assert slsqp.visualization_ids == ("constrained-disk-feasible-region",)
    assert slsqp.comparison_ids == ("COMPARE_CONSTRAINED_FAILURE",)
    assert "#/theater/learning/SCENARIO_CONSTRAINED_DISK_FEASIBLE_PATH" in slsqp.body
    assert "#/compare/COMPARE_CONSTRAINED_FAILURE" in slsqp.body
    assert "目的値だけが良いinfeasibleな点を成功と数えません" in slsqp.body
    assert "solverの一般性能rankingには使いません" in slsqp.body
