---
content_id: lp-qp-conic
kind: method
method_id: MF_LP_QP_CONIC
title_ja: LP・QP・錐最適化
title_en: Linear, Quadratic, and Conic Optimization
summary: 線形・凸二次・錐構造を明示したモデルを専用ソルバーへ渡し、主・双対・gap・infeasibility情報まで利用する凸最適化familyです。
source_ids: [S004, S010, S012, S014, S055, S103]
prerequisites: [concept.convexity]
related_ids: [concept.convexity, constrained-continuous, dual-simplex, branch-and-cut]
visualization_ids: [portfolio-nominal-8-4, portfolio-cvar-8-4]
comparison_ids: [COMPARE_PORTFOLIO_NOMINAL_CVAR_8_4, COMPARE_ENERGY_NOMINAL_CVAR_8_4]
aliases: [/learn/lp-qp-conic]
visualization_aliases: []
comparison_aliases: []
status: published
last_reviewed: 2026-09-30
---

線形・凸二次・錐構造を明示したモデルを専用ソルバーへ渡し、主・双対・gap・infeasibility情報まで利用する凸最適化familyです。

## 30秒でつかむ

注文を口頭で伝える代わりに決まった伝票へ記入するように、目的と制約を係数として渡します。

- 見るもの: 主問題と双対問題の残差、目的値差
- 動かすもの: 選んだソルバーの反復状態
- 前進の判断: 可行性と最適性の必要精度を同時に満たすこと

## 一手の意味

### 三つの代表形

#### Linear program

$$
\min_x c^Tx\quad\text{subject to}\quad Ax\le b,　A_{eq}x=b_{eq}
$$

#### Convex quadratic program

$$
\min_x \frac{1}{2}x^TPx+q^Tx\quad\text{subject to linear constraints},
$$

ここで $P\succeq0$ なら目的関数は凸です。

#### Conic program

$$
\min_x c^Tx\quad\text{subject to}\quad Ax+s=b,　s\in K
$$

$K$として非負orthant、second-order cone、positive semidefinite coneなどを使います。
norm、robust 界、semidefinite relaxationを共通形式で表現できます。

### 構造を隠さない理由

凸構造をブラックボックス 目的値へ包むと、

- 双対 variable
- 最適性ギャップ
- infeasibility 証明
- 感度
- sparsity
- 初期解の再利用

を利用しにくくなります。
専用ソルバーが受け取れる係数モデルとして保つこと自体が重要です。

### Solver family

- simplex / 双対 simplex: 基底、初期解の再利用、LP再最適化
- interior-point / barrier: 大規模・疎な凸problem
- operator splitting: QPやconic problemの反復求解
- first-order conic: 中精度・巨大problem
- modeling layer: CVXPY等がcanonicalizationしてbackendへ渡す

modeling libraryとソルバーを混同しません。
どのbackend、version、optionが使われたかを保存します。

### Primalと双対を読む

凸 problemで適切な正則性があれば、主 目的値と双対 目的値の差が最適性ギャップになります。
双対 variableは、制約 界をわずかに変えたときの価値を表す感度として解釈できる場合があります。

ただし、

- 尺度調整
- degeneracy
- regularization
- ソルバー 許容誤差
- 前処理変換

により、数値的な双対値の読み方は変わります。

## 小さな例

Python節の生産LPは、$2x_1+x_2\le8$ と $x_1+2x_2\le8$ のもとで利益 $5x_1+4x_2$ を最大化します。

| 確認する点 | 利益 | 使用資源 |
|---|---:|---|
| $(0,0)$ | 0 | $(0,0)$ |
| $(4,0)$ | 20 | $(8,4)$ |
| $(8/3,8/3)$ | 24 | $(8,8)$ |

これは頂点を確認した順番で、ソルバー内部の反復ではありません。
最良点では両資源を使い切ります。
双対の資源価格 $(2,1)$ を使うと、$8\times2+8\times1=24$ です。
可行な生産量と双対値の一致から、利益24が大域最適と確認できます。

