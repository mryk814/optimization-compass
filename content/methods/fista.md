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
last_reviewed: 2026-07-15
---

近接勾配法へNesterov型の外挿を加え、凸複合問題の目的gapをより速く減らす加速一次法です。

## 加速の仕組み

basic proximal gradientは現在点からgradient + prox stepを行います。FISTAは過去の移動を使った外挿点 $y_k$ からstepを行います。

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

## 「速い」が単調とは限らない

外挿により目的値が一時的に増えたり、解の周囲で振動したりすることがあります。次を分けて見ます。

- best-so-far objective
- current objective
- proximal-gradient mapping
- iterate difference
- support / active setの変化
- restart回数

monotone variantやadaptive restartを使うと実務上安定する場合がありますが、variantと条件を記録します。

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

## 向いている条件

- convexなsmooth + proximable構造
- L1など非滑らか正則化
- gradientとproxが安価
- 高精度より中程度の精度を多数反復で得たい
- basic proximal gradientが安定だが遅い

## 失敗・切替の兆候

- objectiveが大きく振動する → restartやmonotone variant
- supportが何度も入れ替わる → step、scaling、regularizationを確認
- backtrackingが毎回縮む → gradientのLipschitz modelが悪い
- proxが支配的 → decompositionや専用solverを検討
- 非凸問題へ理論rateをそのまま適用している → 適用範囲を明示

::: warning
FISTAという名前だけでは、backtracking、restart、monotonicity、停止条件が分かりません。比較時はvariantを明記します。
:::
