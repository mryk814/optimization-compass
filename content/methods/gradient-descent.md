---
content_id: method.gradient-descent
kind: method
method_id: M_GRADIENT_DESCENT
title_ja: Gradient Descent
title_en: Gradient Descent
summary: 勾配の反対方向へ進む一次法です。
prerequisites: [concept.convexity]
comparison_ids: [COMPARE_GRADIENT_FAMILY]
aliases: [/learn/method.gradient-descent]
comparison_aliases: [COMPARE_GRADIENT_FAMILY|/compare/gradient-quadratic]
source_ids: [S001, S002]
status: published
last_reviewed: 2026-07-15
---

## 直感

勾配の反対方向へ進む一次法です。

現在地 $x_k$ から、局所的に最も下がる方向 $-\nabla f(x_k)$ を選びます。

$$
x_{k+1} = x_k - \eta \nabla f(x_k)
$$

ここで $\eta$ は学習率です。

### 学習率を読む

- 小さすぎると、安全でも収束が遅くなります。
- 大きすぎると、谷を飛び越えて振動または発散します。
- 目的関数値と勾配ノルムを同じ反復軸で確認します。

::: tip
比較では初期点、停止条件、評価予算を揃えます。反復回数だけを公平性の根拠にしません。
:::

## Python

```python
import numpy as np

x = np.array([2.0, -1.0])
learning_rate = 0.1
for _ in range(100):
    x = x - learning_rate * gradient(x)
```

凸性との関係は[凸性の教材](#/learn/concept.convexity)で確認できます。
