---
content_id: bfgs
kind: method
method_id: M_BFGS
title_ja: BFGS法
title_en: BFGS method
summary: 勾配の変化から逆Hessian（inverse Hessian）の近似を更新し、Newton法に近い探索方向を作る準Newton法です。
source_ids: [S002, S017, S055, S056, S057, S064]
prerequisites: [method.gradient-descent, concept.convexity]
related_ids: [lbfgsb, newton-method, trust-region-newton-cg]
visualization_ids: [constrained-disk-feasible-region]
comparison_ids: [COMPARE_CONSTRAINED_FAILURE]
aliases: [/learn/bfgs]
status: published
last_reviewed: 2026-07-24
---

勾配の変化から逆Hessian（inverse Hessian）の近似を更新し、Newton法に近い探索方向を作る準Newton法です。

## 30秒でつかむ

この手法の気持ちは、勾配の変化から地形の曲がり方を覚え、下りやすい方向を賢く選ぶことです。

進んだ前後の勾配の変化から地形の曲がり方を学び、次の探索方向を整えます。

- **見るもの**: 目的関数値、勾配の変化、line searchの結果
- **動かすもの**: 現在点、探索方向、逆Hessianの近似
- **前進の判断**: 目的関数値とgradient normが下がり、line searchが安定してstepを受け入れること

## 仕組み

勾配降下法が常に $-\nabla f(x_k)$ へ進むのに対し、BFGSは正定値行列 $H_k$ を使って方向を変形します。

$$
p_k = -H_k \nabla f(x_k)
$$

新しい点へ移動した後、

- $s_k = x_{k+1} - x_k$
- $y_k = \nabla f(x_{k+1}) - \nabla f(x_k)$

を使って $H_k$ を更新します。曲率条件 $y_k^T s_k > 0$ が満たされると、正定値性を保ちやすく、下り方向を作れます。

## 向いている条件

| 条件 | 理由 |
|---|---|
| 連続・滑らか | 勾配差を曲率情報として利用するため |
| 中小規模 | 密な（dense）近似行列は概ね $O(n^2)$ memoryを使うため |
| 勾配が信頼できる | 誤った勾配は更新行列を壊すため |
| 局所解でよい | 非凸問題で大域最適性を保証する手法ではないため |

高精度な局所解を少ない反復で得たいときに有力です。変数が多い場合は[L-BFGS-B](#/learn/lbfgsb)などlimited-memory法を検討します。

## 制約処理はBFGSの外にある

BFGSの更新式は、一般の制約を自動では扱いません。
目的関数値が下がっても、制約違反が残る点は解ではありません。

[制約を無視するfailure Theater](#/theater/learning/SCENARIO_CONSTRAINED_DISK)では、円内の可行領域とBFGSのfailure pathを同じ図で確認できます。
[SLSQPとのfailure Compare](#/compare/COMPARE_CONSTRAINED_FAILURE)は、同じ目的・disk制約・初期点・12回のteaching budgetを使います。
変えるのは制約を評価するかどうかです。

これは可行性と目的改善を分けて読む固定教材です。
BFGSやSLSQPの実装内部を再現するbenchmarkではなく、solverの一般性能rankingにも使いません。

## 直線探索（line search）の役割

BFGSの名前は更新式を表しますが、実用上はstepの長さ（step length）を決めるline searchと組み合わせます。stepが大きすぎると目的値が悪化し、小さすぎると曲率情報を十分に得られません。

::: warning
「BFGSを使った」だけでは再現条件として不十分です。
初期点／勾配の実装／line-search条件／停止許容値／scalingを一緒に記録します。
:::

## Python

次の例は、解析的なgradientを渡してBFGSを実行する最小例です。

```python
import numpy as np
from scipy.optimize import minimize


def objective(x: np.ndarray) -> float:
    return float((x[0] - 1.0) ** 2 + 10.0 * (x[1] + 2.0) ** 2)


def gradient(x: np.ndarray) -> np.ndarray:
    return np.array([2.0 * (x[0] - 1.0), 20.0 * (x[1] + 2.0)])


result = minimize(
    objective,
    x0=np.array([4.0, 4.0]),
    jac=gradient,
    method="BFGS",
    options={"gtol": 1e-8, "maxiter": 200},
)

print(result.success, result.x, result.fun, result.nfev, result.njev)
```

## 診断値

- gradient norm
- line-search iteration数
- function / gradient evaluation数
- step norm
- $y_k^T s_k$ が十分正か
- objective change

## 失敗・切替の兆候

- gradient checkが有限差分と一致するか
- 変数・目的値のscaleが極端に違わないか
- line search failureが発生していないか
- 非滑らかな分岐やclip処理が目的関数内にないか
- 異なる初期点で別の局所解へ入っていないか

## 次に読む

Hessianを直接利用できる場合との違いは[Newton法](#/learn/newton-method)、局所modelを信頼できる範囲だけ使う考え方は[trust-region Newton-CG](#/learn/trust-region-newton-cg)で確認できます。
