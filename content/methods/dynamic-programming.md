---
content_id: dynamic-programming
kind: method
method_id: M_DYNAMIC_PROGRAMMING
title_ja: 動的計画法
title_en: Dynamic Programming
summary: 問題をstateとstageに分け、同じ部分問題を再利用してBellman再帰を解く、離散問題向けの厳密法です。
source_ids: [S054]
prerequisites: []
related_ids: [dijkstra-astar, cp-sat, branch-and-bound]
aliases: [/learn/dynamic-programming]
status: published
last_reviewed: 2026-07-18
---

問題をstateとstageに分け、同じ部分問題を再利用してBellman再帰を解く、離散問題向けの厳密法です。

## 最適化問題を状態へ変える

DPでは、意思決定の履歴をすべて保持せず、将来に必要な情報だけをstateへまとめます。
Bellman再帰は、現在のstateから選べるactionと、その後の最適valueを組み合わせます。
代表的な形は

$$
V_t(s)=\min_a\left\{c_t(s,a)+V_{t+1}(T(s,a))\right\}
$$

です。

- $s$: 現在state
- $a$: action
- $T(s,a)$: 次state
- $V_t(s)$: そのstate以降の最適value

重要なのは、stateが「過去の全履歴を忘れても将来を正しく評価できる十分な情報」になっていることです。

## 向いている条件

- knapsack
- shortest path
- sequence alignment
- lot sizing
- finite-horizon control
- resource allocation
- small state-space scheduling

汎用MIPへ書ける問題でも、stateとtransitionが小さければDPの方が速く、厳密保証も説明しやすいことがあります。

## Python: 0-1 knapsack

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class Item:
    value: int
    weight: int


def knapsack(items: list[Item], capacity: int) -> int:
    best = [0] * (capacity + 1)
    for item in items:
        for remaining in range(capacity, item.weight - 1, -1):
            best[remaining] = max(
                best[remaining],
                best[remaining - item.weight] + item.value,
            )
    return best[capacity]


items = [Item(8, 4), Item(5, 3), Item(6, 5), Item(4, 2)]
print(knapsack(items, capacity=8))
```

capacityを後ろから更新することで、同じitemを一度だけ使う0-1条件を保っています。

## 診断値

DPが厳密でも、常に高速とは限りません。

- state数
- action数
- transition数
- horizon
- memory
- value rangeによるpseudo-polynomial性

を確認します。knapsackの $O(nC)$ はcapacity $C$ の数値に依存し、input bit長に対する純粋な多項式時間とは限りません。

## 失敗・切替の兆候

stateへ多くの履歴を入れるほど正確になりますが、tableが指数的に増える場合があります。

対策候補:

- dominanceによるstate pruning
- sparse dictionary
- rolling array
- approximation / discretization
- decomposition
- A*やlabel-setting
- MIP / CP-SATへの切替

::: warning
stateを小さくするために必要情報を落とすと、異なる履歴を誤って同一stateとして扱います。Markov性または最適部分構造を確認します。
:::

## 結果の保証

全state・transitionを正しく評価し再帰を完了すれば、定義した離散modelに対する厳密解を得られます。ただし、連続量の離散化誤差やmodel simplificationは別問題です。

## 次に読む

最短路への特殊化は[Dijkstra / A*](#/learn/dijkstra-astar)、一般の論理制約が増えた場合は[CP-SAT](#/learn/cp-sat)も比較します。
