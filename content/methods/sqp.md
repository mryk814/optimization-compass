---
content_id: sqp
kind: method
method_id: M_SQP
title_ja: 逐次二次計画法（SQP）
title_en: Sequential Quadratic Programming
summary: 各反復で目的関数の二次modelと制約の線形化からQP subproblemを解き、探索方向を得る制約付きNLPのアルゴリズム枠組みです。
source_ids: [S030, S056, S064]
prerequisites: [bfgs]
related_ids: [slsqp, interior-point-nlp, family.constrained-nlp]
status: published
last_reviewed: 2026-07-18
---

各反復で目的関数の二次modelと制約の線形化からQP subproblemを解き、探索方向を得る制約付きNLPのアルゴリズム枠組みです。

## 各反復で何を解いているか

現在点$x_k$で目的関数を二次modelに、制約を線形に近似します。探索方向$p$を求めるQP subproblemは

$$
\min_{p} \quad \nabla f(x_k)^T p + \frac{1}{2} p^T B_k p
$$

を、線形化した等式・不等式制約のもとで解く形になります。$B_k$はLagrangianのHessian、またはBFGS型の準Newton近似です。QPを解くとstepの方向$p_k$と、制約のLagrange乗数の推定値が同時に得られます。この乗数は次の反復のLagrangian Hessian近似や停止判定に使われます。

## 何を見て停止するか

SQPはKarush-Kuhn-Tucker（KKT）条件、つまり

- stationarity（Lagrangian勾配が十分小さい）
- primal feasibility（制約が満たされている）
- dual feasibility（不等式乗数の符号条件）
- complementarity（活性でない制約の乗数がゼロに近い）

への収束を目安に停止判定します。二次収束が理論的に期待できるのは局所的にKKT点近傍かつ制約想定（constraint qualification）が成り立つ場合で、非凸問題では見つかる点が局所解にとどまります。

## Stepを受理する条件

QP subproblemの解をそのまま採用すると、目的が悪化したり制約違反が増えたりする場合があります。実用的なSQP実装は、objective improvementとconstraint violationを同時に評価するmerit関数（$\ell_1$penaltyなど）やfilter法でstepを受理・棄却し、必要ならstep lengthを縮小します。この調整（globalization）がないと、QP近似が良くない領域で発散する可能性があります。

SQPは一つのアルゴリズムではなく、$B_k$の更新方法、QP solverの選び方、merit関数かfilterかというglobalization方針の組み合わせで多くの実装系統に分かれます。[SLSQP](#/learn/slsqp)はその一実装であり、SQP一般に共通する挙動と、SLSQPというsoftware系統固有の停止条件・sign conventionは区別して確認します。

## 向いている条件

- 目的・制約が滑らかで、中規模までの変数数
- bounds・等式・不等式が混在する制約付きNLP
- KKT残差や制約違反など、収束の診断値を確認したい
- 似た問題を繰り返し解き、warm startを活用できる
- gradientとconstraint Jacobianが精度良く得られる

## 避ける／切り替える条件

- 離散変数を含む、または制約が不連続
- 勾配・Jacobianに強いnoiseが乗る
- 変数や制約のscaleが極端に異なる
- infeasibleな初期点からconstraint qualificationが崩れている

大規模疎なNLPでは[Interior-point NLP](#/learn/interior-point-nlp)を、制約付きNLP全体の選び分けは[制約付き非線形最適化の選び分け](#/learn/family.constrained-nlp)を確認します。

## Python

```python
import numpy as np
from scipy.optimize import minimize


def objective(x: np.ndarray) -> float:
    return float((x[0] - 1.0) ** 2 + 2.0 * (x[1] - 2.0) ** 2)


def gradient(x: np.ndarray) -> np.ndarray:
    return np.array([2.0 * (x[0] - 1.0), 4.0 * (x[1] - 2.0)])


def inequality(x: np.ndarray) -> float:
    return float(x[0] + x[1] - 2.0)


result = minimize(
    objective,
    x0=np.array([0.5, 1.5]),
    jac=gradient,
    method="SLSQP",
    constraints=[{"type": "ineq", "fun": inequality}],
    options={"ftol": 1e-10, "maxiter": 200},
)

print(result.success, result.x, result.fun, inequality(result.x), result.message)
```

`inequality(result.x)`が0以上ならSciPyの規約上feasibleです。ここではSLSQPというSQPの一実装を使っており、options名や制約の符号規約は実装固有です。[公式SciPyリファレンス](https://docs.scipy.org/doc/scipy/reference/optimize.minimize-slsqp.html)で利用versionに対応する説明を確認します。

## 診断値

- constraint_violation（最大制約違反量）
- stationarity（Lagrangian勾配residual）
- complementarity
- factorization_status
- QP subproblemのstatusまたはiteration数
- function / gradient / Jacobian evaluation数

::: warning
`success=True`はsolver内部の停止判定を満たしたことを示すだけです。実際のconstraint_violationとstationarityを自分で再計算し、SQP一般の理論と使用中の実装固有の挙動を混同しないようにします。
:::

## 失敗・切替の兆候

- infeasible_start（初期点から実行可能領域に入れない）
- constraint_qualification_failure（制約想定が崩れている）
- bad_jacobian（Jacobianが不正確、または有限差分noiseが大きい）
- poor_scaling（変数・制約のscaleが極端）
- KKT残差が反復を重ねても減らない
- 正則化やstep縮小の反復回数が増大し続ける

## 次に読む

Hessian近似の基本となる準Newton法は[BFGS法](#/learn/bfgs)、同じSQP枠組みの具体的な一実装は[SLSQP](#/learn/slsqp)で確認できます。
