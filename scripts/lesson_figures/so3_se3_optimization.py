"""SO(3)/SE(3) (content/concepts/so3-se3-optimization.md): four markers on a box, measured by a
camera. After subtracting the centroids, only the rotation is left to fit.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence

from ._numeric import Matrix3, _det3
from ._svg import GRID, POINT, UPDATE, _open, _polyline, _scale, _text

SO3_P = ((0.0, 0.0, 0.0), (30.0, 0.0, 0.0), (0.0, 20.0, 0.0), (0.0, 0.0, 10.0))
SO3_Q = ((50.6, 19.2, 80.1), (25.7, 36.2, 87.0), (49.6, 12.2, 98.2), (56.9, 27.5, 83.0))
SO3_STEP = 5e-4
SO3_ITERATIONS = 60


def _identity3() -> Matrix3:
    return [[1.0 if i == j else 0.0 for j in range(3)] for i in range(3)]


def _mat3_mul(a: Matrix3, b: Matrix3) -> Matrix3:
    return [[sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


def _mat3_t(a: Matrix3) -> Matrix3:
    return [[a[j][i] for j in range(3)] for i in range(3)]


def _so3_centered() -> tuple[list[list[float]], list[list[float]]]:
    def centre(points: Sequence[Sequence[float]]) -> list[list[float]]:
        mean = [sum(p[i] for p in points) / len(points) for i in range(3)]
        return [[p[i] - mean[i] for i in range(3)] for p in points]

    return centre(SO3_P), centre(SO3_Q)


def so3_objective(m: Matrix3) -> float:
    """Sum of squared distances between M p_i and q_i for the centred markers."""
    pc, qc = _so3_centered()
    return sum(
        sum((sum(m[i][k] * p[k] for k in range(3)) - q[i]) ** 2 for i in range(3))
        for p, q in zip(pc, qc, strict=True)
    )


def _so3_gradient(m: Matrix3) -> Matrix3:
    pc, qc = _so3_centered()
    grad = [[0.0] * 3 for _ in range(3)]
    for p, q in zip(pc, qc, strict=True):
        r = [sum(m[i][k] * p[k] for k in range(3)) - q[i] for i in range(3)]
        for i in range(3):
            for j in range(3):
                grad[i][j] += 2 * r[i] * p[j]
    return grad


def _so3_exp(w: Sequence[float]) -> Matrix3:
    """Rodrigues' formula: the rotation by |w| about the axis w / |w|."""
    theta = math.sqrt(sum(v * v for v in w))
    k = [[0.0, -w[2], w[1]], [w[2], 0.0, -w[0]], [-w[1], w[0], 0.0]]
    if theta < 1e-12:
        return [[_identity3()[i][j] + k[i][j] for j in range(3)] for i in range(3)]
    k = [[v / theta for v in row] for row in k]
    k2 = _mat3_mul(k, k)
    return [
        [
            _identity3()[i][j] + math.sin(theta) * k[i][j] + (1 - math.cos(theta)) * k2[i][j]
            for j in range(3)
        ]
        for i in range(3)
    ]


def _orthogonality_error(m: Matrix3) -> float:
    mtm = _mat3_mul(_mat3_t(m), m)
    return math.sqrt(sum((mtm[i][j] - _identity3()[i][j]) ** 2 for i in range(3) for j in range(3)))


def _so3_riemannian_step(x: Matrix3) -> Matrix3:
    g = _mat3_mul(_mat3_t(x), _so3_gradient(x))
    w = [(g[2][1] - g[1][2]) / 2, (g[0][2] - g[2][0]) / 2, (g[1][0] - g[0][1]) / 2]
    return _mat3_mul(x, _so3_exp([-SO3_STEP * v for v in w]))


def so3_paths(iterations: int = SO3_ITERATIONS) -> list[dict[str, float]]:
    """From the identity, a gradient step on all nine entries vs a step that stays a rotation."""
    ambient, rotation = _identity3(), _identity3()
    rows = []
    for k in range(iterations + 1):
        if k:
            grad = _so3_gradient(ambient)
            ambient = [[ambient[i][j] - SO3_STEP * grad[i][j] for j in range(3)] for i in range(3)]
            rotation = _so3_riemannian_step(rotation)
        rows.append(
            {
                "k": k,
                "ambient_f": so3_objective(ambient),
                "ambient_orth": _orthogonality_error(ambient),
                "ambient_det": _det3(ambient),
                "rotation_f": so3_objective(rotation),
                "rotation_orth": _orthogonality_error(rotation),
            }
        )
    return rows


