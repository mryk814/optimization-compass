---
content_id: active-set-qp
kind: method
method_id: M_ACTIVE_SET_QP
title_ja: Active-set QP
title_en: Active-Set QP
summary: 凸二次計画（convex QP）で「どの不等式制約が解で等号になるか」を表すworking setを推定・更新しながら、等式制約付きQPを繰り返し解く方法です。
source_ids: [S012, S016, S055, S056]
prerequisites: [concept.convexity]
related_ids: [active-set, admm-qp, barrier-lp-qp, lp-qp-conic]
status: published
last_reviewed: 2026-07-18
---

凸二次計画（convex QP）で「どの不等式制約が解で等号になるか」を表すworking setを推定・更新しながら、等式制約付きQPを繰り返し解く方法です。

## 何を見てworking setを更新するか

凸QPの標準形

$$
\min_x\; \tfrac{1}{2}x^TPx+q^Tx \quad\text{subject to}\quad Ax\le b
$$

を考えます（$P\succeq0$）。最適解では、不等式制約の一部だけが等号 $A_ix=b_i$ で成立し、残りは余裕を持ちます。active-set QPは、現時点で等号になっていると推定した制約の集合をworking set $W_k$ として扱い、$W_k$を等式制約とみなした等式制約付きQPを解きます。候補点ではKKT条件（stationarity、multiplier符号、feasibility、complementarity）を確認します。

- 満たされない不等式制約があればworking setへ追加する
- multiplierの符号が不適切な制約があればworking setから外す

を繰り返し、working setが安定するまで進みます。simplex法が頂点（basis）を辿るのと似た発想で、QPでは頂点でなく「有効な等式面」を辿ると考えると直感がつかみやすくなります。

## 等式制約QPを繰り返し解く仕組み

working set $W_k$ を固定した1反復では、$A_{W_k}x=b_{W_k}$ の下で$\tfrac{1}{2}x^TPx+q^Tx$を最小化する等式制約QPを解きます。これはKKT系

$$
\begin{bmatrix}P & A_{W_k}^T\\ A_{W_k} & 0\end{bmatrix}
\begin{bmatrix}x\\ \lambda\end{bmatrix}
=
\begin{bmatrix}-q\\ b_{W_k}\end{bmatrix}
$$

を解くことに帰着します。得られた解方向が現在のworking setの範囲内で実行可能なら、そのままstepを取ります。途中でinactiveな制約に触れる（blocking constraint）場合は、そこで止めてその制約をworking setへ加えます。この「1反復＝1つの等式制約QPを解く」という構造が、[一般NLPのactive-set法](#/learn/active-set)にも共通する骨格ですが、QP専用の実装ではKKT行列がQPの係数だけで決まるため、factorizationの更新（rank-1更新やSchur補行列の利用など）に特化しやすい点が異なります。

## Simplex法のQP版という直感とMPCでの再解

LPのsimplex法は頂点から頂点へbasisを更新しながら進みますが、active-set QPはworking setという「等号制約の組」を更新しながら進むという意味で、simplex法のQP版とみなせます。この類似性から、前回のworking setを初期値として使うwarm startが自然に働きます。特に、

- model predictive control（MPC）で毎周期わずかに変わるQPを再解する
- sequential quadratic programmingのsubproblemを繰り返し解く
- boundが少しずつ変わるportfolio再最適化

のように「直前の解に近いQPを何度も解く」場面では、working setがほとんど変わらないため少ない反復で収束しやすくなります。一方、制約数が多い問題では、正しいworking setに到達するまでの反復数が組合せ的に増える場合があり、大規模疎QPではoperator-splitting型やbarrier型のほうが安定することがあります。

## 向いている条件

| 条件 | 理由 |
|---|---|
| 凸QP（$P\succeq0$）として明示できる | KKT系の対称性・factorization更新がこの構造に依存するため |
| 小中規模、またはworking setの変化が小さいMPC的な再解 | working setの探索回数が少なく済むため |
| warm startできる近接問題を繰り返し解く | 前回のworking setをそのまま初期値にできるため |
| 高精度なbasisやactive constraint情報が必要 | 等式制約QPを厳密に解くため中間状態の解釈がしやすいため |

制約数が多くworking setが反復ごとに大きく変わる問題や、非凸QPを凸として誤って扱っている場合は避けます。そうした場合は[operator-splitting QP](#/learn/admm-qp)や[primal-dual barrier法](#/learn/barrier-lp-qp)を検討します。

## Python

次はactive-set QPの考え方を教育用に近似した例です。2変数QPに対し、候補となるworking set（制約なし・各不等式制約を等号にした場合）を列挙してKKT系を解き、実行可能な候補の中から目的値が最良のものを選びます。実際のactive-set solverはworking setを1反復ごとに少しずつ更新するのに対し、この例は候補を総当たりする教育的な近似です。

```python
import itertools
import numpy as np

p = np.array([[4.0, 1.0], [1.0, 2.0]])
q = np.array([1.0, 1.0])
# 不等式制約 a_ub @ x <= b_ub
a_ub = np.array([
    [1.0, 0.0],
    [0.0, 1.0],
    [1.0, 1.0],
])
b_ub = np.array([1.0, 1.0, 1.5])


def objective(x: np.ndarray) -> float:
    return float(0.5 * x @ p @ x + q @ x)


def solve_equality_qp(active: tuple[int, ...]) -> np.ndarray | None:
    if not active:
        return np.linalg.solve(p, -q)
    a_active = a_ub[list(active)]
    kkt = np.zeros((2 + len(active), 2 + len(active)))
    kkt[:2, :2] = p
    kkt[:2, 2:] = a_active.T
    kkt[2:, :2] = a_active
    rhs = np.concatenate([-q, b_ub[list(active)]])
    try:
        solution = np.linalg.solve(kkt, rhs)
    except np.linalg.LinAlgError:
        return None
    return solution[:2]


best_x: np.ndarray | None = None
best_value = float("inf")
for size in range(len(a_ub) + 1):
    for active in itertools.combinations(range(len(a_ub)), size):
        candidate = solve_equality_qp(active)
        if candidate is None:
            continue
        if np.all(a_ub @ candidate <= b_ub + 1e-9):
            value = objective(candidate)
            if value < best_value:
                best_value = value
                best_x = candidate

print(best_x, best_value)
```

working setの候補を総当たりで列挙しているため、制約数が増えると組合せが急増します。実務ではOSQPなどのQP solverがworking setを賢く逐次更新します。利用versionのAPIやdefault parameterは[OSQP公式ドキュメント](https://osqp.org/docs/)や[HiGHSドキュメント](https://highs.dev/)で確認します。

## 診断値

- working set size（active constraint数）
- added / removed constraints
- 等式制約QP solveのstatus
- primal / dual residual
- multiplier sign violation
- step lengthとblocking constraint
- degeneracy
- iteration数
- warm-start reuse

## 失敗・切替の兆候

- working setが安定せず追加・削除を繰り返す（cycling）
- degeneracyでmultiplierの符号判定が不安定
- 制約数が多くfactorization更新のcostが支配的になる
- 非凸QP（$P$が不定）をそのまま扱っている
- infeasibleまたはunboundedの証明を目的値だけで見落とす

## 次に読む

一般の非線形制約に対するactive-set法との違いは[Active-set法](#/learn/active-set)、同じ凸QPをfactorization再利用の反復法で解く考え方は[operator-splitting QP](#/learn/admm-qp)、barrier型との対比は[primal-dual barrier法](#/learn/barrier-lp-qp)、LP・QP・conic全体の位置付けは[LP・QP・錐最適化](#/learn/lp-qp-conic)で確認できます。
