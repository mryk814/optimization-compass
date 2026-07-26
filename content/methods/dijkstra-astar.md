---
content_id: dijkstra-astar
kind: method
method_id: M_DIJKSTRA_ASTAR
title_ja: Dijkstra法とA*探索
title_en: Dijkstra's Algorithm and A* Search
summary: 非負の重みを持つgraphで、確定済み距離やadmissible heuristicを使って最短路を厳密に求める探索法です。
source_ids: [S054]
prerequisites: [dynamic-programming]
related_ids: [dynamic-programming, cp-sat]
aliases: [/learn/dijkstra-astar]
status: published
last_reviewed: 2026-07-26
---

非負の重みを持つgraphで、確定済み距離やadmissible heuristicを使って最短路を厳密に求める探索法です。

## まず確認すること

- edge weightは非負か
- コスト（cost）の単位は揃い、path上で加算できるか
- nodeとedgeは、問題の状態と遷移を表しているか
- `side constraint`は`path state`へ含まれているか

## 選ぶnodeのpriorityが違う

Dijkstra法は、始点からの暫定距離$g(n)$が最小のnodeを取り出します。
そのnodeから伸びるedgeをrelaxし、goalへ届くまで確定領域を広げます。
`edge cost`が非負なら、priority queueから確定した距離は後から改善されません。

A*探索は、現在までのcostとgoalまでの残りcostの推定を足したpriorityでnodeを選びます。

$$
f(n)=g(n)+h(n)
$$

- $g(n)$: 始点から現在nodeまでに支払ったcost
- $h(n)$: 現在nodeからgoalまでに必要な残りcostの推定

$h(n)=0$ならDijkstra法と同じpriorityです。
$h$が真の残りcostを過大評価しないadmissible heuristicなら、A*も最適性を維持できます。
consistent heuristicなら、確定済みnodeの再展開を抑えやすくなります。

## 同じ最短costへ、違う範囲を探す

次の固定gridでは、どちらもcost 24の最短路を返します。
違うのは、goalへ着くまでに展開したcellの範囲です。

![17列11行の固定gridをDijkstra法とManhattan heuristic付きA*探索で解いた実行結果。上段のDijkstra法は始点から全方向へ広がり168 cellを展開する。下段のA*はgoal方向へ探索を絞り92 cellを展開する。障害物を避ける経路は異なるが、どちらの最短path costも24である。](./media/dijkstra-astar-grid-execution.svg "固定したunit-cost 4近傍gridのpure Python実行です。A*の展開数はDijkstra法より45%少なくなりますが、別graph、重み、tie-break、heuristic一般の削減率や実行時間は示しません。")

淡い橙が展開済みcell、青緑が返された最短路です。
A*は168 cellから92 cellへ展開範囲を減らしました。
これは、このgridとManhattan heuristicで得た固定結果です。

> 両者の最短costは同じ24です。
> 経路そのものは複数あるため、返されたpathの形が同じである必要はありません。
> 展開数の45%削減は一般性能rankingではありません。

## Python

```python
import heapq

WIDTH, HEIGHT = 17, 11
START = (1, 5)
GOAL = (15, 5)
OBSTACLES = (
    {(6, y) for y in range(1, 10) if y != 2}
    | {(11, y) for y in range(1, 10) if y != 8}
)


def shortest_path(
    *,
    use_heuristic: bool,
) -> tuple[int, tuple[tuple[int, int], ...], tuple[tuple[int, int], ...]]:
    def heuristic(node: tuple[int, int]) -> int:
        if not use_heuristic:
            return 0
        return abs(GOAL[0] - node[0]) + abs(GOAL[1] - node[1])

    distance = {START: 0}
    predecessor = {}
    queue = [(heuristic(START), heuristic(START), START)]
    closed = set()
    expanded = []

    while queue:
        _, _, node = heapq.heappop(queue)
        if node in closed:
            continue
        closed.add(node)
        expanded.append(node)
        if node == GOAL:
            break

        for dx, dy in ((1, 0), (0, 1), (-1, 0), (0, -1)):
            neighbor = (node[0] + dx, node[1] + dy)
            inside = 0 <= neighbor[0] < WIDTH and 0 <= neighbor[1] < HEIGHT
            if not inside or neighbor in OBSTACLES:
                continue
            candidate = distance[node] + 1
            if candidate >= distance.get(neighbor, WIDTH * HEIGHT + 1):
                continue
            distance[neighbor] = candidate
            predecessor[neighbor] = node
            priority = candidate + heuristic(neighbor)
            heapq.heappush(queue, (priority, heuristic(neighbor), neighbor))

    path = [GOAL]
    while path[-1] != START:
        path.append(predecessor[path[-1]])
    path.reverse()
    return distance[GOAL], tuple(path), tuple(expanded)


for name, use_heuristic in (("Dijkstra", False), ("A*", True)):
    cost, path, expanded = shortest_path(use_heuristic=use_heuristic)
    print(f"{name}: cost={cost}, expanded={len(expanded)}, path nodes={len(path)}")
```

```text
Dijkstra: cost=24, expanded=168, path nodes=25
A*: cost=24, expanded=92, path nodes=25
```

`use_heuristic=False`がDijkstra法、`True`がManhattan heuristic付きA*です。
図と出力は、この同じ条件とtie-breakで生成しています。

## 汎用最適化より先に確認する理由

単純なshortest pathはMIPへ変換しても解けます。
専用algorithmはgraph構造を直接利用するため、保証と診断値を対応づけやすくなります。

ただし、次の`side constraint`が増えると専用構造が崩れる場合があります。

- 複数resource capacity
- time window
- path全体に依存する論理条件
- pickup and delivery
- 複数車両の相互作用
- negative edgeやcycle condition

この場合は、`state`拡張DPやresource-constrained shortest pathを検討します。
CP-SATやMIPも候補です。

## 診断値

- expanded node数
- relaxed edge数
- priority queue size
- reopened node数（A*）
- heuristic error / consistency
- memory
- `goal cost`とlower bound

::: warning
地図上の直線距離は常に安全なheuristicとは限りません。
discountやteleport edgeで実costが地理距離より小さくなる場合は、admissibilityを確認します。
:::

## 失敗・切替の兆候

- state explosionでmemoryが増大
- heuristicが弱くDijkstraと同程度に展開
- heuristicが過大で最適解を失う
- `side constraint`を`node state`へ入れ忘れる
- negative edgeをDijkstraで処理する
- `path cost`が加法的でないのに単純`edge sum`へ落とす

## 次に読む

- `state`を拡張して履歴を扱う: [動的計画法](#/learn/dynamic-programming)
- 論理制約やschedulingを含む: [CP-SAT](#/learn/cp-sat)
