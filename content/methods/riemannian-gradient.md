---
content_id: riemannian-gradient
kind: method
method_id: M_RIEMANNIAN_GRADIENT
title_ja: Riemann勾配法
title_en: Riemannian Gradient Descent
summary: 変数を制約多面体としてではなく多様体そのものとして扱い、接空間へ射影した勾配方向へ進んで写像で多様体上に戻す一次法です。
source_ids: [S044, S045, S071]
prerequisites: [method.gradient-descent]
related_ids: [riemannian-trust-region, family.manifold, family.smooth-local]
visualization_ids: [so3-riemannian-alignment]
comparison_ids: [COMPARE_SO3_PROJECTED_RIEMANNIAN]
status: published
last_reviewed: 2026-09-30
---

変数を制約多面体としてではなく多様体そのものとして扱い、接空間へ射影した勾配方向へ進んで写像で多様体上に戻す一次法です。

## 30秒でつかむ

地球の表面を歩くように、いまの位置の接平面で向きを決め、曲面へ戻ります。

Riemann勾配法は、多様体上の点を保ちながら、接空間へ射影した勾配で一歩進む一次法です。

同じSO(3)上の回転へ戻るなら、周囲の空間での一歩の射影と接空間での一歩は同じ更新でしょうか。
固定実行では、採用した回転行列がどちらも直交性と行列式を保っていても、最初の一歩の作り方と目標までの角度は異なります。

![単位行列から同じ、回転角がπに近い目標へ向かうProjected GradientとRiemannian Gradientの固定Python実行。上段は12回の更新での測地距離による残差、中央は最初の更新量のノルムと写像による補正、下段は採用した回転の直交性と行列式残差を示す。](./media/so3-update-diagnostic.svg "同じ目標、初期回転、歩幅、12評価で、周囲の空間での一歩と接空間での一歩を比較します。固定3対応・ノイズなしの教材であり、一般的な性能の順位付けや一般的な局所収束は示しません。")

緑の履歴がこの手法です。
目標への角度が下がることと、採用した回転行列がSO(3)構造を保つことを別々に確認します。

## 一手の意味

接空間へ勾配を射影し、接方向に進んだ点を多様体へ戻します。

$$
x_{k+1}=R_{x_k}\left(-\eta_k\,\operatorname{grad}f(x_k)\right)
$$

### 何を「制約」とみなさないか

球面上のベクトルや正規直交行列、固定ランク行列は、不等式・等式制約の集合としても表現できます。
Riemann勾配法はそれらを制約付き問題ではなく、解空間そのものが持つ幾何構造（多様体）として扱います。
球面上の点は常に「半径1の球面上」にあります。
正規直交行列も常に「直交行列の集合上」にあります。
この見方では多様体へ戻した後に採用する反復点が多様体上に留まるため、採用した反復点の可行性を別の制約処理で回復する必要がありません。

### 3つの操作で進む仕組み

Riemann勾配法の1 一歩は、次の3つの操作でできています。

1. 通常のユークリッド勾配 $\nabla f(x)$ を計算する
2. それを現在点における接空間へ射影し、Riemann勾配を作る
3. 接空間上で一歩を取り、多様体へ戻す写像という操作で多様体上の点に戻す

接空間は、現在点で多様体を局所的に近似する平坦な空間です。
ユークリッド勾配をそのまま使うと接空間からはみ出す成分が混ざるため、射影して多様体に沿う成分だけを残します。
多様体へ戻す写像は、接空間上の移動先を多様体上の近い点へ写す操作で、球面なら「移動後にノルムで割って半径1へ戻す」という単純な形を取れることもあります。

### 定番例としてのRayleigh商最小化

対称行列 $A$ に対して、単位球面 $\|x\|=1$ 上で

$$
f(x) = x^{\top} A x
$$

を最小化する問題は、Riemann勾配法の定番教材です。
解は $A$ の最小固有値に対応する固有ベクトルであり、制約なしの固有値問題として知られています。
球面上では勾配射影と多様体へ戻す写像の動きを直接確認できます。
これはStiefel多様体／Grassmann多様体／SO(3)へ進む足がかりになります。

## 小さな例

$A=\operatorname{diag}(1,2)$ として、単位円上で $x^TAx$ を最小化します。
$x=(1,1)/\sqrt2$、一歩の係数0.25から始めます。

| 反復 | $x_1$ | $x_2$ | 目的値 |
|---|---:|---:|---:|
| 1 | 0.8575 | 0.5145 | 1.2647 |
| 2 | 0.9482 | 0.3177 | 1.1009 |
| 3 | 0.9849 | 0.1729 | 1.0299 |

