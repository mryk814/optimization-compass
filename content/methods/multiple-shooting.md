---
content_id: multiple-shooting
kind: method
method_id: M_MULTIPLE_SHOOTING
title_ja: Direct Multiple Shooting
title_en: Direct Multiple Shooting
summary: 時間区間を区間に分け、各区間で動力学を積分します。境界の連続性をNLPの等式制約として課す軌道最適化です。
source_ids: [S042, S043, S050, S076]
prerequisites: [concept.trajectory-variable, concept.dynamics-defect, concept.time-discretization]
related_ids: [concept.path-terminal-constraints, concept.receding-horizon, direct-shooting, direct-collocation, sqp]
aliases: [/learn/multiple-shooting]
status: published
last_reviewed: 2026-09-30
---

時間区間を区間に分け、各区間で動力学を積分します。境界の連続性をNLPの等式制約として課す軌道最適化です。

## 30秒でつかむ

長い前進シミュレーション一つで、すべての感度を伝える必要はありません。
**短い区間ごとに状態を置き、境界のずれを制約として管理する**のがこの手法の要点です。

- 見るもの: 区間ごとの前進シミュレーション、費用、接続整合性の残差、制約違反
- 動かすもの: 区間開始状態、制御入力、NLPの制約
- 前進の判断: 費用の改善と、区間境界・経路制約の成立
- 別に確認するもの: 区間数を変えたときの解、積分器の安定性、ソルバー時間
- 恐れていること: 初期軌道の不整合、整合性の残差の停滞、過大なNLP、実時間の締切超過

状態を変数に増やすことで、単一射撃法の長時間感度を抑えやすくなります。
ただし、接続制約を解く負担は残ります。

区間内の積分がどれだけ滑らかでも、隣の区間と境界でずれていれば一本の軌道とは呼べません。
記事後半と同じ2-区間問題では、初期推測に二つの短い前進シミュレーションが見えていても境界と目標に整合性の残差が残ります。

![1状態・2区間の固定Multiple Shooting問題を外部数値ライブラリを使わないPythonで評価した結果。初期推定値では区間0の終端と境界状態の決定変数、区間1の終端と目標の間にそれぞれ0.25の整合性の残差がある。接続制約を満たす計算後は二つの区間が境界と目標で接続し、整合性の残差ノルムが0になる。](./media/multiple-shooting-continuity-execution.svg "記事と同じ線形の2区間の定式化の等式制約のKKT方程式を厳密に解いた実行結果です。SciPy SLSQP自体の実行結果、非線形動力学、経路制約、一般的なソルバー性能は示しません。")

上段では緑の区間前進シミュレーションと橙の状態決定変数が赤い整合性の残差で離れています。
下段では同じ三つの時刻がつながり、接続制約の役割を形として確認できます。

## 一手の意味

### 何を変数にし、何を制約にしているか

計画期間全体を$N$個の区間に分けます。
各区間の開始状態は、独立な決定変数$x_0, x_1, \ldots, x_{N-1}$として持ちます。
各区間内では制御入力 $u_i$を仮定し、積分器で終端状態を計算します。

$$
\hat{x}_{i+1} = \Phi(x_i, u_i)
$$

ここで$\Phi$は区間内の積分結果です。
$\hat{x}_{i+1}$は積分器が計算した値であり、次区間の決定変数$x_{i+1}$とは別物です。
両者が一致するという条件

$$
\hat{x}_{i+1} - x_{i+1} = 0
$$

をNLPの等式制約（接続制約、または整合性の残差制約）として課します。目的関数は区間ごとの費用の和と終端費用で構成します。

### 単一射撃法と比べて何が変わるか

