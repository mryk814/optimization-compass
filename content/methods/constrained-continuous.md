---
content_id: constrained-continuous
kind: method
method_id: MF_CONSTRAINED_NLP
title_ja: 制約付き連続最適化
title_en: Constrained Continuous Optimization
summary: 目的値だけでなく実行可能性・active constraint・停止理由を同時に追う連続最適化です。
source_ids: [S017, S029, S030, S055]
prerequisites: [concept.convexity]
related_ids: [concept.convexity, lp-qp-conic]
visualization_ids: []
comparison_ids: []
aliases: [/learn/constrained-continuous]
visualization_aliases: []
comparison_aliases: []
status: published
last_reviewed: 2026-07-15
---

目的値だけでなく実行可能性・active constraint・停止理由を同時に追う連続最適化です。

## 現実の問いを定義する

| 項目 | 例 |
|---|---|
| decision variables | 寸法、温度、流量、control input |
| objective | 重量、誤差、energy、costの最小化 |
| constraints | 強度、品質、balance equation、上下限 |
| problem features | nonlinear constraint、Jacobian、sparsity、feasible start |

現実の問いは「制約を満たす設計の中で何を改善するか」です。infeasibleな点の低いobjectiveは候補解ではありません。

## Alternative-first check

LP・QP・conic formへ落とせるなら専用solverを使います。等式制約を変数消去で安全に取り除ける場合も、dimensionとcondition numberを改善できます。

- candidate: SLSQP / SQP、interior-point、trust-region constrained法。
- conditional: penalty法。penalty係数とconstraint violationの解釈を別に管理できる場合。
- excluded: unconstrained BFGSをそのまま適用する方法。constraintを無視した点を最適解として返しうる場合。

## Representative implementationと最小例

SciPy SLSQP、Ipopt、Knitro、SNOPTが代表例です。実装ごとのderivative契約、sparse対応、status、constraint violationを確認します。

```python
import numpy as np
from scipy.optimize import minimize

def objective(x: np.ndarray) -> float:
    return float((x[0] - 1.0) ** 2 + (x[1] - 2.0) ** 2)

constraints = {"type": "ineq", "fun": lambda x: x[0] + x[1] - 2.0}
result = minimize(objective, x0=np.array([0.0, 2.0]), constraints=constraints, method="SLSQP")
print(result.success, result.fun, result.x)
```

## 実務上の注意

`success`だけでなく、最大constraint violation、stationarity、active constraint、iteration/evaluation budgetを保存します。初期点がinfeasibleな場合に各solverがどう回復するかも同じではありません。feasible regionとfailure contrastは後続の可視化sliceで同じcanonical problemへ接続します。
