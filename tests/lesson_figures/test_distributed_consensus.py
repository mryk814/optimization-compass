from __future__ import annotations

from scripts.lesson_figures.distributed_consensus import FIGURES


def test_distributed_consensus_figures_use_the_article_numbers() -> None:
    from scripts.lesson_figures.distributed_consensus import (
        DC_RHOS,
        DC_SITES,
        dc_admm,
        dc_global,
        dc_local,
    )

    assert [round(dc_local(s), 2) for s in DC_SITES] == [0.44, 1.22, 0.73]
    assert round(dc_global(), 3) == 0.74
    assert [len(dc_admm(rho)) - 1 for rho in DC_RHOS] == [116, 26, 15, 11, 17, 57, 270]
    first = dc_admm(2.0)[1]
    assert [round(first[0][s], 3) for s in DC_SITES] == [0.267, 0.549, 0.489]
    assert round(first[1], 3) == 0.435
    losses = FIGURES["distributed-consensus-losses.svg"]()
    for text in ("病院A：0.44", "合計の底 0.74", "平均 0.80", "患者の数の重み 0.82"):
        assert text in losses
    admm = FIGURES["distributed-consensus-admm.svg"]()
    for text in ("ρ=2で11回", "116", "270"):
        assert text in admm
