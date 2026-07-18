---
content_id: epsilon-constraint
kind: method
method_id: M_EPSILON_CONSTRAINT
title_ja: ε-constraint法
title_en: Epsilon-Constraint Method
summary: 一つの目的を最適化し、ほかの目的を許容上限・下限の制約へ移して、その閾値を変えながらPareto候補を集める方法です。
source_ids: [S039, S055]
related_ids: [multi-objective]
status: published
last_reviewed: 2026-07-18
---

一つの目的を最適化し、ほかの目的を許容上限・下限の制約へ移して、その閾値を変えながらPareto候補を集める方法です。

## 30秒でつかむ

この手法の気持ちは、**複数目的を曖昧な一つのscoreへ足し合わせる代わりに、最も重視する目的を一つ選び、残りは「ここまでは許す」という条件として扱いたい**というものです。

- 見ているもの: 主目的、他目的の値、feasibility、Pareto dominance
- 動かしているもの: ε thresholdと各単目的subproblemの解
- 前進の判断: 異なるtrade-off領域を実行可能に取得できたか
- 別に確認するもの: threshold grid、subproblem数、total evaluation budget
- 恐れていること: thresholdの選び方、目的scale、infeasible subproblem、重複解

weighted sumで取りにくい非凸Pareto frontの領域も候補にできますが、thresholdを何個解くかというbudgetが必要です。

## まず確認すること

| 項目 | 確認内容 |
|---|---|
| objective direction | 各目的がminimizeかmaximizeか |
| primary objective | 一時的に主目的として選べるか |
| ranges | 各目的の現実的な範囲を把握できるか |
| backend | εを制約にした単目的問題を解けるか |
| feasibility | thresholdごとのinfeasibilityを区別できるか |
| budget | thresholdの個数とsubproblemごとのevaluation costを許容できるか |
| decision use | 最終的に誰がtrade-offから選ぶか |

目的値をnormalizeせずに閾値幅を決めると、単位の大きな目的だけ細かく調べることがあります。

## 仕組み

二目的最小化を例に、$f_1$を主目的、$f_2$を制約へ移します。

$$
\min_x f_1(x)\quad \text{subject to}\quad f_2(x)\leq \epsilon,\; x\in X
$$

$\epsilon$を変えて複数回解き、得られた実行可能解から非支配解を残します。目的数が増えるとthreshold gridも増えるため、意思決定上重要な領域へ絞る工夫が必要です。

## 向く条件・避ける条件

向きやすい条件:

- 目的の一つを主目的として説明しやすい
- backend solverが制約付きsubproblemを安定に解ける
- 非凸frontも含め特定trade-off領域を調べたい
- 許容値に実務的意味がある

避ける条件:

- threshold範囲が不明
- 多数目的でgridが爆発する
- subproblem一回が極端に高価
- 実際には単一utilityが明確で複数解不要

## 診断値

見る値:

- thresholdごとのfeasibility
- 得られた非支配解数
- objective spaceのcoverage
- 重複解率
- backend solver status / gap
- decision makerが関心を持つ領域の密度
- thresholdごとのevaluation costとtotal budget

## うまくいったサインと切替サイン

切替サイン:

- 多数のthresholdがinfeasible → objective rangeを再推定
- 同じ解ばかり出る → threshold spacingまたはbackend toleranceを見直す
- 目的数が多くgridが重い → NSGA-IIIやMOEA/Dを検討
- preferenceが明確になった → 関心領域だけへthresholdを集中
- backendが局所解のみ → Pareto集合も局所候補であることを明示

## Python

```python
import numpy as np
from scipy.optimize import minimize


def cost(x: np.ndarray) -> float:
    return float((x[0] - 1.0) ** 2 + x[1] ** 2)


def risk(x: np.ndarray) -> float:
    return float(x[0] ** 2 + (x[1] - 1.0) ** 2)


def solve_for_epsilon(epsilon: float):
    constraint = {"type": "ineq", "fun": lambda x: epsilon - risk(x)}
    return minimize(cost, x0=np.array([0.5, 0.5]), constraints=[constraint])


solutions = [solve_for_epsilon(value) for value in np.linspace(0.2, 2.0, 8)]
print([(result.fun, risk(result.x), result.success) for result in solutions])
```

比較ではbackend、初期点、tolerance、threshold grid、subproblem数を固定します。
得られたPareto候補の数だけでなく、同じtotal evaluation budgetでどの領域を覆えたかを記録します。

## コラム: εはweightではない

weighted sumのweightは目的間の交換率を表します。ε-constraintのthresholdは、ある目的に対する許容限界です。意味が異なるため、同じ数字を対応させても同じ解になるとは限りません。

[多目的最適化とPareto front](#/learn/multi-objective)でdominance、ideal / nadir、reference pointの読み方を確認してください。
