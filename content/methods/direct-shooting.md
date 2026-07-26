---
content_id: direct-shooting
kind: method
method_id: M_DIRECT_SHOOTING
title_ja: Direct Shooting
title_en: Direct Shooting
summary: 時間ごとのcontrolを最適化変数にし、初期状態からdynamicsを前進simulationして得たtrajectoryのcostと制約を改善する最適制御法です。
source_ids: [S042, S043, S050, S076]
prerequisites: [concept.trajectory-variable, concept.time-discretization]
related_ids: [concept.dynamics-defect, concept.path-terminal-constraints, concept.receding-horizon, direct-collocation]
status: published
last_reviewed: 2026-07-26
---

時間ごとのcontrolを最適化変数にし、初期状態からdynamicsを前進simulationして得たtrajectoryのcostと制約を改善する最適制御法です。

## 30秒でつかむ

この手法では、stateをすべて独立には決めません。
**controlを仮定してsimulationし、trajectoryが目標へ近づくよう調整します。**

- 見ているもの: rollout trajectory、cost、terminal error、constraint violation
- 動かしているもの: control sequenceまたはそのparameter
- 前進の判断: costが下がり、feasibilityが保たれているか
- 別に確認するもの: rolloutの実時間、warm startの効き、deadlineへの余裕
- 恐れていること: 不安定dynamics、長いhorizon、初期control依存、感度の悪条件化

stateはsimulationで決まるため、変数数を減らせます。
一方、長いhorizonでは早い時刻のcontrolが後半stateへ強く影響します。
その結果、optimizationが難しくなります。

## まず確認すること

| 項目 | 確認内容 |
|---|---|
| dynamics | 数値的に安定してsimulationできるか |
| control parameterization | piecewise constantなど妥当な表現か |
| horizon | 長すぎて感度が消失・爆発しないか |
| constraints | path constraintをrolloutだけで評価できるか |
| derivatives | sensitivityや自動微分を利用できるか |
| initialization | reasonableな初期controlを用意できるか |

real-time制御ではsolve time、warm start、fallback controllerをcostやfeasibilityとは別の運用条件として記録します。

## 仕組み

離散dynamicsを例にします。

$$
x_{t+1}=F(x_t,u_t)
$$

最適化変数はcontrol列 $u_0,\ldots,u_{T-1}$です。候補controlで前進simulationし、trajectory costと制約を評価します。勾配を使う場合は、control変更が将来stateへ伝わる感度を計算します。

stateを独立変数にしないため、rollout上のdynamics equalityは自動的に満たされます。
その代わり、costを下げてもpath constraintやterminal conditionを満たすとは限りません。
unstable rolloutや長期感度が、controlの改善を後半のstateへ伝える段階で難しさになります。

上段のcontrol列だけがoptimization variableです。
下段のstate trajectoryは、そのcontrol列を先頭からsimulationした結果です。

![減衰のある1-state dynamicsを20 step前進simulationした固定Direct Shooting実行。optimized controlは前半の約0.51から増える。後半11個は上限1に達する。初期controlのstateは0のままである。optimized controlのstateは0.950まで進む。target 1との差は0.0496残る。](./media/direct-shooting-rollout-execution.svg "control sequenceを変数として更新し、state trajectoryをforward simulationで得る固定Direct Shooting実行")

上段を変えるたびに、下段は初期状態からrolloutし直します。
この教材ではterminal targetをhard constraintにせず、control costと一緒にobjectiveへ入れています。
そのため、最終stateはtargetへ完全一致せず `x20 = 0.950` で止まります。

> 固定dynamics `x[t+1] = 0.92 x[t] + 0.1 u[t]` を80回更新した教材です。
> objectiveは `1.000 → 0.0344`、20個中11個のcontrolが上限へ達します。
> path constraintやunstable dynamicsは含みません。
> model mismatchやDirect Shooting一般の性能も示していません。

## 向く条件・避ける条件

向いている条件:

