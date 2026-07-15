import re
from pathlib import Path

from optimization_compass.content_models import load_content


EXPANDED_METHOD_CONTENT_IDS = {
    "admm",
    "bfgs",
    "branch-and-cut",
    "differential-evolution",
    "dijkstra-astar",
    "direct-collocation",
    "dual-simplex",
    "dynamic-programming",
    "fista",
    "genetic-algorithm",
    "lbfgsb",
    "mads",
    "newton-method",
    "particle-swarm",
    "proximal-gradient",
    "trust-region-newton-cg",
}


def test_major_method_families_have_dense_published_guides() -> None:
    root = Path(__file__).resolve().parents[1]
    pages = {page.content_id: page for page in load_content(root / "content")}

    assert len(pages) >= 28
    assert EXPANDED_METHOD_CONTENT_IDS <= pages.keys()

    for content_id in sorted(EXPANDED_METHOD_CONTENT_IDS):
        page = pages[content_id]
        assert page.status == "published"
        assert page.kind == "method"
        assert page.method_id
        assert len(page.summary) >= 35
        assert len(page.body) >= 1_200
        assert page.source_ids
        assert len(page.toc) >= 4

        python_blocks = re.findall(
            r"^```python\n(.*?)^```$",
            page.body,
            re.MULTILINE | re.DOTALL,
        )
        assert python_blocks, f"{content_id} must include a copyable Python example"
        for index, block in enumerate(python_blocks, start=1):
            compile(block, f"{content_id}:python:{index}", "exec")
