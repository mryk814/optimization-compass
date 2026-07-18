---
content_id: family.optimal-control
kind: method
method_id: MF_OPTIMAL_CONTROL
title_ja: 最適制御・軌道最適化の選び分け
title_en: Choosing a Trajectory Optimization Method
summary: 時間発展するdynamicsの下でtrajectoryとcontrolを選ぶ問題群を、direct shooting、direct multiple shooting、direct collocation、iLQR/DDPなどの離散化・解法へつなぐ入口です。
source_ids: [S042, S043, S050, S076]
prerequisites: [concept.trajectory-variable, concept.dynamics-defect, concept.path-terminal-constraints, concept.time-discretization]
related_ids: [concept.receding-horizon, direct-shooting, multiple-shooting, direct-collocation, ilqr-ddp]
status: published
last_reviewed: 2026-07-18
---

時間発展するdynamicsの下でtrajectoryとcontrolを選ぶ問題群を、direct shooting、direct multiple shooting、direct collocation、iLQR/DDPなどの離散化・解法へつなぐ入口です。

## まず読む: 5つの概念

手法名から入ると、stateを変数にするか、dynamicsをどこで確認するか、MPCとして繰り返すかが混ざりやすくなります。次の順で読むと、同じ軌道を見ながら定式化の違いを追えます。

