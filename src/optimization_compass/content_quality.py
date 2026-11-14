"""Correctness checks for published articles.

Articles may take any shape. What is checked is what a reader would trip over: every internal app
link (``#/...``) in a published article must open a page, not the site's "not found" page, and
every formula must render as written. English words glued into Japanese prose are checked in
``language_mixing``. The text size of static SVG figures is measured for review, not enforced.
"""

from __future__ import annotations

import html
import json
import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from optimization_compass.content_markdown import unrenderable_math
from optimization_compass.content_models import ContentPage
from optimization_compass.formulation_atlas import authored_route_ids

# Pages without an ID in the route (site/src/App.tsx).
STATIC_ROUTES = frozenset(
    f"#{route}"
    for route in (
        "/",
        "/map",
        "/formulations",
        "/paths",
        "/diagnose",
        "/theater",
        "/theater/bayesian-optimization",
        "/compare",
        "/gallery",
        "/failures",
        "/sources",
        "/coverage",
        "/data",
        "/learn",
        "/search",
    )
)
# The renderer families LearningSlicePage opens. For any other scenario, /theater/learning/<id>
# shows "not found" (site/src/features/learning-slices/LearningSlicePage.tsx); such scenarios
# open at their own canonical route, usually /traces/<artifact_id>.
LEARNING_SLICE_FAMILIES = frozenset(
    {"feasible_region", "pareto_front", "field_evolution", "assignment_schedule"}
)
_INTERNAL_HREF = re.compile(r'<a href="(#/[^"]*)"')
_LENS_CASES = re.compile(r"ALGORITHM_LENS_CASES\s*=\s*\[([^\]]*)\]")
_SVG_REF = re.compile(r"\]\(\./((?:figures|media)/[^)\s]+\.svg)")
_VIEWBOX_WIDTH = re.compile(r'viewBox="[-\d.]+[\s,]+[-\d.]+[\s,]+([\d.]+)')
_FONT_SIZE = re.compile(r'font-size(?:="|:\s*)([\d.]+)|font:[^;"]*?([\d.]+)px')
# A static figure is shown at most this wide: 440 px for figures/, 672 px for media/ on a PC, and
# 353 px of article width on a 375 px phone. Text should read 12 px or more on the phone and no
# more than 18 px on the PC.
PC_WIDTH = {"figures": 440.0, "media": 672.0}
PHONE_WIDTH = 353.0
MIN_PHONE_TEXT = 12.0
MAX_PC_TEXT = 18.0


@dataclass(frozen=True)
class FigureText:
    """Smallest and largest text size of one static SVG as a reader sees it, in px."""

    path: str
    pc: tuple[float, float] | None
    phone: tuple[float, float] | None

    @property
    def readable(self) -> bool:
        return (
            self.pc is not None
            and self.phone is not None
            and self.phone[0] >= MIN_PHONE_TEXT
            and self.pc[1] <= MAX_PC_TEXT
        )


def public_content_routes(
    pages: Iterable[ContentPage],
    *,
    gallery_ids: Iterable[str] = (),
    comparison_ids: Iterable[str] = (),
    formulation_ids: Iterable[str] = (),
    path_ids: Iterable[str] = (),
) -> frozenset[str]:
    """Return public routes that can be proven from canonical authoring inputs."""
    routes: set[str] = set()
    for page in pages:
        if page.status != "published":
            continue
        routes.add(f"#/learn/{page.content_id}")
        routes.update(f"#{alias}" for alias in page.aliases)
        if page.method_id:
            routes.add(f"#/methods/{page.method_id}")
    routes.update(f"#/gallery/{case_id}" for case_id in gallery_ids)
    routes.update(f"#/compare/{comparison_id}" for comparison_id in comparison_ids)
    # Every problem archetype has a formulation page, with or without an article.
    routes.update(f"#/formulations/{problem_id}" for problem_id in formulation_ids)
    routes.update(f"#/paths/{path_id}" for path_id in path_ids)
    return frozenset(routes)


