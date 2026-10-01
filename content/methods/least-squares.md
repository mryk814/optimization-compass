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
last_reviewed: 2026-09-30
---

観測ごとの残差vectorとJacobian構造を保ち、二乗和・damping・trust-region診断を使ってparameterを局所推定する方法です。

## 30秒でつかむ

Gauss–Newton法は、「この先はまっすぐ進めば着く」と信じて一気に進む運転です。道が読めているうちは速く着きます。カーブの先でも同じ速さで進むと、道から外れます。
Levenberg–Marquardt法（LM法）は、道が怪しいときにブレーキ（減衰）をかけます。信じられる範囲だけ進み、外れたら速度を落として、もう一度試します。

- **見るもの**: 観測ごとの残差ベクトル、Jacobian、重み、上下限
- **動かすもの**: パラメータと、一手の長さを調整する減衰の大きさ $\lambda$
- **前進の判断**: 目的値（cost）の低下、残差のパターン、Jacobianの状態

小さな二乗和だけでは、モデルの正しさやパラメータの一意性は決まりません。

## 一手の意味

観測 $y_i$ とモデルの予測 $m_i(x)$ の差を残差とします。

$$
r_i(x)=m_i(x)-y_i
$$

残差の二乗和の半分を、パラメータ $x$ について最小にします。

$$
\min_x\frac{1}{2}\|r(x)\|_2^2
$$

残差ベクトルをそのままソルバーへ渡すと、ヤコビ行列（Jacobian）$J=\partial r/\partial x$ を利用できます。疎構造と観測ごとの診断も保てます。

