from pathlib import Path

from optimization_compass.content_models import load_content


def test_initial_content_pages_have_frontmatter_and_bodies() -> None:
    root = Path(__file__).resolve().parents[1]
    pages = load_content(root / "content")
    assert {page.content_id for page in pages} == {
        "method.nelder-mead",
        "method.gradient-descent",
        "concept.convexity",
        "concept.derivative-free",
    }
    assert all(page.body for page in pages)
    assert all(page.source_ids for page in pages)
