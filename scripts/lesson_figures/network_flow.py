"""Network flow (content/concepts/network-flow.md): four boxes from the factory S to the shop T."""

from __future__ import annotations

import math
from collections.abc import Callable

from ._svg import GRID, POINT, UPDATE, _open, _text

FLOW_NODES = ("S", "A", "B", "T")
# (from, to, cost per box, capacity per day)
FLOW_ARCS = (
    ("S", "A", 1, 3),
    ("S", "B", 4, 3),
    ("A", "B", 1, 3),
    ("A", "T", 5, 2),
    ("B", "T", 1, 3),
)
FLOW_BOXES = 4


def flow_successive_paths(
    boxes: int = FLOW_BOXES, use_reverse: bool = True
) -> list[tuple[str, int, int, dict[tuple[str, str], int]]]:
    """Successive shortest paths on the residual network (Bellman–Ford).

    Returns (path, cost per box, boxes sent, flow after the push) for each push; the list
    stops early when no residual path reaches T.
    """
    flow = {(u, v): 0 for u, v, _, _ in FLOW_ARCS}
    pushes: list[tuple[str, int, int, dict[tuple[str, str], int]]] = []
    sent = 0
    while sent < boxes:
        residual = []
        for u, v, cost, cap in FLOW_ARCS:
            if flow[u, v] < cap:
                residual.append((u, v, cost, cap - flow[u, v], (u, v), 1))
            if use_reverse and flow[u, v] > 0:
                residual.append((v, u, -cost, flow[u, v], (u, v), -1))
        dist: dict[str, float] = {n: math.inf for n in FLOW_NODES}
        dist["S"] = 0
        pred: dict[str, tuple[str, int, tuple[str, str], int]] = {}
        for _ in FLOW_NODES:
            for u, v, cost, left, arc, sign in residual:
                if dist[u] + cost < dist[v]:
                    dist[v], pred[v] = dist[u] + cost, (u, left, arc, sign)
        if dist["T"] == math.inf:
            break
        path, amount, node = ["T"], boxes - sent, "T"
        while node != "S":
            u, left, _, _ = pred[node]
            amount, node = min(amount, left), u
            path.insert(0, node)
        node = "T"
        while node != "S":
            u, _, arc, sign = pred[node]
            flow[arc] += sign * amount
            node = u
        sent += amount
        pushes.append(("→".join(path), int(dist["T"]), amount, dict(flow)))
    return pushes


def flow_cost(flow: dict[tuple[str, str], int]) -> int:
    return sum(cost * flow[u, v] for u, v, cost, _ in FLOW_ARCS)


def _flow_panel(top: float, flow: dict[tuple[str, str], int]) -> list[str]:
    """One network panel: arcs drawn thicker with more boxes, labelled flow/capacity and cost."""
    at = {"S": (44, top + 92), "A": (220, top + 26), "B": (220, top + 158), "T": (396, top + 92)}
    # label anchor (x, y, text-anchor) for each arc, placed beside its middle
    label = {
        ("S", "A"): (122, top + 34, "middle"),
        ("S", "B"): (122, top + 166, "middle"),
        ("A", "B"): (232, top + 86, "start"),
        ("A", "T"): (318, top + 34, "middle"),
        ("B", "T"): (318, top + 166, "middle"),
    }
    parts = []
    radius = 19
    for u, v, cost, cap in FLOW_ARCS:
        (x1, y1), (x2, y2) = at[u], at[v]
        length = math.hypot(x2 - x1, y2 - y1)
        dx, dy = (x2 - x1) / length, (y2 - y1) / length
        sx, sy = x1 + dx * radius, y1 + dy * radius
        ex, ey = x2 - dx * (radius + 4), y2 - dy * (radius + 4)
        boxes = flow[u, v]
        color = UPDATE if boxes else GRID
        width = 2 + 2.5 * boxes
        marker = "flow-head" if boxes else "flow-head-empty"
        parts.append(
            f'<path d="M{sx:.1f} {sy:.1f}L{ex:.1f} {ey:.1f}" stroke="{color}" '
            f'stroke-width="{width:g}" stroke-linecap="round" marker-end="url(#{marker})"/>'
        )
        lx, ly, anchor = label[u, v]
        full = "（満杯）" if boxes == cap else ""
        parts.append(_text(lx, ly, f"{boxes}/{cap}{full}", "", anchor))
        parts.append(_text(lx, ly + 19, f"運賃{cost}", "tick", anchor))
    for name, (x, y) in at.items():
        parts.append(
            f'<circle cx="{x}" cy="{y:.1f}" r="{radius}" fill="#ffffff" stroke="{POINT}" '
            'stroke-width="2"/>'
        )
        parts.append(_text(x, y + 6, name, "", "middle"))
    return parts


def _network_flow_svg() -> str:
    pushes = flow_successive_paths()
    first, last = pushes[0], pushes[-1]
    first_cost, total = first[1] * first[2], flow_cost(last[3])
    parts = _open(
        "4箱目は、A→Bを1箱戻して通す",
        (
            f"工場Sから店Tへ{FLOW_BOXES}箱を送る最小費用流です。"
            "各辺の数字は流量/容量と1箱の運賃です。"
            f"最安の経路{first[0]}（1箱{first[1]}）に{first[2]}箱を送ると費用{first_cost}で、"
            "S→AとB→Tが満杯になります。"
            f"4箱目は{last[0]}を通り、A→Bの流れを1箱減らします。"
            f"1箱の運賃は4−1+5={last[1]}で、合計は{total}です。"
        ),
        576,
    )
    parts.append(
        "<defs>"
        f'<marker id="flow-head" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="4" '
        f'markerHeight="4" orient="auto"><path d="M0 0L10 5L0 10z" fill="{UPDATE}"/></marker>'
        f'<marker id="flow-head-empty" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" '
        f'markerHeight="6" orient="auto"><path d="M0 0L10 5L0 10z" fill="{GRID}"/></marker>'
        "</defs>"
    )
    parts.append(_text(20, 64, f"① 最安の経路に{first[2]}箱"))
    parts.append(_text(420, 64, f"費用 {first_cost}", "note", "end"))
    parts += _flow_panel(74, first[3])
    parts.append(_text(20, 304, f"② 4箱目は {last[0]}"))
    parts.append(_text(420, 304, f"費用 {total}", "note", "end"))
    parts += _flow_panel(314, last[3])
    parts.append(_text(20, 536, "辺の数字：流量/容量　橙が太いほど多く流す"))
    parts.append(_text(20, 560, f"4箱目の運賃 4−1+5={last[1]}（A→Bは1箱戻す）", "note"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


FIGURES: dict[str, Callable[[], str]] = {
    "network-flow-paths.svg": _network_flow_svg,
}
