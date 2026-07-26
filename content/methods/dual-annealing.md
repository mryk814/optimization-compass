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
last_reviewed: 2026-07-26
---

温度付きの確率的jumpでbounded非凸空間を探索し、re-annealingと局所探索を組み合わせて複数basinから良い候補を探します。

Dual Annealingは、canonicalな手法`M_SIMULATED_ANNEALING`の一変種です。
Python例はSciPy実装`I_SCIPY_DUAL_ANNEALING`に固有のAPIです。
simulated annealing一般の保証と、実装固有のoptionを分けて読みます。

## Annealingの直感

高いtemperatureでは悪化するstepも一定確率で受け入れ、local basinから抜けます。
temperatureを下げるにつれて探索を局所化します。

Dual Annealingはgeneralized simulated annealingのvisiting distributionとacceptance ruleを使います。
必要に応じてlocal minimizerも組み合わせます。

まず、基礎になるSimulated Annealingの受理機構を固定実行で見ます。
橙の`current`は悪化しても、青緑の`best-so-far`は手放しません。

![1次元Rastrigin関数を初期点3.5から固定seedで400反復探索したSimulated Annealingの実行結果。上段は受理した状態が複数のbasinを横断する様子を示す。下段では橙の現在値が何度も上昇する一方、青緑の最良値は32.25から0.00076へ単調に改善する。受理65回のうち32回は悪化移動で、最初の100反復に18回、最後の100反復には1回だけ現れる。](./media/simulated-annealing-execution.svg "固定1次元Rastrigin、seed 7、初期温度5.0、幾何冷却0.985のpure Python実行です。Dual Annealing固有のvisiting distributionとlocal searchは含みません。別seed、高次元、別schedule、手法一般の性能や大域最適性も示しません。")

このrunでは、受理した65 moveのうち32 moveが悪化でした。
最初の100反復では18回、最後の100反復では1回だけです。
温度低下に伴う「探索から絞り込みへ」の移行が見えます。

> この図はclassicな受理機構を切り出した1次元教材です。
> SciPyの`dual_annealing`実行結果ではなく、visiting distributionとlocal searchも含みません。
> Dual Annealingの結果を比較するときは、以下の追加要因を分けて記録します。

## Local searchの有無

`no_local_search=False`では、最終結果や評価回数にlocal minimizerが含まれます。

比較時は、

- annealing evaluation
- local-search evaluation
- `local solver`とtolerance
- local search開始条件

を分けます。local refinementを含むDual Annealingと、含まないpopulation法を同じiteration数で比較しません。

## Temperatureと分布

- initial temperature: 初期jump scale
- visit parameter: long-tail jumpの性質
- accept parameter: 悪化stepの受容
- restart temperature ratio: re-annealingのタイミング

各`parameter`は相互作用し、problem scaleやboundsへ依存します。

## 向いている条件

- bounded continuous nonconvex problem
- multiple basins
- `gradient`を要求しない
- `local solver`とhybrid化したい
- moderate dimension
- stochastic explorationを許容

## 避ける／切り替える条件

- 1評価が極端に高価
- high dimension
- noiseでacceptanceが乱れる
- boundsが広すぎる
- `general constraint`が中心
- reproducibilityにseedを記録しない
- optimality certificateが必要

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

`current state`が悪化してもbest-so-farは保持します。
確率的探索ではcurrentとincumbentを分けます。

::: warning
annealing scheduleが終了したことは大域最適性の証明ではありません。複数seed、同じevaluation budget、local-search有無を揃えて候補品質を評価します。
:::
