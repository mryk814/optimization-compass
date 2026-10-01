---
content_id: local-search-combinatorial
kind: method
method_id: M_LOCAL_SEARCH_COMBINATORIAL
title_ja: 組合せlocal search
title_en: Combinatorial Local Search
summary: 離散的な近傍moveを定義し、改善が見つかる間は可行解を更新するheuristicです。大域最適性は保証しません。
source_ids: [S054, S023]
prerequisites: []
related_ids: [simulated-annealing, genetic-algorithm, family.discrete-structure]
visualization_ids: [time-window-routing-feasible, time-window-routing-violation]
comparison_ids: [COMPARE_TIME_WINDOW_ROUTING_HARD_CONSTRAINT]
status: published
last_reviewed: 2026-09-30
---

離散的な近傍moveを定義し、改善が見つかる間は可行解を更新するheuristicです。大域最適性は保証しません。

## 30秒でつかむ

訪問順の一部分だけを入れ替え、短くなった順番を採るように解を磨きます。

- 見るもの: 近傍候補の費用と可行性
- 動かすもの: 訪問順や割当
- 前進の判断: 可行性を保つ改善が見つかること

## 一手の意味

可行な近傍候補の中から、現在解より目的が小さいものを採ります。

$$
x_{k+1}\in\arg\min_{z\in N(x_k)\cap\mathcal F} f(z)
$$

改善候補がなければ、その近傍に関する局所最適として止まります。

### 近傍をどう定義するか

組合せlocal searchは、現在の解に小さな変更（move）を加えて得られる解の集合を近傍として定義します。
その中から目的値を改善するmoveを見つけては適用します。
代表的な近傍は次のとおりです。

- swap: 2つの要素の割り当てや順序を入れ替える
- 2-opt: 経路の一部を反転させ、交差する2辺を組み替える
- insertion: 1つの要素を別の位置へ移動する

近傍の定義そのものが、この手法の性能を決める設計要素です。
近傍が狭すぎると改善の機会を見逃し、広すぎると1回の反復で近傍全体を評価する費用が増えます。
同じ問題でも、近傍の取り方次第で到達する解の質と探索速度が大きく変わります。

上段は、地点番号を`0 → 2 → 4 → 6 → 1 → 3 → 5 → 7`の順で結んだ初期経路です。
下段は、2-optでsegment反転を4回受理した後の経路です。

![固定した8地点の巡回routeをbest-improvement 2-optで改善した実行結果。上段の初期routeは5か所でedgeが交差し、距離は29.07。segment反転を4回受理すると、下段では地点0から7までを周囲に沿って巡回し、交差は0、距離は16.88になる。最後は2-opt近傍内に改善moveがなく停止する。](./media/local-search-two-opt-execution.svg "固定8地点のrouteで、交差のある初期解から2-opt近傍内の局所最適へ進む実行結果")

2-optは、経路から辺を2本選んで間の順序を反転します。
この固定例では、交差がほどけるたびに距離も短くなります。
最後は2-opt近傍内に改善moveがなくなりますが、大域最適性を証明したわけではありません。

> 固定したEuclidean 8地点のbest-improvement教材です。
> 距離は`29.07 → 16.88`、交差は`5 → 0`、受理moveは4回です。
> time window、vehicle capacity、trafficは含みません。
> 別初期経路や別近傍、routing ソルバー一般の性能も示していません。

### 局所最適で止まる性質と脱出戦略

組合せlocal searchは、定義した近傍に現在解より良い解がなくなった時点で停止します。
この状態を局所最適と呼びますが、大域最適である保証はありません。
近傍の外側により良い解が存在しても、local searchの手続き自体は見つけられません。

この性質を踏まえ、実務では次のような脱出戦略が使われます。

- 再始動: 異なる初期解から複数回local searchを実行し、最良の結果を採用する
- simulated annealingの考え方: 改善しないmoveも一定の確率で受理し、局所最適に留まりにくくする
- tabuの考え方: 直近で訪れた解やmoveを一時的に禁止し、同じ局所最適へ戻ることを防ぐ

これらは局所最適から抜け出しやすくする工夫です。
大域最適性の証明を与えるものではありません。
近傍設計と脱出戦略の組み合わせ全体が、解の質と探索費用のtrade-offを決めます。

## 小さな例

Python節と同じ8地点、初期順 $(0,2,4,6,1,3,5,7)$ を使います。
各反復では、評価した2-opt近傍の中で最も短い候補を一つ採ります。
次の表は、コードの履歴から得た最初の3回です。

| 受理回数 | 反転した位置 $(start,stop)$ | 距離 |
|---|---|---:|
| 0 | 初期状態 | 29.0714 |
| 1 | $(3,6)$ | 25.2057 |
| 2 | $(2,5)$ | 23.1214 |
| 3 | $(1,2)$ | 19.9429 |

4回目で距離16.8824になり、その後は改善がありません。