def site_data_routes(root: Path) -> frozenset[str]:
    """Routes the site resolves by looking an ID up in the data it serves.

    The committed export under ``site/public/data`` is read as it is, so a route that only an
    unexported change adds stays unknown until ``export-site-data`` runs.
    """
    data = root / "site/public/data"
    routes: set[str] = set()
    for entity in _read_json(data / "entity-links.json")["entities"]:
        if entity.get("canonical_url"):
            routes.add(f"#{entity['canonical_url']}")
        routes.update(f"#{alias}" for alias in entity.get("aliases", []))
    traces = _read_json(data / "traces/index.json")["traces"]
    routes.update(f"#/traces/{trace['trace_id']}" for trace in traces)
    trees = {
        item["artifact_id"] for item in _read_json(data / "search-trees/index.json")["artifacts"]
    }
    for scenario in _read_json(data / "visualization-scenarios.json")["scenarios"]:
        family = scenario["artifact"]["renderer_family"]
        if family in LEARNING_SLICE_FAMILIES:
            routes.add(f"#/theater/learning/{scenario['scenario_id']}")
        elif family == "surrogate_uncertainty":
            routes.add(f"#/theater/bayesian-optimization/{scenario['scenario_id']}")
        elif family == "search_tree":
            routes.update(
                f"#/theater/search-tree/{run['artifact_id']}"
                for run in scenario["runs"]
                if run["artifact_id"] in trees
            )
    # Each computed 3D scene has a page (site/src/features/physical-scenes/catalog.ts).
    scenes = root / "site/src/features/physical-scenes/data"
    routes.update(f"#/theater/physical/{path.stem}" for path in scenes.glob("*.json"))
    # Algorithm-lens stages exist only for the cases the site lists; read that list from the site
    # so it is kept in one place.
    lens_source = (root / "site/src/features/theater/theater-routes.ts").read_text(encoding="utf-8")
    lens_cases = _LENS_CASES.search(lens_source)
    if lens_cases is None:
        raise ValueError("theater-routes.ts no longer declares ALGORITHM_LENS_CASES")
    routes.update(
        f"#/theater/lenses/{case_id}" for case_id in re.findall(r'"([^"]+)"', lens_cases[1])
    )
    return frozenset(routes)


def known_public_routes(root: Path, pages: Iterable[ContentPage]) -> frozenset[str]:
    """Every route an article may link to: authored routes, routes in the site data, fixed pages."""
    gallery = _read_json(root / "data/seeds/site_gallery.json")
    comparisons = _read_json(root / "data/seeds/site_comparisons.json")
    formulation_ids, path_ids = authored_route_ids(root)
    authored = public_content_routes(
        pages,
        gallery_ids=(item["case_id"] for item in gallery["cases"]),
        comparison_ids=(item["comparison_id"] for item in comparisons["comparisons"]),
        formulation_ids=formulation_ids,
        path_ids=path_ids,
    )
    return authored | site_data_routes(root) | STATIC_ROUTES


def internal_links(page: ContentPage) -> tuple[str, ...]:
    """Every ``#/...`` link a reader can click in the rendered article, in reading order."""
    return tuple(html.unescape(href) for href in _INTERNAL_HREF.findall(page.html))


def broken_internal_links(page: ContentPage, routes: frozenset[str]) -> tuple[str, ...]:
    """Internal links whose route (without a ``?query``) is not a page the site can show."""
    broken = [link for link in internal_links(page) if link.split("?", 1)[0] not in routes]
    return tuple(dict.fromkeys(broken))


def require_internal_links(pages: Iterable[ContentPage], routes: frozenset[str]) -> None:
    """Reject published articles that link to a page the site cannot show."""
    failures = [
        f"{page.content_id} ({', '.join(broken)})"
        for page in pages
        if page.status == "published" and (broken := broken_internal_links(page, routes))
    ]
    if failures:
        raise ValueError(
            "internal links must open a page the site can show: " + "; ".join(failures)
        )


def require_renderable_math(pages: Iterable[ContentPage]) -> None:
    """Reject published articles with formulas whose rows the site would run into one line."""
    failures = [
        f"{page.content_id} ({' / '.join(formula[:60] for formula in broken)})"
        for page in pages
        if page.status == "published" and (broken := unrenderable_math(page.body))
    ]
    if failures:
        raise ValueError(
            "formulas must render: write rows with cases, array, or matrix environments "
            "(aligned and bare \\\\ or & are shown as one garbled line): " + "; ".join(failures)
        )


def static_svg_paths(page: ContentPage) -> tuple[str, ...]:
    """The static SVG figures an article shows, as paths under ``site/public``."""
    return tuple(sorted(set(_SVG_REF.findall(page.body))))


def figure_text(root: Path, ref: str) -> FigureText:
    """Measure one static SVG; sizes are None when the file or its text sizes are missing."""
    svg_path = root / "site/public" / ref
    svg = svg_path.read_text(encoding="utf-8") if svg_path.is_file() else ""
    width_match = _VIEWBOX_WIDTH.search(svg)
    sizes = [float(a or b) for a, b in _FONT_SIZE.findall(svg)]
    if width_match is None or not sizes:
        return FigureText(ref, None, None)
    width = float(width_match.group(1))
    pc = min(width, PC_WIDTH[ref.split("/")[0]]) / width
    phone = min(width, PHONE_WIDTH) / width
    return FigureText(
        ref, (min(sizes) * pc, max(sizes) * pc), (min(sizes) * phone, max(sizes) * phone)
    )


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))
