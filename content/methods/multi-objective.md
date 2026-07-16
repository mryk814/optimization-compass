---
content_id: multi-objective
kind: method
method_id: M_NSGA_II
title_ja: 多目的最適化とPareto front
title_en: Multi-objective Optimization and the Pareto Front
summary: 複数目的を根拠なく一つのscoreへ潰さず、domination・Pareto集合・preferenceを分けてtrade-off候補を作る最適化です。
source_ids: [S039, S055, S068]
prerequisites: []
related_ids: [concept.convexity, cma-es, constrained-continuous]
visualization_ids: [biobjective-quadratic-pareto-front]
comparison_ids: []
aliases: [/learn/multi-objective]
visualization_aliases: [biobjective-quadratic-pareto-front|/theater/multi-objective]
comparison_aliases: []
status: published
last_reviewed: 2026-07-16
---

複数目的を根拠なく一つのscoreへ潰さず、domination・Pareto集合・preferenceを分けてtrade-off候補を作る最適化です。

## 単一のbestがない理由

minimizationで解 $x_a$ が $x_b$ をdominateするとは、

- すべての目的で $f_i(x_a)\le f_i(x_b)$
- 少なくとも一つでstrictに良い

ことです。どの他解にもdominateされない解がPareto optimalです。

一方を改善すると他方が悪化する場合、数学だけでは最終選択を一意に決められません。preference、risk、policy、実務制約が必要です。

## Decision spaceとobjective space

- decision space: 実際に選ぶ設計変数 $x$
- objective space: $(f_1(x),f_2(x),\ldots)$

objective spaceで近い二点でも、decision spaceでは全く異なる設計かもしれません。可視化では両空間の選択をlinkedさせると理解しやすくなります。

## 代表的な解き方

- weighted sum
- ε-constraint
- goal programming
- achievement scalarizing function
- NSGA-IIなどpopulation-based MOEA
- multi-objective Bayesian Optimization

weighted sumは簡単ですが、非凸なPareto frontの一部を取得できない場合があります。preferenceが明確なら、広いfront全体を生成せず必要領域だけ解く方が効率的です。

## Python: non-dominated pointsを抽出する

```python
import numpy as np


def objectives(x: np.ndarray) -> np.ndarray:
    first = x**2
    second = (x - 2.0) ** 2
    return np.column_stack((first, second))


def nondominated_mask(values: np.ndarray) -> np.ndarray:
    keep = np.ones(len(values), dtype=bool)
    for index, value in enumerate(values):
        dominated = np.all(values <= value, axis=1) & np.any(values < value, axis=1)
        if np.any(dominated):
            keep[index] = False
    return keep


candidates = np.linspace(-1.0, 3.0, 401)
values = objectives(candidates)
mask = nondominated_mask(values)
pareto_decisions = candidates[mask]
pareto_values = values[mask]
print(pareto_decisions[[0, -1]], pareto_values[[0, -1]])
```

これは候補gridから非劣点を抽出する教育例です。連続問題の厳密frontを証明するalgorithmではありません。

## NSGA-IIの状態

NSGA-IIは、

- non-dominated sorting
- crowding distance
- selection
- crossover / mutation
- population更新

で近似frontを作ります。population densityは探索の分布であり、最適性certificateではありません。

記録するparameter:

- population size
- generation / evaluation budget
- crossover / mutation
- constraint handling
- seed
- initialization
- duplicate elimination

## Normalizationとreference

costが数千、riskが0.01のようにscaleが違うと、plotやweighted sumが一方に支配されます。

- objective direction
- physical unit
- normalization range
- ideal point
- nadir / reference point
- hypervolume reference

を明示します。ideal pointは各目的を別々に最適化した値で、同時に実現できる解とは限りません。

## 診断値

- feasible / infeasible population
- non-dominated solution数
- hypervolumeとreference point
- generational distance系
- spacing / diversity
- duplicate solution数
- evaluation budget
- seed間のfront variation
- selected solutionのdecision variables

## 向いている条件

- 本当に競合する複数目的がある
- preferenceを事前に完全固定できない
- 候補集合を意思決定者へ提示したい
- black-boxやnonconvexでscalar solverだけではfrontを取りにくい
- 複数設計のrobustnessを比較したい

## 避ける／切り替える条件

- 単位換算可能な同一価値を別目的として重複計上
- hard constraintをobjectiveへ弱く入れてinfeasible候補を残す
- preferenceが明確なのに巨大frontを無目的に生成
- objective directionを混同
- weighted sum一回だけで「Pareto最適化済み」とする
- 2D plotの左下だけ見てdecision variablesを確認しない
- stochastic algorithmの単一seedだけをfrontとして固定

[Pareto Theater](#/theater/multi-objective)ではdominated / non-dominated、preference変更、selected solution、ideal / nadir referenceを区別します。

::: warning
Pareto frontは意思決定を代替しません。trade-offを可視化し、選択に必要なpreferenceと制約を明らかにするための成果物です。
:::
