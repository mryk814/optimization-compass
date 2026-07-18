---
content_id: adjoint-sensitivity
kind: method
method_id: M_ADJOINT_SENSITIVITY
title_ja: adjoint sensitivity
title_en: Adjoint Sensitivity Analysis
summary: adjoint sensitivityは、状態方程式の解を使って、設計変数が目的関数へ与える感度を少ない追加solveで計算する方法です。
source_ids: [S101]
prerequisites: [topology-optimization, concept.constraint-class]
related_ids: [shape-optimization, geometry-update-failure-modes, simp-topology, density-filter, optimality-criteria-topology]
visualization_ids: [topology-optimization-field-evolution]
comparison_ids: []
aliases: [/learn/adjoint-sensitivity]
status: published
last_reviewed: 2026-07-18
---

adjoint sensitivityは、状態方程式の解を使って、設計変数が目的関数へ与える感度を少ない追加solveで計算する方法です。

## 状態を経由する設計感度

状態方程式を

$$
R(u,m)=0
$$

とし、目的関数を $J(u,m)$ とします。
設計変数 $m$ を少し変えたときの $dJ/dm$ を直接求めると、設計変数の数だけ状態の変化を追う必要があります。

adjoint変数 $\lambda$ を導入し、

$$
\left(\frac{\partial R}{\partial u}\right)^T\lambda=\left(\frac{\partial J}{\partial u}\right)^T
$$

を解くと、状態方程式と目的関数の微分を組み合わせて設計感度を計算できます。

トポロジー最適化では、密度fieldの要素数が増えても、感度計算を設計変数数に比例する回数だけ繰り返さずに済む構造が重要です。

## 何を確認するか

adjoint sensitivityは、単独の更新則ではありません。
状態solveが収束していること、残差とJacobianが正しく定義されていること、感度の符号が有限差分と整合することが前提です。

- state residual
- adjoint residual
- raw sensitivityとfilter後の感度
- finite-differenceまたはgradient check

## 向く条件・避ける条件

状態方程式があり、設計変数が多く、目的関数の数が少ない問題に向きます。
接触や離散的な材料切替のように微分が不連続な場合は、滑らかな近似とその限界を明示します。

## 失敗・切替の兆候

gradient checkが合わない、state residualが大きい、meshを変えると感度の分布だけが大きく変わる場合は、更新則より先に状態方程式、境界条件、微分実装を点検します。
complianceの値がもっともらしくても、感度が誤っていればfield更新は誤った方向へ進みます。

形状変数を扱う場合は、感度の検査対象が密度fieldから境界やgeometry parameterへ移ります。
geometry update、mesh quality、state solveを同じ反復の記録に残し、無効なmeshを通った感度を物理的な勾配として扱わないようにします。

## 最小コードで見る計算順序

実装では、state solve、adjoint solve、設計感度の組み立てを分けて記録します。
次の擬似コードは、更新則や境界条件を省いた感度計算の骨格です。

```python
state = solve_state(design)
adjoint = solve_transpose_jacobian(state, objective)
sensitivity = direct_derivative(state, design) - adjoint @ residual_derivative(state, design)
```

## トポロジー最適化での読み方

SIMPでは、まず密度fieldから剛性を作り、state solveで変位を得ます。
その後、adjoint sensitivityを使って各要素の密度を増減したときのcomplianceの変化を計算します。
この順番を分けて記録すると、更新が止まった原因が「状態方程式の収束」なのか「感度の符号」なのかを切り分けられます。

教育用traceでは、raw sensitivityとfilter後の感度を同じ反復番号で並べます。
これは実装のwall-clock性能を順位付けするためではなく、どの情報が次のdensity updateを決めるかを観察するためです。

## 次に読む

[形状最適化の設計変数](#/learn/shape-optimization)でparameterizationの意味を確認し、[SIMP密度法](#/learn/simp-topology)で感度を使う更新を確認します。[density filter](#/learn/density-filter)は離散fieldの正則化、[形状更新の失敗モード](#/learn/geometry-update-failure-modes)はmeshとstateの切り分けを扱います。