1. [trajectory variable](#/learn/concept.trajectory-variable) — state列とcontrol列のどちらを動かすか
2. [dynamics defect](#/learn/concept.dynamics-defect) — 隣り合うstateがモデルと整合するか
3. [path・terminal制約](#/learn/concept.path-terminal-constraints) — 途中と終端のどこで可行性を判定するか
4. [時間discretization](#/learn/concept.time-discretization) — horizonをmeshへ写すと何が変わるか
5. [receding horizon](#/learn/concept.receding-horizon) — 計画を一度解くのか、観測ごとに解き直すのか

## Roboticsでの読み替え

ロボティクスでは、state $x_k$ を位置・速度・姿勢など、control $u_k$ を力・トルク・操舵などとして読み替えます。initial / terminal conditionは開始姿勢と目標姿勢、path constraintは関節・入力の上下限や障害物回避として現れます。

この対応は読み進めるための地図であり、特定のロボットの安全性や実機性能を保証するものではありません。mesh上の制約を満たした後も、区間内の挙動を高精度simulationや実機側の監視で確認します。

## 30秒でつかむ

このfamilyでは、**dynamicsという時間方向の構造を使い、trajectoryとcontrolを同時に、または段階的に改善します**。

- 見ているもの: dynamics model、state / controlのtrajectory、cost、path / boundary制約
- 動かすもの: control列（と、定式化によってはstate列そのもの）
- 前進の判断: dynamics defectの縮小、costの低下、path制約充足の維持
- 主な弱点: dynamics modelとdiscretizationの誤差、初期軌道の推測への依存、path制約の扱いにくさ

「どの手法が常に優れているか」という順位ではありません。変数として何を持つか、制約をどこで扱うか、real-time性をどこまで必要とするかの違いで選びます。

## まず確認すること

| 確認項目 | 選択への影響 |
|---|---|
| dynamicsの滑らかさ・微分可能性 | 線形化やTaylor展開に基づく手法（collocation、iLQR/DDP）を使えるか |
| horizonの長さ | 長いほどsingle shootingの感度が爆発しやすく、segment分割やcollocationが有利になりやすい |
| path制約の量 | 密ならNLPとして明示的に扱うdirect法、少なければRiccati再帰系も候補になる |
| リアルタイム性（MPC用途か設計時最適化か） | MPCではwarm startやfeedback gainが実用上重要になる |
| 初期軌道の推測が用意できるか | 推測が悪いと、どの手法でもsolverが可行点や良い局所解に届きにくい |

これらの確認だけで、モデルの品質が保証されるわけではありません。dynamics modelの妥当性と離散化の粗さは、個別に検証します。

## 条件付きの選び分け

| 役割 | 手法 | 優先しやすい条件 | 切り替えを考える条件 |
|---|---|---|---|
| 変数が少ないシンプルな出発点 | [Direct Shooting](#/learn/direct-shooting) | horizonが短くdynamicsが安定、変数数を減らしたい | rolloutの感度が大きく、gradientが極端になる |
| 感度爆発を抑えるsegment分割 | [Direct Multiple Shooting](#/learn/multiple-shooting) | horizonが中〜長、不安定・非線形dynamics、積分を並列化できる | continuity制約のdefectが停滞、mesh依存が大きい |
| path制約が密な同時最適化 | [Direct Collocation](#/learn/direct-collocation) | path / boundary制約が多い、疎な構造をsolverに使わせたい | mesh refinementで解が大きく変わる、meshが粗い |
| 高速なlocal refinementとfeedback則 | [iLQR / DDP](#/learn/ilqr-ddp) | dynamicsが滑らか、real-time MPCでfeedback gainが欲しい | 一般path制約が本質、backward passのregularizationで解消しない不安定さ |

これは一般性能rankingではありません。同じdynamics model、horizon、初期軌道、離散化の粗さ、停止条件をそろえて比較します。

## うまくいったサインと切替サイン

うまく進んでいるときは、離散化上の指標だけでなく、実際のsimulationも改善します。

- defect_norm（dynamics整合性の残差）が反復とともに縮小する
- path / boundary制約のconstraint_violationが停止許容値内に収まる
- segment分割やmeshを変えても解やcostが大きく変わらない
- forward rolloutが安定し、発散しない

切替サイン:

- defectが反復を重ねても縮小しない → 初期軌道、線形化、regularizationを見直す
- rolloutが発散する → single shootingからmultiple shootingや別の離散化へ
- mesh / segment分割を変えると解が大きく変化する → refinementやより疎な定式化を検討する
- 一般path制約の違反が残り続ける → Riccati再帰系からdirect collocationのようなNLP定式化へ

## 小さな比較の型

比較ではhorizonや初期軌道を揃えず、離散化の粗さだけを変えるといった曖昧な条件にしません。少なくとも次を固定して記録します。

```python
experiment = {
    "dynamics_model": "same-continuous-time-system",
    "horizon_length": 2.0,
    "initial_trajectory_guess": "same-warm-start",
    "discretization_step": 0.05,
    "path_constraint_tolerance": 1e-6,
    "methods": ["direct-shooting", "multiple-shooting", "direct-collocation", "ilqr-ddp"],
}

assert experiment["discretization_step"] > 0
```

## コラム: 離散化が解けたことは連続時間の保証ではない

direct shooting、multiple shooting、direct collocation、iLQR/DDPのいずれも、実際に扱っているのはdynamicsを離散化した近似問題です。solverが「成功」を報告しても、それは離散化されたNLPやLQR部分問題が収束したことを意味するにとどまり、元の連続時間dynamicsを厳密に満たす保証ではありません。

離散化解を連続時間の解として無条件に扱わないために、得られたcontrolを高精度なsimulationへ通して軌道を再確認し、離散化を細かくしたときに解やcostが安定するかを確認します。mesh依存やstep size依存が大きい場合、その解は離散化のartifactを含んでいる可能性があります。

## 次に読む

5つの概念を読んだら、短いhorizonで仕組みを確認する[Direct Shooting](#/learn/direct-shooting)、感度爆発をsegmentへ分ける[Direct Multiple Shooting](#/learn/multiple-shooting)、path制約を軌道全体へ置く[Direct Collocation](#/learn/direct-collocation)、feedback則を含むlocal refinementを見る[iLQR / DDP](#/learn/ilqr-ddp)へ進みます。ロボットの障害物・関節・入力制約を本格的に扱うCaseとTheaterは、この共通語彙の次の拡張です。
