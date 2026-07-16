---
content_id: proximal-gradient
kind: method
method_id: M_PROX_GRADIENT
title_ja: 近接勾配法
title_en: Proximal gradient method
summary: 滑らかな項には勾配stepを使い、非滑らかな項にはproximal operatorを使う複合凸最適化法です。
source_ids: [S055, S066]
prerequisites: [method.gradient-descent, concept.convexity]
related_ids: [fista, admm]
aliases: [/learn/proximal-gradient]
status: published
last_reviewed: 2026-07-16
---

滑らかな項には勾配stepを使い、非滑らかな項にはproximal operatorを使う複合凸最適化法です。

## 対象となる形

$$
\min_x\; F(x)=f(x)+g(x)
$$

ここで、

- $f$ は微分可能で勾配が利用できる
- $g$ は非滑らかでもよいがproximal operatorを計算できる

とします。更新は

$$
x_{k+1}=\operatorname{prox}_{\eta g}\left(x_k-\eta\nabla f(x_k)\right)
$$

です。

まず滑らかな項を下げるgradient stepを行い、その後に正則化や単純制約をproxで反映します。

## Proxは何をしているか

$$
\operatorname{prox}_{\eta g}(v)
=\arg\min_x\left(g(x)+\frac{1}{2\eta}\|x-v\|^2\right)
$$

L1正則化ならsoft-thresholding、box制約なら区間へのprojectionになります。難しい非滑らか項を持っていても、proxが簡単なら汎用NLPへ無理に平滑化せず構造を使えます。

## Step sizeと停止

$f$ の勾配が $L$-Lipschitzなら、固定stepは $\eta\le 1/L$ が目安です。$L$が不明ならbacktrackingを使います。

確認する値:

- objective value
- proximal-gradient mapping norm
- step size
- sparsity / active set
- function / gradient / prox evaluation数
- validation metric（統計推定の場合）

目的値変化だけで止めると、flatな領域で最適性が弱いまま停止する場合があります。

## Python: Lasso

```python
import numpy as np


def soft_threshold(value: np.ndarray, threshold: float) -> np.ndarray:
    return np.sign(value) * np.maximum(np.abs(value) - threshold, 0.0)


rng = np.random.default_rng(7)
a = rng.normal(size=(40, 8))
true_x = np.array([1.5, 0.0, -2.0, 0.0, 0.0, 0.7, 0.0, 0.0])
b = a @ true_x + 0.05 * rng.normal(size=40)
lam = 0.1

lipschitz = np.linalg.norm(a, ord=2) ** 2
step = 1.0 / lipschitz
x = np.zeros(a.shape[1])

for _ in range(2000):
    gradient = a.T @ (a @ x - b)
    next_x = soft_threshold(x - step * gradient, step * lam)
    if np.linalg.norm(next_x - x) < 1e-10:
        x = next_x
        break
    x = next_x

print(x)
```

## 向いている条件

- smooth loss + L1、group penalty、indicator constraintなど
- sparse・大規模で、一反復を安価にしたい
- 勾配とproxを別々に実装できる
- exactなHessian solveより多数の軽い反復が適する

## 避ける／切り替える条件

- prox自体が高価な最適化問題になる
- $f$ が非滑らか、または勾配が強いnoiseを含む
- 変数scaleにより単一step sizeが極端に保守的
- 強いcoupling constraintを単純projectionで表せない
- basic法の収束が遅い → [FISTA](#/learn/fista)、restart、preconditioningを検討

::: note
FISTAの反復数が少なくても、必ずしも実時間が短いとは限りません。勾配とproxの実コスト、restart、停止条件を揃えて比較します。
:::