[Direct Shooting](#/learn/direct-shooting)（単一射撃法）は、初期状態から計画期間全体を一度に積分します。
最適化変数は制御入力だけです。
これに対し多重射撃法は、各区間の開始状態も変数化します。

- 長時間積分による感度の爆発を、区間単位の短い積分に分けて抑えられます。
  単一射撃法では初期時刻の制御入力の変化が計画期間全体に伝播し、勾配が極端になることがあります。
- 各区間へ個別に初期軌道の推測を与えられるため、不安定な動力学でも現実的な初期値を設定しやすくなります。
- 区間ごとの積分は互いに独立なので、並列に実行できます。

一方で決定変数の数は単一射撃法より増え、接続制約という形で問題の疎な構造が生まれます。

### 選点法との違い

[Direct Collocation](#/learn/direct-collocation)も状態を決定変数にしますが、整合性の残差の作り方が異なります。
多重射撃法は各区間を積分器（Runge–Kuttaなど）で進め、終端と次の開始状態の差を整合性の残差にします。
選点法は多項式近似と選点から整合性の残差を作ります。

積分器を信頼でき、動力学を区間ごとに扱いやすいなら多重射撃法が候補です。
経路制約が密で、時間格子の疎構造を強く使いたいなら選点法を検討します。

生成されるNLPは接続制約により疎な構造を持ちます。
[SQP](#/learn/sqp)や内点法といった制約付きNLP ソルバーで解きます。

実務では[CasADi](https://web.casadi.org/docs/)や[acados](https://docs.acados.org/)のような専用ツールも候補です。
利用版のAPIやソルバー選択は公式参照資料で確認します。

## 小さな例

Python例の1状態、2区間の積分系を使います。
各区間は0.5時間で、状態を0から1へ動かします。
境界状態 $x_1$ と二つの制御入力 $u_0,u_1$ が決定変数です。

| 記録 | $(x_1,u_0,u_1)$ | 目的値 | 接続制約の残差ノルム |
|---|---|---:|---:|
| 初期推測 | $(0.5000,0.5000,1.5000)$ | 1.2500 | 0.3536 |
| 1反復目 | $(0.5000,1.0000,1.0000)$ | 1.0000 | $1.86\times10^{-9}$ |
| 2反復目 | $(0.5000,1.0000,1.0000)$ | 1.0000 | $2.29\times10^{-16}$ |

初期推測では、最初の区間が0.25で終わるのに、次の区間は0.5から始まります。
二つの積分結果をそれぞれ計算できても、一本の軌道にはつながっていません。
求解後は両方の制御が1になり、状態は $0\to0.5\to1$ とつながります。
二つの制御が等しいと、同じ終端条件の下で二乗和が最小になります。

## 向く条件・避ける条件

### まず確認すること

| 項目 | 確認内容 |
|---|---|
| 区間 | 長さと分割位置が動力学の変化を表せるか |
| 初期化 | 各区間の状態と制御入力に初期軌道を置けるか |
| 積分器 | 区間内の動力学を安定して積分できるか |
| 制約 | 接続、経路、終端制約を分けて記録できるか |
| ソルバー | 疎なNLPを扱えるか |
| 実時間 | 並列積分と前回の解からの再開を含む求解時間が締切に合うか |

### 向いている条件

- 計画期間が中〜長く、動力学が不安定または非線形で感度が大きい
- 区間ごとに現実的な初期軌道の推測を用意できる
- 積分を並列化できる計算資源がある
- 接続制約を扱えるNLP ソルバー（SQP、内点法）を利用できる

計画期間が短く動力学が安定しているなら、変数の少ない[Direct Shooting](#/learn/direct-shooting)のほうが単純です。
経路制約が密なら、多項式近似の疎構造を使う[Direct Collocation](#/learn/direct-collocation)を検討します。

## Python

```python
import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import minimize

SEGMENT_DURATION = 0.5
INITIAL_STATE = 0.0
TARGET_STATE = 1.0


def integrate_segment(state0: float, control: float) -> float:
    solution = solve_ivp(lambda t, x: [control], (0.0, SEGMENT_DURATION), [state0])
    return float(solution.y[0, -1])


def unpack(vector: np.ndarray) -> tuple[float, float, float]:
    state1, control0, control1 = vector
    return state1, control0, control1


def objective(vector: np.ndarray) -> float:
    _, control0, control1 = unpack(vector)
    return float(SEGMENT_DURATION * (control0**2 + control1**2))


def continuity_constraints(vector: np.ndarray) -> np.ndarray:
    state1, control0, control1 = unpack(vector)
    end_of_segment0 = integrate_segment(INITIAL_STATE, control0)
    end_of_segment1 = integrate_segment(state1, control1)
    return np.array([end_of_segment0 - state1, end_of_segment1 - TARGET_STATE])


initial_guess = np.array([0.5, 0.5, 1.5])
result = minimize(
    objective,
    initial_guess,
    method="SLSQP",
    constraints={"type": "eq", "fun": continuity_constraints},
    options={"ftol": 1e-10, "maxiter": 200},
)

state1, control0, control1 = unpack(result.x)
print(result.success, result.x, np.linalg.norm(continuity_constraints(result.x)))
```

この例は1状態・2区間の最小構成です。
`state1`は区間境界の決定変数、`continuity_constraints`が整合性の残差に対応します。

実務では状態次元と区間数を決めます。
経路制約と積分器の許容誤差も明示します。
解が積分精度に依存していないかも確認します。

## 診断値

- 目的関数費用と可行な候補の最良コスト
- 動力学の残差ノルム（接続制約の残差）
- KKT 残差
- 制約違反
- 時間格子を変えたときの解の変化（区間分割を変えたときの解の変化）
- 前進シミュレーションの安定性
- ソルバー 実行時間と反復数

## 失敗・切替の兆候

- 整合性の残差が反復を重ねても縮小しない
- 区間ごとの前進シミュレーションが発散する
- 区間数や分割位置（時間格子）を変えると解が大きく変化する
- 初期軌道の推測が悪く、ソルバーが可行点へ到達しない
- 積分器の許容誤差を厳しくすると解や制約違反が大きく変わる
- ソルバー時間が実時間の締切を超える

## 次に読む

[最適制御の定式化](#/formulations/PA042)で、動力学、接続制約、終端条件を整理します。

[軌道変数](#/learn/concept.trajectory-variable)で、区間ごとの状態と制御入力を確認します。
[動力学の残差](#/learn/concept.dynamics-defect)では、接続制約を残差として読みます。
[時間離散化](#/learn/concept.time-discretization)では区間幅と積分器の影響を確認します。

制御入力だけを変数にする[Direct Shooting](#/learn/direct-shooting)と、状態を多項式近似する[Direct Collocation](#/learn/direct-collocation)を比較します。
生成された制約付きNLPの解き方は[SQP](#/learn/sqp)で確認できます。

長い計画期間や不安定な動力学では、区間分割が感度と初期軌道にどう効いたかを記録します。
