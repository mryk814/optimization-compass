---
content_id: multiple-shooting
kind: method
method_id: M_MULTIPLE_SHOOTING
title_ja: Direct Multiple Shooting
title_en: Direct Multiple Shooting
summary: 時間区間をsegmentに分け、各segmentでdynamicsを積分します。境界の連続性をNLPの等式制約として課す軌道最適化です。
source_ids: [S042, S043, S050, S076]
prerequisites: [concept.trajectory-variable, concept.dynamics-defect, concept.time-discretization]
related_ids: [concept.path-terminal-constraints, concept.receding-horizon, direct-shooting, direct-collocation, sqp]
aliases: [/learn/multiple-shooting]
status: published
last_reviewed: 2026-07-26
---

時間区間をsegmentに分け、各segmentでdynamicsを積分します。境界の連続性をNLPの等式制約として課す軌道最適化です。

## 30秒でつかむ

長いrollout一つで、すべての感度を伝える必要はありません。
**短いsegmentごとにstateを置き、境界のずれをconstraintとして管理する**のがこの手法の要点です。

- 見ているもの: segmentごとのrollout、cost、continuity defect、constraint violation
- 動かしているもの: segment開始state、control、NLPの制約
- 前進の判断: costの改善と、segment境界・path constraintの成立
- 別に確認するもの: segment数を変えたときの解、積分器の安定性、solver時間
- 恐れていること: 初期軌道の不整合、defectの停滞、過大なNLP、real-time deadline超過

stateを変数に増やすことで、single shootingの長時間感度を抑えやすくなります。
ただし、continuity制約を解く負担は残ります。

segment内の積分がどれだけ滑らかでも、隣のsegmentと境界でずれていれば一本の軌道とは呼べません。
記事後半と同じ2-segment問題では、初期guessに二つの短いrolloutが見えていてもboundaryとtargetにdefectが残ります。

![1 state、2 segmentの固定Multiple Shooting問題をpure Pythonで評価した結果。初期guessではsegment 0のendpointと境界state decision、segment 1のendpointとtargetの間にそれぞれ0.25のdefectがある。continuity solve後は二つのsegmentがboundaryとtargetで接続し、defect normが0になる。](./media/multiple-shooting-continuity-execution.svg "記事と同じlinear 2-segment定式化をexact equality KKTで解いた実行結果です。SciPy SLSQP自体の実行結果、非線形dynamics、path制約、一般的なsolver性能は示しません。")

上段では緑のsegment rolloutと橙のstate decisionが赤いdefectで離れています。
下段では同じ三つの時刻がつながり、continuity constraintの役割を形として確認できます。

## まず確認すること

| 項目 | 確認内容 |
|---|---|
| segment | 長さと分割位置がdynamicsの変化を表せるか |
| initialization | 各segmentのstateとcontrolに初期軌道を置けるか |
| integrator | segment内のdynamicsを安定して積分できるか |
| constraints | continuity、path、terminal constraintを分けて記録できるか |
| solver | sparseなNLPを扱えるか |
| real-time | 並列積分とwarm startを含むsolve timeがdeadlineに合うか |

## 何を変数にし、何を制約にしているか

horizon全体を$N$個のsegmentに分けます。
各segmentの開始stateは、独立な決定変数$x_0, x_1, \ldots, x_{N-1}$として持ちます。
各segment内ではcontrol $u_i$を仮定し、積分器で終端状態を計算します。

$$
\hat{x}_{i+1} = \Phi(x_i, u_i)
$$

ここで$\Phi$はsegment内の積分結果です。
$\hat{x}_{i+1}$は積分器が計算した値であり、次segmentの決定変数$x_{i+1}$とは別物です。
両者が一致するという条件

$$
\hat{x}_{i+1} - x_{i+1} = 0
$$

をNLPの等式制約（continuity制約、またはdefect制約）として課します。目的関数はsegmentごとのcostの和と終端costで構成します。

