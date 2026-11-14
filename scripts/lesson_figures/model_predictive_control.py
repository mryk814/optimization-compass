"""MPC (content/concepts/model-predictive-control.md): a cart on a rail with a wall at p = 0."""

from __future__ import annotations

from collections.abc import Callable, Sequence

from ._numeric import _solve_linear
from ._svg import GRID, LINE, MUTED, POINT, UPDATE, _open, _polyline, _scale, _text

MPC_A = ((1.0, 1.0), (0.0, 1.0))
MPC_B = (0.5, 1.0)
MPC_Q = (1.0, 0.1)  # diag(Q); the input weight R is MPC_R
MPC_R = 0.1
MPC_X0 = (3.0, 0.0)


def _mpc_terminal_weight() -> tuple[tuple[float, float], tuple[float, float]]:
    """Solve the discrete algebraic Riccati equation by iterating the recursion."""
    a, b, r = MPC_A, MPC_B, MPC_R
    p = [[MPC_Q[0], 0.0], [0.0, MPC_Q[1]]]
    for _ in range(2000):
        pb = [p[0][0] * b[0] + p[0][1] * b[1], p[1][0] * b[0] + p[1][1] * b[1]]
        gain = r + b[0] * pb[0] + b[1] * pb[1]
        pa = [[sum(p[i][m] * a[m][j] for m in range(2)) for j in range(2)] for i in range(2)]
        bpa = [sum(b[m] * pa[m][j] for m in range(2)) for j in range(2)]
        at_pa = [[sum(a[m][i] * pa[m][j] for m in range(2)) for j in range(2)] for i in range(2)]
        p = [
            [(MPC_Q[i] if i == j else 0.0) + at_pa[i][j] - bpa[i] * bpa[j] / gain for j in range(2)]
            for i in range(2)
        ]
    return (p[0][0], p[0][1]), (p[1][0], p[1][1])


def _mpc_plan(horizon: int, state: tuple[float, float], gain_scale: float = 1.0) -> list[float]:
    """Solve the condensed MPC QP with |u|<=1 and p_k>=0 by ADMM (the OSQP iteration)."""
    n = horizon
    terminal = _mpc_terminal_weight()
    # x_k = free_k + sum_j phi[k][j] u_j  (the model the planner believes in)
    free, phi = [], []
    x = list(state)
    cols = [[0.0, 0.0] for _ in range(n)]
    for k in range(n):
        x = [MPC_A[i][0] * x[0] + MPC_A[i][1] * x[1] for i in range(2)]
        free.append(list(x))
        cols = [[MPC_A[i][0] * c[0] + MPC_A[i][1] * c[1] for i in range(2)] for c in cols]
        cols[k] = [MPC_B[0] * gain_scale, MPC_B[1] * gain_scale]
        phi.append([[cols[j][i] for j in range(n)] for i in range(2)])
    # cost = sum_k x_k' W_k x_k + R u'u,  W_k = diag(Q), the last one is the terminal P
    weights = [((MPC_Q[0], 0.0), (0.0, MPC_Q[1]))] * (n - 1) + [terminal]
    hess = [[0.0] * n for _ in range(n)]
    lin = [0.0] * n
    for k in range(n):
        w = weights[k]
        for a_ in range(n):
            wa = [sum(w[i][m] * phi[k][m][a_] for m in range(2)) for i in range(2)]
            lin[a_] += 2 * sum(wa[i] * free[k][i] for i in range(2))
            for b_ in range(n):
                hess[a_][b_] += 2 * sum(wa[i] * phi[k][i][b_] for i in range(2))
    for j in range(n):
        hess[j][j] += 2 * MPC_R
    # constraints l <= C u <= h : rows 0..n-1 are u_j, rows n.. are p_k = free + phi u
    cmat = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]
    cmat += [phi[k][0] for k in range(n)]
    low = [-1.0] * n + [-free[k][0] for k in range(n)]
    high = [1.0] * n + [1e9] * n
    rho, sigma, alpha = 1.0, 1e-9, 1.6
    m = 2 * n
    system = [
        [
            hess[i][j]
            + (sigma if i == j else 0.0)
            + rho * sum(cmat[r][i] * cmat[r][j] for r in range(m))
            for j in range(n)
        ]
        for i in range(n)
    ]
    inverse = [
        list(col)
        for col in zip(
            *[_solve_linear(system, [1.0 if i == j else 0.0 for i in range(n)]) for j in range(n)],
            strict=True,
        )
    ]
    u, z, y = [0.0] * n, [0.0] * m, [0.0] * m
    for _ in range(60000):
        rhs = [
            sigma * u[i] - lin[i] + sum(cmat[r][i] * (rho * z[r] - y[r]) for r in range(m))
            for i in range(n)
        ]
        u_tilde = [sum(inverse[i][j] * rhs[j] for j in range(n)) for i in range(n)]
        cu = [sum(cmat[r][j] * u_tilde[j] for j in range(n)) for r in range(m)]
        z_tilde = cu
        u_next = [alpha * u_tilde[i] + (1 - alpha) * u[i] for i in range(n)]
        z_relaxed = [alpha * z_tilde[r] + (1 - alpha) * z[r] for r in range(m)]
        z_next = [min(max(z_relaxed[r] + y[r] / rho, low[r]), high[r]) for r in range(m)]
        y = [y[r] + rho * (z_relaxed[r] - z_next[r]) for r in range(m)]
        change = max(abs(a_ - b_) for a_, b_ in zip(u_next, u, strict=True))
        u, z = u_next, z_next
        if change < 1e-13:
            break
    return u


