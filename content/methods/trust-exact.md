---
content_id: trust-exact
kind: method
method_id: M_TRUST_EXACT
title_ja: 厳密trust-region Newton法
title_en: Nearly Exact Trust-Region
summary: trust-region部分問題をCGで打ち切って近似するのではなく、固有値分解や行列分解に基づいてほぼ厳密に解く二階最適化法です。
source_ids: [S002, S056]
prerequisites: []
related_ids: [trust-region-newton-cg, trust-krylov, newton-method, family.trust-region]
status: published
last_reviewed: 2026-09-30
---

trust-region部分問題をCGで打ち切って近似するのではなく、固有値分解や行列分解に基づいてほぼ厳密に解く二階最適化法です。

## 30秒でつかむ

地図を信じてよい範囲に、ロープで円を描くところを想像してください。
円の中では、地図（局所二次モデル）の最低点まで厳密に歩きます。円の外は、地図が当たるかどうか分からないので、踏み込みません。
歩いたあとで、地図の予測と実際の高さを見比べます。当たっていれば円を広げ、外れていれば縮めます。

- **見るもの**: 勾配、Hessian、信頼領域の部分問題の解、実際の減少とモデルが予測した減少の比
- **動かすもの**: 現在点と、信頼半径（trust radius）
- **前進の判断**: 実際の改善が、モデルの予測とおおむね一致すること

密なHessianを分解する費用が、一回ごとにかかります。その代わり、一手の質を優先し、外側の反復数は少なくなりやすい手法です。
気をつける点は三つあります。分解の費用、Hessianの誤り、問題規模の増大です。

## 一手の意味

信頼領域法は、各反復で局所二次モデルを作り、信頼半径 $\Delta_k$ の内側だけで最小化します。
次の式は、勾配とHessianで作ったモデルの値を、一手の長さが $\Delta_k$ 以下という条件で最小にするという意味です。

$$
\min_p\; g_k^T p + \frac{1}{2}p^T H_k p
\quad \text{subject to}\quad \lVert p\rVert \leq \Delta_k
$$

この部分問題の最適解は、ある $\lambda \geq 0$ を使って $(H_k + \lambda I)p = -g_k$ を満たします。
同時に、$\lambda$ と半径の境界の関係を表す式（secular equation）を満たすことが知られています。$\lambda>0$ なら、一手は境界の上にあります。

厳密なtrust-region法は、$H_k$ の固有値分解や行列分解を使って、この $\lambda$ を反復的に絞り込みます。
部分問題を、ほぼ厳密な精度で解く方法です。CGのように打ち切るのではなく、部分問題を一回解くだけで複数回の内部反復を使うところが特徴です。

解いた一手 $p_k$ は、そのまま受け入れるとは限りません。実際の減少とモデルの予測の減少の比 $\rho_k$ を見て、採否と半径を決めます。

$$
\rho_k=\frac{f(x_k)-f(x_k+p_k)}{m_k(0)-m_k(p_k)}
$$

$\rho_k$ が小さければ一手を却下して半径を縮め、大きくて一手が境界に達していれば半径を広げます。
SciPyの規則では、$\rho_k<0.25$ で半径を $1/4$ に縮め、$\rho_k>0.75$ で一手が境界にあれば $2$ 倍に広げます。$\rho_k>0.15$ で一手を受理します。

### CG打ち切り版との違い

