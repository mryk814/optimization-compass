---
content_id: family.optimal-control
kind: method
method_id: MF_OPTIMAL_CONTROL
title_ja: 最適制御・軌道最適化の選び分け
title_en: Choosing a Trajectory Optimization Method
summary: 時間発展する動力学の下で軌道と制御入力を選ぶ問題を、変数・離散化・制約・実行頻度から各手法へつなぐ入口です。
source_ids: [S042, S043, S050, S076, S102]
prerequisites: [concept.trajectory-variable, concept.dynamics-defect, concept.path-terminal-constraints, concept.time-discretization]
related_ids: [concept.receding-horizon, direct-shooting, multiple-shooting, direct-collocation, ilqr-ddp]
visualization_ids: [pendulum-collocation-coarse, pendulum-collocation-refined, pendulum-model-rollout-failure]
comparison_ids: [COMPARE_PENDULUM_COLLOCATION_MESH]
status: published
last_reviewed: 2026-07-24
---

時間発展する動力学の下で軌道と制御入力を選ぶ問題を、変数・離散化・制約・実行頻度から各手法へつなぐ入口です。

## 30秒でつかむ

この手法群は、**動力学という時間方向の構造を使います。**
軌道と制御入力を同時に、または段階的に改善します。

- 見ているもの: 動力学モデル、状態・制御入力の軌道、費用、経路・境界制約
- 動かすもの: 制御入力列（と、定式化によっては状態列そのもの）
- 前進の判断: 動力学の整合性残差の縮小、費用の低下、経路制約充足の維持
- 主な弱点: 動力学モデルと離散化の誤差、初期軌道の推測への依存、経路制約の扱いにくさ

これは「どの手法が常に優れているか」という順位ではありません。
変数／制約の置き場所／リアルタイム性の必要度で選びます。

時間格子点上の残差だけで軌道を採用すると、区間内の違反を見落とします。

![同じ振り子の振り上げをN=20、N=40、重力を10%変えた検証用の前進シミュレーションで実行し、時間格子点上と区間再構成または検証用の前進シミュレーション上の経路制約違反を反復ごとに比較した結果。](./media/optimal-control-mesh-execution.svg "時間格子の細分化とモデルの不一致で、時間格子点上の収束と前進シミュレーション上の違反がどう分かれるかを示す固定教材です。手法間の一般性能順位付けではありません。")

N=40では区間再構成の違反がN=20より小さくなります。
しかし、重力を変えた検証用の前進シミュレーションでは、時間格子点上の値が小さくても違反が残ります。

## まず読む: 5つの概念

手法名だけでは、状態を変数にするか、動力学をどこで確認するかが見えません。
MPCとして解き直すかも、別の判断です。
次の順で読むと、同じ軌道に対する定式化の違いを追えます。

