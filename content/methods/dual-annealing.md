---
content_id: dual-annealing
kind: method
method_id: M_SIMULATED_ANNEALING
title_ja: Dual Annealing
title_en: Dual Annealing
summary: 温度付きの確率的jumpでbounded非凸空間を探索し、re-annealingと局所探索を組み合わせて複数basinから良い候補を探します。
source_ids: [S009, S018]
prerequisites: [concept.derivative-free]
related_ids: [shgo, direct-global, differential-evolution]
aliases: [/learn/dual-annealing]
status: published
last_reviewed: 2026-07-17
---

温度付きの確率的jumpでbounded非凸空間を探索し、re-annealingと局所探索を組み合わせて複数basinから良い候補を探します。

このページでは、canonicalな手法 `M_SIMULATED_ANNEALING` の一変種としてDual Annealingを扱います。Python例はSciPy実装 `I_SCIPY_DUAL_ANNEALING` に固有のAPIであり、simulated annealing一般の保証と実装のoptionを混同しないように読みます。

## Annealingの直感

高いtemperatureでは悪化するstepも一定確率で受け入れ、local basinから抜けます。temperatureを下げるにつれて探索を局所化します。

Dual Annealingはgeneralized simulated annealingのvisiting distributionとacceptance ruleを使い、必要に応じてlocal minimizerを組み合わせます。

## Python

```python
import numpy as np
from scipy.optimize import dual_annealing


def rastrigin(x: np.ndarray) -> float:
    return float(10.0 * len(x) + np.sum(x * x - 10.0 * np.cos(2.0 * np.pi * x)))


result = dual_annealing(
    rastrigin,
    bounds=[(-5.12, 5.12), (-5.12, 5.12)],
    maxfun=4_000,
    seed=7,
    no_local_search=False,
)

print(result.success, result.x, result.fun, result.nfev, result.message)
```

SciPy versionにより乱数引数やoption名が変わる可能性があるため、利用versionの公式documentationを確認します。

## Local searchの有無

`no_local_search=False`では、最終結果や評価回数にlocal minimizerが含まれます。

比較時は、

- annealing evaluation
- local-search evaluation
- local solverとtolerance
- local search開始条件

を分けます。local refinementを含むDual Annealingと、含まないpopulation法を同じiteration数で比較しません。

## Temperatureと分布

- initial temperature: 初期jump scale
- visit parameter: long-tail jumpの性質
- accept parameter: 悪化stepの受容
- restart temperature ratio: re-annealingのタイミング

parameterは相互作用し、problem scaleやboundsへ依存します。

## 診断値

- best-so-far objective
- current state objective
- accepted / rejected move数
- temperature
- re-annealing count
- function evaluation数
- local-search call数
- boundary hit率
- seed間の結果分散
- termination reason

current stateが悪化してもbest-so-farは保持します。確率的探索ではcurrentとincumbentを分けます。

## 向いている条件

- bounded continuous nonconvex problem
- multiple basins
- gradientを要求しない
- local solverとhybrid化したい
- moderate dimension
- stochastic explorationを許容

## 避ける／切り替える条件

- 1評価が極端に高価
- high dimension
- noiseでacceptanceが乱れる
- boundsが広すぎる
- general constraintが中心
- reproducibilityにseedを記録しない
- optimality certificateが必要

::: warning
annealing scheduleが終了したことは大域最適性の証明ではありません。複数seed、同じevaluation budget、local-search有無を揃えて候補品質を評価します。
:::
