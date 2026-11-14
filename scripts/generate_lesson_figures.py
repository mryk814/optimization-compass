"""Generate the computed supporting figures that sit next to one formula in a lesson.

uv run python scripts/generate_lesson_figures.py            # write figures and explorable fixture
uv run python scripts/generate_lesson_figures.py --check    # fail if a committed figure is stale

Each article's figures live in one module, scripts/lesson_figures/<article>.py, named after the
article's file (content/concepts/linear-least-squares.md -> linear_least_squares.py). To add an
article's figures, add that module and edit nothing else:

- FIGURES = {"<name>.svg": function returning the SVG text} writes site/public/figures/<name>.svg.
- EXTRA_OUTPUTS = {"<path from the repository root>": function returning the text} writes any
  other file, such as the fixture an explorable reads.
- Its tests go in tests/lesson_figures/test_<article>.py.

This script imports every module of the package except those whose names start with "_", which
hold the shared helpers (_svg.py for drawing, _numeric.py for linear algebra). It stops when two
modules write the same file.
"""

from __future__ import annotations

import argparse
import importlib
import pkgutil
from collections.abc import Callable, Iterable, Sequence
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).parents[1]
OUTPUT = ROOT / "site" / "public" / "figures"
# Run as a file, this script has no package and scripts/ is first on sys.path; the tests import it
# as scripts.generate_lesson_figures. Either way the figure modules import as one package.
PACKAGE = f"{__package__}.lesson_figures" if __package__ else "lesson_figures"


def figure_modules(package: str = PACKAGE) -> list[ModuleType]:
    """Import every module of the package except the shared helpers, in name order."""
    found = pkgutil.iter_modules(importlib.import_module(package).__path__)
    return [
        importlib.import_module(f"{package}.{module.name}")
        for module in sorted(found, key=lambda module: module.name)
        if not module.name.startswith("_")
    ]


def lesson_outputs(modules: Iterable[ModuleType]) -> dict[Path, Callable[[], str]]:
    """Map every output file to the function that draws it; a file has exactly one module."""
    outputs: dict[Path, Callable[[], str]] = {}
    owners: dict[Path, str] = {}
    for module in modules:
        if not hasattr(module, "FIGURES"):
            raise SystemExit(f"{module.__name__} has no FIGURES; prefix a helper module with _")
        extra = getattr(module, "EXTRA_OUTPUTS", {})
        claimed = [(OUTPUT / name, draw) for name, draw in module.FIGURES.items()]
        claimed += [(ROOT / path, draw) for path, draw in extra.items()]
        for path, draw in claimed:
            if path in owners:
                raise SystemExit(
                    f"{path.name} is written by both {owners[path]} and {module.__name__}"
                )
            owners[path] = module.__name__
            outputs[path] = draw
    return outputs


def generate_lesson_figures() -> dict[str, str]:
    """Draw every figure of site/public/figures: file name -> SVG text."""
    outputs = lesson_outputs(figure_modules())
    return {path.name: draw() for path, draw in outputs.items() if path.parent == OUTPUT}


def write_outputs(outputs: dict[Path, Callable[[], str]], *, check: bool) -> list[str]:
    """Write every output, or with check only compare them; return the names of stale files."""
    bodies = {path: draw() for path, draw in outputs.items()}
    stale = []
    for path, body in bodies.items():
        if check:
            # Compared as text, so a checkout with CRLF line ends still matches.
            if not path.exists() or path.read_text(encoding="utf-8") != body:
                stale.append(path.name)
        else:
            path.write_text(body, encoding="utf-8", newline="\n")
    return stale


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="fail if a figure is stale")
    args = parser.parse_args(argv)
    stale = write_outputs(lesson_outputs(figure_modules()), check=args.check)
    if stale:
        raise SystemExit(f"stale lesson figures: {', '.join(stale)}")


if __name__ == "__main__":
    main()
