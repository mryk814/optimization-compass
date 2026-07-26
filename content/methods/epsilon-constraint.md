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
last_reviewed: 2026-07-26
---

一つの目的を最適化し、ほかの目的を許容上限・下限の制約へ移して、その閾値を変えながらPareto候補を集める方法です。

## 30秒でつかむ

複数目的を根拠のない一つのscoreへ足し合わせず、最も重視する目的を一つ選びます。
残りの目的は「ここまでは許す」という条件へ移します。

- 見ているもの: 主目的、他目的の値、feasibility、Pareto dominance
- 動かすもの: ε thresholdと各単目的subproblemの解
- 前進の判断: 異なるtrade-off領域で実行可能解を得られたか
- 別に確認するもの: threshold grid、subproblem数、total evaluation budget
- 恐れていること: thresholdの選び方、目的scale、infeasible subproblem、重複解

weighted sumで取りにくい非凸Pareto frontの領域も候補にできます。
一方で、thresholdごとにsubproblemを解くbudgetが必要です。

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

目的値をnormalizeせずに閾値幅を決めると、単位の大きな目的だけを細かく調べる場合があります。

## 仕組み

二目的最小化を例に、$f_1$を主目的、$f_2$を制約へ移します。

$$
\min_x f_1(x)\quad \text{subject to}\quad f_2(x)\leq \epsilon,\; x\in X
$$

$\epsilon$を変えて複数回解き、得られた実行可能解から非支配解を残します。
目的数が増えるとthreshold gridも増えるため、意思決定上重要な領域へ絞る必要があります。

## 上限を下げると選択が移る

次の固定生産計画では、需要18以上を満たす技術XとYの組合せを整数列挙します。
主目的は`cost`、制約へ移す目的は`emissions`です。

![需要18以上を満たす技術XとYの整数生産planを88個列挙したε-constraint実行。上段のobjective spaceでは橙がfeasible plan、青緑が4つのPareto planを示す。emissions上限を36、30、24、18と下げるたび、cost最小の選択はXとYの組合せを変えながらPareto front上を移る。上限12では実行可能planがない。](./media/epsilon-constraint-production-execution.svg "固定した2技術・需要18の整数列挙です。4つのthresholdはPareto planを一つずつ選び、ε=12はinfeasibleになります。別需要、連続変数、backend solver、threshold設計、ε-constraint一般の性能は示しません。")

上限36では低costな`(X, Y) = (6, 0)`を選びます。
上限を18まで下げると、より低emissionsな`(0, 9)`へ移ります。
上限12は実行可能領域より厳しいため、subproblemはinfeasibleです。

> 88 feasible planのうち、非支配planは4個です。
> 4個の実行可能thresholdは、それぞれ異なるPareto planを選びます。
> これは固定整数列挙であり、一般性能rankingではありません。

## 向く条件・避ける条件

向きやすい条件:

- 目的の一つを主目的として説明しやすい
- `backend solver`が制約付きsubproblemを安定に解ける
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
- thresholdごとの`evaluation cost`とtotal budget

## うまくいったサインと切替サイン

切替サイン:

- 多数のthresholdがinfeasible → objective rangeを再推定
- 同じ解ばかり出る → threshold spacingまたは`backend tolerance`を見直す
- 目的数が多くgridが重い → NSGA-IIIやMOEA/Dを検討
- preferenceが明確になった → 関心領域だけへthresholdを集中
- backendが局所解のみ → Pareto集合も局所候補であることを明示

## Python

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class Plan:
    x_count: int
    y_count: int
    output: int
    cost: int
    emissions: int


def enumerate_plans(demand: int = 18) -> list[Plan]:
    plans = []
    for x_count in range(11):
        for y_count in range(11):
            output = 3 * x_count + 2 * y_count
            if output < demand:
                continue
            plans.append(
                Plan(
                    x_count=x_count,
                    y_count=y_count,
                    output=output,
                    cost=8 * x_count + 7 * y_count,
                    emissions=6 * x_count + 2 * y_count,
                )
            )
    return plans


def solve_for_epsilon(
    plans: list[Plan],
    epsilon: int,
) -> Plan | None:
    eligible = [plan for plan in plans if plan.emissions <= epsilon]
    if not eligible:
        return None
    return min(
        eligible,
        key=lambda plan: (plan.cost, plan.emissions, plan.x_count, plan.y_count),
    )


plans = enumerate_plans()
for epsilon in (36, 30, 24, 18, 12):
    solution = solve_for_epsilon(plans, epsilon)
    if solution is None:
        print(f"epsilon={epsilon}: infeasible")
        continue
    print(
        f"epsilon={epsilon}: X={solution.x_count}, Y={solution.y_count}, "
        f"cost={solution.cost}, emissions={solution.emissions}"
    )
```

```text
epsilon=36: X=6, Y=0, cost=48, emissions=36
epsilon=30: X=4, Y=3, cost=53, emissions=30
epsilon=24: X=2, Y=6, cost=58, emissions=24
epsilon=18: X=0, Y=9, cost=63, emissions=18
epsilon=12: infeasible
```

このコードは`backend solver`の代わりに全整数planを列挙します。
比較では`backend`と初期点を固定します。
`tolerance`、threshold grid、subproblem数も揃えます。
Pareto候補数だけでなく、同じtotal evaluation budgetで覆えた領域も記録します。

## コラム: εはweightではない

weighted sumのweightは目的間の交換率を表します。
`ε-constraint`のthresholdは、ある目的に対する許容限界です。
意味が異なるため、同じ数字を対応させても同じ解になるとは限りません。

## 次に読む

- dominanceとfront全体を読む: [多目的最適化とPareto front](#/learn/multi-objective)
- 目的をweightでまとめる: [重み付き和scalarization](#/learn/weighted-sum)
- 多数目的へ進む: [NSGA-III](#/learn/nsga-iii)