## single shootingと比べて何が変わるか

[Direct Shooting](#/learn/direct-shooting)（single shooting）は、初期状態からhorizon全体を一度に積分します。
最適化変数はcontrolだけです。
これに対しmultiple shootingは、各segmentの開始stateも変数化します。

- 長時間積分による感度の爆発を、segment単位の短い積分に分けて抑えられます。
  single shootingでは初期時刻のcontrolの変化がhorizon全体に伝播し、gradientが極端になることがあります。
- 各segmentへ個別に初期軌道の推測を与えられるため、不安定なdynamicsでも現実的な初期値を設定しやすくなります。
- segmentごとの積分は互いに独立なので、並列に実行できます。

一方で決定変数の数はsingle shootingより増え、continuity制約という形で問題の疎な構造が生まれます。

## collocationとの違い

[Direct Collocation](#/learn/direct-collocation)もstateを決定変数にしますが、defectの作り方が異なります。
multiple shootingは各segmentを積分器（Runge–Kuttaなど）で進め、終端と次の開始stateの差をdefectにします。
collocationは多項式近似とcollocation pointからdefectを作ります。

積分器を信頼でき、dynamicsをsegmentごとに扱いやすいならmultiple shootingが候補です。
path constraintが密で、meshの疎構造を強く使いたいならcollocationを検討します。

生成されるNLPはcontinuity制約により疎な構造を持ちます。
[SQP](#/learn/sqp)やinterior-point法といった制約付きNLP solverで解きます。

実務では[CasADi](https://web.casadi.org/docs/)や[acados](https://docs.acados.org/)のような専用ツールも候補です。
利用versionのAPIやsolver選択は公式referenceで確認します。

## 向いている条件

- horizonが中〜長く、dynamicsが不安定または非線形で感度が大きい
- segmentごとに現実的な初期軌道の推測を用意できる
- 積分を並列化できる計算資源がある
- continuity制約を扱えるNLP solver（SQP、interior-point）を利用できる

horizonが短くdynamicsが安定しているなら、変数の少ない[Direct Shooting](#/learn/direct-shooting)のほうが単純です。
path constraintが密なら、多項式近似の疎構造を使う[Direct Collocation](#/learn/direct-collocation)を検討します。

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

この例は1状態・2segmentの最小構成です。
`state1`はsegment境界の決定変数、`continuity_constraints`がdefectに対応します。

実務ではstate次元とsegment数を決めます。
path constraintと積分器のtoleranceも明示します。
解が積分精度に依存していないかも確認します。

## 診断値

- objective costとbest feasible cost
- defect_norm（continuity制約の残差）
- KKT residual
- constraint_violation
- mesh_error（segment分割を変えたときの解の変化）
- rollout_stability
- solver wall timeとiteration数

## 失敗・切替の兆候

- defectがiterationを重ねても縮小しない
- segmentごとのrolloutが発散する
- segment数や分割位置（mesh）を変えると解が大きく変化する
- 初期軌道の推測が悪く、solverが可行点へ到達しない
- 積分器のtoleranceを厳しくすると解や制約違反が大きく変わる
- solver時間がreal-time deadlineを超える

## 次に読む

[trajectory variable](#/learn/concept.trajectory-variable)で、segmentごとのstateとcontrolを確認します。
[dynamics defect](#/learn/concept.dynamics-defect)では、continuity constraintを残差として読みます。
[時間discretization](#/learn/concept.time-discretization)ではsegment幅と積分器の影響を確認します。

controlだけを変数にする[Direct Shooting](#/learn/direct-shooting)と、stateを多項式近似する[Direct Collocation](#/learn/direct-collocation)を比較します。
生成された制約付きNLPの解き方は[SQP](#/learn/sqp)で確認できます。

長いhorizonや不安定なdynamicsでは、segment分割が感度と初期軌道にどう効いたかを記録します。
