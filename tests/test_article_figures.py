from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree

import pytest

from scripts.generate_article_figures import (
    _finite_horizon_lqr_probe,
    _multiple_shooting_probe,
    _spatial_branch_bound_probe,
    _spatial_interval_lower_bound,
    _spatial_objective,
    generate_article_figures,
    read_dataset_version,
)

ROOT = Path(__file__).parents[1]
VERSION = read_dataset_version()


def test_lqr_probe_matches_the_fixed_article_equations() -> None:
    states, controls, gains = _finite_horizon_lqr_probe()

    assert len(states) == 41
    assert len(controls) == len(gains) == 40
    assert states[-1] == pytest.approx((2.7723676704340833e-05, 3.0156938335117316e-05))
    assert max(abs(value) for value in controls) == pytest.approx(15.208943465016517)
    assert gains[0] == pytest.approx((7.604471732508259, 4.977648136580166))


def test_multiple_shooting_probe_closes_the_fixed_continuity_defects() -> None:
    probe = _multiple_shooting_probe()
    initial = probe["initial"]
    solved = probe["solved"]

    assert isinstance(initial, dict)
    assert isinstance(solved, dict)
    assert initial["vector"] == pytest.approx((0.5, 0.5, 1.5))
    assert initial["defects"] == pytest.approx((-0.25, 0.25))
    assert initial["objective"] == pytest.approx(1.25)
    assert solved["vector"] == pytest.approx((0.5, 1.0, 1.0))
    assert solved["defects"] == pytest.approx((0.0, 0.0), abs=1e-12)
    assert solved["objective"] == pytest.approx(1.0)


def test_spatial_branch_bound_probe_closes_a_valid_interval_gap() -> None:
    probe = _spatial_branch_bound_probe()

    assert probe["best_point"] == pytest.approx(1.0)
    assert probe["best_value"] == pytest.approx(-1.0)
    assert probe["global_bound"] <= probe["best_value"]
    assert 0.0 <= probe["absolute_gap"] <= probe["gap_tolerance"]
    assert probe["explored"] == 70
    assert len(probe["pruned"]) == 25
    assert len(probe["pending"]) == 46


def test_spatial_interval_bound_stays_below_fixed_dense_probes() -> None:
    for lower, upper in ((0.0, 2.0), (0.5, 1.0), (0.75, 1.25), (1.0, 1.5)):
        bound = _spatial_interval_lower_bound(lower, upper)
        sampled_minimum = min(
            _spatial_objective(lower + index / 100 * (upper - lower)) for index in range(101)
        )
        assert bound <= sampled_minimum


def test_article_figures_are_deterministic_and_current() -> None:
    assert "\n" not in VERSION
    first = generate_article_figures(VERSION)
    second = generate_article_figures(VERSION)

    assert first == second
    assert set(first) == {
        "bayesian-optimization-execution.svg",
        "constrained-feasibility-execution.svg",
        "gradient-family-execution.svg",
        "lqr-backward-forward-execution.svg",
        "least-squares-fit-diagnostic.svg",
        "multiple-shooting-continuity-execution.svg",
        "optimal-control-mesh-execution.svg",
        "pareto-preference-execution.svg",
        "portfolio-risk-execution.svg",
        "search-tree-proof-execution.svg",
        "so3-update-diagnostic.svg",
        "spatial-branch-bound-execution.svg",
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
        "content/methods/bayesian-optimization.md": "bayesian-optimization-execution.svg",
        "content/methods/family-expensive-black-box.md": "bayesian-optimization-execution.svg",
        "content/methods/gradient-descent.md": "gradient-family-execution.svg",
        "content/methods/adam.md": "gradient-family-execution.svg",
        "content/methods/momentum-sgd.md": "gradient-family-execution.svg",
        "content/methods/ilqr-ddp.md": "lqr-backward-forward-execution.svg",
        "content/methods/least-squares.md": "least-squares-fit-diagnostic.svg",
        "content/methods/multiple-shooting.md": "multiple-shooting-continuity-execution.svg",
        "content/methods/projected-gradient.md": "so3-update-diagnostic.svg",
        "content/methods/riemannian-gradient.md": "so3-update-diagnostic.svg",
        "content/methods/family-manifold.md": "so3-update-diagnostic.svg",
        "content/methods/nelder-mead.md": "scenario-nm-quadratic/static.svg",
        "content/methods/branch-and-cut.md": "search-tree-proof-execution.svg",
        "content/methods/family-discrete-structure.md": "search-tree-proof-execution.svg",
        "content/methods/spatial-branch-and-bound.md": "spatial-branch-bound-execution.svg",
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
        "content/methods/direct-collocation.md": "optimal-control-mesh-execution.svg",
        "content/methods/family-optimal-control.md": "optimal-control-mesh-execution.svg",
    }

    for relative_path, figure in expected.items():
        source = (ROOT / relative_path).read_text(encoding="utf-8")
        assert figure in source
        closing_marker = source.find("## 次に読む")
        assert source.index(figure) < (closing_marker if closing_marker >= 0 else len(source))
