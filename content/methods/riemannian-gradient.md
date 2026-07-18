---
content_id: riemannian-gradient
kind: method
method_id: M_RIEMANNIAN_GRADIENT
title_ja: Riemann勾配法
title_en: Riemannian Gradient Descent
summary: 変数を制約多面体としてではなく多様体そのものとして扱い、接空間へ射影した勾配方向へ進んでretractionで多様体上に戻す一次法です。
source_ids: [S044, S045, S071]
prerequisites: [method.gradient-descent]
related_ids: [riemannian-trust-region, family.manifold, family.smooth-local]
status: published
last_reviewed: 2026-07-16
---

変数を制約多面体としてではなく多様体そのものとして扱い、接空間へ射影した勾配方向へ進んでretractionで多様体上に戻す一次法です。

## 30秒でつかむ

Riemann勾配法は、多様体上の点を保ちながら、接空間へ射影した勾配で一歩進む一次法です。

## 何を「制約」とみなさないか

球面上のベクトル、正規直交な行列、固定rankの行列などは、不等式や等式制約の集合としても表現できます。しかしRiemann勾配法は、それらを制約付き問題としてではなく、解空間そのものが持つ幾何構造（多様体）として扱います。球面上の点は常に「半径1の球面上」にあり、正規直交行列は常に「直交行列の集合上」にあります。この見方に立つと、探索の各stepは多様体の外へ出ることがなく、制約違反という概念自体が消えます。

## 3つの操作で進む仕組み

Riemann勾配法の1 stepは、次の3つの操作でできています。

1. 通常のEuclid勾配 $\nabla f(x)$ を計算する
2. それを現在点における接空間へ射影し、Riemann勾配を作る
3. 接空間上でstepを取り、retractionという操作で多様体上の点に戻す

接空間は、現在点で多様体を局所的に近似する平坦な空間です。Euclid勾配をそのまま使うと接空間からはみ出す成分が混ざるため、射影して多様体に沿う成分だけを残します。retractionは、接空間上の移動先を多様体上の近い点へ写す操作で、球面なら「移動後にnormで割って半径1へ戻す」という単純な形を取れることもあります。

## 定番例としてのRayleigh商最小化

対称行列 $A$ に対して、単位球面 $\|x\|=1$ 上で

$$
f(x) = x^{\top} A x
$$

を最小化する問題は、Riemann勾配法の定番の教材です。この問題の解は $A$ の最小固有値に対応する固有ベクトルであり、制約なしの固有値問題として知られています。球面という単純な多様体の上で、勾配射影とretractionの動きを直接確認できるため、より複雑なStiefel多様体やGrassmann多様体、SO(3)へ進む前の足がかりになります。

## 向いている条件

| 条件 | 理由 |
|---|---|
| 変数が既知の多様体構造を持つ（球面、直交行列、固定rank行列、回転群など） | 接空間射影とretractionが定義できるため |
| 常に可行な点だけを維持したい | 多様体上に留まる限り制約違反が起こらないため |
| Euclid勾配または対応する勾配情報が得られる | 接空間への射影の元になるため |
| 座標の冗長性を減らしたい | 多様体表現がparameterの余分な自由度を除くため |

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

`rayleigh(x, a)`は`np.linalg.eigh`から得た最小固有値へ近づき、`x`は符号の自由度を除いて最小固有ベクトルへ近づきます。より一般の多様体（Stiefel、Grassmann、SO(3)など）を扱う場合は、接空間射影とretractionの実装を自作するよりも[Pymanopt](https://pymanopt.org/)や[Manopt](https://www.manopt.org/)の公式referenceで利用versionに対応する多様体クラスを確認するほうが安全です。

## 診断値

- Riemannian gradient norm
- retraction error（retraction後に多様体制約からどれだけずれるか）
- orthogonality error（直交系多様体の場合）
- objective change
- step norm

## 失敗・切替の兆候

- 勾配射影が接空間の定義と一致しているかの検算が合わない
- retraction後の点が多様体条件（norm、直交性など）から外れていく
- chart依存の特異点付近でstepが不安定になる
- 初期点によって収束先が大きく変わる
- 停滞から抜け出せず高精度化が必要になる

## 次に読む

より頑健な局所収束や鞍点脱出が必要な場合は[Riemann trust-region法](#/learn/riemannian-trust-region)、多様体手法全体の選び分けは[Riemann多様体最適化の選び分け](#/learn/family.manifold)で確認できます。
