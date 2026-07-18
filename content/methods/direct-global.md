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
last_reviewed: 2026-07-18
---

bounded boxをhyperrectangleへ分割し、局所性定数を事前固定せずpotentially optimalな領域を選んで細分化する決定的大域探索法です。

## 30秒でつかむ

DIRECTは、良いcenter valueを持つ領域と、まだ大きく残る領域を同じ候補として扱い、bounded boxを決定的に細分化します。

- 見ているもの: best-so-far objective、rectangleの大きさ、potentially optimal set
- 動かしているもの: search box、rectangleのpartition、center evaluation
- 前進の判断: 未探索scaleを残しながら、良いcenter付近のrefinementが進むこと
- 恐れていること: 高次元化によるrectangle数の急増、悪いbounds、noisy objective

## 領域をどう選ぶか

DIRECTはDIviding RECTanglesの名前どおり、search boxをrectangleへ分割します。各rectangleのcenterで目的関数を評価し、

- center valueが良い
- rectangleが大きく未探索性が高い

というtrade-offからpotentially optimalなrectangleを選びます。

Lipschitz optimizationの考え方を使いますが、Lipschitz constantを一つに固定せず、複数の可能なslopeに対して有望な領域を残します。

## Globalとlocalのbalance

- large rectangleを残す: unexplored regionを探す
- good center付近を細分化: exploitation
- locally biased variant: local refinementを強める

searchが進むとrectangle数が増え、評価済みcenterとpartition管理の両方が必要です。

## まず確認すること

- boundsが探索したい領域を表しているか
- 問題がbounded low-dimensional black-boxで、objectiveがdeterministicか
- broad explorationとlocal refinementのどちらを重く見るか
- evaluation budgetがrectangleの分割とcenter evaluationを許容するか

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

## 失敗・切替の兆候

- rectangle数やpotentially optimal set sizeだけが増え、best-so-farが改善しない → dimensionとevaluation budgetを確認する
- boundary evaluation率が高い → boundsの意味とscalingを確認する
- center valueの比較が不安定 → noisy objectiveとして別methodを検討する
- general constraintやunbounded problemが中心 → 制約付き手法または別のglobal searchへ切り替える

::: warning
DIRECTは決定的でも、有限budgetで任意のnonconvex black-boxの大域最適性を証明するとは限りません。停止時のbest candidateと未探索scaleを報告します。
:::

## 次に読む

[SHGO](#/learn/shgo)、[Dual Annealing](#/learn/dual-annealing)、[Differential Evolution](#/learn/differential-evolution)と、bounds・再現性・evaluation budgetの違いを比較します。
