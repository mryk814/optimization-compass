---
content_id: optimality-criteria-topology
kind: method
method_id: M_OC_TOPOLOGY
title_ja: トポロジー最適化のOptimality Criteria
title_en: Optimality Criteria Update for Topology Optimization
summary: Optimality Criteriaは、密度感度と体積率制約から要素密度を乗法的に更新し、minimum-complianceの設計fieldを効率よく改善する更新則です。
source_ids: [S097, S098]
prerequisites: [simp-topology, density-filter]
related_ids: [mma, adjoint-sensitivity, topology-optimization]
visualization_ids: [topology-optimization-field-evolution]
comparison_ids: [COMPARE_TOPOLOGY_OC_MMA]
aliases: [/learn/optimality-criteria-topology]
status: published
last_reviewed: 2026-07-18
---

Optimality Criteriaは、密度感度と体積率制約から要素密度を乗法的に更新し、minimum-complianceの設計fieldを効率よく改善する更新則です。

## 体積率を守りながら密度を変える

SIMPで状態と感度を計算した後、OCは感度の符号と大きさを使って密度を更新します。
更新倍率にはmove limitと上下限があり、全要素を自由に動かすわけではありません。

体積率制約があるため、更新倍率の係数は通常、更新後の平均密度が目標に近づくように調整します。
この係数を決める部分が、単なるgradient descentとの違いです。

OCの更新は、KKT条件に近づくための実用的な更新則ですが、離散化された問題の大域解を証明するものではありません。
move limit、filter radius、projectionの設定を変えると、同じvolume fractionでも別の局所的なfieldへ到達します。
そのため、更新を速く見せる単一のcompliance値ではなく、停止条件と感度の整合性を含む反復履歴を残します。

```python
lower, upper = bracket_volume_multiplier(filtered_sensitivity, target_volume)
multiplier = bisect_volume_multiplier(lower, upper, density, filtered_sensitivity)
candidate = np.clip(density * update_factor(multiplier, filtered_sensitivity), 0.001, 1.0)
next_density = limit_move(candidate, density, move_limit)
```

## 反復の読み方

一つの反復では、次の順序が崩れていないか確認します。

1. 現在のdensityから状態方程式を解く
2. complianceと感度を計算する
3. filter後の感度からOC更新を作る
4. volume fractionとmove limitを確認する

Theaterではこの順序をfieldと数値の両方で追えます。

## 向く条件・避ける条件

SIMPのminimum-compliance問題のように、密度、感度、体積率の関係が整理されている問題に向きます。
制約が増えたり、複雑な非線形性が強くなったりすると、[MMA](#/learn/mma)のような近似問題の組み立てを比較します。

## 診断値

`volume_fraction`が目標に近いことだけでなく、`compliance`、`gray_fraction`、`checkerboard_score`、`projection_beta`を同じiterationで確認します。

## 失敗・切替の兆候

密度が上下限に張り付いたまま荷重経路が変わらない、complianceだけが下がってcheckerboard scoreが上がる場合は、move limitとfilterを見直します。
更新の振動が強い場合は、固定presetの範囲を変えた比較を別に作り、OCの性能順位とは分けて読みます。

## 次に読む

[同じfieldでOCとMMAを比較する](#/compare/COMPARE_TOPOLOGY_OC_MMA)と、更新則の差をcomplianceだけでなくfield指標で確認できます。
