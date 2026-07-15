---
content_id: slsqp
kind: method
method_id: M_SLSQP
title_ja: SLSQP
title_en: Sequential Least Squares Programming
summary: 一般制約付きの滑らかな問題を逐次二次近似し、QP subproblem・line search・KKT診断で局所解を探すSQP実装です。
source_ids: [S002, S056, S064]
prerequisites: [constrained-continuous]
related_ids: [constrained-continuous, interior-point-nlp, augmented-lagrangian]
aliases: [/learn/slsqp]
status: published
last_reviewed: 2026-07-15
---

一般制約付きの滑らかな問題を逐次二次近似し、QP subproblem・line search・KKT診断で局所解を探すSQP実装です。

## 一反復で解くもの

現在点で目的と制約を線形化し、Lagrangian Hessianまたはその近似を使ってquadratic programming subproblemを作ります。subproblemのstepをline searchやmerit functionで調整し、

- objective improvement
- constraint violation
- stationarity

を同時に進めます。

SLSQPという名前はKraftのsoftware系統を指し、一般的なSQP familyすべてと同一ではありません。

## Python

```python
import numpy as np
from scipy.optimize import minimize


def objective(x: np.ndarray) -> float:
    return float((x[0] - 1.0) ** 2 + 2.0 * (x[1] - 2.0) ** 2)


def gradient(x: np.ndarray) -> np.ndarray:
    return np.array([2.0 * (x[0] - 1.0), 4.0 * (x[1] - 2.0)])


def inequality(x: np.ndarray) -> float:
    return float(x[0] + x[1] - 2.0)


def equality(x: np.ndarray) -> float:
    return float(x[0] - 0.5 * x[1])


result = minimize(
    objective,
    x0=np.array([0.8, 1.6]),
    jac=gradient,
    method="SLSQP",
    bounds=[(-1.0, 3.0), (-1.0, 3.0)],
    constraints=[
        {"type": "ineq", "fun": inequality},
        {"type": "eq", "fun": equality},
    ],
    options={"ftol": 1e-10, "maxiter": 500},
)

violations = [max(0.0, -inequality(result.x)), abs(equality(result.x))]
print(result.success, result.x, result.fun, max(violations), result.message)
```

SciPyのinequality conventionは関数値が0以上です。modeling toolにより符号が逆なので確認します。

## Derivativeとscale

SLSQPはobjective gradientとconstraint Jacobianの品質に敏感です。有限差分を使う場合、

- step size
- variable bounds
- noise
- unit scale
- nondifferentiable branch

を確認します。constraint値のscaleが大きく違うとmerit functionとQPが悪条件になります。

## 診断値

- maximum constraint violation
- equality residual
- objective value
- projected / Lagrangian gradient
- step norm
- QP subproblem status
- function / gradient / Jacobian evaluation数
- active constraints
- iteration limit / line-search failure
- termination message

`success=True`だけでなく、実際のconstraint residualを再計算します。

## 向いている条件

- 低〜中規模のsmooth NLP
- bounds・等式・不等式が混在
- gradient / Jacobianが利用可能
- local solutionでよい
- warm start可能な近いproblemを繰り返す

## 避ける／切り替える条件

- 強いnoiseや不連続constraint
- sparseな巨大NLPでdense処理が支配
- infeasible modelをalgorithm tuningで解決しようとする
- Jacobian rank deficiency
- scaleが極端
- discrete variable
- global certificateが必要

大規模疎NLPでは[Interior-point NLP](#/learn/interior-point-nlp)、constraint分離やouter loopを使う場合は[Augmented Lagrangian](#/learn/augmented-lagrangian)を比較します。

::: warning
`ftol`は実装の複数停止判定へ影響します。異なるsolverの`tol=1e-6`を同じ精度だと見なさず、KKT residualとconstraint violationを比較します。
:::
