---
content_id: barrier-lp-qp
kind: method
method_id: M_BARRIER_LP_QP
title_ja: Primal-dual barrier法（LP/QP）
title_en: Primal-Dual Barrier Method for LP/QP
summary: 不等式制約を対数障壁（log barrier）へ置き換え、中心パス（central path）に沿ってNewton法で進む、LP/QP専用の内点法です。
source_ids: [S016, S004, S055, S056]
prerequisites: [concept.convexity]
related_ids: [primal-simplex, dual-simplex, interior-point-nlp, lp-qp-conic, concept.linear-program, concept.convex-quadratic-program]
aliases: [/learn/barrier-lp-qp]
status: published
last_reviewed: 2026-09-30
---

不等式制約を対数障壁（log barrier）へ置き換え、中心パス（central path）に沿ってNewton法で進む、LP/QP専用の内点法です。

## 30秒でつかむ

壁に囲まれた部屋の奥にある出口へ向かうとき、壁に沿って角から角へ歩く方法があります。
壁からいつも距離をとり、部屋の真ん中寄りを通って出口へ近づく方法もあります。
後者が内点法です。壁（不等式制約）に近づくほど強く押し返す力を足して、内部にとどまります。

- **見るもの**: 主問題と双対問題の実行可能性の残差、双対ギャップ（duality gap）、障壁の強さ $\mu$
- **動かすもの**: 主変数 $x$、双対変数 $y$、余りの変数 $s$ を同時に。押し返す力 $\mu$ を少しずつ弱める
- **前進の判断**: 双対ギャップが小さくなり、残差が許容誤差以下になれば止まる

simplex法が頂点だけを渡り歩くのに対し、barrier法は領域の内部を通り、最適解へ滑らかに近づきます。

## 一手の意味

一手は、$\mu$ を固定した中心パスの条件を、Newton法で一回だけ解き進める操作です。
$x$ と $s$ を、正の領域から出ない歩幅で更新します。

LP標準形 $\min_x c^\top x$ subject to $Ax=b,\ x\ge0$ を考えます。barrier法は、非負制約を対数障壁で置き換えます。

$$
\min_x\; c^\top x-\mu\sum_i\log x_i \quad\text{subject to}\quad Ax=b
$$

$x_i$ が0に近づくと $-\log x_i$ が大きくなり、$x_i>0$ の内側に押し戻されます。$\mu>0$ を固定した最適解の集まりを、$\mu\to0$ へ動かした軌跡が中心パスです。
各 $\mu$ での最適性条件は、次の三つの式にまとまります。

$$
Ax=b,\qquad A^\top y+s=c,\qquad x_is_i=\mu\;\;(i=1,\dots,n)
$$

上から順に、主問題の等式・双対問題の等式・相補性（complementarity）の条件です。
$\mu=0$ とすれば、LPの最適性条件そのものになります。$\mu>0$ の間は $x_i$ と $s_i$ がどちらも正で、内部にとどまります。

