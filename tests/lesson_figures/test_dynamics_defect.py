from __future__ import annotations

import json

from scripts.lesson_figures import dynamics_defect as tank
from tests.lesson_figures.article_python import assert_article_prints_its_comments


def _max_defect(plan: tank.Plan, n_sub: int) -> float:
    return float(tank.norms(tank.defects(*plan, n_sub))["max"])


def test_hand_checks_of_the_article() -> None:
    assert round(tank.C, 4) == 1.7718
    assert round(tank.f_d(1.0, 0.0, 1)[0], 4) == 0.4685
    assert round(tank.f_d(0.5, 0.0, 1)[0], 4) == 0.1241
    assert round(0.5 - tank.f_d(0.5, 0.0, 1)[0], 4) == 0.3759


def test_iterates_are_the_ones_the_lesson_steps_describe() -> None:
    plans = tank.iterates(1)
    start = tank.defects(*plans[0], 1)
    assert tank.cost(*plans[0])[0] == 0
    assert round(sum(start) * 1000) == 1911
    assert [round(value, 3) for value in start] == [0.032, 0.376, 0.376, 0.376, 0.376, 0.376]

    assert round(tank.cost(*plans[1])[0], 4) == 7.5595
    assert f"{_max_defect(plans[1], 1):.2e}" == "6.48e-05"
    assert _max_defect(plans[1], 1) > tank.TOL
    assert 1e-8 < _max_defect(plans[2], 1) < 1e-7
    assert 1e-12 < _max_defect(plans[3], 1) < 1e-11

    s, q = plans[3]
    assert round(tank.cost(s, q)[0], 4) == 7.5575
    assert round(sum(q) * tank.DT) == 1856
    assert [round(value, 3) for value in s] == [0.519, 0.486, 0.484, 0.484, 0.483, 0.461]
    assert round(q[0], 3) == 0.168


def test_zero_defect_does_not_follow_the_finely_solved_level() -> None:
    s, q = tank.iterates(1)[-1]
    fine = tank.fine_knots(q)
    assert [round(value, 3) for value in fine] == [1.0, 0.582, 0.536, 0.519, 0.508, 0.499, 0.476]
    gaps = [abs(a - b) for a, b in zip([tank.H0, *s], fine, strict=True)]
    assert round(max(gaps), 3) == 0.063
    assert gaps.index(max(gaps)) == 1

    s5, q5 = tank.iterates(5)[-1]
    assert _max_defect((s5, q5), 5) < 1e-11
    assert round(q5[0], 3) == 0.010
    fine5 = tank.fine_knots(q5)
    assert round(max(abs(a - b) for a, b in zip([tank.H0, *s5], fine5, strict=True)), 3) == 0.012


def test_fixture_holds_the_runs_and_the_cut_check() -> None:
    data = json.loads(tank.dynamics_defect_fixture())
    assert sorted(data["runs"]) == ["1", "2", "5"]
    for run in data["runs"].values():
        assert len(run) == tank.ITERATIONS + 1
        assert all(len(row["s"]) == 7 and len(row["q"]) == 6 for row in run)
    # One segment pumping 1 L/s less opens exactly one 0.300 m gap, at the end of that segment.
    assert sorted(data["check"]["cut"]) == ["2", "3", "4", "5", "6"]
    for segment, norms in data["check"]["cut"].items():
        assert norms["argmax"] == int(segment)
        assert round(norms["max"], 6) == 0.3
        assert round(norms["l2"], 6) == 0.3
    assert tank.FIGURES == {}


def test_article_python_prints_what_its_comments_say() -> None:
    assert_article_prints_its_comments("dynamics-defect")