[Gauss–Newton法](#/learn/gauss-newton)は、Hessianを $J^TJ$ で近似して、次の連立方程式を解きます。

$$
J^TJp=-J^Tr
$$

LM法は、左辺に減衰項 $\lambda I$ を足します。次の式は、$\lambda$ が大きいほど一手を短く、勾配の反対向きに寄せるという意味です。

$$
(J^TJ+\lambda I)p=-J^Tr
$$

$\lambda=0$ ならGauss–Newton法です。$\lambda$ を大きくすると、一手は短くなり、最急降下の向きに近づきます。実装によって、信頼領域の解釈や、尺度を付けた減衰の形は異なります。

$\lambda$ は、試した一手の結果を見て調整します。目印は、実際の目的値の減少を、線形モデルが予測した減少で割った比 $\rho$ です。

- $\rho$ が正で1に近い → モデルが当たっている。一手を受け入れて、$\lambda$ を下げる
- $\rho$ が負 → 目的値が増えた。一手を捨てて、$\lambda$ を上げてやり直す

## 小さな例

[Gauss–Newton法](#/learn/gauss-newton)と同じ、指数減衰の当てはめです。時刻 $t=0,1,2,3,4$ で量 $y=5.1,\,3.0,\,1.9,\,1.1,\,0.7$ を観測しました。
モデルは $y=a\,e^{-kt}$ で、初期値は $(a,k)=(1,\,0.1)$ です。

### 減衰の大きさで、最初の一手はどう変わるか

初期値での一手を、$\lambda$ を変えて計算します。勾配の反対向きは、およそ $(0.845,\,-0.536)$ です。

| $\lambda$ | 一手 $(\Delta a,\,\Delta k)$ | 一手の長さ | 一手の先の目的値 |
|---:|---|---:|---:|
| 0（Gauss–Newton） | $(3.746,\ 1.052)$ | 3.89 | 2.870 |
| 1 | $(2.168,\ 0.457)$ | 2.22 | 3.131 |
| 10 | $(0.503,\ -0.067)$ | 0.51 | 8.008 |
| 100 | $(0.067,\ -0.036)$ | 0.076 | 10.62 |

初期値の目的値は $11.25$ です。$\lambda$ を上げるほど一手は短くなり、向きは勾配の反対に近づきます。
一手の先の目的値は、$\lambda$ が小さいほど大きく下がっています。ただし、この比べ方は最初の一手だけです。長い一手が、次の反復でも安全とは限りません。

### 反復の様子

減衰を小さく、$\lambda=0.01$ から始めます。教材用に、$\rho>0$ なら一手を受け入れて $\lambda$ を $1/3$ に、$\rho\le 0$ なら一手を捨てて $\lambda$ を10倍にします。実際の実装の更新規則とは違います。

| 試行 | 現在点 $(a,\,k)$ | $\lambda$ | 試した一手 | 先の目的値 | $\rho$ | 判定 |
|---:|---|---:|---|---:|---:|---|
| 1 | $(1.000,\ 0.100)$ | 0.01 | $(3.718,\ 1.042)$ | 2.855 | 0.76 | 受け入れ |
| 2 | $(4.718,\ 1.142)$ | 0.0033 | $(0.314,\ -1.157)$ | 27.19 | −9.4 | 捨てる |
| 3 | $(4.718,\ 1.142)$ | 0.033 | $(0.311,\ -1.148)$ | 25.23 | −8.7 | 捨てる |
| 4 | $(4.718,\ 1.142)$ | 0.33 | $(0.282,\ -1.061)$ | 12.36 | −3.7 | 捨てる |
| 5 | $(4.718,\ 1.142)$ | 3.3 | $(0.153,\ -0.603)$ | 0.0855 | 1.40 | 受け入れ |
| 6 | $(4.872,\ 0.539)$ | 1.1 | $(0.106,\ -0.046)$ | 0.0099 | 1.00 | 受け入れ |

試行2〜4の一手は、Gauss–Newton法が受け入れて目的値を悪化させた一手（$2.87$ から $29.3$ へ跳ねた一手）と似ています。
LM法は、目的値が増えたので一手を捨て、$\lambda$ を上げてやり直します。
試行5で、一手を約 $0.6$ まで短くすると、目的値は $0.0855$ まで下がります。その後は $\lambda$ を下げながら進み、最終的に $(a,k)\approx(5.0787,\,0.5049)$ に着きます。目的値は約 $0.00408$ です。

同じ初期値でも、Gauss–Newton法は途中で一度大きく悪化しました。LM法は、悪化した一手を試した段階で捨てます。

## 向く条件・避ける条件

先に、次の項目を確認します。

| 項目 | 例 |
|---|---|
| 決める変数 | 反応速度定数、カメラの姿勢、材料パラメータ |
| 残差 | 観測ごとの予測誤差、再投影誤差 |
| 重み | 観測のノイズ、単位、信頼度 |
| 制約 | 上下限、正値性、固定するパラメータ |
| 診断 | 残差のパターン、Jacobianのランク、パラメータの相関 |

小さい二乗和だけでは、モデルが正しいとは言えません。残差に系統的なパターンが残るなら、パラメータではなく、モデルの構造が足りない可能性があります。

向く条件です。

- 観測ごとの残差とJacobianを作れる（[非線形最小二乗](#/learn/concept.nonlinear-least-squares)）
- 重み、上下限、正値性などを、残差とともに扱う必要がある
- 残差のパターンやJacobianのランクを診断したい

避ける、または切り替える条件です。

- 線形の最小二乗である → QR分解やSVDを先に使う（[線形最小二乗](#/learn/concept.linear-least-squares)）
- 求根が本来の問いである → 二乗和にしても解が変わらないか確認する
- 上下限が中心、または大規模である → [Trust Region Reflective](#/learn/trust-region-reflective)（[上下限つきの滑らかな最小化](#/formulations/PA008)）
- 強い一般制約がある → 制約つき非線形計画（NLP）へ切り替える
- 残差やJacobianを作れないブラックボックスである → 微分を使わない手法を使う
- 悪条件（ill-conditioning）である → 尺度合わせ、正則化、実験設計を見直す

## Python

次の例は、上の小さな例と同じ問題を、`scipy.optimize.least_squares` のLM法（`method="lm"`）で解きます。

```python
import numpy as np
from scipy.optimize import least_squares

t = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
y = np.array([5.1, 3.0, 1.9, 1.1, 0.7])


def residuals(p: np.ndarray) -> np.ndarray:
    a, k = p
    return a * np.exp(-k * t) - y


def jacobian(p: np.ndarray) -> np.ndarray:
    a, k = p
    e = np.exp(-k * t)
    return np.column_stack([e, -a * t * e])


result = least_squares(residuals, x0=[1.0, 0.1], jac=jacobian, method="lm")

print(result.x, result.cost, result.status, result.nfev)
# [5.07867619 0.50493273] 0.004081770467869126 2 9
print(result.optimality, result.fun)
# 2.4e-07 [-0.0213  0.0652 -0.0500  0.0166 -0.0261]
print(np.linalg.svd(result.jac, compute_uv=False))
# [6.4828 1.0525]
```

`cost` は $\tfrac12\sum r_i^2$、`status` の正の値は許容誤差を満たして止まったことを表します。
`result.fun` は最終の残差ベクトルで、符号が交互に入れ替わっています。5点では、系統的な偏りは目立ちません。
Jacobianの特異値は $6.48$ と $1.05$ で、どちらも0から離れています。二つのパラメータは、このデータから区別できています。

`method="lm"` は上下限を扱えません。上下限が要るときは `method="trf"` を使います。

## 診断値

curveが観測点に重なれば、推定は終わったと判断できるでしょうか。
固定の診断probeでは、見た目がほぼ重なる最終フレームでも、停止条件には到達していません。

![20点のnoiseless合成dataへ3 parameter指数減衰modelを当てる固定Python診断probe。初期parameterではmodel curveと観測点の間に大きなresidualがあり、12評価後はcurveがほぼ重なる。一方、下段の履歴ではresidual normと既知truthからのparameter距離がともに0ではなく、停止criterion未達である。](./media/least-squares-fit-diagnostic.svg "solver-independentなdamped Gauss–Newton診断probeの実行結果です。curve、観測別residual、residual norm、parameter errorを分けて読みます。LMやSciPy solverの実行結果、実dataの識別性、統計的妥当性は示しません。")

上の2枚は、同じ20観測に対する初期フレームと12評価後です。
curveの重なりだけで止めず、その下の残差のノルムとパラメータの誤差を確認します。

### 重みと頑健な損失

観測ごとにノイズの分散が異なるなら、同じ単位の残差として扱う前に標準化します。
外れ値がある場合、Huberやsoft-L1などの頑健な損失（robust loss）を使えます。その場合は、次の三つを記録します。

- しきい値の意味
- どの観測の重みが下げられたか
- ノイズのモデルとの整合

頑健な損失は、外れ値の原因を自動では説明しません。

### 収集する値

- 残差ベクトルとその分布
- cost、RMS、重み付きRMS
- 勾配、最適性（optimality）
- Jacobianのランクと特異値
- パラメータの共分散の近似
- 上下限に張り付いたパラメータ（active bound）
- 関数評価とJacobian評価の回数
- 受け入れた一手と捨てた一手
- 終了理由

### 識別可能性

異なるパラメータの組がほぼ同じ予測を作る場合、目的値（cost）が小さくてもパラメータは一意に決まりません。

確認する項目です。

- Jacobianのランク
- 条件数
- プロファイル尤度やブートストラップ
- パラメータの相関
- 異なる初期点からの解
- 学習に使わなかったデータでの予測

::: warning
最適化の成功状態（success status）を、統計的な妥当性と混同しません。パラメータの不確かさ、モデルの不一致、測定の過程は別に評価します。
:::

## 失敗・切替の兆候

- 残差のノルムが下がっても、系統的なパターンが残る → モデルの構造が足りない → パラメータを増やす前に、構造を見直す
- 異なる初期点から同程度の目的値（cost）に到達し、パラメータが大きく異なる → 識別できていない → 識別可能性と実験設計を見直す
- 受け入れる一手が減り、$\lambda$ が大きいまま進みが遅い → 線形モデルが信頼できる範囲が狭い → Jacobianの誤り、尺度、初期値を確認する
- Jacobianのランクが低い → 効果の同じパラメータがある → パラメータ化を見直す
- 上下限を破る、または境界に張り付く → LM法は上下限を扱えない → [Trust Region Reflective](#/learn/trust-region-reflective)へ切り替える

## コラム: 共通の診断probeとsolver条件の比較

[LM適用条件の共通診断probe](#/traces/exponential-fit-lm)では、推定値と残差のノルム、Jacobianのランクを同じ評価の軸で追います。
この線はLMの実行結果ではありません。
[solver条件の比較](#/compare/COMPARE_EXPONENTIAL_FIT_SOLVER_CONDITIONS)では、同一のフレーム履歴を使い、上下限への対応と残差ベクトルの入口という条件だけを読み分けます。

## 次に読む

- [Trust Region Reflective](#/learn/trust-region-reflective)：上下限が中心、または大規模な問題へ
- [Gauss–Newton法](#/learn/gauss-newton)：減衰項を足す前の、素の一手
- [非線形最小二乗](#/learn/concept.nonlinear-least-squares)：この手法が解く問題の標準形
- [L-BFGS-B](#/learn/lbfgsb)：残差ベクトルをスカラーの目的へ変換する場合との違い
