"""Shortest path (content/concepts/shortest-path.md): a van from the depot S to the customer T."""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence

from ._svg import GRID, POINT, UPDATE, _open, _text

PATH_NODES = ("S", "A", "B", "C", "T")  # arcs only go forward in this order
# (from, to) -> minutes
PATH_ARCS = {
    ("S", "A"): 2,
    ("S", "B"): 4,
    ("S", "T"): 12,
    ("A", "B"): 5,
    ("A", "T"): 6,
    ("B", "C"): 1,
    ("C", "T"): 2,
}


def path_routes(node: str = "S", seen: tuple[str, ...] = ("S",)) -> list[tuple[str, ...]]:
    """Every route from S to T that visits no node twice."""
    routes = [seen] if node == "T" else []
    for tail, head in PATH_ARCS:
        if tail == node and head not in seen:
            routes += path_routes(head, (*seen, head))
    return routes


def path_total(route: Sequence[str]) -> int:
    return sum(PATH_ARCS[edge] for edge in zip(route, route[1:], strict=False))


def path_distances() -> tuple[dict[str, int], tuple[str, ...]]:
    """Shortest time from S to each node, and the shortest route to T (acyclic: one pass)."""
    dist = {"S": 0}
    pred: dict[str, str] = {}
    for node in PATH_NODES[1:]:
        dist[node], pred[node] = min(
            (dist[tail] + weight, tail)
            for (tail, head), weight in PATH_ARCS.items()
            if head == node
        )
    route = ["T"]
    while route[-1] != "S":
        route.append(pred[route[-1]])
    return dist, tuple(reversed(route))


def path_rules() -> list[tuple[str, tuple[str, ...]]]:
    """Three ways to pick a route: fewest arcs, cheapest next arc at every node, least total."""
    cheapest_first = ("S",)
    while cheapest_first[-1] != "T":
        here = cheapest_first[-1]
        cheapest_first += (
            min(
                (head for tail, head in PATH_ARCS if tail == here), key=lambda h: PATH_ARCS[here, h]
            ),
        )
    routes = path_routes()
    return [
        ("道の数が最少", min(routes, key=lambda r: (len(r), path_total(r)))),
        ("次の道が最安", cheapest_first),
        ("合計が最小", min(routes, key=path_total)),
    ]


def _path_svg() -> str:
    dist, best = path_distances()
    rules = path_rules()
    assert rules[2][1] == best
    parts = _open(
        f"最短の{dist['T']}分は、道が{len(best) - 1}本の経路",
        (
            "拠点Sから客先Tへ向かう、一方通行の7本の道の図です。"
            "辺の数字は所要時間（分）で、各点の d はSからの最短時間です。"
            + "".join(
                f"{name}では{'→'.join(route)}で{path_total(route)}分、"
                for name, route in rules[:-1]
            )
            + f"合計が最小の{'→'.join(best)}は{dist['T']}分です。"
        ),
        520,
    )
    at = {"S": (44, 190), "A": (150, 130), "B": (150, 250), "C": (290, 250), "T": (396, 190)}
    radius = 19
    on_best = set(zip(best, best[1:], strict=False))
    parts.append(
        "<defs>"
        '<marker id="path-head" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="4" '
        f'markerHeight="4" orient="auto"><path d="M0 0L10 5L0 10z" fill="{UPDATE}"/></marker>'
        '<marker id="path-head-quiet" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" '
        f'markerHeight="6" orient="auto"><path d="M0 0L10 5L0 10z" fill="{GRID}"/></marker>'
        "</defs>"
    )
    # weight label anchor (x, y, text-anchor), placed beside each arc
    label = {
        ("S", "A"): (86, 152, "end"),
        ("S", "B"): (86, 238, "end"),
        ("S", "T"): (220, 66, "middle"),
        ("A", "B"): (162, 196, "start"),
        ("A", "T"): (273, 148, "middle"),
        ("B", "C"): (220, 238, "middle"),
        ("C", "T"): (356, 246, "start"),
    }
    for (tail, head), weight in PATH_ARCS.items():
        (x1, y1), (x2, y2) = at[tail], at[head]
        chosen = (tail, head) in on_best
        color, width = (UPDATE, 5) if chosen else (GRID, 2)
        marker = "path-head" if chosen else "path-head-quiet"
        if (tail, head) == ("S", "T"):  # the direct road bends over the others
            ctrl = (220.0, -20.0)
            a = math.hypot(ctrl[0] - x1, ctrl[1] - y1)
            b = math.hypot(x2 - ctrl[0], y2 - ctrl[1])
            sx, sy = x1 + (ctrl[0] - x1) / a * radius, y1 + (ctrl[1] - y1) / a * radius
            ex = x2 - (x2 - ctrl[0]) / b * (radius + 4)
            ey = y2 - (y2 - ctrl[1]) / b * (radius + 4)
            shape = f"M{sx:.1f} {sy:.1f}Q{ctrl[0]:.1f} {ctrl[1]:.1f} {ex:.1f} {ey:.1f}"
        else:
            length = math.hypot(x2 - x1, y2 - y1)
            dx, dy = (x2 - x1) / length, (y2 - y1) / length
            shape = (
                f"M{x1 + dx * radius:.1f} {y1 + dy * radius:.1f}"
                f"L{x2 - dx * (radius + 4):.1f} {y2 - dy * (radius + 4):.1f}"
            )
        parts.append(
            f'<path d="{shape}" fill="none" stroke="{color}" stroke-width="{width}" '
            f'stroke-linecap="round" marker-end="url(#{marker})"/>'
        )
        lx, ly, anchor = label[tail, head]
        parts.append(_text(lx, ly, str(weight), "", anchor))
    below = {"S": (44, 226), "A": (150, 170), "B": (150, 286), "C": (290, 286), "T": (396, 226)}
    for name, (x, y) in at.items():
        stroke = UPDATE if name in best else POINT
        parts.append(
            f'<circle cx="{x}" cy="{y}" r="{radius}" fill="#ffffff" stroke="{stroke}" '
            'stroke-width="2"/>'
        )
        parts.append(_text(x, y + 6, name, "", "middle"))
        parts.append(_text(below[name][0], below[name][1], f"d={dist[name]}", "tick", "middle"))
    parts.append(_text(20, 322, "辺の数字：所要時間（分）　d：Sからの最短時間", "tick"))
    for index, (name, route) in enumerate(rules):
        top = 358 + index * 56
        won = route == best
        style = f' style="fill:{UPDATE}"' if won else ""
        parts.append(_text(20, top, name))
        parts.append(
            f'<text x="420" y="{top}" text-anchor="end"{style}>{path_total(route)}分</text>'
        )
        parts.append(_text(20, top + 22, f"{'→'.join(route)}（道{len(route) - 1}本）", "tick"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


FIGURES: dict[str, Callable[[], str]] = {
    "shortest-path-routes.svg": _path_svg,
}
