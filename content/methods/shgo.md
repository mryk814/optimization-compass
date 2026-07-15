---
content_id: shgo
kind: method
method_id: M_SHGO
title_ja: SHGO
title_en: Simplicial Homology Global Optimization
summary: bounded search spaceをsimplicial complexでsampleし、topological情報からlocal-minimum候補を抽出して局所solverへ渡す大域探索法です。
source_ids: [S007, S018, S072]
prerequisites: [concept.derivative-free]
related_ids: [direct-global, dual-annealing, differential-evolution]
aliases: [/learn/shgo]
status: published
last_reviewed: 2026-07-15
---

bounded search spaceをsimplicial complexでsampleし、topological情報からlocal-minimum候補を抽出して局所solverへ渡す大域探索法です。

## 探索の考え方

SHGOは領域内のsample点とその近傍関係からsimplicial complexを構成し、目的関数の離散的なtopologyを使って有望なlocal-minimum basinを識別します。候補点からlocal optimizationを行い、複数の局所解を集めます。

random restartだけでなく、search space全体の構造をsampleから推定する点が特徴です。

## Python

```python
import numpy as np
from scipy.optimize import shgo


def objective(x: np.ndarray) -> float:
    return float(
        np.sin(3.0 * x[0]) * np.cos(2.0 * x[1])
        + 0.05 * (x[0] ** 2 + x[1] ** 2)
    )


result = shgo(
    objective,
    bounds=[(-3.0, 3.0), (-3.0, 3.0)],
    n=128,
    iters=3,
    sampling_method="simplicial",
)

print(result.success, result.x, result.fun, result.nfev, result.message)
print(getattr(result, "xl", None), getattr(result, "funl", None))
```

返却されるlocal minima一覧やoptionはSciPy versionの公式documentationで確認します。

## Sampling budget

性能は、

- sample数
- iteration数
- sampling method
- local solver
- constraint評価
- dimension

に依存します。低次元では領域構造を捉えやすい一方、dimension増加でsimplicial samplingの費用が急増します。

## Constraint

SHGO実装はconstraint付きproblemを扱えますが、

- feasible regionが細い
- disconnected
- constraint evaluationが高価
- equality toleranceが厳しい

場合、sampleからfeasible候補を得にくいことがあります。feasible fractionを記録します。

## 診断値

- global best / local minima一覧
- sample count
- local optimization count
- objective / constraint evaluation数
- unique minima数
- feasible sample fraction
- basinごとの初期点
- termination message
- dimension / bounds volume

local minima数が増え続ける場合、sample densityが不足しているか、noiseで偽のbasinが生じている可能性があります。

## 向いている条件

- bounded low-dimensional problem
- multimodalなcontinuous objective
- 複数local minimaを列挙したい
- gradientがなくてもlocal solverを組み合わせられる
- deterministicに近いstructured samplingを使いたい

## 避ける／切り替える条件

- 高次元
- 1評価が極端に高価
- strong noise / discontinuity
- boundsが広すぎる
- feasible regionが極端に細い
- global certificateの前提を確認していない
- local solver costをbudgetに含めない

::: warning
SHGOの理論的性質はsampling、continuity、problem class等の前提に依存します。実装の`success`だけで任意black-boxの大域最適性を断定しません。
:::
