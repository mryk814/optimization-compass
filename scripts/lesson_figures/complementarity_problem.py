"""Linear complementarity problem (content/concepts/complementarity-problem.md): a plate on two
floor points. w = q + M z, z >= 0, w >= 0, z_i w_i = 0 for each of the two contact points.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from fractions import Fraction

from ._svg import INK, LINE, POINT, RING, UPDATE, _open, _polyline, _scale, _text

LCP_M = ((Fraction(2), Fraction(1)), (Fraction(1), Fraction(2)))
LCP_Q = (Fraction(-1), Fraction(-3, 2))


def _lcp_solve_set(
    matrix: Sequence[Sequence[Fraction]], q: Sequence[Fraction], active: Sequence[int]
) -> tuple[list[Fraction], list[Fraction]]:
    """Exact (z, w) for one complementary choice: w_i = 0 on `active`, z_i = 0 elsewhere."""
    z = [Fraction(0), Fraction(0)]
    if len(active) == 1:
        i = active[0]
        z[i] = -q[i] / matrix[i][i]
    elif len(active) == 2:
        det = matrix[0][0] * matrix[1][1] - matrix[0][1] * matrix[1][0]
        z[0] = (-q[0] * matrix[1][1] + q[1] * matrix[0][1]) / det
        z[1] = (-q[1] * matrix[0][0] + q[0] * matrix[1][0]) / det
    w = [q[i] + sum(matrix[i][j] * z[j] for j in range(2)) for i in range(2)]
    return z, w


def lcp_contact_data() -> list[dict[str, object]]:
    """The four complementary active sets of the contact example and whether each is a solution."""
    rows: list[dict[str, object]] = []
    for active in ((), (0,), (1,), (0, 1)):
        z, w = _lcp_solve_set(LCP_M, LCP_Q, active)
        rows.append({"active": active, "z": z, "w": w, "ok": min(z + w) >= 0})
    return rows


def _lcp_number(value: Fraction) -> str:
    if value.denominator == 1:
        return str(value.numerator)
    return f"{float(value):.3f}".rstrip("0")


def _lcp_contact_svg() -> str:
    rows = lcp_contact_data()
    lower, upper = (0.0, 0.0), (0.65, 1.05)  # z1 and z2 range of the plot window
    left, right, top, bottom = 62, 416, 58, 340
    sx = _scale(lower[0], upper[0], left, right)
    sy = _scale(lower[1], upper[1], bottom, top)
    q1, q2 = float(LCP_Q[0]), float(LCP_Q[1])
    # w1 = q1 + 2 z1 + z2 = 0 and w2 = q2 + z1 + 2 z2 = 0 as lines z2 = f(z1).
    line1 = lambda z1: -(q1 + float(LCP_M[0][0]) * z1) / float(LCP_M[0][1])  # noqa: E731
    line2 = lambda z1: -(q2 + float(LCP_M[1][0]) * z1) / float(LCP_M[1][1])  # noqa: E731
    corner = rows[3]["z"]
    cx, cy = float(corner[0]), float(corner[1])  # type: ignore[index]
    parts = _open(
        "4つの活性集合の判定",
        (
            "二つの接触点の例で、各点が接触しているかどうかの4通りを z1 と z2 の平面に描きます。"
            "どちらの接触点も接触している候補だけが z も w も非負で、解です。"
        ),
        488,
    )
    shade = [
        (lower[0], upper[1]),
        (lower[0], line1(0.0)),
        (cx, cy),
        (upper[0], line2(upper[0])),
        (upper[0], upper[1]),
    ]
    polygon = " ".join(f"{sx(x):.1f},{sy(y):.1f}" for x, y in shade)
    parts.append(f'<polygon points="{polygon}" fill="{RING}" fill-opacity="0.45"/>')
    parts.append(
        f'<path d="M{left} {top}V{bottom}H{right}" fill="none" stroke="{INK}" stroke-width="1.5"/>'
    )
    for value in (0.0, 0.5):
        parts.append(_text(sx(value), bottom + 20, f"{value:g}", "tick", "middle"))
    for value in (0.0, 0.5, 1.0):
        parts.append(_text(left - 8, sy(value) + 5, f"{value:g}", "tick", "end"))
    parts.append(_text(right, bottom + 40, "z₁（点Aの接触力）", "", "end"))
    parts.append(_text(left - 8, top - 8, "z₂（点B）", "", "start"))
    parts.append(_polyline([(sx(0.0), sy(line1(0.0))), (sx(0.5), sy(line1(0.5)))], LINE, 2.5))
    parts.append(
        _polyline([(sx(0.0), sy(line2(0.0))), (sx(upper[0]), sy(line2(upper[0])))], LINE, 2.5)
    )
    parts.append(_text(sx(0.3) - 12, sy(line1(0.3)) + 5, "w₁=0", "note", "end"))
    parts.append(_text(sx(0.58), sy(line2(0.58)) + 24, "w₂=0", "note", "middle"))
    names = {(): "接触なし", (0,): "Aだけ", (1,): "Bだけ", (0, 1): "AとB"}
    for row in rows:
        z = row["z"]
        ok = bool(row["ok"])
        px_, py_ = sx(float(z[0])), sy(float(z[1]))  # type: ignore[index]
        color = UPDATE if ok else POINT
        if ok:
            parts.append(f'<circle cx="{px_:.1f}" cy="{py_:.1f}" r="7" fill="{color}"/>')
        else:
            parts.append(
                f'<circle cx="{px_:.1f}" cy="{py_:.1f}" r="7" fill="#ffffff" '
                f'stroke="{color}" stroke-width="2"/>'
            )
        mark = "解" if ok else "w<0"
        dx = 14 if row["active"] != (0,) else -12
        anchor = "start" if row["active"] != (0,) else "end"
        dy = -14 if row["active"] != () else -12
        parts.append(
            _text(px_ + dx, py_ + dy, f"{names[row['active']]}（{mark}）", "", anchor)  # type: ignore[index]
        )
    parts.append(_text(20, 424, "橙の点：z≧0 かつ w≧0 を満たす候補（解）"))
    parts.append(_text(20, 448, "薄緑：w₁≧0 かつ w₂≧0 の領域", "note"))
    parts.append(_text(20, 472, "白抜き：w に負の成分があり、解ではない", "note"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


FIGURES: dict[str, Callable[[], str]] = {
    "complementarity-active-sets.svg": _lcp_contact_svg,
}
