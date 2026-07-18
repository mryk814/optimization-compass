---
content_id: projected-gradient
kind: method
method_id: M_PROJECTED_GRADIENT
title_ja: 射影勾配法
title_en: Projected Gradient Method
summary: 勾配stepの後に実行可能集合へprojectionし、単純な凸制約を常に満たしながら目的関数を改善する一次法です。
source_ids: [S055, S056, S066]
prerequisites: [method.gradient-descent, constrained-continuous]
related_ids: [method.gradient-descent, proximal-gradient, mirror-descent, active-set]
aliases: [/learn/projected-gradient]
status: published
last_reviewed: 2026-07-18
---

勾配stepの後に実行可能集合へprojectionし、単純な凸制約を常に満たしながら目的関数を改善する一次法です。

## 30秒でつかむ

Projected Gradientは、勾配で下った点をそのまま採用せず、実行可能集合へ戻して次の反復を続けます。

- 見ているもの: feasible objective、projected-gradient mapping、projection distance
- 動かしているもの: 現在点、step size、active face、projection
- 前進の判断: mapping normと目的値が下がり、projection後の点が実行可能であること
- 恐れていること: projectionの高コスト、悪いstep、単純なclipによる制約の取り違え

## 更新式

convex set $C$ に対し、

$$
x_{k+1}=\Pi_C(x_k-\eta_k\nabla f(x_k))
$$

と更新します。$\Pi_C$ はEuclidean projection

$$
\arg\min_{z\in C}\|z-y\|^2
$$

です。

box、simplex、ball、affine subspaceなど、projectionが閉形式または安価なときに有効です。

## 境界上の勾配を読む

解が境界にある場合、通常の勾配は0でなくてもよいです。重要なのは実行可能方向へ進めないことです。

projected-gradient mapping

$$
G_\eta(x)=\frac{1}{\eta}\left(x-\Pi_C(x-\eta\nabla f(x))\right)
$$

がstationarityの診断になります。

## Python: box projection

```python
import numpy as np


def objective(x: np.ndarray) -> float:
    return float((x[0] - 3.0) ** 2 + 4.0 * (x[1] + 1.0) ** 2)


def gradient(x: np.ndarray) -> np.ndarray:
    return np.array([2.0 * (x[0] - 3.0), 8.0 * (x[1] + 1.0)])


lower = np.array([-2.0, -3.0])
upper = np.array([2.0, 3.0])
x = np.array([0.0, 0.0])
step = 0.1

for _ in range(2_000):
    projected = np.clip(x - step * gradient(x), lower, upper)
    mapping = (x - projected) / step
    x = projected
    if np.linalg.norm(mapping) < 1e-9:
        break

print(x, objective(x), np.linalg.norm(mapping))
```

無制約minimumの$x_0=3$は上限2を超えるため、constrained solutionは境界へ張り付きます。

## Projectionの費用

「制約があるからprojection」ではなく、projection自体が安価かを確認します。

- box: coordinate-wise clip
- Euclidean ball: radial scaling
- simplex: threshold / sorting
- affine set: linear solve
- PSD cone: eigenvalue decomposition
- 複雑なnonlinear set: projectionが別の難しい最適化問題

projectionが高価ならproximal、primal-dual、interior-point、parameterizationを検討します。

## 最初に見る診断値

- objective / best feasible objective
- projected-gradient mapping norm
- step size
- active bound / active face
- projection distance
- function / gradient / projection time
- constraint violation after projection
- line-search status

## 向いている条件

- smooth objective
- convexでprojectionが安価な制約集合
- iteratesを常にfeasibleに保ちたい
- 大規模で一反復を軽くしたい
- warm startを使う

## 避ける／切り替える条件

- nonconvex setでprojectionが多値
- projectionが元problemより高価
- general equality / inequalityを単純clipで代用
- stepが大きく境界間を振動
- ordinary gradient normだけで停止
- nonsmooth regularizerをprojectionと混同

::: note
indicator function $I_C$ のproxはprojectionなので、Projected GradientはProximal Gradientの特殊例として見られます。ただしUIや説明では「制約集合への射影」という役割を明示します。
:::
