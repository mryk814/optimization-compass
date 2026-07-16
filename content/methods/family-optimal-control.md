---
content_id: family.optimal-control
kind: method
method_id: MF_OPTIMAL_CONTROL
title_ja: 最適制御・軌道最適化の選び分け
title_en: Choosing a Trajectory Optimization Method
summary: 時間発展するdynamicsの下でtrajectoryとcontrolを選ぶ問題群を、direct shooting、direct multiple shooting、direct collocation、iLQR/DDPなどの離散化・解法へつなぐ入口です。
source_ids: [S042, S043, S050, S076]
related_ids: [direct-shooting, multiple-shooting, direct-collocation, ilqr-ddp]
status: published
last_reviewed: 2026-07-16
---

時間発展するdynamicsの下でtrajectoryとcontrolを選ぶ問題群を、direct shooting、direct multiple shooting、direct collocation、iLQR/DDPなどの離散化・解法へつなぐ入口です。

## 30秒でつかむ

このfamilyの気持ちは、**dynamicsという時間方向の構造を明示的に使い、trajectoryとcontrolを一度に、または段階的に改善すること**です。

- 見ているもの: dynamics model、state / controlのtrajectory、cost、path / boundary制約
- 動かすもの: control列（と、定式化によってはstate列そのもの）
- 前進の判断: dynamics defectの縮小、costの低下、path制約充足の維持
- 主な弱点: dynamics modelとdiscretizationの誤差、初期軌道の推測への依存、path制約の扱いにくさ

「どの手法が常に優れているか」という順位ではありません。変数として何を持つか、制約をどこで扱うか、real-time性をどこまで必要とするかを交換しています。

## まず確認すること

| 確認項目 | 選択への影響 |
|---|---|
| dynamicsの滑らかさ・微分可能性 | 線形化やTaylor展開に基づく手法（collocation、iLQR/DDP）を使えるか |
| horizonの長さ | 長いほどsingle shootingの感度が爆発しやすく、segment分割やcollocationが有利になりやすい |
| path制約の量 | 密ならNLPとして明示的に扱うdirect法、少なければRiccati再帰系も候補になる |
| リアルタイム性（MPC用途か設計時最適化か） | MPCではwarm startやfeedback gainが実用上重要になる |
| 初期軌道の推測が用意できるか | 推測が悪いと、どの手法でもsolverが可行点や良い局所解に届きにくい |

これらの確認は、モデルの品質そのものを保証しません。dynamics modelの妥当性と離散化の粗さは、常に個別に検証が必要です。

## 条件付きの選び分け

| 役割 | 手法 | 優先しやすい条件 | 切り替えを考える条件 |
|---|---|---|---|
| 変数が少ないシンプルな出発点 | [Direct Shooting](#/learn/direct-shooting) | horizonが短くdynamicsが安定、変数数を減らしたい | rolloutの感度が大きく、gradientが極端になる |
| 感度爆発を抑えるsegment分割 | [Direct Multiple Shooting](#/learn/multiple-shooting) | horizonが中〜長、不安定・非線形dynamics、積分を並列化できる | continuity制約のdefectが停滞、mesh依存が大きい |
| path制約が密な同時最適化 | [Direct Collocation](#/learn/direct-collocation) | path / boundary制約が多い、疎な構造をsolverに使わせたい | mesh refinementで解が大きく変わる、meshが粗い |
| 高速なlocal refinementとfeedback則 | [iLQR / DDP](#/learn/ilqr-ddp) | dynamicsが滑らか、real-time MPCでfeedback gainが欲しい | 一般path制約が本質、backward passのregularizationで解消しない不安定さ |

これは一般性能rankingではありません。同じdynamics model、horizon、初期軌道、離散化の粗さ、停止条件で比較します。

## うまくいったサインと切替サイン

うまく進んでいるときは、離散化上の指標と実際のsimulationの両方が改善します。

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

変数を減らして単純に始めたい場合は[Direct Shooting](#/learn/direct-shooting)、感度爆発を抑えたい場合は[Direct Multiple Shooting](#/learn/multiple-shooting)、path制約を密に扱いたい場合は[Direct Collocation](#/learn/direct-collocation)、real-time MPCでfeedback則が欲しい場合は[iLQR / DDP](#/learn/ilqr-ddp)へ進みます。
