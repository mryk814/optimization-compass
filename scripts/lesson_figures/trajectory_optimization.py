"""Trajectory optimization (content/concepts/trajectory-optimization.md): a warehouse robot moves 4
m in 4 s from rest to rest around a pillar. The acceleration u is held constant on each of N
intervals (zero-order hold), so p and v are linear in u and the path between grid points is a known
parabola. Cost: h * sum |u_k|^2. Pillar: centre (2, -0.3), radius 0.8.
"""

from __future__ import annotations

import functools
import math
from collections.abc import Callable, Sequence

from ._numeric import _solve_linear
from ._svg import GRID, INK, LINE, MUTED, POINT, UPDATE, VIOLATION, _open, _polyline, _scale, _text

TRAJ_START, TRAJ_GOAL = (0.0, 0.0), (4.0, 0.0)
TRAJ_PILLAR, TRAJ_RADIUS = (2.0, -0.3), 0.8
TRAJ_T = 4.0


@functools.cache
def traj_solve(n: int, side: float = 1.0) -> tuple[float, tuple[tuple[float, float], ...]]:
    """Augmented Lagrangian with Gauss–Newton steps; returns (cost, u_0..u_{n-1})."""
    h = TRAJ_T / n
    coef = [[h * h * (k - j - 0.5) if j < k else 0.0 for j in range(n)] for k in range(n + 1)]
    size = 2 * n

    def position(u: list[float], k: int) -> tuple[float, float]:
        return (
            TRAJ_START[0] + sum(coef[k][j] * u[j] for j in range(n)),
            TRAJ_START[1] + sum(coef[k][j] * u[n + j] for j in range(n)),
        )

    ends = [
        [*coef[n], *[0.0] * n],
        [*[0.0] * n, *coef[n]],
        [*[h] * n, *[0.0] * n],
        [*[0.0] * n, *[h] * n],
    ]
    target = [TRAJ_GOAL[0] - TRAJ_START[0], TRAJ_GOAL[1] - TRAJ_START[1], 0.0, 0.0]
    # Start from the controls that best follow an arc on the chosen side of the pillar.
    hess = [[2 * h if i == j else 0.0 for j in range(size)] for i in range(size)]
    rhs = [0.0] * size
    for k in range(n + 1):
        arc = (4 * k / n, side * 1.2 * math.sin(math.pi * k / n))
        for d in range(2):
            for i in range(n):
                rhs[d * n + i] += 2 * coef[k][i] * (arc[d] - TRAJ_START[d])
                for j in range(n):
                    hess[d * n + i][d * n + j] += 2 * coef[k][i] * coef[k][j]
    u = _solve_linear(hess, rhs)
    lam_end, lam, mu, last = [0.0] * 4, [0.0] * (n + 1), 10.0, math.inf

    def gaps(u: list[float]) -> list[float]:
        return [
            (px - TRAJ_PILLAR[0]) ** 2 + (py - TRAJ_PILLAR[1]) ** 2 - TRAJ_RADIUS**2
            for px, py in (position(u, k) for k in range(n + 1))
        ]

    def misses(u: list[float]) -> list[float]:
        return [
            sum(r[j] * u[j] for j in range(size)) - t for r, t in zip(ends, target, strict=True)
        ]

    def merit(u: list[float]) -> float:
        value = h * sum(x * x for x in u)
        value += sum(m * e + 0.5 * mu * e * e for m, e in zip(lam_end, misses(u), strict=True))
        for m, g in zip(lam, gaps(u), strict=True):
            value += (max(0.0, m - mu * g) ** 2 - m * m) / (2 * mu)
        return value

    for _ in range(80):
        for _ in range(50):
            grad = [2 * h * x for x in u]
            hess = [[2 * h if i == j else 0.0 for j in range(size)] for i in range(size)]
            rows = [(lam_end[i] + mu * e, ends[i]) for i, e in enumerate(misses(u))]
            for k, g in enumerate(gaps(u)):
                weight = max(0.0, lam[k] - mu * g)
                if weight > 0:
                    px, py = position(u, k)
                    dx, dy = 2 * (px - TRAJ_PILLAR[0]), 2 * (py - TRAJ_PILLAR[1])
                    rows.append(
                        (-weight, [dx * c for c in coef[k][:n]] + [dy * c for c in coef[k][:n]])
                    )
            for scale, row in rows:
                nonzero = [i for i in range(size) if row[i]]
                for i in nonzero:
                    grad[i] += scale * row[i]
                    for j in nonzero:
                        hess[i][j] += mu * row[i] * row[j]
            step = _solve_linear(hess, [-g for g in grad])
            slope = sum(g * s for g, s in zip(grad, step, strict=True))
            base, t = merit(u), 1.0
            while (
                merit([x + t * s for x, s in zip(u, step, strict=True)]) > base + 1e-4 * t * slope
            ):
                t *= 0.5
                if t < 1e-10:
                    break
            u = [x + t * s for x, s in zip(u, step, strict=True)]
            if max(abs(t * s) for s in step) < 1e-12:
                break
        lam_end = [m + mu * e for m, e in zip(lam_end, misses(u), strict=True)]
        lam = [max(0.0, m - mu * g) for m, g in zip(lam, gaps(u), strict=True)]
        violation = max([abs(e) for e in misses(u)] + [max(0.0, -g) for g in gaps(u)])
        if violation < 1e-11:
            break
        if violation > 0.25 * last:
            mu = min(4 * mu, 1e6)
        last = violation
    cost = h * sum(x * x for x in u)
    return cost, tuple((u[j], u[n + j]) for j in range(n))


