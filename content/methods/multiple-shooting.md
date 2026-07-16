---
content_id: multiple-shooting
kind: method
method_id: M_MULTIPLE_SHOOTING
title_ja: Direct Multiple Shooting
title_en: Direct Multiple Shooting
summary: 時間区間をsegmentに分割し、各segmentで独立にdynamicsを積分してsegment境界の連続性をNLPの等式制約として課す軌道最適化の定式化です。
source_ids: [S042, S043, S050, S076]
prerequisites: []
related_ids: [direct-shooting, direct-collocation, sqp]
aliases: [/learn/multiple-shooting]
status: published
last_reviewed: 2026-07-16
---

時間区間をsegmentに分割し、各segmentで独立にdynamicsを積分してsegment境界の連続性をNLPの等式制約として課す軌道最適化の定式化です。

## 何を変数にし、何を制約にしているか

horizon全体を$N$個のsegmentに分け、各segmentの開始stateを独立な決定変数$x_0, x_1, \ldots, x_{N-1}$として持ちます。各segment内ではcontrol $u_i$を仮定し、積分器で終端状態を計算します。

$$
\hat{x}_{i+1} = \Phi(x_i, u_i)
$$

ここで$\Phi$はsegment内の積分結果です。$\hat{x}_{i+1}$は積分器が計算した値であり、次segmentの決定変数$x_{i+1}$とは別物です。両者が一致するという条件

$$
\hat{x}_{i+1} - x_{i+1} = 0
$$

をNLPの等式制約（continuity制約、またはdefect制約）として課します。目的関数はsegmentごとのcostの和と終端costで構成します。

## single shootingと比べて何が変わるか

[Direct Shooting](#/learn/direct-shooting)（single shooting）は、初期状態からhorizon全体を一度に積分し、controlだけを最適化変数にします。これに対しmultiple shootingは各segmentの開始stateも変数化するため、次の違いが生まれます。

- 長時間積分による感度の爆発を、segment単位の短い積分に分割して抑えられます。single shootingでは初期時刻のcontrolの変化がhorizon全体に伝播し、gradientが極端に大きく・小さくなることがあります。
- 各segmentへ個別に初期軌道の推測を与えられるため、不安定なdynamicsでも現実的な初期値を設定しやすくなります。
- segmentごとの積分は互いに独立なので、並列に実行できます。

一方で決定変数の数はsingle shootingより増え、continuity制約という形で問題の疎な構造が生まれます。

## collocationとの違い

[Direct Collocation](#/learn/direct-collocation)もstateを決定変数にする点はmultiple shootingと共通しますが、defectの作り方が異なります。multiple shootingは各segmentを実際の積分器（Runge–Kuttaなど）でintegrationしてdefectを作るのに対し、collocationは多項式近似とcollocation pointでdefectを作ります。積分器を信頼できるほどdynamicsが scalarに扱いやすいならmultiple shooting、path constraintが密でmeshの疎構造を強く使いたいならcollocationが選択肢になります。

生成されるNLPはcontinuity制約により疎な構造を持ち、[SQP](#/learn/sqp)やinterior-point法といった制約付きNLP solverで解きます。実務では[CasADi](https://web.casadi.org/docs/)や[acados](https://docs.acados.org/)のような、multiple shootingを組み込みで扱う専用ツールを使うことが一般的です。利用versionのAPIやsolver選択は公式referenceで確認します。

## 向いている条件

- horizonが中〜長く、dynamicsが不安定または非線形で感度が大きい
- segmentごとに現実的な初期軌道の推測を用意できる
- 積分を並列化できる計算資源がある
- continuity制約を扱えるNLP solver（SQP、interior-point）を利用できる

horizonが短くdynamicsが安定しているなら、変数の少ない[Direct Shooting](#/learn/direct-shooting)のほうが単純です。path constraintが密で多項式近似の疎構造を強く使いたい場合は[Direct Collocation](#/learn/direct-collocation)を検討します。

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

この例は1状態・2segmentの最小構成です。`state1`はsegment境界の決定変数、`continuity_constraints`がdefectに対応します。実務ではstate次元、segment数、path constraint、積分器のtoleranceを明示的に設計し、解が積分精度に依存していないかを確認します。

## 診断値

- defect_norm（continuity制約の残差）
- KKT residual
- constraint_violation
- mesh_error（segment分割を変えたときの解の変化）
- rollout_stability

## 失敗・切替の兆候

- defectがiterationを重ねても縮小しない
- segmentごとのrolloutが発散する
- segment数や分割位置（mesh）を変えると解が大きく変化する
- 初期軌道の推測が悪く、solverが可行点へ到達しない
- 積分器のtoleranceを厳しくすると解や制約違反が大きく変わる

single shootingとの違いは[Direct Shooting](#/learn/direct-shooting)、状態を多項式近似で扱う定式化は[Direct Collocation](#/learn/direct-collocation)、生成される制約付きNLPの解き方は[SQP](#/learn/sqp)で確認できます。
