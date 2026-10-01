---
content_id: direct-collocation
kind: method
method_id: M_DIRECT_COLLOCATION
title_ja: Direct Collocation
title_en: Direct Collocation
summary: 状態と制御入力を時間格子上の変数にし、動力学の残差を制約として同時に解く軌道最適化法です。
source_ids: [S042, S043, S050, S076, S102]
prerequisites: [concept.trajectory-variable, concept.dynamics-defect, concept.path-terminal-constraints, concept.time-discretization]
related_ids: [concept.receding-horizon, constrained-continuous, least-squares]
visualization_ids: [pendulum-collocation-coarse, pendulum-collocation-refined, pendulum-model-rollout-failure]
comparison_ids: [COMPARE_PENDULUM_COLLOCATION_MESH]
aliases: [/learn/direct-collocation]
status: published
last_reviewed: 2026-09-30
---

状態と制御入力を時間格子上の変数にし、動力学の残差を制約として同時に解く軌道最適化法です。

## 30秒でつかむ

この手法の気持ちは、**状態（state）をシミュレーションだけに任せない**ことです。
軌道全体を変数として置き、動力学とのずれを制約（constraint）として解きます。

- 見るもの: 状態 履歴、制御入力 履歴、費用、動力学の残差、制約違反
- 動かすもの: 時間格子上の状態と制御入力
- 前進の判断: コスト（費用）の改善、整合性の残差、経路制約（path constraint）、境界制約（boundary constraint）の同時成立
- 別に確認するもの: 時間格子（mesh）を細かくしたときの解の変化、ソルバー時間、実時間の締切
- 恐れていること: 粗い時間格子、離散化誤差、疎構造の破綻、未処理の事象

変数は増えます。
その代わり、長い計画期間や不安定動力学でも、全区間の前進シミュレーション感度を一つの初期点から伝え続けずに済む場合があります。

同じ軌道でも、時間格子点と制御入力による更新は別の対象です。
隣接点の動力学の残差も分けて読みます。

時間格子 node上の違反が許容誤差内なら、軌道全体も可行でしょうか。
固定pendulum教材では、そうとは限りません。

![同じpendulum swing-upをN=20、N=40、gravityを10%変えたvalidation rolloutで実行し、mesh node上と区間再構成またはvalidation rollout上のpath violationを反復ごとに比較した結果。node上では3runとも許容値へ近づくが、区間内では違反の残り方が異なる。](./media/optimal-control-mesh-execution.svg "固定Python Traceの実行結果です。mesh node上の収束と区間内またはmodel mismatch下の可行性を分けて読みます。連続時間可行性や実機安全性は保証しません。")

上段では3実行ともnode上の違反が下がります。
下段ではN=40がN=20より小さくなる一方、モデルと実際のずれの検証 前進シミュレーションには大きな違反が残ります。

## 一手の意味

Euler型の例では、隣接する状態の差から、制御入力による変化を引きます。
この差を0にする制約が、状態と制御を結びます。

$$
x_{k+1}-x_k-\Delta t\,u_k=0.
$$

### 点ではなく軌道を変数にする

連続時間系

$$
\dot{x}(t)=f(x(t),u(t),t)
$$

に対し、時間点ごとの状態 $x_k$ と制御入力 $u_k$ を決定変数として並べます。
動力学は選点法の公式で離散化します。
隣接点の整合性をNLPの制約（constraint）として渡します。

これにより、

- 初期 / 終端 条件
- 経路 制約
- 制御入力 上下限
- 障害物 / 安全性 制約
- 積分 費用

を同じモデルで扱えます。

### Shootingとの違い

| 観点 | Direct 選点法 | Direct shooting |
|---|---|---|
| 状態 | 決定変数として保持 | 順向き シミュレーションで消去 |
| 動力学 | 整合性の残差 制約 | 前進シミュレーション |
| 疎構造 | 帯状 / 疎 | 感度が長時間伝播 |
| 不安定な 動力学 | 比較的扱いやすい | 前進シミュレーションが発散しやすい |
| 変数数 | 多い | 少ない |

長い計画期間や不安定系では選点法の疎構造が有利な場合があります。
一方、時間格子（mesh）と離散化を設計し、連続時間の挙動を別途検証する必要があります。

## 小さな例

Python例の1状態積分系を使います。
初期位置0から時間1で位置1へ進み、制御入力の二乗積分を小さくします。
20区間の初期状態を直線、初期制御をすべて0に変えて実行しました。
これは本文の実行例と同じ問題で、初期軌道だけを変えた検査です。

| 記録 | 最終状態 | 最初の制御入力 | 目的値 | 等式残差のノルム |
|---|---:|---:|---:|---:|
| 初期点 | 1.0000 | 0.0000 | 0.0000 | 0.2236 |
| 1反復目 | 1.0000 | 1.0000 | 1.0000 | $8.33\times10^{-10}$ |
| 2反復目 | 1.0000 | 1.0000 | 1.0000 | $1.83\times10^{-16}$ |

