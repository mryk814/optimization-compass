"""Check article files without regenerating site data (safe to run while others author).

    uv run python scripts/check_article.py content/concepts/knapsack.md [more.md ...]

Each file is checked against the Markdown sources, the released database, and the committed site
data. Errors (exit code 1): parse errors and unknown source or content IDs, and, in a published
article, internal links that open no page, formulas the site cannot render (``aligned`` or a bare
``\\\\`` / ``&`` outside ``cases``/``array``/matrix), and ordinary English words glued into
Japanese prose (``costを``). In a draft those three are warnings.
"""

from __future__ import annotations

import sys
from pathlib import Path

from optimization_compass.content_markdown import unrenderable_math
from optimization_compass.content_models import article_kind, load_content, parse_content
from optimization_compass.content_quality import broken_internal_links, known_public_routes
from optimization_compass.db import KnowledgeRepository
from optimization_compass.language_mixing import article_mixed_words

ROOT = Path(__file__).parents[1]


def main(paths: list[str]) -> int:
    if not paths:
        print(__doc__)
        return 2
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    pages = load_content(ROOT / "content")
    content_ids = {page.content_id for page in pages}
    routes = known_public_routes(ROOT, [page for page in pages if page.status == "published"])
    repository = KnowledgeRepository(ROOT / "src/optimization_compass/resources/knowledge.sqlite")
    sources = {
        str(row["source_id"]) for row in repository.fetch_all("SELECT source_id FROM sources")
    }

    failed = False
    for name in paths:
        path = Path(name)
        try:
            page = parse_content(path)
        except ValueError as error:
            print(f"{name}: ERROR {error}")
            failed = True
            continue
        raw = path.read_text(encoding="utf-8")
        body_offset = raw[: raw.index(page.body)].count("\n")
        errors = [f"unknown source {item}" for item in page.source_ids if item not in sources]
        errors += [
            f"unknown content {item}"
            for item in (*page.prerequisites, *page.related_ids)
            if item not in content_ids
        ]
        problems = [f"link opens no page: {link}" for link in broken_internal_links(page, routes)]
        problems += [f"formula will not render: {tex}" for tex in unrenderable_math(page.body)]
        problems += [
            f"line {body_offset + hit.line}: English word in Japanese prose: {hit.text}"
            for hit in article_mixed_words(page)
        ]
        errors += problems if page.status == "published" else []
        warnings = [] if page.status == "published" else problems
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
