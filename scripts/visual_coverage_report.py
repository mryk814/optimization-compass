"""Report which published articles a reader can see or move, to pick where a figure helps most.

uv run python scripts/visual_coverage_report.py              # articles without any figure first
uv run python scripts/visual_coverage_report.py --kind method
uv run python scripts/visual_coverage_report.py --ids adam,bfgs
uv run python scripts/visual_coverage_report.py --figure-text  # SVG text size as displayed

Levels (docs/teaching-article-playbook.md §5): ``explorable`` (the reader changes conditions and
the figure recomputes), ``scene`` (a computed 3D scene or Theater replay linked from the body),
``static`` (an SVG/image in the body), ``none``. An article is listed at its highest level.

``--figure-text`` lists every SVG used in an article with the smallest and largest text size a
reader sees, on a PC and at a 375 px phone (353 px of article width). Supporting figures under
``figures/`` are shown at most 440 px wide, execution figures under ``media/`` at most 672 px.
The playbook asks for 12 px or more on the phone and no more than 18 px on the PC (§5.4).
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

from optimization_compass.content_models import ContentPage, load_content

ROOT = Path(__file__).parents[1]
LEVELS = ("none", "static", "scene", "explorable")
_EXPLORABLE = re.compile(r"^::: explorable ", re.MULTILINE)
_SCENE = re.compile(r"\(#/theater/")
_IMAGE = re.compile(r"^!\[", re.MULTILINE)
_SVG_REF = re.compile(r"\]\(\./((?:figures|media)/[^)\s]+\.svg)")
_VIEWBOX_WIDTH = re.compile(r'viewBox="[-\d.]+[\s,]+[-\d.]+[\s,]+([\d.]+)')
_FONT_SIZE = re.compile(r'font-size(?:="|:\s*)([\d.]+)|font:[^;"]*?([\d.]+)px')
PHONE_WIDTH = 353.0
PC_WIDTH = {"figures": 440.0, "media": 672.0}


def visual_level(page: ContentPage) -> str:
    if _EXPLORABLE.search(page.body):
        return "explorable"
    if _SCENE.search(page.body) or page.visualization_ids:
        return "scene"
    if _IMAGE.search(page.body):
        return "static"
    return "none"


def figure_text_rows(pages: list[ContentPage]) -> list[tuple[str, str, str, str]]:
    used = sorted({ref for page in pages for ref in _SVG_REF.findall(page.body)})
    rows = []
    for ref in used:
        svg = (ROOT / "site" / "public" / ref).read_text(encoding="utf-8")
        width_match = _VIEWBOX_WIDTH.search(svg)
        sizes = [float(a or b) for a, b in _FONT_SIZE.findall(svg)]
        if width_match is None or not sizes:
            rows.append(("?", "?", "unknown", ref))
            continue
        width = float(width_match.group(1))
        pc = min(width, PC_WIDTH[ref.split("/")[0]]) / width
        phone = min(width, PHONE_WIDTH) / width
        verdict = "ok" if min(sizes) * phone >= 12 and max(sizes) * pc <= 18 else "fix"
        rows.append(
            (
                f"{min(sizes) * pc:.0f}-{max(sizes) * pc:.0f}px",
                f"{min(sizes) * phone:.0f}-{max(sizes) * phone:.0f}px",
                verdict,
                ref,
            )
        )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--kind", choices=("method", "concept"), help="only this article kind")
    parser.add_argument("--ids", default="", help="comma-separated content IDs")
    parser.add_argument("--figure-text", action="store_true", help="SVG text size as displayed")
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]

    wanted = {item.strip() for item in args.ids.split(",") if item.strip()}
    pages = [
        page
        for page in load_content(ROOT / "content")
        if page.status == "published"
        and (args.kind is None or page.kind == args.kind)
        and (not wanted or page.content_id in wanted)
    ]
    if args.figure_text:
        text_rows = figure_text_rows(pages)
        print("PC        phone     verdict  figure")
        for pc, phone, verdict, ref in text_rows:
            print(f"{pc:<9} {phone:<9} {verdict:<8} {ref}")
        fixes = sum(row[2] != "ok" for row in text_rows)
        print(f"{len(text_rows) - fixes} ok / {fixes} to fix (total {len(text_rows)})")
        return
    rows = sorted(
        ((visual_level(page), page) for page in pages),
        key=lambda row: (LEVELS.index(row[0]), row[1].kind, row[1].content_id),
    )
    for level, page in rows:
        print(f"{level:<10} {page.kind:<8} {page.content_id}  {page.title_ja}")
    counts = Counter(level for level, _ in rows)
    print(" / ".join(f"{level}: {counts[level]}" for level in LEVELS), f"(total {len(rows)})")


if __name__ == "__main__":
    main()
