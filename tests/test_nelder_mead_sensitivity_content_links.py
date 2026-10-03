from pathlib import Path

from optimization_compass.content_models import load_content


def test_nelder_mead_lessons_connect_initial_simplex_sensitivity() -> None:
    pages = {page.content_id: page for page in load_content(Path("content"))}
    method = pages["method.nelder-mead"]
    concept = pages["concept.derivative-free"]

    for page in (method, concept):
        assert page.visualization_ids == (
            "nelder-mead-quadratic",
            "nelder-mead-quadratic-shifted",
        )
        assert "COMPARE_NELDER_MEAD_INITIAL_SIMPLEX" in page.comparison_ids
        assert "#/theater/learning/SCENARIO_NM_QUADRATIC" in page.body
        assert "#/theater/learning/SCENARIO_NM_QUADRATIC_SHIFTED" in page.body
        assert "#/compare/COMPARE_NELDER_MEAD_INITIAL_SIMPLEX" in page.body
        assert any(term in page.body for term in ("一般性能順位付け", "一般的な性能の順位付け"))

    assert "変えるのは初期単体の位置だけです" in method.body
    assert "微分を使わない系統全体" in concept.body