def traj_states(n: int, side: float = 1.0) -> list[tuple[float, float, float, float]]:
    """(px, py, vx, vy) at the n+1 grid points."""
    h = TRAJ_T / n
    px, py, vx, vy = *TRAJ_START, 0.0, 0.0
    states = [(px, py, vx, vy)]
    for ux, uy in traj_solve(n, side)[1]:
        px, py = px + h * vx + 0.5 * h * h * ux, py + h * vy + 0.5 * h * h * uy
        vx, vy = vx + h * ux, vy + h * uy
        states.append((px, py, vx, vy))
    return states


def traj_path(n: int, side: float = 1.0, samples: int = 40) -> list[tuple[float, float]]:
    """The continuous path: a parabola on each interval, sampled `samples` times."""
    h = TRAJ_T / n
    points = []
    controls = traj_solve(n, side)[1]
    for (px, py, vx, vy), (ux, uy) in zip(traj_states(n, side), controls, strict=False):
        for s in range(samples):
            tau = h * s / samples
            points.append(
                (px + vx * tau + 0.5 * ux * tau * tau, py + vy * tau + 0.5 * uy * tau * tau)
            )
    points.append(TRAJ_GOAL)
    return points


def traj_clearance(points: Sequence[tuple[float, float]]) -> float:
    return min(math.hypot(x - TRAJ_PILLAR[0], y - TRAJ_PILLAR[1]) for x, y in points)


def _traj_floor(
    parts: list[str], top: float, bottom: float
) -> Callable[[float, float], tuple[float, float]]:
    px = _scale(-0.8, 4.8, 50, 410)
    unit = (410 - 50) / 5.6
    mid = (top + bottom) / 2

    def at(x: float, y: float) -> tuple[float, float]:
        return px(x), mid - unit * (y + 0.3)

    cx, cy = at(*TRAJ_PILLAR)
    parts.append(
        f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{unit * TRAJ_RADIUS:.1f}" fill="#e4e7e1" '
        f'stroke="{MUTED}" stroke-width="1.5"/>'
    )
    parts.append(_text(cx, cy + 5, "柱", "tick", "middle"))
    for (x, y), name in ((TRAJ_START, "出発"), (TRAJ_GOAL, "到着")):
        sx, sy = at(x, y)
        parts.append(
            f'<rect x="{sx - 6:.1f}" y="{sy - 6:.1f}" width="12" height="12" fill="{INK}"/>'
        )
        left = x < TRAJ_PILLAR[0]
        parts.append(
            _text(sx + (-12 if left else 12), sy + 5, name, "tick", "end" if left else "start")
        )
    return at


