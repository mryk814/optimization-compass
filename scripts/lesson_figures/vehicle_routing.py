"""Vehicle routing (content/concepts/vehicle-routing.md): depot 0 and seven customers,
two vehicles.
"""

from __future__ import annotations

import itertools
import math
from collections.abc import Callable, Sequence

from ._svg import LINE, POINT, UPDATE, VIOLATION, _open, _polyline, _scale, _text

VRP_XY = ((0, 0), (0, 6), (0, -6), (-2, 2), (1, 0), (6, -2), (1, -1), (3, -3))
VRP_DEMAND = (0, 2, 3, 2, 1, 3, 2, 3)
VRP_CAPACITY = 9


def _vrp_length(route: Sequence[int]) -> float:
    path = [0, *route, 0]
    return sum(math.dist(VRP_XY[a], VRP_XY[b]) for a, b in zip(path, path[1:], strict=False))


def _vrp_nearest_neighbour() -> list[list[int]]:
    left, routes = set(range(1, len(VRP_XY))), []
    while left:
        route, load, here = [], 0, 0
        while True:
            fits = [j for j in left if load + VRP_DEMAND[j] <= VRP_CAPACITY]
            if not fits:
                break
            j = min(fits, key=lambda j: math.dist(VRP_XY[here], VRP_XY[j]))
            route.append(j)
            left.remove(j)
            load, here = load + VRP_DEMAND[j], j
        routes.append(route)
    return routes


def _vrp_two_opt(route: Sequence[int]) -> list[int]:
    best, improved = list(route), True
    while improved:
        improved = False
        for i in range(len(best) - 1):
            for j in range(i + 1, len(best)):
                trial = best[:i] + best[i : j + 1][::-1] + best[j + 1 :]
                if _vrp_length(trial) < _vrp_length(best) - 1e-12:
                    best, improved = trial, True
    return best


def _vrp_degree_only() -> tuple[float, list[list[int]], list[list[int]]]:
    """Minimum-cost successor assignment: every customer in/out once, two depot arcs, no loads.

    The two depot copies are nodes 7 and 8; depot-to-depot arcs are forbidden. Pure Python
    brute force over the 9! successor permutations (the MILP without subtour constraints).
    """
    n = len(VRP_XY)

    def node(i: int) -> int:  # successor-permutation index -> instance node
        return i + 1 if i < n - 1 else 0

    cost = [
        [
            math.inf
            if (a == b or (a >= n - 1 and b >= n - 1))
            else math.dist(VRP_XY[node(a)], VRP_XY[node(b)])
            for b in range(n + 1)
        ]
        for a in range(n + 1)
    ]
    best_cost, best = math.inf, ()
    for perm in itertools.permutations(range(n + 1)):
        total = 0.0
        for a, b in enumerate(perm):
            total += cost[a][b]
            if total >= best_cost:
                break
        else:
            best_cost, best = total, perm
    successor = {node(a): node(b) for a, b in enumerate(best) if a < n - 1}
    starts = [node(b) for a, b in enumerate(best) if a >= n - 1]
    routes, seen = [], set()
    for start in starts:
        route = [start]
        while successor[route[-1]] != 0:
            route.append(successor[route[-1]])
        routes.append(route)
        seen.update(route)
    loops: list[list[int]] = []
    for start in range(1, n):
        if start not in seen:
            loop = [start]
            while successor[loop[-1]] != start:
                loop.append(successor[loop[-1]])
            loops.append(loop)
            seen.update(loop)
    return best_cost, sorted(routes), sorted(loops)


def vrp_data() -> dict[str, object]:
    """Optimum by enumeration, nearest neighbour + 2-opt, and the degree-only relaxation."""
    n = len(VRP_XY)
    best_route: dict[tuple[int, ...], tuple[int, ...]] = {}

    def shortest(members: tuple[int, ...]) -> tuple[int, ...]:
        if members not in best_route:
            best_route[members] = min(itertools.permutations(members), key=_vrp_length)
        return best_route[members]

    splits = []
    for mask in range(1, 2 ** (n - 1) - 1):
        a = tuple(i for i in range(1, n) if mask >> (i - 1) & 1)
        b = tuple(i for i in range(1, n) if not mask >> (i - 1) & 1)
        if a < b and all(sum(VRP_DEMAND[i] for i in s) <= VRP_CAPACITY for s in (a, b)):
            ra, rb = shortest(a), shortest(b)
            splits.append((_vrp_length(ra) + _vrp_length(rb), list(ra), list(rb)))
    splits.sort()
    nearest = _vrp_nearest_neighbour()
    improved = [_vrp_two_opt(route) for route in nearest]
    degree_cost, degree_routes, degree_loops = _vrp_degree_only()
    return {
        "optimum": splits[0][0],
        "optimum_routes": [splits[0][1], splits[0][2]],
        "split_count": len(splits),
        "nearest": sum(_vrp_length(r) for r in nearest),
        "nearest_routes": nearest,
        "heuristic": sum(_vrp_length(r) for r in improved),
        "heuristic_routes": improved,
        "degree_cost": degree_cost,
        "degree_routes": degree_routes,
        "degree_loops": degree_loops,
    }


