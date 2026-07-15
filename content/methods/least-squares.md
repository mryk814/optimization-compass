---
content_id: least-squares
kind: method
method_id: M_LEVENBERG_MARQUARDT
title_ja: 非線形最小二乗とLevenberg–Marquardt法
title_en: Nonlinear Least Squares and Levenberg-Marquardt
summary: 観測値とmodel予測の残差を直接組み立て、その二乗和を局所的に減らす方法です。
source_ids: [S003, S041]
prerequisites: []
related_ids: [method.gradient-descent]
visualization_ids: []
comparison_ids: []
aliases: [/learn/least-squares]
visualization_aliases: []
comparison_aliases: []
status: published
last_reviewed: 2026-07-15
---

観測値とmodel予測の残差を直接組み立て、その二乗和を局所的に減らす方法です。

## 現実の問いを残差へ分ける

| 項目 | 例 |
|---|---|
| decision variables | 反応速度定数、材料model係数、camera pose |
| objective | 残差ベクトル $r(x)$ の二乗和 $\frac{1}{2}\lVert r(x)\rVert^2$ |
| constraints | parameter bounds、正値性、固定parameter |
| problem features | 残差構造、Jacobian、外れ値、識別可能性 |

現実の問いは「どのparameterなら複数の観測を一貫して説明できるか」です。総損失だけでなく、観測ごとの残差を残すとmodel mismatchを診断できます。

## Alternative-first check

線形最小二乗で書けるなら、反復的な非線形最適化より先にQRやSVDを検討します。root findingとして扱うべき等式系なら、目的関数化によって解釈が変わっていないか確認します。

- candidate: Levenberg–Marquardt / trust-region least squares。滑らかな残差とJacobianを利用できる場合。
- conditional: robust loss付きleast squares。外れ値modelを明示できる場合。
- excluded: Nelder–Mead。残差Jacobianを捨て、parameter数が増えると評価回数が膨らみやすい場合。

## Representative implementationと最小例

SciPy `least_squares`とCeres Solverが代表的です。scale、Jacobian、termination status、residual distributionを保存します。

```python
import numpy as np
from scipy.optimize import least_squares

x_data = np.array([0.0, 1.0, 2.0, 3.0])
y_data = np.array([1.1, 2.9, 5.2, 6.8])

def residuals(parameters: np.ndarray) -> np.ndarray:
    slope, intercept = parameters
    return slope * x_data + intercept - y_data

result = least_squares(residuals, x0=np.array([1.0, 0.0]))
print(result.x, result.cost, result.optimality)
```

## 実務上の注意

小さい二乗和はparameterが一意に決まった証拠ではありません。Jacobianのrank、parameter相関、残差pattern、初期値依存性を確認します。noise分散が観測ごとに異なる場合はweightの意味を記録し、無根拠に二乗誤差へ揃えません。
