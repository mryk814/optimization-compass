---
content_id: direct-global
kind: method
method_id: M_DIRECT
title_ja: DIRECT
title_en: DIRECT
summary: bounded boxをhyperrectangleへ分割し、局所性定数を事前固定せずpotentially optimalな領域を選んで細分化する決定的大域探索法です。
source_ids: [S008, S018, S073]
prerequisites: [concept.derivative-free]
related_ids: [shgo, dual-annealing, differential-evolution]
aliases: [/learn/direct]
status: published
last_reviewed: 2026-07-15
---

bounded boxをhyperrectangleへ分割し、局所性定数を事前固定せずpotentially optimalな領域を選んで細分化する決定的大域探索法です。

## 領域をどう選ぶか

DIRECTはDIviding RECTanglesの名前どおり、search boxをrectangleへ分割します。各rectangleのcenterで目的関数を評価し、

- center valueが良い
- rectangleが大きく未探索性が高い

というtrade-offからpotentially optimalなrectangleを選びます。

Lipschitz optimizationの考え方を使いますが、Lipschitz constantを一つに固定せず、複数の可能なslopeに対して有望な領域を残します。

## Python

```python
import numpy as np
from scipy.optimize import direct


def objective(x: np.ndarray) -> float:
    return float(
        np.sin(4.0 * x[0])
        + np.cos(3.0 * x[1])
        + 0.08 * (x[0] ** 2 + x[1] ** 2)
    )


result = direct(
    objective,
    bounds=[(-3.0, 3.0), (-3.0, 3.0)],
    maxfun=3_000,
    locally_biased=False,
    f_min_rtol=1e-6,
)

print(result.success, result.x, result.fun, result.nfev, result.message)
```

`locally_biased`、volume / length tolerance、known `f_min` optionはSciPy versionの公式documentationで確認します。

## Globalとlocalのbalance

- large rectangleを残す: unexplored regionを探す
- good center付近を細分化: exploitation
- locally biased variant: local refinementを強める

searchが進むとrectangle数が増え、評価済みcenterとpartition管理の両方が必要です。

## Scaling

各変数を内部的にunit intervalへ写す考え方が基本ですが、boundsの意味が不適切なら探索も不適切です。

- boundsが広すぎる
- optimumがboundary外
- log scaleが必要
- categorical変数を連続化
- unit変換で重要領域を圧縮

を確認します。

## 診断値

- best-so-far objective
- function evaluation数
- rectangle count
- potentially optimal set size
- rectangle diameter / volume
- local vs global refinement割合
- boundary evaluation率
- termination reason
- dimension

## 向いている条件

- bounded low-dimensional black-box
- deterministic objective
- gradientがない
- broad explorationとlocal refinementの両方が必要
- random seedに依存しないbaselineが欲しい
- evaluation budgetが中程度

## 避ける／切り替える条件

- 高次元でrectangle数が急増
- noisy objectiveでcenter valueの比較が不安定
- 1評価が極端に高価
- unbounded problem
- general constraintが中心
- boundsが恣意的
- exact global certificateの前提を満たさない

::: warning
DIRECTは決定的でも、有限budgetで任意のnonconvex black-boxの大域最適性を証明するとは限りません。停止時のbest candidateと未探索scaleを報告します。
:::
