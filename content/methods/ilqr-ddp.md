---
content_id: ilqr-ddp
kind: method
method_id: M_ILQR_DDP
title_ja: iLQR / DDP
title_en: Iterative LQR / Differential Dynamic Programming
summary: 現在の軌道の周りでdynamicsとcostを二次近似し、backward passでRiccati型のfeedback gainを求め、forward passで軌道を更新する反復的な軌道最適化法です。
source_ids: [S042, S043, S050, S076]
prerequisites: []
related_ids: [multiple-shooting, direct-collocation, dynamic-programming, family.optimal-control]
status: published
last_reviewed: 2026-07-18
---

現在の軌道の周りでdynamicsとcostを二次近似し、backward passでRiccati型のfeedback gainを求め、forward passで軌道を更新する反復的な軌道最適化法です。

## 30秒でつかむ

この手法の気持ちは、**いきなり大きな非線形問題を解くのではなく、現在の軌道の近くで小さなLQR問題を解き、そのfeedback則で実際のtrajectoryを更新したい**というものです。

- 見ているもの: rollout trajectory、cost、local quadratic model、feedback gain
- 動かしているもの: control sequenceと局所近似
- 前進の判断: forward pass後のcost改善とrollout安定性
- 別に確認するもの: constraint violation、離散化への依存、backward / forward passの実時間
- 恐れていること: 不良な$Q_{uu}$、初期軌道依存、強い非線形性、一般path constraintの扱いにくさ

costが下がること、制約を満たすこと、real-time deadlineに間に合うことは別の判定です。

## まず確認すること

| 項目 | 確認内容 |
|---|---|
| dynamics | 1次または2次の微分を計算できるか |
| initial trajectory | 現在のstateとcontrolの軌道を用意できるか |
| cost | 局所2次近似で改善を判定できるか |
| constraints | box制約か、一般のpath制約まで必要か |
| regularization | $Q_{uu}$が正定値でない場合の処理があるか |
| real-time | backward / forward passの時間がdeadlineに合うか |

## backward passとforward passで何をしているか

現在の候補軌道 $\bar{x}_k, \bar{u}_k$ の周りで、dynamics

$$
x_{k+1} = f(x_k, u_k)
$$

を1次または2次までTaylor展開し、costも2次近似します。backward passでは、終端から時刻を遡りながら価値関数の局所2次modelを更新し、各時刻でLQR部分問題を解いて、

- feedforward項 $k_k$
- feedback gain $K_k$

を求めます。forward passでは、実際のdynamicsに沿って

$$
u_k = \bar{u}_k + \alpha k_k + K_k(x_k - \bar{x}_k)
$$

でcontrolを計算し、軌道を再simulationします。$\alpha$はline searchのstep lengthで、costが改善しない場合は縮小して再試行します。改善した軌道を次の反復の$\bar{x}_k, \bar{u}_k$として、backward / forward passを繰り返します。

## iLQRとDDPの違い

iLQR（iterative LQR）は、dynamicsのTaylor展開を1次項までとし、2次のdynamics項を無視します。これはGauss-Newton近似に相当し、2階微分（Hessian）の計算を避けられる代わりに、非線形性が強いdynamicsでは価値関数の近似精度が落ちます。

DDP（differential dynamic programming）は、dynamicsの2次項（stateとcontrolに関するHessian-vector積相当の項）まで価値関数の展開に含めます。これにより局所的な近似精度は上がりますが、2階微分の計算とその評価costが必要になります。どちらも共通してbackward / forward passのRiccati再帰という骨格を持ち、iLQRはDDPの1次近似版として位置づけられます。

## direct法（shooting/collocation）との違い

