---
content_id: coordinate-descent
kind: method
method_id: M_COORDINATE_DESCENT
title_ja: 座標降下法
title_en: Coordinate Descent
summary: 全変数を同時に動かさず、一つまたは小さなblockだけを更新して安価な部分問題を反復する大規模最適化法です。
source_ids: [S055, S056, S066]
prerequisites: [method.gradient-descent]
related_ids: [proximal-gradient, fista, least-squares]
aliases: [/learn/coordinate-descent]
status: published
last_reviewed: 2026-07-16
---

全変数を同時に動かさず、一つまたは小さなblockだけを更新して安価な部分問題を反復する大規模最適化法です。

## 一回に何を解くか

現在点 $x$ の座標 $j$ だけを変えるとき、

$$
\min_d f(x + d e_j)
$$

という1次元部分問題を解きます。更新順はcyclic、random、greedy、block単位などがあります。

Lassoのように各座標更新がsoft-thresholdingで閉形式になる問題では、汎用勾配法より構造を直接使えます。

## Python: Lassoのcoordinate update

```python
import numpy as np


def soft_threshold(value: float, threshold: float) -> float:
    return float(np.sign(value) * max(abs(value) - threshold, 0.0))


rng = np.random.default_rng(3)
a = rng.normal(size=(80, 10))
true_x = np.zeros(10)
true_x[[1, 4, 8]] = [1.2, -1.8, 0.7]
b = a @ true_x + 0.05 * rng.normal(size=80)
lam = 0.1
x = np.zeros(a.shape[1])
column_norm = np.sum(a * a, axis=0)

for _ in range(1_000):
    previous = x.copy()
    for coordinate in range(a.shape[1]):
        residual_without_coordinate = b - a @ x + a[:, coordinate] * x[coordinate]
        correlation = a[:, coordinate] @ residual_without_coordinate
        x[coordinate] = soft_threshold(correlation, lam) / column_norm[coordinate]
    if np.linalg.norm(x - previous) < 1e-10:
        break

print(x)
```

この例はdense matrixを毎座標で再計算する教育実装です。実務ではresidualをincrementalに更新し、sparse構造やactive setを利用します。

## 更新順序

- cyclic: 実装が単純で再現的
- randomized: adversarialな順序を避けやすい
- greedy / Gauss-Southwell: 大きく改善しそうな座標を選ぶ
- block coordinate: coupledな変数群をまとめる
- asynchronous: 分散・並列だがstalenessを管理する

同じcoordinate descentでも選択ruleとpartial solve accuracyで挙動が変わります。

## 診断値

- objective / duality gap
- coordinate update norm
- full sweep数
- active coordinate数
- residual norm
- zero-to-nonzero / nonzero-to-zero transitions
- coordinate selection frequency
- cache / sparse operation time
- stopping tolerance

座標ごとの更新が小さくても、全体の勾配やduality gapが大きければ収束していません。

## 向いている条件

- 高次元・疎なproblem
- 各座標またはblockの部分問題が安価
- L1正則化やseparable penalty
- data matrixのcolumn accessが効率的
- warm startでregularization pathを解く

## 避ける／切り替える条件

- 変数間couplingが強く一座標ずつでは極端に遅い
- coordinate scalingが悪い
- nonseparable constraintを更新ごとに破る
- 部分問題が元問題と同じくらい高価
- asynchronous updateのstalenessが大きい
- stoppingを「一周した」だけで判定

::: note
iterationはcoordinate updateかfull sweepかを明記します。Gradient Descentの一反復とcoordinate update一回を直接比較しません。
:::

非滑らか正則化をfull-vector proxで扱う方法は[近接勾配法](#/learn/proximal-gradient)、加速法は[FISTA](#/learn/fista)で確認できます。
