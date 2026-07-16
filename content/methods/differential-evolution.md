---
content_id: differential-evolution
kind: method
method_id: M_DIFFERENTIAL_EVOLUTION
title_ja: Differential Evolution（差分進化）
title_en: Differential Evolution
summary: 個体間の差分vectorから候補を作り、crossoverとselectionでbounded連続空間を探索するpopulation法です。
source_ids: [S006, S074]
prerequisites: [concept.derivative-free]
related_ids: [cma-es, genetic-algorithm, particle-swarm]
aliases: [/learn/differential-evolution]
status: published
last_reviewed: 2026-07-16
---

個体間の差分vectorから候補を作り、crossoverとselectionでbounded連続空間を探索するpopulation法です。

## 一世代で何をするか

代表的なDE/rand/1では、target個体 $x_i$ と異なる3個体を選び、mutant

$$
v_i=x_{r1}+F(x_{r2}-x_{r3})
$$

を作ります。次にcrossoverでtrial個体 $u_i$ を作り、目的値が改善した方を次世代へ残します。

- $F$: 差分の拡大率
- $CR$: crossover率
- population size
- strategy: base vectorと差分数の選び方

が探索の性格を変えます。

## 向いている条件

- boundsを持つ連続black-box
- 勾配が利用できない、または不連続・多峰性
- 目的評価をpopulation単位で並列化できる
- 局所法の初期値依存を緩和したい
- 最適性証明ではなく良いglobal candidateが欲しい

評価が高価で数十回しか呼べない場合、populationを維持するだけでbudgetを使い切るため、Bayesian Optimizationなどとの比較が必要です。

## 比較で揃える条件

- search bounds
- population sizeと初期population
- random seed
- objective evaluation budget
- constraint handling
- polishing local searchの有無
- stopping / stall condition

iteration数ではなくobjective evaluation数を主なbudgetにします。

## Python

```python
import numpy as np
from scipy.optimize import differential_evolution


def rastrigin(x: np.ndarray) -> float:
    return float(10.0 * len(x) + np.sum(x * x - 10.0 * np.cos(2.0 * np.pi * x)))


result = differential_evolution(
    rastrigin,
    bounds=[(-5.12, 5.12), (-5.12, 5.12)],
    strategy="best1bin",
    popsize=12,
    maxiter=300,
    seed=7,
    polish=False,
    updating="deferred",
    workers=1,
)

print(result.success, result.x, result.fun, result.nfev)
```

## 診断値

- best-so-far objective
- population diversity
- feasible fraction
- bound付近への集中
- 世代あたり評価数
- seed間の結果分散
- stall generation数

::: warning
`polish=True`で最後に局所法を使う実装では、最終結果はDEだけの成果ではありません。population探索とlocal refinementの評価回数を分けて記録します。
:::

## 失敗・切替の兆候

- population diversityが早期に消える
- 全個体がboundsへ張り付く
- 評価budgetに対し世代数が少なすぎる
- penalty設計によりinfeasible個体しか生成されない
- 変数scaleが極端で差分vectorが一部座標だけ支配する
- 単一seedの成功例を一般性能として扱っている
