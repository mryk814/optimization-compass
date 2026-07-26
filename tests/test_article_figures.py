from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree

from scripts.generate_article_figures import generate_article_figures, read_dataset_version

ROOT = Path(__file__).parents[1]
VERSION = read_dataset_version()


def test_article_figures_are_deterministic_and_current() -> None:
    assert "\n" not in VERSION
    first = generate_article_figures(VERSION)
    second = generate_article_figures(VERSION)

    assert first == second
    assert set(first) == {
        "constrained-feasibility-execution.svg",
        "gradient-family-execution.svg",
        "pareto-preference-execution.svg",
        "portfolio-risk-execution.svg",
        "search-tree-proof-execution.svg",
        "topology-field-execution.svg",
        "trf-probe-execution.svg",
    }
    for name, payload in first.items():
        assert payload == (ROOT / "site" / "public" / "media" / name).read_bytes()


def test_article_figures_have_accessible_svg_titles_and_execution_provenance() -> None:
    figures = generate_article_figures(VERSION)

    for payload in figures.values():
        root = ElementTree.fromstring(payload)
        namespace = {"svg": "http://www.w3.org/2000/svg"}
        assert root.attrib["role"] == "img"
        assert root.attrib["aria-labelledby"] == "figure-title figure-description"
        assert root.find("svg:title", namespace).text
        assert root.find("svg:desc", namespace).text
        assert "実行生成:" in payload.decode("utf-8")


def test_articles_place_execution_results_before_long_diagnostic_sections() -> None:
    expected = {
        "content/methods/gradient-descent.md": "gradient-family-execution.svg",
        "content/methods/adam.md": "gradient-family-execution.svg",
        "content/methods/momentum-sgd.md": "gradient-family-execution.svg",
        "content/methods/nelder-mead.md": "scenario-nm-quadratic/static.svg",
        "content/methods/branch-and-cut.md": "search-tree-proof-execution.svg",
        "content/methods/family-discrete-structure.md": "search-tree-proof-execution.svg",
        "content/methods/simp-topology.md": "topology-field-execution.svg",
        "content/methods/density-filter.md": "topology-field-execution.svg",
        "content/methods/optimality-criteria-topology.md": "topology-field-execution.svg",
        "content/concepts/topology-optimization.md": "topology-field-execution.svg",
        "content/concepts/chance-risk-contract.md": "portfolio-risk-execution.svg",
        "content/methods/trust-region-reflective.md": "trf-probe-execution.svg",
        "content/methods/constrained-continuous.md": "constrained-feasibility-execution.svg",
        "content/methods/family-constrained-nlp.md": "constrained-feasibility-execution.svg",
        "content/methods/slsqp.md": "constrained-feasibility-execution.svg",
        "content/methods/bfgs.md": "constrained-feasibility-execution.svg",
        "content/methods/weighted-sum.md": "pareto-preference-execution.svg",
    }

    for relative_path, figure in expected.items():
        source = (ROOT / relative_path).read_text(encoding="utf-8")
        assert figure in source
        closing_marker = source.find("## 次に読む")
        assert source.index(figure) < (closing_marker if closing_marker >= 0 else len(source))
