---
content_id: simp-topology
kind: method
method_id: M_SIMP_TOPOLOGY
title_ja: SIMP密度法
title_en: SIMP Topology Optimization
summary: SIMP密度法は、要素密度を連続変数にして剛性を密度のべき乗で補間し、体積率制約のもとでコンプライアンスを下げるトポロジー最適化手法です。
source_ids: [S097, S098]
prerequisites: [topology-optimization, concept.constraint-class]
related_ids: [shape-optimization, geometry-update-failure-modes, density-filter, optimality-criteria-topology, mma]
visualization_ids: [topology-optimization-field-evolution, shape-topology-representation-contrast]
comparison_ids: [COMPARE_TOPOLOGY_OC_MMA, COMPARE_SHAPE_TOPOLOGY_REPRESENTATION]
aliases: [/learn/simp-topology]
status: published
last_reviewed: 2026-09-30
---

SIMP密度法は、要素密度を連続変数にして剛性を密度のべき乗で補間し、体積率制約のもとでコンプライアンスを下げるトポロジー最適化手法です。

## 30秒でつかむ

設計領域の各升へ材料の濃淡を置き、濃淡を剛性へ変換して荷重の通り道を作ります。

- 見るもの: 密度、変位、コンプライアンス
- 動かすもの: 要素密度とそれに対応する剛性
- 前進の判断: 体積を守り、物理残差と密度の指標が落ち着くこと

## 一手の意味

### 密度を剛性へ写像する

要素 $e$ の密度を $\rho_e$ とし、ヤング率を次で補間します。

$$
E_e(\rho_e)=E_{\min}+\rho_e^p(E_0-E_{\min}).
$$

$p>1$ にすると中間密度の剛性が相対的に不利になります。
その結果、密度場は材料と空孔に分かれやすくなりますが、これは罰則化を含む連続緩和です。

### 更新で見るもの

状態方程式 $K(\rho)u=F$ を解き、コンプライアンスと密度感度を計算します。
感度から密度を更新したら、次の反復で再び状態を解きます。

- 体積率が目標に近いか
- 中間密度率が減っているか
- フィルター後の感度を使っているか
- メッシュを変えたとき設計が大きく変わらないか

コンプライアンスの単調な改善だけでは終了判定に足りません。

SIMPで見えている密度は、完成した部材形状そのものではありません。
密度場は、連続な設計変数を使うための緩和です。
罰則化とフィルターの選択によって最終場の読み方が変わります。
射影とメッシュも別に記録します。

中間密度が残る場合も、単にpを大きくしません。
状態方程式の残差と感度の勾配の検算を分けて確認します。
体積制約とメッシュの細分化も同時に確認します。

境界を直接更新する形状最適化とは、設計変数と失敗モードが異なります。
SIMPの市松模様や中間密度を、形状更新の成功と読み替えないでください。

## 小さな例

1本のばねを要素に見立て、荷重を1とします。
係数は $E_0=1$、$E_{\min}=0.001$、$p=3$ です。
剛性を $E(\rho)$ とすれば、変位もコンプライアンスも $1/E(\rho)$ です。

| 評価する密度 $\rho$ | 剛性 $E(\rho)$ | コンプライアンス |
|---|---:|---:|
| 0.25 | 0.0166 | 60.2070 |
| 0.50 | 0.1259 | 7.9444 |
| 0.75 | 0.4225 | 2.3671 |

密度を2倍にしても剛性は2倍になりません。
べき乗の補間が中間密度の扱いを変えます。
これは独立な3点評価で、体積制約を守る最適化反復ではありません。

### 実行結果を先に見る

![8×4要素の固定教材で、初期密度場、フィルターありの反復6と反復12、フィルターなしの反復12を比較した実行結果。各図にコンプライアンス、中間密度の割合、市松模様の指標を表示する。](./media/topology-field-execution.svg "SIMPの密度場を固定Python生成プログラムで更新した結果です。濃淡は設計変数であり、完成部材の強度や製造性を保証しません。")

材料経路の濃淡だけでなく、中間密度率と市松模様を同じ反復で見ます。
コンプライアンスだけが改善しても、場の離散化アーティファクトが減ったとは限りません。

## 向く条件・避ける条件

### 向く条件・避ける条件

要素密度を設計変数として扱え、体積率と状態方程式を定義できる問題に向きます。
接触や座屈を追加すると、同じ更新式だけでは設計の意味を保てない場合があります。
製造制約と非線形材料も別にモデル化します。

## Python

小さな例の計算を再現する、実行可能な教育用コードです。

```python
for density in (0.25, 0.5, 0.75):
    stiffness = 0.001 + density**3 * (1.0 - 0.001)
    load = 1.0
    displacement = load / stiffness
    compliance = load * displacement
    print(density, stiffness, compliance)
```

## 診断値

`volume_fraction`と`compliance`を反復ごとに保存します。
`gray_fraction`と`checkerboard_score`も対応付けます。
フィルター半径と罰則化を結果と一緒に記録します。
射影の係数βと更新幅の上限も必要です。

## 失敗・切替の兆候

交互模様の指標が下がらない場合は、[密度フィルター](#/learn/density-filter)や射影を見直します。
中間密度率が残り続ける場合も同様です。
メッシュ変更で荷重経路が変わる場合は、メッシュ依存性を先に調べます。
形状パラメータを更新している場合は、[形状更新の失敗モード](#/learn/geometry-update-failure-modes)へ進みます。
反転・メッシュ品質・状態方程式の残差を分けて確認します。
更新の制約処理が複雑なら、[MMA](#/learn/mma)との比較が有効です。

### 表現と更新則を別に比べる

| 比較軸 | 固定するもの | 変えるもの | 入口 |
|---|---|---|---|
| 設計表現 | 同じ物理条件と外側の包絡面 | 3つの形状パラメータ／密度場 | [形状／トポロジーの比較](#/compare/COMPARE_SHAPE_TOPOLOGY_REPRESENTATION) |
| 更新則 | 同じ密度場と評価条件 | OC／MMA | [OC／MMA Compare](#/compare/COMPARE_TOPOLOGY_OC_MMA) |

[設計表現を比較する再生ページ](#/theater/learning/SCENARIO_SHAPE_TOPOLOGY_REPRESENTATION_CONTRAST)では、パラメータと幾何を分けます。
メッシュと物理状態も同じ評価軸で対応付けます。
これはSIMPやSLSQPの実ソルバー結果ではなく、結合構造変更を許す表現の違いを読む固定教材です。
実時間・解品質・一般性能の順位付けには使いません。

```text
stiffness = emin + density**penalty * (e0 - emin)
state = solve_linear_system(assemble_stiffness(stiffness), load)
compliance = load @ state
```

## 次に読む

[Optimality Criteria](#/learn/optimality-criteria-topology)は体積制約を含む更新則、[随伴感度](#/learn/adjoint-sensitivity)は状態方程式から感度を得る仕組みを説明します。

- 問題の形を確認する: [PDE制約付き最適化](#/formulations/PA045)
