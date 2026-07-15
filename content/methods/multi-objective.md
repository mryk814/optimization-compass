---
content_id: multi-objective
kind: method
method_id: M_NSGA_II
title_ja: 多目的最適化とPareto front
title_en: Multi-objective Optimization and the Pareto Front
summary: 複数の目的を単一bestへ潰さず、支配されないtrade-off集合として意思決定を支援します。
source_ids: [S039, S055, S068]
prerequisites: []
related_ids: [concept.convexity, cma-es]
visualization_ids: [biobjective-quadratic-pareto-front]
comparison_ids: []
aliases: [/learn/multi-objective]
visualization_aliases: [biobjective-quadratic-pareto-front|/theater/multi-objective]
comparison_aliases: []
status: published
last_reviewed: 2026-07-15
---

複数の目的を単一bestへ潰さず、支配されないtrade-off集合として意思決定を支援します。

## 現実の問いを分ける

| 項目 | 例 |
|---|---|
| decision variables | 設計寸法、運転条件、配分 |
| objectives | costと性能、重量と強度、riskとreturn |
| constraints | feasibility、budget、安全限界 |
| problem features | objective direction、Pareto dominance、preference |

現実の問いは「一方を改善すると他方が悪化する候補の中で、どこを選ぶか」です。ideal pointやnadirはreferenceであり、常に実行可能な単一解ではありません。

## Alternative-first check

意思決定者のpreferenceが事前に明確なら、ε-constraintやgoal programmingで必要な領域だけ解く選択があります。weighted sumは簡単ですが、非凸なPareto frontの一部を取得できない場合があります。

- candidate: NSGA-II。非凸・black-boxで複数の非劣解を一度に探索したい場合。
- conditional: weighted sum / ε-constraint。preferenceとsolver構造を利用できる場合。
- excluded: 単目的solverを目的ごとに独立実行し、結果を一つのbestとして比較する方法。trade-off関係を保存しません。

## Representative implementationと最小例

`pymoo`はNSGA-IIとbenchmark problemを提供します。population、seed、generation、constraint handlingを記録します。

```python
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.optimize import minimize
from pymoo.problems import get_problem

problem = get_problem("zdt1")
result = minimize(problem, NSGA2(pop_size=40), ("n_gen", 50), seed=1, verbose=False)
print(result.F)
```

## 実務上の注意

plot上で左下に見える点だけを選ばず、目的の方向、normalization、制約、reference pointを明記します。近似frontの密度は精度保証ではありません。後続のPareto可視化ではdominated / non-dominated、選択中のpreference、schematicかexecutable resultかを画面上で分けます。
