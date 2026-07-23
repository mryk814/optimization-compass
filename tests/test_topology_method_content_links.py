from pathlib import Path

from optimization_compass.content_models import load_content


def test_simp_guide_separates_representation_and_update_rule_comparisons() -> None:
    pages = {page.content_id: page for page in load_content(Path("content"))}
    simp = pages["simp-topology"]

    assert simp.visualization_ids == (
        "topology-optimization-field-evolution",
        "shape-topology-representation-contrast",
    )
    assert simp.comparison_ids == (
        "COMPARE_TOPOLOGY_OC_MMA",
        "COMPARE_SHAPE_TOPOLOGY_REPRESENTATION",
    )
    for route in (
        "#/compare/COMPARE_SHAPE_TOPOLOGY_REPRESENTATION",
        "#/compare/COMPARE_TOPOLOGY_OC_MMA",
        "#/theater/learning/SCENARIO_SHAPE_TOPOLOGY_REPRESENTATION_CONTRAST",
    ):
        assert route in simp.body

    assert "設計表現" in simp.body
    assert "更新則" in simp.body
    assert "一般性能のrankingには使いません" in simp.body