各反復では、この三つの式を現在の点で線形化し、$x,y,s$ の変化量を同時に求めます。これがNewton方程式です。
線形化した系は対称で疎になることが多く、分解（factorization）して解きます。QPでは、目的の二次項が同じ枠組みでNewton方程式の係数行列に加わります。
反復ごとに線形系を作り直して解く点が、[operator-splitting QP](#/learn/admm-qp)のように分解を固定して使い回す方式との違いです。

$x^\top s$ が双対ギャップで、中心パス上では $n\mu$ に等しくなります。$\mu$ を下げるほどギャップが縮み、最適解に近づきます。

### simplexとの違い

primal/dual simplexは頂点（基底）を渡り歩きます。barrier法は多面体の内部を進み、頂点上の基底を直接は保ちません。

- 反復回数は問題の大きさにほぼ依存しにくい一方、一反復あたりのNewton方程式を解く仕事は重くなり得ます
- 明示的な基底を返さないため、基底が必要な後続処理（感度解析やwarm restartなど）には、crossoverで基底可能解へ変換する工程が使われる場合があります
- 停止判定は、主問題・双対問題の実行可能性の残差と双対ギャップで行います。simplexの被約費用の符号条件とは異なります

一般の非線形制約を持つ問題でのbarrier法の考え方は[非線形内点法](#/learn/interior-point-nlp)で扱います。この記事は、凸で構造の明らかなLP/QPに限ります。

## 小さな例

[線形計画](#/learn/concept.linear-program)のパン屋の問題を使います。売上 $3x_1+4x_2$ を最大にする問題を、最小化 $\min\,-3x_1-4x_2$ に直し、余りの変数 $s_1,s_2$ を足して標準形にします。
非負の変数は $x_1,x_2,s_1,s_2$ の4個なので、双対ギャップは中心パス上で $4\mu$ です。

まず、障壁の強さ $\mu$ ごとに、中心パス上の点を見ます。

| $\mu$ | 中心パス上の $(x_1,\,x_2)$ | 売上 $3x_1+4x_2$ | 双対ギャップ $4\mu$ |
|---:|---|---:|---:|
| 10 | $(2.638,\;1.855)$ | $15.33$ | $40$ |
| 1 | $(3.752,\;2.727)$ | $22.17$ | $4$ |
| 0.1 | $(3.974,\;2.970)$ | $23.80$ | $0.4$ |
| 0.01 | $(3.997,\;2.997)$ | $23.98$ | $0.04$ |

$\mu$ が大きいうちは領域の内部にあり、$\mu$ を下げるにつれて最適な頂点 $(4,\,3)$ へ寄っていきます。
どの点も可行領域の内部にあり、頂点や辺の上には乗りません。売上は $24$ に下から近づき、$24$ との差はいつも双対ギャップ以下です。

次に、実際のNewton法の歩みを見ます。$x=s=(1,1,1,1)$ と $y=0$ から出発します。各反復で $\mu$ の目標を現在の30%に下げます。
出発点は制約を満たしていません。実行可能性の残差も同時に縮めていく方式（infeasible-start）です。

| 反復 | $(x_1,\,x_2)$ | 売上 | 双対ギャップ $x^\top s$ | 主問題の残差 $\lVert Ax-b\rVert$ |
|---:|---|---:|---:|---:|
| 0 | $(1,\;1)$ | $7.0$ | $4.0$ | $14.42$ |
| 1 | $(1.779,\;1.595)$ | $11.72$ | $1.88$ | $10.07$ |
| 2 | $(3.418,\;2.545)$ | $20.44$ | $0.82$ | $2.74$ |
| 3 | $(3.977,\;2.987)$ | $23.88$ | $0.23$ | $0.00$ |
| 6 | $(4.000,\;3.000)$ | $24.00$ | $0.006$ | $0.00$ |

三回の反復で、主問題の残差が0になりました。そのあとは、双対ギャップだけが約3割ずつ縮んでいきます。
simplex法が頂点を二回渡って終わったのに対し、barrier法は同じ問題を内部の点の列で解いています。
最後に得られる点は、頂点の近くの内部の点です。頂点そのものが必要なら、crossoverで基底を復元します。

## 向く条件・避ける条件

| 条件 | 理由 |
|---|---|
| LP/QP/conicの構造が明示できる | 中心パスの議論がこれらの標準形に依存するため |
| 大規模・疎な問題 | 疎なKKT系の分解を利用できるため |
| 明確な双対ギャップで停止判定したい | 主問題・双対問題の実行可能性とギャップが直接得られるため |
| 基底を必ずしも必要としない | barrier法自体は基底を維持しないため |

避ける、または切り替える場面は次のとおりです。

- 基底やwarm startによる再最適化を頻繁に行いたい。[primal simplex](#/learn/primal-simplex)や[dual simplex](#/learn/dual-simplex)が候補です。
- 制約や目的が非線形で、LP/QPの標準形に収まらない。[非線形内点法](#/learn/interior-point-nlp)を検討します。
- 係数の尺度（scale）が極端で、数値warningが出る。単位を揃えてから解きます。
- crossoverの費用が許容できないほど大きい。頂点解が不要なら、crossoverを外せるかを確認します。

## Python

小さな例の反復を再現します。表の各行は、`print` が出す反復番号・$x_1,x_2$・売上・双対ギャップ・主問題の残差に対応します。

```python
import numpy as np
from scipy.optimize import linprog

# 最小化 c^T x  s.t.  A x = b,  x >= 0（余り変数 s1, s2 を含む標準形）
A = np.array([[3.0, 2.0, 1.0, 0.0], [1.0, 3.0, 0.0, 1.0]])
b = np.array([18.0, 13.0])
c = np.array([-3.0, -4.0, 0.0, 0.0])

x, y, s = np.ones(4), np.zeros(2), np.ones(4)  # 正の値から出発する（内点）
sigma = 0.3  # 一手で中心パスの mu をどこまで下げるか
for k in range(9):
    mu = x @ s / 4
    print(k, x[:2].round(3), round(-(c @ x), 3), round(x @ s, 4),
          round(float(np.linalg.norm(A @ x - b)), 4))
    r_primal = A @ x - b
    r_dual = A.T @ y + s - c
    r_center = x * s - sigma * mu
    # Newton方程式を、dy についての小さな線形系に整理して解く
    d = x / s
    rhs = -r_primal - A @ ((-r_center + x * r_dual) / s)
    dy = np.linalg.solve(A @ (d[:, None] * A.T), rhs)
    ds = -r_dual - A.T @ dy
    dx = (-r_center - x * ds) / s
    # x と s が正のままでいられる最大の歩幅の 0.99 倍だけ進む
    step = 1.0
    for v, dv in ((x, dx), (s, ds)):
        if (dv < 0).any():
            step = min(step, 0.99 * float(np.min(-v[dv < 0] / dv[dv < 0])))
    x, y, s = x + step * dx, y + step * dy, s + step * ds

result = linprog(c[:2], A_ub=[[3, 2], [1, 3]], b_ub=[18, 13],
                 bounds=[(0, None)] * 2, method="highs-ipm")
print(result.x.round(3), round(-result.fun, 3), result.status)
```

```text
0 [1. 1.] 7.0 4.0 14.4222
1 [1.779 1.595] 11.717 1.8825 10.0666
2 [3.418 2.545] 20.435 0.8166 2.7396
3 [3.977 2.987] 23.88 0.2294 0.0
4 [3.996 2.995] 23.965 0.0688 0.0
5 [3.999 2.998] 23.99 0.0206 0.0
6 [4. 3.] 23.997 0.0062 0.0
7 [4. 3.] 23.999 0.0019 0.0
8 [4. 3.] 24.0 0.0006 0.0
[4. 3.] 24.0 0
```

上のコードは仕組みを見せる最小の実装です。実務では、歩幅や $\sigma$ の決め方、初期点の作り方が洗練されたソルバーを使います。
最後の二行は、`linprog` の `method="highs-ipm"` でHiGHSの内点法（interior-point）を明示的に指定した確認です。

同じ問題を `method="highs-ds"`（dual simplex）と比べる場合は、iteration数だけでなく、一反復あたりの分解の費用を含めて比べます。
ソルバーが持つcrossoverの有無や既定のパラメータは、利用versionの[公式SciPyリファレンス](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.linprog.html)や[HiGHSドキュメント](https://highs.dev/)で確認します。

## 診断値

- 主問題の実行可能性の残差（primal feasibility residual）
- 双対問題の実行可能性の残差（dual feasibility residual）
- 双対ギャップ（絶対値と相対値）
- 障壁パラメータ $\mu$
- 相補性（$x^\top s$）
- KKT系の条件数
- crossoverの有無と費用

判断の目安は次のとおりです。
三つの残差（主・双対・ギャップ）がすべて許容誤差以下になれば、停止してよい状態です。
$\mu$ を下げてもギャップが縮まなければ、歩幅が極端に短くなっていないか、KKT系の条件数が悪化していないかを見ます。

## 失敗・切替の兆候

| 症状 | 考えられる原因 | 対処 |
|---|---|---|
| $\mu$ を下げても双対ギャップが縮まらない | 歩幅が極端に短い。中心パスから外れている | 初期点・尺度・パラメータを見直す。simplexで解いて比べる |
| KKT系の分解でmemoryが足りない | 大規模で、疎性が活かせていない | 分解の並べ替えを確認する。一次法（[PDLP](#/learn/pdlp)など）を検討する |
| 係数の尺度が桁違いで数値warningが出る | 単位の不揃い | 単位を揃えて尺度を調整する |
| 実行不能・非有界を目的値だけで見落とす | 状態（status）を確認していない | statusと残差を必ず記録する |
| crossover後の基底が数値的に不安定 | 数値誤差、許容誤差の設定 | 許容誤差を確認する。必要なら[dual simplex](#/learn/dual-simplex)で解き直す |

## 次に読む

問題の形から選び直す場合は、[LP・QP・錐最適化の選び分け](#/learn/lp-qp-conic)も確認します。

- [線形計画](#/learn/concept.linear-program)：小さな例の問題を定式化から読み直す
- [凸二次計画](#/learn/concept.convex-quadratic-program)：二次項が加わったときのKKT系
- [Primal simplex法](#/learn/primal-simplex)：頂点を渡り歩く別の道
- [非線形内点法](#/learn/interior-point-nlp)：非線形制約への一般化
