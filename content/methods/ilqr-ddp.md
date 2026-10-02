---
content_id: ilqr-ddp
kind: method
method_id: M_ILQR_DDP
title_ja: iLQR / DDP
title_en: Iterative LQR / Differential Dynamic Programming
summary: 現在の軌道の周りで動力学を局所展開し、費用を二次近似する軌道最適化法です。後退計算でRiccati型のフィードバック係数を求め、前進計算で軌道を更新します。
source_ids: [S042, S043, S050, S076]
prerequisites: [concept.trajectory-variable, concept.time-discretization, concept.receding-horizon]
related_ids: [concept.dynamics-defect, concept.path-terminal-constraints, multiple-shooting, direct-collocation, dynamic-programming, family.optimal-control]
status: published
last_reviewed: 2026-09-30
---

現在の軌道の周りで動力学を局所展開し、費用を二次近似する軌道最適化法です。後退計算でRiccati型のフィードバック係数を求め、前進計算で軌道を更新します。

## 30秒でつかむ

この手法は、**大きな非線形問題をいきなり解かず、現在の軌道の近くで小さなLQR問題を解きます**。得られたフィードバック則で実際の軌道を更新します。

- 見るもの: 前進シミュレーション軌道、費用、局所二次モデル、フィードバック係数
- 動かすもの: 制御入力の列と局所近似
- 前進の判断: 前進計算後の費用改善と前進シミュレーション安定性
- 別に確認するもの: 制約違反、離散化への依存、逆向き / 前進計算の実時間
- 恐れていること: 不良な$Q_{uu}$、初期軌道依存、強い非線形性、一般経路制約の扱いにくさ

費用が下がること、制約を満たすこと、実時間の締切に間に合うことは別の判定です。

後退計算でフィードバック係数が得られても、前進シミュレーションがどう変わるかはまだ分かりません。
記事後半の線形 LQR部分問題を実行します。
時刻別係数が初期状態 $[2, 0]$を目標 $[0, 0]$へ戻す過程を、状態と制御入力の履歴で確認できます。

![2状態、1制御入力、40ステップの有限予測時間 LQR部分問題をPythonだけで実行した結果。後退計算で終端側から時刻別係数を作り、前進シミュレーションで位置、速度、制御入力を追う。制御入力なしの位置は2に留まり、フィードバックありでは終端状態が0へ近づく。](./media/lqr-backward-forward-execution.svg "記事のPython例と同じ線形 LQR部分問題の実行結果です。非線形iLQR/DDP反復、正則化、直線探索、一般制約、リアルタイム性能は含みません。")

上段の係数は終端費用から逆向きに作られ、状態と制御入力は初期状態から順向きに進みます。
二つの向きを混同しないことが、後退計算と前進計算を読む最初の足場です。

## 一手の意味

### 後退計算と前進計算で何をしているか

現在の候補軌道 $\bar{x}_k, \bar{u}_k$ の周りで、動力学

$$
x_{k+1} = f(x_k, u_k)
$$

を1次または2次までTaylor展開し、費用も2次近似します。後退計算では、終端から時刻を遡りながら価値関数の局所2次モデルを更新し、各時刻でLQR部分問題を解いて、

- フィードフォワード項 $k_k$
- フィードバック係数 $K_k$

を求めます。前進計算では、実際の動力学に沿って

$$
u_k = \bar{u}_k + \alpha k_k + K_k(x_k - \bar{x}_k)
$$

で制御入力を計算し、軌道を再シミュレーションします。$\alpha$は直線探索の一歩の長さで、費用が改善しない場合は縮小して再試行します。改善した軌道を次の反復の$\bar{x}_k, \bar{u}_k$として、逆向き / 前進計算を繰り返します。

### iLQRとDDPの違い

iLQR（iterative LQR）は、動力学のTaylor展開を1次項までとし、2次の動力学項を無視します。これはGauss-Newton近似に相当し、2階微分（ヘッセ行列）の計算を避けられる代わりに、非線形性が強い動力学では価値関数の近似精度が落ちます。

DDP（differential dynamic programming）は、動力学の2次項まで価値関数の展開に含めます。この2次項は、状態と制御入力に関するヘッセ行列とベクトルの積相当の項です。局所的な近似精度は上がりますが、2階微分の計算とその評価費用が必要になります。どちらも逆向き / 前進計算のRiccati再帰という骨格は共通です。iLQRはDDPの1次近似版として位置づけられます。

### 直接法（シューティング法・選点法）との違い

