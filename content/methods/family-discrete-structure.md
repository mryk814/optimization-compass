---
content_id: family.discrete-structure
kind: method
method_id: MF_DISCRETE_EXACT
title_ja: 離散・組合せ最適化の選び分け
title_en: Choosing a Discrete Optimization Strategy
summary: 離散変数を含む問題で、graph・動的計画法・CP-SAT・MILP・local searchを構造と必要な保証から選び分ける入口です。
source_ids: [S005, S016, S021, S022, S023, S054, S079]
related_ids: [dynamic-programming, dijkstra-astar, cp-sat, branch-and-bound, branch-and-cut]
visualization_ids: [binary-knapsack-bnb-complete, binary-knapsack-bnb-budget]
comparison_ids: [COMPARE_KNAPSACK_BNB_BUDGET]
status: published
last_reviewed: 2026-07-24
---

離散変数を含む問題で、graph・動的計画法・CP-SAT・MILP・local searchを構造と必要な保証から選び分ける入口です。

## 30秒でつかむ

このfamilyの中心は、**候補を全部列挙せず、調べる必要のない組合せを構造で減らすこと**です。
問題固有の構造・制約伝播・緩和bound・近傍moveを使います。

- 見ているもの: state、edge、domain、constraint propagation、incumbent、bound、gap
- 動かすもの: path、state、partial assignment、探索木、近傍解
- 前進の判断: 可行解の発見、bound改善、domain縮小、未探索領域の削減
- 主な弱点: state explosion、弱いrelaxation、symmetry、巨大Big-M、弱いpropagation

離散問題を見たら、最初からMILPやmetaheuristicへ進まず、graph・flow・matching・DPなどの専用構造を先に確認します。

## まず確認すること

| 確認項目 | 選択への影響 |
|---|---|
| 専用構造 | shortest path、flow、matching、interval schedulingとして解けるか |
| state分解 | Bellman recursionや段階構造を作れるか |
| 制約表現 | 線形係数中心か、論理・resource・global constraint中心か |
| 連続変数 | 離散と連続が混在するか |
| 必要な保証 | 良い可行解、gap、最適性証明、UNSAT証明のどれか |
| 時間制限 | proofまで待つか、incumbentを早く得るか |
| problem scale | 変数数だけでなくdomain、constraint graph、relaxation強度 |

整数化や時間離散化では、scaleが現実の精度を保つか確認します。係数を大きくするだけでは精度問題は解決しません。

## 条件付きの選び分け

| 役割 | 手法 | 優先しやすい条件 | 切り替えを考える条件 |
|---|---|---|---|
| graph専用法 | [Dijkstra / A*](#/learn/dijkstra-astar) | shortest path、非負edge、admissible heuristic | side constraintが増え専用構造が崩れる |
| 段階的再利用 | [Dynamic Programming](#/learn/dynamic-programming) | optimal substructure、stateを小さく定義可能 | state次元・memoryが爆発する |
| 論理・scheduling | [CP-SAT](#/learn/cp-sat) | finite domain、reification、resource、時間窓 | domainが巨大、整数scaleが不自然、伝播が弱い |
| 線形modelとgap | [Branch-and-Cut](#/learn/branch-and-cut) | binary/integer、強いLP relaxation、証明が必要 | root gapが大、Big-M・symmetryでtreeが爆発 |
| 探索原理の理解 | [Branch-and-Bound](#/learn/branch-and-bound) | incumbent・bound・gapの意味を確認したい | 実solver機能を単純treeと同一視してしまう |
| 早い良質可行解 | Combinatorial Local Search | 巨大routing/scheduling、proofより運用解 | feasibility維持が難しい、解品質のboundが必要 |
| 混合非線形と証明 | Outer / Spatial Branch-and-Bound | 対応するconvex relaxationを構築可能 | relaxationが弱い、black-box・noiseがある |

「CP-SAT対MILP」の万能な勝敗はありません。constraint表現とrelaxation / propagationの強さがinstanceごとに変わります。

## Caseから構造を見分ける

同じ離散変数でも、何を表すかによって最初に試すfamilyが変わります。

| Case | 中心になる構造 | 最初の問い |
|---|---|---|
| [限られた予算を施策へ配分する](#/gallery/budget-allocation) | binary選択・線形予算上限 | incumbentに加えてgapや証明が必要か |
| [スタッフのシフトを組む](#/gallery/shift-scheduling) | finite domain・resource・公平性 | 論理制約を直接表せるか |
| [時間窓付き配送ルートを10分以内に組む](#/gallery/EC019) | routing・時間窓・time limit | proofより早い良質可行解を優先するか |

これは手法の順位表ではありません。
変数domain、制約表現、必要な成果物を具体的な問題から確かめる入口です。

## 探索木でboundと停止を読む

[証明完了の探索木](#/theater/search-tree/binary-knapsack-bnb-complete)では、incumbentとglobal boundが一致するまでを追います。
[4 nodeで止まる探索木](#/theater/search-tree/binary-knapsack-bnb-budget)では、実行可能解があってもgapと未探索nodeが残る状態を確認します。

[停止条件を並べるCompare](#/compare/COMPARE_KNAPSACK_BNB_BUDGET)は、同じ4変数knapsackでnode stop limitだけを変えます。
この教材instanceは、上の実務Caseそのものではありません。
CP-SAT／MILP／routing手法の一般性能rankingにも使いません。

## うまくいったサインと切替サイン

追うべき値:

- incumbent objective
- best boundとoptimality gap
- node / branch / conflict / propagation数
- root relaxation gap
- feasible solutionの発見時刻
- presolve reduction
- domain reduction
- memoryと未処理node数

切替サイン:

- 専用graph構造が見つかる → 汎用modelから専用法へ戻す
- state数が指数的に増える → DP state圧縮、別定式化、MILP/CPへ
- CPでdomainが縮まらない → 制約表現、symmetry、MILP relaxationを検討
- MILP root gapが大きい → formulation、valid inequality、CP/専用法を検討
- 可行解が長時間出ない → heuristic、warm start、constraint debugging
- gapは小さいがproofが遅い → 許容gapと運用要件を確認

## 小さな選択ブリーフ

解法を指定する前に、構造と必要な成果物を記録します。

```python
problem_brief = {
    "variable_types": ["binary", "integer"],
    "special_structure": ["time_windows", "resource_capacity"],
    "continuous_relaxation_expected": "unknown",
    "required_output": "feasible-solution-with-gap",
    "time_limit_seconds": 300,
    "candidate_families": ["CP-SAT", "MILP", "routing-local-search"],
}

assert problem_brief["time_limit_seconds"] > 0
```

## コラム: 変数数だけでは難しさは分からない

同じ1万binary変数でも、問題構造によって難しさは異なります。
network matrix、強い伝播を持つscheduling、弱いBig-Mのmodelを同列に扱いません。

離散最適化では、変数数だけでなくdomain sizeとconstraint graphも記録します。
symmetry／relaxation gap／可行解密度／decomposition可能性も確認します。
solverを替える前にmodel formulationを見直す価値が大きい領域です。

## 次に読む

論理・resource制約が中心なら[CP-SAT](#/learn/cp-sat)を確認します。
線形modelとgapが重要なら[Branch-and-Cut](#/learn/branch-and-cut)へ進みます。
専用構造があるなら[Dynamic Programming](#/learn/dynamic-programming)と[Dijkstra / A*](#/learn/dijkstra-astar)を確認します。
