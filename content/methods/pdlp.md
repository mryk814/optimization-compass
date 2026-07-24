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
last_reviewed: 2026-07-24
---

行列因数分解を避け、行列ベクトル積だけを使う一次法（PDHG）をLPへ適用し、巨大疎LPを扱う近年の方向です。

## 30秒でつかむ

PDLPは、basisやKKT行列のfactorizationを毎回作る代わりに、primalとdualのresidualを行列ベクトル積で少しずつ減らします。

- 見ているもの: primal residual、dual residual、duality gap
- 動かしているもの: primal variable $x$、dual variable $y$、step size、restart
- 前進の判断: residualとgapが同時に減り、許容誤差へ近づくこと
- 恐れていること: 悪いconditioning、step size不足、高精度要求、infeasibleやunboundedの見落とし

## なぜ因数分解を避けるのか

[Primal simplex](#/learn/primal-simplex)はbasis行列を更新します。
[primal-dual barrier法](#/learn/barrier-lp-qp)は、中心pathのNewton stepでKKT行列を扱います。
超大規模な疎問題では、factorizationのfill-inがmemoryと計算時間を圧迫する場合があります。

PDHG（primal-dual hybrid gradient）は、$Ax$や$A^Ty$の行列ベクトル積で反復を進めます。
factorizationを避けるため、巨大疎LPまで同じ更新形式を保てます。
Google OR-ToolsのPDLPは、この方向を実装したsolverです（S078）。

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

$\Pi_{x\ge0}$は非負制約へのprojectionで、閉形式（clip）で計算できます。
step size $\tau,\sigma$は、$A$のスペクトルノルム$L=\|A\|_2$を使って決めます。
基本形では$\tau\sigma L^2<1$を満たすように保守的な値を選びます。

## 許容誤差をどう読むか

PDHGは頂点（basis）を直接たどるのではなく、次の3量を同時に小さくします。

1. primal feasibility residual
2. dual feasibility residual
3. duality gap

基本的なPDHGの収束rateは$O(1/k)$で、高精度ほど反復数がかさむ場合があります。
一方、実用PDLPはdiagonal preconditioning／adaptive step size／restartなどを組み合わせます。
高い相対精度へ到達した実例もあるため、PDLPを中精度だけのsolverとはみなしません。

simplex系とPDLPでは、停止条件と返す解の形が異なります。
同じ許容誤差$10^{-8}$でも、primal／dual infeasibilityとgapの定義・absolute／relative scalingを揃えて比較します。
factorizationのmemory、必要精度、反復時間を同じ問題で確認して選びます。

## 向いている条件

- 超大規模・疎なLPでfactorizationのmemoryが問題になる
- 行列ベクトル積が安価（GPU等での並列化を含む）
- 必要精度までresidualとgapを減らせる反復時間が許容できる
- warm startやdiagonal scalingを活用できる

## 避ける／切り替える条件

- basisを持つ頂点解や疎な頂点解が必要（[primal simplex](#/learn/primal-simplex)や[dual simplex](#/learn/dual-simplex)を検討）
- 問題が小〜中規模で密であり、factorizationのcostが許容範囲内
- 数値conditioningが悪くpreconditioningなしでは収束が遅い
- 高精度なdual sensitivityを即座に必要とする

## Python

次はequality制約LP $\min_x c^Tx$ subject to $Ax=b,\ x\ge0$ の教育用PDHG反復です。
制約は単純なsimplex $x_1+x_2+x_3=1$ とします。
step sizeは$A$のスペクトルノルムから保守的に決めています。

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

$x$は$[0,1,0]$付近へ近づきます。
これは$c$が最小の座標に質量が寄る解です。
あわせて、`primal_residual`が反復とともに小さくなることを確認します。

実務では、restart／diagonal scaling／収束判定をsolverへ任せます。
[OR-Tools Linear Optimization公式ドキュメント](https://developers.google.com/optimization/lp)で利用versionのAPIと挙動を確認してください。

## 診断値

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
- basisを使う後段処理や高精度なsensitivityが必要になり、返された解では不足する → simplex系を検討する
- restartを繰り返しても収束が遅い → barrier法やsimplexとのcost、精度、memoryを比較する

## 次に読む

Newton stepで同じLP標準形を解く方式は[primal-dual barrier法](#/learn/barrier-lp-qp)で確認できます。
basisを保った再最適化は[primal simplex](#/learn/primal-simplex)が扱います。
一次法全体での位置付けは[非滑らか・複合凸最適化の選び分け](#/learn/family.composite-convex)で確認できます。
