"""Check article files without regenerating site data (safe to run while others author).

    uv run python scripts/check_article.py content/concepts/knapsack.md [more.md ...]

Each file is checked against the Markdown sources, the released database, and the committed site
data. Errors (exit code 1): parse errors, unknown source or content IDs, and, in a published
article, internal links that open no page. In a draft the same link problems are warnings.
English words mixed into Japanese prose are listed as warnings.
"""

from __future__ import annotations

import sys
from pathlib import Path

from optimization_compass.content_models import article_kind, load_content, parse_content
from optimization_compass.content_quality import (
    broken_internal_links,
    known_public_routes,
    language_contract_warnings,
)
from optimization_compass.db import KnowledgeRepository

ROOT = Path(__file__).parents[1]


def main(paths: list[str]) -> int:
    if not paths:
        print(__doc__)
        return 2
    pages = load_content(ROOT / "content")
    content_ids = {page.content_id for page in pages}
    routes = known_public_routes(ROOT, [page for page in pages if page.status == "published"])
    repository = KnowledgeRepository(ROOT / "src/optimization_compass/resources/knowledge.sqlite")
    sources = {
        str(row["source_id"]) for row in repository.fetch_all("SELECT source_id FROM sources")
    }

    failed = False
    for name in paths:
        try:
            page = parse_content(Path(name))
        except ValueError as error:
            print(f"{name}: ERROR {error}")
            failed = True
            continue
        errors = [f"unknown source {item}" for item in page.source_ids if item not in sources]
        errors += [
            f"unknown content {item}"
            for item in (*page.prerequisites, *page.related_ids)
            if item not in content_ids
        ]
        problems = [f"link opens no page: {link}" for link in broken_internal_links(page, routes)]
        warnings = [
            f"English word line~{warning.line}: {warning.detail}"
            for warning in language_contract_warnings(page)
        ]
        if page.status == "published":
            errors += problems
        else:
            warnings += problems
        status = "ERROR" if errors else "ok"
        print(f"{page.content_id} [{article_kind(page)}]: {status}, {len(warnings)} warnings")
        for error in errors:
            print(f"  error: {error}")
        for warning in warnings:
            print(f"  warning: {warning}")
        failed = failed or bool(errors)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
