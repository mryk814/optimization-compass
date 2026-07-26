---
content_id: admm-qp
kind: method
method_id: M_ADMM_QP
title_ja: Operator-splitting QP（ADMM型）
title_en: ADMM / Operator-Splitting QP
summary: 凸二次計画（convex QP）を固定した分割構造で反復し、同じ線形系の因数分解を使い回しながらoperator splittingで解く専用solverの方式です。
source_ids: [S012, S062, S055, S010]
prerequisites: [concept.convexity]
related_ids: [admm, lp-qp-conic, proximal-gradient]
aliases: [/learn/admm-qp]
visualization_ids: [repeated-mpc-qp-warm-start, repeated-mpc-qp-cold-start]
comparison_ids: [COMPARE_REPEATED_MPC_QP_WARM_START]
status: published
last_reviewed: 2026-07-26
---

凸二次計画（convex QP）を固定した分割構造で反復し、同じ線形系の因数分解を使い回しながらoperator splittingで解く専用solverの方式です。

## 何を固定して反復するか

[ADMM](#/learn/admm)は$f$と$g$の分け方を問題ごとに設計する汎用framework ですが、QP専用solverは分割構造をあらかじめ固定します。代表形は

$$
\min_x \frac{1}{2}x^TPx+q^Tx\quad\text{subject to}\quad l\le Ax\le u
$$

$P\succeq0$なら凸QPです。
OSQPはこの形をそのまま受け取り、$x$と補助変数$z=Ax$を分けて交互に更新します。
設計上の自由度を減らす代わりに、同じKKT行列を反復全体で固定して使えるようにしています。

## 因数分解を1回で使い回す仕組み

各反復は次を繰り返します。

1. $x$を更新する線形系を解く（KKT行列は$\rho$を固定する限り不変）
2. $z$を$[l,u]$へprojectionする
3. dual変数を更新する

$P$・$A$・penalty parameter $\rho$が固定なら、KKT行列は反復間で変わりません。
最初の反復でfactorization（Choleskyや$LDL^T$）を1度だけ計算します。
以降の反復では前進後退代入だけで済ませられます。
これがinterior-point法のように、反復ごとに行列を作り直す方式との大きな違いです。

## まず確認すること

operator splittingは1反復が軽く、warm startや同じ問題構造の逐次再解に向きます。
例として、model predictive controlやportfolio rebalancingの定期再最適化があります。
一方、高精度な最適解へ収束させるには反復数がかさむことがあります。
厳密なbasis・certificate・高いduality gap精度が要る場合は、[primal-dual barrier法](#/learn/barrier-lp-qp)など別方式を検討します。

同じ疎構造のQPを繰り返し中精度で解くなら、factorization再利用の利点が大きくなります。

## 向いている条件

| 条件 | 理由 |
|---|---|
| 凸QP（$P\succeq0$）として明示できる | 分割構造がQPの標準形に依存するため |
| 疎な係数行列 | factorizationとmatrix-vector積を軽くできるため |
| 同じ構造のQPを繰り返し解く | KKT行列とfactorizationを使い回せるため |
| 中精度で運用上十分 | primal/dual residualの収束が漸近的なため |

## 避ける／切り替える条件

- 非凸QPを凸として誤って扱っている
- $\rho$やscalingが悪く残差が一方だけ停滞する
- 高精度なcertificateやexact basisが必要
- 制約や目的が線形・二次形式に収まらないnonlinear構造

## Python

次は箱型制約QPをADMM型反復で解く教育用の例です。
対象は$\min_x \frac{1}{2}x^TPx+q^Tx$ subject to $l\le x\le u$です。
$P+\rho I$のCholesky因数分解を1回だけ計算し、反復全体で使い回します。

```python
import numpy as np


def solve_box_qp_admm(
    p: np.ndarray,
    q: np.ndarray,
    lower: np.ndarray,
    upper: np.ndarray,
    rho: float = 1.0,
    n_iter: int = 200,
) -> tuple[np.ndarray, np.ndarray, float, float]:
    n = q.shape[0]
    factor = np.linalg.cholesky(p + rho * np.eye(n))  # 反復間で使い回す
    x = np.zeros(n)
    z = np.zeros(n)
    y = np.zeros(n)
    for _ in range(n_iter):
        rhs = -q + rho * (z - y)
        w = np.linalg.solve(factor, rhs)
        x = np.linalg.solve(factor.T, w)
        z_prev = z
        z = np.clip(x + y, lower, upper)
        y = y + x - z
    primal_residual = float(np.linalg.norm(x - z))
    dual_residual = float(rho * np.linalg.norm(z - z_prev))
    return x, z, primal_residual, dual_residual


p = np.array([[4.0, 1.0], [1.0, 2.0]])
q = np.array([1.0, 1.0])
lower = np.array([-1.0, -1.0])
upper = np.array([1.0, 1.0])

x, z, primal_residual, dual_residual = solve_box_qp_admm(p, q, lower, upper)
print(x, z, primal_residual, dual_residual, 0.5 * x @ p @ x + q @ x)
```

より一般の$Ax$を含む形やconic制約を扱う場合は、[OSQP公式ドキュメント](https://osqp.org/docs/)を確認します。
成熟したwarm startやpresolveを使う場合も同様です。
利用versionのAPIと`default parameter`は、公式referenceで確認します。

## 診断値

- primal residual（$\|Ax-z\|$相当）
- dual residual
- objective value
- $\rho$（penalty parameter）とscaling
- iteration数
- factorization再利用回数

## 失敗・切替の兆候

- `primal residual`／`dual residual`の一方だけが停滞する
- infeasibleまたはunboundedの証明が返る
- 係数のscaleが桁違いで数値warningが出る
- 同じ精度要求に対し反復数が増え続ける
- 非凸な$P$を凸QPとして与えてしまっている

## 反復MPCでwarm startを読む

[warm startのTrace](#/traces/repeated-mpc-qp-warm-start)と[cold startのTrace](#/traces/repeated-mpc-qp-cold-start)は、同じMPC QPを周期ごとに解く固定教材です。
[warm startの比較](#/compare/COMPARE_REPEATED_MPC_QP_WARM_START)では、問題・bounds・残差・deadlineの判定規則を固定します。
変えるのは、前周期の解を再利用するかどうかだけです。

ここで読むのは、各周期の残差とdeadline余裕です。
CPU・OS・linear algebra backend・実装固有のcacheやjitterを測ったbenchmarkではありません。
warm startが初回解や実機latencyを必ず改善するとも主張しません。

## 次に読む

分割構造を自分で設計したい場合は[ADMM](#/learn/admm)を確認します。
単一のproxで済む問題は[近接勾配法](#/learn/proximal-gradient)へ進みます。
LP・QP・conic全体の位置付けは[LP・QP・錐最適化](#/learn/lp-qp-conic)で確認できます。
