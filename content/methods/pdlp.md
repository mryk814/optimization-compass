---
content_id: pdlp
kind: method
method_id: M_PDLP
title_ja: PDHG型一次法LP（PDLP）
title_en: Primal-Dual Hybrid Gradient for LP
summary: 行列因数分解を避け、行列ベクトル積だけを使う一次法（PDHG）をLPへ適用し、巨大疎LPを扱う近年の方向です。
source_ids: [S078, S055, S016]
prerequisites: [concept.convexity]
related_ids: [barrier-lp-qp, primal-simplex, family.composite-convex]
aliases: [/learn/pdlp]
status: published
last_reviewed: 2026-07-18
---

行列因数分解を避け、行列ベクトル積だけを使う一次法（PDHG）をLPへ適用し、巨大疎LPを扱う近年の方向です。

## 30秒でつかむ

PDLPは、basisやKKT行列のfactorizationを毎回作る代わりに、primalとdualのresidualを行列ベクトル積で少しずつ減らします。

- 見ているもの: primal residual、dual residual、duality gap
- 動かしているもの: primal variable $x$、dual variable $y$、step size、restart
- 前進の判断: residualとgapが同時に減り、許容誤差へ近づくこと
- 恐れていること: 悪いconditioning、step size不足、高精度要求、infeasibleやunboundedの見落とし

## なぜ因数分解を避けるのか

[Primal simplex](#/learn/primal-simplex)や[primal-dual barrier法](#/learn/barrier-lp-qp)は、basisの更新や中心pathのNewton stepでKKT行列やbasis行列のfactorizationを必要とします。問題が超大規模かつ疎になると、このfactorizationのfill-inがmemoryを圧迫し、支配的なcostになることがあります。PDHG（primal-dual hybrid gradient）をLPへ適用する方向は、$Ax$や$A^Ty$といった行列ベクトル積だけで反復を進め、factorizationそのものを避けます。Google OR-ToolsのPDLPはこの方向を実装した代表例です（S078）。

## PDHG反復が何をしているか

LP標準形 $\min_x c^Tx$ subject to $Ax=b,\ x\ge0$ は、次のsaddle point問題として書けます。

$$
\min_{x\ge0}\max_{y}\; c^Tx+y^T(b-Ax)
$$

PDHGは$x$の勾配stepと$y$の勾配stepを交互に行い、$x$側の更新に使う$y$を1歩先の値で外挿（extrapolation）します。

$$
x_{k+1}=\Pi_{x\ge0}\left(x_k-\tau\left(c-A^Ty_k\right)\right)
$$

$$
y_{k+1}=y_k+\sigma\left(b-A\left(2x_{k+1}-x_k\right)\right)
$$

$\Pi_{x\ge0}$は非負制約へのprojectionで、閉形式（clip）で計算できます。step size $\tau,\sigma$は行列$A$のスペクトルノルム$L=\|A\|_2$から$\tau\sigma L^2<1$を満たすように保守的に決めます。

## 許容誤差をどう読むか

simplexは頂点（basis）へ厳密に到達して停止しますが、PDHGはprimal feasibility residual、dual feasibility residual、duality gapを漸近的に減らす一次法です。多くの実装で反復数に対する収束は$O(1/k)$程度にとどまり、高精度な解へ絞り込むには反復数がかさみます。そのため、同じ「許容誤差$10^{-8}$」でも、simplexのbasisベースの停止条件とPDHGのresidualベースの停止条件は意味が異なります。中精度で十分な超大規模疎LP、またはfactorizationがmemoryに収まらない規模の問題が対象になります。

## 向いている条件

- 超大規模・疎なLPでfactorizationのmemoryが問題になる
- 行列ベクトル積が安価（GPU等での並列化を含む）
- 中精度の解で運用上十分
- warm startやdiagonal scalingを活用できる

## 避ける／切り替える条件

- 厳密なbasisやexact certificateが必要（[primal simplex](#/learn/primal-simplex)や[dual simplex](#/learn/dual-simplex)を検討）
- 問題が小〜中規模で密であり、factorizationのcostが許容範囲内
- 数値conditioningが悪くpreconditioningなしでは収束が遅い
- 高精度なdual sensitivityを即座に必要とする

## Python

次はequality制約LP $\min_x c^Tx$ subject to $Ax=b,\ x\ge0$ を、単純なsimplex制約（$x_1+x_2+x_3=1$）で解く教育用のPDHG反復です。step sizeは$A$のスペクトルノルムから保守的に決めています。

```python
import numpy as np


def project_nonneg(x: np.ndarray) -> np.ndarray:
    return np.maximum(x, 0.0)


a = np.array([[1.0, 1.0, 1.0]])
b = np.array([1.0])
c = np.array([3.0, 1.0, 2.0])

lipschitz = np.linalg.norm(a, ord=2)
tau = 0.9 / lipschitz
sigma = 0.9 / lipschitz

x = np.full(3, 1.0 / 3.0)
y = np.zeros(1)

for _ in range(5_000):
    x_next = project_nonneg(x - tau * (c - a.T @ y))
    y = y + sigma * (b - a @ (2.0 * x_next - x))
    x = x_next

primal_residual = float(np.linalg.norm(a @ x - b))
print(x, float(c @ x), primal_residual)
```

$x$は$[0,1,0]$付近（$c$が最小の座標に質量が寄る解）に近づき、`primal_residual`が反復とともに小さくなることを確認します。実務規模の疎LP、restart、diagonal scaling、収束判定の詳細は自分で再現せず、[OR-Tools Linear Optimization公式ドキュメント](https://developers.google.com/optimization/lp)で利用versionのAPIと挙動を確認します。

## 最初に見る診断値

- primal feasibility residual（$\|Ax-b\|$）
- dual feasibility residual
- duality gap
- step size $\tau,\sigma$と$A$のスペクトルノルム推定
- iteration数
- restart発生の有無

## 失敗・切替の兆候

- iteration数を増やしてもresidualが縮まらない → coefficient scale、preconditioning、step sizeを確認する
- infeasibleまたはunboundedの兆候が出ているのに残差だけを見て見落とす → termination reasonとproblem statusを分けて確認する
- coefficient scaleが極端でstep sizeの見積もりが保守的すぎる／不足する → scalingとスペクトルノルム推定を見直す
- 高精度なbasisやsensitivityが必要になり中精度解では不足する → simplex系を検討する
- restartを繰り返しても収束が遅い → barrier法やsimplexとのcost、精度、memoryを比較する

同じLP標準形をNewton stepで解く方式は[primal-dual barrier法](#/learn/barrier-lp-qp)、basisを保った再最適化は[primal simplex](#/learn/primal-simplex)、非滑らか・複合凸最適化全体での一次法の位置付けは[非滑らか・複合凸最適化の選び分け](#/learn/family.composite-convex)で確認できます。
