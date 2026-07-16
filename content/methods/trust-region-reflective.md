---
content_id: trust-region-reflective
kind: method
method_id: M_TRUST_REGION_REFLECTIVE
title_ja: Trust Region Reflective（TRF）
title_en: Trust Region Reflective
summary: bounds付き非線形最小二乗で、境界までの距離と反射方向を使いながらGauss–Newton型の局所modelを安全に改善する方法です。
source_ids: [S003, S096, S097]
related_ids: [least-squares, gauss-newton, trust-krylov, lbfgsb, slsqp]
status: published
last_reviewed: 2026-07-16
---

bounds付き非線形最小二乗で、境界までの距離と反射方向を使いながらGauss–Newton型の局所modelを安全に改善する方法です。

## 30秒でつかむ

この手法の気持ちは、**残差を減らす方向へ進みたいが、parameterの上下限へ正面から突っ込まず、境界までの余裕を見ながら、必要なら反射した方向も試したい**というものです。

- 見ているもの: residual vector、Jacobian、boundsまでの距離、scaled gradient
- 動かしているもの: parameter、trust-regionの形と大きさ、候補step
- 前進の判断: 実際のcost低下と局所modelが予測した低下の一致
- 恐れていること: parameter scaleの不一致、rank deficientなJacobian、境界上での停滞、誤った残差model

SciPyの`scipy.optimize.least_squares`では`method='trf'`がdefaultです。`curve_fit`でもboundsを指定するとTRFがdefaultになります。ただし、defaultは万能ランキングではなく、bounds・疎Jacobian・robustnessを広く扱える実装上の堅実な選択です。

## まず確認すること

| 項目 | 確認内容 |
|---|---|
| 問題形式 | scalar objectiveではなく、観測ごとのresidual vectorを返せるか |
| 変数 | 連続parameterで、上下限に実務上の意味があるか |
| Jacobian | callable、有限差分、sparse構造のどれを使うか |
| scale | parameterの単位が何桁も異なっていないか |
| 解の意味 | 局所最小でよいか、parameter uncertaintyを別に評価するか |
| 制約 | bounds以外の一般等式・不等式制約が必要ではないか |

TRFは一般的な`minimize`のtrust-region Newton法とは別物です。非線形最小二乗のresidual/Jacobian構造とboundsを直接使います。

## 仕組み

残差 $r(x)$ の二乗和を考えます。

$$
F(x)=\frac{1}{2}\lVert r(x)\rVert_2^2,
\qquad l\leq x\leq u
$$

現在点では、Jacobian $J$を使って残差を線形化します。

$$
r(x+p)\approx r(x)+J(x)p
$$

TRFは、このGauss–Newton型modelへboundsを考慮した特別な対角項を加え、境界までの距離とgradient方向に応じてtrust regionの形を調整します。境界を直接踏み越えるstepを避けるだけでなく、boundsで反射した探索方向も候補にします。

SciPy実装はiteratesをstrictly feasibleに保ちます。そのため`active_mask`は「数値的に境界と判断したか」をtoleranceで表し、必ずしもparameterがbit単位でboundと一致することを意味しません。

## LM・TRF・dogboxの選び分け

| 状況 | まず比較する候補 | 理由 |
|---|---|---|
| 小規模・無制約・残差数が変数数以上 | LM | boundsを使わず、良い近傍では効率的なことが多い |
| boundsあり、またはlarge sparse Jacobian | TRF | boundsと疎構造を直接扱い、一般にrobust |
| 小規模bounds付き、Jacobianがfull rank | dogbox | rectangular trust regionが合う場合がある |
| bounds以外の一般制約 | SLSQP / interior-point NLP | TRFの制約supportを超える |
| residual構造を作れないscalar objective | L-BFGS-Bなど | least-squares専用構造を使えない |

`curve_fit`は無制約ならLM、bounds指定時にはTRFを暗黙選択します。手法を比較するときは、`method`を明示しているか、APIがdefaultを選んだかを記録します。

## 向く条件・避ける条件

向きやすい条件:

- bounds付きcurve fitting・parameter estimation
- residual vectorとJacobianを直接定義できる
- large sparse Jacobianを`jac_sparsity`やsparse matrixとして渡せる
- robust lossを使いながらleast-squares構造を保ちたい
- LMではboundsを扱えない、または問題規模が大きい

避ける条件:

- 離散・カテゴリ変数
- bounds以外の一般等式・不等式制約
- 強い不連続や、再現不能なnoiseが残差差分を支配する
- 大域最適性certificateが必要
- parameterの単位・bounds・残差weightが説明できない

## うまくいったサインと切替サイン

主に次を読みます。

- `cost`: residual二乗和の半分。統計的妥当性そのものではない
- `optimality`: boundsを考慮した一階optimality measure
- `active_mask`: lower boundがactiveなら`-1`、upper boundなら`1`、それ以外は`0`
- `nfev` / `njev`: residualとJacobianの評価回数
- `status` / `message`: `gtol`、`ftol`、`xtol`、budgetのどれで止まったか
- residual pattern、Jacobian rank、condition number、異なる初期値の結果

切替サイン:

- `cost`は下がらず`active_mask`だけ固定する → bounds、scale、初期値を確認
- `optimality`が高いまま`xtol`で停止する → stepが小さいだけでstationarityが弱い可能性
- sparse問題で評価が重い → `jac_sparsity`と`tr_solver='lsmr'`を検討
- rank deficiencyが強い → parameterization、regularization、実験設計を見直す
- boundsが不要で小規模 → LMと同じbudgetで比較
- 一般制約が必要 → constrained NLPへ切り替える

## Python例

既知の無制約解がbounds外にあり、最適解が境界へ移る例です。

```python
import numpy as np
from scipy.optimize import least_squares


def residuals(x: np.ndarray) -> np.ndarray:
    return np.array([
        x[0] - 2.0,
        2.0 * (x[1] + 1.0),
    ])


def jacobian(x: np.ndarray) -> np.ndarray:
    del x
    return np.array([
        [1.0, 0.0],
        [0.0, 2.0],
    ])


result = least_squares(
    residuals,
    x0=np.array([1.0, 0.0]),
    jac=jacobian,
    bounds=([0.0, -0.5], [1.5, 2.0]),
    method="trf",
)

print(result.x)          # おおよそ [1.5, -0.5]
print(result.cost)
print(result.optimality)
print(result.active_mask)
print(result.status, result.message)
```

`success=True`だけで判断せず、解がどのboundに張り付き、残差がどの観測に残っているかを確認します。

## コラム: exactとLSMRは別の手法ではない

SciPyのTRFでは、dense JacobianならSVD相当の計算を使う`exact`系、large sparse JacobianならLSMRから得た近似Gauss–Newton方向を含む2次元部分空間法を利用できます。これはTRFの内部subproblem solverの違いであり、canonical method自体を別IDへ分けるものではありません。

`tr_solver=None`では、最初に返されたJacobianの型に基づいてSciPyが内部solverを選びます。benchmarkではTRFという名前だけでなく、Jacobian表現、`jac_sparsity`、`tr_solver`、regularization optionも保存します。

## 次に読む

残差model全体の作り方は[非線形最小二乗とLevenberg–Marquardt法](#/learn/least-squares)、曲率近似の基本は[Gauss–Newton法](#/learn/gauss-newton)、大規模trust-region内部solveは[Trust-region Krylov](#/learn/trust-krylov)を確認してください。
