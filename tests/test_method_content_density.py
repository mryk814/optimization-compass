import re
from pathlib import Path

from optimization_compass.content_models import load_content

MINIMUM_PUBLISHED_METHOD_GUIDES = 26
MINIMUM_SUMMARY_CHARACTERS = 35
MINIMUM_BODY_CHARACTERS = 1_200
MINIMUM_TOC_ENTRIES = 4


def test_all_published_method_guides_meet_the_explanation_floor() -> None:
    root = Path(__file__).resolve().parents[1]
    method_pages = [
        page
        for page in load_content(root / "content")
        if page.status == "published" and page.kind == "method"
    ]

    assert len(method_pages) >= MINIMUM_PUBLISHED_METHOD_GUIDES

    for page in sorted(method_pages, key=lambda item: item.content_id):
        assert page.method_id
        assert len(page.summary) >= MINIMUM_SUMMARY_CHARACTERS
        assert len(page.body) >= MINIMUM_BODY_CHARACTERS
        assert page.source_ids
        assert len(page.toc) >= MINIMUM_TOC_ENTRIES

        python_blocks = re.findall(
            r"^```python\n(.*?)^```$",
            page.body,
            re.MULTILINE | re.DOTALL,
        )
        assert python_blocks, f"{page.content_id} must include a copyable Python example"
        for index, block in enumerate(python_blocks, start=1):
            compile(block, f"{page.content_id}:python:{index}", "exec")
