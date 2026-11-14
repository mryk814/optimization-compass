"""Dynamics defect (content/concepts/dynamics-defect.md): the tank of the solver series, with the
inflow as the control and the 30 minutes cut into six shooting segments.

    dh/dt [m/s] = (q - C*sqrt(h)) / 1000,   C = 1000*a*sqrt(2g)   (h in m, q in L/s, area 1 m^2)

The variables are the knot levels s_1..s_6 and the flows q_0..q_5 (s_0 = 1 is fixed):

    minimise  J = sum_k ((s_k - 0.5)/0.1)^2 + sum_k q_k^2
    s.t.      d_k = s_k - f_d(s_{k-1}, q_{k-1}) = 0

f_d is explicit Euler with `n_sub` equal substeps per segment. The iterates are those of a
full-step SQP that uses the objective's Hessian only, started from every knot on the target with
the pump off. The explorable `tank-shooting-defect` reads the iterates from the fixture written
here and computes defects, cost and the finely solved level itself (`math.ts`); the fixture's
`check` block holds the same quantities computed here, which the figure's test compares.

Pure Python with only + - * / and sqrt (no pow, exp or log, whose last bits differ between
platforms), and the fixture is rounded, so `--check` gives the same bytes everywhere.
"""

from __future__ import annotations

import json
import math
from collections.abc import Callable

from ._numeric import _solve_linear

G, A_OUT, AREA = 9.81, 0.0004, 1.0
C = 1000 * A_OUT * math.sqrt(2 * G)
DT, N = 300.0, 6
H0, H_TARGET, W = 1.0, 0.5, 0.1
KAPPA = DT / 1000 / AREA  # m of level per (L/s) held for one segment
TOL = 1e-6
ITERATIONS = 4
SUBSTEPS = (1, 2, 5)
FIXTURE_PATH = "site/src/features/explorable/figures/tank-shooting-defect/fixture.json"

Plan = tuple[list[float], list[float]]  # (s_1..s_6, q_0..q_5)


def f_d(s: float, q: float, n_sub: int) -> tuple[float, float, float]:
    """End level of one segment, and its derivatives with respect to s and q."""
    h, dh_ds, dh_dq = s, 1.0, 0.0
    k = KAPPA / n_sub
    for _ in range(n_sub):
        root = math.sqrt(h)
        factor = 1 - k * C / (2 * root)
        dh_ds, dh_dq = dh_ds * factor, dh_dq * factor + k
        h = h + k * (q - C * root)
    return h, dh_ds, dh_dq


def defects(s: list[float], q: list[float], n_sub: int) -> list[float]:
    """d_k for the knots 1..6: the knot minus where the model carries the knot before it."""
    levels = [H0, *s]
    return [levels[k + 1] - f_d(levels[k], q[k], n_sub)[0] for k in range(N)]


def cost(s: list[float], q: list[float]) -> tuple[float, float, float]:
    """(J, tracking part, pump part)."""
    track = sum(((value - H_TARGET) / W) * ((value - H_TARGET) / W) for value in s)
    pump = sum(value * value for value in q)
    return track + pump, track, pump


def sqp_step(s: list[float], q: list[float], n_sub: int) -> Plan:
    """One full step of the equality-constrained SQP (KKT system of the quadratic model)."""
    levels = [H0, *s]
    size = 2 * N
    jac = [[0.0] * size for _ in range(N)]
    for k in range(N):
        _, d_s, d_q = f_d(levels[k], q[k], n_sub)
        jac[k][k] = 1.0
        if k >= 1:
            jac[k][k - 1] = -d_s
        jac[k][N + k] = -d_q
    hess = [2 / (W * W)] * N + [2.0] * N
    grad = [2 * (value - H_TARGET) / (W * W) for value in s] + [2 * value for value in q]
    kkt = [[0.0] * (size + N) for _ in range(size + N)]
    for i in range(size):
        kkt[i][i] = hess[i]
    for k in range(N):
        for i in range(size):
            kkt[size + k][i] = jac[k][i]
            kkt[i][size + k] = jac[k][i]
    rhs = [-value for value in grad] + [-value for value in defects(s, q, n_sub)]
    step = _solve_linear(kkt, rhs)
    return (
        [value + step[i] for i, value in enumerate(s)],
        [value + step[N + i] for i, value in enumerate(q)],
    )


