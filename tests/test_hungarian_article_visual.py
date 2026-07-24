from __future__ import annotations

from pathlib import Path

from optimization_compass.content_models import load_content


ROOT = Path(__file__).resolve().parents[1]


def test_hungarian_article_links_an_accessible_assignment_figure() -> None:
    pages = load_content(ROOT / "content")
    page = next(item for item in pages if item.content_id == "hungarian-algorithm")

    assert "./media/hungarian-assignment-matrix.svg" in page.body
    assert "各行から一つ、各列から一つ" in page.body
    assert "合計費用5" in page.body

    asset = ROOT / "site/public/media/hungarian-assignment-matrix.svg"
    svg = asset.read_text(encoding="utf-8")
    assert asset.is_file()
    assert '<title id="title">' in svg
    assert '<desc id="desc">' in svg
    assert 'aria-labelledby="title desc"' in svg
