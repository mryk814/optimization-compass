---
content_id: admm
kind: method
method_id: M_ADMM
title_ja: 交互方向乗数法（ADMM）
title_en: Alternating Direction Method of Multipliers
summary: 分離しやすい部分問題を交互に解き、主残差と双対残差を減らして一致を作る分割最適化法です。
source_ids: [S012, S055, S061, S062]
prerequisites: [concept.convexity]
related_ids: [proximal-gradient, fista, lp-qp-conic]
aliases: [/learn/admm]
status: published
last_reviewed: 2026-09-30
---

分離しやすい部分問題を交互に解き、主残差と双対残差を減らして一致を作る分割最適化法です。

## 30秒でつかむ

二人で同じ予定を作るとき、各自の都合を別々に直し、最後に食い違いを調整するような手法です。

変数を分け、滑らかな項と非滑らかな正則化を別々の部分問題として扱います。
制約や分散データも、構造に応じて分離します。

- 見ているもの: 主残差、双対残差、目的値、部分問題の求解誤差
- 動かしているもの: $x$、$z$、双対変数 $u$、罰則係数 $\rho$
- 前進の判断: 主残差と双対残差の両方が下がり、一致が進むこと

## 一手の意味

一致制約 $x=z$ の場合、各項を別々に最小化してから不一致を双対変数へ加えます。

$$
x_{k+1}=\arg\min_x\left(f(x)+\frac{\rho}{2}\|x-z_k+u_k\|^2\right)
$$

$$
z_{k+1}=\arg\min_z\left(g(z)+\frac{\rho}{2}\|x_{k+1}-z+u_k\|^2\right),\qquad
u_{k+1}=u_k+x_{k+1}-z_{k+1}
$$

### 仕組み

#### 変数を分ける理由

代表形は

$$
\min_{x,z}\; f(x)+g(z) \quad \text{subject to}\quad Ax+Bz=c
$$

です。
$f$ と $g$ を別々に扱うことで、各部分問題の解きやすい構造を使えます。
滑らかな項と非滑らかな正則化のほか、制約や分散データも分割の対象です。

scaled ADMMでは概ね次を繰り返します。

1. $x$ を更新する
2. $z$ を更新する
3. 双対変数 $u$ を更新する

## 小さな例

$\frac12(x-3)^2+0.8|z|$ を $x=z$ のもとで最小化します。
$\rho=1$、$x=z=u=0$ から始めます。
Python節の分割更新を1変数にした実行です。

| 反復 | $x$ | $z$ | $u$ | 主残差 $|x-z|$ |
|---|---:|---:|---:|---:|
| 1 | 1.500 | 0.700 | 0.800 | 0.800 |
| 2 | 1.450 | 1.450 | 0.800 | 0.000 |
| 3 | 1.825 | 1.825 | 0.800 | 0.000 |

2反復目に主残差が消えても、$z$ はまだ変わります。
双対残差も見る必要がある例です。

## 向く条件・避ける条件

### まず確認すること

各部分問題が閉形式、近接演算、疎な線形求解などで解きやすいときに有効です。
分割後の部分問題が元問題より難しくなる場合は、分割の利点を得にくくなります。

### 向いている条件・避ける条件

向いている:

- 凸な分離構造
- 疎な QP、L1正則化、一致、分散最適化
- 近接演算や射影が安価
- 初期解の再利用を繰り返し利用したい

避ける／条件付き:

- 分割後の部分問題が元問題より難しい
- 高精度解が必要だが残差収束が遅い
- 非凸ADMMを理論保証付き凸ADMMと同一視している
- $\rho$や尺度により残差が一方だけ停滞する

## Python

L1正則化の分割を確認する小さな例です。
次は $\frac{1}{2}\|x-b\|^2 + \lambda\|z\|_1$、$x=z$ の小さな例です。

```python
import numpy as np


def soft_threshold(value: np.ndarray, threshold: float) -> np.ndarray:
    return np.sign(value) * np.maximum(np.abs(value) - threshold, 0.0)


b = np.array([3.0, -0.4, 1.2])
lam = 0.8
rho = 1.0
x = np.zeros_like(b)
z = np.zeros_like(b)
u = np.zeros_like(b)

for _ in range(200):
    x = (b + rho * (z - u)) / (1.0 + rho)
    previous_z = z.copy()
    z = soft_threshold(x + u, lam / rho)
    u = u + x - z

    primal = np.linalg.norm(x - z)
    dual = rho * np.linalg.norm(z - previous_z)
    if primal < 1e-8 and dual < 1e-8:
        break

print(z, primal, dual)
```

## 診断値

目的値だけでは不十分です。

- 主残差: $r_k = Ax_k + Bz_k - c$
- 双対残差: $s_k$（一致変数の変化に対応）
- 目的値
- 部分問題の求解誤差
- 罰則係数 $\rho$

主残差だけ小さくても双対残差が大きければ、変数は制約を満たしつつまだ動いています。
逆も同様です。

::: warning
ADMMの1反復が軽いとは限りません。
各部分問題で因数分解やinner 最適化を行う場合、inner 求解の費用と精度も記録します。
:::

## 失敗・切替の兆候

$\rho$は単なる学習率ではなく、一致 violationへの重みと数値条件数へ影響します。

- 主残差が双対残差より極端に大きい → $\rho$を上げる候補
- 双対残差が極端に大きい → $\rho$を下げる候補
- 頻繁に変える → 因数分解再利用や理論条件への影響を確認

実装によってadaptive ruleが異なるため、defaultを無条件に横比較しません。

## 次に読む

単一変数で直接近接演算 一歩を使える場合は[proximal 勾配](#/learn/proximal-gradient)の方が単純なことがあります。

- 問題の形を確認する: [非滑らかな複合凸最適化](#/formulations/PA010)
