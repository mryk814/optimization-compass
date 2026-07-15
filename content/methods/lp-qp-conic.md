---
content_id: lp-qp-conic
kind: method
method_id: MF_LP_QP_CONIC
title_ja: LP・QP・錐最適化
title_en: Linear, Quadratic, and Conic Optimization
summary: 線形・凸二次・錐構造を保ったままmodel化し、専用solverの保証と数値情報を利用します。
source_ids: [S004, S010, S012, S014, S055]
prerequisites: [concept.convexity]
related_ids: [concept.convexity, constrained-continuous]
visualization_ids: []
comparison_ids: []
aliases: [/learn/lp-qp-conic]
visualization_aliases: []
comparison_aliases: []
status: published
last_reviewed: 2026-07-15
---

線形・凸二次・錐構造を保ったままmodel化し、専用solverの保証と数値情報を利用します。

## どの構造を持っているか

| family | objective | constraints | 代表的な問い |
|---|---|---|---|
| LP | 線形 | 線形 | 生産量、輸送、配合 |
| convex QP | 凸二次 | 線形 | portfolio、MPC、regularized fitting |
| conic | 線形 | cone membership | norm、robust bound、semidefinite relaxation |

decision variables、objective direction、単位、constraint boundsを先に固定します。problem featuresは凸性、疎性、dual情報、warm start、必要な最適性gapです。

## Alternative-first check

最短路、最大流、least squaresなど、さらに専用のalgorithmへ落とせる場合は先に確認します。一方、凸構造をblack-box objectiveへ隠すとdual・infeasibility certificate・sensitivityを失います。

- candidate: HiGHS、OSQP、Clarabel、CVXPY経由の対応solver。
- conditional: SLSQPなど一般NLP。modelが滑らかでも、凸性とdual情報を十分活かせない場合があります。
- excluded: population-based search。厳密な凸modelに対して保証と効率を捨てる理由がない場合。

## 最小LP例

```python
import numpy as np
from scipy.optimize import linprog

cost = np.array([3.0, 2.0])
capacity = np.array([[-1.0, -1.0]])
required = np.array([-4.0])
result = linprog(cost, A_ub=capacity, b_ub=required, bounds=[(0, None), (0, None)])
print(result.status, result.fun, result.x)
```

## 実務上の注意

solver statusを目的値だけに置き換えません。primal/dual feasibility、gap、scaling、toleranceを一緒に確認します。QPではHessianが正半定値か、conic modelでは採用したconeと近似が現実の問いを保っているかを記録します。[問題構造Map](#/map)から凸性と制約classを往復できます。
