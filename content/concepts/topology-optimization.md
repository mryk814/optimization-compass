---
content_id: topology-optimization
kind: concept
canonical_entity_type: problem
canonical_entity_id: PROBLEM_TOPOLOGY_OPTIMIZATION
title_ja: トポロジー最適化
title_en: Topology Optimization
summary: トポロジー最適化は、設計領域内の材料分布を変数にして、状態方程式と体積制約のもとで剛性やコンプライアンスを改善する設計問題です。
source_ids: [S097, S098, S101]
prerequisites: [concept.variable-domain, concept.constraint-class]
related_ids: [shape-optimization, geometry-update-failure-modes, simp-topology, density-filter, optimality-criteria-topology, adjoint-sensitivity]
visualization_ids: [topology-optimization-field-evolution]
comparison_ids: [COMPARE_TOPOLOGY_OC_MMA]
aliases: [/learn/topology-optimization]
status: published
last_reviewed: 2026-10-02
---

トポロジー最適化は、設計領域内の材料分布を変数にして、状態方程式と体積制約のもとで剛性やコンプライアンスを改善する設計問題です。

## 形状ではなく材料分布を決める

有限要素ごとの密度 $\rho_e$ を設計変数にすると、材料を置く場所と空ける場所を同時に探索できます。
線形弾性の最小コンプライアンス問題は、典型的には次の形です。

$$
\min_{\rho} c(\rho)=F^Tu
\quad\text{subject to}\quad K(\rho)u=F,\quad \operatorname{mean}(\rho)\le v^*,\quad \rho_{\min}\le\rho_e\le1.
$$

状態 $u$ は密度から決まり、密度は状態を通じてコンプライアンスに影響します。
したがって、普通の連続変数の目的関数に見えても、実際には「設計場を更新する問題」です。

## 実行結果を先に見る

[荷重を支える材料配置の計算例](#/theater/physical/topology)では、左端を固定した領域に荷重をかけ、同じ材料量のまま配置を更新します。
表示を最初に戻し、固定面と荷重の間に残る材料を追ってください。
この例は3D線形弾性の有限要素法で計算しています。表示する密度の下限や変形倍率を変えても、元の密度場で求めた目的値と体積率は変わりません。

![8×4要素の固定教材を12反復実行した密度場。初期場、フィルタありの反復6と反復12、フィルタなしの反復12を並べ、コンプライアンス、中間密度の割合、チェッカーボード指標を同じ反復から表示している。](./media/topology-field-execution.svg "Optimization CompassのPythonで書かれた教材用生成プログラムを実行した結果です。フィルタありでは滑らかな材料経路が現れ、フィルタなしではチェッカーボードが強く残ります。実FEMの妥当性や製造性は示しません。")

濃淡の形だけでなく、各図の中間密度の割合とチェッカーボードも一緒に見ます。コンプライアンスが下がったという一つの数値だけでは、場の妥当性を判断できません。

## 形状最適化との違い

形状最適化は境界や形状パラメータを更新しますが、SIMPのような密度法は要素ごとの密度場を更新します。
密度場から境界を取り出す後処理を加えても、元の連続境界を直接最適化したことにはなりません。
表現が違えば、更新できる設計と現れるメッシュ依存性も変わります。

## 反復ごとに対応づける量

- **設計場**：現在の材料分布です。
- **状態場**：その設計で解いた変位やひずみエネルギーです。
- **感度**：密度を変えたときコンプライアンスがどう変わるかを表します。
- **制約指標**：体積率、中間密度の割合、チェッカーボード指標です。

コンプライアンスが下がっても、チェッカーボードや中間密度が消えたとは限りません。
離散化の解像度やフィルタ半径を変えると、別の局所解へ移る場合もあります。

## 何を保証しないか

密度法の解は連続体の形状そのものではありません。
SIMPの罰則化は中間密度を抑えますが、0と1だけの設計を無条件に返すわけではありません。
また、教育用の小さなメッシュで得た形状を、実構造の強度、座屈、製造性へそのまま読み替えることもできません。
形状更新を含む場合は、形状の妥当性、メッシュ品質、状態残差を別々に確認します。

## 可視化で確認する

[片持ちはりの場の変化](#/theater/learning/SCENARIO_TOPOLOGY_SIMP_OC)では、密度、状態、感度を同じ反復番号で見比べます。
[チェッカーボードの失敗例](#/theater/learning/SCENARIO_TOPOLOGY_CHECKERBOARD)を開くと、コンプライアンスだけを追う読み方が破綻する箇所を確認できます。

[形状更新の失敗モード](#/learn/geometry-update-failure-modes)では、要素反転や負のヤコビアン、チェッカーボード、メッシュ依存性を同じ目的値にまとめない診断順を確認できます。

## 次に読む

[SIMP](#/learn/simp-topology)は材料補間と罰則化、[密度フィルタ](#/learn/density-filter)は離散化による人工的な構造の抑制、[随伴感度](#/learn/adjoint-sensitivity)は状態方程式を介した感度計算を扱います。
