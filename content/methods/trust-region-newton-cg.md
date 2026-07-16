---
content_id: trust-region-newton-cg
kind: method
method_id: M_TRUST_NCG
title_ja: Trust-region Newton-CG
title_en: Trust-region Newton-CG
summary: 局所二次モデルを信頼半径の内側だけで使い、CGでNewton方向を近似する大域化された二階法です。
source_ids: [S002, S056]
prerequisites: [newton-method]
related_ids: [newton-method, bfgs, least-squares]
aliases: [/learn/trust-region-newton-cg]
status: published
last_reviewed: 2026-07-16
---

局所二次モデルを信頼半径の内側だけで使い、CGでNewton方向を近似する大域化された二階法です。

## Trust regionの考え方

Newton stepを無条件に採用せず、現在点の周囲

$$
\|p\| \le \Delta_k
$$

で二次modelを最小化します。$\Delta_k$ は「このmodelをどこまで信用するか」を表す半径です。

試行stepの後、実際の改善とmodelが予測した改善の比

$$
\rho_k = \frac{f(x_k)-f(x_k+p_k)}{m_k(0)-m_k(p_k)}
$$

を見ます。予測がよく当たればstepを採用して半径を広げ、外れれば棄却して半径を縮めます。

## Newton-CGで何を省いているか

Hessianを完全にfactorizeする代わりに、conjugate gradientでtrust-region部分問題を近似します。必要なのはHessian-vector積 $\nabla^2 f(x)v$ で、巨大なHessian行列を明示しなくても動かせます。

向いている条件:

- 連続・滑らかな問題
- 勾配とHessian-vector積が利用可能
- dense Hessianを保存できない
- line search Newtonが不安定
- negative curvatureも検出しながら進みたい

## 診断値

- gradient norm
- trust radius $\Delta_k$
- actual / predicted reduction ratio $\rho_k$
- accepted / rejected step数
- inner CG iteration数
- negative-curvatureまたはboundary termination
- function / gradient / HVP evaluation数

半径が縮み続ける場合、微分が誤っている、modelが不連続を跨いでいる、scaleが悪い、または目的関数評価にnoiseがある可能性があります。

## Python

```python
import numpy as np
from scipy.optimize import minimize


def objective(x: np.ndarray) -> float:
    return float((1.0 - x[0]) ** 2 + 20.0 * (x[1] - x[0] ** 2) ** 2)


def gradient(x: np.ndarray) -> np.ndarray:
    return np.array([
        2.0 * (x[0] - 1.0) - 80.0 * x[0] * (x[1] - x[0] ** 2),
        40.0 * (x[1] - x[0] ** 2),
    ])


def hessian_product(x: np.ndarray, vector: np.ndarray) -> np.ndarray:
    hessian = np.array([
        [2.0 - 80.0 * x[1] + 240.0 * x[0] ** 2, -80.0 * x[0]],
        [-80.0 * x[0], 40.0],
    ])
    return hessian @ vector


result = minimize(
    objective,
    x0=np.array([-1.2, 1.0]),
    jac=gradient,
    hessp=hessian_product,
    method="trust-ncg",
    options={"gtol": 1e-8, "maxiter": 300},
)

print(result.success, result.x, result.fun, result.message)
```

::: note
反復回数だけでBFGSと比較しません。HVP、gradient、目的関数の各評価費を分け、同じ停止条件と初期点で比較します。
:::

## 避ける／切り替える条件

- 目的関数が不連続または強いnoiseを含む
- gradient / HVPを信頼できない
- 1回のHVPが目的評価より極端に高価
- 単純なboundsだけでL-BFGS-Bが十分
- 一般制約が中心で、制約付きtrust-region実装を用意していない