[Direct Shooting](#/learn/direct-shooting)／[Direct Multiple Shooting](#/learn/multiple-shooting)／[Direct Collocation](#/learn/direct-collocation)は直接法です。離散化した軌道問題をひとつのNLPとして、SQPや内点法などの汎用ソルバーに渡します。

これに対しiLQR/DDPは、時間方向の構造を[動的計画法](#/learn/dynamic-programming)と同じ発想で使います。計画期間全体のNLPを解く代わりに、時刻ごとの小さなLQR部分問題を逆向きに解きます。

この違いから、iLQR/DDPでは反復のたびにフィードバック係数 $K_k$が副産物として得られます。そのため、実時間 MPCでの再計画に使いやすいという利点があります。

一方、一般の経路制約や不等式制約をRiccati再帰へ組み込むことは弱点になりがちです。直接法なら、NLP ソルバーの制約処理をそのまま使えます。多くの実装は、無制約または簡単な矩形の領域制約までを標準としています。一般制約を厳密に扱いたい場合は、直接選点法のような定式化を検討します。

## 小さな例

Python例の線形LQR部分問題を使います。
状態は位置と速度、初期状態は $(2,0)$ です。
後退計算で40時刻分の係数を作り、前進計算の最初の3時刻を記録しました。

| 時刻 | 位置 | 速度 | 制御入力 |
|---|---:|---:|---:|
| 0 | 2.0000 | 0.0000 | -15.2089 |
| 1 | 2.0000 | -1.5209 | -7.6385 |
| 2 | 1.8479 | -2.2847 | -2.6797 |

最初の制御入力で速度が変わり、次の時刻から位置が目標0へ動きます。
終端の状態は約 $(0.000028,0.000030)$ でした。
これは一度の線形LQR求解と、その前進計算の時刻列です。
非線形iLQR/DDPの3反復ではありません。
制御入力の上下限も含まないため、大きな初期制御をそのまま実機へ適用しません。

## 向く条件・避ける条件

### まず確認すること

| 項目 | 確認内容 |
|---|---|
| 動力学 | 1次または2次の微分を計算できるか |
| 初期軌道 | 現在の状態と制御入力の軌道を用意できるか |
| 費用 | 局所2次近似で改善を判定できるか |
| 制約 | 矩形の領域制約か、一般の経路制約まで必要か |
| 正則化 | $Q_{uu}$が正定値でない場合の処理があるか |
| 実時間 | 逆向き / 前進計算の時間が締切に合うか |

### 向いている条件

- 動力学が滑らかで微分可能（1次または2次の微分が計算できる）
- 高速な局所軌道の改良が必要（実時間 MPCでの再計画など）
- 良い初期軌道の推測を用意できる
- フィードバック則（$K_k$）を制御則としてそのまま使いたい

### 避ける／切り替える条件

- 動力学が未同定、または強く確率的でモデルと実際のずれが大きい
- 不連続な事象（衝突、切り替えなど）を時間格子や混成構造で明示していない
- 一般の経路制約や不等式制約が本質的で、Riccati再帰では扱いにくい
- 実時間の締切に対して逆向き / 前進計算の計算時間が合わない

## Python

非線形動力学を反復的に再線形化する完全なiLQR/DDP実装には、自動微分／正則化／直線探索が必要です。
次は、内部で解く有限計画期間のLQR部分問題だけを取り出した最小例です。
後退計算でフィードバック係数を作り、前進シミュレーションします。

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

この例は線形な1回のLQR求解です。
iLQR/DDPの非線形反復や一般制約処理は含みません。
実際の数値実装では、利用版のAPI・正則化・直線探索戦略を確認します。
公式参照資料には次があります。

- [CasADi](https://web.casadi.org/docs/)
- [acados](https://docs.acados.org/)
- [Drake MathematicalProgram](https://drake.mit.edu/doxygen_cxx/group__solvers.html)

## 診断値

- 費用の変化と直線探索の採用率
- 動力学の残差ノルム（前進シミュレーション後の動力学整合性）
- 制約違反
- KKT 残差（制約付き変種を使う場合）
- 時間格子を変えたときの解の変化
- 前進シミュレーションの安定性
- 逆向き / 前進計算の実行時間と反復数

## 失敗・切替の兆候

- 前進計算の前進シミュレーションが発散し、直線探索で費用が改善しない
- 後退計算で$Q_{uu}$が正定値でなくなり、正則化を強めても解消しない
- 反復を重ねても整合性の残差や費用の変化が停滞する
- 離散化の時間刻みを変えると解や費用が大きく変わる
- 一般経路制約の違反が反復後も残り続ける

## 次に読む

[最適制御の定式化](#/formulations/PA042)で、状態と制御入力を動力学がどう結ぶかを確認します。

[軌道変数](#/learn/concept.trajectory-variable)で基準となる状態/制御入力軌道を読みます。
[時間離散化](#/learn/concept.time-discretization)では局所モデルの時間刻みを確認し、時間構造の原型は[動的計画法](#/learn/dynamic-programming)で確かめます。

実行する制御入力列の先頭だけを使う場合は、[観測ごとに解き直す運用](#/learn/concept.receding-horizon)へ進みます。
前進シミュレーションの[動力学の残差](#/learn/concept.dynamics-defect)と制約違反は分けて記録します。

区間分割で感度を抑えるなら[Direct Multiple Shooting](#/learn/multiple-shooting)、経路制約を密に扱うなら[Direct Collocation](#/learn/direct-collocation)と比較します。
[最適制御・軌道最適化の選び分け](#/learn/family.optimal-control)では、この二つを含む全体の入口を確認できます。
