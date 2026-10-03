---
content_id: optimality-criteria-topology
kind: method
method_id: M_OC_TOPOLOGY
title_ja: トポロジー最適化のOptimality Criteria
title_en: Optimality Criteria Update for Topology Optimization
summary: Optimality Criteriaは、密度感度と体積率制約から要素密度を乗法的に更新し、コンプライアンス最小化の設計場を効率よく改善する更新則です。
source_ids: [S097, S098]
prerequisites: [simp-topology, density-filter]
related_ids: [mma, adjoint-sensitivity, topology-optimization]
visualization_ids: [topology-optimization-field-evolution]
comparison_ids: [COMPARE_TOPOLOGY_OC_MMA]
aliases: [/learn/optimality-criteria-topology]
status: published
last_reviewed: 2026-09-30
---

Optimality Criteriaは、密度感度と体積率制約から要素密度を乗法的に更新し、コンプライアンス最小化の設計場を効率よく改善する更新則です。

## 30秒でつかむ

同じ材料量を守りながら、よく働く場所へ材料を少しずつ移します。

- 見るもの: 密度感度と体積率
- 動かすもの: 要素密度と体積制約の乗数
- 前進の判断: 体積を守り、柔らかさと更新幅が落ち着くこと

## 一手の意味

負の感度を持つ密度へ材料を配り、体積の乗数 $\lambda$ を二分法で合わせます。

$$
\rho_e^{new}=\operatorname{clip}\left(
\rho_e\sqrt{\frac{-\partial c/\partial\rho_e}{\lambda\,\partial V/\partial\rho_e}},
\max(\rho_{\min},\rho_e-m),\min(1,\rho_e+m)\right)
$$

ここで $m$ は更新幅の上限です。
平方根は代表的な更新指数を使った形です。
感度の符号と体積微分が、この形の前提に合うか確認します。

### 体積率を守りながら密度を変える

SIMPで状態と感度を計算した後、OCは感度の符号と大きさを使って密度を更新します。
更新倍率には更新幅の上限と上下限があり、全要素を自由に動かすわけではありません。

体積率制約があるため、更新倍率の係数は通常、更新後の平均密度が目標に近づくように調整します。
この係数を決める部分が、単なる勾配降下との違いです。

OCの更新は、KKT条件に近づくための実用的な更新則ですが、離散化された問題の大域解を証明するものではありません。
更新幅の上限やフィルター半径と射影の設定によって、同じ体積率でも別の局所的な密度場へ到達します。
そのため、更新を速く見せる単一のコンプライアンス値ではなく、停止条件と感度の整合性を含む反復履歴を残します。

### 反復の読み方

一つの反復では、次の順序が崩れていないか確認します。

1. 現在の密度から状態方程式を解く
2. コンプライアンスと感度を計算する
3. フィルター後の感度からOC更新を作る
4. 体積率と更新幅の上限を確認する

Theaterではこの順序を場と数値の両方で追えます。

## 小さな例

二つの密度を $\rho=(0.5,0.5)$ とし、平均密度0.5を守ります。
感度の動きを追うため、目的を $1/\rho_1+4/\rho_2$ とする小さな代用問題です。
更新幅は0.1、更新指数は $1/2$ とします。

| 反復 | $\rho_1$ | $\rho_2$ | 目的値 | 平均密度 |
|---|---:|---:|---:|---:|
| 0 | 0.5000 | 0.5000 | 10.0000 | 0.5000 |
| 1 | 0.4000 | 0.6000 | 9.1667 | 0.5000 |
| 2 | 0.3333 | 0.6667 | 9.0000 | 0.5000 |
| 3 | 0.3333 | 0.6667 | 9.0000 | 0.5000 |

よく働く第2要素へ密度を移し、体積の乗数は2反復目から9へ落ち着きます。
これはOCの体積調整を示す代用問題で、有限要素解析のコンプライアンスではありません。

### OC更新の場を見る

![8×4要素の固定教材で、OCによる初期密度場、反復6、反復12を並べた実行結果。各反復のコンプライアンス、中間密度の割合、市松模様の指標と、フィルターなしの失敗比較を併記する。](./media/topology-field-execution.svg "固定したOC教材の計算結果です。反復履歴とフィルターの失敗比較を読む図であり、MMAとの性能順位や実FEMの妥当性は示しません。")

上段から左下へ、OCが同じ材料量の目標のもとで場を更新する流れを追います。
右下は更新則の比較ではなく、フィルターを外したときの失敗比較です。

```text
lower, upper = bracket_volume_multiplier(filtered_sensitivity, target_volume)
multiplier = bisect_volume_multiplier(lower, upper, density, filtered_sensitivity)
candidate = np.clip(density * update_factor(multiplier, filtered_sensitivity), 0.001, 1.0)
next_density = limit_move(candidate, density, move_limit)
```

## 向く条件・避ける条件

### 向く条件・避ける条件

SIMPのコンプライアンス最小化のように、密度と感度と体積率の関係が整理されている問題に向きます。
制約が増えたり、複雑な非線形性が強くなったりすると、[MMA](#/learn/mma)のような近似問題の組み立てを比較します。

## Python

小さな例の計算を再現する、実行可能な教育用コードです。

```python
import numpy as np

density = np.array([0.5, 0.5])
weights = np.array([1.0, 4.0])
for iteration in range(1, 4):
    sensitivity = -weights / density**2
    lower, upper = 0.0, 100.0
    for _ in range(100):
        multiplier = 0.5 * (lower + upper)
        candidate = np.clip(
            density * np.sqrt(-sensitivity / multiplier),
            np.maximum(0.001, density - 0.1),
            np.minimum(1.0, density + 0.1),
        )
        if candidate.mean() > 0.5:
            lower = multiplier
        else:
            upper = multiplier
    density = candidate
    print(iteration, density, (weights / density).sum(), density.mean())
```

## 診断値

`volume_fraction`が目標に近いことを確認します。
`compliance`／`gray_fraction`／`checkerboard_score`／`projection_beta`も同じ反復で確認します。

## 失敗・切替の兆候

密度が上下限に張り付いたまま荷重経路が変わらない、コンプライアンスだけが下がって交互模様の指標が上がる場合は、更新幅の上限とフィルターを見直します。
更新の振動が強い場合は、固定設定の範囲を変えた比較を別に作り、OCの性能順位とは分けて読みます。

## 次に読む

[同じ場でOCとMMAを比較する](#/compare/COMPARE_TOPOLOGY_OC_MMA)と、更新則の差をコンプライアンスだけでなく場指標で確認できます。

- 問題の形を確認する: [PDE制約付き最適化](#/formulations/PA045)
