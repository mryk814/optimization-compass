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
last_reviewed: 2026-07-26
---

凸二次計画（convex QP）で「どの不等式制約が解で等号になるか」を表すworking setを推定・更新しながら、等式制約付きQPを繰り返し解く方法です。

## 何を見てworking setを更新するか

凸QPの標準形

$$
\min_x\; \tfrac{1}{2}x^TPx+q^Tx \quad\text{subject to}\quad Ax\le b
$$

を考えます（$P\succeq0$）。最適解では、不等式制約の一部だけが等号 $A_ix=b_i$ で成立します。残りの制約には余裕があります。

active-set QPは、等号になると推定した制約をworking set $W_k$ として扱います。$W_k$を等式制約とみなし、等式制約付きQPを解きます。候補点ではKKT条件を確認します。確認対象はstationarity／multiplier符号／feasibility／complementarityです。

- 満たされない不等式制約があればworking setへ追加する
- multiplierの符号が不適切な制約があればworking setから外す

を繰り返し、working setが安定するまで進みます。simplex法が頂点（basis）を辿るのと似た発想で、QPでは頂点でなく「有効な等式面」を辿ると考えると直感がつかみやすくなります。

## 等式制約QPを繰り返し解く仕組み

1反復ではworking set $W_k$ を固定します。その下で、$A_{W_k}x=b_{W_k}$を満たしながら$\tfrac{1}{2}x^TPx+q^Tx$を最小化する等式制約QPを解きます。これはKKT系

$$
\begin{bmatrix}P & A_{W_k}^T\\ A_{W_k} & 0\end{bmatrix}
\begin{bmatrix}x\\ \lambda\end{bmatrix}
=
\begin{bmatrix}-q\\ b_{W_k}\end{bmatrix}
$$

を解くことに帰着します。得られた解方向が現在のworking setの範囲内で実行可能なら、そのままstepを取ります。途中でinactiveな制約に触れた場合は、そこで止めます。この制約がblocking constraintです。停止後、その制約をworking setへ加えます。

