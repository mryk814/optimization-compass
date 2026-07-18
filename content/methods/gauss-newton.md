---
content_id: gauss-newton
kind: method
method_id: M_GAUSS_NEWTON
title_ja: Gauss–Newton法
title_en: Gauss-Newton Method
summary: 非線形最小二乗の残差Jacobianから曲率近似を作り、一般目的関数として扱わず残差構造を直接利用する局所法です。
source_ids: [S003, S041, S056]
related_ids: [least-squares, newton-method, trust-region-newton-cg]
status: published
last_reviewed: 2026-07-18
---

非線形最小二乗の残差Jacobianから曲率近似を作り、一般目的関数として扱わず残差構造を直接利用する局所法です。

## 30秒でつかむ

この手法の気持ちは、**合計lossだけを見るのではなく、観測ごとの残差がparameterを変えるとどう動くかを使って、全部の残差をまとめて小さくしたい**というものです。

- 見ているもの: 残差vectorとJacobian
- 動かしているもの: parameterと線形化されたleast-squares step
- 前進の判断: 二乗和、残差分布、gradient相当量の低下
- 恐れていること: rank deficiency、外れ値、初期値の悪さ、大きな残差での近似誤差

一般のNewton法とは異なり、目的関数が残差二乗和であることを利用してHessianの一部を近似します。

## 仕組み

残差 $r(x)$ を現在点の近くで線形化します。

$$
r(x+p) \approx r(x) + J(x)p
$$

その近似残差の二乗和を最小にするstepを求めます。

$$
J^T J p = -J^T r
$$

$J^T J$を直接作るとcondition numberが悪化する場合があるため、実装ではQR、SVD、疎linear algebra、trust-regionを使うことがあります。

## まず確認すること

| 項目 | 確認内容 |
|---|---|
| formulation | 目的が本当に残差二乗和として意味を持つか |
| residual | 観測ごとの残差を返せるか |
| Jacobian | 正確または安定に計算できるか |
| weighting | 単位・noise分散に応じたweightが必要か |
| identifiability | parameterがデータから区別できるか |
| constraints | boundsや一般制約をどう扱うか |

線形最小二乗なら反復法よりQRやSVDを先に検討します。
外れ値がある場合はrobust lossの意味を明示します。

## 向く条件・避ける条件

向きやすい条件:

- curve fitting、parameter estimation、bundle adjustmentなどの非線形最小二乗
- 残差Jacobianを利用できる
- 解の近くで残差が小さい、またはmodelがよく合う
- 観測ごとの残差を診断したい

避ける条件:

- 一般目的関数を無理に一つの残差へ置き換える
- 不連続・離散変数・強いoutlierを未処理
- Jacobianのrankが低くparameterが識別不能
- 大域最適性certificateが必要

## Python

```python
import numpy as np

x_data = np.array([0.0, 1.0, 2.0, 3.0])
y_data = np.array([1.1, 2.9, 5.2, 6.8])


def residuals(parameters: np.ndarray) -> np.ndarray:
    slope, intercept = parameters
    return slope * x_data + intercept - y_data


def jacobian(parameters: np.ndarray) -> np.ndarray:
    del parameters
    return np.column_stack([x_data, np.ones_like(x_data)])


parameters = np.array([1.0, 0.0])
for _ in range(5):
    residual = residuals(parameters)
    matrix = jacobian(parameters)
    step, *_ = np.linalg.lstsq(matrix, -residual, rcond=None)
    parameters = parameters + step

print(parameters, np.linalg.norm(residuals(parameters)))
```

## 診断値

残差を一つのnormにまとめるだけでなく、観測別の偏りとparameterの安定性を分けて確認します。

- residual normと観測別residual pattern
- Jacobian rank / singular values
- step norm
- gradient相当の $J^T r$
- trust radiusまたはdamping
- 初期値ごとのparameter差

## うまくいったサインと切替サイン

- stepが大きく振動する → Levenberg–Marquardtやtrust-regionへ切り替える
- rank deficiencyがある → parameterization、regularization、固定parameterを見直す
- 一部観測だけ残差が大きい → model mismatch、outlier、weightを確認する
- 二乗和は小さいがparameterが不安定 → identifiabilityを疑う
- constraintsが本質 → constrained least-squares対応または一般NLPへ切り替える

## コラム: 最小二乗の局所性を見落とさない

残差の二乗和が下がっても、モデルの識別性や観測の偏りまで解決したとは限りません。残差patternとparameterの安定性を分けて確認します。

## 次に読む

Gauss–Newton stepが大きすぎる、Jacobianが悪条件、初期点が遠い場合にはdampingやtrust regionが必要です。
Levenberg–Marquardtはその代表的な安定化です。

実務上は[非線形最小二乗とLevenberg–Marquardt](#/learn/least-squares)を入口にし、残差、Jacobian、rank、停止statusを一緒に保存してください。