- horizonが比較的短い
- dynamics simulationが安定・高速
- state constraintが少ない、または扱いやすい
- control dimensionを低くparameterizeできる

## うまくいったサインと切替サイン

次の条件では、変数を減らせる利点よりもrolloutの不安定さが支配的になります。

- 長いhorizonで不安定dynamics
- 多数の厳しいpath constraint
- eventやdiscontinuityを未処理
- model mismatchが大きくsimulationを信用できない

## 診断値

- total costとterminal error
- state / control constraint violation
- rollout stability
- gradient normとstep norm
- horizon別のsensitivity
- wall timeとiteration数
- 初期controlごとの解

costの低下、constraint violationの許容範囲、rolloutの安定性は別々に記録します。
wall timeとiteration数は、解の良さではなくreal-time運用の判定に使います。

## 追加の診断

- rolloutが発散 → parameterization、horizon、stabilizing initial controlを見直す
- 初期時刻の勾配だけ巨大 → scalingやmultiple shootingを検討
- path constraintが満たせない → direct collocationへ
- horizonを延ばすと解が急変 → discretizationとmodelを確認
- real-time deadlineを超える → warm start、receding horizon、専用solverを検討

## Python

```python
HORIZON = 20
DECAY = 0.92
DT = 0.1
TARGET = 1.0
CONTROL_PENALTY = 0.002
LEARNING_RATE = 4.0


def rollout(controls: list[float]) -> list[float]:
    states = [0.0]
    for control in controls:
        states.append(DECAY * states[-1] + DT * control)
    return states


def objective(controls: list[float]) -> tuple[float, list[float]]:
    states = rollout(controls)
    terminal_cost = (states[-1] - TARGET) ** 2
    control_cost = CONTROL_PENALTY * sum(control * control for control in controls)
    return terminal_cost + control_cost, states


controls = [0.0] * HORIZON
terminal_weights = [
    DT * DECAY ** (HORIZON - 1 - index)
    for index in range(HORIZON)
]
history = []
for iteration in range(81):
    cost, states = objective(controls)
    history.append((iteration, cost, states[-1]))
    if iteration == 80:
        break

    terminal_error = states[-1] - TARGET
    gradient = [
        2.0 * terminal_error * weight + 2.0 * CONTROL_PENALTY * control
        for weight, control in zip(terminal_weights, controls, strict=True)
    ]
    controls = [
        max(-1.0, min(1.0, control - LEARNING_RATE * derivative))
        for control, derivative in zip(controls, gradient, strict=True)
    ]

print(history[0], history[-1])
print(sum(control >= 1.0 - 1e-12 for control in controls))
```

出力ではobjectiveが `1.0` から `0.034356...` へ下がり、terminal stateは `0.950387...` になります。
上限へ達するcontrolは11個です。

この例は単純なdynamicsと固定stepのprojected gradientを使います。
実務ではintegration errorとstate constraintsを保存します。
unitsとsolver statusも分けて記録します。

## コラム: Direct Collocationとの違い

Direct Collocationはstateもdecision variableにし、dynamics defectをconstraintとして課します。変数は増えますが、長いhorizonやpath constraintで疎構造を使いやすくなります。

[Direct Collocation](#/learn/direct-collocation)とは、変数数だけで比較しません。
rollout安定性／defect／sparsity／warm startも確認します。

## 次に読む

まず[trajectory variable](#/learn/concept.trajectory-variable)で、control列とrolloutされたstate列を分けて読みます。
次に[時間discretization](#/learn/concept.time-discretization)で、controlの保持方法とstep sizeを確認します。
path制約やterminal conditionが主役なら、[path・terminal制約](#/learn/concept.path-terminal-constraints)へ進みます。
長いhorizonでrollout感度が問題なら、[Direct Multiple Shooting](#/learn/multiple-shooting)へ切り替えます。
観測ごとに先頭のcontrolだけを使う運用は、[receding horizon](#/learn/concept.receding-horizon)で確認します。
