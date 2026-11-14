from __future__ import annotations

import re
from pathlib import Path
from types import ModuleType
from xml.etree import ElementTree

import pytest

from scripts import generate_lesson_figures as cli
from scripts.generate_lesson_figures import (
    OUTPUT,
    figure_modules,
    generate_lesson_figures,
    lesson_outputs,
    write_outputs,
)
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


def _module(name: str, **attributes: object) -> ModuleType:
    module = ModuleType(name)
    for key, value in attributes.items():
        setattr(module, key, value)
    return module


def _draw() -> str:
    return ""


def test_every_article_module_is_found_and_the_helpers_are_not() -> None:
    modules = figure_modules()
    found = {module.__name__.rsplit(".", 1)[1] for module in modules}
    files = {path.stem for path in (ROOT / "scripts" / "lesson_figures").glob("*.py")}
    assert found == {stem for stem in files if not stem.startswith("_")}
    assert "inverseProblem.fixture.json" in {path.name for path in lesson_outputs(modules)}


def test_a_new_module_is_found_without_editing_anything(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    package = tmp_path / "fake_lesson_figures"
    package.mkdir()
    (package / "__init__.py").write_text("", encoding="utf-8")
    (package / "_shared.py").write_text("COLOUR = 'red'\n", encoding="utf-8")
    for name in ("zeta", "alpha"):
        (package / f"{name}.py").write_text(
            f"FIGURES = {{'{name}.svg': lambda: '{name}'}}\n", encoding="utf-8"
        )
    monkeypatch.syspath_prepend(tmp_path)
    modules = figure_modules("fake_lesson_figures")
    assert [module.__name__ for module in modules] == [
        "fake_lesson_figures.alpha",
        "fake_lesson_figures.zeta",
    ]
    assert [path.name for path in lesson_outputs(modules)] == ["alpha.svg", "zeta.svg"]


def test_two_modules_that_write_one_file_stop_the_run() -> None:
    first = _module("first", FIGURES={"a.svg": _draw})
    same_name = _module("second", FIGURES={"a.svg": _draw})
    same_path = _module(
        "second", FIGURES={"b.svg": _draw}, EXTRA_OUTPUTS={"site/public/figures/a.svg": _draw}
    )
    for second in (same_name, same_path):
        with pytest.raises(SystemExit, match="a.svg is written by both first and second"):
            lesson_outputs([first, second])


def test_a_module_without_figures_stops_the_run() -> None:
    with pytest.raises(SystemExit, match="helper has no FIGURES"):
        lesson_outputs([_module("helper", COLOUR="red")])


def test_check_names_the_stale_files_and_writes_nothing(tmp_path: Path) -> None:
    current, stale, missing = (tmp_path / name for name in ("a.svg", "b.svg", "c.json"))
    current.write_bytes(b"same\r\n")  # a CRLF checkout of a current file
    stale.write_text("old\n", encoding="utf-8")
    outputs = {current: lambda: "same\n", stale: lambda: "new\n", missing: lambda: "{}\n"}
    assert write_outputs(outputs, check=True) == ["b.svg", "c.json"]
    assert stale.read_text(encoding="utf-8") == "old\n" and not missing.exists()
    assert write_outputs(outputs, check=False) == []
    assert stale.read_bytes() == b"new\n" and missing.read_bytes() == b"{}\n"
    assert write_outputs(outputs, check=True) == []


def test_main_check_fails_until_the_figures_are_written(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    figure = tmp_path / "figure.svg"
    monkeypatch.setattr(cli, "figure_modules", lambda: [])
    monkeypatch.setattr(cli, "lesson_outputs", lambda modules: {figure: lambda: "<svg/>\n"})
    with pytest.raises(SystemExit, match="stale lesson figures: figure.svg"):
        cli.main(["--check"])
    assert not figure.exists()
    cli.main([])
    cli.main(["--check"])
    assert figure.read_text(encoding="utf-8") == "<svg/>\n"