1. [軌道の変数](#/learn/concept.trajectory-variable) — 状態列と制御入力列のどちらを動かすか
2. [動力学の整合性残差](#/learn/concept.dynamics-defect) — 隣り合う状態がモデルと整合するか
3. [経路・終端制約](#/learn/concept.path-terminal-constraints) — 途中と終端のどこで可行性を判定するか
4. [時間離散化](#/learn/concept.time-discretization) — 予測時間を格子へ写すと何が変わるか
5. [観測ごとに解き直す運用](#/learn/concept.receding-horizon) — 計画を一度解くのか、観測ごとに解き直すのか

## ロボティクスでの読み替え

ロボティクスでは、状態 $x_k$ を位置・速度・姿勢などとして読み替えます。
制御入力 $u_k$ は、力・トルク・操舵などです。
初期条件・終端条件は開始姿勢と目標姿勢に対応します。
経路制約には、関節・入力の上下限や障害物回避があります。

この対応は読み進めるための地図であり、特定のロボットの安全性や実機性能を保証しません。
格子上の制約を満たした後も、区間内を高精度シミュレーションや実機側の監視で確認します。

## まず確認すること

| 確認項目 | 選択への影響 |
|---|---|
| 動力学の滑らかさ・微分可能性 | 線形化やTaylor展開に基づく手法（選点法、iLQR/DDP）を使えるか |
| 予測時間の長さ | 長いほど単一シューティング法の感度が爆発しやすく、区間分割や選点法が有利になりやすい |
| 経路制約の量 | 密ならNLPとして明示的に扱う直接法、少なければRiccati再帰系も候補になる |
| リアルタイム性（MPC用途か設計時最適化か） | MPCではウォームスタートやフィードバック係数が実用上重要になる |
| 初期軌道の推測が用意できるか | 推測が悪いと、どの手法でもソルバーが可行点や良い局所解に届きにくい |

これらの確認だけで、モデルの品質が保証されるわけではありません。動力学モデルの妥当性と離散化の粗さは、個別に検証します。

## 条件付きの選び分け

| 役割 | 手法 | 優先しやすい条件 | 切り替えを考える条件 |
|---|---|---|---|
| 変数が少ないシンプルな出発点 | [Direct Shooting](#/learn/direct-shooting) | 予測時間が短く動力学が安定、変数数を減らしたい | 前進シミュレーションの感度が大きく、勾配が極端になる |
| 感度爆発を抑える区間分割 | [Direct Multiple Shooting](#/learn/multiple-shooting) | 予測時間が中〜長、不安定・非線形動力学、積分を並列化できる | 連続性制約の整合性残差が停滞、格子依存が大きい |
| 経路制約が密な同時最適化 | [Direct Collocation](#/learn/direct-collocation) | 経路・境界制約が多い、疎な構造をソルバーに使わせたい | 時間格子の細分化で解が大きく変わる、格子が粗い |
| 高速な局所的な改良とフィードバック則 | [iLQR / DDP](#/learn/ilqr-ddp) | 動力学が滑らか、リアルタイム MPCでフィードバック係数が欲しい | 一般経路制約が本質、後退計算の正則化で解消しない不安定さ |

これは一般性能順位付けではありません。
同じ動力学モデル／予測時間／初期軌道／離散化の粗さ／停止条件をそろえて比較します。

## うまくいったサインと切替サイン

うまく進んでいるときは、離散化上の指標だけでなく、実際のシミュレーションも改善します。

- defect_norm（動力学整合性の残差）が反復とともに縮小する
- 経路・境界制約のconstraint_violationが停止許容値内に収まる
- 区間分割や格子を変えても解や費用が大きく変わらない
- 前進シミュレーションが安定し、発散しない

切替サイン:

- 整合性残差が反復を重ねても縮小しない → 初期軌道、線形化、正則化を見直す
- 前進シミュレーションが発散する → 単一シューティング法から多重シューティング法や別の離散化へ
- 格子 / 区間分割を変えると解が大きく変化する → 細分化やより疎な定式化を検討する
- 一般経路制約の違反が残り続ける → Riccati再帰系から直接選点法のようなNLP定式化へ

## 小さな比較の型

比較では予測時間や初期軌道を揃えず、離散化の粗さだけを変えるといった曖昧な条件にしません。少なくとも次を固定して記録します。

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

各手法が実際に扱うのは、動力学を離散化した近似問題です。
ソルバーの「成功」は、離散化したNLPやLQR部分問題の収束を示します。
元の連続時間動力学を厳密に満たす保証ではありません。

得られた制御入力は高精度なシミュレーションへ通し、軌道を再確認します。
離散化を細かくしたときに、解や費用が安定するかも確認します。
格子依存や歩幅依存が大きい解は、離散化による見かけの結果を含む可能性があります。

## ロボティクスと制御への導線

[振り子の振り上げの事例](#/gallery/EC029)では、動力学と初期・終端・経路制約を固定します。予算と許容誤差も揃え、N=20とN=40の格子を比較できます。主な可視化画面は時間格子点上の整合性残差と区間再構成の制約違反を分けます。失敗可視化画面では重力を変えた検証用の前進シミュレーションでモデルの不一致を確認します。

事前に計算した軌道を観測ごとに更新する場合は、[観測ごとに解き直す運用](#/learn/concept.receding-horizon)を先に読みます。その後に[100Hz MPCの事例](#/gallery/EC025)へ進みます。

接触や動作モードの切替を含む問題では、[入れ子・均衡・相補性・ハイブリッド構造](#/learn/concept.nested-equilibrium-complementarity-hybrid)を参照します。既知の接触予定と動作モードの発見は別の問題として扱います。

安全制約をQPで補正する安全フィルターは、[制約付き最適化](#/learn/family.constrained-nlp)と[LP・QP・錐最適化](#/learn/lp-qp-conic)へ接続します。状態・制御入力の上下限を満たすことと、不変集合や安全性の保証を同一視しません。

## 次に読む

5つの概念を読んだら、[Direct Shooting](#/learn/direct-shooting)と[Direct Multiple Shooting](#/learn/multiple-shooting)の状態の扱いを比べます。経路制約を置く[Direct Collocation](#/learn/direct-collocation)と、フィードバック則を含む[iLQR / DDP](#/learn/ilqr-ddp)も選び分けます。具体的な診断は[振り子の振り上げの事例](#/gallery/EC029)と[時間格子の感度比較](#/compare/COMPARE_PENDULUM_COLLOCATION_MESH)で確認できます。