各行で点の長さは1です。
最小固有値1に対応する方向 $(1,0)$ へ近づきます。
これは正規化で戻す球面の例で、SO(3)の更新式とは異なります。

## 向く条件・避ける条件

### 向いている条件

| 条件 | 理由 |
|---|---|
| 変数が既知の多様体構造を持つ（球面、直交行列、固定ランク行列、回転群など） | 接空間射影と多様体へ戻す写像が定義できるため |
| 常に可行な点だけを維持したい | 多様体上に留まる限り制約違反が起こらないため |
| ユークリッド勾配または対応する勾配情報が得られる | 接空間への射影の元になるため |
| 座標の冗長性を減らしたい | 多様体表現がパラメータの余分な自由度を除くため |

一般の不等式・等式制約が主体で、変数が既知の多様体に一致しない場合は、[制約付きNLPの選び分け](#/learn/family.constrained-nlp)のほうが素直な入口です。

## Python

```python
import numpy as np


def rayleigh(x: np.ndarray, a: np.ndarray) -> float:
    return float(x @ a @ x)


def egrad(x: np.ndarray, a: np.ndarray) -> np.ndarray:
    return 2.0 * a @ x


def tangent_projection(x: np.ndarray, v: np.ndarray) -> np.ndarray:
    return v - (x @ v) * x


def retract(x: np.ndarray) -> np.ndarray:
    return x / np.linalg.norm(x)


rng = np.random.default_rng(0)
n = 6
m = rng.normal(size=(n, n))
a = (m + m.T) / 2.0

x = rng.normal(size=n)
x = retract(x)

step_size = 0.05
for _ in range(500):
    grad_euclid = egrad(x, a)
    grad_riemann = tangent_projection(x, grad_euclid)
    x = retract(x - step_size * grad_riemann)

eigvals, eigvecs = np.linalg.eigh(a)
min_eigval = eigvals[0]
min_eigvec = eigvecs[:, 0]

print(rayleigh(x, a), min_eigval)
print(min(np.linalg.norm(x - min_eigvec), np.linalg.norm(x + min_eigvec)))
```

`rayleigh(x, a)`は`np.linalg.eigh`から得た最小固有値へ近づきます。
`x`は符号の自由度を除いて最小固有ベクトルへ近づきます。
Stiefel多様体／Grassmann多様体／SO(3)などでは、接空間射影と多様体へ戻す写像の実装が変わります。
[Pymanopt](https://pymanopt.org/)や[Manopt](https://www.manopt.org/)の公式リファレンスで、利用バージョンに対応する多様体クラスを確認するほうが安全です。

## 診断値

- Riemann勾配ノルム
- 多様体へ戻す写像の誤差（多様体へ戻した後に多様体制約からどれだけずれるか）
- 直交性の誤差（直交系多様体の場合）
- 目的値の変化
- 一歩のノルム

## 失敗・切替の兆候

- 勾配射影が接空間の定義と一致しているかの検算が合わない
- 多様体へ戻した後の点が多様体条件（ノルム、直交性など）から外れていく
- 座標近傍依存の特異点付近で一歩が不安定になる
- 初期点によって収束先が大きく変わる
- 停滞から抜け出せず高精度化が必要になる

### SO(3)で接空間の一歩を見る

[Riemannian 更新のTheater](#/theater/learning/SCENARIO_SO3_RIEMANNIAN_ALIGNMENT)では、リー代数上の一歩を指数写像でSO(3)へ戻す流れを追えます。
目的関数値と、直交性・行列式の残差を分けて確認します。

[射影による更新との比較](#/compare/COMPARE_SO3_PROJECTED_RIEMANNIAN)は、同じ目標・初期回転・目的関数・一歩の係数・12回の評価を使います。
変えるのは、接空間の一歩を使うか、周囲の空間での一歩をQR射影するかだけです。

これは回転角がπに近い固定目標、ノイズなし、単一初期値の教育用比較です。
反復数や最終損失から一般的な速度の順位を付けるものではありません。

## 次に読む

より頑健な局所収束や鞍点脱出が必要な場合は[Riemann信頼領域法](#/learn/riemannian-trust-region)、多様体手法全体の選び分けは[Riemann多様体最適化の選び分け](#/learn/family.manifold)で確認できます。

- 問題の形を確認する: [回転群上の最適化](#/formulations/PA037)
