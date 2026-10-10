# 同一性と粒度の対応ルール

収録範囲（[`editorial-scope.md`](editorial-scope.md)）の種別と、データベースの既存の語彙との対応を決めます。新しい項目を足すときや、まとめ行を分けたくなったときに、ここで「どの表の、どの段に置くか」と「何を変えてはいけないか」を確かめます。

この文書はschemaを変えません。新しい段（たとえば `method_level = strategy`）が必要に見えたら、AGENTS.md の stop and escalate に従って設計レビューに回します。

## 種別と既存の語彙

データベースの `methods.method_level` は `family`（`MF_*`）と `variant`（`M_*`）の二段だけです。収録範囲の種別は、次のように写します。

| 収録範囲の種別 | 置き場所 | 例 | 置かない場所 |
|---|---|---|---|
| family（手法群） | `methods`、`method_level = family`、`MF_*` | `MF_SMOOTH_LOCAL` | — |
| algorithm（手順として解ける手法） | `methods`、`method_level = variant`、`M_*`。親とは `method_hierarchy` の `is_a` で結ぶ | `M_BFGS` is_a `MF_SMOOTH_LOCAL` | `glossary` だけに置かない |
| variant（名前のある変種） | まず親の行の `aliases` と `terminology_aliases`。行を持たせるときは `M_*` を足し、`method_hierarchy` の `variant_of` で親と結ぶ | Nesterov momentum → `M_MOMENTUM_SGD` の別名 | 親の行の意味を変えて流用しない |
| strategy（分解・緩和・スカラー化など） | 手順として実行できるもの（動的計画、多点開始、重み付き和）は algorithm と同じく `M_*`。手順でなく考え方であるもの（Lagrange 緩和）は `glossary` と記事の節 | `M_WEIGHTED_SUM`、`G059` | 新しい `method_level` を作らない |
| primitive（部品） | `glossary` と、それを使う手法の記事の節。手法の行は作らない | Armijo 条件 → 直線探索の用語 `G051`、BFGS・NLCG の記事 | `methods` に置かない |
| implementation（ライブラリの実装） | `implementations` と `method_implementation_map` | SciPy の `minimize(method="BFGS")` | `methods` に置かない（method と implementation は別。AGENTS.md） |
| problem_archetype（問題型） | `problem_archetypes`、`PA*` と `formulation_atlas.json` | `PA017` 線形計画 | — |
| modeling_profile（評価や情報の性質） | `problem_features`、`F_*` と概念記事 | `F_EVALUATION_COST` と `concept.evaluation-cost` | 問題型の行にしない |
| neighboring_problem（隣接問題） | 前処理群の `PA*`（`domain_group = precheck`）か概念記事 | 求根 → `PA004` | — |

実行できる基準問題（`problem_definitions`、`PROBLEM_*`）は問題型とは別の表です。一つの基準問題が複数の問題型に結ばれてよく、収録範囲では `problem_definition` 型の参照として扱います。

## まとめ行の扱い

既存には、二つの名前を一つの行にまとめたものがあります。

| 行 | まとめている名前 | URL |
|---|---|---|
| `M_DIJKSTRA_ASTAR` | Dijkstra、A* | `/methods/M_DIJKSTRA_ASTAR`、`/learn/dijkstra-astar` |
| `M_TURBO_SAASBO` | TuRBO、SAASBO | `/methods/M_TURBO_SAASBO`、`/learn/turbo-saasbo` |
| `M_HYPERBAND_ASHA` | Hyperband、ASHA | `/methods/M_HYPERBAND_ASHA`、`/learn/hyperband-asha` |
| `M_ILQR_DDP` | iLQR、DDP | `/methods/M_ILQR_DDP`、`/learn/ilqr-ddp` |
| `PA019` | 非凸QP、非凸QCQP | `/formulations/PA019` |
| `PA027` | SAT、MaxSAT | `/formulations/PA027` |
| `PA032` | ナップサック、集合被覆 | `/formulations/PA032` |
| `PA047` | ゲーム、均衡、変分不等式 | `/formulations/PA047` |

方針は次のとおりです。

1. **今は分けません。** 収録範囲では、まとめられた名前をどちらも `variant_of` にして、同じ行を二重に数えません。
2. **分けるときも、旧IDの意味は変えません。** まとめ行のIDは「二つをまとめた行」のまま残し、片方の名前へ意味を移しません。分けた側には新しいIDを足し、`method_hierarchy` の `variant_of` でまとめ行と結びます。
3. **既存URLは残します。** `/methods/<まとめ行のID>` と記事の `/learn/...` は、分けた後もまとめ行のページとして開けるようにします。分けた行には新しいURLを足します。
4. 分けるのは、二つの名前で前提・失敗・推薦が変わり、それを記事と比較で示せるときだけです。名前が有名だという理由では分けません。

## 多対多の対応

一つの名前が複数の行にまたがるときは、収録範囲の `refs` に複数の参照を並べ、`note_ja` にどの面がどの行にあたるかを書きます。一つに決め打ちしません。

- Nesterov 加速：先読みのモメンタムは `M_MOMENTUM_SGD`、加速の外挿は `M_FISTA`
- 低ランク因子分解：因子を同時に決める形は `PA033`、SVD の閉形式は `PA003`
- 滑らかな無制約NLP：次元と勾配の有無で `PA006` と `PA007`

## 変更ごとの移行例

| 変更 | やること | 例 |
|---|---|---|
| 別名を足す | 親の行の `aliases` と `terminology_aliases` に足す（dataset の変更。リリース手順に従う）。収録範囲は `alias_of` のまま | 「Nesterov momentum」を `M_MOMENTUM_SGD` の別名に（既にある） |
| 変種に行を持たせる | `M_*` を新しく足し、`method_hierarchy` に `variant_of` で親を書く。親の記事の該当節から新しい記事へリンク。収録範囲は `variant_of` → `same_entity` に直す | AdaGrad を `M_ADAGRAD`（仮）として `MF_STOCHASTIC_ML` の下へ。ID は追加時の設計レビューで決める |
| 部品を説明する | `glossary` に用語を足し、使う手法の記事に節を足す。手法の行は作らない。収録範囲は `primitive_in` | Armijo 条件は直線探索の用語 `G051` と BFGS の記事 |
| まとめ行を分ける | 上の「まとめ行の扱い」の2〜3に従う。収録範囲は分けた側を `same_entity`、まとめ行を指していた方は `variant_of` のまま | `M_DIJKSTRA_ASTAR` から A* を分ける場合、`M_DIJKSTRA_ASTAR` の意味とURLは残す |
| 表現なしを埋める | 種別に合う置き場所へ通常の追加手順で足す（[`adding-knowledge.md`](adding-knowledge.md)）。収録範囲は `unrepresented` → 対応する関係に直す | Sinkhorn を足すときは、まず輸送の問題型と手法の置き場所を決める |

どの移行でも、計画用ID（`TOPIC_*` / `STRUCTURE_*`）をデータベースのIDにしません。
