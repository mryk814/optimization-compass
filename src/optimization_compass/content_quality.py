"""Correctness checks for published articles.

Articles may take any shape. What is checked is what a reader would trip over: every internal app
link (``#/...``) in a published article must open a page, not the site's "not found" page, and
every formula must render as written.
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
_FENCED_CODE_PATTERN = re.compile(r"^```.*?^```$", re.MULTILINE | re.DOTALL)
_DISPLAY_MATH_PATTERN = re.compile(r"^\$\$.*?^\$\$$", re.MULTILINE | re.DOTALL)
_MARKDOWN_LINK_PATTERN = re.compile(r"\[([^\]]+)\]\([^)]+\)")
_BARE_ENGLISH_PARTICLE_PATTERN = re.compile(
    r"\b(?:cost|model|state|design|mesh|solver|tolerance|field|objective|constraint|"
    r"gradient|residual|failure|success|boundary|load|scale|iteration|policy|reason|"
    r"status|update|quality|parameter|geometry|physics|optimization|progress|valid|"
    r"unknown|time|storage)(?:を|は|が|の|に|で|へ|と|も|だけ|した|する|しない|"
    r"まで|から|より)"
)
_GLUED_ENGLISH_PATTERN = re.compile(
    r"(?:statefield|designfield|statevariable|designvariable|"
    r"失敗status|失敗theater|状態field|状態status|設計field|設計status)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class StyleWarning:
    content_id: str
    code: str
    line: int
    detail: str


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


def language_contract_warnings(page: ContentPage) -> tuple[StyleWarning, ...]:
    """Detect clear Japanese/English prose mixing in the article being prepared.

    Canonical English terms, proper names, code, formulas, and identifiers remain allowed.
    This check targets only English ordinary words joined directly to Japanese grammar or
    glued into Japanese compounds.
    """
    body = _FENCED_CODE_PATTERN.sub("", page.body)
    body = _DISPLAY_MATH_PATTERN.sub("", body)
    warnings: list[StyleWarning] = []
    for line_number, raw_line in enumerate(body.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith(("|", ":::", "![")):
            continue
        visible = _MARKDOWN_LINK_PATTERN.sub(r"\1", line)
        visible = re.sub(r"`[^`]+`", "code", visible)
        matches = [
            *_BARE_ENGLISH_PARTICLE_PATTERN.finditer(visible),
            *_GLUED_ENGLISH_PATTERN.finditer(visible),
        ]
        for match in matches:
            warnings.append(
                StyleWarning(
                    page.content_id,
                    "prose.language-mixing",
                    line_number,
                    match.group(0),
                )
            )
    return tuple(warnings)


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))
