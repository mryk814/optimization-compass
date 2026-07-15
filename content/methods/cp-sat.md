---
content_id: cp-sat
kind: method
method_id: M_CP_SAT
title_ja: CP-SATと制約プログラミング
title_en: CP-SAT and Constraint Programming
summary: Boolean・整数・論理・scheduling制約を伝播とSAT学習を含む探索で扱い、実行可能解・bound・停止statusを追う離散最適化法です。
source_ids: [S022, S053]
prerequisites: [branch-and-bound]
related_ids: [branch-and-bound, branch-and-cut, dynamic-programming]
visualization_ids: [binary-knapsack-bnb-complete, binary-knapsack-bnb-budget]
comparison_ids: []
aliases: [/learn/cp-sat]
visualization_aliases: []
comparison_aliases: []
status: published
last_reviewed: 2026-07-15
---

Boolean・整数・論理・scheduling制約を伝播とSAT学習を含む探索で扱い、実行可能解・bound・停止statusを追う離散最適化法です。

## 現実の問いをmodelへ移す

| 項目 | 例 |
|---|---|
| decision variables | 人・仕事・時間帯の割当、順序、optional task |
| objective | 費用、遅延、希望違反、makespan |
| hard constraints | 必要人数、資格、相互排他、precedence、time window |
| soft constraints | 希望、安定性、変更量をpenaltyとして表す |
| problem features | finite domain、論理関係、global scheduling constraint |

hard constraintとsoft penaltyを分けます。すべてを大きなpenaltyへ押し込むと、本当に禁止したい条件と単に避けたい条件を区別しにくくなります。

## CP-SATの内部をどう捉えるか

CP-SATは単純なtree enumerationではありません。実装は、

- domain propagation
- Boolean encoding
- conflict analysis / learned clauses
- presolve
- linear relaxationやcutの利用
- primal heuristic
- branching / restart

などを統合します。したがって教育用Search Treeはincumbent・bound・gap・pruneの概念を示しますが、実solver内部を完全再現する図ではありません。

## 整数化とscale

実数係数を整数へscaleする場合、丸め誤差と係数範囲を確認します。

- 通貨を円・銭のどちらで持つか
- 時間を秒・分のどちらで離散化するか
- 小数係数を何倍して整数化するか
- overflowや巨大係数で伝播が弱くならないか

「整数化できた」ことと、現実の精度を保ったことは別です。

## Python

```python
from ortools.sat.python import cp_model

model = cp_model.CpModel()
workers = range(3)
tasks = range(4)
assignment = {
    (worker, task): model.new_bool_var(f"assign_{worker}_{task}")
    for worker in workers
    for task in tasks
}

for task in tasks:
    model.add(sum(assignment[worker, task] for worker in workers) == 1)

capacity = [2, 2, 2]
for worker in workers:
    model.add(sum(assignment[worker, task] for task in tasks) <= capacity[worker])

cost = [
    [3, 8, 4, 6],
    [5, 2, 7, 3],
    [6, 4, 3, 5],
]
model.minimize(
    sum(cost[worker][task] * assignment[worker, task] for worker in workers for task in tasks)
)

solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 10.0
solver.parameters.random_seed = 7
status = solver.solve(model)

print(status, solver.objective_value, solver.best_objective_bound)
```

実行後はstatusを確認してからvalueを読みます。`FEASIBLE`は実行可能解を得たが最適性未証明、`OPTIMAL`は設定tolerance下で証明済み、`INFEASIBLE`はmodelが矛盾、`UNKNOWN`はbudget等で結論がない状態です。

## 診断値

- status
- objective / best bound / gap
- conflicts
- branches
- propagations
- restarts
- wall time
- first feasibleまでの時間
- solution count
- presolve reduction
- random seed / worker count

並列worker数を変えると探索順と再現性が変わる場合があります。

## 向いている条件

- Boolean・integer・finite-domain変数
- 論理含意、optional interval、no-overlap、cumulativeなど
- scheduling・assignment・packing
- feasibility自体が難しい
- time limit内の良い解とboundが欲しい

## Alternative-first

- pure shortest path / matching / flow → 専用graph algorithm
- small state DP → [動的計画法](#/learn/dynamic-programming)
- 強い線形緩和を持つMILP → [Branch-and-Cut](#/learn/branch-and-cut)
- 本質的に連続・滑らか → NLP/QP系

## 失敗・切替の兆候

- domainが巨大でpropagationが弱い
- symmetryにより同等解を反復
- soft penaltyのscaleがobjectiveを歪める
- 係数の整数scaleが過大
- feasible solutionが長時間見つからない
- `UNKNOWN`を`INFEASIBLE`と誤読
- continuous physicsを粗い整数gridへ無理に離散化

::: warning
CP-SAT、MIP、専用DPは同じ離散問題を異なる表現で解けます。algorithm名だけで比較せず、model、time limit、hardware、seed、worker数、gapを揃えます。
:::
