---
content_id: simp-topology
kind: method
method_id: M_SIMP_TOPOLOGY
title_ja: SIMP密度法
title_en: SIMP Topology Optimization
summary: SIMP密度法は、要素密度を連続変数にして剛性を密度のべき乗で補間し、体積率制約のもとでcomplianceを下げるトポロジー最適化手法です。
source_ids: [S097, S098]
prerequisites: [topology-optimization, concept.constraint-class]
related_ids: [shape-optimization, geometry-update-failure-modes, density-filter, optimality-criteria-topology, mma]
visualization_ids: [topology-optimization-field-evolution, shape-topology-representation-contrast]
comparison_ids: [COMPARE_TOPOLOGY_OC_MMA, COMPARE_SHAPE_TOPOLOGY_REPRESENTATION]
aliases: [/learn/simp-topology]
status: published
last_reviewed: 2026-07-24
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
密度fieldは、連続な設計変数を使うためのrelaxationです。
penalizationとfilterの選択によって最終fieldの読み方が変わります。
projectionとmeshも別に記録します。

中間密度が残る場合も、単にpを大きくしません。
state residualと感度のgradient checkを分けて確認します。
volume制約とmesh refinementも同時に監査します。

境界を直接更新する形状最適化とは、設計変数と失敗モードが異なります。
SIMPのcheckerboardやgray densityを、geometry updateの成功と読み替えないでください。

## 表現と更新則を別に比べる

| 比較軸 | 固定するもの | 変えるもの | 入口 |
|---|---|---|---|
| 設計表現 | 同じ物理条件と外側envelope | 3つのshape parameter／density field | [shape／topology Compare](#/compare/COMPARE_SHAPE_TOPOLOGY_REPRESENTATION) |
| 更新則 | 同じdensity fieldと評価条件 | OC／MMA | [OC／MMA Compare](#/compare/COMPARE_TOPOLOGY_OC_MMA) |

[representation contrastのTheater](#/theater/learning/SCENARIO_SHAPE_TOPOLOGY_REPRESENTATION_CONTRAST)では、parameterとgeometryを分けます。
meshと物理状態（physical state）も同じevaluation軸で対応付けます。
これはSIMPやSLSQPの実solver結果ではなく、topology変更を許す表現の違いを読む固定教材です。
wall-clock・解品質・一般性能のrankingには使いません。

```python
stiffness = emin + density**penalty * (e0 - emin)
state = solve_linear_system(assemble_stiffness(stiffness), load)
compliance = load @ state
```

## 向く条件・避ける条件

要素密度を設計変数として扱え、体積率と状態方程式を定義できる問題に向きます。
接触や座屈を追加すると、同じ更新式だけでは設計の意味を保てない場合があります。
製造制約と非線形材料も別にmodel化します。

## 診断値

`volume_fraction`と`compliance`を反復ごとに保存します。
`gray_fraction`と`checkerboard_score`も対応付けます。
filter radiusとpenalizationを結果と一緒に記録します。
projection betaとmove limitも必要です。

## 失敗・切替の兆候

checkerboard scoreが下がらない場合は、[density filter](#/learn/density-filter)やprojectionを見直します。
gray fractionが残り続ける場合も同様です。
mesh変更で荷重経路が変わる場合は、mesh依存性を先に調べます。
形状parameterを更新している場合は、[形状更新の失敗モード](#/learn/geometry-update-failure-modes)へ進みます。
inversion・mesh quality・state residualを分けて確認します。
更新の制約処理が複雑なら、[MMA](#/learn/mma)との比較が有効です。

## 次に読む

[Optimality Criteria](#/learn/optimality-criteria-topology)は体積制約を含む更新則、[adjoint sensitivity](#/learn/adjoint-sensitivity)は状態方程式から感度を得る仕組みを説明します。