近傍に改善がなくなることと、大域最適性の証明は異なります。

## 向く条件・避ける条件

### 向いている条件

- 巨大なrouting・スケジューリングで、証明より早い良質な可行解が重要
- 近傍を問題の構造に合わせて設計でき、1回の近傍評価が軽い
- 厳密解法（MILPなど）では規模的に現実的な時間で解けない
- 複数の初期解や再始動を試す計算余力がある

### 避ける／切り替える条件

大域最適性の証明や最適性ギャップの保証が必須なら、組合せlocal searchだけでは不十分です。
MILPやCP-SATのような厳密法は、実行時間がかかっても最適性の界を提供できます。
一方、組合せlocal searchは到達した解が最適からどれだけ離れているかを示せません。
厳密な保証が必要な場合は、[離散・組合せ最適化の選び分け](#/learn/family.discrete-structure)にある他の手法を検討します。
追加制約が複雑で、近傍設計自体が難しい場合も同様です。

## Python

```python
from math import hypot


points = (
    (0.0, 0.0), (2.0, 0.3), (4.2, 0.0), (4.5, 2.0),
    (4.0, 4.2), (2.1, 4.5), (-0.2, 4.0), (-0.5, 2.0),
)


def tour_length(tour: tuple[int, ...]) -> float:
    return sum(
        hypot(
            points[tour[(index + 1) % len(tour)]][0] - points[tour[index]][0],
            points[tour[(index + 1) % len(tour)]][1] - points[tour[index]][1],
        )
        for index in range(len(tour))
    )


def two_opt_step(
    tour: tuple[int, ...],
) -> tuple[tuple[int, ...], float, tuple[int, int] | None]:
    best_tour = tour
    best_length = tour_length(tour)
    best_move = None
    for start in range(1, len(tour) - 1):
        for stop in range(start + 1, len(tour)):
            candidate = (
                tour[:start]
                + tuple(reversed(tour[start : stop + 1]))
                + tour[stop + 1 :]
            )
            candidate_length = tour_length(candidate)
            if candidate_length < best_length - 1e-12:
                best_tour = candidate
                best_length = candidate_length
                best_move = (start, stop)
    return best_tour, best_length, best_move


tour = (0, 2, 4, 6, 1, 3, 5, 7)
history = [(tour, tour_length(tour), None)]
while True:
    tour, length, move = two_opt_step(tour)
    if move is None:
        break
    history.append((tour, length, move))

print(history[0])
print(history[-1])
```

初期距離は`29.071...`です。
4回のsegment反転後は、経路が`(0, 1, 2, 3, 4, 5, 6, 7)`になります。
距離は`16.882...`です。

このコードは、小さなTSP instanceで2-opt近傍を総当たりする教育用実装です。
改善がなくなるまでbest-improvementを反復します。
実務のrouting／スケジューリング問題は、より複雑な近傍や制約を扱います。
[OR-Tools Routing](https://developers.google.com/optimization/routing)のようなmetaheuristic 枠組みを使う場合は、利用versionの公式referenceを確認します。

## 診断値

改善の有無だけでなく、近傍の広さと探索の停滞を記録します。

- states（現在の解と近傍候補が表す状態）
- edges（tourやscheduleが持つ辺・順序関係の数）
- labels（改善move・受理moveの記録）
- メモリ（近傍候補の生成と評価に使うメモリ量）
- optimality condition（近傍内に改善moveが残っていないかどうか）

## 失敗・切替の兆候

- 早期に局所最適へ収束し、再始動やtabuを使っても改善が見られない
- 近傍1回あたりの評価費用が問題規模に対して大きくなりすぎている
- 到達した解の質を保証する界が得られず、運用上の説明ができない
- 追加制約が増え、近傍moveのたびに可行性を保つ処理が複雑化している

### 時間窓を`hard constraint`として読む

[可行経路のTrace](#/traces/time-window-routing-feasible)と[時間窓違反のTrace](#/traces/time-window-routing-violation)は、同じ固定経路を使います。
変えるのは一つの時間窓だけです。
[時間窓の比較](#/compare/COMPARE_TIME_WINDOW_ROUTING_HARD_CONSTRAINT)では、同じ総移動時間でも到着が時間窓を超えれば実行不可能になることを確認します。

これはOR-Tools／local search／交通予測／経路品質の性能比較ではありません。
時間窓違反を小さな目的値差やpenaltyへ混ぜず、可行性を確認してから解の質を評価するためのcontrastです。

## 次に読む

近傍の外側を確率的に探索する考え方は[Simulated Annealing](#/learn/simulated-annealing)で確認できます。
集団で複数解を並行して探索する場合は[遺伝的algorithm](#/learn/genetic-algorithm)へ進みます。
全体の選び分けは[離散・組合せ最適化の選び分け](#/learn/family.discrete-structure)を参照してください。

- 問題の形を確認する: [車両経路問題](#/formulations/PA031)
