"""Check article files without regenerating site data (safe to run while others author).

    uv run python scripts/check_article.py content/concepts/knapsack.md [more.md ...]

For each file this reports, from the Markdown sources and the released database only:
parse errors, the section skeleton, the concept publication floor and its "次に読む" links,
unknown source / prerequisite / related IDs, and prose style warnings. Exit code 1 on errors;
style warnings are listed but do not fail the check.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from optimization_compass.content_models import load_content, parse_content
from optimization_compass.content_quality import (
    inspect_concept,
    language_contract_warnings,
    public_content_routes,
    style_warnings,
)
from optimization_compass.content_skeletons import skeleton_gaps, skeleton_kind
from optimization_compass.db import KnowledgeRepository
from optimization_compass.formulation_atlas import authored_route_ids

ROOT = Path(__file__).parents[1]


def main(paths: list[str]) -> int:
    if not paths:
        print(__doc__)
        return 2
    pages = load_content(ROOT / "content")
    published = [page for page in pages if page.status == "published"]
    content_ids = {page.content_id for page in pages}
    gallery = json.loads((ROOT / "data/seeds/site_gallery.json").read_text(encoding="utf-8"))
    comparisons = json.loads(
        (ROOT / "data/seeds/site_comparisons.json").read_text(encoding="utf-8")
    )
    formulation_ids, path_ids = authored_route_ids(ROOT)
    routes = public_content_routes(
        published,
        gallery_ids=(item["case_id"] for item in gallery["cases"]),
        comparison_ids=(item["comparison_id"] for item in comparisons["comparisons"]),
        formulation_ids=formulation_ids,
        path_ids=path_ids,
    )
    repository = KnowledgeRepository(ROOT / "src/optimization_compass/resources/knowledge.sqlite")
    sources = {
        str(row["source_id"]) for row in repository.fetch_all("SELECT source_id FROM sources")
    }

    failed = False
    for name in paths:
        errors: list[str] = []
        try:
            page = parse_content(Path(name))
        except ValueError as error:
            print(f"{name}: ERROR {error}")
            failed = True
            continue
        errors += [f"unknown source {item}" for item in page.source_ids if item not in sources]
        errors += [
            f"unknown content {item}"
            for item in (*page.prerequisites, *page.related_ids)
            if item not in content_ids
        ]
        if skeleton_kind(page) is not None:
            errors += [f"skeleton {gap}" for gap in skeleton_gaps(page)]
        if page.kind == "concept" and page.status == "published":
            row = inspect_concept(page, routes)
            if not row.meets_floor:
                errors.append(
                    f"concept floor (summary={row.summary_characters}, body={row.body_characters}, "
                    f"toc={row.toc_entries}, next={len(row.valid_next_links)}, "
                    f"invalid={','.join(row.invalid_next_links) or '-'})"
                )
        warnings = [*style_warnings(page), *language_contract_warnings(page)]
        status = "ERROR" if errors else "ok"
        kind = skeleton_kind(page) or page.kind
        print(f"{page.content_id} [{kind}]: {status}, {len(warnings)} style warnings")
        for error in errors:
            print(f"  error: {error}")
        for warning in warnings:
            print(f"  style: {warning.code} line~{warning.line}: {warning.detail}")
        failed = failed or bool(errors)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
