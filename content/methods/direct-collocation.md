---
content_id: direct-collocation
kind: method
method_id: M_DIRECT_COLLOCATION
title_ja: Direct Collocation
title_en: Direct Collocation
summary: 状態とcontrolを時間mesh上の変数にし、dynamics defectを制約として同時に解くtrajectory optimization法です。
source_ids: [S042, S043, S050, S076, S102]
prerequisites: [concept.trajectory-variable, concept.dynamics-defect, concept.path-terminal-constraints, concept.time-discretization]
related_ids: [concept.receding-horizon, constrained-continuous, least-squares]
visualization_ids: [pendulum-collocation-coarse, pendulum-collocation-refined, pendulum-model-rollout-failure]
comparison_ids: [COMPARE_PENDULUM_COLLOCATION_MESH]
aliases: [/learn/direct-collocation]
status: published
last_reviewed: 2026-07-26
---

状態とcontrolを時間mesh上の変数にし、dynamics defectを制約として同時に解くtrajectory optimization法です。

## 30秒でつかむ

この手法の気持ちは、**状態（state）をsimulationだけに任せない**ことです。
軌道全体を変数として置き、dynamicsとのずれを制約（constraint）として解きます。

- 見ているもの: state history、control history、cost、dynamics defect、constraint violation
- 動かしているもの: mesh上のstateとcontrol
- 前進の判断: コスト（cost）の改善、defect、経路制約（path constraint）、境界制約（boundary constraint）の同時成立
- 別に確認するもの: 時間格子（mesh）を細かくしたときの解の変化、solver時間、real-time deadline
- 恐れていること: 粗いmesh、discretization error、sparse構造の破綻、未処理のevent

変数は増えます。
その代わり、長いhorizonや不安定dynamicsでも、全区間のrollout感度を一つの初期点から伝え続けずに済む場合があります。

同じ軌道でも、mesh点とcontrolによる更新は別の対象です。
隣接点のdynamics defectも分けて読みます。

mesh node上のviolationがtolerance内なら、軌道全体も可行でしょうか。
固定pendulum教材では、そうとは限りません。

![同じpendulum swing-upをN=20、N=40、gravityを10%変えたvalidation rolloutで実行し、mesh node上と区間再構成またはvalidation rollout上のpath violationを反復ごとに比較した結果。node上では3runとも許容値へ近づくが、区間内では違反の残り方が異なる。](./media/optimal-control-mesh-execution.svg "固定Python Traceの実行結果です。mesh node上の収束と区間内またはmodel mismatch下の可行性を分けて読みます。連続時間可行性や実機安全性は保証しません。")

上段では3runともnode上のviolationが下がります。
下段ではN=40がN=20より小さくなる一方、model mismatchのvalidation rolloutには大きな違反が残ります。

## まず確認すること

| 項目 | 確認内容 |
|---|---|
| dynamics | 連続時間systemとdiscretizationを定義できるか |
| mesh | eventや急変区間を表せる密度か |
| constraints | initial / terminal、path、control boundsを明示できるか |
| derivatives | defect Jacobianのsparse patternを利用できるか |
| initialization | stateとcontrolの初期軌道を用意できるか |
| real-time | solve timeとwarm startが運用deadlineに合うか |

コスト（cost）が下がっても、mesh上のdefectやconstraint violationが許容範囲に入るとは限りません。
solver status、連続時間へ戻したsimulation、real-time運用を別々に確認します。

## 点ではなく軌道を変数にする

連続時間system

$$
\dot{x}(t)=f(x(t),u(t),t)
$$

に対し、時間点ごとのstate $x_k$ とcontrol $u_k$ をdecision variablesとして並べます。
dynamicsはcollocation formulaで離散化します。
隣接点の整合性をNLPの制約（constraint）として渡します。

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
一方、時間格子（mesh）とdiscretizationを設計し、連続時間の挙動を別途検証する必要があります。

## 向く条件・避ける条件

向いている条件:

- known dynamicsを持つtrajectory optimization
- 経路制約や境界制約の数が多い
- sparse derivativeを利用できる
- warm startを使うMPC
- 状態（state）とcontrolの全履歴を説明したい

避ける／切り替える条件:

- dynamicsが未同定または強くstochastic
- discontinuous eventをmeshへ明示していない
- derivativeやscalingが不正確
- 時間格子（mesh）の粗さでsolutionがgrid依存
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
実務ではintegration errorとstate constraintsを保存します。
単位とsolverの停止状態も別々に保存します。

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
- KKT条件の残差（residual）とtermination reason

粗いmeshでは、離散NLPが可行でも連続systemへ戻すとconstraintを破ることがあります。
確認は、mesh上のdefectだけで終えず、高精度simulationとmesh変更の両方で行います。

1. mesh上のdefectを確認
2. 得られたcontrolで高精度simulation
3. mesh間でobjectiveとtrajectoryを比較
4. 誤差が大きい区間をrefine
5. warm startして再solve

コスト（cost）とfeasibilityは別の診断軸です。
mesh依存性、KKT residual、solver時間も分けて読みます。

## 失敗・切替の兆候

- 時間格子（mesh）上のコスト（cost）は改善するが、高精度simulationで制約（constraint）を破る → 時間格子を細分化し、discretization errorを確認する
- dynamics defectが停滞する → derivative、scaling、initial trajectoryを見直す
- 経路制約（path constraint）の違反がmesh間に残る → event区間やmesh密度を見直す
- solver時間がreal-time deadlineを超える → mesh、warm start、problem size、専用solverを検討する
- dynamicsが未同定または強くstochastic → defectを制約として置く決定論的な前提に依存しない定式化と比較する

::: warning
NLPの`success`は、連続時間問題の正しさを直接保証しません。
discretization error、model mismatch、simulation validationを別に確認します。
:::

## 次に読む

まず[trajectory variable](#/learn/concept.trajectory-variable)でstateとcontrolを同時に持つ意味を確認します。[dynamics defect](#/learn/concept.dynamics-defect)ではmesh上の等式制約を読みます。[path・terminal制約](#/learn/concept.path-terminal-constraints)で制約を評価する時刻を確認し、[時間discretization](#/learn/concept.time-discretization)でmesh refinementへ進みます。

[pendulum swing-up Case](#/gallery/EC029)ではnode feasibilityと区間再構成を分けます。[mesh sensitivity Compare](#/compare/COMPARE_PENDULUM_COLLOCATION_MESH)ではN=20とN=40をcontrast-onlyで確認できます。観測ごとに再solveする用途では[receding horizon](#/learn/concept.receding-horizon)へ進みます。
