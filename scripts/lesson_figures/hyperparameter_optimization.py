"""Hyperparameter optimization (content/concepts/hyperparameter-optimization.md): a ridge polynomial
fit on 30 noisy points; the objective is the 5-fold cross-validation error.

The article's lesson is the explorable `hpo-budget-race`. Python owns the example (the data, the
splits, the random settings, the fresh points); the figure reads the scores from the fixture
written here and only fits the curves it draws.
"""

from __future__ import annotations

import json
import math
import random
import statistics
from collections.abc import Callable, Sequence
from functools import cache
from typing import TypedDict

from ._numeric import _solve_linear

HPO_N = 30
HPO_SIGMA = 0.4
HPO_LOG_LAM = (-6.0, 1.0)
HPO_DEGREES = list(range(2, 16))
HPO_DATA_SEED = 1
HPO_BUDGET = 16
HPO_RANDOM_SEED = 0
HPO_GRID_DEGREES = (2, 6, 11, 15)
HPO_GRID_MID_DEGREES = (3, 7, 10, 14)
# The settings map of the figure: every degree at log10 lambda = -6, -5.5, ..., 1.
HPO_LATTICE_LOG_LAM = [HPO_LOG_LAM[0] + 0.5 * i for i in range(15)]
# Split 0 is the one the article measures with; the others are the lesson's re-measurements.
HPO_SPLITS = 12
# Random runs the reader can switch between; the lesson uses seed 0.
HPO_RACE_SEEDS = 8
# "Fresh" points: same formula, another seed, never used to choose a setting.
HPO_FRESH_SEED = 999
HPO_FRESH_N = 5000


def hpo_data(seed: int = HPO_DATA_SEED, n: int = HPO_N) -> tuple[list[float], list[float]]:
    rng = random.Random(seed)
    xs = [rng.uniform(-1, 1) for _ in range(n)]
    ys = [math.sin(3 * v) + 0.5 * v + HPO_SIGMA * rng.gauss(0, 1) for v in xs]
    return xs, ys


def _legendre_row(x: float, degree: int) -> list[float]:
    row = [1.0, x]
    for n in range(2, degree + 1):
        row.append(((2 * n - 1) * x * row[n - 1] - (n - 1) * row[n - 2]) / n)
    return row[: degree + 1]


def _hpo_fit(xs: Sequence[float], ys: Sequence[float], degree: int, lam: float) -> list[float]:
    rows = [_legendre_row(x, degree) for x in xs]
    size = degree + 1
    gram = [
        [sum(r[i] * r[j] for r in rows) + (len(xs) * lam if i == j else 0.0) for j in range(size)]
        for i in range(size)
    ]
    rhs = [sum(r[i] * y for r, y in zip(rows, ys, strict=True)) for i in range(size)]
    return _solve_linear(gram, rhs)


def hpo_cv_mse(
    xs: Sequence[float],
    ys: Sequence[float],
    degree: int,
    lam: float,
    k: int = 5,
    split_seed: int = 0,
) -> float:
    order = list(range(len(xs)))
    random.Random(split_seed).shuffle(order)
    errors = []
    for i in range(k):
        fold = order[i::k]
        train = [j for j in order if j not in fold]
        w = _hpo_fit([xs[j] for j in train], [ys[j] for j in train], degree, lam)
        squares = [
            (sum(c * b for c, b in zip(w, _legendre_row(xs[j], degree), strict=True)) - ys[j]) ** 2
            for j in fold
        ]
        errors.append(sum(squares) / len(squares))
    return sum(errors) / k


def hpo_random_configs(seed: int = HPO_RANDOM_SEED, n: int = HPO_BUDGET) -> list[tuple[int, float]]:
    rng = random.Random(seed)
    low, high = HPO_LOG_LAM
    return [(rng.choice(HPO_DEGREES), 10.0 ** rng.uniform(low, high)) for _ in range(n)]


def hpo_grid_configs() -> list[tuple[int, float]]:
    low, high = HPO_LOG_LAM
    exponents = [low + (high - low) * i / 3 for i in range(4)]
    return [(d, 10.0**e) for d in HPO_GRID_DEGREES for e in exponents]


def hpo_grid_mid_configs() -> list[tuple[int, float]]:
    """The same 4 x 4 grid moved by half a cell: the centre of each quarter of the range."""
    low, high = HPO_LOG_LAM
    exponents = [low + (high - low) * (i + 0.5) / 4 for i in range(4)]
    return [(d, 10.0**e) for d in HPO_GRID_MID_DEGREES for e in exponents]


