---
content_id: family.graph-dp
kind: method
method_id: MF_GRAPH_DP
title_ja: Graph専用法・動的計画法の選び分け
title_en: Choosing a Graph Algorithm or Dynamic Programming
summary: 問題が既知のgraph・DP構造に一致するかを確認し、一致するなら汎用最適化より先に専用法を検討するための入口です。
source_ids: [S054]
related_ids: [dynamic-programming, dijkstra-astar, hungarian-algorithm, network-simplex, local-search-combinatorial]
status: published
last_reviewed: 2026-07-16
---

問題が既知のgraph・DP構造に一致するかを確認し、一致するなら汎用最適化より先に専用法を検討するための入口です。

## 30秒でつかむ

このfamilyの気持ちは、**問題がshortest path、flow、matching、段階的なDP構造のいずれかに一致するなら、汎用の最適化solverへ持ち込む前に、その構造を直接利用する専用法をまず確認すること**です。

- 見ているもの: node、edge、state、段階、optimal substructureの有無
- 動かすもの: path、flow、matching、DPのstate遷移
- 前進の判断: 距離やcostの確定、flowの改善、stateの縮約、部分問題の再利用
- 主な弱点: 構造が崩れると適用不能、state空間の爆発

これは一般性能rankingではありません。専用法が使える構造を持つ問題では、汎用最適化より高速かつ強い保証が得られる場合が多いという役割の違いを示します。

## まず確認すること

| 確認項目 | 選択への影響 |
|---|---|
| 最適部分構造の有無 | 部分問題の最適解を組み合わせて全体の最適解が作れるか |
| 状態空間の大きさ | DPのstateが現実的なmemoryに収まるか |
| side constraintsの有無 | 構造を壊す追加制約（複数resource、time window、論理条件など）がないか |
| graph表現への対応 | 問題をnode/edgeやflow networkとして素直に表現できるか |
| 必要な保証 | 厳密解・多項式時間の保証が必要か、早い可行解でよいか |

これらを確認した結果、構造が崩れている、またはstate空間が巨大すぎると分かった場合は、MILP・CP-SATなど汎用の離散最適化へ進みます。判断の入口は[離散・組合せ最適化の選び分け](#/learn/family.discrete-structure)にまとめています。

## 条件付きの選び分け

| 役割 | 手法 | 優先しやすい条件 | 切り替えを考える条件 |
|---|---|---|---|
| 段階的な部分問題の再利用 | [動的計画法](#/learn/dynamic-programming) | optimal substructureがあり、stateを小さく定義できる | state数・memoryが爆発する |
| 最短路の専用探索 | [Dijkstra / A*](#/learn/dijkstra-astar) | shortest path、非負edge、admissible heuristicが使える | side constraintsが増え専用構造が崩れる |
| 二部matchingの専用解法 | [Hungarian Algorithm](#/learn/hungarian-algorithm) | 割当問題が二部完全matchingとして表現できる | side constraintsで完全matchingの前提が崩れる |
| flow networkの専用simplex | [Network Simplex法](#/learn/network-simplex) | 最小費用流のnetwork構造（node-arc接続行列）を保っている | side constraintsで専用構造が崩れる |
| 早い良質可行解が必要な大規模問題 | [組合せlocal search](#/learn/local-search-combinatorial) | 巨大routing/scheduling、証明より運用解を優先 | 大域最適性の証明やgapの保証が必須になる |

同じ問題規模でも、構造を保ったまま解けるか、side constraintsで崩れているかによって適した手法は変わります。

## うまくいったサインと切替サイン

うまく専用構造を利用できているときは、次のような値が安定して観測できます。

- states・edges・labelsの数が問題規模に対して現実的な範囲に収まっている
- memory使用量が想定内で推移している
- optimality condition（最短路の確定、flowの被約費用条件、matchingの完全性など）が満たされている

切替サイン:

- state数やnode/edge数が指数的またはmemory上限を超えて増大する
- side constraintsが増え、専用構造（network、二部matching、Bellman再帰）の前提が崩れる
- 厳密な保証よりも早い可行解が優先される状況に変わる、またはその逆
- 専用法の実装や近傍設計が問題の複雑さに対して過度に手間がかかる

## 小さな比較の型

専用法を選ぶ前に、問題の構造と必要な成果物を記録します。

```python
problem_brief = {
    "graph_structure": ["shortest_path", "min_cost_flow", "bipartite_matching"],
    "optimal_substructure": True,
    "state_dimension_estimate": "small",
    "side_constraints_present": False,
    "required_output": "exact-optimal-with-guarantee",
    "candidate_methods": [
        "dynamic-programming",
        "dijkstra-astar",
        "network-simplex",
    ],
}

assert problem_brief["state_dimension_estimate"] in {"small", "moderate", "large"}
```

## コラム: 専用法と汎用最適化は競合しない

Graph専用法やDPは、問題が持つ構造をそのまま利用するため、同じ問題を汎用のLP/MILPへ変換して解くよりも高速で、保証も明確になりやすい手法です。しかし、これは専用法が汎用最適化より常に優れているという意味ではありません。専用法は、想定した構造（network、二部matching、Bellman再帰など）から外れた瞬間に前提が崩れ、適用できなくなります。

実務では、まず問題の構造を確認し、専用法が使える範囲を見極めたうえで、side constraintsが加わった部分だけを汎用solverで扱う、という組み合わせもよく使われます。構造を壊さない範囲で専用法を使い、壊れた部分だけ汎用化するという判断が、この family全体の軸になります。

## 次に読む

構造が崩れてMILP・CP-SATなど汎用の離散最適化を検討する場合は[離散・組合せ最適化の選び分け](#/learn/family.discrete-structure)へ進みます。
