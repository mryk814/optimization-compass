---
content_id: mirror-descent
kind: method
method_id: M_MIRROR_DESCENT
title_ja: Mirror Descent
title_en: Mirror Descent
summary: Euclidean距離ではなく問題に合うBregman geometryを使い、simplex・確率分布・非一様scale上で劣勾配stepを行う一次法です。
source_ids: [S055, S066]
prerequisites: [concept.convexity, subgradient]
related_ids: [subgradient, proximal-gradient, multi-objective]
aliases: [/learn/mirror-descent]
status: published
last_reviewed: 2026-07-15
---

Euclidean距離ではなく問題に合うBregman geometryを使い、simplex・確率分布・非一様scale上で劣勾配stepを行う一次法です。

## なぜEuclidean stepを変えるか

通常のprojected subgradientは

$$
x_{k+1}=\Pi_C(x_k-\eta g_k)
$$

とEuclidean距離でprojectionします。Mirror Descentはstrongly convexなmirror map $\psi$ からBregman divergence

$$
D_\psi(x,y)=\psi(x)-\psi(y)-\nabla\psi(y)^T(x-y)
$$

を作り、

$$
x_{k+1}=\arg\min_{x\in C}\left\{\eta g_k^Tx+D_\psi(x,x_k)\right\}
$$

を解きます。

geometryをproblem domainへ合わせることで、単純なEuclidean projectionより自然な更新になります。

## Probability simplexの例

$x_i\ge0$、$\sum_i x_i=1$ のsimplexでnegative entropyをmirror mapに使うと、exponentiated-gradient型の更新になります。

```python
import numpy as np


def loss_gradient(probability: np.ndarray) -> np.ndarray:
    target = np.array([0.65, 0.25, 0.10])
    return probability - target


probability = np.full(3, 1.0 / 3.0)
learning_rate = 0.8

for _ in range(500):
    gradient = loss_gradient(probability)
    log_weight = np.log(probability) - learning_rate * gradient
    log_weight -= np.max(log_weight)
    probability = np.exp(log_weight)
    probability /= probability.sum()
    if np.linalg.norm(gradient) < 1e-9:
        break

print(probability, probability.sum())
```

update後も正の成分とsum=1を保ちます。0成分、overflow、regularizationの扱いは実装で確認します。

## Mirror mapを選ぶ

- Euclidean squared norm: projected gradientへ戻る
- negative entropy: probability simplex
- log barrier系: positive orthant / interior geometry
- matrix entropy: positive semidefinite構造
- problem-specific separable map: non-uniform coordinate scale

mirror mapが変わればdual spaceでのstepとprimalへの戻し方も変わります。

## 診断値

- objective / regret / duality gap
- Bregman step size
- subgradient normとdual norm
- minimum coordinate / boundary proximity
- constraint violation
- entropyまたはsparsity
- running average
- step schedule

Euclidean normだけでstepを評価すると、選択したgeometryの意味を取り逃がす場合があります。

## 向いている条件

- convex optimization
- probability・simplex・positive変数
- online learning / regret minimization
- non-Euclidean geometryが自然
- sparse high-dimensional domain
- projectionを別geometryで安価に書ける

## 避ける／切り替える条件

- mirror projectionが元problemより難しい
- mirror mapがdomain boundaryで数値不安定
- 非凸problemへconvex guaranteeを適用
- step scheduleとdual normを無視
- Euclidean geometryで十分なのに複雑化
- 0 probabilityをlogへ入れる

::: note
Mirror Descentは特定の一つの更新式ではなく、mirror map・norm・step scheduleを含むfamilyです。比較ではgeometryまで明記します。
:::

非滑らか凸problemの基本は[劣勾配法](#/learn/subgradient)、proximal operatorが利用できる場合は[近接勾配法](#/learn/proximal-gradient)も比較します。
