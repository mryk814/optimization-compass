---
content_id: shape-optimization
kind: concept
canonical_entity_type: feature
canonical_entity_id: F_VARIABLE_DOMAIN
title_ja: 形状最適化の設計変数
title_en: Shape Optimization Design Variables
summary: 形状最適化では、境界や形状を表す設計変数を更新し、物理状態を再計算して性能と幾何の妥当性を同時に確認します。
source_ids: [S054, S055, S056, S101, S104, S105, S106]
prerequisites: [concept.variable-domain, topology-optimization]
related_ids: [geometry-update-failure-modes, topology-optimization, adjoint-sensitivity, density-filter]
visualization_ids: [shape-diffuser-valid-update, shape-diffuser-invalid-geometry, shape-topology-representation-contrast]
comparison_ids: [COMPARE_SHAPE_TOPOLOGY_REPRESENTATION]
aliases: [/learn/shape-optimization]
status: published
last_reviewed: 2026-07-19
---

形状最適化では、境界や形状を表す設計変数を更新し、物理状態を再計算して性能と幾何の妥当性を同時に確認します。

## 形状変数は「何を動かすか」を表す

形状最適化で更新するのは、単なる数値列ではありません。境界の位置、断面寸法、節点の移動量、または形状を表す係数が設計変数になります。
同じ設計領域でも、どの表現を選ぶかで更新できる形状と失敗の仕方が変わります。

| 設計変数の表現 | 更新する対象 | 最初に確認すること |
| --- | --- | --- |
| 境界のparameter | 境界上の寸法や節点 | boundsと滑らかさ、固定境界 |
| 形状basisの係数 | splineや低次元の形状 | 表現できる形状の範囲 |
| mesh nodeの移動量 | 離散化meshの座標 | 要素品質、境界の交差 |
| 密度field | 要素ごとの材料分布 | 形状との変換、filter、gray density |

最後の密度fieldは、境界を直接動かす形状変数とは異なります。[トポロジー最適化](#/learn/topology-optimization)は材料分布を設計する問題として始まり、SIMPではその分布を連続fieldで表します。したがって、密度fieldの改善をそのまま滑らかな形状の改善とは読みません。

## 一回の更新で通る経路

形状変数を $q$、形状とmeshから作る物理モデルを $R(u,q)=0$、目的関数を $J(u,q)$ とします。
一回の更新は、概ね次の順に進みます。

1. $q$から境界とmeshを作り、幾何の妥当性を確認する。
2. 妥当なmeshでstate $u$を解く。
3. 目的、制約、感度を記録する。
4. 更新候補を受け入れる前に、geometryとmesh qualityを再確認する。

目的関数だけを返すblack-box評価にすると、幾何の失敗と物理状態の失敗が同じ「評価失敗」に隠れます。診断では、geometry update、mesh quality、state residual、目的、制約違反を別の値として保存します。

## 形状の表現が保証する範囲

低次元の形状parameterは、更新を安定させやすい一方で、表現できる形状を狭めます。自由度を増やすと表現力は広がりますが、meshの変形や感度のnoiseが増える場合があります。

形状変数のboundsを守っても、自己交差しないこと、要素が反転しないこと、物理制約を満たすことまでは保証しません。geometry validityを独立した制約または事前チェックとして扱います。

::: warning
離散mesh上で目的関数が改善しても、連続体の形状が改善したことや、細かいmeshでも同じ設計になることは示されません。mesh refinement、geometry validity、物理制約を分けて再評価してください。
:::

## 診断値

- geometry updateの最大変位と境界の最小距離
- 要素の最小qualityと、反転要素・負のJacobianの数
- state residualと制約違反
- 目的関数、感度、finite-differenceまたはgradient check
- mesh refinement後の目的・制約・形状の変化

目的だけが改善し、mesh qualityやconstraint violationが悪化するなら、その更新は採用せず、更新幅、parameterization、mesh-motion、または再meshの方針を見直します。

## applicationへ広げるときのmap

[2D diffuser Case](#/gallery/shape-diffuser)は、parameter、geometry、mesh、physical stateを分ける最小contractです。physical stateを置き換えるときも、この順序は維持します。

| domain | physical stateと目的 | 追加で確認する制約 |
| --- | --- | --- |
| structural | displacement／stress、compliance | stress、buckling、支持・荷重境界 |
| CFD | velocity／pressure、loss | 境界層、流量、乱流model |
| thermal | temperature／heat flux、熱抵抗 | 温度上限、熱源、接触熱抵抗 |
| acoustic | pressure wave、散乱・透過 | 周波数帯、放射境界、共振 |
| photonic | Maxwell state、透過・反射 | 波長帯、材料分散、fabrication rule |

いずれも離散stateの目的改善だけでは、連続modelや別meshでの性能を保証しません。geometry validity、mesh refinement、state residual、物理制約を同じlayer contractで再評価します。

[shape／topology表現Compare](#/compare/COMPARE_SHAPE_TOPOLOGY_REPRESENTATION)では、同じ物理briefの下でfixed-topology parameterと接続変更を許すfieldをcontrast-onlyで確認できます。

## 次に読む

[形状更新の失敗モード](#/learn/geometry-update-failure-modes)でgeometry validityとmesh qualityの切り分けを確認し、[adjoint sensitivity](#/learn/adjoint-sensitivity)で状態方程式を介した感度を読みます。密度fieldのartifactは[density filter](#/learn/density-filter)が扱います。