def _vrp_panel(
    left: float,
    top: float,
    routes: Sequence[Sequence[int]],
    color: str,
    loops: Sequence[Sequence[int]] = (),
) -> list[str]:
    """One map panel, 22 px per unit: depot (navy square), customers (numbered circles)."""
    px = _scale(-2, 6, left + 12, left + 12 + 8 * 22)
    py = _scale(6, -6, top + 12, top + 12 + 12 * 22)
    parts = []
    paths = [([0, *r, 0], color) for r in routes] + [([*lp, lp[0]], VIOLATION) for lp in loops]
    for path, stroke in paths:
        parts.append(_polyline([(px(VRP_XY[i][0]), py(VRP_XY[i][1])) for i in path], stroke, 3))
    x0, y0 = px(0), py(0)
    parts.append(f'<rect x="{x0 - 8:.1f}" y="{y0 - 8:.1f}" width="16" height="16" fill="{POINT}"/>')
    for i in range(1, len(VRP_XY)):
        x, y = px(VRP_XY[i][0]), py(VRP_XY[i][1])
        parts.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="10" fill="#f7f8f3" stroke="{POINT}" '
            'stroke-width="1.5"/>'
        )
        parts.append(_text(x, y + 5.5, str(i), "tick", "middle"))
    return parts


def _vrp_routes_svg() -> str:
    data = vrp_data()
    parts = _open(
        "配送経路：近似と最適",
        (
            "depotと7人の顧客を、容量9の2台で回る配送経路です。最近傍法と2-optの結果は"
            f"{data['heuristic']:.3f}、全探索の最適は{data['optimum']:.3f}で、"
            "2台への顧客の分け方が違います。"
        ),
        448,
    )
    parts += _vrp_panel(14, 96, data["heuristic_routes"], UPDATE)  # type: ignore[arg-type]
    parts += _vrp_panel(226, 96, data["optimum_routes"], LINE)  # type: ignore[arg-type]
    parts.append(_text(20, 56, "最近傍法＋2-opt"))
    parts.append(_text(20, 78, f"{data['heuristic']:.3f}", "note"))
    parts.append(_text(232, 56, "全探索の最適"))
    parts.append(_text(232, 78, f"{data['optimum']:.3f}", "note"))
    parts.append(_text(20, 404, "紺の四角：depot　数字：顧客"))
    parts.append(_text(20, 428, "橙：最近傍法＋2-opt　緑：最適"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


def _vrp_subtour_svg() -> str:
    data = vrp_data()
    loops = data["degree_loops"]
    parts = _open(
        "輪を禁じないと現れる解",
        (
            "各顧客に入る弧と出る弧を1本ずつにして、depotを出る弧を2本にするだけの制約では、"
            f"費用{data['degree_cost']:.3f}の解が選ばれます。depotにつながらない輪が"
            f"{len(loops)}つ残り、実際には回れません。積載の制約を足すと、輪が消えて"  # type: ignore[arg-type]
            f"費用{data['optimum']:.3f}になります。"
        ),
        448,
    )
    parts += _vrp_panel(14, 96, data["degree_routes"], LINE, loops)  # type: ignore[arg-type]
    parts += _vrp_panel(226, 96, data["optimum_routes"], LINE)  # type: ignore[arg-type]
    parts.append(_text(20, 56, "次数の制約だけ"))
    parts.append(_text(20, 78, f"{data['degree_cost']:.3f}", "note"))
    parts.append(_text(232, 56, "積載の制約つき"))
    parts.append(_text(232, 78, f"{data['optimum']:.3f}", "note"))
    parts.append(_text(20, 404, "赤：depotにつながらない輪"))
    parts.append(_text(20, 428, "緑：depotから出る経路　紺の四角：depot"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


FIGURES: dict[str, Callable[[], str]] = {
    "vrp-routes.svg": _vrp_routes_svg,
    "vrp-subtour.svg": _vrp_subtour_svg,
}
