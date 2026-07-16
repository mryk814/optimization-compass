---
content_id: least-squares
kind: method
method_id: M_LEVENBERG_MARQUARDT
title_ja: 非線形最小二乗とLevenberg–Marquardt法
title_en: Nonlinear Least Squares and Levenberg-Marquardt
summary: 観測ごとの残差vectorとJacobian構造を保ち、二乗和・damping・trust-region診断を使ってparameterを局所推定する方法です。
source_ids: [S003, S041]
prerequisites: []
related_ids: [method.gradient-descent, trust-region-newton-cg, trust-region-reflective]
visualization_ids: []
comparison_ids: []
aliases: [/learn/least-squares]
visualization_aliases: []
comparison_aliases: []
status: published
last_reviewed: 2026-07-16
---

観測ごとの残差vectorとJacobian構造を保ち、二乗和・damping・trust-region診断を使ってparameterを局所推定する方法です。

## Scalar lossへ潰す前に残差を定義する

観測 $y_i$ とmodel予測 $m_i(x)$ の差を

$$
r_i(x)=m_i(x)-y_i
$$

とし、

$$
\min_x\frac{1}{2}\|r(x)\|_2^2
$$

を解きます。残差vectorを直接solverへ渡すと、Jacobian $J=\partial r/\partial x$、sparsity、観測別診断を利用できます。

## Gauss–NewtonとLevenberg–Marquardt

Gauss–NewtonはHessianを概ね $J^TJ$ で近似し、

$$
J^TJp=-J^Tr
$$

を解きます。Levenberg–Marquardtはdampingを加え、

$$
(J^TJ+\lambda I)p=-J^Tr
$$

とすることで、modelが悪い領域ではstepを抑えます。実装によりtrust-region解釈やscale付きdampingが異なります。

## SciPyのdefaultであるTRF

SciPyの`scipy.optimize.least_squares`は、`method`を指定しない場合にTrust Region Reflective（TRF）を使います。TRFも残差とJacobianからGauss–Newton型modelを作りますが、boundsまでの距離に応じてtrust regionの形を調整し、境界で反射した探索方向も考えます。

- bounds付きparameterを直接扱える
- denseな中小規模とlarge sparse Jacobianの両方へ実装経路を持つ
- `cost`、`optimality`、`active_mask`、`nfev`、`njev`、`status`を診断できる
- defaultであることは、すべてのinstanceでLMやdogboxより優れるという意味ではない

境界で何が起きているか、LM・dogboxとの選び分け、SciPyの戻り値は[Trust Region Reflective法](#/learn/trust-region-reflective)で詳しく確認できます。

## 現実の問いを残差へ分ける

| 項目 | 例 |
|---|---|
| decision variables | 反応速度定数、camera pose、材料parameter |
| residuals | 観測ごとの予測誤差、reprojection error |
| weights | 観測noise、単位、信頼度 |
| constraints | bounds、正値性、固定parameter |
| diagnostics | residual pattern、Jacobian rank、parameter相関 |

小さい二乗和だけではmodelが正しいとは言えません。residualに系統的patternが残れば、parameterではなくmodel構造が不足している可能性があります。

## Python

```python
import numpy as np
from scipy.optimize import least_squares

x_data = np.linspace(0.0, 4.0, 20)
y_data = 1.8 * np.exp(-0.7 * x_data) + 0.25


def residuals(parameters: np.ndarray) -> np.ndarray:
    amplitude, rate, offset = parameters
    prediction = amplitude * np.exp(-rate * x_data) + offset
    return prediction - y_data


def jacobian(parameters: np.ndarray) -> np.ndarray:
    amplitude, rate, _ = parameters
    exponential = np.exp(-rate * x_data)
    return np.column_stack(
        (
            exponential,
            -amplitude * x_data * exponential,
            np.ones_like(x_data),
        )
    )


result = least_squares(
    residuals,
    x0=np.array([1.0, 0.4, 0.0]),
    jac=jacobian,
    bounds=([0.0, 0.0, -1.0], [5.0, 3.0, 2.0]),
    method="trf",
    xtol=1e-12,
    ftol=1e-12,
    gtol=1e-12,
)

print(result.success, result.x, result.cost, result.optimality, result.nfev)
```

## Weightとrobust loss

観測ごとのnoise分散が異なるなら、同じ単位の残差として扱う前に標準化します。外れ値がある場合、Huberやsoft-L1などのrobust lossを使えますが、

- thresholdの意味
- どの観測がdown-weightされたか
- noise modelとの整合

を残します。robust lossは外れ値の原因を自動説明しません。

## 診断値

- residual vectorと分布
- cost / RMS / weighted RMS
- gradient / optimality
- Jacobian rankとsingular values
- parameter covarianceの近似
- active bounds
- function / Jacobian evaluation数
- accepted / rejected step
- termination reason

## 識別可能性

異なるparameter組がほぼ同じ予測を作る場合、costが小さくてもparameterは一意に決まりません。

確認:

- Jacobianのrank
- condition number
- profile likelihoodやbootstrap
- parameter相関
- 異なる初期点からの解
- holdout dataでの予測

::: warning
optimizerの成功statusを統計的妥当性と混同しません。parameter uncertainty、model mismatch、measurement processを別に評価します。
:::

## Alternative-firstと切替

- 線形least squares → QR / SVDを先に使う
- root findingが本来の問い → 二乗和化で解が変わらないか確認
- bounds中心・大規模 → [Trust Region Reflective](#/learn/trust-region-reflective)
- 無制約・小規模 → LM
- 強い一般制約 → constrained NLP
- residual/Jacobianを作れないblack-box → derivative-free法
- ill-conditioning → scaling、regularization、実験設計を見直す
