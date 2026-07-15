---
content_id: augmented-lagrangian
kind: method
method_id: M_AUGMENTED_LAGRANGIAN
title_ja: 拡張Lagrangian法
title_en: Augmented Lagrangian Method
summary: 制約違反へpenaltyを加えつつmultiplierを更新し、極端なpenaltyだけに依存せず実行可能性と目的改善を両立する方法です。
source_ids: [S018, S029, S055, S056]
prerequisites: [constrained-continuous]
related_ids: [constrained-continuous, slsqp, interior-point-nlp, admm]
aliases: [/learn/augmented-lagrangian]
status: published
last_reviewed: 2026-07-15
---

制約違反へpenaltyを加えつつmultiplierを更新し、極端なpenaltyだけに依存せず実行可能性と目的改善を両立する方法です。

## Equality constraintの代表形

$$
\min_x f(x)\quad\text{subject to}\quad c(x)=0
$$

に対し、augmented Lagrangian

$$
L_\rho(x,\lambda)=f(x)+\lambda^Tc(x)+\frac{\rho}{2}\|c(x)\|^2
$$

を作ります。outer iterationで、

1. $x$について $L_\rho$ を近似最小化
2. $\lambda\leftarrow\lambda+\rho c(x)$
3. constraint progressに応じて$\rho$を調整

します。

pure penalty法のように$\rho$を無限に大きくする必要を減らし、multiplierがconstraintの感度を表します。

## Python: 小さな等式制約

```python
import numpy as np
from scipy.optimize import minimize


def objective(x: np.ndarray) -> float:
    return float((x[0] - 2.0) ** 2 + (x[1] + 1.0) ** 2)


def constraint(x: np.ndarray) -> np.ndarray:
    return np.array([x[0] + x[1] - 1.0])


x = np.array([0.0, 0.0])
multiplier = np.zeros(1)
penalty = 1.0

for _ in range(30):
    def augmented(value: np.ndarray) -> float:
        residual = constraint(value)
        return float(
            objective(value)
            + multiplier @ residual
            + 0.5 * penalty * (residual @ residual)
        )

    result = minimize(augmented, x, method="BFGS")
    x = result.x
    residual = constraint(x)
    multiplier = multiplier + penalty * residual
    if np.linalg.norm(residual) < 1e-8:
        break
    penalty = min(10.0 * penalty, 1e8)

print(x, objective(x), constraint(x), multiplier)
```

これは教育用outer loopです。実装ではinner solve tolerance、inequality treatment、multiplier safeguards、penalty update ruleを明示します。

## Inner solveとouter solve

各outer iterationでinner problemを高精度に解きすぎると費用を浪費し、粗すぎるとmultiplier updateが不安定になります。

記録するもの:

- outer iteration数
- inner iteration / evaluation数
- inner tolerance
- constraint residual
- multiplier norm
- penalty $\rho$
- objective
- stationarity
- termination reason

## Inequality constraint

inequalityにはslack、projected multiplier update、positive-part penaltyなどを使う変種があります。単純に$g(x)^2$をpenaltyへ入れると、満たされている不等式まで罰する可能性があります。

## ADMMとの関係

ADMMは分離構造を持つaugmented Lagrangianを交互更新します。しかし、一般のaugmented-Lagrangian methodとADMMの収束条件・更新順・対象problemは同じではありません。

## 向いている条件

- equalityまたは一般制約をouter-inner構造で扱う
- constraintを分離して既存unconstrained solverを再利用したい
- pure penaltyのill-conditioningを緩和したい
- warm startや近いproblemの反復solve
- derivative-free inner solverと組み合わせるvariant

## 失敗・切替の兆候

- penaltyだけ増えconstraintが減らない
- multiplierが発散
- inner solve failureを無視してouter update
- constraint scaleが極端に違う
- infeasible model
- non-smooth constraintをsmooth inner solverへ渡す
- terminationがinner objectiveだけ

::: warning
constraint residualが小さくてもstationarityが悪ければ局所最適条件を満たしていません。objective、feasibility、stationarityを別々に報告します。
:::
