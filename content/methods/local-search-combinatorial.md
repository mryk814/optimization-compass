---
content_id: local-search-combinatorial
kind: method
method_id: M_LOCAL_SEARCH_COMBINATORIAL
title_ja: 組合せlocal search
title_en: Combinatorial Local Search
summary: swapや2-optなど離散的な近傍moveを定義し、改善が見つかる限りそれを繰り返して可行解を改善するheuristicです。
source_ids: [S054, S023]
prerequisites: []
related_ids: [simulated-annealing, genetic-algorithm, family.discrete-structure]
status: published
last_reviewed: 2026-07-16
---

swapや2-optなど離散的な近傍moveを定義し、改善が見つかる限りそれを繰り返して可行解を改善するheuristicです。

## 近傍をどう定義するか

組合せlocal searchは、現在の解に小さな変更（move）を加えて得られる解の集合を近傍として定義し、その中から目的値を改善するmoveを見つけては適用する、という操作を繰り返します。代表的な近傍は次のとおりです。

- swap: 2つの要素の割り当てや順序を入れ替える
- 2-opt: 経路の一部を反転させ、交差する2辺を組み替える
- insertion: 1つの要素を別の位置へ移動する

近傍の定義そのものが、この手法の性能を決める中心的な設計要素です。近傍が狭すぎると改善の機会を見逃し、広すぎると1回の反復で近傍全体を評価するcostが増えます。同じ問題でも、近傍の取り方次第で到達する解の質と探索速度が大きく変わります。

## 局所最適で止まる性質と脱出戦略

組合せlocal searchは、定義した近傍の中に現在の解より良い解が存在しなくなった時点で停止します。この状態を局所最適と呼びますが、それが大域最適である保証はありません。近傍の外側により良い解が存在していても、local searchの手続き自体はそれを見つけられません。

この性質を踏まえ、実務では次のような脱出戦略が使われます。

- restart: 異なる初期解から複数回local searchを実行し、最良の結果を採用する
- simulated annealingの考え方: 改善しないmoveも一定の確率で受理し、局所最適に留まりにくくする
- tabuの考え方: 直近で訪れた解やmoveを一時的に禁止し、同じ局所最適へ戻ることを防ぐ

これらは局所最適から抜け出す確率を高める工夫であり、大域最適性の証明を与えるものではありません。近傍設計と脱出戦略の組み合わせ全体が、解の質と探索costのtrade-offを決めます。

## 向いている条件

- 巨大なrouting・schedulingで、証明より早い良質な可行解が重要
- 近傍を問題の構造に合わせて設計でき、1回の近傍評価が軽い
- 厳密解法（MILPなど）では規模的に現実的な時間で解けない
- 複数の初期解やrestartを試す計算余力がある

## 避ける／切り替える条件

大域最適性の証明やoptimality gapの保証が必須の場面では、組合せlocal searchだけでは不十分です。MILPやCP-SATのような厳密法は、たとえ実行時間がかかっても最適性のboundを提供できますが、組合せlocal searchは到達した解が最適からどれだけ離れているかを示せません。厳密な保証が必要な場合や、side constraintsが複雑で近傍設計自体が難しい場合は、[離散・組合せ最適化の選び分け](#/learn/family.discrete-structure)にある他の手法を検討します。

## Python

```python
import numpy as np


def tour_length(tour: np.ndarray, points: np.ndarray) -> float:
    ordered = points[tour]
    diffs = ordered - np.roll(ordered, -1, axis=0)
    return float(np.sqrt((diffs**2).sum(axis=1)).sum())


def two_opt_step(tour: np.ndarray, points: np.ndarray) -> tuple[np.ndarray, bool]:
    n = len(tour)
    best_tour = tour
    best_length = tour_length(tour, points)
    improved = False

    for i in range(n - 1):
        for j in range(i + 1, n):
            candidate = tour.copy()
            candidate[i : j + 1] = candidate[i : j + 1][::-1]
            candidate_length = tour_length(candidate, points)
            if candidate_length < best_length:
                best_tour = candidate
                best_length = candidate_length
                improved = True

    return best_tour, improved


rng = np.random.default_rng(0)
points = rng.uniform(size=(8, 2))
tour = np.arange(len(points))

improved = True
while improved:
    tour, improved = two_opt_step(tour, points)

print(tour, tour_length(tour, points))
```

このコードは、小さなTSP instanceに対して2-optの近傍を総当たりで調べ、改善がなくなるまで反復する教育用の実装です。実務でのrouting/scheduling問題は、より複雑な近傍や制約を扱うため、[OR-Tools Routing](https://developers.google.com/optimization/routing)のようなmetaheuristicフレームワークを使い、利用versionに対応する公式referenceを確認します。

## 診断値

- states（現在の解と近傍候補が表す状態）
- edges（tourやscheduleが持つ辺・順序関係の数）
- labels（改善move・受理moveの記録）
- memory（近傍候補の生成と評価に使うmemory量）
- optimality condition（近傍内に改善moveが残っていないかどうか）

## 失敗・切替の兆候

- 早期に局所最適へ収束し、restartやtabuを使っても改善が見られない
- 近傍1回あたりの評価costが問題規模に対して大きくなりすぎている
- 到達した解の質を保証するboundが得られず、運用上の説明ができない
- side constraintsが増え、近傍moveのたびに可行性を保つ処理が複雑化している

近傍の外側を確率的に探索する考え方は[Simulated Annealing](#/learn/simulated-annealing)、集団で複数解を並行して探索する考え方は[遺伝的algorithm](#/learn/genetic-algorithm)で確認できます。離散・組合せ最適化全体の選び分けは[離散・組合せ最適化の選び分け](#/learn/family.discrete-structure)を参照してください。
