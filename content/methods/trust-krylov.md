---
content_id: trust-krylov
kind: method
method_id: M_TRUST_KRYLOV
title_ja: Trust-region Krylov法
title_en: Trust-Region Krylov
summary: ヘッセ行列とベクトルの積から作るKrylov部分空間で信頼領域の部分問題を近似し、大規模な滑らか問題へ曲率を安全に利用する局所法です。
source_ids: [S002, S056]
related_ids: [family.smooth-local, newton-cg, trust-region-newton-cg]
status: published
last_reviewed: 2026-09-30
---

ヘッセ行列とベクトルの積から作るKrylov部分空間で信頼領域の部分問題を近似し、大規模な滑らか問題へ曲率を安全に利用する局所法です。

## 30秒でつかむ

広大な山地を全部測量する代わりに、足元の傾きと、その傾きの向きに動いたときの傾きの変化だけを調べます。
そこから数本の方向を選び、その方向が張る小さな平面の中だけで、信用できる一歩を探します。
平面の外は見ません。

- **見るもの**: 勾配、ヘッセ行列とベクトルの積（Hessian-vector product、HVP）、局所モデルが予測した改善
- **動かすもの**: Krylov部分空間、信頼半径、候補の一手
- **前進の判断**: 実際の減少とモデルが予測した減少の比

