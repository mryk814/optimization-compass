---
content_id: trust-region-reflective
kind: method
method_id: M_TRUST_REGION_REFLECTIVE
title_ja: Trust Region Reflective法
title_en: Trust Region Reflective
summary: bounds付き非線形最小二乗で、境界までの距離に応じてtrust regionを変形し、反射方向も使って局所解を探すGauss–Newton系手法です。
source_ids: [S003, S096]
related_ids: [least-squares, gauss-newton, trust-krylov, lbfgsb, slsqp]
status: published
last_reviewed: 2026-07-16
---

bounds付き非線形最小二乗で、境界までの距離に応じてtrust regionを変形し、反射方向も使って局所解を探すGauss–Newton系手法です。

## 30秒でつかむ

この手法の気持ちは、**残差を小さくする方向へ進みたいが、parameterの上下限へ正面からぶつかるのではなく、境界までの余裕を見ながら歩幅と方向を調整したい**というものです。

- 見ているもの: residual vector、Jacobian、gradient、boundsまでの距離
- 動かしているもの: 現在点、trust regionの形、Gauss–Newton候補、反射候補
- 前進の判断: 実際のcost低下と局所modelが予測した低下の一致
- 恐れていること: 悪いJacobian、rank deficiency、parameter scaleの不一致、境界上での停滞

SciPyの`scipy.optimize.least_squares`では`method="trf"`がdefaultです。しかしdefaultであることは、あらゆる問題で最も速い、または最も正確という意味ではありません。

## まず確認すること

| 項目 | 確認内容 |
|---|---|
| formulation | 目的を観測ごとのresidual vectorとして自然に表せるか |
| bounds | 上下限が物理的・統計的に意味を持つか |
| Jacobian | 解析、automatic differentiation、または安定した差分で得られるか |
| scale | parameterごとの単位・桁が大きく異ならないか |
| sparsity | large problemでJacobian sparsityやLinearOperatorを渡せるか |
| goal | bounds内の局所解と一階診断で十分か |

一般非線形制約、離散変数、大域最適性certificateが必要な問題へは、そのまま適用しません。

## 仕組み

非線形最小二乗は、residual vector $r(x)$から次を最小化します。

$$
F(x)=\frac{1}{2}\lVert r(x)\rVert_2^2
$$

Gauss–Newton型の局所modelは、Jacobian $J(x)$を使って、近くのresidualを線形化します。

$$
r(x+p)\approx r(x)+J(x)p
$$

TRFはこのmodelをtrust regionの内側で改善します。通常の球をそのまま使うのではなく、boundsまでの距離と勾配方向に応じてscaleを変え、境界へ直接突っ込むstepを避けます。

## なぜReflectiveなのか

候補方向がboundへ向かう場合、境界で反射した方向も探索候補として考えます。これは「値をboundでclipするだけ」とは異なります。

SciPyの実装は、理論上の条件を満たすために反復点をstrictly feasible、つまりboundの少し内側へ保ちます。そのため、終了時の`active_mask`は完全な等号判定ではなく、toleranceに基づく判定です。

この設計により、境界近くの解を扱いつつ、実行可能領域の内部で局所modelを更新できます。

## DenseとSparseで何が変わるか

SciPyではJacobianの表現に応じてtrust-region部分問題の解き方が変わります。

| 状況 | 主な内部solve |
|---|---|
| denseで中小規模 | SVDに近いexact trust-region solve |
| large sparse | LSMRによる近似Gauss–Newton方向とscaled gradientの2次元部分空間 |
| `jac_sparsity`を指定 | sparse finite differenceとLSMR経路を利用 |

同じ`method="trf"`でも、Jacobianの型・sparsity・rankにより計算量と診断方法が変わります。

## 向く条件・避ける条件

向きやすい条件:

- bounds付き非線形最小二乗
- residualとJacobianを直接扱える
- large sparse Jacobianを持つparameter estimation
- robust lossで外れ値の影響を弱めたい
- LMではboundsを扱えない

避ける条件:

- 一般非線形制約が本質
- residual分解が不自然なscalar objective
- 不連続、離散、強い未model化noise
- global optimumの証明が必要
- boundsが単なる推測で、解を人工的に固定してしまう

## うまくいったサインと切替サイン

まず見る値:

- `cost`とresidual pattern
- `optimality`
- `active_mask`
- `nfev`と`njev`
- `status`と`message`
- Jacobianのrankまたはsingular values
- 異なる初期値からの解

切替サイン:

- `optimality`が下がらず、active boundが頻繁に入れ替わる → boundsとscaleを確認
- rank deficiencyが強い → parameterization、regularization、実験設計を見直す
- boundsなしの小規模問題でevaluationを減らしたい → LMと比較
- 小規模bounds問題でTRFが重い → dogboxを同じbudgetで比較
- 一般制約が必要 → SLSQP、trust-constr、interior-point NLPへ
- 多数の初期値で異なる解 → global searchまたはidentifiabilityを確認

## LM・dogbox・L-BFGS-Bとの違い

| 手法 | 主な対象 | bounds | 残差構造 | 注意点 |
|---|---|---:|---:|---|
| LM | 小規模・無制約least squares | なし | 使う | 解の近くで効率的だが、boundsとsparse Jacobianに非対応 |
| TRF | bounded / unbounded least squares | あり | 使う | SciPy default。large sparseにも対応するが、局所法 |
| dogbox | 小規模bounds付きleast squares | あり | 使う | rank-deficient Jacobianでは遅くなりやすい |
| L-BFGS-B | 一般scalar objective | あり | 潰してしまう | residual別診断やrobust loss構造を直接使わない |

`least_squares`で解ける問題を、理由なくscalar lossへ潰して`minimize`へ渡すと、residual・Jacobian・sparsityの情報を失う場合があります。

## Python

```python
import numpy as np
from scipy.optimize import least_squares


def residuals(x: np.ndarray) -> np.ndarray:
    return np.array([
        10.0 * (x[1] - x[0] ** 2),
        1.0 - x[0],
    ])


def jacobian(x: np.ndarray) -> np.ndarray:
    return np.array([
        [-20.0 * x[0], 10.0],
        [-1.0, 0.0],
    ])


result = least_squares(
    residuals,
    x0=np.array([2.0, 2.0]),
    jac=jacobian,
    bounds=([-np.inf, 1.5], [np.inf, np.inf]),
    method="trf",
)

print(result.x)
print(result.cost, result.optimality, result.active_mask)
print(result.status, result.message, result.nfev, result.njev)

assert result.success
assert np.isclose(result.x[1], 1.5, atol=1e-6)
```

この例では無制約のRosenbrock最小点がbounds外になるため、解は下限境界`x[1] = 1.5`上に移ります。

## コラム: defaultは推薦順位ではない

library defaultは、APIが対象とする広い問題で壊れにくい選択を提供するためのものです。利用者のproblem size、Jacobian、bounds、noise、必要保証を見た最終推薦とは異なります。

SciPyでは`least_squares`のdefaultはTRFです。一方、`curve_fit`はboundsなしならLM、boundsを与えるとTRFを選びます。この条件はlibrary versionとAPIごとに記録し、手法の一般性能rankingとして扱いません。

## 次に読む

残差の作り方とidentifiabilityは[非線形最小二乗とLevenberg–Marquardt](#/learn/least-squares)、曲率近似の基礎は[Gauss–Newton法](#/learn/gauss-newton)を確認してください。一般制約がある場合は[制約付き非線形最適化の選び分け](#/learn/family.constrained-nlp)へ進みます。
