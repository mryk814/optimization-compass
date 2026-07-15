---
content_id: dual-simplex
kind: method
method_id: M_DUAL_SIMPLEX
title_ja: Dual Simplex法
title_en: Dual Simplex Method
summary: dual可行性を保ちながらprimal infeasibilityを解消し、LPのbasisを効率よく再最適化するsimplex変種です。
source_ids: [S004, S016, S055]
prerequisites: [lp-qp-conic]
related_ids: [lp-qp-conic, branch-and-cut]
aliases: [/learn/dual-simplex]
status: published
last_reviewed: 2026-07-15
---

dual可行性を保ちながらprimal infeasibilityを解消し、LPのbasisを効率よく再最適化するsimplex変種です。

## Primal simplexとの対比

LPを標準形で考えると、

- primal simplex: primal feasibleなbasisを保ち、objectiveを改善する
- dual simplex: dual feasibleなbasisを保ち、primal feasibilityを回復する

という見方ができます。

制約の追加、bound変更、MIP nodeでのbranchingなどにより、以前のbasisがdual feasibleだがprimal infeasibleになる状況ではdual simplexが自然です。

## どこで使われるか

- MILPの各nodeでLP relaxationを再最適化
- 既存LPへ制約やcutを追加
- scenarioやparameter変更後のre-optimization
- presolve後に得られたbasisの利用
- sparseな大規模LP

ユーザーがalgorithmを直接選ばなくても、LP/MIP solverが内部で自動選択する場合があります。

## Python

```python
import numpy as np
from scipy.optimize import linprog

c = np.array([1.0, 2.0, 0.5])
a_ub = np.array([
    [-1.0, -1.0, 0.0],
    [2.0, 1.0, 1.0],
])
b_ub = np.array([-1.0, 4.0])

result = linprog(
    c,
    A_ub=a_ub,
    b_ub=b_ub,
    bounds=[(0.0, None), (0.0, None), (0.0, None)],
    method="highs-ds",
)

print(result.success, result.x, result.fun, result.message)
```

`highs-ds`はHiGHSのdual simplex solverを指定します。実装version、presolve、scaling、toleranceは結果の診断に含めます。

## 結果を読む

- primal feasibility residual
- dual feasibility residual
- objective value
- basis status
- simplex iteration数
- degeneracy / stalling
- presolve reduction
- infeasible / unbounded status
- numerical warning

LPの`infeasible`と`unbounded`は別の状態です。modeling error、単位、bounds、signを確認し、solver statusを単に「失敗」とまとめません。

## Degeneracy

複数のbasisが同じvertexを表すdegeneracyでは、pivotしてもobjectiveが変わらないことがあります。anti-cycling、pricing、perturbationなどは実装依存です。

::: note
simplex iteration数をinterior-point iteration数と直接比較しません。一反復の計算内容、factorization、crossover、warm startの有無が異なります。
:::

## 向いている／避ける条件

向いている:

- LP構造が明示される
- basis warm startが有効
- 制約追加後の再最適化
- MIP node LP
- exactなblack-box探索ではなく係数modelを解く

避ける／切り替える:

- nonlinear / nonconvexな関係を無理にLP化
- coefficient scaleが極端
- denseな巨大LPでbarrier法が適する
- black-box objective
- integer条件をLP解だけで満たしたと誤解

LP/QP/conic全体の位置付けは[LP・QP・錐最適化](#/learn/lp-qp-conic)、MILP内での利用は[Branch-and-Cut](#/learn/branch-and-cut)で確認できます。
