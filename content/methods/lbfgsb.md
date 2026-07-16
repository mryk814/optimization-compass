---
content_id: lbfgsb
kind: method
method_id: M_LBFGSB
title_ja: L-BFGS-B法
title_en: L-BFGS-B
summary: 少数の曲率更新だけを保存し、上下限制約を保ちながら大規模な滑らか最適化を行う準Newton法です。
source_ids: [S002, S056, S065]
prerequisites: [bfgs]
related_ids: [bfgs, newton-method, trust-region-newton-cg]
aliases: [/learn/lbfgsb]
status: published
last_reviewed: 2026-07-16
---

少数の曲率更新だけを保存し、上下限制約を保ちながら大規模な滑らか最適化を行う準Newton法です。

## BFGSとの違い

通常のBFGSはdenseな逆Hessian近似を保持するため、変数数 $n$ に対して概ね $O(n^2)$ のmemoryを使います。L-BFGSは直近 $m$ 回の $s_k$ と $y_k$ だけを保存し、行列を明示せずtwo-loop recursionで方向を計算します。

L-BFGS-Bはさらに各変数のbounds

$$
l_i \le x_i \le u_i
$$

をnativeに扱います。一般の等式・不等式制約を扱う手法ではありません。

## 向いている条件

- 数千〜数百万変数の滑らかな目的関数
- gradientまたはautomatic differentiationが利用できる
- 制約が主に単純な上下限
- dense Hessianを保存できない
- 局所解で十分、または凸性により局所解が大域解になる

boundsを付ければ物理的に意味のない値を防げますが、変数間の関係を表す一般制約の代わりにはなりません。

## 境界上の停止を読む

境界に張り付いた変数では、通常のgradient normだけを見ると「勾配が残っている」と見える場合があります。重要なのは、実行可能方向へ射影したgradientやKKT条件です。

確認する値:

- projected gradient norm
- active boundの数
- function / gradient evaluation数
- line-search status
- step norm
- memory parameter $m$

::: note
境界上で解が止まること自体は失敗ではありません。目的関数が境界の外側へ改善する方向を示していても、その方向が禁止されていれば境界点が最適になり得ます。
:::

## Python

```python
import numpy as np
from scipy.optimize import minimize


def objective(x: np.ndarray) -> float:
    return float((x[0] - 3.0) ** 2 + 4.0 * (x[1] + 1.0) ** 2)


def gradient(x: np.ndarray) -> np.ndarray:
    return np.array([2.0 * (x[0] - 3.0), 8.0 * (x[1] + 1.0)])


result = minimize(
    objective,
    x0=np.array([0.0, 0.0]),
    jac=gradient,
    method="L-BFGS-B",
    bounds=[(-2.0, 2.0), (-3.0, 3.0)],
    options={"ftol": 1e-12, "gtol": 1e-8, "maxiter": 300},
)

print(result.success, result.x, result.fun, result.message)
```

この例では無制約最適点の $x_0=3$ が上限2を超えるため、制約付き解は境界へ移ります。

## 避ける／切り替える条件

- nonlinear equalityやcoupled inequalityが重要 → SLSQP、interior-pointなど
- 目的関数が不連続・強いnoiseを含む → derivative-free法を検討
- gradientが誤っている → 先にgradient check
- line searchが何度も失敗 → scaling、非滑らかさ、NaN領域を確認
- boundsだけではmodelの実行可能性を表現できない → 制約付きmodelへ移行