def so3_rotation_minimum(iterations: int = 400) -> float:
    rotation = _identity3()
    for _ in range(iterations):
        rotation = _so3_riemannian_step(rotation)
    return so3_objective(rotation)


def _so3_paths_svg() -> str:
    rows = so3_paths()
    best = so3_rotation_minimum()
    flipped = [row["k"] for row in rows if row["ambient_det"] < 0]
    below = next(row["k"] for row in rows if row["ambient_f"] < best)
    last = rows[-1]
    parts = _open(
        "9成分を動かすか、回転のまま動かすか",
        (
            f"箱の4つのマーカーの例で、単位行列から一歩の大きさ{SO3_STEP:g}で{SO3_ITERATIONS}回"
            "更新した2つの経路です。9成分の勾配法は"
            f"k={below}で回転での最小{best:.3f}を下回り、k={SO3_ITERATIONS}で"
            f"{last['ambient_f']:.3f}になります。そのときの‖MᵀM−I‖は{last['ambient_orth']:.3f}で、"
            f"k={flipped[0]}では行列式が{rows[flipped[0]]['ambient_det']:.2f}です。"
            f"回転のまま動かす経路は{last['rotation_f']:.3f}に近づき、"
            "‖MᵀM−I‖は全反復で1e−14より小さいままです。"
        ),
        604,
    )
    px = _scale(0.0, float(SO3_ITERATIONS), 64, 420)

    def panel(
        top: int, bottom: int, upper: float, key_a: str, key_r: str, ticks: Sequence[float]
    ) -> Callable[[float], float]:
        py = _scale(0.0, upper, bottom, top)
        parts.append(f'<path d="M64 {top}V{bottom}H420" fill="none" stroke="{GRID}"/>')
        for value in ticks:
            parts.append(_text(56, py(value) + 5, f"{value:g}", "tick", "end"))
        for k in (0, 20, 40, 60):
            parts.append(_text(px(k), bottom + 20, f"{k}", "tick", "middle"))
        for key, color in ((key_r, POINT), (key_a, UPDATE)):
            points = [(px(row["k"]), py(min(row[key], upper))) for row in rows]
            parts.append(_polyline(points, color, 3))
        return py

    parts.append(_text(20, 62, "① 二乗和（8より大きい値は上端で切る）"))
    py1 = panel(80, 240, 8.0, "ambient_f", "rotation_f", (0.0, 4.0, 8.0))
    parts.append(
        f'<path d="M64 {py1(best):.1f}H420" stroke="{POINT}" stroke-width="1.5" '
        'stroke-dasharray="5 4"/>'
    )
    parts.append(_text(420, py1(best) - 8, f"回転での最小 {best:.3f}", "note", "end"))
    parts.append(_text(420, 282, "反復 k", "tick", "end"))

    parts.append(_text(20, 318, "② 回転からのはずれ ‖MᵀM − I‖"))
    py2 = panel(336, 476, 1.2, "ambient_orth", "rotation_orth", (0.0, 0.6, 1.2))
    first = rows[flipped[0]]
    parts.append(
        f'<circle cx="{px(first["k"]):.1f}" cy="{py2(first["ambient_orth"]):.1f}" r="5" '
        f'fill="none" stroke="{UPDATE}" stroke-width="2"/>'
    )
    parts.append(
        _text(
            px(first["k"]) + 12,
            py2(first["ambient_orth"]) + 6,
            f"k={first['k']}：行列式 {first['ambient_det']:.2f}（鏡像）".replace("-", "−"),
        )
    )
    parts.append(_text(420, 518, "反復 k", "tick", "end"))

    parts.append(f'<path d="M20 548H48" stroke="{UPDATE}" stroke-width="3"/>')
    parts.append(_text(56, 554, "9成分の勾配法"))
    parts.append(f'<path d="M190 548H218" stroke="{POINT}" stroke-width="3"/>')
    parts.append(_text(226, 554, "回転のまま動かす"))
    parts.append(_text(20, 584, f"どちらも単位行列から、一歩の大きさ {SO3_STEP:g}", "note"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


FIGURES: dict[str, Callable[[], str]] = {
    "so3-rotation-paths.svg": _so3_paths_svg,
}
