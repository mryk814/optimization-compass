---
content_id: density-filter
kind: method
method_id: M_DENSITY_FILTER
title_ja: density filter
title_en: Density Filter
summary: density filterは、要素近傍の密度や感度を重み付き平均し、checkerboardとmesh依存性を抑えるトポロジー最適化の正則化手法です。
source_ids: [S099]
prerequisites: [topology-optimization, simp-topology]
related_ids: [shape-optimization, geometry-update-failure-modes, optimality-criteria-topology, adjoint-sensitivity]
visualization_ids: [topology-optimization-field-evolution]
comparison_ids: [COMPARE_TOPOLOGY_OC_MMA]
aliases: [/learn/density-filter]
status: published
last_reviewed: 2026-07-18
---

density filterは、要素近傍の密度や感度を重み付き平均し、checkerboardとmesh依存性を抑えるトポロジー最適化の正則化手法です。

## 隣接要素を独立に更新しない

有限要素ごとの感度をそのまま使うと、隣接要素が細かく交互に変化する場合があります。
density filterは近傍半径と距離重みを使い、各要素の更新を周囲のfieldと結びます。

典型的な平均は、

$$
\tilde{\rho}_e=\frac{\sum_i w_{ei}\rho_i}{\sum_i w_{ei}},
\qquad w_{ei}=\max(0,r_{\min}-\operatorname{dist}(e,i))
$$

の形です。
実際に密度をfilterするか、感度をfilterするかで、制約の扱いと実装の意味は変わります。

近傍平均は、単に画像をぼかす処理ではありません。
設計変数を更新する前に、どの要素がどの要素へ影響を渡すかを定義するため、境界付近の重み、filter半径、体積制約を同時に確認する必要があります。
半径を大きくすれば細かい模様は消えやすくなりますが、細い部材や局所的な応力経路も消える可能性があります。
したがって、checkerboard scoreだけを下げることを成功条件にせず、compliance、gray fraction、mesh refinement後の挙動を並べて読みます。

mesh nodeを直接動かす形状更新とは、artifactの抑え方が違います。
density filterはfieldの近傍を平滑化しますが、要素のinversionや自己交差したgeometryを修復する検査ではありません。

```python
weights = build_neighbor_weights(mesh, radius)
filtered_density = weighted_average(density, weights)
filtered_sensitivity = weighted_average(raw_sensitivity, weights)
```

## 何を直しているか

filterはcomplianceを直接最小化する手法ではありません。
近傍を混ぜることで、meshの一要素だけに依存する更新を抑え、設計fieldに最小長さのような性質を持たせます。

- `filter radius`：どの範囲を混ぜるか
- `checkerboard score`：交互模様が残っていないか
- `gray fraction`：中間密度がどれだけ残るか
- `volume fraction`：平滑化後も制約を守っているか

## 向く条件・避ける条件

要素近傍に意味があり、mesh上の短いartifactを抑えたい問題に向きます。
物理的な最小部材寸法や製造制約をfilter radiusだけで表せるとは限りません。

## 失敗・切替の兆候

filter radiusを変えると結果が大きく変わる場合、mesh、projection、penalizationの影響を分けて確認します。
filterを入れれば製造可能になるわけではないため、後段で実際の製造制約を評価します。

目的値が改善しても、mesh refinementで荷重経路や境界が変わるならmesh dependenceが残っています。
[形状更新の失敗モード](#/learn/geometry-update-failure-modes)でgeometry validityとmesh qualityを先に確認してください。

## 次に読む

[SIMP密度法](#/learn/simp-topology)で密度と剛性の関係を確認し、[Optimality Criteria](#/learn/optimality-criteria-topology)でfilter後の感度を更新へ使う流れを追います。
