---
content_id: lp-qp-conic
kind: method
method_id: MF_LP_QP_CONIC
title_ja: LP・QP・錐最適化
title_en: Linear, Quadratic, and Conic Optimization
summary: 線形・凸二次・錐構造を明示したモデルを専用ソルバーへ渡し、主問題・双対問題・ギャップ・実行不能性情報まで利用する凸最適化手法群です。
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

線形・凸二次・錐構造を明示したモデルを専用ソルバーへ渡し、主問題・双対問題・ギャップ・実行不能性情報まで利用する凸最適化手法群です。

## 30秒でつかむ

注文を口頭で伝える代わりに決まった伝票へ記入するように、目的と制約を係数として渡します。

- 見るもの: 主問題と双対問題の残差、目的値差
- 動かすもの: 選んだソルバーの反復状態
- 前進の判断: 可行性と最適性の必要精度を同時に満たすこと

## 一手の意味

### 三つの代表形

#### 線形計画

$$
\min_x c^Tx\quad\text{subject to}\quad Ax\le b,　A_{eq}x=b_{eq}
$$

#### 凸二次計画

$$
\min_x \frac{1}{2}x^TPx+q^Tx\quad\text{subject to linear constraints},
$$

ここで $P\succeq0$ なら目的関数は凸です。

#### 錐計画

$$
\min_x c^Tx\quad\text{subject to}\quad Ax+s=b,　s\in K
$$

$K$として非負象限、二次錐、半正定値錐などを使います。
ノルム、頑健な界、半正定値緩和を共通形式で表現できます。

### 構造を隠さない理由

凸構造をブラックボックス目的値へ包むと、

- 双対変数
- 最適性ギャップ
- 実行不能性証明
- 感度
- 疎性
- 初期解の再利用

を利用しにくくなります。
専用ソルバーが受け取れる係数モデルとして保つこと自体が重要です。

### 解法手法群

- 主単体法 / 双対単体法: 基底、初期解の再利用、LP再最適化
- 内点法 / 障壁: 大規模・疎な凸問題
- 作用素分割: QPや錐問題の反復求解
- 一次錐: 中精度・巨大問題
- モデル化を担う層: CVXPY等が標準形へ変換して実行に使うソルバーへ渡す

モデル化ライブラリとソルバーを混同しません。
どの実行に使うソルバー、バージョン、オプションが使われたかを保存します。

### 主問題と双対を読む

凸問題で適切な正則性があれば、主目的値と双対目的値の差が最適性ギャップになります。
双対変数は、制約界をわずかに変えたときの価値を表す感度として解釈できる場合があります。

ただし、

- 尺度調整
- 退化
- 正則化
- ソルバー許容誤差
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

### 専用構造から先に検討する

- 線形最小二乗 → QR / SVD
- 最短路 / 最大流 / マッチング → グラフアルゴリズム
- 変数分離で閉形式が得られる問題 → 解析解
- 純粋な線形方程式系 → 因数分解
- LP 緩和だけでは整数条件を満たさない → MILP / CP-SAT

### 向いている条件

- 係数・行列としてモデル化できる
- 凸性が成立する
- 証明や双対情報が重要
- 疎な構造を使いたい
- 反復する求解や初期解の再利用がある
- 高精度または明確な状態が必要

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

最大化を`-profit`の最小化へ変換したため、出力時に符号を戻しています。
単位、目的方向、制約の符号をモデルの点検で明示します。

## 診断値

- 主実行可能性残差
- 双対実行可能性残差
- 絶対 / 相対ギャップ
- 相補性
- 反復 / 因数分解時間
- 前処理簡約
- 有効な制約
- 実行不可能 / 非有界証明
- 数値計算の警告
- 初期解の再利用

`infeasible`／`unbounded`／`infeasible_or_unbounded`／`iteration_limit`は異なる状態です。
目的値だけを読みません。

## 失敗・切替の兆候

- $P$が非正半定値なのに凸 QPとして扱う
- Big-Mが巨大で数値不安定
- 単位の尺度が何桁も異なる
- 錐緩和が現実の条件を緩めすぎる
- 整数決定変数を連続解の丸めだけで済ませる
- ソルバー状態を成功／失敗の二値へ潰す
- ブラックボックスシミュレーションを無理に係数モデルへ置換

::: warning
ソルバー間比較ではモデル標準形への変換／許容誤差／前処理／計算機環境／初期解の再利用を揃えます。
反復回数だけでは一反復の仕事量が違うため公平ではありません。
:::

### 平均目的とCVaRを二分野で読む

シナリオの平均だけを見る目的と、裾のリスクを加える目的を二つの分野で読み分けます。

| 分野 | 事例 | 比較で変えるもの |
|---|---|---|
| 金融 | [シナリオの裾のリスクを抑えて配分する](#/gallery/portfolio-cvar-allocation) | [学習目的値のリスクの扱い](#/compare/COMPARE_PORTFOLIO_NOMINAL_CVAR_8_4) |
| エネルギー | [価格シナリオの裾の費用を抑えて電力を調達する](#/gallery/energy-cvar-procurement) | [同じ構造を調達問題として読む](#/compare/COMPARE_ENERGY_NOMINAL_CVAR_8_4) |

[平均目的の実行記録](#/theater/learning/SCENARIO_PORTFOLIO_NOMINAL_8_4)と[CVaR目的の実行記録](#/theater/learning/SCENARIO_PORTFOLIO_CVAR_8_4)は、同じ固定教材を使います。
4変数の各成分に上限を持つ単体とリスク水準 0.75を共有します。
標本は8件の学習用と4件の評価用に固定します。
0.05刻みの格子と12回の損失の評価計算予算も固定し、リスクの扱いだけを変えます。

実行記録は固定4資産の教材です。
エネルギー比較は単体・シナリオ・裾のリスクの読み方だけを再利用し、電力市場／需要／送電網／契約を再現しません。
4件の評価用に分けた結果から一般性能順位付けや確率保証を導きません。

## 次に読む

LP 基底再最適化は[Dual Simplex](#/learn/dual-simplex)、MILP探索との接続は[Branch-and-Cut](#/learn/branch-and-cut)で確認できます。

- 問題の形を確認する: [線形計画](#/formulations/PA017)