[Newton-CG法](#/learn/newton-cg)と似ていますが、一手の長さの決め方が違います。Newton-CG法は、向きを決めてから直線探索で長さを決めました。
Trust-region Krylov法は、信頼領域の部分問題として、向きと長さを同時に扱います。

気をつける点は三つあります。局所モデルが悪いこと、HVPの誤差、半径の過小化です。

## 一手の意味

局所二次モデルを、信頼半径 $\Delta_k$ の内側で最小化します。
次の式は、モデルの値を、一手の長さが $\Delta_k$ 以下という条件で最小にするという意味です。

$$
\min_p\; g_k^T p + \frac{1}{2}p^T H_k p
\quad \text{subject to}\quad \lVert p\rVert \leq \Delta_k
$$

高次元では、この部分問題を全空間では解きません。HVPから作るKrylov部分空間の中で近似します。

$$
\mathcal{K}_j=\mathrm{span}\{g_k,\ H_k g_k,\ H_k^2 g_k,\ \dots,\ H_k^{j-1} g_k\}
$$

式は「勾配と、それにヘッセ行列を繰り返し掛けた向きが張る空間」と言っています。HVPを1回計算するごとに、部分空間の次元が1つ増えます。
$j$ が小さければ、部分問題は小さな問題になり、安く解けます。

候補の一手を得たら、実際の減少とモデルの予測の減少の比 $\rho_k$ を見て、採否と半径の更新を決めます。この部分は[厳密なtrust-region Newton法](#/learn/trust-exact)と同じです。

## 小さな例

[Newton法](#/learn/newton-method)や[厳密なtrust-region Newton法](#/learn/trust-exact)と同じ関数 $f(x,y)=(x-1)^2+20(y+2)^2$ を、初期点 $(4,\,3)$ から解きます。
この点で、Krylov部分空間の次元 $j$ と半径 $\Delta$ を変えて、部分問題を解いた結果を並べます。

| 半径 $\Delta$ | 部分空間の次元 $j$ | 一手 $p$ | モデルの値 | 次の点での目的値 |
|---:|---:|---|---:|---:|
| 1 | 1 | $(-0.030,\,-1.000)$ | −180.107 | 328.893 |
| 1 | 2 | $(-0.037,\,-0.999)$ | −180.111 | 328.889 |
| 4 | 1 | $(-0.120,\,-3.998)$ | −480.63 | 28.4 |
| 4 | 2 | $(-0.485,\,-3.970)$ | −481.48 | 27.5 |

次元1の部分空間は、勾配 $(6,\,200)$ の向きだけです。一手は勾配の反対へ、長さ $\Delta$ ぶん進みます。
次元2では、HVPで得た $Hg=(12,\,8000)$ が加わります。曲がり方が分かるので、一手の向きが $x$ 方向へ少し回ります。

半径が $1$ のときは、差がほとんどありません。半径が広がる $4$ のときに、差がはっきり出ます。モデルの値も、次元2のほうが低くなります。

この問題は2変数なので、次元2の部分空間が全空間です。表の $\Delta=4,\ j=2$ の一手は、[厳密なtrust-region Newton法](#/learn/trust-exact)の表の一手と一致します。
変数が多い問題では、$j$ が変数の数よりずっと小さい段階で打ち切るので、厳密な解と一致するとは限りません。HVPの回数を抑える代わりに、部分問題の解は近似になります。

Rosenbrock関数 $f(x,y)=100(y-x^2)^2+(1-x)^2$ も、同じ手法で解けます。
初期点 $(-1.2,\,1)$ から、SciPyの `trust-krylov` は38回の反復で最小点 $(1,\,1)$ に着きます。実行例は下のPythonの節にあります。
この回数は、この問題と初期半径、許容での一例です。手法どうしの優劣ではありません。

## 向く条件・避ける条件

Trust-region Krylov法は、ヘッセ行列を作れない大きな問題で、曲率と信頼領域の安全性を両立させたいときの手法です。
先に、次の項目を確認します。

| 項目 | 確認すること |
|---|---|
| 目的関数 | 二階近似が意味を持つ程度に滑らかか |
| 勾配とHVP | 高い精度で、効率よく計算できるか |
| 次元 | 密なヘッセ行列を作らずに済む価値があるか |
| 非凸性 | 負の曲率を見つける意味があるか |
| 制約 | 無制約か。制約があれば対応する別の版が必要 |

一反復の目的関数の評価が高価な場合は、却下した一手の回数も、予算として記録します。

向く条件です。

- 大規模で滑らかな無制約問題である（[大規模な無制約の最小化](#/formulations/PA007)）
- HVPを、自動微分や問題の構造から得られる
- 不定なヘッセ行列や負の曲率を、無視したくない
- 直線探索より、局所モデルの信頼度を明示したい

避ける、または切り替える条件です。

- 勾配やHVPがノイズに支配される
- 不連続、離散変数、ブラックボックス評価しかない
- 部分問題の求解が、目的関数の評価より支配的である
- 一般制約や、大域最適性の証明が必要である
- 変数が少なく、密なヘッセ行列を分解できる → [厳密なtrust-region Newton法](#/learn/trust-exact)と比べる（[滑らかな無制約の最小化](#/formulations/PA006)）
- より単純な内側のCGで足りる → [Trust-region Newton-CG](#/learn/trust-region-newton-cg)と比べる

## Python

次の例は、積 $Hv$ だけを渡してTrust-region Krylov法を実行する最小例です。上の二次関数とRosenbrock関数に適用します。

```python
import numpy as np
from scipy.optimize import minimize


def rosenbrock(x: np.ndarray) -> float:
    return float(100.0 * (x[1] - x[0] ** 2) ** 2 + (1.0 - x[0]) ** 2)


def rosenbrock_grad(x: np.ndarray) -> np.ndarray:
    return np.array([
        -400.0 * x[0] * (x[1] - x[0] ** 2) - 2.0 * (1.0 - x[0]),
        200.0 * (x[1] - x[0] ** 2),
    ])


def rosenbrock_hessp(x: np.ndarray, v: np.ndarray) -> np.ndarray:
    """Hessian 行列を作らず、積 H(x) v だけを返す。"""
    return np.array([
        (1200.0 * x[0] ** 2 - 400.0 * x[1] + 2.0) * v[0] - 400.0 * x[0] * v[1],
        -400.0 * x[0] * v[0] + 200.0 * v[1],
    ])


# 二次関数 (x-1)^2 + 20 (y+2)^2 : Hessian は diag(2, 40)
def quad(x):
    return (x[0] - 1.0) ** 2 + 20.0 * (x[1] + 2.0) ** 2


def quad_grad(x):
    return np.array([2.0 * (x[0] - 1.0), 40.0 * (x[1] + 2.0)])


def quad_hessp(x, v):
    return np.array([2.0 * v[0], 40.0 * v[1]])


result = minimize(quad, np.array([4.0, 3.0]), jac=quad_grad, hessp=quad_hessp,
                  method="trust-krylov", options={"gtol": 1e-8})
print(result.success, result.x, result.nit, result.nhev)
# True [ 1. -2.] 4 10

result = minimize(rosenbrock, np.array([-1.2, 1.0]), jac=rosenbrock_grad,
                  hessp=rosenbrock_hessp, method="trust-krylov",
                  options={"gtol": 1e-8})
print(result.success, result.x, result.nit, result.nhev)
# True [0.99999999 0.99999999] 38 91
```

`nit` は反復回数、`nhev` はSciPyが報告するHVPの回数です。
出力はSciPy 1.18.1での結果です。利用中のバージョンのオプションと既定値は、[scipy.optimize.minimize](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.minimize.html)の公式リファレンスで確認します。

## 診断値

- 信頼半径
- 実際の減少と予測の減少の比 $\rho$
- 受理した一手の数と、却下した一手の数
- Krylov部分空間の反復回数
- 勾配のノルム
- 負の曲率が検出されたか

半径が縮み続ける、または却下が続くときは、局所モデルが地形と合っていません。HVPの回数は、外側の反復とは別に数えます。

## 失敗・切替の兆候

- 半径が縮み続ける → モデル、尺度、HVPのいずれかが地形と合っていない → 尺度とHVPを確認する
- 一手の却下が多い → 二次近似が通用する範囲が狭い、またはノイズがある → 微分の精度と、ノイズの有無を疑う
- Krylov部分空間の反復が上限に張り付く → 条件数が悪い → 前処理や、精度を下げた求解を検討する
- 曲率を使っても改善しない → 曲率の情報が費用に見合わない → L-BFGSや一階法と費用を比較する
- 初期点で解が変わる → 局所解が複数ある → 局所法であることを受け入れるか、大域探索へ切り替える

## コラム: Krylov空間は全ヘッセ行列を作らない

Krylov法は、全固有ベクトルを先に求めるのではありません。現在の勾配と曲率に関係する方向を、反復的に作ります。
HVPの費用と内側の反復まで含めて、Trust-region Newton-CGやNewton-CGと比較します。

## 次に読む

- [Trust-region Newton-CG](#/learn/trust-region-newton-cg)：より単純な内側のCGで部分問題を近似する方法
- [Newton-CG法](#/learn/newton-cg)：直線探索で長さを決める型。HVPの回数、却下した一手の数、実行時間を揃えて比べる
- [厳密なtrust-region Newton法](#/learn/trust-exact)：部分問題をほぼ厳密に解く方法
- [大規模な無制約の最小化](#/formulations/PA007)：この手法が解く問題の標準形
