---
content_id: admm
kind: method
method_id: M_ADMM
title_ja: 交互方向乗数法（ADMM）
title_en: Alternating Direction Method of Multipliers
summary: 分離しやすい部分問題を交互に解き、主残差と双対残差を減らしてconsensusを作る分割最適化法です。
source_ids: [S012, S055, S061, S062]
prerequisites: [concept.convexity]
related_ids: [proximal-gradient, fista, lp-qp-conic]
aliases: [/learn/admm]
status: published
last_reviewed: 2026-07-15
---

分離しやすい部分問題を交互に解き、主残差と双対残差を減らしてconsensusを作る分割最適化法です。

## なぜ変数を分けるのか

代表形は

$$
\min_{x,z}\; f(x)+g(z) \quad \text{subject to}\quad Ax+Bz=c
$$

です。$f$ と $g$ を別々に扱うため、滑らかな項、非滑らかな正則化、制約、分散データなどを異なる部分問題へ分けられます。

scaled ADMMでは概ね次を繰り返します。

1. $x$ を更新する
2. $z$ を更新する
3. dual変数 $u$ を更新する

各部分問題が閉形式、prox、疎な線形solveなどで解きやすいときに有効です。

## 収束を何で判断するか

目的値だけでは不十分です。

- primal residual: $r_k = Ax_k + Bz_k - c$
- dual residual: $s_k$（consensus変数の変化に対応）
- objective value
- subproblem solve error
- penalty parameter $\rho$

primal residualだけ小さくてもdual residualが大きければ、変数は制約を満たしつつまだ動いています。逆も同様です。

::: warning
ADMMの1反復が軽いとは限りません。各subproblemでfactorizationやinner optimizationを行う場合、inner solveの費用と精度も記録します。
:::

## PythonでL1正則化の分割を確認する

次は $\frac{1}{2}\|x-b\|^2 + \lambda\|z\|_1$、$x=z$ の小さな例です。

```python
import numpy as np


def soft_threshold(value: np.ndarray, threshold: float) -> np.ndarray:
    return np.sign(value) * np.maximum(np.abs(value) - threshold, 0.0)


b = np.array([3.0, -0.4, 1.2])
lam = 0.8
rho = 1.0
x = np.zeros_like(b)
z = np.zeros_like(b)
u = np.zeros_like(b)

for _ in range(200):
    x = (b + rho * (z - u)) / (1.0 + rho)
    previous_z = z.copy()
    z = soft_threshold(x + u, lam / rho)
    u = u + x - z

    primal = np.linalg.norm(x - z)
    dual = rho * np.linalg.norm(z - previous_z)
    if primal < 1e-8 and dual < 1e-8:
        break

print(z, primal, dual)
```

## $\rho$を読む

$\rho$は単なる学習率ではなく、consensus violationへの重みと数値conditioningへ影響します。

- primal residualがdual residualより極端に大きい → $\rho$を上げる候補
- dual residualが極端に大きい → $\rho$を下げる候補
- 頻繁に変える → factorization再利用や理論条件への影響を確認

実装によってadaptive ruleが異なるため、defaultを無条件に横比較しません。

## 向いている／避ける条件

向いている:

- convexな分離構造
- sparse QP、L1正則化、consensus、distributed optimization
- proxやprojectionが安価
- warm startを繰り返し利用したい

避ける／条件付き:

- 分割後のsubproblemが元問題より難しい
- 高精度解が必要だが残差収束が非常に遅い
- 非凸ADMMを理論保証付き凸ADMMと同一視している
- $\rho$やscaleにより残差が一方だけ停滞する

単一変数で直接prox stepを使える場合は[proximal gradient](#/learn/proximal-gradient)の方が単純なことがあります。
