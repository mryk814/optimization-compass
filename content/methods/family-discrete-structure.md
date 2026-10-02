---
content_id: family.discrete-structure
kind: method
method_id: MF_DISCRETE_EXACT
title_ja: 離散・組合せ最適化の選び分け
title_en: Choosing a Discrete Optimization Strategy
summary: 離散変数を含む問題で、グラフ・動的計画法・CP-SAT・MILP・局所探索を構造と必要な保証から選び分ける入口です。
source_ids: [S005, S016, S021, S022, S023, S054, S079]
related_ids: [dynamic-programming, dijkstra-astar, cp-sat, branch-and-bound, branch-and-cut, concept.mixed-integer-linear-program]
visualization_ids: [binary-knapsack-bnb-complete, binary-knapsack-bnb-budget]
comparison_ids: [COMPARE_KNAPSACK_BNB_BUDGET]
status: published
last_reviewed: 2026-09-30
---

離散変数を含む問題で、グラフ・動的計画法・CP-SAT・MILP・局所探索を構造と必要な保証から選び分ける入口です。

## 30秒でつかむ

この手法群の中心は、**候補を全部列挙せず、調べる必要のない組合せを構造で減らすこと**です。
問題固有の構造・制約伝播・緩和界・近傍への移動操作を使います。

- 見ているもの: 状態、辺、候補範囲、制約伝播、暫定解、界、ギャップ
- 動かすもの: 経路、状態、部分割当、探索木、近傍解
- 前進の判断: 可行解の発見、界改善、候補範囲縮小、未探索領域の削減
- 主な弱点: 状態数の爆発、弱い緩和、対称性、巨大Big-M、弱い伝播

離散問題を見たら、最初からMILPやメタヒューリスティクスへ進まず、グラフ・フロー・マッチング・DPなどの専用構造を先に確認します。

## 探索木で構造を見る

![4変数0-1 ナップサックを9節点まで決定論的に探索したBranch-and-Bound木。部分割当ごとの値と界を使い、実行不能または改善不能な枝を除き、ギャップ 0で最適性を証明する。](./media/search-tree-proof-execution.svg "離散探索で候補を全列挙せずに減らす一例です。固定Branch-and-Bound教材であり、CP-SAT、MILP、局所探索の一般性能順位付けではありません。")

木の大きさより、各枝を残す理由と切る理由に注目します。専用グラフ法・制約伝播・緩和でも、「調べなくてよい候補を何で判定するか」が選択の軸です。

## まず確認すること

| 確認項目 | 選択への影響 |
|---|---|
| 専用構造 | 最短路、フロー、マッチング、区間スケジューリングとして解けるか |
| 状態分解 | Bellman再帰や段階構造を作れるか |
| 制約表現 | 線形係数中心か、論理・資源・大域制約中心か |
| 連続変数 | 離散と連続が混在するか |
| 必要な保証 | 良い可行解、ギャップ、最適性証明、UNSAT証明のどれか |
| 時間制限 | 証明まで待つか、暫定解を早く得るか |
| 問題の規模 | 変数数だけでなく候補範囲、制約グラフ、緩和強度 |

整数化や時間離散化では、尺度が現実の精度を保つか確認します。係数を大きくするだけでは精度問題は解決しません。

## 条件付きの選び分け

