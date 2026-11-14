"""Distributed consensus (content/concepts/distributed-consensus.md): three hospitals each keep
their own records (dose above the reference t, effective y) and share one coefficient theta in
P(effective) = sigma(theta * t). Raw records never leave a hospital.
"""

from __future__ import annotations

import math
from collections.abc import Callable

from ._svg import GRID, INK, LINE, MUTED, POINT, RING, UPDATE, _open, _polyline, _scale, _text

DC_SITES = {
    "A": ((-1, 1, 2, 3), (0, 1, 0, 1)),
    "B": ((-2, -1, 1, 1, 2), (0, 1, 1, 1, 1)),
    "C": ((-3, -2, -1, 1, 2, 3), (0, 0, 1, 0, 1, 1)),
}


def _dc_sigmoid(value: float) -> float:
    return 1.0 / (1.0 + math.exp(-value))


def dc_loss(site: str, theta: float) -> float:
    """Negative log-likelihood of one hospital's records."""
    ts, ys = DC_SITES[site]
    return sum(math.log1p(math.exp(theta * t)) - y * theta * t for t, y in zip(ts, ys, strict=True))


def _dc_slope(site: str, theta: float) -> float:
    ts, ys = DC_SITES[site]
    return sum(t * (_dc_sigmoid(theta * t) - y) for t, y in zip(ts, ys, strict=True))


def _dc_curvature(site: str, theta: float) -> float:
    ts, _ = DC_SITES[site]
    return sum(t * t * _dc_sigmoid(theta * t) * (1 - _dc_sigmoid(theta * t)) for t in ts)


def _dc_newton(slope: Callable[[float], float], curve: Callable[[float], float]) -> float:
    theta = 0.0
    for _ in range(60):
        theta -= slope(theta) / curve(theta)
    return theta


def dc_local(site: str) -> float:
    return _dc_newton(lambda th: _dc_slope(site, th), lambda th: _dc_curvature(site, th))


def dc_global() -> float:
    return _dc_newton(
        lambda th: sum(_dc_slope(s, th) for s in DC_SITES),
        lambda th: sum(_dc_curvature(s, th) for s in DC_SITES),
    )


def dc_admm(rho: float, rounds: int = 2000) -> list[tuple[dict[str, float], float]]:
    """Consensus ADMM; stops when every hospital is within 1e-3 of z and z is within 1e-3
    of the pooled answer."""
    x = dict.fromkeys(DC_SITES, 0.0)
    u = dict.fromkeys(DC_SITES, 0.0)
    z = 0.0
    target = dc_global()
    history = [(dict(x), z)]
    for _ in range(rounds):
        x = {
            s: _dc_newton(
                lambda th, s=s, z=z, u=u: _dc_slope(s, th) + rho * (th - z + u[s]),
                lambda th, s=s: _dc_curvature(s, th) + rho,
            )
            for s in DC_SITES
        }
        z = sum(x[s] + u[s] for s in DC_SITES) / len(DC_SITES)
        u = {s: u[s] + x[s] - z for s in DC_SITES}
        history.append((dict(x), z))
        if max(abs(x[s] - z) for s in DC_SITES) < 1e-3 and abs(z - target) < 1e-3:
            break
    return history


DC_COLORS = {"A": RING, "B": POINT, "C": UPDATE}


