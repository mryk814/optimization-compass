---
content_id: admm-qp
kind: method
method_id: M_ADMM_QP
title_ja: Operator-splitting QP（ADMM型）
title_en: ADMM / Operator-Splitting QP
summary: 凸QPを固定した分割構造で反復し、同じ線形系の因数分解を使い回しながらoperator splittingで解く専用solverの方式です。
source_ids: [S012, S062, S055, S010]
prerequisites: [concept.convexity]
related_ids: [admm, lp-qp-conic, proximal-gradient]
aliases: [/learn/admm-qp]
status: published
last_reviewed: 2026-07-16
---

凸QPを固定した分割構造で反復し、同じ線形系の因数分解を使い回しながらoperator splittingで解く専用solverの方式です。

## 一般ADMMとどう違うか

[ADMM](#/learn/admm)は$f$と$g$の分け方を問題ごとに設計する汎用framework ですが、QP専用solverは分割構造をあらかじめ固定します。代表形は

$$
\min_x \frac{1}{2}x^TPx+q^Tx\quad\text{subject to}\quad l\le Ax\le u
$$

で、$P\succeq0$なら凸QPです。OSQPはこの形をそのまま受け取り、$x$と補助変数$z=Ax$を分けて交互に更新します。設計上の自由度を減らす代わりに、同じKKT行列を反復全体で固定して使えるようにしています。

## 因数分解を1回で使い回す仕組み

各反復は次を繰り返します。

1. $x$を更新する線形系を解く（KKT行列は$\rho$を固定する限り不変）
2. $z$を$[l,u]$へprojectionする
3. dual変数を更新する

$P$、$A$、penalty parameter $\rho$が固定なら、KKT行列は反復間で変わりません。そのため最初の反復で1度だけfactorization（Cholesky や $LDL^T$）を計算し、以降の反復では前進後退代入だけで済ませられます。これがinterior-point法のように反復ごとに行列を作り直す方式との大きな違いです。

## 中精度で十分な場合と高精度が必要な場合

operator splittingは1反復が軽く、warm startや同じ問題構造の逐次再解（model predictive control、portfolio rebalancingの定期再最適化など）に強い一方、高精度な最適解へ収束させるには反復数がかさむことがあります。厳密なbasisやcertificate、高いduality gap精度が要る場合は[primal-dual barrier法](#/learn/barrier-lp-qp)など別方式を検討します。逆に、同じ疎構造のQPを繰り返し中精度で解くならfactorization再利用の利点が大きくなります。

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

次は箱型制約QP $\min_x \frac{1}{2}x^TPx+q^Tx$ subject to $l\le x\le u$ をADMM型反復で解く教育用の例です。$P+\rho I$のCholesky因数分解を1回だけ計算し、反復全体で使い回します。

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

より一般の$Ax$を含む形や、conic制約、成熟したwarm start・presolveを使う場合は[OSQP公式ドキュメント](https://osqp.org/docs/)を確認します。利用versionのAPI・default parameterは公式referenceで確認します。

## 診断値

- primal residual（$\|Ax-z\|$相当）
- dual residual
- objective value
- $\rho$（penalty parameter）とscaling
- iteration数
- factorization再利用回数

## 失敗・切替の兆候

- primal residualとdual residualが片方だけ停滞する
- infeasibleまたはunboundedの証明が返る
- 係数のscaleが桁違いで数値warningが出る
- 同じ精度要求に対し反復数が増え続ける
- 非凸な$P$を凸QPとして与えてしまっている

分割構造を自分で設計したい場合は[ADMM](#/learn/admm)、単一のproxで済む問題は[近接勾配法](#/learn/proximal-gradient)、LP・QP・conic全体の位置付けは[LP・QP・錐最適化](#/learn/lp-qp-conic)で確認できます。
