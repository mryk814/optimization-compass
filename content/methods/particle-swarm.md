---
content_id: particle-swarm
kind: method
method_id: M_PARTICLE_SWARM
title_ja: 粒子群最適化（PSO）
title_en: Particle Swarm Optimization
summary: 各粒子のbest経験と群全体のbestを使って速度を更新し、連続black-box空間を集団で探索する手法です。
source_ids: [S033, S040]
prerequisites: [concept.derivative-free]
related_ids: [cma-es, differential-evolution, genetic-algorithm]
aliases: [/learn/particle-swarm]
status: published
last_reviewed: 2026-07-15
---

各粒子のbest経験と群全体のbestを使って速度を更新し、連続black-box空間を集団で探索する手法です。

## 一手の構造

粒子 $i$ の位置 $x_i$ と速度 $v_i$ を、概ね

$$
v_i \leftarrow \omega v_i
+c_1r_1(p_i-x_i)
+c_2r_2(g-x_i)
$$

$$
x_i \leftarrow x_i+v_i
$$

で更新します。

- $p_i$: その粒子が見つけたpersonal best
- $g$: swarmまたはneighborhoodのbest
- $\omega$: inertia
- $c_1,c_2$: personal / social attraction

探索と収束のバランスは、係数だけでなくtopology、velocity clamp、bound handlingにも依存します。

## 直感的な読み方

- 粒子が広く散る: explorationが残っている
- best周辺へ一斉に集まる: exploitationが強い
- 同じ方向へ高速で飛び続ける: velocityやscaleが不適切
- 多峰性なのに一群へ早期集中: premature convergenceの可能性

群のbestだけでなく、粒子間距離や座標ごとの分散を表示すると状態を読みやすくなります。

## Python: 教育用PSO

```python
import numpy as np


def objective(points: np.ndarray) -> np.ndarray:
    return np.sum(points * points, axis=1)


rng = np.random.default_rng(5)
particle_count = 30
dimension = 2
lower = np.full(dimension, -5.0)
upper = np.full(dimension, 5.0)
position = rng.uniform(lower, upper, size=(particle_count, dimension))
velocity = np.zeros_like(position)
personal_best = position.copy()
personal_value = objective(personal_best)

for _ in range(200):
    global_best = personal_best[np.argmin(personal_value)]
    r1 = rng.random(size=position.shape)
    r2 = rng.random(size=position.shape)
    velocity = (
        0.7 * velocity
        + 1.4 * r1 * (personal_best - position)
        + 1.4 * r2 * (global_best - position)
    )
    position = np.clip(position + velocity, lower, upper)
    value = objective(position)
    improved = value < personal_value
    personal_best[improved] = position[improved]
    personal_value[improved] = value[improved]

best = personal_best[np.argmin(personal_value)]
print(best, personal_value.min())
```

この例はglobal-best topologyです。局所neighborhood topologyでは情報伝播が遅くなり、多様性を保ちやすい場合があります。

## 診断値

- global best / median objective
- position diversity
- velocity norm
- boundary hit率
- personal bestの更新数
- feasible fraction
- seed間の結果分散
- evaluation budget

## 向いている条件

- bounded continuous black-box
- gradientが得られない
- evaluationを並列化できる
- moderate dimension
- 滑らかさに依存しないglobal candidate探索

## 避ける／修正する条件

- 変数scaleが揃っていない
- boundでclipされた粒子が多数停止する
- 1評価が極端に高価でswarmを維持できない
- discrete encodingが速度の意味を失わせる
- global bestへ早期集中して多様性が消える
- 最適性gapやcertificateが必要

::: warning
PSOの「群が一点へ集まった」は収束診断の一部であり、その点が大域最適解だという証明ではありません。
:::
