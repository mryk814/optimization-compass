---
content_id: adjoint-sensitivity
kind: method
method_id: M_ADJOINT_SENSITIVITY
title_ja: 随伴感度
title_en: Adjoint Sensitivity Analysis
summary: 随伴感度は、状態方程式の解を使って、設計変数が目的関数へ与える感度を少ない追加求解で計算する方法です。
source_ids: [S101]
prerequisites: [topology-optimization, concept.constraint-class]
related_ids: [shape-optimization, geometry-update-failure-modes, simp-topology, density-filter, optimality-criteria-topology]
visualization_ids: [topology-optimization-field-evolution, pde-state-tolerance-tight, pde-state-solve-failure]
comparison_ids: [COMPARE_PDE_STATE_TOLERANCE_COST]
aliases: [/learn/adjoint-sensitivity]
status: published
last_reviewed: 2026-09-30
---

随伴感度は、状態方程式の解を使って、設計変数が目的関数へ与える感度を少ない追加求解で計算する方法です。

## 30秒でつかむ

水道のバルブを少し変えたとき、下流の水量がどちらへ変わるかを調べる感覚です。
多数の設計変数が状態を通じて目的へ影響するとき、その感度をまとめて計算します。

- **見るもの**：状態方程式の残差、随伴の残差、設計感度
- **動かすもの**：感度を計算するための随伴変数
- **前進の判断**：残差が小さく、有限差分と感度が整合すること

## 一手の意味

状態と随伴を解いた後、設計変数の直接の影響から、状態を経由する影響を引きます。

$$
\frac{dJ}{dm}
=
\frac{\partial J}{\partial m}
-\lambda^\top\frac{\partial R}{\partial m}.
$$

状態方程式を

$$
R(u,m)=0
$$

とし、目的関数を $J(u,m)$ とします。
設計変数 $m$ を少し変えたときの $dJ/dm$ を直接求めると、設計変数の数だけ状態の変化を追う必要があります。

随伴変数 $\lambda$ を導入し、

$$
\left(\frac{\partial R}{\partial u}\right)^T\lambda=\left(\frac{\partial J}{\partial u}\right)^T
$$

を解くと、状態方程式と目的関数の微分を組み合わせて設計感度を計算できます。

トポロジー最適化では、密度場の要素数が増えても、感度計算を設計変数数に比例する回数だけ繰り返さずに済む構造が重要です。

## 小さな例

設計変数 $m$ が、状態 $u$ を式 $mu=1$ で決める小さな問題です。
目的は $J=\tfrac12(u-1)^2$ とします。
随伴方程式は $m\lambda=u-1$、設計感度は $dJ/dm=-\lambda u$ です。
感度を確かめた後、幅0.5の勾配更新で $m$ を変えます。

| 更新回数 | $m$ | 状態 $u$ | 随伴 $\lambda$ | 感度 | 目的値 |
|---|---:|---:|---:|---:|---:|
| 0 | 2.0000 | 0.5000 | -0.2500 | 0.1250 | 0.1250 |
| 1 | 1.9375 | 0.5161 | -0.2497 | 0.1289 | 0.1171 |
| 2 | 1.8731 | 0.5339 | -0.2489 | 0.1329 | 0.1086 |

正の感度なので、目的を下げる更新は $m$ を減らす向きです。
状態が1へ近づき、目的値が下がっています。
刻み幅 $10^{-5}$ の中心差分も、3行とも感度と小数第10位まで一致しました。
この例の更新則は感度の利用例であり、随伴法そのものが更新幅を決めるわけではありません。

## 向く条件・避ける条件

状態方程式があり、設計変数が多く、目的関数の数が少ない問題に向きます。
接触や離散的な材料切替のように微分が不連続な場合は、滑らかな近似とその限界を明示します。

## Python

小さな例では、状態と随伴の求解を別々に実行します。
その後、感度を確認できます。

