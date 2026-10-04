---
content_id: riemannian-trust-region
kind: method
method_id: M_RIEMANNIAN_TRUST_REGION
title_ja: Riemann信頼領域法
title_en: Riemannian Trust-Region
summary: 接空間上に二次モデルを作り信頼半径の内側だけで最小化し、写像で多様体上に戻す大域化された二階法です。
source_ids: [S044, S045, S071]
related_ids: [riemannian-gradient, trust-region-newton-cg, family.manifold, family.trust-region]
status: published
last_reviewed: 2026-10-03
---

接空間上に二次モデルを作り信頼半径の内側だけで最小化し、写像で多様体上に戻す大域化された二階法です。

## 30秒でつかむ

球面上で近くの地図を信用する範囲を決め、予想した下り具合と実際の下り具合を比べます。

Riemann信頼領域法は、接空間上の二次モデルを信頼半径内で解き、多様体へ戻す写像で多様体上へ戻す二階法です。

## 一手の意味

目的値の実際の減少を、接空間の近似が予測した減少で割ります。

$$
\rho_k=\frac{f(x_k)-f(R_{x_k}(p_k))}{m_k(0)-m_k(p_k)}
$$

分母が正の候補でこの比を計算し、採用と半径更新を決めます。

### ユークリッド版の信頼領域法との対応

