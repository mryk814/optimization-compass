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
last_reviewed: 2026-07-18
---

最小費用流のnetwork構造を使い、basisを全域木として扱うことで一般のsimplex法より高速に解く専用法です。

## 何を解いているか

最小費用流問題は、各nodeでflowの保存則を満たしながら、各edgeの容量制約の範囲でflowを流し、edgeごとの単位費用の合計を最小化する問題です。
これは線形計画問題として定式化でき、[Primal simplex法](#/learn/primal-simplex)でも解けます。
しかし、この線形計画のnode-arc接続行列は、行の多くが0で、非零成分が$+1$と$-1$だけという特殊な構造を持ちます。
Network Simplex法は、この構造を活かし、basisを一般の行列演算ではなくgraph上の全域木として扱うことで、汎用simplex法より高速に同じ最適解を求めます。

## Basisが全域木に対応する理由

線形計画のsimplex法では、basisは基底変数に対応する列の集合です。最小費用流の場合、node-arc接続行列の性質から、実行可能なbasisは常にnetworkの全域木（spanning tree）に対応することが分かっています。全域木上の各edgeにflow量を割り当てれば、木の外にあるnon-basic edgeのflowは0または容量上限のどちらかに固定され、node数から1を引いた本数のbasic edgeのflow量だけを決めればnetwork全体のflowが定まります。

このため、basis変換（pivot操作）は行列の行基本変形ではなく、木に1本のedgeを追加してcycleを作り、そのcycleに沿ってflowを押し出し、最も制約が厳しいedgeを木から外すという、graph上の操作として実行できます。被約費用の計算もnode potentialの差として求まり、一般のsimplex法が必要とする行列演算より軽い計算で済みます。

## 整数性という構造の恩恵

最小費用流問題のnode-arc接続行列はtotally unimodularです。この性質により、edgeの容量とnodeの需給量がすべて整数であれば、線形緩和のまま解いた最適basic feasible solutionは自動的に整数値になります。つまり、整数解を得るために分枝限定法などの追加操作を行う必要がありません。これは、network構造を持つ問題に共通する利点であり、[Hungarian algorithm](#/learn/hungarian-algorithm)のような他の専用法にも同様の整数性が現れます。

ただし、この整数性はnetwork構造そのものに由来するため、side constraints（複数edgeにまたがる論理条件やresource制約など）を追加すると、接続行列がtotally unimodularでなくなり、整数性の保証は失われます。

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

このコードは`scipy.optimize.linprog`で最小費用流を一般のLPとして解く教育用の例です。実務でnetwork構造を持つ大規模な最小費用流を解く場合は、node-arc構造を直接利用する専用のnetwork simplex実装のほうが高速です。利用するsolverやライブラリの対応範囲は、公式の[NEOS Guide: Optimization Problem Types](https://neos-guide.org/guide/types/)などの資料と、利用versionのドキュメントを確認します。

## 診断値

network構造を保てているかと、basis更新が最適性条件へ近づいているかを確認します。

- states（basisに対応する全域木の構造）
- edges（networkのedge数と容量制約の有無）
- labels（node potentialの値）
- memory（全域木構造と補助配列が使うmemory量）
- optimality condition（すべてのnon-basic edgeで被約費用の符号条件が満たされているか）

## 失敗・切替の兆候

- side constraintsの追加でnode-arc接続行列がnetwork構造を保てなくなっている
- 需給量や容量が整数でなく、整数解を前提とした後段処理と食い違う
- 負の費用cycleなど、想定していない前提が紛れ込んでいる
- 問題規模に対してnode数・edge数が巨大で、汎用LPとして解くと遅い

## 次に読む

同じ「node-arc構造を専用法で使う」という考え方は[Primal simplex法](#/learn/primal-simplex)や[Dijkstra法とA*](#/learn/dijkstra-astar)にも共通します。離散・組合せ最適化全体の選び分けは[離散・組合せ最適化の選び分け](#/learn/family.discrete-structure)を参照してください。
