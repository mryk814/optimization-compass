---
content_id: trust-region-reflective
kind: method
method_id: M_TRUST_REGION_REFLECTIVE
title_ja: Trust Region Reflective法
title_en: Trust Region Reflective
summary: bounds付き非線形最小二乗で、境界までの距離と反射方向を使いながら、残差とJacobianから作る局所modelを安全に改善する方法です。
source_ids: [S003, S096]
related_ids: [least-squares, gauss-newton, trust-krylov]
status: published
last_reviewed: 2026-07-16
---

bounds付き非線形最小二乗で、境界までの距離と反射方向を使いながら、残差とJacobianから作る局所modelを安全に改善する方法です。

## 30秒でつかむ

この手法の気持ちは、**残差を減らす方向へ進みたいが、parameterの上下限へ正面から突っ込まず、境界までの余裕を見て歩幅と向きを調整したい**というものです。

- 見ているもの: residual vector、Jacobian、cost、boundsまでの距離
- 動かしているもの: 現在点、trust-regionの形、Gauss–Newton型の候補step
- 前進の判断: 実際のcost低下が局所modelの予測と合っているか
- 恐れていること: 悪いscale、rank-deficient Jacobian、誤ったsparsity、境界付近の停滞

SciPyの`scipy.optimize.least_squares`では、`method`を省略するとTRFが選ばれます。これは「すべての最小二乗で最強」という意味ではなく、boundsの有無を問わず比較的robustに使え、large sparse Jacobianにも対応しやすいというAPI上のdefaultです。

## まず確認すること

| 項目 | 確認内容 |
|---|---|
| problem form | scalar lossではなく、観測ごとのresidual vectorを返せるか |
| bounds | parameterの上下限に物理的・統計的な意味があるか |
| Jacobian | analytic、automatic differentiation、finite differenceのどれか |
| sparsity | large problemで`jac_sparsity`またはsparse Jacobianを渡せるか |
| scale | parameterごとの単位と感度が大きく異ならないか |
| requirement | 局所推定でよいか、大域最適性や一般制約が必要か |

単に「parameterが大きくなりすぎるのが怖い」だけなら、boundsを置く前にparameterization、regularization、データの識別可能性を確認します。境界へ張り付いた解が、現象の答えではなくmodel不足の兆候である場合もあります。

## 仕組み

非線形最小二乗では、residual vector $r(x)$の二乗和を最小化します。

$$
F(x)=\frac{1}{2}\lVert r(x)\rVert_2^2,
\qquad l\leq x\leq u
$$

現在点でresidualを線形化すると、Jacobian $J(x)$を使ったGauss–Newton型の局所modelが得られます。TRFは、このmodelをtrust region内で改善します。

通常の球状trust regionをそのまま置くのではなく、各parameterがboundsからどれだけ離れているかとgradientの向きを使ってscaleを変えます。境界へ直接向かうstepを避けるだけでなく、boundsで反射した探索方向も候補として考えます。理論上の条件を保つため、SciPy実装は反復点をstrictly feasibleな位置に保ちます。

内部の部分問題はJacobianの形で変わります。

- denseで中小規模: SVDに近いexact系のsolve
- large sparse: scaled gradientとLSMRによる近似Gauss–Newton方向が張る低次元部分空間
- `jac_sparsity`を指定: sparse finite differenceとLSMR利用を促す

したがって、同じ`method="trf"`でも、Jacobianをdense arrayで返すか、sparse arrayや`LinearOperator`で返すかによって実行経路とcostが変わります。

## 向く条件・避ける条件

向きやすい条件:

- bounds付きの非線形least squares
- residual vectorとJacobian構造を保持できる
- 変数または観測数が大きく、Jacobianが疎
- robust lossと組み合わせたい
- LMではboundsを扱えない
- `curve_fit`へboundsを与えたとき、暗黙に選ばれた手法を理解したい

避ける条件:

