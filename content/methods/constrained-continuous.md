---
content_id: constrained-continuous
kind: method
method_id: MF_CONSTRAINED_NLP
title_ja: 制約付き連続最適化
title_en: Constrained Continuous Optimization
summary: 目的値だけでなくprimal feasibility・stationarity・active constraint・停止理由を同時に追い、実行可能な連続解を求める最適化familyです。
source_ids: [S017, S029, S030, S055]
prerequisites: [concept.convexity]
related_ids: [concept.convexity, lp-qp-conic, direct-collocation, lbfgsb]
visualization_ids: [constrained-disk-feasible-region]
comparison_ids: []
aliases: [/learn/constrained-continuous]
visualization_aliases: [constrained-disk-feasible-region|/theater/constrained-continuous]
comparison_aliases: []
status: published
last_reviewed: 2026-07-15
---

目的値だけでなくprimal feasibility・stationarity・active constraint・停止理由を同時に追い、実行可能な連続解を求める最適化familyです。

## 問題の形

$$
\min_x f(x)
$$

subject to

$$
g_i(x)\le0,\quad h_j(x)=0,\quad l\le x\le u.
$$

infeasibleな点で目的値が低くても候補解ではありません。まず「何がhard constraintか」「どの許容誤差まで満たせば実行可能か」を定義します。

## KKT条件をどう読むか

正則性の下で局所解は、Lagrangian

$$
L(x,\lambda,\nu)=f(x)+\sum_i\lambda_i g_i(x)+\sum_j\nu_j h_j(x)
$$

について概ね次を満たします。

- primal feasibility
- stationarity: $\nabla_xL=0$
- dual feasibility: $\lambda_i\ge0$
- complementarity: $\lambda_i g_i(x)=0$

active constraintは解で等号になる不等式です。目的改善方向が制約境界に遮られ、境界上が最適になることがあります。

## Algorithm familyの違い

- SQP / SLSQP: 局所QP subproblemとmerit / line search
- interior-point: barrierで境界内部を進みprimal-dual systemを解く
- augmented Lagrangian: constraint violationをmultiplierとpenaltyで管理
- active-set: active constraint集合を更新
- projected gradient: 単純集合へprojection
- trust-region constrained: 局所modelとfeasibilityを半径内で管理

同じ「制約付きsolver」でも必要derivative、sparsity、feasible start、statusの意味が異なります。

## Python: SLSQP

```python
import numpy as np
from scipy.optimize import minimize


def objective(x: np.ndarray) -> float:
    return float((x[0] - 1.0) ** 2 + (x[1] - 2.0) ** 2)


def objective_gradient(x: np.ndarray) -> np.ndarray:
    return np.array([2.0 * (x[0] - 1.0), 2.0 * (x[1] - 2.0)])


def inequality(x: np.ndarray) -> float:
    return float(x[0] + x[1] - 2.0)


result = minimize(
    objective,
    x0=np.array([0.0, 0.0]),
    jac=objective_gradient,
    method="SLSQP",
    bounds=[(-1.0, 2.0), (-1.0, 3.0)],
    constraints={"type": "ineq", "fun": inequality},
    options={"ftol": 1e-10, "maxiter": 500},
)

violation = max(0.0, -inequality(result.x))
print(result.success, result.x, result.fun, violation, result.message)
```

SciPyの`ineq` conventionは関数値が0以上です。modeling systemごとにconstraint sign conventionを確認します。

## Feasible start

solverによって、

- infeasible startを許す
- phase-Iでfeasibilityを探す
- strictly interiorな初期点を必要とする
- boundsへprojectionする

などが異なります。初期点がinfeasibleな場合、objective改善よりconstraint restorationが先に進むことがあります。

## Scalingとderivative

constraint値、variable、objectiveのscaleが大きく違うとKKT systemが悪条件になります。

確認:

- gradient / Jacobian directional check
- sparse pattern
- finite-difference step
- variable scaling
- constraint normalization
- Hessian / quasi-Newton option
- factorization status

## 診断値

- maximum constraint violation
- equality residual
- stationarity / KKT residual
- complementarity
- active constraints
- objective and best feasible objective
- step norm / trust radius / barrier parameter
- function / gradient / Jacobian evaluation数
- termination reason

[Feasible-region Theater](#/theater/constrained-continuous)では、unconstrained optimum、feasible region、constrained optimum、failure contrastを区別して表示します。

## Alternative-first

- LP / convex QP / conic form → [専用凸solver](#/learn/lp-qp-conic)
- equalityを安全に変数消去できる → dimension削減
- simple boundsだけ → [L-BFGS-B](#/learn/lbfgsb)
- trajectory dynamicsが中心 → [Direct Collocation](#/learn/direct-collocation)
- projectionが閉形式 → projected / proximal method

## 失敗・切替の兆候

- constraint violationが減らない
- KKT residualが停滞
- `success`でもviolationが許容値を超える
- Jacobian rank deficiency / constraint qualification failure
- penaltyを増やしてill-conditioning
- bad scalingでtiny step
- non-smooth / noisy constraintをsmooth NLPへ入れる
- discrete条件を連続緩和の丸めだけで済ませる

::: warning
目的値が良いinfeasible点と、目的値はやや悪いfeasible点を同じランキングへ入れません。実行可能性、最適性、数値許容値を別々に報告します。
:::