| 役割 | 手法 | 優先しやすい条件 | 切り替えを考える条件 |
|---|---|---|---|
| グラフ専用法 | [Dijkstra / A*](#/learn/dijkstra-astar) | 最短路、非負辺、過大評価しないヒューリスティクス | 追加の制約が増え専用構造が崩れる |
| 段階的再利用 | [Dynamic Programming](#/learn/dynamic-programming) | 最適部分構造、状態を小さく定義可能 | 状態次元・メモリが爆発する |
| 論理・スケジューリング | [CP-SAT](#/learn/cp-sat) | 有限の候補範囲、真偽値との対応付け、資源、時間窓 | 候補範囲が巨大、整数尺度が不自然、伝播が弱い |
| 線形モデルとギャップ | [Branch-and-Cut](#/learn/branch-and-cut) | 二値・整数、強いLP 緩和、証明が必要 | 探索木の根でのギャップが大、Big-M・対称性で探索木が爆発 |
| 探索原理の理解 | [Branch-and-Bound](#/learn/branch-and-bound) | 暫定解・界・ギャップの意味を確認したい | 実ソルバー機能を単純探索木と同一視してしまう |
| 早い良質可行解 | Combinatorial Local Search | 大規模な経路選択・スケジューリング、証明より運用解 | 実行可能性維持が難しい、解品質の界が必要 |
| 混合非線形と証明 | Outer / Spatial Branch-and-Bound | 対応する凸緩和を構築可能 | 緩和が弱い、ブラックボックス・ノイズがある |

「CP-SAT対MILP」の万能な勝敗はありません。制約表現と緩和 / 伝播の強さが問題例ごとに変わります。

## 事例から構造を見分ける

同じ離散変数でも、何を表すかによって最初に試す手法群が変わります。

| 事例 | 中心になる構造 | 最初の問い |
|---|---|---|
| [限られた予算を施策へ配分する](#/gallery/budget-allocation) | 二値選択・線形予算上限 | 暫定解に加えてギャップや証明が必要か |
| [スタッフのシフトを組む](#/gallery/shift-scheduling) | 有限の候補範囲・資源・公平性 | 論理制約を直接表せるか |
| [時間窓付き配送ルートを10分以内に組む](#/gallery/EC019) | 経路選択・時間窓・時間上限 | 証明より早い良質可行解を優先するか |

これは手法の順位表ではありません。
変数候補範囲、制約表現、必要な成果物を具体的な問題から確かめる入口です。

## 探索木で界と停止を読む

[証明完了の探索木](#/theater/search-tree/binary-knapsack-bnb-complete)では、暫定解と全体の界が一致するまでを追います。
[4節点で止まる探索木](#/theater/search-tree/binary-knapsack-bnb-budget)では、実行可能解があってもギャップと未探索の節点が残る状態を確認します。

[停止条件を並べる比較](#/compare/COMPARE_KNAPSACK_BNB_BUDGET)は、同じ4変数ナップサックで探索節点数の上限だけを変えます。
この教材問題例は、上の実務事例そのものではありません。
CP-SAT／MILP／経路選択手法の一般性能順位付けにも使いません。

## うまくいったサインと切替サイン

追うべき値:

- 暫定解目的値
- 最良界と最適性ギャップ
- 節点 / 分岐 / 矛盾 / 伝播数
- 根の緩和ギャップ
- 実行可能解の発見時刻
- 前処理による削減
- 候補範囲の削減
- メモリと未処理節点数

切替サイン:

- 専用グラフ構造が見つかる → 汎用モデルから専用法へ戻す
- 状態数が指数的に増える → DP 状態圧縮、別定式化、MILP/CPへ
- CPで候補範囲が縮まらない → 制約表現、対称性、MILP 緩和を検討
- MILP 探索木の根でのギャップが大きい → 定式化、有効不等式、CP/専用法を検討
- 可行解が長時間出ない → ヒューリスティクス、ウォームスタート、制約の誤りの調査
- ギャップは小さいが証明が遅い → 許容ギャップと運用要件を確認

## 小さな比較の型

実装や定式化を比べるときは、節点数や反復数だけを揃えません。
同じ問題例・時間制限・ギャップの許容値・求める成果物を揃え、何を記録するかを先に決めます。

### 比較の前に構造と成果物を記録する

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

### 比較の実験条件

上の記録をもとに、固定するものと変えるものを分けます。ここで変えるのは、モデルの表現だけです。

```python
experiment = {
    "problem_instance": "same-discrete-instance",
    "required_output": problem_brief["required_output"],
    "time_limit_seconds": problem_brief["time_limit_seconds"],
    "relative_gap_tolerance": 1e-4,
    "random_seed": 0,
    "compared": ["CP-SAT model", "MILP model"],
    "record": ["incumbent", "best_bound", "gap", "first_feasible_time", "termination_reason"],
}

assert experiment["time_limit_seconds"] > 0
assert experiment["required_output"] == problem_brief["required_output"]
```

これは手法の順位を決める型ではありません。
時間内に見つかった暫定解・最良の界・ギャップ・停止した理由を並べます。どの成果物がどの条件で得られたかを読みます。

## コラム: 変数数だけでは難しさは分からない

同じ1万二値変数でも、問題構造によって難しさは異なります。
ネットワーク行列、強い伝播を持つスケジューリング、弱いBig-Mのモデルを同列に扱いません。

離散最適化では、変数数だけでなく候補範囲の大きさと制約グラフも記録します。
対称性／緩和ギャップ／可行解密度／分解可能性も確認します。
ソルバーを替える前に、モデルの定式化を見直す価値が大きい領域です。

## 次に読む

論理・資源制約が中心なら[CP-SAT](#/learn/cp-sat)を確認します。
線形モデルとギャップが重要なら[Branch-and-Cut](#/learn/branch-and-cut)へ進みます。
専用構造があるなら[Dynamic Programming](#/learn/dynamic-programming)と[Dijkstra / A*](#/learn/dijkstra-astar)を確認します。

定式化から入るなら、[混合整数線形計画](#/learn/concept.mixed-integer-linear-program)・[最短路問題](#/formulations/PA029)・[ナップサック・集合被覆](#/formulations/PA032)のページで、標準形と見分け方を確かめられます。
