from __future__ import annotations

from scripts.lesson_figures.linear_system import FIGURES


def test_linear_system_figure_uses_the_article_numbers() -> None:
    from fractions import Fraction

    from scripts.lesson_figures.linear_system import _pa002_circuit_data

    data = _pa002_circuit_data()
    assert data["voltage"] == [Fraction(9, 4), Fraction(3, 2), Fraction(3, 4)]
    assert data["pivots"] == [Fraction(2), Fraction(3, 2), Fraction(4, 3)]
    # Kirchhoff's current law at every node: what leaves equals what is injected.
    assert (data["ground_1"], data["wire_12"]) == (Fraction(9, 4), Fraction(3, 4))
    assert data["ground_1"] + data["wire_12"] == 3
    assert data["wire_12"] == data["wire_23"] == data["ground_3"]
    figure = FIGURES["linear-system-circuit.svg"]()
    for text in (
        "v₁ = 2.25 V",
        "v₂ = 1.5 V",
        "v₃ = 0.75 V",
        "0.75 A",
        "2.25 A",
        "2.25 + 0.75 = 3 A",
    ):
        assert text in figure
    assert "stroke-dasharray" not in figure
