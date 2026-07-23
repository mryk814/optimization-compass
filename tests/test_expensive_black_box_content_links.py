from pathlib import Path

from optimization_compass.content_models import load_content
from optimization_compass.content_quality import style_warnings


def test_expensive_black_box_guides_expose_primary_visuals_before_sensitivity_runs() -> None:
    pages = {page.content_id: page for page in load_content(Path("content"))}

    bayesian_optimization = pages["bayesian-optimization"]
    assert bayesian_optimization.visualization_ids == (
        "ARTIFACT_BO_EXPLORE_NOISELESS",
        "ARTIFACT_BO_EXPLORE_SMALL_NOISE",
        "ARTIFACT_BO_MULTIFIDELITY_LEDGER",
        "ARTIFACT_BO_LOW_FIDELITY_BIAS",
    )
    assert bayesian_optimization.comparison_ids == (
        "COMPARE_BO_ACQUISITION_NOISE_BASELINE",
        "COMPARE_BO_MULTIFIDELITY_COST",
    )
    assert "#/compare/COMPARE_BO_ACQUISITION_NOISE_BASELINE" in bayesian_optimization.body
    assert "#/compare/COMPARE_BO_MULTIFIDELITY_COST" in bayesian_optimization.body
    assert "個別のsensitivity runとbaselineは比較ページから開けます" in (bayesian_optimization.body)

    family = pages["family.expensive-black-box"]
    assert "#/compare/COMPARE_BO_MULTIFIDELITY_COST" in family.body
    assert style_warnings(family) == ()

    random_search = pages["random-search"]
    assert random_search.visualization_ids == ("ARTIFACT_BO_EXPLORE_NOISELESS_RANDOM_BASELINE",)
    assert random_search.comparison_ids == ("COMPARE_BO_ACQUISITION_NOISE_BASELINE",)
    assert "#/compare/COMPARE_BO_ACQUISITION_NOISE_BASELINE" in random_search.body
    assert "一般的なrankingは決めません" in random_search.body
