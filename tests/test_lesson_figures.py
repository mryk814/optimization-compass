from __future__ import annotations

import re
from pathlib import Path
from xml.etree import ElementTree

from scripts.generate_lesson_figures import (
    OUTPUT,
    WIDTH,
    generate_lesson_figures,
    least_squares_fit,
    least_squares_sse,
)

ROOT = Path(__file__).parents[1]
SVG = "{http://www.w3.org/2000/svg}"


def test_least_squares_figures_use_the_article_numbers() -> None:
    x1, x2, sse = least_squares_fit()
    assert (round(x1, 6), round(x2, 6), round(sse, 6)) == (0.9, 0.9, 0.7)
    assert round(least_squares_sse(0.5, 1.3), 6) == 1.66
    figures = generate_lesson_figures()
    assert "この直線では合計 0.70" in figures["least-squares-residuals.svg"]
    assert "二乗和 1.66" in figures["least-squares-contours.svg"]
    assert figures["least-squares-minimum.svg"].count("0.9 で最小 0.70") == 2


def test_lesson_figures_are_current_and_drawn_at_their_display_width() -> None:
    for name, body in generate_lesson_figures().items():
        assert body == generate_lesson_figures()[name]
        assert (OUTPUT / name).read_text(encoding="utf-8") == body, f"regenerate {name}"
        root = ElementTree.fromstring(body)
        assert root.attrib["width"] == str(WIDTH)
        assert root.attrib["viewBox"].split()[2] == str(WIDTH)
        assert root.find(f"{SVG}title").text and root.find(f"{SVG}desc").text
        # One SVG unit is one CSS pixel on a PC: text stays between tick and body size.
        sizes = [float(size) for size in re.findall(r"font-size:(\d+(?:\.\d+)?)px", body)]
        assert sizes and min(sizes) >= 15 and max(sizes) <= 17


def test_lesson_figures_are_referenced_by_content() -> None:
    corpus = "".join(path.read_text(encoding="utf-8") for path in ROOT.glob("content/**/*.md"))
    for name in generate_lesson_figures():
        assert f"./figures/{name}" in corpus