def _traj_paths_svg() -> str:
    above, below = traj_solve(20, 1.0), traj_solve(20, -1.0)
    parts = _open(
        "柱の上を回る経路と、下を回る経路",
        (
            "搬送ロボットが4秒で4m先へ、止まった状態から止まった状態へ動く。時間を20区間に分け、"
            "区間ごとに一定の加速度を決める。"
            f"① 床の上の経路。柱の上を回る経路は加速度の二乗の積分が{above[0]:.2f}、"
            f"下を回る経路は{below[0]:.2f}。"
            "② 時刻ごとの加速度の大きさ。"
        ),
        612,
    )
    parts.append(_text(20, 64, "① 床の上の経路（m）"))
    at = _traj_floor(parts, 80, 330)
    for side, color, dash in ((-1.0, POINT, ' stroke-dasharray="6 4"'), (1.0, UPDATE, "")):
        parts.append(
            _polyline([at(x, y) for x, y in traj_path(20, side)], color, 3).replace(
                "/>", f"{dash}/>"
            )
        )
        for x, y, _, _ in traj_states(20, side):
            sx, sy = at(x, y)
            parts.append(f'<circle cx="{sx:.1f}" cy="{sy:.1f}" r="3.5" fill="{color}"/>')
    parts.append(
        _text(410, 96, f"上を回る：{above[0]:.2f}", anchor="end").replace(
            "<text ", f'<text style="fill:{UPDATE}" '
        )
    )
    parts.append(
        _text(410, 324, f"下を回る：{below[0]:.2f}", anchor="end").replace(
            "<text ", f'<text style="fill:{POINT}" '
        )
    )

    parts.append(_text(20, 380, "② 加速度の大きさ（m/s²）"))
    tx = _scale(0.0, TRAJ_T, 64, 410)
    ay = _scale(0.0, 3.0, 560, 400)
    parts.append(f'<path d="M64 400V560H410" fill="none" stroke="{GRID}"/>')
    for value in (0, 1, 2, 3):
        parts.append(_text(56, ay(value) + 5, str(value), "tick", "end"))
    for value in (0, 1, 2, 3, 4):
        parts.append(_text(tx(value), 580, str(value), "tick", "middle"))
    parts.append(_text(410, 600, "時刻（秒）", "tick", "end"))
    h = TRAJ_T / 20
    for side, color, dash in ((-1.0, POINT, ' stroke-dasharray="6 4"'), (1.0, UPDATE, "")):
        steps = []
        for k, (ux, uy) in enumerate(traj_solve(20, side)[1]):
            size = math.hypot(ux, uy)
            steps += [(tx(k * h), ay(size)), (tx((k + 1) * h), ay(size))]
        parts.append(_polyline(steps, color, 2.5).replace("/>", f"{dash}/>"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


def _traj_grid_svg() -> str:
    coarse_points = traj_path(5)
    depth = TRAJ_RADIUS - traj_clearance(coarse_points)
    nodes = traj_states(5)
    node_gap = min(math.hypot(x - TRAJ_PILLAR[0], y - TRAJ_PILLAR[1]) for x, y, _, _ in nodes)
    counts = (5, 10, 20, 40)
    parts = _open(
        "格子点の外でも、間で柱に入る",
        (
            "① 5区間で解いた経路。6つの格子点はどれも柱の外（柱の中心から"
            f"{node_gap:.2f}m以上）だが、格子点の間の経路は柱に{100 * depth:.0f}cm入る。"
            "② 区間の数ごとの、加速度の二乗の積分。"
            + "、".join(f"{n}区間 {traj_solve(n)[0]:.2f}" for n in counts)
            + "。5区間だけが柱を通り抜けて安くなっている。"
        ),
        600,
    )
    parts.append(_text(20, 64, "① 5区間で解いた経路"))
    at = _traj_floor(parts, 80, 330)
    # The grid nodes where the clearance constraint is active sit exactly on the pillar's edge,
    # and floating-point noise put them on either side depending on the platform's libm. Count
    # the edge as part of the red stretch so the figure is the same on Windows and Linux.
    inside = [
        p
        for p in coarse_points
        if math.hypot(p[0] - TRAJ_PILLAR[0], p[1] - TRAJ_PILLAR[1]) < TRAJ_RADIUS + 1e-9
    ]
    parts.append(_polyline([at(x, y) for x, y in coarse_points], UPDATE, 3))
    parts.append(
        _polyline([at(x, y) for x, y in inside], VIOLATION, 8).replace(
            "/>", ' stroke-linecap="round"/>'
        )
    )
    for x, y, _, _ in nodes:
        sx, sy = at(x, y)
        parts.append(
            f'<circle cx="{sx:.1f}" cy="{sy:.1f}" r="6" fill="#ffffff" '
            f'stroke="{UPDATE}" stroke-width="3"/>'
        )
    parts.append(
        _text(410, 324, f"赤：柱の中（最大{100 * depth:.0f}cm）", anchor="end").replace(
            "<text ", f'<text style="fill:{VIOLATION}" '
        )
    )
    parts.append(_text(20, 380, "② 区間の数と、加速度の二乗の積分"))
    by = _scale(0.0, 4.0, 540, 400)
    parts.append(f'<path d="M100 400V540H410" fill="none" stroke="{GRID}"/>')
    width = (410 - 100) / len(counts)
    for i, n in enumerate(counts):
        cost = traj_solve(n)[0]
        left = 100 + width * i + 14
        color = VIOLATION if n == 5 else LINE
        parts.append(
            f'<rect x="{left:.1f}" y="{by(cost):.1f}" width="{width - 28:.1f}" '
            f'height="{540 - by(cost):.1f}" fill="{color}"/>'
        )
        parts.append(_text(left + (width - 28) / 2, by(cost) - 8, f"{cost:.2f}", "tick", "middle"))
        parts.append(_text(left + (width - 28) / 2, 560, f"{n}区間", "tick", "middle"))
    for value in (0, 2, 4):
        parts.append(_text(92, by(value) + 5, str(value), "tick", "end"))
    parts.append(_text(20, 590, "赤：格子点の間で柱を通り抜ける解", "tick"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


FIGURES: dict[str, Callable[[], str]] = {
    "trajectory-pillar-paths.svg": _traj_paths_svg,
    "trajectory-grid-check.svg": _traj_grid_svg,
}
