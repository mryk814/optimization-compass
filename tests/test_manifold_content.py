import re
from pathlib import Path

from optimization_compass.content_models import load_content


def test_manifold_concept_covers_existing_geometry_relations() -> None:
    root = Path(__file__).resolve().parents[1]
    pages = {page.content_id: page for page in load_content(root / "content")}

    page = pages["concept.manifold"]
    assert page.kind == "concept"
    assert page.canonical_entity_type == "feature"
    assert page.canonical_entity_id == "F_VARIABLE_MANIFOLD"
    assert {
        "concept.variable-domain",
        "concept.simplex",
        "family.manifold",
        "riemannian-gradient",
        "riemannian-trust-region",
    } <= set(page.related_ids)
    assert {
        "## 直感: 解は曲がった集合の上にある",
        "## Euclidean updateで壊れるもの",
        "## 接空間から集合へ戻す",
        "## 表現の非一意性と特異点",
        "## feasible iterateと収束は別の判定",
        "## 次に読む",
    } <= set(page.body.splitlines())

    python_blocks = re.findall(
        r"^```python\n(.*?)^```$",
        page.body.replace(chr(96), "`"),
        re.MULTILINE | re.DOTALL,
    )
    assert len(python_blocks) == 1
    compile(python_blocks[0], "concept.manifold:python:1", "exec")