[Direct Shooting](#/learn/direct-shooting)や[Direct Multiple Shooting](#/learn/multiple-shooting)、[Direct Collocation](#/learn/direct-collocation)は、離散化した軌道問題をひとつのNLPとして汎用solver（SQPやinterior-point法）に渡します。これに対しiLQR/DDPは、時間方向の構造を[動的計画法](#/learn/dynamic-programming)と同じ発想で使い、horizon全体のNLPを解く代わりに、時刻ごとの小さなLQR部分問題をbackwardに解いていきます。

この違いから、iLQR/DDPは反復のたびにfeedback gain $K_k$が副産物として得られ、real-time MPCでの再planningに使いやすいという利点があります。一方で、一般のpath制約や不等式制約をRiccati再帰へ組み込むのは、direct法がNLP solverの制約処理をそのまま使えるのに比べて弱点になりがちです。多くの実装は無制約または簡単なbox制約までを標準としており、一般制約を厳密に扱いたい場合はdirect collocationのような定式化を検討します。

## 向いている条件

- dynamicsが滑らかで微分可能（1次または2次の微分が計算できる）
- 高速なlocal trajectory refinementが必要（real-time MPCでの再planningなど）
- 良い初期軌道の推測を用意できる
- feedback則（$K_k$）を制御則としてそのまま使いたい

## 避ける／切り替える条件

- dynamicsが未同定、または強くstochasticでmodel mismatchが大きい
- 不連続なevent（衝突、切り替えなど）をmeshやhybrid構造で明示していない
- 一般のpath制約や不等式制約が本質的で、Riccati再帰では扱いにくい
- real-time deadlineに対してbackward / forward passの計算時間が合わない

## Python

非線形dynamicsを反復的に再linearizeする完全なiLQR/DDP実装は、自動微分、regularization、line searchまで必要です。次はその内部で解く有限horizon LQR部分問題だけを取り出し、backward passでfeedback gainを作ってforward rolloutする最小例です。

```python
import numpy as np

# x[k + 1] = A x[k] + B u[k]
A = np.array([[1.0, 0.1], [0.0, 1.0]])
B = np.array([[0.0], [0.1]])
Q = np.diag([1.0, 0.1])
R = np.array([[0.01]])
terminal_Q = 10.0 * Q
horizon = 40

# backward pass: value Hessian Pからfeedback gain Kを求める
P = terminal_Q.copy()
gains = []
for _ in range(horizon):
    control_hessian = R + B.T @ P @ B
    K = np.linalg.solve(control_hessian, B.T @ P @ A)
    gains.append(K)
    P = Q + A.T @ P @ (A - B @ K)
gains.reverse()

# forward pass: 得られたfeedback則で軌道をrolloutする
x = np.array([2.0, 0.0])
states = [x.copy()]
controls = []
for K in gains:
    u = -K @ x
    x = A @ x + B @ u
    controls.append(float(u.item()))
    states.append(x.copy())

print("terminal state:", states[-1])
print("maximum control:", max(abs(value) for value in controls))
```

この例はlinearな1回のLQR solveであり、iLQR/DDPの非線形反復や一般制約処理は含みません。実際の数値実装は[CasADi](https://web.casadi.org/docs/)や[acados](https://docs.acados.org/)、[Drake MathematicalProgram](https://drake.mit.edu/doxygen_cxx/group__solvers.html)などの公式referenceで、利用versionのAPI、regularization、line-search戦略を確認します。

## 診断値

- costの変化とline searchの採用率
- defect_norm（forward rollout後のdynamics整合性）
- constraint_violation
- KKT residual（制約付き変種を使う場合）
- mesh_error（離散化を変えたときの解の変化）
- rollout_stability
- backward / forward passのwall timeとiteration数

## 失敗・切替の兆候

- forward passのrolloutが発散し、line searchでcostが改善しない
- backward passで$Q_{uu}$が正定値でなくなり、regularizationを強めても解消しない
- 反復を重ねてもdefectやcostの変化が停滞する
- 離散化の時間刻みを変えると解やcostが大きく変わる
- 一般path制約の違反が反復後も残り続ける

segment分割で感度を抑える定式化は[Direct Multiple Shooting](#/learn/multiple-shooting)、path制約を密に扱いたい場合は[Direct Collocation](#/learn/direct-collocation)、時間構造を使う考え方の原型は[動的計画法](#/learn/dynamic-programming)、軌道最適化手法全体の選び分けは[最適制御・軌道最適化の選び分け](#/learn/family.optimal-control)で確認できます。
