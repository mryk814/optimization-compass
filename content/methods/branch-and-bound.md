---
content_id: branch-and-bound
kind: method
method_id: M_BRANCH_BOUND
title_ja: Branch-and-Bound（分枝限定法）
title_en: Branch and Bound
summary: 離散問題を部分空間へ分枝し、incumbentとrelaxation boundで改善不能なsubtreeを除外しながら最適性の証明まで進める厳密探索法です。
source_ids: [S021, S022, S079]
prerequisites: []
related_ids: [branch-and-cut, cp-sat, dynamic-programming]
visualization_ids: [binary-knapsack-bnb-complete, binary-knapsack-bnb-budget]
comparison_ids: [COMPARE_KNAPSACK_BNB_BUDGET]
aliases: [/learn/branch-and-bound]
visualization_aliases: []
status: published
last_reviewed: 2026-07-24
---

離散問題を部分空間へ分枝し、incumbentとrelaxation boundで改善不能なsubtreeを除外しながら最適性の証明まで進める厳密探索法です。

## 探索木の1 node

各nodeは、元問題へ追加の固定条件やboundsを加えた部分問題です。nodeで次を計算します。

- infeasibleか
- relaxationや問題固有のboundはいくつか
- 実行可能解を作れるか
- incumbentを改善できる可能性があるか
- さらに分枝すべき変数は何か

minimizationでは、nodeのlower boundが現在のincumbent以上なら、そのsubtreeは改善できないためpruneできます。

## 全列挙をどこまで省けるか

naive enumerationは全割当を調べます。Branch-and-Boundは、

- 制約違反で実行不能
- boundがincumbentを改善不能
- symmetryやdominanceで重複

な領域をまとめて捨てます。調べなかった枝について「なぜ改善不能か」をboundで説明できることが重要です。

## boundとgapをどう読むか

- **incumbent / best feasible**: 現時点で見つかった最良実行可能解
- **global bound**: 未探索領域を含む理論上の限界
- **gap**: incumbentとboundの差

探索完了またはgap tolerance達成なら、定義したmodelに対して最適性を主張できます。time / node / memory budgetで止まった場合、incumbentは実行可能候補でも最適性は未証明です。

## まず確認すること

- 部分問題ごとにfeasible解またはboundを計算できるか
- minimization / maximizationのboundの向きを取り違えていないか
- 最適性の証明まで必要か、time / node / memory budget内の可行解で足りるか

ここが決まると、boundの強さとincumbentを見ながら、探索を続けるか止めるかを判断できます。

## Python: 0-1 knapsackの教育用探索

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class Item:
    value: int
    weight: int


def solve_knapsack(items: list[Item], capacity: int) -> tuple[int, list[int]]:
    ordered = sorted(items, key=lambda item: item.value / item.weight, reverse=True)
    best_value = 0
    best_choice: list[int] = []

    def fractional_bound(index: int, weight: int, value: int) -> float:
        remaining = capacity - weight
        bound = float(value)
        for item in ordered[index:]:
            if item.weight <= remaining:
                remaining -= item.weight
                bound += item.value
            else:
                bound += item.value * remaining / item.weight
                break
        return bound

    def search(index: int, weight: int, value: int, choice: list[int]) -> None:
        nonlocal best_value, best_choice
        if weight > capacity:
            return
        if value > best_value:
            best_value = value
            best_choice = choice.copy()
        if index == len(ordered):
            return
        if fractional_bound(index, weight, value) <= best_value:
            return

        item = ordered[index]
        search(index + 1, weight + item.weight, value + item.value, [*choice, 1])
        search(index + 1, weight, value, [*choice, 0])

    search(0, 0, 0, [])
    return best_value, best_choice


items = [Item(8, 4), Item(5, 3), Item(6, 5), Item(4, 2)]
print(solve_knapsack(items, capacity=8))
```

fractional knapsackのvalueをupper boundとして使っています。
一般MILPではLP relaxation／cut／presolve／heuristicなどをsolverが組み合わせます。

## 探索戦略

- best-bound: 証明側を進めやすい
- depth-first: memoryを抑え、incumbentを早く得る場合がある
- breadth-first: levelごとに探索するがmemoryが増えやすい
- hybrid: solverがphaseに応じて切替

branching variable／node selection／heuristicは性能へ強く影響します。
model formulationの強さも同じくらい重要です。

## 診断値

- incumbent / global bound / relative and absolute gap
- node count / open node count
- root relaxation gap
- first feasibleまでの時間
- prune reason別のnode数
- depth
- memory
- termination reason
- feasibility / integrality tolerance

## 探索完了と予算停止を分けて見る

[証明完了の探索木](#/theater/search-tree/binary-knapsack-bnb-complete)では、incumbentとglobal boundが一致するまでを追います。
[4 nodeで止まる探索木](#/theater/search-tree/binary-knapsack-bnb-budget)では、実行可能なincumbentがあっても正のgapと未探索nodeが残る状態を確認します。

[二つの停止結果を並べるCompare](#/compare/COMPARE_KNAPSACK_BNB_BUDGET)は、同じ4変数knapsackを使います。
instance・seed・branch順・初期incumbent・fractional boundを固定します。
9回のevaluation上限も共通にし、node stop limitだけを9から4へ変えます。

これは停止条件の読み方を学ぶ固定教材です。
CP-SATやMIP solverの速度、総当たりとの一般性能rankingを示すものではありません。

## 失敗・切替の兆候

- boundが弱くほぼ全列挙になる
- incumbentが長時間見つからない
- symmetryで同等nodeを反復
- Big-Mやscaleによりrelaxationが弱い
- node treeがmemoryを圧迫
- noisy black-boxをboundなしで無理に分枝
- 専用DP、flow、matchingで解ける構造を見落とす

::: warning
探索木が小さい一例だけでsolver一般の性能を評価しません。
problem instance／formulation／presolve／cut／heuristic／hardware／time limitを揃えます。
:::

## 次に読む

現代的MILP solverでcutを統合する枠組みは[Branch-and-Cut](#/learn/branch-and-cut)、論理・scheduling制約中心なら[CP-SAT](#/learn/cp-sat)も比較します。
