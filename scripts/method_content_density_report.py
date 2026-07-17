from __future__ import annotations

import argparse
from pathlib import Path

from optimization_compass.content_models import load_content
from optimization_compass.method_content_density import DensityRow, inspect_page, render_report

ROOT = Path(__file__).resolve().parents[1]

__all__ = ["DensityRow", "inspect_page", "render_report"]


def main() -> None:
    parser = argparse.ArgumentParser(description="Report published method-guide content density.")
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "docs/method-content-density-report.md",
    )
    args = parser.parse_args()

    pages = [
        page
        for page in load_content(ROOT / "content")
        if page.status == "published" and page.kind == "method"
    ]
    rows = [inspect_page(page) for page in sorted(pages, key=lambda item: item.content_id)]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_report(rows), encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