[Trust-region Newton-CG](#/learn/trust-region-newton-cg)や[Trust-region Krylov法](#/learn/trust-krylov)は、Hessianとベクトルの積だけからCGやKrylov部分空間で部分問題を近似します。途中で打ち切ることで、一反復あたりの費用を抑えます。
厳密なtrust-region法は逆の設計です。密なHessianを分解できる規模を前提に、部分問題の質を優先します。

その結果、外側の反復数は少なくなりやすくなります。一方、一反復の費用は分解の $O(n^3)$ 相当を含み、重くなります。
密なHessianを保持できる中小規模の問題なら、反復数の少なさが総費用で有利になる場合があります。

### 負の曲率の扱い

$H_k$ が不定で負の固有値を持つとき、部分問題の解は境界に置かれます。向きは、負の曲率をもつ固有ベクトルの方向です。
固有値分解を通じて、この方向を正確に特定できます。負の曲率を無視することも、CGの打切り位置に依存して曖昧に扱うことも避けられます。
不定なHessianを含む非凸問題で、大域化の挙動を精密に制御したいときに適しています。

## 小さな例

### 半径を変えると、一手の向きが変わる

[Newton法](#/learn/newton-method)と同じ関数 $f(x,y)=(x-1)^2+20(y+2)^2$ を、初期点 $(4,\,3)$ から解きます。
勾配は $(6,\,200)$、Hessianは $\mathrm{diag}(2,\,40)$ です。この点で、半径 $\Delta$ ごとに部分問題を解いた結果を並べます。

| 半径 $\Delta$ | $\lambda$ | 一手 $p$ | 次の点での目的値 |
|---:|---:|---|---:|
| 1 | 160.1 | $(-0.037,\,-0.999)$ | 328.9 |
| 2 | 60.1 | $(-0.097,\,-1.998)$ | 188.7 |
| 4 | 10.4 | $(-0.485,\,-3.970)$ | 27.5 |
| 5.83 以上 | 0 | $(-3,\,-5)$ | 0 |

半径が小さいうちは $\lambda$ が大きく、一手は勾配の反対にほぼ沿います。半径を広げるほど $\lambda$ が下がり、一手はHessianの効いた向きへ回ります。
$\lambda=0$ になるのは、Newton法の一手 $(-3,\,-5)$（長さ $\sqrt{34}\approx5.83$）が円の中に収まったときです。このとき、信頼領域法の一手はNewton法と一致します。

初期半径を $1$ にすると、この問題は3回の反復で解けます。予測が毎回ぴったり当たるので、半径が $1\to2\to4$ と倍々に広がり、3回目でNewton法の一手が円に収まります。

### 椀が合わないとき、一手を却下する

Newton法の記事で使った、Rosenbrock関数 $f(x,y)=100(y-x^2)^2+(1-x)^2$ を初期点 $(-1.2,\,1)$ から解きます。素のNewton法は、途中の点で一手が行き過ぎ、目的値が $4.7$ から $1412$ に跳ね上がりました。
初期半径 $1$ の厳密な信頼領域法を、同じ点から追います。

| 反復 | 現在点 | 目的値 | 半径 $\Delta$ | $\lambda$ | 一手の長さ | $\rho$ | 判定 |
|---:|---|---:|---:|---:|---:|---:|---|
| 0 | $(-1.200,\,1.000)$ | 24.20 | 1 | 0 | 0.381 | 1.00 | 受理 |
| 1 | $(-1.175,\,1.381)$ | 4.732 | 1 | 1.357 | 1 | −0.43 | 却下、半径を $0.25$ へ |
| 2 | $(-1.175,\,1.381)$ | 4.732 | 0.25 | 6.459 | 0.25 | 1.01 | 受理、半径を $0.5$ へ |

反復0は、Newton法の一手が円の中に収まり、$\lambda=0$ です。この一手はNewton法と同じ点 $(-1.175,\,1.381)$ に着きます。
反復1の点で、Newton法の一手は長さが約 $4.95$ です。円の半径は $1$ なので、境界上の一手（$\lambda=1.357$）を採ります。それでもモデルは外れ、目的値は $4.73$ から $5.39$ に上がるので、却下します。
点は動かさずに半径を $0.25$ へ縮めます。すると予測が当たり、受理されます。

以降も、受理された一手では目的値が下がります。この初期点からは25回の反復で最小点 $(1,\,1)$ に着きます。この回数は、この問題と初期半径 $1$ での一例です。

## 向く条件・避ける条件

厳密な信頼領域法は、Hessianを分解する費用を払って、一手の質を買う手法です。
先に、次の項目を確認します。

| 項目 | 確認すること |
|---|---|
| Hessian | 解析式や自動微分で、精度よく評価できるか |
| 規模 | 密なHessianを保持し、分解できる大きさか |
| 曲率 | Hessianが不定になり得るか |
| 費用 | 部分問題の分解と、目的関数の評価のどちらが支配的か |

向く条件です。

- 密なHessianを保持して分解できる、中小規模の問題である（[滑らかな無制約の最小化](#/formulations/PA006)）
- Hessianと勾配を、解析式または自動微分で精度よく評価できる
- Hessianが不定になり得て、負の曲率の方向を正確に扱いたい
- 反復数を減らし、各反復の部分問題の質を優先したい

避ける、または切り替える条件です。

- 変数が多く、密なHessianの保持や分解が現実的でない → [Trust-region Krylov法](#/learn/trust-krylov)や[Trust-region Newton-CG](#/learn/trust-region-newton-cg)へ切り替える（[大規模な無制約の最小化](#/formulations/PA007)）
- Hessianが得られない、またはノイズに支配される → [BFGS法](#/learn/bfgs)などの準Newton法へ切り替える
- 部分問題の求解より、目的関数の評価のほうが桁違いに高価である

## Python

次の例は、厳密な信頼領域法を上の二次関数とRosenbrock関数に適用します。Hessianは解析式で渡します。

```python
import numpy as np
from scipy.optimize import minimize


def rosenbrock(x: np.ndarray) -> float:
    return float(100.0 * (x[1] - x[0] ** 2) ** 2 + (1.0 - x[0]) ** 2)


def rosenbrock_grad(x: np.ndarray) -> np.ndarray:
    dx0 = -400.0 * x[0] * (x[1] - x[0] ** 2) - 2.0 * (1.0 - x[0])
    dx1 = 200.0 * (x[1] - x[0] ** 2)
    return np.array([dx0, dx1])


def rosenbrock_hess(x: np.ndarray) -> np.ndarray:
    h00 = 1200.0 * x[0] ** 2 - 400.0 * x[1] + 2.0
    h01 = -400.0 * x[0]
    h11 = 200.0
    return np.array([[h00, h01], [h01, h11]])


# 二次関数 (x-1)^2 + 20 (y+2)^2 : Hessian は定数の diag(2, 40)
def quad(x):
    return (x[0] - 1.0) ** 2 + 20.0 * (x[1] + 2.0) ** 2


def quad_grad(x):
    return np.array([2.0 * (x[0] - 1.0), 40.0 * (x[1] + 2.0)])


def quad_hess(x):
    return np.diag([2.0, 40.0])


result = minimize(quad, x0=np.array([4.0, 3.0]), jac=quad_grad, hess=quad_hess,
                  method="trust-exact", options={"gtol": 1e-8})
print(result.success, result.x, result.nit, result.nhev)
# True [ 1. -2.] 3 4

result = minimize(rosenbrock, x0=np.array([-1.2, 1.0]), jac=rosenbrock_grad,
                  hess=rosenbrock_hess, method="trust-exact",
                  options={"gtol": 1e-8})
print(result.success, result.x, result.nit, result.nhev)
# True [1. 1.] 25 26
```

`nit` は反復回数です。二次関数は3回、Rosenbrock関数は25回で止まります。表の反復回数と一致します。
`method="trust-exact"` は `hess` を必須とします。`hess` を渡さないとSciPyはエラーで停止します。Hessianを解析的に書けない、または安価に評価できない問題では、別の手法を検討します。
出力はSciPy 1.18.1での結果です。利用中のバージョンの挙動は、[scipy.optimize.minimize](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.minimize.html)の公式リファレンスで確認します。

## 診断値

信頼領域法は、モデルの当たり具合を毎回数値にできます。それが診断の中心です。

- 勾配のノルム（gradient norm）
- 信頼半径
- 実際の減少と予測の減少の比 $\rho$
- 却下した一手の数
- 部分問題の内部での $\lambda$ の探索回数（固有値分解などをもとにした内部反復）

$\rho$ が1に近く、半径が縮まなければ、モデルは地形とよく合っています。

## 失敗・切替の兆候

- 信頼半径が縮み続ける → 二次モデルが地形と合っていない（Hessianの誤り、強い非線形性など） → 微分チェックと尺度を見直す
- 実際の減少と予測の減少の比が改善しない → 同じくモデルの誤り → 微分チェックと尺度を見直す
- 変数の増加で、密なHessianの保持や分解が遅い、またはメモリを圧迫する → 規模が固有値分解に合わない → Trust-region Krylov法やTrust-region Newton-CGへ切り替える
- Hessianが疎で構造を持ち、密な分解が本来不要な費用を払っている → 構造を使えていない → Krylov系や疎なソルバーを検討する
- 有限差分によるgradientやHessianのチェックが、解析式と合わない → 微分の実装が誤っている → 先に微分を直す

## 次に読む

- [Trust-region Newton-CG](#/learn/trust-region-newton-cg)：部分問題をCGで打ち切り、大規模へ広げる方法
- [Trust-region Krylov法](#/learn/trust-krylov)：Krylov部分空間で部分問題を近似する方法
- [信頼領域法の選び分け](#/learn/family.trust-region)：信頼領域法全体の選び分け
- [滑らかな無制約の最小化](#/formulations/PA006)：この手法が解く問題の標準形