## 向く条件・避ける条件

### Alternative-first

- linear least squares → QR / SVD
- shortest path / max 流量 / マッチング → graph algorithm
- separable closed form → 解析解
- pure linear system → 因数分解
- LP relaxationだけでは整数条件を満たさない → MILP / CP-SAT

### 向いている条件

- 係数・matrixとしてモデル化できる
- 凸性が成立する
- 証明や双対情報が重要
- 疎な structureを使いたい
- repeated 求解や初期解の再利用がある
- high accuracyまたは明確な状態が必要

## Python

```python
import numpy as np
from scipy.optimize import linprog

profit = np.array([5.0, 4.0])
resource_use = np.array([
    [2.0, 1.0],
    [1.0, 2.0],
])
resource_capacity = np.array([8.0, 8.0])

result = linprog(
    c=-profit,
    A_ub=resource_use,
    b_ub=resource_capacity,
    bounds=[(0.0, None), (0.0, None)],
    method="highs",
)

if not result.success:
    raise RuntimeError(result.message)
print(result.x, -result.fun, result.status, result.message)
```

maximizationを`-profit`のminimizationへ変換したため、出力時に符号を戻しています。
単位、目的方向、制約 signをモデル reviewで明示します。

## 診断値

- 主 feasibility 残差
- 双対 feasibility 残差
- absolute / relative gap
- complementarity
- 反復 / 因数分解 time
- 前処理 簡約
- active constraints
- 実行不可能 / 非有界 証明
- numerical warning
- warm-start reuse

`infeasible`／`unbounded`／`infeasible_or_unbounded`／`iteration_limit`は異なる状態です。
目的値だけを読みません。

## 失敗・切替の兆候

- $P$が非正半定値なのに凸 QPとして扱う
- Big-Mが巨大で数値不安定
- unit 尺度が何桁も異なる
- cone relaxationが現実の条件を緩めすぎる
- 整数 decisionを連続解の丸めだけで済ませる
- ソルバー 状態を成功／失敗の二値へ潰す
- ブラックボックス simulationを無理に係数モデルへ置換

::: warning
ソルバー間比較ではモデル canonicalization／許容誤差／前処理／hardware／初期解の再利用を揃えます。
反復回数だけでは一反復の仕事量が違うため公平ではありません。
:::

### NominalとCVaRを二分野で読む

scenarioの平均だけを見る目的と、tail riskを加える目的を二つの分野で読み分けます。

| 分野 | Case | Compareで変えるもの |
|---|---|---|
| 金融 | [scenarioのtail riskを抑えて配分する](#/gallery/portfolio-cvar-allocation) | [training 目的値のrisk treatment](#/compare/COMPARE_PORTFOLIO_NOMINAL_CVAR_8_4) |
| エネルギー | [価格scenarioのtail 費用を抑えて電力を調達する](#/gallery/energy-cvar-procurement) | [同じ構造を調達問題として読む](#/compare/COMPARE_ENERGY_NOMINAL_CVAR_8_4) |

[nominal目的のTrace](#/theater/learning/SCENARIO_PORTFOLIO_NOMINAL_8_4)と[CVaR目的のTrace](#/theater/learning/SCENARIO_PORTFOLIO_CVAR_8_4)は、同じ固定教材を使います。
4変数のcapped simplexとrisk level 0.75を共有します。
sampleは8件のtrainingと4件のheld-outに固定します。
0.05刻みのgridと12回のloss evaluation 計算予算も固定し、risk treatmentだけを変えます。

実行Traceは固定4資産の教材です。
エネルギー比較はsimplex・scenario・tail riskの読み方だけを再利用し、電力市場／需要／送電網／契約を再現しません。
4件のheld-out結果から一般性能rankingや確率保証を導きません。

## 次に読む

LP 基底再最適化は[Dual Simplex](#/learn/dual-simplex)、MILP探索との接続は[Branch-and-Cut](#/learn/branch-and-cut)で確認できます。

- 問題の形を確認する: [線形計画](#/formulations/PA017)
