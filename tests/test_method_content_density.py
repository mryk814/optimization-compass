import re
from dataclasses import replace
from pathlib import Path

import pytest

from optimization_compass.content_models import load_content
from optimization_compass.content_validation import require_published_method_references
from optimization_compass.db import KnowledgeRepository

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

REPRESENTATIVE_INTUITION_METHOD_IDS = {
    "M_BAYESIAN_OPT_GP",
    "M_BFGS",
    "M_BRANCH_CUT",
    "M_GRADIENT_DESCENT",
    "M_INTERIOR_POINT_NLP",
    "M_LBFGSB",
    "M_MADS",
    "M_NELDER_MEAD",
    "M_NEWTON",
    "M_POWELL",
    "M_SLSQP",
    "M_TRUST_NCG",
}

REQUIRED_INTUITION_LABELS = (
    "- **見るもの**:",
    "- **動かすもの**:",
    "- **前進の判断**:",
)

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


def test_representative_methods_open_with_the_intuition_contract() -> None:
    root = Path(__file__).resolve().parents[1]
    pages = {
        page.method_id: page
        for page in load_content(root / "content")
        if page.method_id is not None
    }

    assert len(REPRESENTATIVE_INTUITION_METHOD_IDS) == 12
    assert pages.keys() >= REPRESENTATIVE_INTUITION_METHOD_IDS

    for method_id in sorted(REPRESENTATIVE_INTUITION_METHOD_IDS):
        page = pages[method_id]
        assert page.status == "published"
        assert page.kind == "method"

        headings = [line for line in page.body.splitlines() if line.startswith("## ")]
        assert headings[0] == "## 30秒でつかむ", (
            f"{method_id} must open with the beginner intuition section"
        )

        introduction = page.body.split("## 30秒でつかむ", maxsplit=1)[1].split("\n## ", maxsplit=1)[
            0
        ]
        assert introduction.count("この手法の気持ち") == 1
        for label in REQUIRED_INTUITION_LABELS:
            assert introduction.count(label) == 1, f"{method_id} is missing {label}"
