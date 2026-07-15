---
content_id: interior-point-nlp
kind: method
method_id: M_INTERIOR_POINT_NLP
title_ja: 非線形内点法
title_en: Nonlinear Interior-Point Method
summary: 不等式制約へbarrierを導入し、primal・dual・slack・complementarityを同時に更新して大規模な滑らかNLPを解く方法です。
source_ids: [S017, S029, S056, S087]
prerequisites: [constrained-continuous]
related_ids: [constrained-continuous, slsqp, augmented-lagrangian]
aliases: [/learn/interior-point-nlp]
status: published
last_reviewed: 2026-07-15
---

不等式制約へbarrierを導入し、primal・dual・slack・complementarityを同時に更新して大規模な滑らかNLPを解く方法です。

## 境界の内側を進む

不等式 $g_i(x)\le0$ にslack $s_i>0$ を導入し、barrier parameter $\mu$ を使って境界へ近づきます。log barrierの単純な形は

$$
f(x)-\mu\sum_i\log(-g_i(x))
$$

です。primal-dual法では、KKT systemへslackとdual multiplierを含め、$\mu$を下げながらcomplementarityを0へ近づけます。

## 「feasible interior」が必要とは限らない

古典的barrierの説明ではstrictly feasible startを想定しますが、現代実装はrestoration phase、filter、slack、infeasible-start primal-dual法などを持つ場合があります。実装が何を要求するかを確認します。

## Python: trust-constrでbarrierを観察する

```python
import numpy as np
from scipy.optimize import NonlinearConstraint, minimize


def objective(x: np.ndarray) -> float:
    return float((x[0] - 1.0) ** 2 + (x[1] - 2.0) ** 2)


def gradient(x: np.ndarray) -> np.ndarray:
    return np.array([2.0 * (x[0] - 1.0), 2.0 * (x[1] - 2.0)])


def constraint(x: np.ndarray) -> np.ndarray:
    return np.array([x[0] ** 2 + x[1] ** 2])


unit_disk = NonlinearConstraint(constraint, -np.inf, 1.0)
result = minimize(
    objective,
    x0=np.array([0.2, 0.2]),
    jac=gradient,
    method="trust-constr",
    constraints=[unit_disk],
    options={"gtol": 1e-9, "barrier_tol": 1e-9, "maxiter": 1_000},
)

violation = max(0.0, constraint(result.x)[0] - 1.0)
print(result.success, result.x, result.fun, violation, result.message)
```

SciPyの`trust-constr`とIpopt等の実装は同じではありません。linear solver、Hessian approximation、filter、scaling、restorationをversion付きで記録します。

## KKT systemとsparsity

大規模NLPでは、目的評価よりKKT matrixのfactorizationが支配することがあります。

見るべき構造:

- Jacobian sparsity
- Hessian / Lagrangian Hessian sparsity
- symmetric indefinite linear solve
- fill-in
- ordering
- regularization
- iterative refinement

automatic differentiationで値が得られても、sparse patternを失うとmemoryが増大します。

## 診断値

- primal infeasibility
- dual infeasibility / stationarity
- complementarity
- barrier parameter $\mu$
- step acceptance / filter status
- restoration phase
- KKT factorization status
- regularization magnitude
- function / derivative evaluation数
- termination reason

barrier parameterが小さくてもprimal infeasibilityが残っていれば、良い解ではありません。

## 向いている条件

- smoothな大規模・疎NLP
- boundsと多数の一般制約
- gradient / Jacobian / HessianまたはHVPが利用可能
- KKT residualを追いたい
- local solutionで十分、またはconvex問題

## 避ける／切り替える条件

- discontinuous / noisy constraint
- discrete variable
- derivativeが不正確
- KKT solveがmemoryを超える
- scaleが悪くregularizationが増大
- infeasible modelをbarrier調整で隠す
- strict real-time budgetにfactorizationが合わない

::: warning
内点法のiteration数は少なく見えることがありますが、一反復のKKT solveは重い場合があります。SLSQPやfirst-order法との比較ではfactorization・derivative費用を含むwall timeを記録します。
:::
