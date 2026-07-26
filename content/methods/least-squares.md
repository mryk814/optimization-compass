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
visualization_ids: [exponential-fit-lm]
comparison_ids: [COMPARE_EXPONENTIAL_FIT_SOLVER_CONDITIONS]
aliases: [/learn/least-squares]
visualization_aliases: []
comparison_aliases: []
status: published
last_reviewed: 2026-07-26
---

観測ごとの残差vectorとJacobian構造を保ち、二乗和・damping・trust-region診断を使ってparameterを局所推定する方法です。

## 30秒でつかむ

観測ごとの残差を保ったまま、Jacobianと診断値を使ってparameterを局所推定します。

- 見ているもの: residual vector、Jacobian、weights、bounds
- 前進の判断: costの低下、residual pattern、Jacobianの状態
- 注意すること: 小さいcostだけではmodelの正しさやparameterの一意性は決まりません

予測curveが観測点に重なれば、推定は終わったと判断できるでしょうか。
固定診断probeでは、見た目がほぼ重なる最終frameでも停止criterionには到達していません。

![20点のnoiseless合成dataへ3 parameter指数減衰modelを当てる固定Python診断probe。初期parameterではmodel curveと観測点の間に大きなresidualがあり、12評価後はcurveがほぼ重なる。一方、下段の履歴ではresidual normと既知truthからのparameter距離がともに0ではなく、停止criterion未達である。](./media/least-squares-fit-diagnostic.svg "solver-independentなdamped Gauss–Newton診断probeの実行結果です。curve、観測別residual、residual norm、parameter errorを分けて読みます。LMやSciPy solverの実行結果、実dataの識別性、統計的妥当性は示しません。")

上の2枚は同じ20観測に対する初期frameと12評価後です。
curveの重なりだけで止めず、その下のresidual normとparameter errorを確認します。

## 仕組み

### 残差を定義する

観測 $y_i$ とmodel予測 $m_i(x)$ の差を

$$
r_i(x)=m_i(x)-y_i
$$

とし、

$$
\min_x\frac{1}{2}\|r(x)\|_2^2
$$

を解きます。
残差vectorを直接solverへ渡すと、Jacobian $J=\partial r/\partial x$を利用できます。
sparsityと観測別診断も保てます。

### Gauss–NewtonとLevenberg–Marquardt

Gauss–NewtonはHessianを概ね $J^TJ$ で近似し、

$$
J^TJp=-J^Tr
$$

を解きます。Levenberg–Marquardtはdampingを加え、

$$
(J^TJ+\lambda I)p=-J^Tr
$$

とすることで、modelが悪い領域ではstepを抑えます。実装によりtrust-region解釈やscale付きdampingが異なります。

## まず確認すること

| 項目 | 例 |
|---|---|
| decision variables | 反応速度定数、camera pose、材料parameter |
| residuals | 観測ごとの予測誤差、reprojection error |
| weights | 観測noise、単位、信頼度 |
| constraints | bounds、正値性、固定parameter |
| diagnostics | residual pattern、Jacobian rank、parameter相関 |

小さい二乗和だけではmodelが正しいとは言えません。residualに系統的patternが残れば、parameterではなくmodel構造が不足している可能性があります。

## 向く条件・避ける条件

向いている条件:

- 観測ごとのresidualとJacobianを作れる
- weights、bounds、正値性などを残差とともに扱う必要がある
- residual patternやJacobian rankを診断したい

避ける／切り替える条件:

- 線形least squares → QR / SVDを先に使う
- root findingが本来の問い → 二乗和化で解が変わらないか確認
- bounds中心・大規模 → [Trust Region Reflective](#/learn/trust-region-reflective)
- 強い一般制約 → constrained NLP
- residual/Jacobianを作れないblack-box → derivative-free法
- ill-conditioning → scaling、regularization、実験設計を見直す

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

[LM適用条件の共通診断probe](#/traces/exponential-fit-lm)では、推定値と残差norm、Jacobian rankを同じevaluation軸で追います。
この線はLMの実行結果ではありません。
[solver条件の比較](#/compare/COMPARE_EXPONENTIAL_FIT_SOLVER_CONDITIONS)では同一のframe履歴を使い、bounds対応と残差vector interfaceの条件だけを読み分けます。

## 診断値

### Weightとrobust loss

観測ごとのnoise分散が異なるなら、同じ単位の残差として扱う前に標準化します。外れ値がある場合、Huberやsoft-L1などのrobust lossを使えますが、

- thresholdの意味
- どの観測がdown-weightされたか
- noise modelとの整合

を残します。robust lossは外れ値の原因を自動説明しません。

### 収集する値

- residual vectorと分布
- cost / RMS / weighted RMS
- gradient / optimality
- Jacobian rankとsingular values
- parameter covarianceの近似
- active bounds
- function / Jacobian evaluation数
- accepted / rejected step
- termination reason

### 識別可能性

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

## 失敗・切替の兆候

- residual normが下がっても系統的patternが残る → parameter追加より先にmodel構造を見直す
- 異なる初期点から同程度のcostへ到達し、parameterが大きく異なる → 識別可能性と実験設計を見直す

## 次に読む

bounds中心・大規模な問題では[Trust Region Reflective](#/learn/trust-region-reflective)へ進みます。
残差vectorをscalar objectiveへ変換する場合との違いは、[L-BFGS-B](#/learn/lbfgsb)と[solver条件の比較](#/compare/COMPARE_EXPONENTIAL_FIT_SOLVER_CONDITIONS)で確認できます。