MPC_GAIN_ERROR = 1.3  # the real cart responds 30 % more strongly to the input than the model says
MPC_STEPS = 12


def _mpc_step(state: Sequence[float], u: float, scale: float = 1.0) -> list[float]:
    return [
        MPC_A[i][0] * state[0] + MPC_A[i][1] * state[1] + scale * MPC_B[i] * u for i in range(2)
    ]


def mpc_wall_data() -> dict[str, list[float]]:
    """Positions over 12 steps: the model's plan, the plan run open loop, and receding horizon."""
    plan = _mpc_plan(MPC_STEPS, MPC_X0)
    model, real = [list(MPC_X0)], [list(MPC_X0)]
    for u in plan:
        model.append(_mpc_step(model[-1], u))
        real.append(_mpc_step(real[-1], u, MPC_GAIN_ERROR))
    state, receding = list(MPC_X0), [list(MPC_X0)]
    for _ in range(MPC_STEPS):
        u = _mpc_plan(5, (state[0], state[1]))[0]
        state = _mpc_step(state, u, MPC_GAIN_ERROR)
        receding.append(state)
    return {
        "model": [s[0] for s in model],
        "open_loop": [s[0] for s in real],
        "receding": [s[0] for s in receding],
        "receding_velocity_end": [receding[-1][1]],
    }


def _mpc_wall_svg() -> str:
    data = mpc_wall_data()
    open_loop, receding, model = data["open_loop"], data["receding"], data["model"]
    low = min(open_loop)
    parts = _open(
        "解き直しと壁",
        (
            "台車を位置3から壁（位置0）の手前で止める12歩の計画です。実機の入力の効きは"
            f"モデルの{MPC_GAIN_ERROR}倍とします。計画を解き直さず最後まで実行すると、"
            f"位置が{open_loop[-1]:.2f}まで進んで壁を越えます。毎回5歩先まで解き直すと、"
            f"最小の位置は{min(receding):.3f}で、壁を越えません。"
        ),
        392,
    )
    px = _scale(0.0, MPC_STEPS, 64, 420)
    py = _scale(-1.2, 3.2, 270, 52)
    parts.append(f'<path d="M64 52V270H420" fill="none" stroke="{GRID}"/>')
    for step in (0, 4, 8, 12):
        parts.append(_text(px(step), 292, f"{step}", "tick", "middle"))
    for value in (-1, 0, 1, 2, 3):
        parts.append(_text(56, py(value) + 5, f"{value}", "tick", "end"))
    parts.append(_text(420, 314, "歩数", "tick", "end"))
    parts.append(_text(70, 62, "位置", "tick"))
    parts.append(f'<path d="M64 {py(0):.2f}H420" stroke="{POINT}" stroke-width="5"/>')
    parts.append(_polyline([(px(k), py(v)) for k, v in enumerate(model)], UPDATE, 2))
    parts.append(_polyline([(px(k), py(v)) for k, v in enumerate(open_loop)], MUTED, 3))
    parts.append(_polyline([(px(k), py(v)) for k, v in enumerate(receding)], LINE, 3))
    parts.append(_text(20, 340, "紺：壁（位置0）　橙：モデル上の計画"))
    parts.append(
        _text(20, 364, f"灰：解き直さず実行。12歩後 {open_loop[-1]:.2f}（最小 {low:.2f}）", "note")
    )
    parts.append(_text(20, 388, f"緑：毎回解き直し。最小 {min(receding):.3f}", "note"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


FIGURES: dict[str, Callable[[], str]] = {
    "mpc-wall-receding.svg": _mpc_wall_svg,
}