「1反復＝1つの等式制約QPを解く」という構造は、[一般NLPのactive-set法](#/learn/active-set)にも共通します。一方、QP専用の実装ではKKT行列がQPの係数だけで決まります。そのため、rank-1更新やSchur補行列を使うfactorization更新に特化しやすい点が異なります。

制約を外す判断は、点を動かさずmultiplierの符号を見て行います。
制約を加える判断は、face上を進みblocking constraintへ触れた時点で行います。

![2変数の固定convex QPを原点から解くactive-set実行。原点Aではx1下限制約を外す。x2下限のface上をBまで進んでx1上限制約を加える。同じ点Bでx2下限制約を外す。斜めの制約へ進みCで最適になる。下段はremove → add → remove → add → optimalの5 eventを示す。](./media/active-set-qp-execution.svg "working setから制約を外し、blocking constraintを加える固定active-set QP実行")

図のAとBでは、`direction = 0` のまま負のmultiplierを持つ制約を外しています。
BとCへ向かう橙の線では、実行可能性を保つstep lengthを選び、最初に触れた制約を加えています。

> この図は2変数の固定convex QPをfeasibleな原点から解いた教材です。
> objectiveは `0.000 → -4.125`、最終点は `(1.5, 0.5)` です。
> degeneracyやcyclingは含みません。
> factorization更新costやactive-set QP一般の性能も示していません。

## Simplex法のQP版という直感とMPCでの再解

LPのsimplex法は、頂点から頂点へbasisを更新しながら進みます。active-set QPは「等号制約の組」であるworking setを更新します。この意味で、simplex法のQP版とみなせます。この類似性から、前回のworking setを初期値として使うwarm startが自然に働きます。特に、

- model predictive control（MPC）で毎周期わずかに変わるQPを再解する
- sequential quadratic programmingのsubproblemを繰り返し解く
- boundが少しずつ変わるportfolio再最適化

のように「直前の解に近いQPを何度も解く」場面では、working setがほとんど変わりません。そのため、少ない反復で収束しやすくなります。

一方、制約数が多い問題では、正しいworking setに到達するまでの反復数が組合せ的に増える場合があります。大規模疎QPでは、operator-splitting型やbarrier型のほうが安定することがあります。

## 向いている条件

| 条件 | 理由 |
|---|---|
| 凸QP（$P\succeq0$）として明示できる | KKT系の対称性・factorization更新がこの構造に依存するため |
| 小中規模、またはworking setの変化が小さいMPC的な再解 | working setの探索回数が少なく済むため |
| warm startできる近接問題を繰り返し解く | 前回のworking setをそのまま初期値にできるため |
| 高精度なbasisやactive constraint情報が必要 | 等式制約QPを厳密に解くため中間状態の解釈がしやすいため |

制約数が多くworking setが反復ごとに大きく変わる問題や、非凸QPを凸として誤って扱っている場合は避けます。そうした場合は[operator-splitting QP](#/learn/admm-qp)や[primal-dual barrier法](#/learn/barrier-lp-qp)を検討します。

## Python

図と同じQPを、working setを1制約ずつ更新して解きます。
`direction = 0` ならmultiplierを調べ、動けるならblocking constraintまで進みます。

```python
import numpy as np

hessian = np.diag([2.0, 1.0])
linear = np.array([-4.0, -1.0])
a_ub = np.array([
    [-1.0, 0.0],  # x1 >= 0
    [0.0, -1.0],  # x2 >= 0
    [1.0, 0.0],   # x1 <= 1.5
    [1.0, 1.0],   # x1 + x2 <= 2
])
b_ub = np.array([0.0, 0.0, 1.5, 2.0])
labels = ["x1 >= 0", "x2 >= 0", "x1 <= 1.5", "x1 + x2 <= 2"]

x = np.array([0.0, 0.0])
working = [0, 1]
events = []
for _ in range(10):
    gradient = hessian @ x + linear
    a_working = a_ub[working]
    kkt = np.block([
        [hessian, a_working.T],
        [a_working, np.zeros((len(working), len(working)))],
    ])
    solution = np.linalg.solve(kkt, np.r_[-gradient, np.zeros(len(working))])
    direction, multipliers = solution[:2], solution[2:]

    if np.linalg.norm(direction) <= 1e-10:
        if np.all(multipliers >= -1e-10):
            events.append(("optimal", None))
            break
        position = int(np.argmin(multipliers))
        removed = working.pop(position)
        events.append(("remove", labels[removed]))
        continue

    step_length = 1.0
    blocker = None
    for index, normal in enumerate(a_ub):
        if index in working or normal @ direction <= 1e-10:
            continue
        candidate = (b_ub[index] - normal @ x) / (normal @ direction)
        if candidate < step_length - 1e-12:
            step_length, blocker = float(candidate), index

    x += step_length * direction
    if blocker is not None:
        working.append(blocker)
        events.append(("add", labels[blocker]))

objective = 0.5 * x @ hessian @ x + linear @ x
print(events)
print(x, objective)
```

出力のevent順は `remove → add → remove → add → optimal` です。
最終点は `[1.5, 0.5]`、目的関数値は `-4.125` になります。

実務のactive-set型solverはfactorizationを更新し、等式制約QPを毎回ゼロから解くcostを抑えます。
OSQPのようなoperator-splitting型は、working setとは別の反復を使います。利用versionのAPIやdefault parameterは[OSQP公式ドキュメント](https://osqp.org/docs/)や[HiGHSドキュメント](https://highs.dev/)で確認します。

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

一般の非線形制約に対する違いは、[Active-set法](#/learn/active-set)で確認できます。同じ凸QPを別の反復法で解く考え方は、[operator-splitting QP](#/learn/admm-qp)へ進みます。barrier型との対比は[primal-dual barrier法](#/learn/barrier-lp-qp)で扱います。LP・QP・conic全体の位置付けは[LP・QP・錐最適化](#/learn/lp-qp-conic)で確認できます。
