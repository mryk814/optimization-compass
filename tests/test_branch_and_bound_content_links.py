from pathlib import Path

from optimization_compass.content_models import load_content


def test_branch_and_bound_guide_separates_proof_from_budget_stop() -> None:
    pages = {page.content_id: page for page in load_content(Path("content"))}
    branch_and_bound = pages["branch-and-bound"]

    assert branch_and_bound.visualization_ids == (
        "binary-knapsack-bnb-complete",
        "binary-knapsack-bnb-budget",
    )
    assert branch_and_bound.comparison_ids == ("COMPARE_KNAPSACK_BNB_BUDGET",)
    assert "#/theater/search-tree/binary-knapsack-bnb-complete" in branch_and_bound.body
    assert "#/theater/search-tree/binary-knapsack-bnb-budget" in branch_and_bound.body
    assert "#/compare/COMPARE_KNAPSACK_BNB_BUDGET" in branch_and_bound.body
    assert "正のgapと未探索node" in branch_and_bound.body
    assert "一般性能ranking" in branch_and_bound.body
