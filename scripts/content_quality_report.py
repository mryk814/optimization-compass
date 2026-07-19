from __future__ import annotations

import argparse
import json
from pathlib import Path

from optimization_compass.content_models import load_content
from optimization_compass.content_quality import (
    inspect_concept,
    public_content_routes,
    render_content_quality_report,
)

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description="Report concept floors and prose warnings.")
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "docs/content-quality-report.md",
    )
    args = parser.parse_args()

    pages = load_content(ROOT / "content")
    gallery = json.loads((ROOT / "data/seeds/site_gallery.json").read_text(encoding="utf-8"))
    comparisons = json.loads(
        (ROOT / "data/seeds/site_comparisons.json").read_text(encoding="utf-8")
    )
    published_pages = [page for page in pages if page.status == "published"]
    routes = public_content_routes(
        published_pages,
        gallery_ids=(item["case_id"] for item in gallery["cases"]),
        comparison_ids=(item["comparison_id"] for item in comparisons["comparisons"]),
    )
    rows = [
        inspect_concept(page, routes)
        for page in pages
        if page.kind == "concept" and page.status == "published"
    ]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        render_content_quality_report(rows, pages),
        encoding="utf-8",
        newline="\n",
    )


if __name__ == "__main__":
    main()