初期軌道は目的値だけ見ると良く見えますが、制御入力0では状態が進みません。
状態と制御を同時に調整し、整合性の残差を減らして初めて有効な候補になります。
この例はEuler型の直接離散化です。
高次の選点法公式や連続時間の安全性を実証する例ではありません。

## 向く条件・避ける条件

### まず確認すること

| 項目 | 確認内容 |
|---|---|
| 動力学 | 連続時間系と離散化を定義できるか |
| 時間格子 | 事象や急変区間を表せる密度か |
| 制約 | 初期 / 終端、経路、制御入力 上下限を明示できるか |
| 微分 | 整合性の残差 Jacobianの疎 配置を利用できるか |
| 初期化 | 状態と制御入力の初期軌道を用意できるか |
| 実時間 | 求解時間と前回の解からの再開が運用締切に合うか |

コスト（費用）が下がっても、時間格子上の整合性の残差や制約違反が許容範囲に入るとは限りません。
ソルバー 状態区分、連続時間へ戻したシミュレーション、実時間運用を別々に確認します。

### 向く条件・避ける条件

向いている条件:

- 既知の 動力学を持つ軌道最適化
- 経路制約や境界制約の数が多い
- 疎 微分を利用できる
- 前回の解からの再開を使うMPC
- 状態（state）と制御入力の全履歴を説明したい

避ける／切り替える条件:

- 動力学が未同定または強く確率的
- 不連続な 事象を時間格子へ明示していない
- 微分や尺度合わせが不正確
- 時間格子（mesh）の粗さで解が格子依存
- 実時間の締切にソルバー時間が合わない

## Python

次は単一積分系 $x_{k+1}=x_k+\Delta t\,u_k$ をEuler 整合性の残差で表す最小例です。
厳密には高次選点法ではなく、直接離散化の入口です。

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

この例は単純な動力学です。
実務では積分誤差と状態 制約を保存します。
単位とソルバーの停止状態も別々に保存します。

## 診断値

軌道を位置だけで見せるとソルバー状態が分かりません。
次を同期表示します。

- 物理的な 軌道
- 状態 履歴
- 制御入力 履歴
- 動力学の残差
- 経路 制約違反
- 目的関数 累積
- 有効な 上下限
- 時間格子 点 / 細分化
- KKT条件の残差（residual）と停止理由

粗い時間格子では、離散NLPが可行でも連続系へ戻すと制約を破ることがあります。
確認は、時間格子上の整合性の残差だけで終えず、高精度シミュレーションと時間格子変更の両方で行います。

1. 時間格子上の整合性の残差を確認
2. 得られた制御入力で高精度シミュレーション
3. 時間格子間で目的関数と軌道を比較
4. 誤差が大きい区間を細分化
5. 前回の解からの再開して再求解

コスト（費用）と可行性は別の診断軸です。
時間格子依存性、KKT 残差、ソルバー時間も分けて読みます。

## 失敗・切替の兆候

- 時間格子（mesh）上のコスト（費用）は改善するが、高精度シミュレーションで制約（constraint）を破る → 時間格子を細分化し、離散化誤差を確認する
- 動力学の残差が停滞する → 微分、尺度合わせ、初期 軌道を見直す
- 経路制約（path constraint）の違反が時間格子間に残る → 事象区間や時間格子密度を見直す
- ソルバー時間が実時間の締切を超える → 時間格子、前回の解からの再開、問題 大きさ、専用ソルバーを検討する
- 動力学が未同定または強く確率的 → 整合性の残差を制約として置く決定論的な前提に依存しない定式化と比較する

::: warning
NLPの`success`は、連続時間問題の正しさを直接保証しません。
離散化誤差、モデルと実際のずれ、シミュレーション 検証を別に確認します。
:::

## 次に読む

[最適制御の定式化](#/formulations/PA042)で、動力学と経路制約を読むところから確認できます。

まず[軌道 変数](#/learn/concept.trajectory-variable)で状態と制御入力を同時に持つ意味を確認します。[動力学の残差](#/learn/concept.dynamics-defect)では時間格子上の等式制約を読みます。[経路・終端制約](#/learn/concept.path-terminal-constraints)で制約を評価する時刻を確認し、[時間離散化](#/learn/concept.time-discretization)で時間格子 細分化へ進みます。

[pendulum swing-up Case](#/gallery/EC029)ではnode 可行性と区間再構成を分けます。[時間格子 感度 Compare](#/compare/COMPARE_PENDULUM_COLLOCATION_MESH)ではN=20とN=40をcontrast-onlyで確認できます。観測ごとに再求解する用途では[観測ごとに解き直す運用](#/learn/concept.receding-horizon)へ進みます。