class _Cv:
    """`hpo_cv_mse` for many settings on one dataset, with the same arithmetic in the same order.

    A degree-d Legendre row is a prefix of the degree-15 row, so each training set's Gram matrix is
    summed once per split and its top-left block is reused for every degree.
    """

    def __init__(self, xs: Sequence[float], ys: Sequence[float], k: int = 5) -> None:
        self.ys = list(ys)
        self.k = k
        self.size = HPO_DEGREES[-1] + 1
        self.rows = [_legendre_row(x, self.size - 1) for x in xs]
        self._splits: dict[int, list[tuple[list[int], list[list[float]], list[float]]]] = {}

    def _folds(self, split_seed: int) -> list[tuple[list[int], list[list[float]], list[float]]]:
        if split_seed not in self._splits:
            order = list(range(len(self.ys)))
            random.Random(split_seed).shuffle(order)
            folds = []
            for i in range(self.k):
                fold = order[i :: self.k]
                rows = [self.rows[j] for j in order if j not in fold]
                targets = [self.ys[j] for j in order if j not in fold]
                span = range(self.size)
                gram = [[sum(r[a] * r[b] for r in rows) for b in span] for a in span]
                rhs = [sum(r[a] * y for r, y in zip(rows, targets, strict=True)) for a in span]
                folds.append((fold, gram, rhs))
            self._splits[split_seed] = folds
        return self._splits[split_seed]

    def mse(self, degree: int, lam: float, split_seed: int = 0) -> float:
        size = degree + 1
        penalty = (len(self.ys) - len(self.ys) // self.k) * lam
        errors = []
        for fold, gram, rhs in self._folds(split_seed):
            matrix = [
                [gram[a][b] + (penalty if a == b else 0.0) for b in range(size)]
                for a in range(size)
            ]
            w = _solve_linear(matrix, rhs[:size])
            squares = [
                (sum(c * b for c, b in zip(w, self.rows[j], strict=False)) - self.ys[j]) ** 2
                for j in fold
            ]
            errors.append(sum(squares) / len(squares))
        return sum(errors) / self.k


class _Fresh:
    """Mean squared error, on the fresh points, of a curve fitted on a whole dataset.

    The 5000 points enter only through sum(row row^T), sum(row y) and sum(y^2), so one score is a
    quadratic form in the coefficients. A degree-d Legendre row is a prefix of the degree-15 row.
    """

    def __init__(self) -> None:
        xs, ys = hpo_data(HPO_FRESH_SEED, HPO_FRESH_N)
        size = HPO_DEGREES[-1] + 1
        rows = [_legendre_row(x, size - 1) for x in xs]
        self.n = len(ys)
        self.gram = [[sum(r[i] * r[j] for r in rows) for j in range(size)] for i in range(size)]
        self.moment = [sum(r[i] * y for r, y in zip(rows, ys, strict=True)) for i in range(size)]
        self.square = sum(y * y for y in ys)

    def mse(self, xs: Sequence[float], ys: Sequence[float], degree: int, lam: float) -> float:
        w = _hpo_fit(xs, ys, degree, lam)
        size = len(w)
        quadratic = sum(w[i] * self.gram[i][j] * w[j] for i in range(size) for j in range(size))
        cross = sum(c * m for c, m in zip(w, self.moment, strict=False))
        return (quadratic - 2 * cross + self.square) / self.n


def hpo_fresh_mse(degree: int, lam: float) -> float:
    """The fresh-point error of the article's 30-point fit, point by point (checks `_Fresh`)."""
    xs, ys = hpo_data()
    w = _hpo_fit(xs, ys, degree, lam)
    new_x, new_y = hpo_data(HPO_FRESH_SEED, HPO_FRESH_N)
    errors = [
        (sum(c * b for c, b in zip(w, _legendre_row(x, degree), strict=True)) - y) ** 2
        for x, y in zip(new_x, new_y, strict=True)
    ]
    return sum(errors) / len(errors)


class RacePoint(TypedDict):
    d: int
    log_lam: float
    cv: list[float]  # one score per split
    fresh: float


class RaceFit(TypedDict):
    d: int
    log_lam: float
    coef: list[float]


class RaceData(TypedDict):
    x: list[float]
    y: list[float]
    map_cv: list[list[list[float]]]  # [split][degree][log_lam]
    map_fresh: list[list[float]]  # [degree][log_lam]
    grid: list[RacePoint]
    grid_mid: list[RacePoint]
    random: list[list[RacePoint]]  # [seed]
    random_bests_200: list[float]
    fits: list[RaceFit]


@cache
def hpo_race_data() -> RaceData:
    """Everything the lesson shows: the map of scores, the runs of 16, and their re-measurements.

    Scores are unrounded here; `hpo_race_fixture` rounds them for the figure.
    """
    xs, ys = hpo_data()
    fresh = _Fresh()
    cv = _Cv(xs, ys)

    def points(configs: Sequence[tuple[int, float]]) -> list[RacePoint]:
        return [
            {
                "d": d,
                "log_lam": math.log10(lam),
                "cv": [cv.mse(d, lam, s) for s in range(HPO_SPLITS)],
                "fresh": fresh.mse(xs, ys, d, lam),
            }
            for d, lam in configs
        ]

    lattice = [[(d, 10.0**e) for e in HPO_LATTICE_LOG_LAM] for d in HPO_DEGREES]
    return {
        "x": xs,
        "y": ys,
        "map_cv": [
            [[cv.mse(d, lam, s) for d, lam in row] for row in lattice] for s in range(HPO_SPLITS)
        ],
        "map_fresh": [[fresh.mse(xs, ys, d, lam) for d, lam in row] for row in lattice],
        "grid": points(hpo_grid_configs()),
        "grid_mid": points(hpo_grid_mid_configs()),
        "random": [points(hpo_random_configs(seed)) for seed in range(HPO_RACE_SEEDS)],
        "random_bests_200": [
            min(cv.mse(d, lam) for d, lam in hpo_random_configs(seed)) for seed in range(200)
        ],
        # Coefficients of three fits, so that the figure's own ridge fit is checked against this.
        "fits": [
            {"d": d, "log_lam": e, "coef": _hpo_fit(xs, ys, d, 10.0**e)}
            for d, e in ((3, -3.5), (15, -6.0), (15, -1.5))
        ],
    }


def hpo_race_fixture() -> str:
    """JSON text of the race example for the `hpo-budget-race` explorable."""
    data = hpo_race_data()

    # Six decimals: the figure prints three, and rounding a rounded number disagrees with rounding
    # the original only when the original sits within 5e-7 of a tie. Full floats would differ in
    # their last digits between platforms and make `--check` fail (see FAILURES.md).
    def r(value: float) -> float:
        return round(value, 6)

    def points(run: list[RacePoint]) -> list[RacePoint]:
        return [
            {
                "d": p["d"],
                "log_lam": r(p["log_lam"]),
                "cv": [r(v) for v in p["cv"]],
                "fresh": r(p["fresh"]),
            }
            for p in run
        ]

    payload = {
        # Written into the committed fixture as it is: the script that writes the file and
        # the function that computes the data.
        "generated_by": "scripts/generate_lesson_figures.py (hpo_race_data)",
        # The figure fits its curves from these, and a degree-15 fit magnifies input rounding, so
        # the points keep 12 significant digits (the same on every platform).
        "data": {
            "x": [float(f"{v:.12g}") for v in data["x"]],
            "y": [float(f"{v:.12g}") for v in data["y"]],
        },
        "space": {"degrees": HPO_DEGREES, "log_lam": HPO_LATTICE_LOG_LAM},
        "map": {
            "cv": [[[r(v) for v in row] for row in split] for split in data["map_cv"]],
            "fresh": [[r(v) for v in row] for row in data["map_fresh"]],
        },
        "runs": {
            "grid": points(data["grid"]),
            "grid_mid": points(data["grid_mid"]),
            "random": [points(run) for run in data["random"]],
        },
        "random_bests_200": [r(v) for v in data["random_bests_200"]],
        "fits": [
            {"d": f["d"], "log_lam": f["log_lam"], "coef": [float(f"{c:.9g}") for c in f["coef"]]}
            for f in data["fits"]
        ],
    }
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n"


@cache
def hpo_selection_data() -> dict[str, list[tuple[float, float]]]:
    """100 other datasets: the score when chosen, and the score on the fresh points.

    `selected` picks the best of 16 random settings by cross-validation. `fixed` uses one setting
    decided in advance, (degree 3, log10 lambda = -3.5), so nothing is chosen.
    """
    fresh = _Fresh()
    selected, fixed = [], []
    for seed in range(100, 200):
        xs, ys = hpo_data(seed)
        configs = hpo_random_configs(seed + 5000)
        cv = _Cv(xs, ys)
        scores = [cv.mse(d, lam) for d, lam in configs]
        best = min(range(len(configs)), key=lambda i: scores[i])
        selected.append((scores[best], fresh.mse(xs, ys, *configs[best])))
        fixed.append((cv.mse(3, 10.0**-3.5), fresh.mse(xs, ys, 3, 10.0**-3.5)))
    return {"selected": selected, "fixed": fixed}


def hpo_selection_summary(pairs: Sequence[tuple[float, float]]) -> tuple[float, float, int]:
    """Median score when chosen, median score on the fresh points, datasets where fresh is worse."""
    return (
        statistics.median(p[0] for p in pairs),
        statistics.median(p[1] for p in pairs),
        sum(p[1] > p[0] for p in pairs),
    )


# The lesson's explorable replaced this article's static figure.
FIGURES: dict[str, Callable[[], str]] = {}
# Scores of the race explorable, keyed by the path from the repository root.
EXTRA_OUTPUTS: dict[str, Callable[[], str]] = {
    "site/src/features/explorable/figures/hpo-budget-race/fixture.json": hpo_race_fixture,
}
