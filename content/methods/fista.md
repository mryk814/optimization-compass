---
content_id: fista
kind: method
method_id: M_FISTA
title_ja: FISTA
title_en: Fast Iterative Shrinkage-Thresholding Algorithm
summary: 近接勾配法へNesterov型の外挿を加え、凸複合問題の目的gapをより速く減らす加速一次法です。
source_ids: [S055, S066, S067]
prerequisites: [proximal-gradient]
related_ids: [proximal-gradient, admm]
aliases: [/learn/fista]
status: published
last_reviewed: 2026-09-30
---

近接勾配法へNesterov型の外挿を加え、凸複合問題の目的gapをより速く減らす加速一次法です。

## 30秒でつかむ

歩く向きが続いているとき、直前の移動を次の一歩へ足して先を狙うような加速です。

FISTAは、勾配一歩の前に過去の移動を使った外挿を入れ、近接勾配法より目的gapを速く減らすことを狙います。

- 見ているもの: 目的値、近接勾配写像、非ゼロ成分と活性集合
- 動かしているもの: 現在点、外挿点、一歩、近接演算
- 前進の判断: 最良目的値と目的gapが減ること
- 恐れていること: 外挿による振動、supportの入れ替わり、variantの違いによる比較のずれ

速さは現在の目的値の単調減少を意味しません。

## 一手の意味

### 仕組み

basic proximal 勾配は現在点から勾配一歩と近接演算 一歩を行います。
FISTAは過去の移動を使った外挿点 $y_k$ から一歩を行います。

$$
x_{k+1}=\operatorname{prox}_{\eta g}\left(y_k-\eta\nabla f(y_k)\right)
$$

$$
t_{k+1}=\frac{1+\sqrt{1+4t_k^2}}{2}
$$

$$
y_{k+1}=x_{k+1}+\frac{t_k-1}{t_{k+1}}(x_{k+1}-x_k)
$$

凸条件下では、basic法の代表的な $O(1/k)$ に対し、FISTAは目的gapについて $O(1/k^2)$ のrateを持ちます。

## 小さな例

$F(x)=\frac12(x-3)^2+0.8|x|$ を更新します。
初期値は $x=y=0$ と $t=1$ です。
一歩の係数は $\eta=0.25$ とします。

| 反復 | $x$ | 次の外挿点 $y$ | $F(x)$ |
|---|---:|---:|---:|
| 1 | 0.5500 | 0.5500 | 3.4413 |
| 2 | 0.9625 | 1.0787 | 2.8457 |
| 3 | 1.3590 | 1.5312 | 2.4336 |

2反復目から、外挿点が現在点より先へ出ます。
同じ問題の近接勾配法では、3反復目は $x=1.2719$ です。
この差は固定した3反復の挙動で、実時間の性能順位を示しません。

## 向く条件・避ける条件

### まず確認すること

- 目的関数が滑らかなな項と、近接演算を計算できる項の複合形になっているか
- 勾配と近接演算が安価に計算できるか
- 凸条件下のrateを使う問題か、非凸問題として挙動を別に評価するか
- backtracking、再始動、monotonicityのvariantを比較条件として記録できるか

### 向く条件・避ける条件

向きやすい条件:

- 凸な滑らかな + proximable構造
- L1など非滑らか正則化
- 勾配と近接演算が安価
- 高精度より中程度の精度を多数反復で得たい
- basic proximal 勾配が安定だが遅い

避ける条件:

- 非凸問題へ理論rateをそのまま適用する
- 近接演算が支配的で、分解や専用ソルバーのほうが適している

## Python

```python
import numpy as np


def soft_threshold(value: np.ndarray, threshold: float) -> np.ndarray:
    return np.sign(value) * np.maximum(np.abs(value) - threshold, 0.0)


rng = np.random.default_rng(11)
a = rng.normal(size=(60, 12))
true_x = np.zeros(12)
true_x[[1, 5, 9]] = [1.2, -2.0, 0.8]
b = a @ true_x + 0.05 * rng.normal(size=60)
lam = 0.08
step = 1.0 / (np.linalg.norm(a, ord=2) ** 2)

x = np.zeros(a.shape[1])
y = x.copy()
t = 1.0

for _ in range(1500):
    gradient = a.T @ (a @ y - b)
    next_x = soft_threshold(y - step * gradient, step * lam)
    next_t = (1.0 + np.sqrt(1.0 + 4.0 * t * t)) / 2.0
    next_y = next_x + ((t - 1.0) / next_t) * (next_x - x)

    if np.linalg.norm(next_x - x) < 1e-10:
        x = next_x
        break
    x, y, t = next_x, next_y, next_t

print(x)
```

## 診断値

「速い」を現在の目的値だけで判断すると、外挿による一時的な増加を見落とします。

monotone variantやadaptive 再始動を使うと実務上安定する場合がありますが、variantと条件を記録します。

- 最良目的値
- 現在の目的値
- 近接勾配写像
- iterate difference
- 非ゼロ成分と活性集合の変化
- 再始動回数

## 失敗・切替の兆候

- 目的値が大きく振動する → 再始動やmonotone variantを検討する
- supportが何度も入れ替わる → 一歩、尺度調整、regularizationを確認する
- backtrackingが毎回縮む → 勾配のLipschitz モデルを確認する
- 近接演算が支配的 → decompositionや専用ソルバーを検討する

::: warning
FISTAという名前だけでは、実装の違いは分かりません。
後退探索／再始動／単調性／停止条件を確認します。
比較時はvariantを明記します。
:::

## 次に読む

[近接勾配法](#/learn/proximal-gradient)で外挿を使わない基本の一歩と比較し、分解が必要なら[ADMM](#/learn/admm)も確認します。

- 問題の形を確認する: [非滑らかな複合凸最適化](#/formulations/PA010)
