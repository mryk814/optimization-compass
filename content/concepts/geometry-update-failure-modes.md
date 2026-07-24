---
content_id: geometry-update-failure-modes
kind: concept
canonical_entity_type: feature
canonical_entity_id: F_STRUCTURE_PDE_CONSTRAINED
title_ja: 形状更新の失敗モード
title_en: Geometry-Update Failure Modes
summary: 形状更新の失敗は、目的関数の悪化とは分け、geometry・mesh・state solveのどこで壊れたかを診断します。
source_ids: [S054, S055, S056, S101, S104, S106]
prerequisites: [shape-optimization, concept.constraint-class]
related_ids: [shape-optimization, topology-optimization, adjoint-sensitivity, density-filter]
visualization_ids: [shape-diffuser-valid-update, shape-diffuser-invalid-geometry]
comparison_ids: [COMPARE_SHAPE_TOPOLOGY_REPRESENTATION]
aliases: [/learn/geometry-update-failure-modes]
status: published
last_reviewed: 2026-07-24
---

形状更新の失敗は、目的関数の悪化とは分け、geometry・mesh・state solveのどこで壊れたかを診断します。

## 直感: 失敗は4層で起きる

形状最適化の一反復には、geometry・mesh・physics・optimizationの層があります。
どこで壊れたかを分けなければ、更新幅だけを小さくして原因を残します。

[成立する更新](#/theater/learning/SCENARIO_SHAPE_DIFFUSER_VALID_UPDATE)と[無効なgeometry](#/theater/learning/SCENARIO_SHAPE_DIFFUSER_INVALID_GEOMETRY)を先に見比べると、目的proxyだけでは受理できない理由を追えます。

| 層 | 観測する失敗 | 典型的な確認 |
| --- | --- | --- |
| geometry | 自己交差、重複境界、許容範囲外 | 境界の距離、交差、形状parameter |
| mesh | 要素のつぶれ、反転、負のJacobian | 最小quality、aspect ratio、要素orientation |
| physics | state solveの発散、残差の増大 | state residual、線形solveのstatus |
| optimization | 感度の不整合、更新の振動 | gradient check、update norm、constraint violation |

評価が失敗したときは、最初にこの層を記録します。
geometryが無効なら、物理solveを「悪い目的値」として学習させません。
別の失敗状態として扱います。

## mesh qualityとinversionを確認する

mesh nodeを動かす更新では、隣接要素の体積やJacobianが変わります。
要素が極端につぶれると、物理solveのconditionが悪化します。
orientationが反転すれば、意図した要素として扱えない場合があります。

更新候補を受け入れる前に、次を確認します。

- geometryが自己交差していない
- 要素の最小qualityが許容範囲にある
- inversionや負のJacobianがない
- 境界条件と材料領域の対応が保たれている

この検査を通過しても、PDEの解が正しいとは限りません。
qualityの閾値は、要素型・物理model・実装に依存します。
一つの数値を普遍的な安全基準として扱いません。

## checkerboardとmesh dependenceを分ける

境界を直接更新しない密度fieldでは、checkerboardのような離散artifactが現れる場合があります。
complianceが改善していても、交互配置がmeshの局所構造に依存しているかもしれません。
形状として解釈する前に、filterと解像度を確認します。

meshを細かくしたときは、目的値だけでなく荷重経路と境界も比べます。
gray fractionやcheckerboard scoreが変わるなら、mesh dependenceが残っています。
[density filter](#/learn/density-filter)はartifactを抑える手段の一つです。
物理的な最小部材寸法や製造性を単独では保証しません。

[shapeとtopologyのCompare](#/compare/COMPARE_SHAPE_TOPOLOGY_REPRESENTATION)では、設計表現を変えたときに何を同一条件として読めないかを確認できます。

## 切り分けの順序

1. geometry validityを確認し、無効な候補を物理評価から除外する。
2. mesh qualityとinversionを確認し、必要なら更新幅やmesh-motionを見直す。
3. state residualと制約違反を確認し、物理solveの失敗を分ける。
4. gradient checkとmesh refinementで、感度と離散化の影響を確認する。
5. それでも改善しなければ、parameterizationが必要な形状を表現できているかを見直す。

この順序は、評価できた候補だけで目的値を比較するためのものです。
失敗候補を大きな罰則値に置き換える場合もあります。
その場合も、元の失敗理由を別のledgerに残します。

::: warning
mesh qualityや離散問題の目的値だけから、連続体の可行性を結論づけないでください。
物理的な妥当性やglobal optimumも保証されません。
mesh・state・geometryの検証を同じ更新履歴に残します。
:::

## 次に読む

[形状最適化の設計変数](#/learn/shape-optimization)で表現と更新経路を確認します。
[adjoint sensitivity](#/learn/adjoint-sensitivity)では、gradient checkとstate residualを読みます。
[トポロジー最適化](#/learn/topology-optimization)では、density fieldとshapeを混同しない見方を扱います。
