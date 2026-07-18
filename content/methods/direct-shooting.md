---
content_id: direct-shooting
kind: method
method_id: M_DIRECT_SHOOTING
title_ja: Direct Shooting
title_en: Direct Shooting
summary: 時間ごとのcontrolを最適化変数にし、初期状態からdynamicsを前進simulationして得たtrajectoryのcostと制約を改善する最適制御法です。
source_ids: [S042, S043, S050, S076]
related_ids: [direct-collocation]
status: published
last_reviewed: 2026-07-18
---

時間ごとのcontrolを最適化変数にし、初期状態からdynamicsを前進simulationして得たtrajectoryのcostと制約を改善する最適制御法です。

## 30秒でつかむ

この手法の気持ちは、**stateを全部独立に決めるのではなく、controlだけを仮定してsimulationを走らせ、その結果のtrajectoryが目標へ近づくようcontrolを調整したい**というものです。

- 見ているもの: rollout trajectory、cost、terminal error、constraint violation
- 動かしているもの: control sequenceまたはそのparameter
- 前進の判断: costが下がり、feasibilityが保たれているか
- 別に確認するもの: rolloutの実時間、warm startの効き、deadlineへの余裕
- 恐れていること: 不安定dynamics、長いhorizon、初期control依存、感度の悪条件化

stateはsimulationで決まるため変数数を減らせますが、長いhorizonでは早い時刻のcontrolが後半stateへ強く影響し、optimizationが難しくなります。

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

## 向いている条件

向いている条件:

- horizonが比較的短い
- dynamics simulationが安定・高速
- state constraintが少ない、または扱いやすい
- control dimensionを低くparameterizeできる

## 避ける／切り替える条件

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

## 失敗・切替の兆候

- rolloutが発散 → parameterization、horizon、stabilizing initial controlを見直す
- 初期時刻の勾配だけ巨大 → scalingやmultiple shootingを検討
- path constraintが満たせない → direct collocationへ
- horizonを延ばすと解が急変 → discretizationとmodelを確認
- real-time deadlineを超える → warm start、receding horizon、専用solverを検討

## Python

```python
import numpy as np
from scipy.optimize import minimize

DT = 0.1
HORIZON = 20


def rollout(controls: np.ndarray) -> np.ndarray:
    states = np.zeros(HORIZON + 1)
    for index, control in enumerate(controls):
        states[index + 1] = states[index] + DT * control
    return states


def objective(controls: np.ndarray) -> float:
    states = rollout(controls)
    terminal_cost = (states[-1] - 1.0) ** 2
    control_cost = 0.01 * float(controls @ controls)
    return float(terminal_cost + control_cost)


result = minimize(objective, x0=np.zeros(HORIZON), method="L-BFGS-B", bounds=[(-1.0, 1.0)] * HORIZON)
print(result.success, rollout(result.x)[-1], result.fun)
```

この例は単純なdynamicsです。実務ではintegration error、state constraints、units、solver statusを保存します。

## コラム: Direct Collocationとの違い

Direct Collocationはstateもdecision variableにし、dynamics defectをconstraintとして課します。変数は増えますが、長いhorizonやpath constraintで疎構造を使いやすくなります。

[Direct Collocation](#/learn/direct-collocation)と、変数数だけでなくrollout安定性、defect、sparsity、warm startで比較してください。
