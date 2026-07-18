---
content_id: concept.time-discretization
kind: concept
canonical_entity_type: feature
canonical_entity_id: F_STRUCTURE_TRAJECTORY
title_ja: 時間discretization
title_en: Time Discretization
summary: 時間discretizationは連続時間のdynamicsと制約を有限個の時刻点へ写す設計で、meshの粗さは計算量だけでなく解の意味を変えます。
source_ids: [S042, S043, S050, S076]
related_ids: [family.optimal-control, direct-collocation, multiple-shooting, direct-shooting, ilqr-ddp]
status: published
last_reviewed: 2026-07-18
---

時間discretizationは連続時間のdynamicsと制約を有限個の時刻点へ写す設計で、meshの粗さは計算量だけでなく解の意味を変えます。

## horizonを格子に切る

連続時間の系を

$$
\dot{x}(t)=f(x(t),u(t)),\qquad t\in[0,T]
$$

とすると、時間discretizationは$T$を$N$区間へ分け、$\Delta t=T/N$ごとにstateやcontrolを表す操作です。最適化が解くのは、元の微分方程式そのものではなく、選んだintegrator・補間・meshにより作られた有限次元問題です。

粗いmeshは変数と計算を減らしますが、速い変化、制約境界、短い接触を見落としやすくなります。細かいmeshは表現力を増やす一方で、変数・制約・条件数を増やし、初期軌道への依存を強めることがあります。

## step sizeはsolver設定ではなく定式化の一部

| 設計項目 | 粗すぎるとき | 細かすぎるとき | 記録する値 |
| --- | --- | --- | --- |
| $\Delta t$ | dynamicsと制約の変化を取り逃す | NLPが大きくなり収束が遅い | horizon、区間数、step size |
| control parameterization | 入力の切替を表せない | 不自然な高周波controlを許す | zero-order holdかpiecewise linearか |
| integrator / collocation scheme | rollout誤差が解へ混ざる | 計算費用が支配する | 方式、order、tolerance |
| mesh distribution | 重要なイベントに点がない | 不要な領域まで過剰に細かい | 等間隔か局所refinementか |

同じmethod名でも、この表の選択が違えば別の問題を解いているに近いことがあります。比較や再現では、method名とobjectiveだけでなくdiscretizationを固定条件として書きます。

## refinementは「解が安定するか」を見る実験

もっとも小さな検証は、同じhorizon・初期軌道・modelでmeshを細かくして、判断が変わるかを見ることです。たとえば次を追います。

- objectiveとterminal errorが大きく変わらないか
- [dynamics defect](#/learn/concept.dynamics-defect)とpath制約違反が許容範囲に収まるか
- controlの形やactive constraintの時刻が大きく動かないか
- 高精度simulationに通した結果が離散化解と整合するか

解が大きく変わるなら、粗いmeshの結果を「最適な連続時間軌道」と呼びません。どこを細かくすべきか、initial guessが変わっただけではないか、integratorの誤差かを切り分けます。

## 先に決めるべき3つ

1. controlを各区間で一定にするか、線形・高次に補間するか
2. stateをrolloutで作るか、mesh上の変数として明示するか
3. path制約をどの時刻点で評価し、最終的にどのsimulationで再確認するか

この3つは[Direct Shooting](#/learn/direct-shooting)、[Direct Multiple Shooting](#/learn/multiple-shooting)、[Direct Collocation](#/learn/direct-collocation)の比較条件でもあります。

::: warning
離散化を細かくして結果が安定したことは、modelが正しいことの証明ではありません。model mismatch、測定誤差、実機の遅れは別の検証対象です。
:::

## 次に読む

mesh上のstateとcontrolを同時に扱う設計は[Direct Collocation](#/learn/direct-collocation)、segmentを積分して結ぶ設計は[Direct Multiple Shooting](#/learn/multiple-shooting)で具体化します。途中の可行性の読み方は[path・terminal制約](#/learn/concept.path-terminal-constraints)を参照してください。
