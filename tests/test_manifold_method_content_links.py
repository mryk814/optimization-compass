from pathlib import Path

from optimization_compass.content_models import load_content


def test_manifold_method_guides_link_each_run_and_the_shared_contrast() -> None:
    pages = {page.content_id: page for page in load_content(Path("content"))}
    projected = pages["projected-gradient"]
    riemannian = pages["riemannian-gradient"]

    assert projected.visualization_ids == ("so3-projected-alignment",)
    assert riemannian.visualization_ids == ("so3-riemannian-alignment",)
    for page in (projected, riemannian):
        assert page.comparison_ids == ("COMPARE_SO3_PROJECTED_RIEMANNIAN",)
        assert "#/compare/COMPARE_SO3_PROJECTED_RIEMANNIAN" in page.body
        assert "一般的な速度ranking" in page.body

    assert "#/theater/learning/SCENARIO_SO3_PROJECTED_ALIGNMENT" in projected.body
    assert "#/theater/learning/SCENARIO_SO3_RIEMANNIAN_ALIGNMENT" in riemannian.body
