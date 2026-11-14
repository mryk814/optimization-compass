"""Linear system (content/concepts/linear-system.md): three nodes in a row, nodes 1 and 3 joined to
ground by conductance 1 S, every wire 1 S, 3 A injected at node 1. A x = b with A = [[2, -1, 0],
[-1, 2, -1], [0, -1, 2]] and b = (3, 0, 0).
"""

from __future__ import annotations

from collections.abc import Callable
from fractions import Fraction

from ._svg import INK, LINE, POINT, UPDATE, _open, _text

PA002_MATRIX = ((2, -1, 0), (-1, 2, -1), (0, -1, 2))
PA002_INJECTION = (3, 0, 0)


def _pa002_circuit_data() -> dict[str, object]:
    """Exact node voltages, the elimination pivots and the current in every wire."""
    rows = [
        [Fraction(v) for v in row] + [Fraction(r)]
        for row, r in zip(PA002_MATRIX, PA002_INJECTION, strict=True)
    ]
    pivots: list[Fraction] = []
    for i in range(3):
        pivots.append(rows[i][i])
        for j in range(i + 1, 3):
            factor = rows[j][i] / rows[i][i]
            rows[j] = [a - factor * c for a, c in zip(rows[j], rows[i], strict=True)]
    voltage = [Fraction(0)] * 3
    for i in (2, 1, 0):
        tail = sum(rows[i][j] * voltage[j] for j in range(i + 1, 3))
        voltage[i] = (rows[i][3] - tail) / rows[i][i]
    return {
        "voltage": voltage,
        "pivots": pivots,
        "wire_12": voltage[0] - voltage[1],
        "wire_23": voltage[1] - voltage[2],
        "ground_1": voltage[0],
        "ground_3": voltage[2],
    }


def _pa002_value(value: Fraction) -> str:
    return f"{float(value):g}"


def _pa002_arrow(x: float, y: float, direction: str) -> str:
    if direction == "right":
        points = f"{x - 7:.1f},{y - 6:.1f} {x + 7:.1f},{y:.1f} {x - 7:.1f},{y + 6:.1f}"
    else:
        points = f"{x - 6:.1f},{y - 7:.1f} {x:.1f},{y + 7:.1f} {x + 6:.1f},{y - 7:.1f}"
    return f'<polygon points="{points}" fill="{UPDATE}"/>'


def _pa002_circuit_svg() -> str:
    data = _pa002_circuit_data()
    voltage: list[Fraction] = data["voltage"]  # type: ignore[assignment]
    nodes = (110.0, 235.0, 360.0)
    wire_y, ground_y = 160.0, 290.0
    amps = {
        "w12": _pa002_value(data["wire_12"]),  # type: ignore[arg-type]
        "w23": _pa002_value(data["wire_23"]),  # type: ignore[arg-type]
        "g1": _pa002_value(data["ground_1"]),  # type: ignore[arg-type]
        "g3": _pa002_value(data["ground_3"]),  # type: ignore[arg-type]
    }
    total = _pa002_value(data["ground_1"] + data["ground_3"])  # type: ignore[operator]
    parts = _open(
        "接点の電圧と電流",
        (
            "3つの接点を一列につないだ回路。接点1に外から3 Aを流し込み、"
            "接点1と接点3は接地につながる。"
            f"電圧は接点1が{_pa002_value(voltage[0])} V、接点2が{_pa002_value(voltage[1])} V、"
            f"接点3が{_pa002_value(voltage[2])} V。接点1と接点2の間と接点2と接点3の間を"
            f"それぞれ{amps['w12']} Aが流れ、接地へは接点1から{amps['g1']} A、"
            f"接点3から{amps['g3']} A流れる。"
        ),
        420,
    )
    parts.append(
        f'<line x1="24" y1="{wire_y}" x2="86" y2="{wire_y}" stroke="{UPDATE}" stroke-width="3"/>'
    )
    parts.append(_pa002_arrow(86, wire_y, "right"))
    parts.append(_text(55, wire_y - 14, "3 A", "", "middle"))
    for a, c in ((nodes[0], nodes[1]), (nodes[1], nodes[2])):
        parts.append(
            f'<line x1="{a + 22:.1f}" y1="{wire_y}" x2="{c - 22:.1f}" y2="{wire_y}" '
            f'stroke="{LINE}" stroke-width="3"/>'
        )
        mid = (a + c) / 2
        parts.append(_pa002_arrow(mid, wire_y, "right"))
    parts.append(_text((nodes[0] + nodes[1]) / 2, wire_y - 14, f"{amps['w12']} A", "", "middle"))
    parts.append(_text((nodes[1] + nodes[2]) / 2, wire_y - 14, f"{amps['w23']} A", "", "middle"))
    for x, key in ((nodes[0], "g1"), (nodes[2], "g3")):
        parts.append(
            f'<line x1="{x:.1f}" y1="{wire_y + 22}" x2="{x:.1f}" y2="{ground_y}" '
            f'stroke="{LINE}" stroke-width="3"/>'
        )
        parts.append(_pa002_arrow(x, (wire_y + ground_y) / 2, "down"))
        parts.append(_text(x + 14, (wire_y + ground_y) / 2 + 5, f"{amps[key]} A"))
    parts.append(_text(nodes[1], 240, "接地なし", "tick", "middle"))
    parts.append(
        f'<line x1="70" y1="{ground_y}" x2="400" y2="{ground_y}" stroke="{INK}" stroke-width="3"/>'
    )
    parts.append(_text(235, ground_y + 28, "接地（0 V）", "", "middle"))
    for index, x in enumerate(nodes):
        parts.append(
            f'<circle cx="{x:.1f}" cy="{wire_y}" r="22" fill="#e3eee6" '
            f'stroke="{POINT}" stroke-width="2.5"/>'
        )
        parts.append(_text(x, wire_y + 6, str(index + 1), "", "middle"))
        parts.append(
            _text(
                x, wire_y - 42, f"v{'₁₂₃'[index]} = {_pa002_value(voltage[index])} V", "", "middle"
            )
        )
    parts.append(_text(20, 364, "各抵抗は 1 S。電流 = 電圧差 × 1 S", "note"))
    parts.append(_text(20, 388, f"接点2：流入 {amps['w12']} A、流出 {amps['w23']} A"))
    parts.append(_text(20, 412, f"接地へ：{amps['g1']} + {amps['g3']} = {total} A"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


FIGURES: dict[str, Callable[[], str]] = {
    "linear-system-circuit.svg": _pa002_circuit_svg,
}
