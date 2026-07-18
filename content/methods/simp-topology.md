---
content_id: simp-topology
kind: method
method_id: M_SIMP_TOPOLOGY
title_ja: SIMP密度法
title_en: SIMP Topology Optimization
summary: SIMP密度法は、要素密度を連続変数にして剛性を密度のべき乗で補間し、体積率制約のもとでcomplianceを下げるトポロジー最適化手法です。
source_ids: [S097, S098]
prerequisites: [topology-optimization, concept.constraint-class]
related_ids: [density-filter, optimality-criteria-topology, mma]
visualization_ids: [topology-optimization-field-evolution]
comparison_ids: [COMPARE_TOPOLOGY_OC_MMA]
aliases: [/learn/simp-topology]
status: published
last_reviewed: 2026-07-18
---

SIMP密度法は、要素密度を連続変数にして剛性を密度のべき乗で補間し、体積率制約のもとでcomplianceを下げるトポロジー最適化手法です。

## 密度を剛性へ写像する

要素 $e$ の密度を $\rho_e$ とし、ヤング率を次で補間します。

$$
E_e(\rho_e)=E_{\min}+\rho_e^p(E_0-E_{\min}).
$$

$p>1$ にすると中間密度の剛性が相対的に不利になります。
その結果、密度fieldは材料と空孔に分かれやすくなりますが、これはpenalizationを含む連続緩和です。

## 更新で見るもの

状態方程式 $K(\rho)u=F$ を解き、complianceと密度感度を計算します。
感度から密度を更新したら、次の反復で再び状態を解きます。

- 体積率が目標に近いか
- gray fractionが減っているか
- filter後の感度を使っているか
- meshを変えたとき設計が大きく変わらないか

complianceの単調な改善だけでは終了判定に足りません。

SIMPで見えている密度は、完成した部材形状そのものではありません。
連続な設計変数を使いやすくするためのrelaxationであり、penalization、filter、projection、meshの選択によって最終fieldの読み方が変わります。
特に中間密度が残る場合は、単にpを大きくするのではなく、state residual、感度のgradient check、volume制約、mesh refinementを分けて確認します。

```python
stiffness = emin + density**penalty * (e0 - emin)
state = solve_linear_system(assemble_stiffness(stiffness), load)
compliance = load @ state
```

## 向く条件・避ける条件

要素密度を設計変数として扱え、体積率と状態方程式を定義できる問題に向きます。
接触、座屈、製造制約、非線形材料を追加すると、同じ更新式だけでは設計の意味を保てない場合があります。

## 診断値

`volume_fraction`、`compliance`、`gray_fraction`、`checkerboard_score`を反復ごとに保存します。
filter radius、penalization、projection beta、move limitも、結果と一緒に記録します。

## 失敗・切替の兆候

checkerboard scoreが下がらない、gray fractionが残り続ける、mesh変更で荷重経路が変わる場合は、[density filter](#/learn/density-filter)やprojectionの設定を見直します。
更新の制約処理が複雑なら、[MMA](#/learn/mma)との比較が有効です。

## 次に読む

[Optimality Criteria](#/learn/optimality-criteria-topology)は体積制約を含む更新則、[adjoint sensitivity](#/learn/adjoint-sensitivity)は状態方程式から感度を得る仕組みを説明します。
