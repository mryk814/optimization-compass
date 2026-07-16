---
content_id: concept.derivative-free
kind: concept
canonical_entity_type: feature
canonical_entity_id: F_DERIVATIVE_ACCESS
title_ja: Derivative-free optimization
title_en: Derivative-free optimization
summary: 微分を直接使わず、関数値の比較から探索する考え方です。
related_ids: [method.nelder-mead]
visualization_ids: [nelder-mead-quadratic]
source_ids: [S001, S002]
status: published
last_reviewed: 2026-07-16
---

## 直感

微分を直接使わず、関数値の比較から探索する考え方です。

> 微分不能という意味だけではありません。勾配が得られない、信頼できない、または取得コストが高い場合も対象です。

### 向いている状況

| 状況 | 確認すること |
| --- | --- |
| 実験・シミュレーション | 1評価の時間と並列実行数 |
| ノイズあり | 再評価、ロバストな比較、停止条件 |
| 混合変数 | 離散変数を扱える探索演算子 |

- 関数値だけで動く局所探索
- 集団を使う大域探索
- surrogateで評価点を選ぶ逐次探索

::: warning
「導関数を使わない」は「調整不要」を意味しません。評価予算、初期設計、探索範囲を先に固定します。
:::

## 次に読む

[Nelder–Meadの教材](#/methods/M_NELDER_MEAD)では、単体を変形する一歩を確認できます。
