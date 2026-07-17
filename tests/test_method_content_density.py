import re
from pathlib import Path

from optimization_compass.content_models import load_content

MINIMUM_PUBLISHED_METHOD_GUIDES = 67
MINIMUM_SUMMARY_CHARACTERS = 35
MINIMUM_BODY_CHARACTERS = 1_200
MINIMUM_TOC_ENTRIES = 4

BEGINNER_FAMILY_GUIDE_IDS = {
    "family.composite-convex",
    "family.constrained-nlp",
    "family.discrete-structure",
    "family.expensive-black-box",
    "family.global-search",
    "family.local-dfo",
    "family.smooth-local",
    "family.stochastic-ml",
}

BEGINNER_METHOD_TRANCHE_IDS = {
    "adamw",
    "basin-hopping",
    "bundle-method",
    "cobyqa",
    "direct-shooting",
    "epsilon-constraint",
    "gauss-newton",
    "hyperband-asha",
    "moead",
    "newton-cg",
    "nonlinear-cg",
    "nsga-iii",
    "outer-approximation-minlp",
    "spsa",
    "tpe",
    "trust-krylov",
}

REQUIRED_FAMILY_SECTIONS = (
    "## 30秒でつかむ",
    "## まず確認すること",
    "## 条件付きの選び分け",
    "## うまくいったサインと切替サイン",
    "## コラム:",
    "## 次に読む",
)

REQUIRED_BEGINNER_METHOD_SECTIONS = (
    "## 30秒でつかむ",
    "## まず確認すること",
    "## 仕組み",
    "## 向く条件・避ける条件",
    "## うまくいったサインと切替サイン",
    "## Python",
    "## コラム:",
)


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


def test_family_choice_guides_use_the_beginner_first_contract() -> None:
    root = Path(__file__).resolve().parents[1]
    pages = {page.content_id: page for page in load_content(root / "content")}

    assert pages.keys() >= BEGINNER_FAMILY_GUIDE_IDS

    for content_id in sorted(BEGINNER_FAMILY_GUIDE_IDS):
        page = pages[content_id]
        assert page.status == "published"
        assert page.kind == "method"
        assert page.method_id.startswith("MF_")
        for section in REQUIRED_FAMILY_SECTIONS:
            assert section in page.body, f"{content_id} is missing {section}"
        assert "切替" in page.body
        assert "| 役割 | 手法 |" in page.body


def test_second_method_tranche_uses_the_beginner_first_contract() -> None:
    root = Path(__file__).resolve().parents[1]
    pages = {page.content_id: page for page in load_content(root / "content")}

    assert pages.keys() >= BEGINNER_METHOD_TRANCHE_IDS

    for content_id in sorted(BEGINNER_METHOD_TRANCHE_IDS):
        page = pages[content_id]
        assert page.status == "published"
        assert page.kind == "method"
        assert page.method_id.startswith("M_")
        for section in REQUIRED_BEGINNER_METHOD_SECTIONS:
            assert section in page.body, f"{content_id} is missing {section}"
        assert "この手法の気持ち" in page.body
        assert "切替サイン" in page.body
