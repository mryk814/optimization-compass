---
content_id: newton-cg
kind: method
method_id: M_NEWTON_CG
title_ja: Newton-CG法
title_en: Newton Conjugate Gradient
summary: Hessian全体を保持せずHessian-vector積と共役勾配法でNewton方向を近似し、滑らかな大規模問題へ二階情報を使う局所法です。
source_ids: [S002, S056]
related_ids: [family.smooth-local, newton-method, trust-region-newton-cg]
status: published
last_reviewed: 2026-09-30
---

Hessian全体を保持せずHessian-vector積と共役勾配法でNewton方向を近似し、滑らかな大規模問題へ二階情報を使う局所法です。

## 30秒でつかむ

曲がり方を記した分厚い台帳（Hessian）を、持ち歩けない場面を想像してください。
代わりに「この向きへ動くと、傾きはどう変わるか」を、必要な向きだけ問い合わせます。
数回の問い合わせでも、Newton法の一手にかなり近い向きが作れます。Newton-CG法は、この問い合わせを使って一手の向きを決めます。

- **見るもの**: 勾配、Hessianとベクトルの積（Hessian-vector product、HVP）、内側の共役勾配法（CG）の残差
- **動かすもの**: 現在点と、内側のCGで近似した一手の向き。一手の長さは外側の直線探索（line search）で決める
- **前進の判断**: 直線探索のあとに目的関数値が下がり、勾配のノルム（gradient norm）が小さくなること

外側で点を動かし、内側で向きを作る二重構造です。内側を長く回すほど向きはNewton方向に近づきますが、HVPの回数が増えます。
気をつける点は三つあります。曲率が負の方向、HVPの誤り、内側のCGの回しすぎです。

## 一手の意味

Newton法の一手は、連立一次方程式 $H(x_k)\,p_k=-\nabla f(x_k)$ の解でした。
Newton-CG法は、この方程式を共役勾配法（CG）で途中まで解きます。CGが必要とするのは積 $H(x_k)v$ の値だけで、$H$ の行列は要りません。

得られた向き $p_k$ に、直線探索で決めた長さ $\alpha_k$ を掛けて進みます。

$$
x_{k+1}=x_k+\alpha_k p_k
$$

式は「Newton方向を近似で求め、行き過ぎないように長さを調整して進む」と言っています。

内側のCGは、次の二つのどちらかが起きたところで止めます。

- **残差が十分に小さくなる**: 残差が勾配の大きさの一定割合 $\eta_k$ 以下になったら止めます。割合は $\eta_k=\min(0.5,\sqrt{\lVert\nabla f(x_k)\rVert})$ のように、勾配が小さいほど厳しくします。SciPyの実装もこの形です。
- **負の曲率に出会う**: CGの向き $d$ に対して $d^\top H d\le 0$ になったら、その向きに二次モデルの底はありません。そこで打ち切ります。SciPyでは、最初の内側反復で起きたときは最急降下方向に切り替えます。

早く止めれば一手は安くなりますが、方向の質は落ちます。外側の直線探索と内側の許容と負の曲率への対応は、まとめて一つのアルゴリズムです。

### HVPの作り方

HVPは、Hessian行列を組み立てずに、その作用だけを計算する方法です。

- 解析式や自動微分なら、正確な $H(x)v$ が得られます。
- 有限差分で勾配の差から近似することもできます。この場合は差分の幅と数値誤差が加わります。

自動微分でHVPを得るときも、方向微分のチェックを行います。勾配と同じ目的関数を微分しているか、確認するためです。

## 小さな例

### 二次関数で内側のCGを追う