def _dc_losses_svg() -> str:
    local = {s: dc_local(s) for s in DC_SITES}
    best = dc_global()
    mean = sum(local.values()) / 3
    counts = {s: len(DC_SITES[s][0]) for s in DC_SITES}
    weighted = sum(counts[s] * local[s] for s in DC_SITES) / sum(counts.values())
    parts = _open(
        "病院ごとの損失と、3病院の合計",
        (
            "効く確率 σ(θt) の係数 θ ごとの損失。① 病院ごとの損失（底の値を0にそろえた）。"
            + "、".join(f"病院{s}の底は θ={local[s]:.2f}" for s in DC_SITES)
            + "。② 3病院の損失の合計。底は "
            f"θ={best:.3f}。病院ごとの答えの平均 {mean:.3f}、患者の数で重み付けした平均 "
            f"{weighted:.3f} はどちらも合計の底からずれる。"
        ),
        610,
    )
    px = _scale(0.0, 2.0, 64, 410)
    for tick in (0, 0.5, 1, 1.5, 2):
        parts.append(_text(px(tick), 292, f"{tick:g}", "tick", "middle"))
    thetas = [2.0 * i / 200 for i in range(201)]
    parts.append(_text(20, 64, "① 病院ごとの損失（底を0にそろえる）"))
    ly = _scale(0.0, 1.2, 272, 84)
    parts.append(f'<path d="M64 84V272H410" fill="none" stroke="{GRID}"/>')
    for value in (0, 0.5, 1):
        parts.append(_text(56, ly(value) + 5, f"{value:g}", "tick", "end"))
    for index, s in enumerate(DC_SITES):
        floor = dc_loss(s, local[s])
        points = [
            (px(t), ly(dc_loss(s, t) - floor)) for t in thetas if dc_loss(s, t) - floor <= 1.2
        ]
        parts.append(_polyline(points, DC_COLORS[s], 3))
        parts.append(
            f'<circle cx="{px(local[s]):.1f}" cy="{ly(0):.1f}" r="6" fill="{DC_COLORS[s]}"/>'
        )
        x0 = 20 + 132 * index
        parts.append(_polyline([(x0, 316 - 5), (x0 + 20, 316 - 5)], DC_COLORS[s], 3))
        parts.append(_text(x0 + 26, 316, f"病院{s}：{local[s]:.2f}", "tick"))
    parts.append(_text(20, 364, "② 3病院の損失の合計（θ=0.5〜1を拡大）"))
    qx = _scale(0.5, 1.0, 64, 410)
    zoom = [0.5 + 0.5 * i / 200 for i in range(201)]
    total = [sum(dc_loss(s, t) for s in DC_SITES) for t in zoom]
    low = min(total)
    sy = _scale(0.0, 0.3, 552, 384)
    parts.append(f'<path d="M64 384V552H410" fill="none" stroke="{GRID}"/>')
    for value in (0, 0.1, 0.2, 0.3):
        parts.append(_text(56, sy(value) + 5, f"{value:g}", "tick", "end"))
    for tick in (0.5, 0.6, 0.7, 0.8, 0.9, 1.0):
        parts.append(_text(qx(tick), 572, f"{tick:g}", "tick", "middle"))
    curve = [(qx(t), sy(min(v - low, 0.3))) for t, v in zip(zoom, total, strict=True)]
    parts.append(_polyline(curve, LINE, 3))
    marks = (
        (best, f"合計の底 {best:.2f}", 120, 470, True),
        (mean, f"平均 {mean:.2f}", 250, 440, False),
        (weighted, f"患者の数の重み {weighted:.2f}", 280, 470, False),
    )
    for theta, label, tx, ty, solid in marks:
        value = sum(dc_loss(s, theta) for s in DC_SITES) - low
        cx, cy = qx(theta), sy(value)
        parts.append(
            f'<path d="M{cx:.1f} {cy - 6:.1f}L{tx:.1f} {ty + 6:.1f}" stroke="{MUTED}" '
            'stroke-width="1"/>'
        )
        fill = LINE if solid else "#ffffff"
        parts.append(
            f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="5.5" fill="{fill}" stroke="{INK}" '
            'stroke-width="1.5"/>'
        )
        parts.append(_text(tx, ty, label, "tick", "middle"))
    parts.append(_text(410, 596, "係数 θ", "tick", "end"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


DC_RHOS = (0.1, 0.5, 1.0, 2.0, 5.0, 20.0, 100.0)


def _dc_admm_svg() -> str:
    history = dc_admm(2.0)
    best = dc_global()
    parts = _open(
        "合意へ近づく様子と、罰則係数",
        (
            f"① 罰則係数 ρ=2 のADMMで、3病院の係数と共通の値 z が {best:.3f} へ近づく。"
            f"{len(history) - 1}回のやり取りで、各病院の値と z の差が0.001未満、"
            f"z が {best:.3f} から0.001以内になる。"
            "② ρ ごとの、そろうまでのやり取りの回数。"
            + "、".join(f"ρ={rho:g}で{len(dc_admm(rho)) - 1}回" for rho in DC_RHOS)
            + "。"
        ),
        612,
    )
    parts.append(_text(20, 64, "① ρ=2 のときの、病院ごとの係数と共通の値 z"))
    px = _scale(0.0, float(len(history) - 1), 64, 410)
    vy = _scale(0.0, 1.0, 272, 84)
    parts.append(f'<path d="M64 84V272H410" fill="none" stroke="{GRID}"/>')
    for value in (0, 0.5, 1):
        parts.append(_text(56, vy(value) + 5, f"{value:g}", "tick", "end"))
    for k in range(0, len(history), 2):
        parts.append(_text(px(k), 292, str(k), "tick", "middle"))
    parts.append(
        f'<path d="M64 {vy(best):.1f}H410" stroke="{GRID}" stroke-width="1.5" '
        'stroke-dasharray="5 4"/>'
    )
    for s in DC_SITES:
        points = [(px(k), vy(x[s])) for k, (x, _) in enumerate(history)]
        parts.append(_polyline(points, DC_COLORS[s], 2.5))
    parts.append(
        _polyline([(px(k), vy(z)) for k, (_, z) in enumerate(history)], INK, 2.5).replace(
            "/>", ' stroke-dasharray="6 4"/>'
        )
    )
    for index, (name, color) in enumerate(
        (*((f"病院{s}", DC_COLORS[s]) for s in DC_SITES), ("z", INK))
    ):
        x0 = 64 + 88 * index
        parts.append(_polyline([(x0, 316 - 5), (x0 + 22, 316 - 5)], color, 2.5))
        parts.append(_text(x0 + 28, 316, name, "tick"))
    parts.append(_text(410, 340, "やり取りの回数", "tick", "end"))

    parts.append(_text(20, 384, "② ρ ごとの、そろうまでの回数"))
    by = _scale(0.0, math.log10(1000.0), 560, 410)
    parts.append(f'<path d="M64 410V560H410" fill="none" stroke="{GRID}"/>')
    for value in (1, 10, 100, 1000):
        parts.append(_text(56, by(math.log10(value)) + 5, str(value), "tick", "end"))
    width = (410 - 64) / len(DC_RHOS)
    for index, rho in enumerate(DC_RHOS):
        count = len(dc_admm(rho)) - 1
        left = 64 + width * index + 8
        top = by(math.log10(count))
        color = INK if rho == 2.0 else LINE
        parts.append(
            f'<rect x="{left:.1f}" y="{top:.1f}" width="{width - 16:.1f}" height="{560 - top:.1f}" '
            f'fill="{color}"/>'
        )
        parts.append(_text(left + (width - 16) / 2, top - 6, str(count), "tick", "middle"))
        parts.append(_text(left + (width - 16) / 2, 580, f"{rho:g}", "tick", "middle"))
    parts.append(_text(410, 602, "罰則係数 ρ（縦は対数目盛）", "tick", "end"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


FIGURES: dict[str, Callable[[], str]] = {
    "distributed-consensus-losses.svg": _dc_losses_svg,
    "distributed-consensus-admm.svg": _dc_admm_svg,
}
