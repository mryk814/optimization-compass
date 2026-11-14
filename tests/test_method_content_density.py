import re
from dataclasses import replace
from pathlib import Path

import pytest

from optimization_compass.content_models import load_content
from optimization_compass.content_validation import require_published_method_references
from optimization_compass.db import KnowledgeRepository

MINIMUM_PUBLISHED_METHOD_GUIDES = 67


def test_published_method_guides_cite_sources_and_ship_valid_python() -> None:
    root = Path(__file__).resolve().parents[1]
    method_pages = [
        page
        for page in load_content(root / "content")
        if page.status == "published" and page.kind == "method"
    ]

    assert len(method_pages) >= MINIMUM_PUBLISHED_METHOD_GUIDES

    for page in sorted(method_pages, key=lambda item: item.content_id):
        assert page.method_id
        assert page.source_ids

        python_blocks = re.findall(
            r"^```python\n(.*?)^```$",
            page.body,
            re.MULTILINE | re.DOTALL,
        )
        for index, block in enumerate(python_blocks, start=1):
            compile(block, f"{page.content_id}:python:{index}", "exec")


def test_published_method_guides_reference_canonical_methods() -> None:
    root = Path(__file__).resolve().parents[1]
    pages = [
        page
        for page in load_content(root / "content")
        if page.status == "published" and page.kind == "method"
    ]
    repository = KnowledgeRepository(root / "src/optimization_compass/resources/knowledge.sqlite")
    known_methods = {
        str(row["method_id"]) for row in repository.fetch_all("SELECT method_id FROM methods")
    }

    require_published_method_references(pages, known_methods)

    invalid_page = replace(pages[0], method_id="M_UNKNOWN_CONTENT_REFERENCE")
    with pytest.raises(
        ValueError,
        match=(
            rf"{re.escape(invalid_page.content_id)} references unknown canonical method: "
            r"M_UNKNOWN_CONTENT_REFERENCE"
        ),
    ):
        require_published_method_references([invalid_page], known_methods)
