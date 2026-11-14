from __future__ import annotations

import re
from pathlib import Path
from xml.etree import ElementTree

from scripts.generate_lesson_figures import OUTPUT, generate_lesson_figures
from scripts.lesson_figures._svg import WIDTH

ROOT = Path(__file__).parents[2]
SVG = "{http://www.w3.org/2000/svg}"


def test_lesson_figures_are_current_and_drawn_at_their_display_width() -> None:
    again = generate_lesson_figures()
    for name, body in generate_lesson_figures().items():
        assert body == again[name]
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
