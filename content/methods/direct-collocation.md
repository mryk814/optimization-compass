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
last_reviewed: 2026-07-18
---

状態とcontrolを時間mesh上の変数にし、dynamics defectを制約として同時に解くtrajectory optimization法です。

## 30秒でつかむ

この手法の気持ちは、**stateをsimulationだけに任せず、軌道全体を変数として置き、dynamicsとのずれをconstraintとして解きたい**というものです。

- 見ているもの: state history、control history、cost、dynamics defect、constraint violation
- 動かしているもの: mesh上のstateとcontrol
- 前進の判断: costの改善と、defect、path constraint、boundary constraintの同時成立
- 別に確認するもの: meshを細かくしたときの解の変化、solver時間、real-time deadline
- 恐れていること: 粗いmesh、discretization error、sparse構造の破綻、未処理のevent

変数は増えます。
その代わり、長いhorizonや不安定dynamicsでも、全区間のrollout感度を一つの初期点から伝え続けずに済む場合があります。

## まず確認すること

| 項目 | 確認内容 |
|---|---|
| dynamics | 連続時間systemとdiscretizationを定義できるか |
| mesh | eventや急変区間を表せる密度か |
| constraints | initial / terminal、path、control boundsを明示できるか |
| derivatives | defect Jacobianのsparse patternを利用できるか |
| initialization | stateとcontrolの初期軌道を用意できるか |
| real-time | solve timeとwarm startが運用deadlineに合うか |

costが下がっても、mesh上のdefectやconstraint violationが許容範囲に入るとは限りません。
solver status、連続時間へ戻したsimulation、real-time運用を別々に確認します。

## 点ではなく軌道を変数にする

連続時間system

$$
\dot{x}(t)=f(x(t),u(t),t)
$$

に対し、時間点ごとのstate $x_k$ とcontrol $u_k$ をdecision variablesとして並べます。
dynamicsをcollocation formulaで離散化し、隣接点の整合性をconstraintとしてNLP solverへ渡します。

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

長いhorizonや不安定systemではcollocationの疎構造が有利な場合があります。
一方、meshとdiscretizationを設計し、連続時間の挙動を別途検証する必要があります。

## 向く条件・避ける条件

向いている条件:

- known dynamicsを持つtrajectory optimization
- path / boundary constraintが多い
- sparse derivativeを利用できる
- warm startを使うMPC
- stateとcontrolの全履歴を説明したい

避ける／切り替える条件:

- dynamicsが未同定または強くstochastic
- discontinuous eventをmeshへ明示していない
- derivativeやscalingが不正確
- meshが粗くsolutionがgrid依存
- real-time deadlineにsolver時間が合わない

## Python

次はsingle-integrator $x_{k+1}=x_k+\Delta t\,u_k$ をEuler defectで表す最小例です。
厳密には高次collocationではなく、direct transcriptionの入口です。

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

この例は単純なdynamicsです。
実務ではintegration error、state constraints、units、solver statusを保存します。

## 診断値

軌道を位置だけで見せるとsolver状態が分かりません。
次を同期表示します。

- physical trajectory
- state history
- control history
- dynamics defect
- path constraint violation
- objective accumulation
- active bounds
- mesh point / refinement
- KKT residualとtermination reason

meshが粗いと、離散NLPでは可行でも連続systemへ戻すとconstraintを破ることがあります。
確認は、mesh上のdefectだけで終えず、高精度simulationとmesh変更の両方で行います。

1. mesh上のdefectを確認
2. 得られたcontrolで高精度simulation
3. mesh間でobjectiveとtrajectoryを比較
4. 誤差が大きい区間をrefine
5. warm startして再solve

cost、feasibility、mesh依存性、KKT residual、solver時間は別々の診断軸です。

## 失敗・切替の兆候

- mesh上のcostは改善するが、高精度simulationでconstraintを破る → meshをrefineし、discretization errorを確認する
- dynamics defectが停滞する → derivative、scaling、initial trajectoryを見直す
- path constraintがmesh間で破れる → event区間やmesh密度を見直す
- solver時間がreal-time deadlineを超える → mesh、warm start、problem size、専用solverを検討する
- dynamicsが未同定または強くstochastic → deterministicなdefect constraintを前提にしない定式化と比較する

::: warning
NLP solverの`success`は、連続時間問題の正しさを直接保証しません。
discretization error、model mismatch、simulation validationを別に確認します。
:::
