---
content_id: cp-sat
kind: method
method_id: M_CP_SAT
title_ja: CP-SATと制約プログラミング
title_en: CP-SAT and Constraint Programming
summary: 論理・整数・組合せ制約を伝播と探索で扱い、実行可能性と目的値を同時に詰める方法です。
source_ids: [S022, S053]
prerequisites: [branch-and-bound]
related_ids: [branch-and-bound]
visualization_ids: [binary-knapsack-bnb-complete, binary-knapsack-bnb-budget]
comparison_ids: []
aliases: [/learn/cp-sat]
visualization_aliases: []
comparison_aliases: []
status: published
last_reviewed: 2026-07-15
---

論理・整数・組合せ制約を伝播と探索で扱い、実行可能性と目的値を同時に詰める方法です。

## 現実の問いをモデルへ移す

| 項目 | 例 |
|---|---|
| decision variables | 人・仕事・時間帯の割当を表すBooleanまたは整数変数 |
| objective | 希望違反、遅延、費用などの合計を最小化 |
| constraints | 必要人数、資格、順序、相互排他、時間窓 |
| problem features | 離散変数、論理制約、組合せ探索、実行可能性 |

現実の問いは「どの割当ならすべてのhard constraintを満たし、その中でsoft penaltyを小さくできるか」です。soft constraintを先にhard constraintへ混ぜると、実行可能解が存在しない理由を追いにくくなります。

## Alternative-first check

ネットワークフロー、matching、区間schedulingなど専用多項式時間algorithmで書けるなら、まず専用解法を確認します。線形緩和が強い純粋なMIPならBranch-and-Cutも有力です。CP-SATは、論理関係・reification・複雑なscheduling制約を自然に表せるときの候補です。

- candidate: CP-SAT。離散・論理制約が中心で、実行可能解とboundを追いたい場合。
- conditional: MIP。線形制約と強い連続緩和を持つ場合。
- excluded: Nelder–Meadなど連続black-box法。離散制約をnativeに扱わず、実行可能性や最適性gapを説明できません。

## Representative implementationと最小例

OR-Tools CP-SATとMiniZincが代表的です。status、best bound、time limit、random seedを結果と一緒に保存します。

```python
from ortools.sat.python import cp_model

model = cp_model.CpModel()
x = model.new_bool_var("x")
y = model.new_bool_var("y")
model.add(x + y <= 1)
model.maximize(3 * x + 2 * y)

solver = cp_model.CpSolver()
status = solver.solve(model)
print(status, solver.value(x), solver.value(y), solver.objective_value)
```

## 読み違えないために

探索木の模式図は、実solver内部のSAT learningやpresolveを完全再現したものではありません。[Search-tree Theater](#/theater/search-tree/binary-knapsack-bnb-complete)ではincumbent・bound・gapの意味を確認し、実装の性能比較には同じmodel、同じ時間制限、同じhardwareを使います。
