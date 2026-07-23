from pathlib import Path

from optimization_compass.content_models import load_content


def test_parameter_estimation_guides_link_the_existing_visual_cluster() -> None:
    pages = {page.content_id: page for page in load_content(Path("content"))}

    trf = pages["trust-region-reflective"]
    assert trf.visualization_ids == (
        "exponential-fit-trf",
        "exponential-fit-trf-poor-init",
    )
    assert "#/traces/exponential-fit-trf" in trf.body
    assert "#/traces/exponential-fit-trf-poor-init" in trf.body

    lm = pages["least-squares"]
    assert lm.visualization_ids == ("exponential-fit-lm",)
    assert "#/traces/exponential-fit-lm" in lm.body

    lbfgsb = pages["lbfgsb"]
    assert lbfgsb.visualization_ids == ("exponential-fit-lbfgsb",)
    assert "#/traces/exponential-fit-lbfgsb" in lbfgsb.body

    for page in (trf, lm, lbfgsb):
        assert page.comparison_ids == ("COMPARE_EXPONENTIAL_FIT_SOLVER_CONDITIONS",)
        assert "#/compare/COMPARE_EXPONENTIAL_FIT_SOLVER_CONDITIONS" in page.body
        assert "実行結果ではありません" in page.body
