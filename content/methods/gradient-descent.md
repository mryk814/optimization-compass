---
content_id: method.gradient-descent
kind: method
method_id: M_GRADIENT_DESCENT
title_ja: 勾配降下法
title_en: Gradient Descent
summary: 現在点の勾配が示す局所的な上り方向と反対へstepを取り、滑らかな目的関数の値を反復的に下げる一次法です。
prerequisites: [concept.convexity]
related_ids: [bfgs, proximal-gradient, trust-region-newton-cg]
comparison_ids: [COMPARE_GRADIENT_FAMILY]
aliases: [/learn/method.gradient-descent]
comparison_aliases: [COMPARE_GRADIENT_FAMILY|/compare/gradient-quadratic]
source_ids: [S001, S002]
status: published
last_reviewed: 2026-07-15
---

現在点の勾配が示す局所的な上り方向と反対へstepを取り、滑らかな目的関数の値を反復的に下げる一次法です。

## 一手の意味

更新は

$$
x_{k+1}=x_k-\eta_k\nabla f(x_k)
$$

です。勾配 $\nabla f(x_k)$ は現在点で最も急に増える局所方向なので、その反対は局所的な下降方向です。ただし、有限のstepを取った先でも目的値が下がるかはstep size $\eta_k$ と目的関数の曲率に依存します。

## 何が必要か

| 項目 | 確認すること |
|---|---|
| variable | 連続変数であるか、projection可能な単純制約か |
| objective | 局所的に滑らかで有限値を返すか |
| gradient | analytic、automatic differentiation、検証済み数値微分か |
| scale | 座標ごとの単位や曲率が極端に違わないか |
| goal | 局所停留点でよいか、凸性により大域解を期待できるか |

勾配を計算できることと、勾配が正しいことは別です。実装前に有限差分とのdirectional derivative checkを行います。

## 学習率を読む

- 小さすぎる: 安定でも収束が遅い
- 大きすぎる: 谷を飛び越えて振動または発散する
- 一方向では適切でも、条件数の悪い谷では他方向に大きすぎる
- 固定stepが難しい: line search、schedule、preconditioningを検討する

細長い谷でzig-zagする現象は、勾配方向が最適点への直線方向とは限らないことを示します。[Gradient family comparison](#/compare/gradient-quadratic)ではMomentumやAdamと同じ初期点・budgetで確認できます。

## 停止条件と診断

目的値の変化だけで停止すると、scaleが小さいだけの点を収束と誤認することがあります。最低限、次を記録します。

- gradient norm
- projected gradient norm（boundsがある場合）
- step norm
- objective valueとbest-so-far
- function / gradient evaluation数
- learning rate
- NaN / overflow / line-search status
- iteration / wall-clock budget

凸問題でも、停止許容値が粗ければ高精度解ではありません。非凸問題ではgradient normが小さくてもlocal minimum、saddle、flat regionの可能性があります。

## Python

```python
import numpy as np


def objective(x: np.ndarray) -> float:
    return float((x[0] - 1.0) ** 2 + 20.0 * (x[1] + 2.0) ** 2)


def gradient(x: np.ndarray) -> np.ndarray:
    return np.array([2.0 * (x[0] - 1.0), 40.0 * (x[1] + 2.0)])


x = np.array([4.0, 3.0])
learning_rate = 0.04
for _ in range(2_000):
    g = gradient(x)
    if np.linalg.norm(g) < 1e-8:
        break
    candidate = x - learning_rate * g
    if objective(candidate) > objective(x):
        learning_rate *= 0.5
        continue
    x = candidate

print(x, objective(x), np.linalg.norm(gradient(x)))
```

この例の簡易backtrackingは教育用です。実務ではWolfe条件など、利用するline-search contractを明示します。

## 向いている条件

- smoothな連続最適化
- gradientが安価・信頼できる
- 一反復を軽くして大規模化したい
- convex問題、または局所解でよい非凸問題
- stochastic gradient変種へ移行できるmachine-learning問題

## 避ける／切り替える条件

- 離散・カテゴリ変数
- 不連続や評価失敗が頻発
- gradient noiseがstepを支配
- 強い一般制約を無視している
- 条件数が悪く極端に遅い → scaling、preconditioning、BFGS系
- 非滑らか正則化がある → [近接勾配法](#/learn/proximal-gradient)
- 曲率情報を使える → [BFGS](#/learn/bfgs)やtrust-region法

::: warning
同じ反復回数でも、目的評価、gradient評価、line searchの追加評価は異なります。手法比較ではoracle budgetと停止条件を揃えます。
:::
