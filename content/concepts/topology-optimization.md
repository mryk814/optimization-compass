---
content_id: topology-optimization
kind: concept
canonical_entity_type: problem
canonical_entity_id: PROBLEM_TOPOLOGY_OPTIMIZATION
title_ja: トポロジー最適化
title_en: Topology Optimization
summary: トポロジー最適化は、設計領域内の材料分布を変数にして、状態方程式と体積制約のもとで剛性やcomplianceを改善する設計問題です。
source_ids: [S097, S098, S101]
prerequisites: [concept.variable-domain, concept.constraint-class]
related_ids: [simp-topology, density-filter, optimality-criteria-topology, adjoint-sensitivity]
visualization_ids: [topology-optimization-field-evolution]
comparison_ids: [COMPARE_TOPOLOGY_OC_MMA]
aliases: [/learn/topology-optimization]
status: published
last_reviewed: 2026-07-18
---

トポロジー最適化は、設計領域内の材料分布を変数にして、状態方程式と体積制約のもとで剛性やcomplianceを改善する設計問題です。

## 形状ではなく材料分布を決める

有限要素ごとの密度 $\rho_e$ を設計変数にすると、材料を置く場所と空ける場所を同時に探索できます。
線形弾性の最小compliance問題は、典型的には次の形です。

$$
\min_{\rho} c(\rho)=F^Tu
\quad\text{subject to}\quad K(\rho)u=F,\quad \operatorname{mean}(\rho)\le v^*,\quad \rho_{\min}\le\rho_e\le1.
$$

状態 $u$ は密度から決まり、密度は状態を通じてcomplianceに影響します。
したがって、普通の連続変数の目的関数に見えても、実際には「設計fieldを更新する問題」です。

## 反復ごとに対応づける量

- **設計field**：現在の材料分布です。
- **状態field**：その設計で解いた変位やひずみエネルギーです。
- **感度**：密度を変えたときcomplianceがどう変わるかを表します。
- **制約指標**：volume fraction、gray fraction、checkerboard scoreです。

complianceが下がっても、checkerboardやgray densityが消えたとは限りません。
離散化の解像度やfilter radiusを変えると、別の局所解へ移る場合もあります。

## 何を保証しないか

密度法の解は連続体の形状そのものではありません。
SIMPのpenalizationは中間密度を抑えますが、0と1だけの設計を無条件に返すわけではありません。
また、教育用の小さなmeshで得た形状を、実構造の強度、座屈、製造性へそのまま読み替えることもできません。

## Theaterで確認する

[片持ちはりのfield evolution](#/theater/learning/SCENARIO_TOPOLOGY_SIMP_OC)では、density、state、sensitivityを同じ反復番号で見比べます。
[checkerboard failure](#/theater/learning/SCENARIO_TOPOLOGY_CHECKERBOARD)を開くと、complianceだけを追う読み方が破綻する箇所を確認できます。

## 次に読む

[SIMP](#/learn/simp-topology)は材料補間とpenalization、[density filter](#/learn/density-filter)は離散化artifactの抑制、[adjoint sensitivity](#/learn/adjoint-sensitivity)は状態方程式を介した感度計算を扱います。