- 一般のscalar objectiveを無理に一個のresidualへしただけ
- 等式・一般不等式などbounds以外の制約が本質
- 離散・カテゴリparameter
- 強い不連続や、再評価不能なnoise
- 大域最適性certificateが必要
- 小さな無制約問題で、良いJacobianがありLMが明確に適している

### LM・TRF・dogboxの条件付き比較

| 状況 | まず比較する候補 | 理由 |
|---|---|---|
| 小規模・無制約・残差数が変数数以上 | LM | boundsとsparse Jacobianは扱えないが、通常は効率が良い |
| boundsあり、またはlarge sparse | TRF | bounds距離、反射方向、sparse trust solverを利用できる |
| 小規模bounds付き、Jacobianがfull rank | dogbox | rectangular trust regionが合う場合がある |
| rank deficiencyが強い | TRFを中心に診断 | dogboxは遅くなりやすく、TRFのLSMR regularizationを検討できる |
| bounds以外の一般制約 | constrained NLP | least-squares APIの適用範囲を超える |

## うまくいったサインと切替サイン

SciPyの戻り値では、`success`だけでなく次を読みます。

- `cost`: residual二乗和の半分。統計的妥当性そのものではない
- `fun`: 観測ごとのresidual。patternや外れ値を確認する
- `optimality`: boundsを考慮した一階optimality measure
- `active_mask`: lower boundは`-1`、freeは`0`、upper boundは`1`
- `nfev` / `njev`: residualとJacobianの評価回数
- `status` / `message`: `gtol`、`ftol`、`xtol`、budgetのどれで止まったか

切替サイン:

- `optimality`が下がらない → Jacobian、scale、rankを確認
- 多数のparameterが予想外のboundへ張り付く → bounds、model、identifiabilityを見直す
- `nfev`が大きく数値Jacobianが支配的 → analytic Jacobianや`jac_sparsity`を検討
- sparse problemなのにdense memoryが膨らむ → sparse return typeと`tr_solver`を確認
- 異なる初期値で解が大きく変わる → local methodとしてmulti-startや別modelを検討
- 一般制約違反が残る → SLSQP、interior-point、trust-constrなどへ

`active_mask`はTRFがstrictly feasibleな反復点を作るため、最終点がboundに十分近いかをtoleranceで判定した値です。境界の厳密な数学的証明として単独利用しません。

## Python例

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
    gtol=1e-10,
)

print("x:", result.x)
print("cost:", result.cost)
print("optimality:", result.optimality)
print("active bounds:", result.active_mask)
print("evaluations:", result.nfev, result.njev)
print("termination:", result.status, result.message)
```

この問題の無制約解は`[1, 1]`ですが、`x[1] >= 1.5`により実行不能です。TRFは境界上の局所解を返します。結果を読むときは、`x[1]`がboundに近いこと、`active_mask`、residual pattern、`optimality`を一緒に確認します。

## コラム: defaultは推薦順位ではない

libraryのdefaultには、APIが対象とするproblem classで広く安全に動くこと、optionを省略しても破綻しにくいこと、保守可能な実装があることなど複数の理由があります。個別instanceで最速・最高精度という意味ではありません。

SciPyでは`least_squares`のdefaultがTRFです。一方、`curve_fit`は無制約ならLM、boundsを渡すとTRFをdefaultにします。さらに一般scalar目的の`minimize(method=None)`では、boundsとconstraintsの有無に応じてBFGS、L-BFGS-B、SLSQPが選ばれます。同じ「SciPyのdefault」でも、APIとproblem contractが異なります。

## 次に読む

残差・weight・識別可能性の全体像は[非線形最小二乗とLevenberg–Marquardt法](#/learn/least-squares)、純粋なGauss–Newton近似は[Gauss–Newton法](#/learn/gauss-newton)、一般の大規模trust-region Newton法は[Trust-Region Krylov](#/learn/trust-krylov)で確認してください。
