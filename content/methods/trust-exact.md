---
content_id: trust-exact
kind: method
method_id: M_TRUST_EXACT
title_ja: 厳密信頼領域Newton法
title_en: Nearly Exact Trust-Region
summary: 信頼領域の部分問題をCGで打ち切って近似するのではなく、固有値分解や行列分解に基づいてほぼ厳密に解く二階最適化法です。
source_ids: [S002, S056]
prerequisites: []
related_ids: [trust-region-newton-cg, trust-krylov, newton-method, family.trust-region]
status: published
last_reviewed: 2026-10-03
---

厳密信頼領域Newton法は、半径内の二次モデルを、行列分解を使って高い精度で最小にする方法です。ここで「厳密」に近づけるのは現在点の部分問題です。元の非線形問題の大域最適解を保証する名前ではありません。SciPyの名称も nearly exact（ほぼ厳密）です。

本稿の問いは、半径を小さくすると、なぜNewtonの一歩が単に短くなるだけでなく、向きまで変わるのかです。同じ現在点で半径だけを変え、正則化係数 $\lambda$ と各成分を追うと、その理由が見えます。

## 30秒でつかむ

- 目的値・勾配に加え、明示的なヘッセ行列を使います。
- $\|p\|_2\le\Delta$ の内側で二次モデルの良い最小点を求め、その後に実際の目的値で採否を決めます。
- 密な $n\times n$ 行列の保存には $O(n^2)$、典型的な分解には1回あたり $O(n^3)$ の費用がかかります。1部分問題で複数回分解する場合もあります。
- HVPだけで済む[Trust-region Newton-CG](#/learn/trust-region-newton-cg)や[Trust-region Krylov](#/learn/trust-krylov)とは、一歩の精度と内側費用の交換条件が違います。

## 半径内の最小点を特徴づける四つの条件

現在点で定数項を除いたモデルを

$$
q(p)=g^\top p+\tfrac12p^\top Hp,\qquad \min_{\|p\|_2\le\Delta}q(p)
$$

とします。対称な $H$ と正の半径に対し、この部分問題の大域最小点 $p$ は、ある $\lambda\ge0$ とともに次を満たします。

$$
(H+\lambda I)p=-g,\qquad
H+\lambda I\succeq0,\qquad
\|p\|_2\le\Delta,\qquad
\lambda(\|p\|_2-\Delta)=0.
$$

1本目だけでは不十分です。2本目は、ずらした曲率がどの方向にも負でないことを要求します。最後の相補性は、半径が効かなければ $\lambda=0$、$\lambda>0$ なら境界にいることを表します。$\lambda$ は、元問題に新しく加える恒久的な正則化ではなく、その部分問題の半径制約に対応する乗数です。

この条件を満たすと本当に最小になる理由も短く追えます。任意の実行可能な $z$ に対して、停留条件を代入すると

$$
q(z)-q(p)=\tfrac12(z-p)^\top(H+\lambda I)(z-p)
+\tfrac{\lambda}{2}(\|p\|_2^2-\|z\|_2^2)\ge0.
$$

最初の項は半正定値性から非負。$\lambda>0$ なら $\|p\|=\Delta\ge\|z\|$ なので2項目も非負です。$\lambda=0$ なら2項目は消えます。したがって、円内にもっと低いモデル値はありません。ここで証明したのは二次部分問題に限られます。

## 同じ点で 半径だけを変える

[Newton法](#/learn/newton-method)と同じ

$$
f(x,y)=(x-1)^2+20(y+2)^2,\qquad x_0=(4,3)
$$

を使います。$g=(6,200)$、$H=\operatorname{diag}(2,40)$ で、無制約Newton方向は $p_N=(-3,-5)$、長さは $\sqrt{34}\approx5.830952$ です。

半径がこれより小さければ、$\lambda>0$ を選びます。この例の停留条件は成分ごとに解けます。

$$
p_x(\lambda)=-\frac{6}{2+\lambda},\qquad
p_y(\lambda)=-\frac{200}{40+\lambda}.
$$

残るのは、$\|p(\lambda)\|_2=\Delta$ になる $\lambda$ を探す1変数の方程式です。正定値のこの例では、$\lambda$ を増やすほど長さが単調に小さくなるため、区間を挟んだ根探索で確実に求められます。

| 固定点からの半径 $\Delta$ | $\lambda$ | 一歩 $p$ | 試行点の目的値 |
|---:|---:|---|---:|
| 1 | 160.137083 | $(-0.037006,-0.999315)$ | 328.888936 |
| 2 | 60.116830 | $(-0.096592,-1.997666)$ | 188.709951 |
| 4 | 10.371613 | $(-0.484981,-3.970490)$ | 27.523124 |
| $\sqrt{34}$ 以上 | 0 | $(-3,-5)$ | 0 |

これは4回の連続した更新ではありません。全て同じ $(4,3)$ に立ち、半径だけを変えた四つの候補です。外側の最適化の軌跡と混ぜないでください。

![同じ現在点で信頼半径を変えた4本の一歩と、半径に対する各成分の変化](./media/trust-exact-main.svg)

図の原点は現在点からの移動 $p=0$ です。青い小半径では、ほぼ真下に進みます。紫のNewton点が許容されるまで広げると、左向き成分も大きくなります。

理由は「全成分に同じ縮小率を掛ける」式ではないからです。Newton方向との比は $x$ 成分で $2/(2+\lambda)$、$y$ 成分で $40/(40+\lambda)$ です。小さい曲率2の方向は、同じ $\lambda$ によって強く抑えられます。$\lambda$ が非常に大きいと $p\approx-g/\lambda$ となり勾配方向へ、$\lambda=0$ ではNewton方向へ近づきます。

主例の表は独自の固有値・根探索による高精度な計算です。半径内性、停留残差、相補性、$H+\lambda I$ の最小固有値を検査しました。SciPyの近似的な部分問題解を厳密値として表示しているわけではありません。

## exactでも外側の採否が必要な理由

候補を得たら、[信頼領域法](#/learn/family.trust-region)の比

$$
\rho=\frac{f(x)-f(x+p)}{-q(p)}
$$

でモデルを照合します。予測減少 $-q(p)$ が正であることが前提です。部分問題を正確に解いても、二次モデル自体が元の関数を近似していることは変わりません。

主例は厳密な二次関数なので $f(x+p)=f(x)+q(p)$ であり、どの候補でも減少が正なら $\rho=1$ です。従って、この例だけで「モデルが外れたときに半径をどう学習するか」は見えません。その動きは[trust-region Newton-CGの棄却例](#/learn/trust-region-newton-cg)にあります。

主例を実際に進め、初期半径1、境界で $\rho>0.75$ なら2倍という外側規則を使うと、半径は1→2→4です。ただし点が変わるので、2回目の $\lambda$ は固定点表の60.116830ではなく40.211552になります。3回目は残りのNewton方向の長さが約3.4626で半径4に収まり、解に着きます。固定点の比較図と外側の反復を区別すると、数値の取り違えを防げます。

一般の非二次関数では、厳密な部分問題解でも棄却は起こります。`trust-exact` を選ぶ理由は、棄却がなくなることではなく、許容した局所モデルをしっかり解く価値があることです。

## 負の曲率があっても 解は単一の固有ベクトルとは限らない

$H$ に負の固有値があれば、最適な部分問題解は境界にあります。ただし「負の固有ベクトルの向きへ進めばよい」とは限りません。線形項 $g^\top p$ も、全ての曲率成分も、解に影響します。

例えば $H=\operatorname{diag}(-2,4)$、$g=(1,2)$、$\Delta=1$ では

$$
\lambda\approx3.042935,\qquad p\approx(-0.958832,-0.283973)
$$

です。負固有値の固有ベクトルは横軸方向ですが、解は縦成分も持ちます。$H+\lambda I$ の最小固有値は約1.042935、停留残差は約 $2.2\times10^{-16}$ で、四条件を満たすことを数値で確かめています。

さらに $g=(0,1)$ に変えると、$\lambda=2$ で $H+\lambda I$ が特異になります。このhard caseでは

$$
p=(\pm\sqrt{35}/6,-1/6)
$$

が解です。単純な逆行列 $(H+\lambda I)^{-1}$ は使えず、零空間成分で境界まで補う必要があります。本稿の検証コードはこの2次元例を扱いますが、実用の数値的hard case全般を解説・実装するものではありません。これらは主例の正定値な1変数根探索に、そのまま移せない場合です。

## 小さな表と実用ソルバーを再現する

```python
import numpy as np
import scipy
from scipy.optimize import brentq, minimize

H = np.diag([2.0, 40.0])
g = np.array([6.0, 200.0])
x0 = np.array([4.0, 3.0])
f = lambda x: (x[0]-1)**2 + 20*(x[1]+2)**2
grad = lambda x: np.array([2*(x[0]-1), 40*(x[1]+2)])

# 主例専用の厳密部分問題。H が正定値であることを使う。
for delta in [1.0, 2.0, 4.0, np.sqrt(34.0)]:
    if delta >= np.sqrt(34.0):
        lam = 0.0
    else:
        def length_error(lam):
            return np.linalg.norm(-g/(np.diag(H)+lam))-delta
        lam = brentq(length_error, 0.0, 1000.0, xtol=1e-12)
    p = -g/(np.diag(H)+lam)
    print(delta, lam, p, f(x0+p))

# 別の実行。SciPy は固有値分解版の上記コードと同一ではない。
r = minimize(f, x0, jac=grad, hess=lambda x: H, method="trust-exact",
             options={"gtol": 1e-8, "initial_trust_radius": 1.0,
                      "max_trust_radius": 1000.0, "eta": 0.15,
                      "maxiter": 300, "subproblem_maxiter": 25})
print(scipy.__version__, r.success, r.nit, r.nfev, r.njev, r.nhev)
# 1.17.0 True 3 4 4 4
```

SciPy 1.17.0の実装は、ずらした行列のCholesky分解などを使う反復法です。毎回全固有ベクトルを求める実装だとは説明しません。また有限の停止許容があるため、名前が `exact` でも機械精度の部分問題解を毎回保証するわけではありません。[版固定の実装](https://github.com/scipy/scipy/blob/v1.17.0/scipy/optimize/_trustregion_exact.py)と[公式オプション](https://docs.scipy.org/doc/scipy-1.17.0/reference/optimize.minimize-trustexact.html)を参照してください。

実測環境はPython 3.12.14、NumPy 2.3.5、SciPy 1.17.0です。Rosenbrock関数 $100(y-x^2)^2+(1-x)^2$、初期 $(-1.2,1)$、同じ外側設定の補助実測は25反復、関数26回、勾配23回、ヘッセ行列26回、最終勾配L2ノルム約 $6.39\times10^{-9}$ でした。`nhev` はここではヘッセ行列の評価回数であり、分解回数ではありません。全検証と図生成は `generate_verify.py`、未丸めのKKT残差・固有値・回数は `verified-numbers.json` にあります。

## 部分問題の精度に費用を払う価値があるか

同じモデルで探索空間を十分に扱えば、粗い候補より良いモデル減少を得られます。ただし、その差が実際の目的値でも有益か、追加の分解費用に見合うかは別問題です。外側反復が少なくても、総時間は長いかもしれません。

- 密なヘッセ行列を精度よく計算・保存・分解できる中小規模の[滑らかな無制約問題](#/formulations/PA006)では候補になります。
- [大規模な無制約問題](#/formulations/PA007)でHVPだけが安いなら、[Trust-region Newton-CG](#/learn/trust-region-newton-cg)または[Trust-region Krylov](#/learn/trust-krylov)を検討します。
- ヘッセ行列を得る費用が高いなら、[BFGS法](#/learn/bfgs)との評価費用比較が必要です。
- 微分が誤っているなら、部分問題を精密に解くほど間違ったモデルに忠実になります。手法変更より先に微分を照合します。

最終的には外側勾配、目的値、終了理由を確認します。本コードの通常停止は $\|g\|_2<10^{-8}$ です。小さな勾配を非凸元問題の大域最小証明には読み替えません。半径が小さいことも、部分問題がよく解けたことも、それだけでは元問題の収束証明ではありません。

## 次に読む

- [信頼領域法の選び分け](#/learn/family.trust-region)：モデル、受理比、半径を分ける
- [Trust-region Krylov](#/learn/trust-krylov)：全空間の分解を避け、調べた部分空間内で一歩を改善する
- [Newton法](#/learn/newton-method)：半径が効かないときの一歩との関係
- [SciPy minimize](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.minimize.html)：共通APIと戻り値
