---
content_id: active-set
kind: method
method_id: M_ACTIVE_SET
title_ja: Active-set法
title_en: Active-Set Methods
summary: 解で等号になる制約集合を推定し、そのface上の等式制約problemを解きながらactive setを追加・削除する方法です。
source_ids: [S004, S016, S055, S056]
prerequisites: [constrained-continuous]
related_ids: [constrained-continuous, projected-gradient, slsqp, dual-simplex]
aliases: [/learn/active-set]
status: published
last_reviewed: 2026-07-18
---

解で等号になる制約集合を推定し、そのface上の等式制約problemを解きながらactive setを追加・削除する方法です。

## 30秒でつかむ

Active-set法は、現在のactive setを仮の等式制約として解き、blocking constraintを追加し、multiplierの符号条件が崩れたconstraintを外す方法です。

- 見ているもの: active set、primal / dual residual、multiplier sign、blocking constraint
- 動かしているもの: $W_k$、search direction、step、constraintの追加・削除
- 前進の判断: equality-constrained solveが進み、primal feasibility・stationarity・multiplier sign・complementarityが整うこと
- 恐れていること: active setの振動、degeneracy / cycling、infeasible model

![多角形の可行領域の内側から候補点が辺へ進み、青緑のactiveな辺に沿って橙のblocking constraintへ近づく模式図](./media/active-set-feasible-face.png "active setを等式として扱い、候補が可行領域のfaceを移る直感を示す教育用模式図です。実際の追加・削除規則やmultiplierの符号までは図だけで決めません。")

## Active constraintとは

不等式 $g_i(x)\le0$ が解で $g_i(x)=0$ になるときactiveです。active-set法は現在の候補集合 $W_k$ を等式として扱い、

1. $W_k$ 上でsearch directionを計算
2. inactive constraintへ当たるまでstep
3. 必要ならconstraintを追加
4. multiplierが不適切ならconstraintを削除

します。

QPでは、正しいactive setが分かれば等式制約QPへ帰着できます。

## Multiplierの役割

active constraintのLagrange multiplierが符号条件を満たさない場合、そのconstraintをactive setから外す候補になります。したがって、

- primal feasibility
- stationarity
- multiplier sign
- complementarity

を一緒に確認します。

## Warm start

近いQPを繰り返す場合、前回のactive setとbasisが良いwarm startになります。

- model predictive control
- sequential quadratic programmingのsubproblem
- parameter sweep
- boundが少し変わるportfolio / allocation

で有効です。

## Python: box-constrained quadraticの教育例

```python
import itertools
import numpy as np


def objective(x: np.ndarray) -> float:
    return float(0.5 * x @ np.array([[4.0, 1.0], [1.0, 2.0]]) @ x - np.array([6.0, 3.0]) @ x)


lower = np.array([0.0, 0.0])
upper = np.array([1.0, 2.0])
candidates: list[np.ndarray] = []

# 2変数の教育例なので、free / lower / upperのactive patternを列挙します。
for pattern in itertools.product((-1, 0, 1), repeat=2):
    x = np.zeros(2)
    free = []
    for index, state in enumerate(pattern):
        if state == -1:
            x[index] = lower[index]
        elif state == 1:
            x[index] = upper[index]
        else:
            free.append(index)

    if free:
        hessian = np.array([[4.0, 1.0], [1.0, 2.0]])
        linear = np.array([6.0, 3.0])
        fixed = [index for index in range(2) if index not in free]
        rhs = linear[free] - hessian[np.ix_(free, fixed)] @ x[fixed]
        x[free] = np.linalg.solve(hessian[np.ix_(free, free)], rhs)
    if np.all(x >= lower) and np.all(x <= upper):
        candidates.append(x)

best = min(candidates, key=objective)
print(best, objective(best))
```

これはactive patternを列挙する小さな説明例です。実際のactive-set solverはpatternを賢く更新し、全列挙しません。

## 診断値

- active set size
- added / removed constraints
- primal / dual residual
- multiplier sign violation
- equality-constrained solve status
- step lengthとblocking constraint
- degeneracy
- iteration数
- warm-start reuse

## 向いている条件

- LP / convex QP
- 解でactive constraintが比較的少ない
- 高精度解やbasisが必要
- warm startする近接problem
- inequality構造を明示できる

## 避ける／切り替える条件

- active setが頻繁に大きく変化
- degeneracy / cycling
- constraint数が多くfactorization更新が重い
- nonconvex QPで局所性を無視
- noisy / discontinuous constraint
- infeasible model

## 失敗・切替の兆候

- active setの追加・削除が振動する → degeneracy / cyclingとfactorization更新を確認する
- multiplier sign violationやprimal / dual residualが残る → KKT条件とequality-constrained solve statusを確認する
- blocking constraintが頻繁に変わる → step lengthとactive set sizeを確認する
- infeasible modelになる → active-set法を続けず、制約の実行可能性を確認する

::: warning
active setが安定したことは、大域最適性の証明とは限りません。convexity、KKT residual、solver statusを確認します。
:::

## 次に読む

LP basis更新との関係は[Dual Simplex](#/learn/dual-simplex)、general smooth NLPでは[SLSQP](#/learn/slsqp)も比較します。
