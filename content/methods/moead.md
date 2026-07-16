---
content_id: moead
kind: method
method_id: M_MOEA_D
title_ja: MOEA/D
title_en: Multi-Objective Evolutionary Algorithm Based on Decomposition
summary: 多目的問題を異なるweightやreference方向を持つ多数の単目的subproblemへ分け、近いsubproblem同士で候補を共有する進化的手法です。
source_ids: [S039]
related_ids: [multi-objective, epsilon-constraint, nsga-iii]
status: published
last_reviewed: 2026-07-16
---

多目的問題を異なるweightやreference方向を持つ多数の単目的subproblemへ分け、近いsubproblem同士で候補を共有する進化的手法です。

## 30秒でつかむ

この手法の気持ちは、**Pareto front全体を一つの巨大なpopulation問題として扱うより、異なるtrade-offを担当する小さな仕事へ分け、近い担当同士で良い候補を交換したい**というものです。

- 見ているもの: scalarized value、reference方向、近傍subproblem、objective vector
- 動かしているもの: subproblemごとの候補と近傍population
- 前進の判断: 各方向のscalarized objectiveと全体coverageの改善
- 恐れていること: decompositionの偏り、objective scaling、近傍の同質化

分解に使うscalarizationが探索するfrontの形へ影響します。weightを均等に置けば解が均等に並ぶとは限りません。

## まず確認すること

| 項目 | 確認内容 |
|---|---|
| objectives | direction、scale、rangeが定義されているか |
| decomposition | weighted sum、Tchebycheffなど何を使うか |
| reference directions | 関心領域と必要な解数に合うか |
| neighborhood | どのsubproblem間で情報を共有するか |
| constraints | feasible solutionをどう優先するか |
| budget | subproblem数 × generationの評価数を許容できるか |

convex frontだけを前提にweighted sumを使うと、非凸frontの一部を取りにくい場合があります。

## 仕組み

各weight vector $w^j$に対してscalarized subproblemを作ります。

$$
\min_x g(x\mid w^j, z^*)
$$

$z^*$はideal pointなどのreferenceです。近いweight vectorをneighborとし、variationで作った候補がneighbor subproblemを改善すれば置き換えます。これにより局所的な情報共有とfront全体の分布を両立させます。

## 向く条件・避ける条件

向きやすい条件:

- 複数目的のblack-box問題
- trade-offを複数の方向へ分解して管理したい
- objective spaceに近傍関係を置ける
- population評価を並列化できる

避ける条件:

- 一評価が非常に高価で多数subproblemを維持できない
- objective scaleが未整理
- preferenceが一領域に集中しているのに全方向を探索する
- 厳密なPareto certificateが必要

## うまくいったサインと切替サイン

見る値:

- subproblemごとの改善率
- occupied reference direction数
- neighbor replacement数
- hypervolume / IGD / spacing
- ideal pointの更新
- feasible fraction
- seed間のfront差

切替サイン:

- 一部方向だけ改善 → scaling、decomposition、weight配置を見直す
- neighborが同じ解へ収束 → neighborhoodやvariationを広げる
- frontの重要領域が疎い → preference-based weightへ集中
- 目的数が多くweight数が爆発 → NSGA-IIIや別many-objective法を比較
- backend solverが強くthresholdに意味がある → ε-constraintへ

## Python例

```python
from pymoo.algorithms.moo.moead import MOEAD
from pymoo.optimize import minimize
from pymoo.problems import get_problem
from pymoo.util.ref_dirs import get_reference_directions

problem = get_problem("zdt1")
reference_directions = get_reference_directions("uniform", 2, n_partitions=40)
algorithm = MOEAD(
    ref_dirs=reference_directions,
    n_neighbors=10,
    prob_neighbor_mating=0.7,
)
result = minimize(problem, algorithm, ("n_gen", 100), seed=7, verbose=False)
print(result.F.shape)
```

比較ではdecomposition、weight、neighborhood、population相当数、seed、evaluation budgetを記録します。

## コラム: 分解は意思決定ではない

多数のscalarized subproblemを解いても、最終的にどの解を採用するかは別の意思決定です。均等なweightは利用者の選好を表すとは限りません。

[多目的最適化とPareto front](#/learn/multi-objective)を入口に、many-objectiveでreference方向を直接使う[NSGA-III](#/learn/nsga-iii)や、許容値を明示する[ε-constraint法](#/learn/epsilon-constraint)と比較してください。