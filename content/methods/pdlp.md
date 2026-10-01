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
last_reviewed: 2026-09-30
---

行列因数分解を避け、行列ベクトル積だけを使う一次法（PDHG）をLPへ適用し、巨大疎LPを扱う近年の方向です。

## 30秒でつかむ

大きな連立方程式を一度に解く代わりに、制約側と変数側から小さな修正を交互に返します。

PDLPは、基底やKKT行列の因数分解を毎回作りません。
主と双対の残差を、行列ベクトル積で少しずつ減らします。

- 見ているもの: 主残差、双対残差、duality gap
- 動かしているもの: 主 variable $x$、双対 variable $y$、一歩の係数、再始動
- 前進の判断: 残差とgapが同時に減り、許容誤差へ近づくこと
- 恐れていること: 悪い条件数、一歩の係数不足、高精度要求、実行不可能や非有界の見落とし

## 一手の意味

### なぜ因数分解を避けるのか

[Primal simplex](#/learn/primal-simplex)は基底行列を更新します。
[主-双対 barrier法](#/learn/barrier-lp-qp)は、中心pathのNewton 一歩でKKT行列を扱います。
超大規模な疎問題では、因数分解のfill-inがメモリを圧迫する場合があります。
計算時間への影響も無視できません。

PDHG（主-双対 hybrid 勾配）は、$Ax$や$A^Ty$の行列ベクトル積で反復を進めます。
因数分解を避けるため、巨大疎LPでも同じ更新形式を保てます。
Google OR-ToolsのPDLPは、この方向を実装したソルバーです（S078）。

### PDHG反復が何をしているか

LP標準形 $\min_x c^Tx$ subject to $Ax=b,\ x\ge0$ は、次のsaddle point問題として書けます。

$$
\min_{x\ge0}\max_{y}\; c^Tx+y^T(b-Ax)
$$

PDHGは$x$と$y$を交互に更新します。
$y$側の更新では、$x$を $2x_{k+1}-x_k$ へ外挿（extrapolation）します。

$$
x_{k+1}=\Pi_{x\ge0}\left(x_k-\tau\left(c-A^Ty_k\right)\right)
$$

$$
y_{k+1}=y_k+\sigma\left(b-A\left(2x_{k+1}-x_k\right)\right)
$$

$\Pi_{x\ge0}$は非負制約への射影で、閉形式（clip）で計算できます。
一歩の係数 $\tau,\sigma$は、$A$のスペクトルノルム$L=\|A\|_2$を使って決めます。
基本形では$\tau\sigma L^2<1$を満たすように保守的な値を選びます。

上段では、最初は均等だった$x$が最小費用の$x_2$へ移ります。
下段では、停止判定に使う三つの量を同じ反復軸で追います。

![3変数のsimplex LPをPDHGで100回更新した固定実行。上段ではx1、x2、x3へ均等だった質量が、反復5、20、100を経て最小costのx2へ集まる。下段ではprimal residual、dual residual、primalとdualの目的値差を対数軸で示す。初期のdual residualは0だが目的値差は2であり、一つの量だけでは収束を判定できない。](./media/pdlp-residual-execution.svg "同じPDHG実行からprimal変数と三つの停止判定量を生成した固定教材")

初期点は主と双対のfeasibility 残差がともに0です。
しかし、主と双対の目的値差は2なので、まだ最適ではありません。
一つの残差だけでなく、feasibilityと目的値差を同時に確認する必要があります。

> 固定した3変数equality LPの100反復です。
> 最終解は `x = (0, 1, 0)` 付近、目的値は `2.000 → 1.000` です。
> 図の目的値差はraw absolute differenceです。
> 実行不可能な途中反復では、双対 界や証明を意味しません。
> 尺度調整、再始動、infeasibility 証明は含みません。
> PDLP実装一般の性能も示していません。

## 小さな例

Python節の $c=(3,1,2)$、$x_1+x_2+x_3=1$ を使います。
$x=(1/3,1/3,1/3)$、$y=0$、$\tau=\sigma=0.9/\sqrt3$ から更新します。

| 反復 | $x_2$（$x_1=x_3=0$） | 主残差 | 双対残差 | 目的値差 |
|---|---:|---:|---:|---:|
| 1 | 0.0000 | 1.0000 | 0.0392 | 1.0392 |
| 2 | 0.0204 | 0.9796 | 0.5377 | 1.5173 |
| 3 | 0.2998 | 0.7002 | 0.7563 | 1.4566 |

途中の $x$ は等式制約を満たさない場合があります。
その時点の目的値差を、大域最適性の証明として扱いません。

## 向く条件・避ける条件

### 許容誤差をどう読むか

PDHGは頂点（基底）を直接たどるのではなく、次の3量を同時に小さくします。

1. 主 feasibility 残差
2. 双対 feasibility 残差
3. duality gap

基本的なPDHGの収束rateは$O(1/k)$で、高精度ほど反復数がかさむ場合があります。
一方、実用PDLPはdiagonal preconditioning／adaptive 一歩の係数／再始動などを組み合わせます。
高い相対精度へ到達した実例もあるため、PDLPを中精度だけのソルバーとはみなしません。

simplex系とPDLPでは、停止条件と返す解の形が異なります。
同じ許容誤差$10^{-8}$でも、その意味が同じとは限りません。
主／双対 infeasibilityとgapの定義を揃えて比較します。
absolute／relative 尺度調整も確認します。
因数分解のメモリ、必要精度、反復時間を同じ問題で確認して選びます。

### 向いている条件

- 超大規模・疎なLPで因数分解のメモリが問題になる
- 行列ベクトル積が安価（GPU等での並列化を含む）
- 必要精度まで残差とgapを減らせる反復時間が許容できる
- 初期解の再利用やdiagonal 尺度調整を活用できる

### 避ける／切り替える条件

- 基底を持つ頂点解や疎な頂点解が必要（[主 simplex](#/learn/primal-simplex)や[双対 simplex](#/learn/dual-simplex)を検討）
- 問題が小〜中規模で密であり、因数分解の費用が許容範囲内
- 数値条件数が悪くpreconditioningなしでは収束が遅い
- 高精度な双対 感度を即座に必要とする

## Python

次はequality制約LP $\min_x c^Tx$ subject to $Ax=b,\ x\ge0$ の教育用PDHG反復です。
制約は単純なsimplex $x_1+x_2+x_3=1$ とします。
一歩の係数は$A$のスペクトルノルムから決めます。

```python
from math import sqrt


costs = (3.0, 1.0, 2.0)
rhs = 1.0
tau = sigma = 0.9 / sqrt(3.0)
primal = [1.0 / 3.0] * 3
dual = 0.0
history = []

for iteration in range(101):
    primal_residual = abs(sum(primal) - rhs)
    reduced_costs = [cost - dual for cost in costs]
    dual_residual = sqrt(sum(min(value, 0.0) ** 2 for value in reduced_costs))
    primal_objective = sum(cost * value for cost, value in zip(costs, primal))
    objective_difference = abs(primal_objective - rhs * dual)
    history.append(
        (iteration, tuple(primal), primal_residual, dual_residual, objective_difference)
    )
    if iteration == 100:
        break

    primal_next = [
        max(0.0, value - tau * (cost - dual))
        for value, cost in zip(primal, costs)
    ]
    extrapolated_sum = sum(
        2.0 * next_value - value
        for next_value, value in zip(primal_next, primal)
    )
    dual += sigma * (rhs - extrapolated_sum)
    primal = primal_next

print(history[0])
print(history[-1])
```

最終行では$x$が`(0, 1, 0)`付近へ近づきます。
これは$c$が最小の座標に質量が寄る解です。
三つの判定量が同時に小さいことも確認します。

実務では、再始動／diagonal 尺度調整／収束判定をソルバーへ任せます。
[OR-Tools Linear Optimization公式ドキュメント](https://developers.google.com/optimization/lp)で利用versionのAPIと挙動を確認してください。

## 診断値

- 主 feasibility 残差（$\|Ax-b\|$）
- 双対 feasibility 残差
- duality gap
- 一歩の係数 $\tau,\sigma$と$A$のスペクトルノルム推定
- 反復数
- 再始動発生の有無

## 失敗・切替の兆候

- 反復数を増やしても残差が縮まらない → coefficient 尺度、preconditioning、一歩の係数を確認する
- 実行不可能または非有界の兆候が出ているのに残差だけを見て見落とす → termination 理由とproblem 状態を分けて確認する
- coefficient 尺度が極端で一歩の係数の見積もりが保守的すぎる／不足する → 尺度調整とスペクトルノルム推定を見直す
- 基底を使う後段処理や高精度な感度が必要になり、返された解では不足する → simplex系を検討する
- 再始動を繰り返しても収束が遅い → barrier法やsimplexとの費用、精度、メモリを比較する

## 次に読む

Newton 一歩で同じLP標準形を解く方式は[主-双対 barrier法](#/learn/barrier-lp-qp)で確認できます。
基底を保った再最適化は[主 simplex](#/learn/primal-simplex)が扱います。
一次法全体での位置付けは[非滑らか・複合凸最適化の選び分け](#/learn/family.composite-convex)で確認できます。

- 問題の形を確認する: [線形計画](#/formulations/PA017)
