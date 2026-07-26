---
content_id: dynamic-programming
kind: method
method_id: M_DYNAMIC_PROGRAMMING
title_ja: 動的計画法
title_en: Dynamic Programming
summary: 問題を状態（state）と段階（stage）に分け、同じ部分問題を再利用してBellman再帰を解く、離散問題向けの厳密法です。
source_ids: [S054]
prerequisites: []
related_ids: [dijkstra-astar, cp-sat, branch-and-bound]
aliases: [/learn/dynamic-programming]
status: published
last_reviewed: 2026-07-26
---

問題を状態（state）と段階（stage）に分け、同じ部分問題を再利用してBellman再帰を解く、離散問題向けの厳密法です。

## 最適化問題を状態へ変える

DPでは、意思決定の履歴をすべて保持しません。
将来の評価に必要な情報だけを`state`へまとめます。
Bellman再帰は、現在の`state`から選べる`action`と、その後の最適値を組み合わせます。

$$
V_t(s)=\min_a\left\{c_t(s,a)+V_{t+1}(T(s,a))\right\}
$$

- $s$: 現在の`state`
- $a$: 選べる`action`
- $T(s,a)$: 次の`state`
- $V_t(s)$: その`state`以降の最適値

重要なのは、`state`が将来を正しく評価できる十分な情報を持つことです。
同じ`state`へ到達した履歴を一つの部分問題として再利用します。

## tableを埋め、選択を戻る

次の0/1 knapsackでは、itemを1個ずつ追加する段階を縦軸、利用可能capacityを横軸にします。
各cellは、その範囲で得られる最大valueです。

![capacity 8の固定0/1 knapsackを4 itemで解いたDP table。itemを考慮する段階を行、capacity 0から8を列として最大valueを記録する。最終cellのvalue 13から青緑の線をbacktrackingすると、item AとBを選び、合計weight 7、unused capacity 1になる。](./media/dynamic-programming-knapsack-execution.svg "固定4 itemの整数knapsackをpure Pythonで実行した結果です。DP tableは厳密に13を返しますが、別instance、連続量、近似、solver一般の性能や大規模state spaceでの実用性は示しません。")

橙が大きいvalueを持つcell、青緑が最終cellから選択を復元するbacktrackingです。
item CとDを追加してもcapacity 8の最良valueは13から増えません。
backtrackingではAとBを選び、weightを`8 → 5 → 1`と戻します。

> 最大valueは13、選択はAとB、合計weightは7です。
> tableを埋める処理と、選択したitemを復元する処理は分けています。
> 固定4 itemの教材であり、DP一般の性能rankingではありません。

## 向いている条件

- knapsack
- shortest path
- sequence alignment
- lot sizing
- finite-horizon control
- resource allocation
- small state-space scheduling

汎用MIPへ書ける問題でも、`state`と`transition`が小さければDPを直接使える場合があります。
厳密保証とtableの各値を対応づけて説明しやすい点も特徴です。

## Python

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class Item:
    name: str
    weight: int
    value: int


def knapsack(
    items: list[Item],
    capacity: int,
) -> tuple[int, list[str], list[list[int]]]:
    table = [[0] * (capacity + 1) for _ in range(len(items) + 1)]
    take = [[False] * (capacity + 1) for _ in range(len(items) + 1)]

    for item_count, item in enumerate(items, start=1):
        for available in range(capacity + 1):
            skip_value = table[item_count - 1][available]
            take_value = (
                table[item_count - 1][available - item.weight] + item.value
                if item.weight <= available
                else -1
            )
            if take_value > skip_value:
                table[item_count][available] = take_value
                take[item_count][available] = True
            else:
                table[item_count][available] = skip_value

    selected = []
    remaining = capacity
    for item_count in range(len(items), 0, -1):
        if take[item_count][remaining]:
            item = items[item_count - 1]
            selected.append(item.name)
            remaining -= item.weight
    selected.reverse()
    return table[-1][-1], selected, table


items = [
    Item("A", weight=4, value=8),
    Item("B", weight=3, value=5),
    Item("C", weight=5, value=6),
    Item("D", weight=2, value=4),
]
value, selected, table = knapsack(items, capacity=8)
weight = sum(item.weight for item in items if item.name in selected)
print(f"selected={selected}, weight={weight}, value={value}")
print(f"last row={table[-1]}")
```

```text
selected=['A', 'B'], weight=7, value=13
last row=[0, 0, 4, 5, 8, 9, 12, 13, 13]
```

2次元tableを残すため、図の全cellとbacktrackingを同じ実行から再現できます。
memoryを減らすだけなら1次元rolling arrayへ置き換えられますが、選択復元には追加情報が必要です。

## 診断値

- state数
- action数
- transition数
- horizon
- memory
- value rangeによるpseudo-polynomial性

DPが厳密でも、常に高速とは限りません。
knapsackの$O(nC)$はcapacity $C$の数値に依存します。
input bit長に対する純粋な多項式時間とは限りません。

## 失敗・切替の兆候

`state`へ多くの履歴を入れるほど、tableが指数的に増える場合があります。

対策候補:

- dominanceによるstate pruning
- sparse dictionary
- rolling array
- approximation / discretization
- decomposition
- A*やlabel-setting
- MIP / CP-SATへの切替

::: warning
`state`を小さくするために必要情報を落とすと、異なる履歴を誤って同一`state`として扱います。
Markov性または最適部分構造を確認します。
:::

## 結果の保証

全`state`と`transition`を正しく評価して再帰を完了すれば、定義した離散modelに対する厳密解を得られます。
ただし、連続量の離散化誤差やmodel simplificationは別問題です。

## 次に読む

- 最短路へ特殊化する: [Dijkstra / A*](#/learn/dijkstra-astar)
- 一般の論理制約が増える: [CP-SAT](#/learn/cp-sat)
- boundで探索を刈り込む: [Branch and Bound](#/learn/branch-and-bound)
