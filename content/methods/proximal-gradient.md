---
content_id: proximal-gradient
kind: method
method_id: M_PROX_GRADIENT
title_ja: 近接勾配法
title_en: Proximal gradient method
summary: 滑らかな項には勾配一歩を使い、非滑らかな項にはproximal operatorを使う複合凸最適化法です。
source_ids: [S055, S066]
prerequisites: [method.gradient-descent, concept.convexity]
related_ids: [fista, admm]
aliases: [/learn/proximal-gradient]
status: published
last_reviewed: 2026-09-30
---

滑らかな項には勾配一歩を使い、非滑らかな項にはproximal operatorを使う複合凸最適化法です。

## 30秒でつかむ

滑らかな坂では下り、角のある罰則では別の調整を行うように、一歩を二つへ分けます。

Proximal Gradientは、滑らかなな部分を勾配で下げたあと、非滑らかな正則化や単純制約を近接演算へ渡します。
二つの構造を一つの微分可能な目的へ無理に平滑化しないことが主線です。

- 見ているもの: 目的値、近接勾配写像、非ゼロ成分と活性集合
- 動かしているもの: 現在点、一歩の係数、勾配、近接演算
- 前進の判断: mapping normと目的値が下がり、supportが安定すること
- 恐れていること: 近接演算の高コスト、一歩の保守性、強いノイズ、coupling 制約

## 一手の意味

### 対象となる形

$$
\min_x\; F(x)=f(x)+g(x)
$$

ここで、

- $f$ は微分可能で勾配が利用できる
- $g$ は非滑らかでもよいがproximal operatorを計算できる

とします。
更新は

$$
x_{k+1}=\operatorname{prox}_{\eta g}\left(x_k-\eta\nabla f(x_k)\right)
$$

です。

まず滑らかな項を下げる勾配 一歩を行い、その後に正則化や単純制約を近接演算で反映します。

### Proxは何をしているか

$$
\operatorname{prox}_{\eta g}(v)
=\arg\min_x\left(g(x)+\frac{1}{2\eta}\|x-v\|^2\right)
$$

L1正則化ならsoft-thresholding、box制約なら区間への射影になります。
難しい非滑らか項を持っていても、近接演算が簡単なら汎用NLPへ無理に平滑化せず構造を使えます。

### Step sizeと停止をどう判断するか

$f$ の勾配が $L$-Lipschitzなら、固定一歩は $\eta\le 1/L$ が目安です。
$L$が不明ならbacktrackingを使います。

最初に見る値:

- 目的値
- 近接勾配写像 norm
- 一歩の係数
- sparsity / active set
- function / 勾配 / 近接演算 evaluation数
- validation metric（統計推定の場合）

目的値変化だけで止めると、flatな領域で最適性が弱いまま停止する場合があります。

## 小さな例

$F(x)=\frac12(x-3)^2+0.8|x|$ を $x=0$、$\eta=0.25$ から更新します。
勾配で進んだ値から、0.2をソフト閾値で引きます。

| 反復 | 更新後の $x$ | $F(x)$ |
|---|---:|---:|
| 1 | 0.5500 | 3.4413 |
| 2 | 0.9625 | 2.8457 |
| 3 | 1.2719 | 2.5107 |

最適点は $x=2.2$ です。
一歩ごとに近づきますが、目的値変化だけで停止せず近接勾配写像も確認します。

## 向く条件・避ける条件

### 向いている条件

- 滑らかな loss + L1、group penalty、indicator 制約など
- 疎な・大規模で、一反復を安価にしたい
- 勾配と近接演算を別々に実装できる
- exactなHessian 求解より多数の軽い反復が適する

## Python

```python
import numpy as np


def soft_threshold(value: np.ndarray, threshold: float) -> np.ndarray:
    return np.sign(value) * np.maximum(np.abs(value) - threshold, 0.0)


rng = np.random.default_rng(7)
a = rng.normal(size=(40, 8))
true_x = np.array([1.5, 0.0, -2.0, 0.0, 0.0, 0.7, 0.0, 0.0])
b = a @ true_x + 0.05 * rng.normal(size=40)
lam = 0.1

lipschitz = np.linalg.norm(a, ord=2) ** 2
step = 1.0 / lipschitz
x = np.zeros(a.shape[1])

for _ in range(2000):
    gradient = a.T @ (a @ x - b)
    next_x = soft_threshold(x - step * gradient, step * lam)
    if np.linalg.norm(next_x - x) < 1e-10:
        x = next_x
        break
    x = next_x

print(x)
```

## 診断値

各反復の目的値、可行性、更新幅を同じ時点で記録します。
目的値だけで停止を決めません。

## 失敗・切替の兆候

- 近接演算自体が高価な最適化問題になる → decompositionや専用ソルバーと比較する
- $f$ が非滑らか、または勾配が強いノイズを含む → subgradientまたはstochastic methodを検討する
- 変数尺度により単一一歩の係数が極端に保守的 → 尺度調整、backtracking、preconditioningを確認する
- 強いcoupling 制約を単純射影で表せない → 主-双対またはconstrained ソルバーを検討する
- basic法の収束が遅い → [FISTA](#/learn/fista)、再始動、preconditioningを検討する

::: note
FISTAの反復数が少なくても、必ずしも実時間が短いとは限りません。
勾配と近接演算の実コスト、再始動、停止条件を揃えて比較します。
:::

## 次に読む

[Branch-and-Cut](#/learn/branch-and-cut)で主問題の探索を確認します。
[制約付き連続最適化](#/learn/constrained-continuous)で連続部分問題を確認します。

- 問題の形を確認する: [非滑らかな複合凸最適化](#/formulations/PA010)
