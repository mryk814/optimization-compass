---
content_id: network-simplex
kind: method
method_id: M_NETWORK_SIMPLEX
title_ja: Network Simplex法
title_en: Network Simplex
summary: 最小費用流のnetwork構造を使い、basisを全域木として扱うことで一般のsimplex法より高速に解く専用法です。
source_ids: [S054]
prerequisites: []
related_ids: [primal-simplex, dijkstra-astar, family.discrete-structure]
status: published
last_reviewed: 2026-07-24
---

最小費用流のnetwork構造を使い、basisを全域木として扱うことで一般のsimplex法より高速に解く専用法です。

## 何を解いているか

最小費用流問題では、各nodeでflowの保存則を満たします。
そのうえで容量制約の範囲内にflowを流し、edgeごとの単位費用の合計を最小化します。
これは線形計画問題として定式化でき、[Primal simplex法](#/learn/primal-simplex)でも解けます。
ただし、node-arc接続行列の多くの成分は0です。
非零成分も$+1$と$-1$だけという特殊な構造を持ちます。
Network Simplex法は、basisを一般の行列ではなくgraph上の全域木として扱います。
この構造を使い、汎用simplex法より軽い更新で同じ最適解を求めます。

## Basisが全域木に対応する理由

線形計画のsimplex法では、basisは基底変数に対応する列の集合です。
最小費用流では、実行可能なbasisがnetworkの全域木（spanning tree）に対応します。
木の外にあるnon-basic edgeは、flowを0または容量上限に固定します。
残るnode数$-1$本のbasic edgeを決めれば、flow保存則からnetwork全体のflowが定まります。

1回のbasis変換（pivot操作）は、graph上で次のように見えます。

1. 被約費用から、改善方向へ入れるnon-basic edgeを選ぶ
2. そのedgeを木へ加え、ただ1つできるcycleに沿ってflowを動かす
3. 容量の上限または下限へ最初に達するedgeを木から外す

被約費用は、edge costと両端のnode potentialから計算できます。
したがって、一般のsimplex法が使う行列演算をgraph上の更新へ置き換えられます。

## 整数性という構造の恩恵

最小費用流問題のnode-arc接続行列はtotally unimodularです。
edgeの容量とnodeの需給量が整数なら、最適basic feasible solutionも整数になります。
整数解を得るためだけに、分枝限定法を加える必要はありません。
[Hungarian algorithm](#/learn/hungarian-algorithm)のような他のnetwork専用法にも、同じ構造由来の整数性が現れます。

この保証はnetwork構造に由来します。
複数edgeにまたがる論理条件やresource制約などのside constraintsを足すと、totally unimodularとは限りません。
その場合、線形緩和から整数解が得られる保証も失われます。

## 向いている条件

- 問題が最小費用流として定式化でき、node-arc接続行列がnetwork構造を保っている
- flow保存則と容量制約以外のside constraintsがない、または後で分離できる
- 整数容量・整数需給量に対して整数最適解が必要
- 大規模なnetworkで汎用simplex法より高速な専用solverを使いたい

## 避ける／切り替える条件

side constraintsが加わり、node-arc接続行列のnetwork構造が崩れる場合は専用法の前提が成り立ちません。この場合は、一般のLP（[Primal simplex法](#/learn/primal-simplex)などのLP・QP・錐最適化solver）や、離散変数を含むならMILP・CP-SATへ戻ることを検討します。

## Python

```python
import numpy as np
from scipy.optimize import linprog


def build_incidence_matrix(
    edges: list[tuple[int, int]], n_nodes: int
) -> np.ndarray:
    incidence = np.zeros((n_nodes, len(edges)))
    for edge_index, (tail, head) in enumerate(edges):
        incidence[tail, edge_index] = 1.0
        incidence[head, edge_index] = -1.0
    return incidence


edges = [(0, 1), (0, 2), (1, 2), (1, 3), (2, 3)]
costs = np.array([4.0, 2.0, 1.0, 5.0, 3.0])
capacities = np.array([4.0, 3.0, 2.0, 4.0, 5.0])
supply_demand = np.array([4.0, 0.0, 0.0, -4.0])

incidence = build_incidence_matrix(edges, n_nodes=4)
bounds = [(0.0, capacity) for capacity in capacities]

result = linprog(
    c=costs,
    A_eq=incidence,
    b_eq=supply_demand,
    bounds=bounds,
    method="highs",
)

print(result.success, result.x, result.fun)
```

このコードは`scipy.optimize.linprog`で最小費用流を一般のLPとして解く教育用の例です。
大規模な実務問題では、node-arc構造を直接使うnetwork simplex実装を検討します。
対応範囲は、公式の[NEOS Guide: Optimization Problem Types](https://neos-guide.org/guide/types/)と利用versionのsolverドキュメントで確認します。

## 診断値

network構造を保てているかと、basis更新が最適性条件へ近づいているかを確認します。

- states（basisに対応する全域木の構造）
- edges（networkのedge数と容量制約の有無）
- labels（node potentialの値）
- memory（全域木構造と補助配列が使うmemory量）
- feasibility（需給量の総和が0で、全nodeの需要を満たせるか）
- optimality condition（すべてのnon-basic edgeで被約費用の符号条件が満たされているか）

## 失敗・切替の兆候

- side constraintsの追加でnode-arc接続行列がnetwork構造を保てなくなっている
- 需給量や容量が整数でなく、整数解を前提とした後段処理と食い違う
- 需給量の総和が0でない、または容量不足で全nodeの需要を満たせない
- 無限容量の負費用cycleがあり、目的値を下げ続けられる
- 問題規模に対してnode数・edge数が巨大で、汎用LPとして解くと遅い

## 次に読む

同じ「node-arc構造を専用法で使う」という考え方は[Primal simplex法](#/learn/primal-simplex)や[Dijkstra法とA*](#/learn/dijkstra-astar)にも共通します。離散・組合せ最適化全体の選び分けは[離散・組合せ最適化の選び分け](#/learn/family.discrete-structure)を参照してください。