[Newton法](#/learn/newton-method)と同じ関数 $f(x,y)=(x-1)^2+20(y+2)^2$ を、初期点 $(4,\,3)$ から解きます。
Hessianは $\mathrm{diag}(2,\,40)$ ですが、ここでは積 $Hv$ だけを使います。SciPyの規則で内側を止めた結果です。

| 外側 $k$ | 現在点 | 勾配のノルム | 内側のCG回数 | 一手の長さ | 次の点 | 目的値 |
|---:|---|---:|---:|---:|---|---:|
| 0 | $(4,\,3)$ | 200.1 | 1 | 5.007 | $(3.850,\,-2.004)$ | 509 → 8.12 |
| 1 | $(3.850,\,-2.004)$ | 5.70 | 2 | 2.850 | $(1,\,-2)$ | 8.12 → 0 |

反復0では、勾配が大きいので許容が緩く、内側のCGは1回で止まります。残差は最初の約2.8%まで減っています。
この1回のCGは、最急降下方向への厳密な直線探索と同じです。そのため、[BFGS法](#/learn/bfgs)の表の反復0と同じ点 $(3.850,\,-2.004)$ に着きます。

反復1では、勾配が5.70まで下がり、許容も厳しくなります。内側の1回目では残差が許容を超えるので、2回目に進みます。
2回目で得た一手は、Newton方向 $(-2.850,\,0.004)$ です。この問題は2変数なので、CGは高々2回で厳密な解に達します。

Newton法は同じ問題を1回で解きました。Newton-CG法は、外側2回でHVP合計3回です。変数が多い問題では、内側を厳密に解き切る余裕がないので、この打切りが効いてきます。

### Rosenbrock関数では打切りが効く

Rosenbrock関数 $f(x,y)=100(y-x^2)^2+(1-x)^2$ を、初期点 $(-1.2,\,1)$ から解きます。素のNewton法は6回の更新で最小点 $(1,\,1)$ に着きました。
SciPyのNewton-CGは、既定の許容で外側83回、HVP142回かかります。内側のCGは毎回1〜2回で止まっています。

内側を短く切った一手は、Newton方向から離れます。その分だけ、外側の反復が増えます。
この回数は、この問題と初期点、既定の許容での一例です。手法どうしの優劣ではありません。

## 向く条件・避ける条件

Newton-CG法は、Hessianを作れないほど大きい問題に、曲率の情報を持ち込む手法です。
先に、次の項目を確認します。

| 項目 | 確認すること |
|---|---|
| 勾配 | 正確、または十分に信頼できるか |
| HVP | 行列を作らずに $H(x)v$ を計算できるか |
| 規模 | 密なHessianを保持できない大きさか |
| 曲率 | 非凸の領域で負の曲率が現れるか |
| 制約 | 原則は無制約。制約は別の手法で扱う |

向く条件です。

- 滑らかな大規模の無制約問題である（[大規模な無制約の最小化](#/formulations/PA007)）
- 勾配とHVPを効率よく計算できる
- BFGS法の密な行列を避けつつ、曲率を使いたい
- 解の近くで、高精度に仕上げたい

避ける、または切り替える条件です。

- 不連続、強いノイズ、離散変数を含む
- HVPが目的関数と食い違っている → 微分の実装を先に直す
- 直線探索の追加評価を許せない
- 一般制約や大域最適性の証明が必要である
- 負の曲率が頻繁に出る → [trust-region Newton-CG](#/learn/trust-region-newton-cg)へ切り替える
- Hessianが小さく密に持てる → [Newton法](#/learn/newton-method)と比べる（[滑らかな無制約の最小化](#/formulations/PA006)）

## Python

次の例は、積 $Hv$ だけを渡してNewton-CG法を実行する最小例です。一つ目は上の二次関数、二つ目はRosenbrock関数です。

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


result = minimize(quad, np.array([4.0, 3.0]), jac=quad_grad,
                  hessp=quad_hessp, method="Newton-CG")
print(result.success, result.x, result.nit, result.nhev)
# True [ 1. -2.] 3 4

result = minimize(rosenbrock, np.array([-1.2, 1.0]), jac=rosenbrock_grad,
                  hessp=rosenbrock_hessp, method="Newton-CG")
print(result.success, result.x, result.nit, result.nhev)
# True [0.9999826  0.99996514] 83 142
```

出力の `nit` は外側の反復回数、`nhev` はHVPを呼んだ回数です。
二次関数の `nit` は3で、表の2回に、収束を確かめる1回が加わります。`nhev` が4なのも、この確認の1回を含むためです。
出力はSciPy 1.18.1での結果です。利用中のバージョンのオプションは、[scipy.optimize.minimize](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.minimize.html)の公式リファレンスで確認します。

## 診断値

何を記録するかで、内側と外側のどちらに問題があるかが分かります。

- 勾配のノルム（gradient norm）
- 外側の反復回数と、内側のCGの反復回数
- HVPの呼び出し回数の合計
- 直線探索の試行回数
- 曲率 $p^\top H p$（負や0に近い値は、二次モデルの底がない向きを示す）
- 一手のノルムと、目的値の変化

HVPの回数を数えると、一階法や準Newton法と同じ土俵で費用を比べられます。

## 失敗・切替の兆候

- 内側のCGが毎回上限まで走る → 条件数が悪い → 前処理（preconditioning）、許容の緩和、L-BFGSを検討する
- 負の曲率や直線探索の失敗が多い → 非凸の領域で、二次モデルの向きが下り方向にならない → trust-region Newton-CGへ切り替える
- HVPの計算が目的関数の評価より重い → 曲率を使う利点が費用に見合わない → 一階法や準Newton法と比較する
- 勾配チェックが合わない → 微分の実装が誤っている → アルゴリズムを変える前に、微分の実装を直す
- 解の近くでは速いが、初期点からは不安定 → 大域化の方針が合わない → 直線探索の条件や、信頼領域への切替を見直す

## コラム: HVPの費用を含めて比較する

Newton-CG法の利点は、Hessian行列を作らずに曲率を使えることです。
一方で、HVPの回数と内側のCGの反復が増えると、費用は膨らみます。
そのとき、単純な一階法や準Newton法のほうが有利になる場合があります。外側の反復回数だけでなく、HVPの回数まで数えて比べます。

## 次に読む

- [Newton法](#/learn/newton-method)：Hessianを直接使う一手との違い
- [trust-region Newton-CG](#/learn/trust-region-newton-cg)：非凸の領域で、局所モデルを信頼できる範囲だけで使う方法
- [非線形共役勾配法](#/learn/nonlinear-cg)：Hessianを使わずに、メモリをさらに単純化する方法
- [大規模な無制約の最小化](#/formulations/PA007)：この手法が解く問題の標準形
