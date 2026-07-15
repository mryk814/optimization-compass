---
content_id: direct-collocation
kind: method
method_id: M_DIRECT_COLLOCATION
title_ja: Direct Collocation
title_en: Direct Collocation
summary: 状態とcontrolを時間mesh上の変数にし、dynamics defectを制約として同時に解くtrajectory optimization法です。
source_ids: [S042, S043, S050, S076]
prerequisites: [constrained-continuous]
related_ids: [constrained-continuous, least-squares]
aliases: [/learn/direct-collocation]
status: published
last_reviewed: 2026-07-15
---

状態とcontrolを時間mesh上の変数にし、dynamics defectを制約として同時に解くtrajectory optimization法です。

## 点ではなく軌道を変数にする

連続時間system

$$
\dot{x}(t)=f(x(t),u(t),t)
$$

に対し、時間点ごとのstate $x_k$ とcontrol $u_k$ をdecision variablesとして並べます。dynamicsをcollocation formulaで離散化し、隣接点の整合性をconstraintとしてNLP solverへ渡します。

これにより、

- initial / terminal condition
- path constraint
- control bounds
- obstacle / safety constraint
- integral cost

を同じmodelで扱えます。

## Shootingとの違い

| 観点 | Direct collocation | Direct shooting |
|---|---|---|
| state | decision variableとして保持 | forward simulationで消去 |
| dynamics | defect constraint | rollout |
| sparsity | banded / sparse | sensitivityが長時間伝播 |
| unstable dynamics | 比較的扱いやすい | rolloutが発散しやすい |
| variable数 | 多い | 少ない |

長いhorizonや不安定systemではcollocationの疎構造が有利な場合があります。一方、meshとdiscretizationを設計する必要があります。

## 教育用の直接transcription例

次はsingle-integrator $x_{k+1}=x_k+\Delta t\,u_k$ をEuler defectで表す最小例です。厳密には高次collocationではなく、direct transcriptionの入口です。

```python
import numpy as np
from scipy.optimize import minimize

steps = 20
dt = 1.0 / steps


def unpack(vector: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    state = vector[: steps + 1]
    control = vector[steps + 1 :]
    return state, control


def objective(vector: np.ndarray) -> float:
    _, control = unpack(vector)
    return float(dt * np.sum(control * control))


def equality_constraints(vector: np.ndarray) -> np.ndarray:
    state, control = unpack(vector)
    dynamics = state[1:] - state[:-1] - dt * control
    return np.concatenate(([state[0]], dynamics, [state[-1] - 1.0]))


initial = np.concatenate((np.linspace(0.0, 1.0, steps + 1), np.ones(steps)))
result = minimize(
    objective,
    initial,
    method="SLSQP",
    constraints={"type": "eq", "fun": equality_constraints},
    bounds=[(None, None)] * (steps + 1) + [(-2.0, 2.0)] * steps,
    options={"ftol": 1e-10, "maxiter": 500},
)

state, control = unpack(result.x)
print(result.success, objective(result.x), np.linalg.norm(equality_constraints(result.x)))
```

## 何を可視化するか

軌道を位置だけで見せるとsolver状態が分かりません。次を同期表示します。

- physical trajectory
- state history
- control history
- dynamics defect
- path constraint violation
- objective accumulation
- active bounds
- mesh point / refinement
- KKT residualとtermination reason

## Mesh refinement

meshが粗いと、離散NLPでは可行でも連続systemへ戻すとconstraintを破ることがあります。

確認手順:

1. mesh上のdefectを確認
2. 得られたcontrolで高精度simulation
3. mesh間でobjectiveとtrajectoryを比較
4. 誤差が大きい区間をrefine
5. warm startして再solve

::: warning
NLP solverの`success`は、連続時間問題の正しさを直接保証しません。discretization error、model mismatch、simulation validationを別に確認します。
:::

## 向いている／避ける条件

向いている:

- known dynamicsを持つtrajectory optimization
- path / boundary constraintが多い
- sparse derivativeを利用できる
- warm startを使うMPC
- stateとcontrolの全履歴を説明したい

避ける／条件付き:

- dynamicsが未同定または強くstochastic
- discontinuous eventをmeshへ明示していない
- derivativeやscalingが不正確
- meshが粗くsolutionがgrid依存
- real-time deadlineにsolver時間が合わない
