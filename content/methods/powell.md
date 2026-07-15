---
content_id: powell
kind: method
method_id: M_POWELL
title_ja: Powell方向集合法
title_en: Powell Direction-Set Method
summary: 勾配を使わず複数の探索方向に沿う1次元最小化を繰り返し、改善した合成方向でdirection setを更新する局所法です。
source_ids: [S002, S018, S056]
prerequisites: [concept.derivative-free]
related_ids: [method.nelder-mead, pattern-search, mads]
aliases: [/learn/powell]
status: published
last_reviewed: 2026-07-15
---

勾配を使わず複数の探索方向に沿う1次元最小化を繰り返し、改善した合成方向でdirection setを更新する局所法です。

## 一巡の流れ

$n$次元で$n$本程度の方向 $d_1,\ldots,d_n$ を持ち、各方向について

$$
\min_\alpha f(x+\alpha d_i)
$$

というline minimizationを行います。一巡の始点と終点の差から新しい方向を作り、改善の小さい方向と交換します。

quadratic problemではconjugate directionsに近づく直感がありますが、一般非線形problemで有限回厳密解を保証するわけではありません。

## Python

```python
import numpy as np
from scipy.optimize import minimize


def objective(x: np.ndarray) -> float:
    return float((1.0 - x[0]) ** 2 + 30.0 * (x[1] - x[0] ** 2) ** 2)


result = minimize(
    objective,
    x0=np.array([-1.2, 1.0]),
    method="Powell",
    bounds=[(-3.0, 3.0), (-2.0, 4.0)],
    options={"xtol": 1e-8, "ftol": 1e-10, "maxfev": 5_000},
)

print(result.success, result.x, result.fun, result.nfev, result.message)
```

SciPy実装のbounds、初期方向、line search、停止条件はversionの公式documentationで確認します。

## Direction setとscaling

初期方向が座標軸だけの場合、変数scaleが大きく違うとline search rangeと改善量が偏ります。

- 変数を無次元化
- domainに合う初期direction
- boundsとfeasible interval
- line minimizerのtolerance

を確認します。方向がほぼ線形従属になると探索geometryが劣化します。

## 診断値

- function evaluation数
- cycle数
- directionごとの改善量
- line-search evaluation数
- direction matrixのcondition
- step norm
- objective / best-so-far
- bounds hit率
- termination reason

iteration数だけでは各iteration内のline evaluation数が分かりません。

## 向いている条件

- 低〜中次元のcontinuous black-box
- objectiveが比較的滑らかだがgradientを得られない
- 1次元line searchが有効
- boundsを持つ局所改善
- Nelder–Mead以外のgeometryを試したい

## 避ける／切り替える条件

- 高次元で各cycleの評価数が大きい
- noiseでline minimizationが不安定
- discontinuityや評価失敗が多い
- general constraintをboundsだけで代用
- global optimumやcertificateが必要
- direction setが退化し改善が止まる

::: warning
Powell法はgradient-freeですが、function evaluation budgetを多く使う場合があります。Nelder–Mead、Pattern Search、MADSと同じ初期点・bounds・evaluation budgetで比較します。
:::
