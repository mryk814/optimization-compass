from __future__ import annotations

import json
import math
import statistics

import pytest

from scripts.lesson_figures.hyperparameter_optimization import (
    HPO_DEGREES,
    HPO_FRESH_N,
    HPO_FRESH_SEED,
    HPO_LATTICE_LOG_LAM,
    RacePoint,
    _Cv,
    _Fresh,
    hpo_cv_mse,
    hpo_data,
    hpo_fresh_mse,
    hpo_race_data,
    hpo_race_fixture,
    hpo_selection_data,
    hpo_selection_summary,
)


def _best(points: list[RacePoint], split: int = 0) -> RacePoint:
    return min(points, key=lambda p: p["cv"][split])


def _setting(point: RacePoint) -> tuple[int, float]:
    return point["d"], round(point["log_lam"], 2)


def _so_far(points: list[RacePoint]) -> list[float]:
    return [round(min(p["cv"][0] for p in points[: i + 1]), 3) for i in range(len(points))]


def test_the_shortcuts_compute_the_article_objective() -> None:
    xs, ys = hpo_data()
    cv = _Cv(xs, ys)
    for degree, exponent, split in ((3, -3.5, 0), (15, -6.0, 0), (7, -3.0, 3), (11, 1.0, 11)):
        lam = 10.0**exponent
        assert cv.mse(degree, lam, split) == hpo_cv_mse(xs, ys, degree, lam, split_seed=split)
    fresh = _Fresh()
    for degree, exponent in ((3, -3.5), (15, -6.0)):
        direct = hpo_fresh_mse(degree, 10.0**exponent)
        assert fresh.mse(xs, ys, degree, 10.0**exponent) == pytest.approx(direct, rel=1e-9)


def test_the_noise_on_the_30_points_is_smaller_than_on_the_fresh_points() -> None:
    def noise(seed: int, n: int) -> float:
        xs, ys = hpo_data(seed, n)
        return statistics.mean(
            (y - math.sin(3 * x) - 0.5 * x) ** 2 for x, y in zip(xs, ys, strict=True)
        )

    assert round(noise(1, 30), 3) == 0.124
    assert round(noise(HPO_FRESH_SEED, HPO_FRESH_N), 3) == 0.159


def test_one_evaluation_and_the_map() -> None:
    data = hpo_race_data()
    degree15 = dict(zip(HPO_LATTICE_LOG_LAM, data["map_cv"][0][HPO_DEGREES.index(15)], strict=True))
    assert [round(degree15[e], 3) for e in (-6.0, -1.5, 1.0)] == [4.486, 0.230, 1.079]
    assert min(degree15, key=lambda e: degree15[e]) == -1.5
    cells = {
        (d, e): data["map_cv"][0][i][j]
        for i, d in enumerate(HPO_DEGREES)
        for j, e in enumerate(HPO_LATTICE_LOG_LAM)
    }
    best = min(cells, key=lambda key: cells[key])
    assert (best, round(cells[best], 3), round(max(cells.values()), 3)) == ((3, -3.5), 0.137, 4.486)


def test_the_race_of_16_evaluations() -> None:
    data = hpo_race_data()
    grid, mid, rand = data["grid"], data["grid_mid"], data["random"][0]
    assert _so_far(grid) == [0.267] * 4 + [0.192] * 12
    assert _so_far(rand) == [0.747] + [0.172] * 6 + [0.144] * 9
    assert _so_far(mid) == [0.137] * 16
    assert (_setting(_best(grid)), _setting(_best(rand))) == ((6, -3.67), (3, -1.67))
    assert _setting(_best(mid)) == (3, -3.38)
    for run, kinds in ((grid, (4, 4)), (mid, (4, 4)), (rand, (16, 11))):
        assert (len({p["log_lam"] for p in run}), len({p["d"] for p in run})) == kinds


def test_200_random_runs_spread_between_the_two_grids() -> None:
    bests = hpo_race_data()["random_bests_200"]
    quartiles = statistics.quantiles(bests, n=4, method="inclusive")
    assert [round(q, 3) for q in quartiles] == [0.137, 0.138, 0.160]
    assert (round(min(bests), 3), round(max(bests), 3)) == (0.137, 0.192)
    assert sum(round(b, 3) <= 0.137 for b in bests) == 95


def test_other_splits_move_the_scores_and_the_chosen_setting() -> None:
    data = hpo_race_data()
    grid, rand = data["grid"], data["random"][0]
    chosen = _best(rand)
    assert (round(min(chosen["cv"]), 3), round(max(chosen["cv"]), 3)) == (0.144, 0.177)
    rand_winners = [_setting(_best(rand, s)) for s in range(12)]
    assert sorted((rand_winners.count(w), w) for w in set(rand_winners)) == [
        (1, (4, -3.83)),
        (2, (7, -2.96)),
        (9, (3, -1.67)),
    ]
    grid_winners = [_setting(_best(grid, s)) for s in range(12)]
    assert sorted((grid_winners.count(w), w) for w in set(grid_winners)) == [
        (3, (6, -3.67)),
        (4, (6, -1.33)),
        (5, (11, -1.33)),
    ]
    # In all 12 splits the random run's best score is the smaller one.
    assert all(_best(rand, s)["cv"][s] < _best(grid, s)["cv"][s] for s in range(12))


def test_the_gap_between_the_two_winners_closes_on_fresh_points() -> None:
    data = hpo_race_data()
    grid, rand = _best(data["grid"]), _best(data["random"][0])
    assert (round(grid["cv"][0], 3), round(rand["cv"][0], 3)) == (0.192, 0.144)
    assert (round(grid["fresh"], 3), round(rand["fresh"], 3)) == (0.175, 0.173)
    assert round(grid["cv"][0] - rand["cv"][0], 3) == 0.048
    assert round(grid["fresh"] - rand["fresh"], 3) == 0.002
    fresh_cells = [v for row in data["map_fresh"] for v in row]
    assert round(min(fresh_cells), 3) == 0.170


def test_choosing_makes_the_score_optimistic_and_not_choosing_does_not() -> None:
    data = hpo_selection_data()
    chosen, fresh, worse = hpo_selection_summary(data["selected"])
    assert (round(chosen, 3), round(fresh, 3), worse) == (0.188, 0.198, 64)
    chosen, fresh, worse = hpo_selection_summary(data["fixed"])
    assert (round(chosen, 3), round(fresh, 3), worse) == (0.200, 0.185, 43)
    assert sum(pair[1] < pair[0] for pair in data["fixed"]) == 57


def test_the_fixture_holds_the_same_scores_rounded() -> None:
    data, fixture = hpo_race_data(), json.loads(hpo_race_fixture())
    assert fixture["space"] == {"degrees": HPO_DEGREES, "log_lam": HPO_LATTICE_LOG_LAM}
    assert len(fixture["map"]["cv"]) == 12 and len(fixture["runs"]["random"]) == 8
    assert fixture["map"]["cv"][0][1][5] == round(data["map_cv"][0][1][5], 6)
    assert fixture["runs"]["grid"][5]["fresh"] == round(data["grid"][5]["fresh"], 6)
