---
content_id: lp-qp-conic
kind: method
method_id: MF_LP_QP_CONIC
title_ja: LP・QP・錐最適化
title_en: Linear, Quadratic, and Conic Optimization
summary: 線形・凸二次・錐構造を明示したmodelを専用solverへ渡し、primal・dual・gap・infeasibility情報まで利用する凸最適化familyです。
source_ids: [S004, S010, S012, S014, S055]
prerequisites: [concept.convexity]
related_ids: [concept.convexity, constrained-continuous, dual-simplex, branch-and-cut]
visualization_ids: []
comparison_ids: []
aliases: [/learn/lp-qp-conic]
visualization_aliases: []
comparison_aliases: []
status: published
last_reviewed: 2026-07-15
---

線形・凸二次・錐構造を明示したmodelを専用solverへ渡し、primal・dual・gap・infeasibility情報まで利用する凸最適化familyです。

## 三つの代表形

### Linear program

$$
\min_x c^Tx\quad\text{subject to}\quad Ax\le b,　A_{eq}x=b_{eq}
$$

### Convex quadratic program

$$
\min_x \frac{1}{2}x^TPx+q^Tx\quad\text{subject to linear constraints},
$$

ここで $P\succeq0$ なら目的関数は凸です。

### Conic program

$$
\min_x c^Tx\quad\text{subject to}\quad Ax+s=b,　s\in K
$$

$K$として非負orthant、second-order cone、positive semidefinite coneなどを使います。norm、robust bound、semidefinite relaxationを共通形式で表現できます。

## 構造を隠さない理由

convex構造をblack-box objectiveへ包むと、

- dual variable
- optimality gap
- infeasibility certificate
- sensitivity
- sparsity
- warm start

を利用しにくくなります。専用solverが受け取れる係数modelとして保つこと自体が重要です。

## Python: 生産LP

```python
import numpy as np
from scipy.optimize import linprog

profit = np.array([5.0, 4.0])
resource_use = np.array([
    [2.0, 1.0],
    [1.0, 2.0],
])
resource_capacity = np.array([8.0, 8.0])

result = linprog(
    c=-profit,
    A_ub=resource_use,
    b_ub=resource_capacity,
    bounds=[(0.0, None), (0.0, None)],
    method="highs",
)

if not result.success:
    raise RuntimeError(result.message)
print(result.x, -result.fun, result.status, result.message)
```

maximizationを`-profit`のminimizationへ変換したため、出力時に符号を戻しています。単位、目的方向、constraint signをmodel reviewで明示します。

## Primalとdualを読む

convex problemで適切な正則性があれば、primal objectiveとdual objectiveの差がoptimality gapになります。dual variableは、constraint boundをわずかに変えたときの価値を表すsensitivityとして解釈できる場合があります。

ただし、

- scaling
- degeneracy
- regularization
- solver tolerance
- presolve変換

により、数値的なdual値の読み方は変わります。

## Solver family

- simplex / dual simplex: basis、warm start、LP再最適化
- interior-point / barrier: 大規模・疎な凸problem
- operator splitting: QPやconic problemの反復solve
- first-order conic: 中精度・巨大problem
- modeling layer: CVXPY等がcanonicalizationしてbackendへ渡す

modeling libraryとsolverを混同しません。どのbackend、version、optionが使われたかを保存します。

## Statusと診断

- primal feasibility residual
- dual feasibility residual
- absolute / relative gap
- complementarity
- iteration / factorization time
- presolve reduction
- active constraints
- infeasible / unbounded certificate
- numerical warning
- warm-start reuse

`infeasible`、`unbounded`、`infeasible_or_unbounded`、`iteration_limit`は異なる状態です。目的値だけを読みません。

## Alternative-first

- linear least squares → QR / SVD
- shortest path / max flow / matching → graph algorithm
- separable closed form → 解析解
- pure linear system → factorization
- LP relaxationだけではinteger条件を満たさない → MILP / CP-SAT

## 向いている条件

- 係数・matrixとしてmodel化できる
- convexityが成立する
- certificateやdual情報が重要
- sparse structureを使いたい
- repeated solveやwarm startがある
- high accuracyまたは明確なstatusが必要

## 失敗・切替の兆候

- $P$が非正半定値なのにconvex QPとして扱う
- Big-Mが巨大で数値不安定
- unit scaleが何桁も異なる
- cone relaxationが現実の条件を緩めすぎる
- integer decisionを連続解の丸めだけで済ませる
- solver statusを成功／失敗の二値へ潰す
- black-box simulationを無理に係数modelへ置換

::: warning
solver間比較ではmodel canonicalization、tolerance、presolve、hardware、warm startを揃えます。反復回数だけでは一反復の仕事量が違うため公平ではありません。
:::

LP basis再最適化は[Dual Simplex](#/learn/dual-simplex)、MILP探索との接続は[Branch-and-Cut](#/learn/branch-and-cut)で確認できます。
