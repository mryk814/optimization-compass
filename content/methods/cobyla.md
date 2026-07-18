---
content_id: cobyla
kind: method
method_id: M_COBYLA
title_ja: COBYLA
title_en: Constrained Optimization BY Linear Approximations
summary: 目的関数と制約の値だけから局所線形modelを作り、trust-region半径内で一般不等式制約付きの局所解を探す微分不要法です。
source_ids: [S002, S018, S056]
prerequisites: [concept.derivative-free, constrained-continuous]
related_ids: [constrained-continuous, mads, pattern-search]
aliases: [/learn/cobyla]
status: published
last_reviewed: 2026-07-18
---

目的関数と制約の値だけから局所線形modelを作り、trust-region半径内で一般不等式制約付きの局所解を探す微分不要法です。

## 30秒でつかむ

COBYLAは勾配を要求しない代わりに、近くの評価点から目的関数とconstraintの傾きを推定します。

- 見ているもの: objective、constraint value、simplexのgeometry
- 動かしているもの: 局所linear model、trust-region radius、候補点
- 前進の判断: feasibleな点でobjectiveが改善し、modelと実評価の差が抑えられること
- 恐れていること: scaleの不一致、noise、細いfeasible region、局所modelの退化

## 何を近似するか

COBYLAはsimplex状の補間点から、目的関数と各constraintの局所線形近似を作ります。そのmodel上でtrust-region radius内のstepを求め、実評価でmodelを更新します。

必要なのはvalue evaluationであり、勾配やJacobianを直接要求しません。一方で、局所modelの品質にはscale、geometry、noiseが影響します。

## 先に確認すること

- objectiveとconstraintをvalue evaluationだけで評価できるか
- constraintを一貫して$c_i(x)\ge0$へ表せるか
- 初期trust-region scale（`rhobeg`）と変数・constraintのscaleが釣り合っているか
- global optimumではなく、局所的なfeasible candidateで足りるか

## Constraintの表現

実装では通常、すべてのconstraintを

$$
c_i(x)\ge0
$$

のような不等式へ揃えます。equalityは二つのinequalityやtolerance帯として表すことがありますが、厳密等式を近似帯へ変える意味を確認します。

## Python

```python
import numpy as np
from scipy.optimize import minimize


def objective(x: np.ndarray) -> float:
    return float((x[0] - 1.0) ** 2 + (x[1] - 2.0) ** 2)


def inside_disk(x: np.ndarray) -> float:
    return float(1.0 - x[0] ** 2 - x[1] ** 2)


def above_line(x: np.ndarray) -> float:
    return float(x[0] + x[1] - 0.5)


result = minimize(
    objective,
    x0=np.array([0.2, 0.4]),
    method="COBYLA",
    constraints=[
        {"type": "ineq", "fun": inside_disk},
        {"type": "ineq", "fun": above_line},
    ],
    options={"rhobeg": 0.5, "tol": 1e-7, "maxiter": 3_000},
)

violation = max(0.0, -inside_disk(result.x), -above_line(result.x))
print(result.success, result.x, result.fun, violation, result.message)
```

SciPy版のbounds対応、`catol`、`rhobeg`、`tol`の意味は利用versionの公式documentationを確認します。

## Trust-region radius

- `rhobeg`: 初期探索scale
- final radius / `tol`: 終了時の局所model scale
- 大きすぎる: 局所線形modelが悪い
- 小さすぎる: 初期点近傍から抜けにくい

変数を無次元化し、constraint値のscaleも揃えます。

## 最初に見る診断値

- objective / best feasible objective
- maximum constraint violation
- trust-region radius
- function evaluation数
- feasible evaluation fraction
- model geometry
- failed / non-finite evaluation数
- termination reason

COBYLAはderivative-based KKT residualを直接返さない場合があるため、feasibilityと局所perturbationによる改善余地を別に確認します。

## 向いている条件

- 低〜中次元のsmoothまたはmoderately smooth black-box
- 勾配 / Jacobianが利用できない
- 一般inequality constraint
- evaluationが比較的安価
- local feasible candidateが欲しい

## 失敗・切替の兆候

- exact equalityが重要 → equalityを扱える別の制約法を検討する
- strong noiseで線形modelが不安定 → repeated evaluationやnoise-aware methodを比較する
- 高次元 → modelの評価数とgeometryを確認し、別のderivative-free法を検討する
- 1評価が極端に高価 → 低評価budget向けの手法やsurrogateを比較する
- discontinuous feasibility → COBYLAの連続local modelを前提にしない
- global optimumやcertificateが必要 → local methodの保証範囲を超えるため、別のsolverを検討する
- feasible regionが極端に細い → 初期点、scaling、制約の表現を見直す

::: warning
COBYLAがconstraint violationを小さくしたことと、連続modelの大域最適性は別です。異なる初期点とscaleで再確認します。
:::