[Trust-region Newton-CG](#/learn/trust-region-newton-cg)は、現在点まわりの二次モデルをユークリッド空間で作ります。
信頼半径 $\Delta_k$ の内側だけを信用し、打切り共役勾配法で近似解を求めます。
Riemann信頼領域法はこの考え方を多様体上へそのまま持ち込みます。
二次モデルを現在点の接空間に作り、計量に合う勾配・ヘッセ行列とレトラクションを対応させます。
接空間は局所的に平坦なので、ユークリッド版の部分問題の解法や採用判定の枠組みをほぼそのまま流用できます。

### 接空間上で何を解いているか

各一歩では、Riemann勾配とリーマンヘッセ行列を使って部分問題

$$
\min_{\|p\|\le \Delta_k,\, p \in T_x M} \; m_k(p)
$$

を解きます。大規模な場合は打切りCGによる近似解がよく使われます。
$T_xM$ は現在点$x$における接空間です。
候補の一歩を、多様体へ戻す写像で多様体上の点へ写します。
実際の改善とモデルが予測した改善の比 $\rho_k$ を確認します。
この比から候補の採否と信頼半径の更新を判断します。
この流れはユークリッド版の信頼領域法の判定ロジックと同じで、幾何の分だけ「二次モデルを作る場所」と「一歩を多様体へ戻す操作」が追加されています。

### リーマンヘッセ行列の入手性という課題

ユークリッド誘導計量を使う埋込み多様体では、リーマンヘッセ行列はユークリッドヘッセ行列を接空間へ射影し、さらに多様体の曲率に由来する補正項を加えて得られます。
別の計量では、計量に対応した接続の項も必要です。この補正項は多様体ごとに異なる幾何量で、ユークリッドヘッセ行列をそのまま接空間へ落とすだけでは正しいリーマンヘッセ行列とベクトルの積になりません。
PymanoptやManoptでは、多様体側の幾何演算と目的側の微分を組み合わせます。自動微分・解析的な積・有限差分近似のどれを使うかは、渡した微分情報と実装で変わります。ライブラリ名だけで精度や入手方法は決まりません。

## 小さな例：球面の二次モデルを実際に解く

$A=\operatorname{diag}(1,2,4)$、$f(x)=x^TAx$ を $\|x\|=1$ の下で最小化します。最小固有値は1、解は $(\pm1,0,0)$。初期点は $(1,1,1)/\sqrt3$ です。

前の記事の「接勾配を半径で切る」だけでは、二階の信頼領域法にはなりません。本例では、接空間の二次部分問題、候補のレトラクション、改善比、受理・棄却、半径更新まで実装します。

### ヘッセ行列から、曲面の補正を落とさない

球面上の接ベクトル $\xi$ には

$$
\operatorname{grad}f(x)=2(Ax-f(x)x),\qquad
\operatorname{Hess}f(x)[\xi]
=2P_x(A\xi)-2f(x)\xi,
\quad P_x=I-xx^T
$$

です。$-2f(x)\xi$ が球面の曲率に由来する項です。$2A\xi$ を射影するだけでは足りません。

$Q$ を $x$ と直交する正規直交基底を列に持つ $3\times2$ 行列として、$\xi=Qp$ と置きます。すると

$$
g=2Q^TAx,\quad H=2Q^T(A-f(x)I)Q,\qquad
\min_{\|p\|\le\Delta}\;g^Tp+\tfrac12p^THp
$$

という2変数の普通の信頼領域部分問題になります。小例では固有値分解で解きます。大規模問題で使う打切りCGとは、部分問題の解き方が違います。

解の検算には $(H+\lambda I)p=-g$、$H+\lambda I\succeq0$、$\lambda\ge0$、$\|p\|\le\Delta$、$\lambda(\Delta-\|p\|)=0$ を使えます。境界に当たるときは、$\|(H+\lambda I)^{-1}g\|=\Delta$ となる $\lambda$ を探します。勾配が最小固有空間と直交するhard caseは別に扱い、負の曲率方向を落とさないようにします。

候補は $x_{\mathrm{trial}}=(x+Qp)/\|x+Qp\|$。球面のこの正規化は二次のレトラクションであり、上のリーマンヘッセ行列がこの局所二次モデルに対応します。一般の一次のレトラクションでは、この対応を無条件に置けません。

![最初の候補方向に沿った接空間モデルの予測減少と、球面へ戻した後の実際の減少。右は初期半径4の候補の棄却、半径1への縮小後の受理と、その後の改善比。](./media/riemannian-trust-rayleigh.svg "A=diag(1,2,4)の同一実行。左は最初の方向だけの断面で、右の次の候補は縮めた部分問題を解き直している。")

### 大きすぎる最初の一歩を、実際に棄却する

半径を意図的に $\Delta_0=4$ と大きく始めます。教材のルールは次のとおりです。

- $\rho>0.1$ なら受理。それ以外は現在点を変えず棄却
- $\rho<0.25$ なら半径を1/4へ
- $\rho>0.75$ かつ境界に当たった候補なら半径を2倍（上限4）
- その他では半径を維持

| 提案 $k$ | 提案前の費用 | 半径 | $\rho$ | 採否 |
|---|---:|---:|---:|---|
| 0 | 2.3333 | 4 | 0.0588 | 棄却 |
| 1 | 2.3333 | 1 | 0.5000 | 受理 |
| 2 | 1.0443 | 1 | 0.9615 | 受理 |
| 3 | 1.0001 | 1 | 0.9999 | 受理 |

棄却行の次でも現在の費用は2.3333です。悪かったのは点そのものではなく、その点から大きすぎるモデル予測を信用した候補です。半径を縮め、同じ点から二次部分問題を解き直します。

この二次関数と球面の正規化では、解析的にも $\rho=1/(1+\|p\|^2)$ と分かります。分子と分母を展開すると、実際の減少だけが $1+\|p\|^2$ で割られるためです。最初の長さ4なら $\rho=1/17$、次の長さ1なら $\rho=1/2$。一般の目的関数で成立する公式ではありませんが、この実装の強い検算になります。

最適点に近く、予測減少も実測減少も丸め誤差に近づいた後は、比の末尾の桁を読みすぎません。勾配ノルムと予測減少の下限を停止条件にします。

## 向く条件・避ける条件

### 一次法から乗り換える理由

[Riemann勾配法](#/learn/riemannian-gradient)は実装が単純で初期の収束が速いことがありますが、局所解付近での収束が遅くなったり、鞍点付近で長く停滞したりすることがあります。
Riemann信頼領域法は二次情報を使うため、良い近傍では収束が速くなります。
負の曲率方向も検出しやすく、鞍点からの脱出にも使われます。
一次法で目的値の減少が長時間止まったときに、高精度化の手段として検討する位置づけです。

### 向いている条件

- 変数が既知の多様体構造を持つ（球面、Stiefel、Grassmann、SO(3)など）
- Riemann勾配に加えてリーマンヘッセ行列またはそのベクトルとの積が利用できる
- Riemann勾配法が停滞し、局所解近傍での高精度化や鞍点脱出が必要
- 多様体上での頑健な大域化（信頼半径による棄却）を使いたい

ヘッセ行列情報が得られない、または多様体構造自体が本質でない場合は、[Riemann勾配法](#/learn/riemannian-gradient)や[Riemann多様体最適化の選び分け](#/learn/family.manifold)から検討します。

## Python

次のコードは本文の球面・初期点・半径更新を再現します。2次元部分問題の小さな検証実装であり、汎用ソルバーの代替ではありません。

```python
import numpy as np
from scipy.linalg import null_space
from scipy.optimize import brentq

A = np.diag([1.0, 2.0, 4.0])

def subproblem(g, H, radius):
    # Spectral solution of a 2D Euclidean trust-region problem.
    d, V = np.linalg.eigh(H)
    c = V.T @ g
    if d[0] > 0:
        p = -c / d
        if np.linalg.norm(p) <= radius:
            return V @ p, 0.0
    lower = max(0.0, -d[0])
    denominator = d + lower
    singular = denominator < 1e-12
    p = np.zeros_like(c)
    p[~singular] = -c[~singular] / denominator[~singular]
    # Hard case: gradient is orthogonal to the lowest eigenspace.
    if np.all(np.abs(c[singular]) < 1e-12) and np.linalg.norm(p) <= radius:
        if lower > 0:
            j = np.flatnonzero(singular)[0]
            p[j] = np.sqrt(max(0.0, radius**2 - p @ p))
        return V @ p, lower
    norm_at = lambda lam: np.linalg.norm(c / (d + lam))
    lo, hi = lower + 1e-13, max(1.0, lower + 1.0)
    while norm_at(hi) > radius:
        hi = 2 * hi + 1
    lam = brentq(lambda z: norm_at(z) - radius, lo, hi, xtol=1e-14)
    return V @ (-c / (d + lam)), lam


def solve():
    x = np.ones(3) / np.sqrt(3.0)
    radius, history = 4.0, []
    for k in range(30):
        Q = null_space(x[None, :])  # 3 x 2 orthonormal tangent basis
        f = float(x @ A @ x)
        g = 2 * Q.T @ A @ x
        H = 2 * Q.T @ (A - f * np.eye(3)) @ Q
        if np.linalg.norm(g) < 1e-9:
            break
        p, lam = subproblem(g, H, radius)
        predicted = -g @ p - 0.5 * p @ H @ p
        if predicted <= 1e-15:
            break
        trial = x + Q @ p
        trial /= np.linalg.norm(trial)
        actual = f - trial @ A @ trial
        rho = actual / predicted
        accept = rho > 0.1
        history.append(dict(k=k, x=x.tolist(), f=f, radius=radius,
                            step=float(np.linalg.norm(p)), predicted=float(predicted),
                            actual=float(actual), rho=float(rho), accepted=bool(accept),
                            kkt=float(np.linalg.norm((H + lam * np.eye(2)) @ p + g))))
        old_radius = radius
        if rho < 0.25:
            radius *= 0.25
        elif rho > 0.75 and np.linalg.norm(p) > 0.99 * old_radius:
            radius = min(2 * radius, 4.0)
        if accept:
            x = trial
    return x, history

if __name__ == '__main__':
    x, history = solve()
    for r in history:
        print(r['k'], round(r['f'], 6), round(r['radius'], 4),
              round(r['rho'], 4), r['accepted'])
    print('cost:', x @ A @ x)
```

勾配、ヘッセ行列とベクトルの積、多様体へ戻す写像は多様体ごとに異なる幾何演算です。
実務では[Pymanopt](https://pymanopt.org/)の公式リファレンスで信頼領域法のソルバーについて、利用バージョンに対応する説明を確認します。

このコードの勾配ノルムによる停止は、掲載初期点での一階停止条件です。任意の初期点から鞍点や極大点を脱することまで確認するなら、接空間Hessianの最小固有値など二階の条件も点検します。勾配がゼロなら、負曲率があってもこのコードは部分問題を呼ぶ前に止まります。

## 診断値

- Riemann勾配ノルム
- 信頼半径 $\Delta_k$
- 実際の減少と予測した減少の比 $\rho_k$
- 内側の打ち切りCG 反復数
- 多様体へ戻す写像の誤差
- 受理／棄却した一歩の数

## 失敗・切替の兆候

- Riemann勾配検査（有限差分との一致確認）が合わない
- 多様体へ戻した後に多様体制約からのずれが大きい
- 座標近傍依存の特異点付近で一歩の挙動が不安定になる
- 信頼半径が縮み続け候補の一歩がほぼ採用されない
- リーマンヘッセ行列近似の質がソルバーによって大きく違う

## 次に読む

一次法から始めたいときは[Riemann勾配法](#/learn/riemannian-gradient)、多様体手法全体の選び分けは[Riemann多様体最適化の選び分け](#/learn/family.manifold)を確認します。

- 問題の形を確認する: [回転群上の最適化](#/formulations/PA037)

## 一次資料と検算

球面のヘッセ行列、二次レトラクション、信頼領域法の条件は [Boumalの教科書](https://www.nicolasboumal.net/book/IntroOptimManifolds_Boumal_2023.pdf) 5.10節、6.4節、7.2節を参照できます。[Manoptの公式例](https://www.manopt.org/firstexample.html)は、微分検査とソルバーを組み合わせる入口です。

本例では固有値1への到達、最初の部分問題の別解法SLSQPとの照合、レトラクションに沿う二階中心差分、負の曲率だけが残るhard caseを検査しています。大域化は大域最小解の保証という意味ではありません。本例の最小値を証明できるのは、対称行列の固有値という別の構造があるためです。