```python
m = 2.0
for iteration in range(3):
    u = 1.0 / m
    adjoint = (u - 1.0) / m
    sensitivity = -adjoint * u
    eps = 1e-5
    objective = lambda value: 0.5 * (1.0 / value - 1.0) ** 2
    finite_difference = (objective(m + eps) - objective(m - eps)) / (2.0 * eps)
    print(iteration, m, u, sensitivity, finite_difference, objective(m))
    m -= 0.5 * sensitivity
```

3回とも、状態残差 $mu-1$ と随伴残差 $m\lambda-(u-1)$ は丸め誤差の範囲で0です。
PDEの実装へ進む場合は、次の計算順序を使います。

実装では、状態求解と随伴求解を分けて記録します。
設計感度の組み立ても別の段階です。
次の擬似コードは、更新則や境界条件を省いた感度計算の骨格です。

```python
state = solve_state(design)
adjoint = solve_transpose_jacobian(state, objective)
sensitivity = direct_derivative(state, design) - adjoint @ residual_derivative(state, design)
```

## 診断値

随伴感度は、単独の更新則ではありません。
状態求解が収束していること、残差とヤコビ行列が正しく定義されていること、感度の符号が有限差分と整合することが前提です。

- 状態残差
- 随伴残差
- 加工前の感度とフィルター後の感度
- 有限差分または勾配検査

## 失敗・切替の兆候

### 失敗・切替の兆候

勾配検査が合わない場合は、更新則より先に微分実装を点検します。
状態残差が大きい場合は、状態方程式と境界条件を確認します。
格子を変えたとき感度の分布だけが大きく変わる場合も、更新を続けません。
コンプライアンスの値がもっともらしくても、感度が誤っていれば場更新は誤った方向へ進みます。

形状変数を扱う場合は、感度の検査対象が密度場から境界や配置パラメータへ移ります。
形状の更新と格子の品質を同じ反復に記録します。
状態求解も対応付け、無効な格子を通った感度を物理的な勾配として扱いません。

### 可視化は正常系から失敗へ読む

1. [場更新の実行記録](#/theater/learning/SCENARIO_TOPOLOGY_SIMP_OC)で、状態求解と感度が密度の更新へ入る位置を確認する
2. [厳しい許容誤差の評価記録](#/theater/learning/SCENARIO_PDE_STATE_TOLERANCE_TIGHT)で、状態残差と随伴残差を同じシミュレーター呼び出し軸で追う
3. [許容誤差/費用比較](#/compare/COMPARE_PDE_STATE_TOLERANCE_COST)で、許容誤差だけを変えた緩い許容誤差実行を開く
4. [状態-求解失敗の評価記録](#/theater/learning/SCENARIO_PDE_STATE_SOLVE_FAILURE)で、失敗を架空の目的値に置き換えず状態区分として読む

前面に置く代表可視化は、全体像・正常系・失敗の3つです。
緩い許容誤差の個別実行は比較が引き受け、同格の入口を増やしません。
各画面は固定格子と固定予算の教育用実行記録であり、実行時間や格子変更への安定性を示しません。

### トポロジー最適化での読み方

SIMPでは、まず密度場から剛性を作り、状態求解で変位を得ます。
その後、随伴感度を使って各要素の密度を増減したときのコンプライアンスの変化を計算します。
この順番を分けて記録すると、更新が止まった原因が「状態方程式の収束」なのか「感度の符号」なのかを切り分けられます。

教育用実行記録では、加工前の感度とフィルター後の感度を同じ反復番号で並べます。
これは実装の実行時間性能を順位付けするためではなく、どの情報が次の密度の更新を決めるかを観察するためです。

## 次に読む

[PDE制約付き最適化](#/formulations/PA045)で、設計変数と状態を分ける定式化を確認します。

[形状最適化の設計変数](#/learn/shape-optimization)で変数の表現の意味を確認し、[SIMP密度法](#/learn/simp-topology)で感度を使う更新を確認します。[密度フィルター](#/learn/density-filter)は離散場の正則化、[形状更新の失敗モード](#/learn/geometry-update-failure-modes)は格子と状態の切り分けを扱います。
