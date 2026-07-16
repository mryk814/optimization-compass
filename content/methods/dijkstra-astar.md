---
content_id: dijkstra-astar
kind: method
method_id: M_DIJKSTRA_ASTAR
title_ja: Dijkstra法とA*探索
title_en: Dijkstra's Algorithm and A* Search
summary: graphの非負edge costを累積し、確定済み距離またはadmissible heuristicを使って最短路を厳密に探索します。
source_ids: [S054]
prerequisites: [dynamic-programming]
related_ids: [dynamic-programming, cp-sat]
aliases: [/learn/dijkstra-astar]
status: published
last_reviewed: 2026-07-16
---

graphの非負edge costを累積し、確定済み距離またはadmissible heuristicを使って最短路を厳密に探索します。

## Dijkstra法

始点からの暫定距離が最小のnodeを取り出し、そのnodeから伸びるedgeをrelaxします。edge costが非負なら、priority queueから確定した距離は後から改善されません。

確認する前提:

- edge weightが非負
- costの単位と加法性が妥当
- node / edgeが問題の状態と遷移を正しく表す
- side constraintがpath stateへ含まれている

## A*探索

A*はpriorityを

$$
f(n)=g(n)+h(n)
$$

とします。

- $g(n)$: 始点から現在nodeまでの実cost
- $h(n)$: goalまでの推定cost

$h$ が真の残りcostを過大評価しないadmissible heuristicなら最適性を維持できます。consistent heuristicなら再展開を抑えやすくなります。

## Python: Dijkstra法

```python
import heapq
from collections.abc import Mapping

Graph = Mapping[str, list[tuple[str, float]]]


def dijkstra(graph: Graph, start: str) -> dict[str, float]:
    distance = {node: float("inf") for node in graph}
    distance[start] = 0.0
    queue = [(0.0, start)]

    while queue:
        current_distance, node = heapq.heappop(queue)
        if current_distance != distance[node]:
            continue
        for neighbor, edge_cost in graph[node]:
            if edge_cost < 0:
                raise ValueError("Dijkstra requires non-negative edge costs")
            candidate = current_distance + edge_cost
            if candidate < distance[neighbor]:
                distance[neighbor] = candidate
                heapq.heappush(queue, (candidate, neighbor))

    return distance


graph = {
    "A": [("B", 2.0), ("C", 5.0)],
    "B": [("C", 1.0), ("D", 4.0)],
    "C": [("D", 1.0)],
    "D": [],
}
print(dijkstra(graph, "A"))
```

## 汎用最適化より先に確認する理由

単純なshortest pathをMIPへ変換しても解けますが、専用algorithmはgraph構造を直接利用し、通常は速く、保証も明確です。

ただし次のside constraintが増えると専用構造が崩れる場合があります。

- 複数resource capacity
- time window
- path全体に依存する論理条件
- pickup and delivery
- 複数車両の相互作用
- negative edgeやcycle condition

この場合、state拡張DP、resource-constrained shortest path、CP-SAT、MIPなどを検討します。

## 診断値

- expanded node数
- relaxed edge数
- priority queue size
- reopened node数（A*）
- heuristic error / consistency
- memory
- goal costとlower bound

::: warning
地図上の直線距離は常に安全なheuristicとは限りません。実costが地理距離より小さくなり得るdiscountやteleport edgeがある場合、admissibilityを確認します。
:::

## 失敗・切替の兆候

- state explosionでmemoryが増大
- heuristicが弱くDijkstraと同程度に展開
- heuristicが過大で最適解を失う
- side constraintをnode stateへ入れ忘れる
- negative edgeをDijkstraで処理する
- path costが加法的でないのに単純edge sumへ落とす
