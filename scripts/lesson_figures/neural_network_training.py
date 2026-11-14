"""Neural network training (content/concepts/neural-network-training.md): the smallest network h(x)
= v tanh(u x), four steering readings, mean squared error, full-batch gradient descent.
"""

from __future__ import annotations

import math
from collections.abc import Callable

from ._svg import (
    GRID,
    INK,
    LINE,
    MUTED,
    POINT,
    RING,
    UPDATE,
    _contour_segments,
    _open,
    _polyline,
    _scale,
    _text,
)

NN_X = (-2.0, -1.0, 1.0, 2.0)
NN_Y = (-1.0, -0.6, 0.7, 0.9)
NN_ETA = 0.5
NN_START_A = (0.3, -0.2)
NN_START_B = (0.2, -0.3)


def nn_loss(u: float, v: float) -> float:
    return sum((v * math.tanh(u * x) - y) ** 2 for x, y in zip(NN_X, NN_Y, strict=True)) / len(NN_X)


def nn_gradient(u: float, v: float) -> tuple[float, float]:
    gu = gv = 0.0
    for x, y in zip(NN_X, NN_Y, strict=True):
        t = math.tanh(u * x)
        r = v * t - y
        gu += 2 * r * v * x * (1 - t * t) / len(NN_X)
        gv += 2 * r * t / len(NN_X)
    return gu, gv


def nn_path(start: tuple[float, float], steps: int) -> list[tuple[float, float]]:
    u, v = start
    path = [(u, v)]
    for _ in range(steps):
        gu, gv = nn_gradient(u, v)
        u, v = u - NN_ETA * gu, v - NN_ETA * gv
        path.append((u, v))
    return path


def nn_minimum() -> tuple[float, float]:
    return nn_path(NN_START_A, 400)[-1]