def iterates(n_sub: int) -> list[Plan]:
    """Iterations 0..ITERATIONS from the initial guess: every knot on the target, pump off."""
    s, q = [H_TARGET] * N, [0.0] * N
    out = [(s, q)]
    for _ in range(ITERATIONS):
        s, q = sqp_step(s, q, n_sub)
        out.append((s, q))
    return out


def _rate(h: float, q: float) -> float:
    return (q - C * math.sqrt(max(h, 0.0))) / 1000 / AREA


def fine_knots(q: list[float]) -> list[float]:
    """The continuous model under the same flows (RK4, 1 s steps): levels at 0, 5, ..., 30 min."""
    h, out = H0, [H0]
    for flow in q:
        for _ in range(int(DT)):
            k1 = _rate(h, flow)
            k2 = _rate(h + 0.5 * k1, flow)
            k3 = _rate(h + 0.5 * k2, flow)
            k4 = _rate(h + k3, flow)
            h += (k1 + 2 * k2 + 2 * k3 + k4) / 6
        out.append(h)
    return out


def norms(d: list[float]) -> dict[str, float | int]:
    sizes = [abs(value) for value in d]
    return {
        "max": max(sizes),
        "argmax": sizes.index(max(sizes)) + 1,
        "l2": math.sqrt(sum(value * value for value in d)),
        "total": sum(d),
    }


def _rounded(values: list[float]) -> list[float]:
    # Twelve significant digits, as in inverse_problem.py (see FAILURES.md on full-precision
    # floats in fixtures). Defects below about 1e-12 m are therefore rounding, not the solver.
    return [float(f"{value:.12g}") for value in values]


def _check(value: object) -> object:
    """Check values keep eight digits; the figure's test compares them with a tolerance."""
    if isinstance(value, float):
        return float(f"{value:.8g}")
    if isinstance(value, dict):
        return {key: _check(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_check(item) for item in value]
    return value


def fixture_data() -> dict[str, object]:
    """The iterates of each run, and the quantities the figure must reproduce from them."""
    runs: dict[str, list[dict[str, list[float]]]] = {}
    check_runs: dict[str, object] = {}
    for n_sub in SUBSTEPS:
        plans = [(_rounded(s), _rounded(q)) for s, q in iterates(n_sub)]
        runs[str(n_sub)] = [{"s": [H0, *s], "q": q} for s, q in plans]
        rows = []
        for s, q in plans[:3]:
            total, track, pump = cost(s, q)
            rows.append(
                {"cost": total, "track": track, "pump": pump, **norms(defects(s, q, n_sub))}
            )
        s, q = plans[-1]
        truth = fine_knots(q)
        check_runs[str(n_sub)] = {
            "iterations": rows,
            "final_cost": cost(s, q)[0],
            "pumped_litres": sum(q) * DT,
            "fine_knots": truth,
            "max_gap_to_fine": max(abs(a - b) for a, b in zip([H0, *s], truth, strict=True)),
            "cost_on_fine": cost(truth[1:], q)[0],
        }
    # Step 3 of the n_sub = 1 run, with one segment pumping 1 L/s less and the knots untouched.
    s, q = (_rounded(values) for values in iterates(1)[3])
    cut = {}
    for segment in range(2, N + 1):  # segment 1 is left out: q_0 < 1 L/s would go negative
        flows = [value - 1.0 if k == segment - 1 else value for k, value in enumerate(q)]
        cut[str(segment)] = norms(defects(s, flows, 1))
    return {
        # Written into the committed fixture as it is; changing it changes the fixture's bytes.
        "generated_by": "scripts/generate_lesson_figures.py (dynamics_defect.fixture_data)",
        "constants": {
            "g": G,
            "a": A_OUT,
            "area": AREA,
            "dt": DT,
            "n": N,
            "h0": H0,
            "h_target": H_TARGET,
            "w": W,
            "tol": TOL,
        },
        "runs": runs,
        "check": _check({"C": C, "kappa": KAPPA, "runs": check_runs, "cut": cut}),
    }


def dynamics_defect_fixture() -> str:
    return json.dumps(fixture_data(), ensure_ascii=False, indent=1) + "\n"


# This article's picture is the explorable; it has no static SVG.
FIGURES: dict[str, Callable[[], str]] = {}
EXTRA_OUTPUTS: dict[str, Callable[[], str]] = {FIXTURE_PATH: dynamics_defect_fixture}
