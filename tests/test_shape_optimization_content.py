from pathlib import Path

from optimization_compass.content_models import ContentPage, load_content

ROOT = Path(__file__).resolve().parents[1]


def _pages() -> dict[str, ContentPage]:
    return {page.content_id: page for page in load_content(ROOT / "content")}


def test_shape_slice_uses_existing_canonical_entities_and_sources() -> None:
    pages = _pages()

    shape = pages["shape-optimization"]
    failure = pages["geometry-update-failure-modes"]

    assert (shape.canonical_entity_type, shape.canonical_entity_id) == (
        "feature",
        "F_VARIABLE_DOMAIN",
    )
    assert (failure.canonical_entity_type, failure.canonical_entity_id) == (
        "feature",
        "F_STRUCTURE_PDE_CONSTRAINED",
    )
    assert set(shape.source_ids) == {"S054", "S055", "S056", "S101"}
    assert set(failure.source_ids) == {"S054", "S055", "S056", "S101"}


def test_shape_slice_makes_geometry_and_discretization_limits_observable() -> None:
    pages = _pages()
    shape_body = pages["shape-optimization"].body
    failure_body = pages["geometry-update-failure-modes"].body

    for phrase in ("geometry validity", "mesh quality", "state residual", "mesh refinement"):
        assert phrase in shape_body
    for phrase in ("inversion", "負のJacobian", "checkerboard", "mesh dependence"):
        assert phrase in failure_body
    assert "連続体の可行性" in failure_body
    assert "::: warning" in shape_body
    assert "::: warning" in failure_body
