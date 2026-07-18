---
content_id: concept.trajectory-variable
kind: concept
canonical_entity_type: feature
canonical_entity_id: F_VARIABLE_TRAJECTORY
title_ja: trajectory variable
title_en: Trajectory Variables
summary: trajectory variableは、時刻ごとのstateやcontrolをまとめて最適化変数として扱う見方で、軌道最適化で「何を動かしているか」を明確にします。
source_ids: [S042, S043, S050, S076]
related_ids: [family.optimal-control, direct-shooting, multiple-shooting, direct-collocation, ilqr-ddp]
status: published
last_reviewed: 2026-07-18
---

trajectory variableは、時刻ごとのstateやcontrolをまとめて最適化変数として扱う見方で、軌道最適化で「何を動かしているか」を明確にします。

## 1個の点ではなく、時間に並んだ決定

通常の最適化では、変数は$x\in\mathbb{R}^n$のような1本のベクトルです。軌道最適化では、状態$x_k$とcontrol $u_k$を時刻$k=0,\ldots,N$に並べ、次のような**列**として扱います。

$$
X=(x_0,x_1,\ldots,x_N),\qquad U=(u_0,u_1,\ldots,u_{N-1}).
$$

この列がtrajectory variableです。ロボットなら$x_k$は位置・速度・姿勢など、$u_k$は力・トルク・操舵などを表します。最適化は「次の入力を1個選ぶ」だけでなく、futureの状態と入力が矛盾しない並びを選びます。

## state列とcontrol列を混同しない

stateは系が実際にたどる量、controlは系へ与える量です。両方を変数に置くか、controlだけを置いてstateをsimulationで作るかが、定式化の大きな違いになります。

| 定式化 | 主な最適化変数 | stateの作り方 | 最初に疑う点 |
| --- | --- | --- | --- |
| Direct Shooting | control列 | 初期stateからforward rollout | 長いhorizonで感度が悪化していないか |
| Direct Multiple Shooting | control列とsegment境界state | segmentごとにrolloutし連続性を制約化 | 境界でstateがつながっているか |
| Direct Collocation | mesh上のstate列とcontrol列 | dynamics defectを制約化 | meshが粗すぎないか |
| iLQR / DDP | nominal trajectoryの周りのupdate | rolloutとlocal modelを往復 | local近似の外へ出ていないか |

変数数だけを見て「少ないほうが良い」とは決められません。stateを明示的に持つと変数は増えますが、path制約や途中の状態を直接見られる利点があります。controlだけにすると形は小さくなりますが、rolloutの感度がすべてcontrol列へ集まります。

## まず描くべき4本の線

実装や結果を読む前に、少なくとも次を別々に描きます。

- state trajectory: 位置、速度、温度などがどう変わるか
- control trajectory: 入力が飽和・振動していないか
- reference: 追従したい目標軌道や終端目標
- constraint boundary: 許容範囲、障害物、入力上限

objectiveが下がっていても、controlが細かく振動する、stateが制約境界をかすめる、終端だけを合わせて途中が不自然になる、といった違和感はこの4本を分けると見つけやすくなります。

## 変数の意味はdynamicsで閉じる

stateとcontrolを自由に並べただけではtrajectoryになりません。離散化したdynamics

$$
x_{k+1}=f_d(x_k,u_k)
$$

またはそれに対応する残差が、隣り合う時刻を結びます。この結び目をどのように扱うかが、[Direct Shooting](#/learn/direct-shooting)、[Direct Multiple Shooting](#/learn/multiple-shooting)、[Direct Collocation](#/learn/direct-collocation)の差になります。

::: warning
trajectory variableは離散時刻上の表現です。solverがこの列に対して成功したことだけから、連続時間の実機・高精度simulationでも同じ軌道になるとは結論付けません。controlを再simulationし、時刻刻みを変えても重要な判断が変わらないかを確認します。
:::

## 次に読む

trajectoryの隣り合う点がdynamicsと整合しているかは[dynamics defect](#/learn/concept.dynamics-defect)、制約をどの時刻で確認するかは[path・terminal制約](#/learn/concept.path-terminal-constraints)へ進みます。変数をどう置くかの比較は[最適制御・軌道最適化の選び分け](#/learn/family.optimal-control)が入口です。
