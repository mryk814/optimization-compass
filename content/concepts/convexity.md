---
content_id: concept.convexity
kind: concept
title_ja: 凸性
title_en: Convexity
summary: 局所的な下り坂と大域的な最適性をつなぐ性質です。
related_ids: [method.gradient-descent]
source_ids: [S001]
status: published
last_reviewed: 2026-07-15
---

## 直感

局所的な下り坂と大域的な最適性をつなぐ性質です。

2点を結ぶ線分が関数のグラフより上にあれば、関数は凸です。

$$
f(\theta x + (1-\theta)y) \leq \theta f(x) + (1-\theta)f(y),\quad 0 \leq \theta \leq 1
$$

![凸関数と2点を結ぶ線分の模式図](./media/convexity.svg "凸関数では2点を結ぶ線分が関数のグラフより上にあります。")

### 最適化での意味

1. 局所最小解は大域最小解になります。
2. 強凸性など追加条件があれば、収束率も評価できます。
3. 非凸問題では、初期値や探索戦略の影響を別に調べます。

::: note
凸集合と凸関数は別の定義です。制約集合と目的関数の両方を確認してください。
:::