def _nn_two_valleys_svg() -> str:
    wu, wv = nn_minimum()
    bottom, saddle = nn_loss(wu, wv), nn_loss(0.0, 0.0)
    path_a, path_b = nn_path(NN_START_A, 12), nn_path(NN_START_B, 12)
    px = _scale(-1.6, 1.6, 64, 400)
    py = _scale(1.6, -1.6, 48, 384)
    parts = _open(
        "重みの平面",
        (
            f"h(x)=v tanh(u x) の4点の平均二乗誤差の等高線。谷底は w*=({wu:.2f}, {wv:.2f}) と "
            f"−w* の二つで、どちらも損失 {bottom:.4f}。原点は勾配が0の鞍点で、損失 {saddle:.3f}。"
            f"学習率 {NN_ETA} の勾配降下法は、始点A {NN_START_A} から w* へ、"
            f"始点B {NN_START_B} から −w* へ進みます。"
            f"二つの谷底を結ぶ線分では、中点の原点で損失が {saddle:.3f} に上がります。"
        ),
        816,
    )
    parts.append(f'<path d="M64 48V384H400V48Z" fill="none" stroke="{GRID}"/>')
    for level in (0.05, 0.2, 0.4, saddle, 1.0, 2.0, 3.5):
        style = (
            f'stroke="{MUTED}" stroke-width="2"'
            if level == saddle
            else f'stroke="{RING}" stroke-width="1.5"'
        )
        segments = _contour_segments(nn_loss, level, (-1.6, 1.6), (-1.6, 1.6), (128, 128))
        data = "".join(
            f"M{px(a[0]):.1f} {py(a[1]):.1f}L{px(b[0]):.1f} {py(b[1]):.1f}" for a, b in segments
        )
        parts.append(f'<path d="{data}" fill="none" {style}/>')
    for value in (-1, 0, 1):
        parts.append(_text(px(value), 404, f"{value}", "tick", "middle"))
        parts.append(_text(56, py(value) + 5, f"{value}", "tick", "end"))
    parts.append(_text(400, 426, "u（入力側の重み）", "tick", "end"))
    parts.append(_text(72, 68, "v（出力側の重み）", "tick"))
    parts.append(
        f'<path d="M{px(-wu):.1f} {py(-wv):.1f}L{px(wu):.1f} {py(wv):.1f}" '
        f'stroke="{MUTED}" stroke-width="2" stroke-dasharray="6 5"/>'
    )
    for path, color in ((path_a, LINE), (path_b, POINT)):
        parts.append(_polyline([(px(a), py(b)) for a, b in path], color, 2.5))
        for a, b in path[1:]:
            parts.append(f'<circle cx="{px(a):.1f}" cy="{py(b):.1f}" r="3.5" fill="{color}"/>')
        a, b = path[0]
        parts.append(
            f'<rect x="{px(a) - 5:.1f}" y="{py(b) - 5:.1f}" width="10" height="10" fill="#f7f8f3" '
            f'stroke="{color}" stroke-width="2.5"/>'
        )
    for sign in (1, -1):
        parts.append(
            f'<circle cx="{px(sign * wu):.1f}" cy="{py(sign * wv):.1f}" r="7" fill="{UPDATE}"/>'
        )
    parts.append(f'<circle cx="{px(0):.1f}" cy="{py(0):.1f}" r="5" fill="{INK}"/>')
    parts.append(_text(px(wu) + 12, py(wv) - 10, "w*"))
    parts.append(_text(px(-wu) - 12, py(-wv) + 22, "−w*", "", "end"))
    parts.append(_text(px(0) - 10, py(0) - 12, "鞍点", "", "end"))
    parts.append(_text(px(NN_START_A[0]) + 10, py(NN_START_A[1]) + 4, "A", "note"))
    parts.append(_text(px(NN_START_B[0]) - 10, py(NN_START_B[1]) + 14, "B", "", "end"))
    parts.append(_text(20, 456, f"緑：始点A {NN_START_A} から w* へ", "note"))
    parts.append(_text(20, 480, f"青：始点B {NN_START_B} から −w* へ"))
    parts.append(_text(20, 504, f"濃い線：損失 {saddle:.3f}（u=0 か v=0 で出力が0）", "tick"))
    parts.append(_text(20, 528, f"学習率 {NN_ETA}、点は1回の更新ごと（12回分）", "tick"))

    # Panel 2: the loss on the segment s w*, s from -1 to 1.
    parts.append(_text(20, 576, "谷底を結ぶ線分での損失", "title"))
    sx = _scale(-1.0, 1.0, 64, 400)
    sy = _scale(0.0, 0.7, 748, 608)
    parts.append(f'<path d="M64 608V748H400" fill="none" stroke="{GRID}"/>')
    for value, label in ((-1.0, "−w*"), (0.0, "0"), (1.0, "w*")):
        parts.append(_text(sx(value), 768, label, "tick", "middle"))
    for value in (0.0, 0.3, 0.6):
        parts.append(_text(56, sy(value) + 5, f"{value:.1f}", "tick", "end"))
    profile = [(s / 50, nn_loss(s / 50 * wu, s / 50 * wv)) for s in range(-50, 51)]
    parts.append(
        f'<path d="M{sx(-1):.1f} {sy(bottom):.1f}L{sx(1):.1f} {sy(bottom):.1f}" '
        f'stroke="{UPDATE}" stroke-width="2" stroke-dasharray="6 5"/>'
    )
    parts.append(_polyline([(sx(s), sy(value)) for s, value in profile], LINE, 3))
    parts.append(f'<circle cx="{sx(0):.1f}" cy="{sy(saddle):.1f}" r="5" fill="{INK}"/>')
    parts.append(_text(sx(0) + 12, sy(saddle) + 5, f"中点 {saddle:.3f}"))
    parts.append(_text(20, 796, f"橙の破線：両端の損失 {bottom:.4f} を結ぶ弦", "note"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


FIGURES: dict[str, Callable[[], str]] = {
    "nn-training-two-valleys.svg": _nn_two_valleys_svg,
}
