---
content_id: geometry-update-failure-modes
kind: concept
canonical_entity_type: feature
canonical_entity_id: F_STRUCTURE_PDE_CONSTRAINED
title_ja: 形状更新の失敗モード
title_en: Geometry-Update Failure Modes
summary: 形状更新の失敗は、目的関数の悪化だけでなく、無効なgeometry、mesh qualityの低下、state solveの不整合として切り分けます。
source_ids: [S054, S055, S056, S101, S104, S106]
prerequisites: [shape-optimization, concept.constraint-class]
related_ids: [shape-optimization, topology-optimization, adjoint-sensitivity, density-filter]
visualization_ids: [shape-diffuser-valid-update, shape-diffuser-invalid-geometry]
comparison_ids: [COMPARE_SHAPE_TOPOLOGY_REPRESENTATION]
aliases: [/learn/geometry-update-failure-modes]
status: published
last_reviewed: 2026-07-19
---

形状更新の失敗は、目的関数の悪化だけでなく、無効なgeometry、mesh qualityの低下、state solveの不整合として切り分けます。

## まず失敗の層を分ける

形状最適化の一反復には、geometry、mesh、physics、optimizationの層があります。どこで壊れたかを分けないと、更新幅だけを小さくして原因を残します。

| 層 | 観測する失敗 | 典型的な確認 |
| --- | --- | --- |
| geometry | 自己交差、重複境界、許容範囲外 | 境界の距離、交差、形状parameter |
| mesh | 要素のつぶれ、反転、負のJacobian | 最小quality、aspect ratio、要素orientation |
| physics | state solveの発散、残差の増大 | state residual、線形solveのstatus |
| optimization | 感度の不整合、更新の振動 | gradient check、update norm、constraint violation |

評価が失敗したときは、最初にこの層を記録します。geometryが無効なら物理solveを「悪い目的値」として学習させず、別の失敗状態として扱います。

## mesh qualityとinversion

mesh nodeを動かす更新では、隣接要素の体積やJacobianが変わります。要素が極端につぶれると物理solveのconditionが悪化し、orientationが反転すると、そもそも意図した要素として扱えない場合があります。

更新候補を受け入れる前に、次を確認します。

- geometryが自己交差していない
- 要素の最小qualityが許容範囲にある
- inversionや負のJacobianがない
- 境界条件と材料領域の対応が保たれている

この検査を通過しても、PDEの解が正しいとは限りません。qualityの閾値は要素型、物理モデル、実装に依存するため、数値を普遍的な安全基準として扱いません。

## checkerboardとmesh dependence

境界を直接更新しない密度fieldでは、checkerboardのような離散artifactが現れる場合があります。complianceが改善していても、交互配置がmeshの局所構造に依存していれば、形状として解釈する前にfilterや解像度を確認します。

meshを細かくしたときに目的値だけでなく、荷重経路、境界、gray fraction、checkerboard scoreが変わるなら、mesh dependenceが残っています。[density filter](#/learn/density-filter)はartifactを抑える手段の一つですが、物理的な最小部材寸法や製造性を単独で保証しません。

## 切り分けの順序

1. geometry validityを確認し、無効な候補を物理評価から除外する。
2. mesh qualityとinversionを確認し、必要なら更新幅やmesh-motionを見直す。
3. state residualと制約違反を確認し、物理solveの失敗を分ける。
4. gradient checkとmesh refinementで、感度と離散化の影響を確認する。
5. それでも改善しなければ、parameterizationが必要な形状を表現できているかを見直す。

この順序は、評価ができた候補だけで目的値を比較するためのものです。失敗候補を大きな罰則値に置き換える場合も、元の失敗理由を別のledgerに残します。

[2D diffuser failure Theater](#/theater/learning/SCENARIO_SHAPE_DIFFUSER_INVALID_GEOMETRY)では、目的proxyが改善しても自己交差と反転cellで候補を棄却する経路を確認できます。

::: warning
mesh qualityが高いこと、または離散問題の目的値が改善したことだけから、連続体の可行性、物理的な妥当性、global optimumを結論づけないでください。mesh、state、geometryの検証を同じ更新履歴に残します。
:::

## 次に読む

[形状最適化の設計変数](#/learn/shape-optimization)で表現と更新経路を確認し、[adjoint sensitivity](#/learn/adjoint-sensitivity)でgradient checkとstate residualを読みます。[トポロジー最適化](#/learn/topology-optimization)では、density fieldとshapeを混同しない見方を扱います。
