from pathlib import Path

from optimization_compass.content_models import load_content


def test_discrete_family_guide_connects_cases_and_search_tree_lessons() -> None:
    pages = {page.content_id: page for page in load_content(Path("content"))}
    discrete = pages["family.discrete-structure"]

    assert discrete.visualization_ids == (
        "binary-knapsack-bnb-complete",
        "binary-knapsack-bnb-budget",
    )
    assert discrete.comparison_ids == ("COMPARE_KNAPSACK_BNB_BUDGET",)
    for route in (
        "#/gallery/budget-allocation",
        "#/gallery/shift-scheduling",
        "#/gallery/EC019",
        "#/theater/search-tree/binary-knapsack-bnb-complete",
        "#/theater/search-tree/binary-knapsack-bnb-budget",
        "#/compare/COMPARE_KNAPSACK_BNB_BUDGET",
    ):
        assert route in discrete.body

    assert "実務Caseそのものではありません" in discrete.body
    assert "一般性能ranking" in discrete.body
