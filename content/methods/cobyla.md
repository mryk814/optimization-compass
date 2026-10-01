---
content_id: cobyla
kind: method
method_id: M_COBYLA
title_ja: COBYLA
title_en: Constrained Optimization BY Linear Approximations
summary: 目的関数と制約の値だけから局所線形モデルを作り、信頼領域半径内で一般不等式制約付きの局所解を探す微分不要法です。
source_ids: [S002, S018, S056]
prerequisites: [concept.derivative-free, constrained-continuous]
related_ids: [constrained-continuous, mads, pattern-search]
aliases: [/learn/cobyla]
status: published
last_reviewed: 2026-09-30
---

目的関数と制約の値だけから局所線形モデルを作り、信頼領域半径内で一般不等式制約付きの局所解を探す微分不要法です。

## 30秒でつかむ

机の端を越えないよう、周囲の数点を試して進む向きを決める感覚です。

COBYLAは勾配を要求しない代わりに、近くの評価点から目的関数と制約の傾きを推定します。

- 見るもの: 目的関数、制約 値、単体の配置
- 動かすもの: 局所線形モデル、信頼領域の半径、候補点
- 前進の判断: 可行な点で目的関数が改善し、モデルと実評価の差が抑えられること
- 恐れていること: 尺度の不一致、雑音、細い可行領域、局所モデルの退化

## 一手の意味

局所線形近似 $m_k$ を、信用する半径 $\Delta_k$ の中で改善します。

$$
\min_s m_k^f(s)
\quad \text{s.t.}\quad
m_k^{c_i}(s)\ge0,\quad \|s\|\le\Delta_k.
$$

### 何を近似するか

COBYLAは単体状の補間点から、目的関数と各制約の局所線形近似を作ります。そのモデル上で信頼領域の半径内の一歩を求め、実評価でモデルを更新します。

必要なのは関数値の評価であり、勾配やJacobianを直接要求しません。
局所モデルの品質には尺度と補間点の配置が影響します。
評価の雑音にも注意します。

### Constraintの表現

実装では通常、すべての制約を

$$
c_i(x)\ge0
$$

のような不等式へ揃えます。等式制約は二つの不等式制約や許容誤差帯として表すことがありますが、厳密等式を近似帯へ変える意味を確認します。

## 小さな例

Python例は、円の内部と直線の上側で $(1,2)$ に近い点を探します。
初期半径0.5で、最初の3回のコールバックに記録された候補です。

| 記録 | 候補点 | 目的値 | 円の制約違反 |
|---|---|---:|---:|
| 初期点 | $(0.2000,0.4000)$ | 3.2000 | 0.0000 |
| 1回目 | $(0.2117,1.0073)$ | 1.6069 | 0.0595 |
| 2回目 | $(0.2117,1.0073)$ | 1.6069 | 0.0595 |
| 3回目 | $(0.2117,1.0073)$ | 1.6069 | 0.0595 |

記録が同じでも、内部では近似や半径の調整が進むことがあります。
この候補は円の外です。制約違反が残る点は解ではありません。
最後は約 $(0.4472,0.8945)$、目的値約1.5279でした。
最大制約違反は約 $8.75\times10^{-9}$ でした。

## 向く条件・避ける条件

### 先に確認すること

- 目的関数と制約を関数値の評価だけで評価できるか
- 制約を一貫して$c_i(x)\ge0$へ表せるか
- 初期信頼領域 尺度（`rhobeg`）と変数・制約の尺度が釣り合っているか
- 大域最適解ではなく、局所的な可行 候補で足りるか

### 向いている条件

- 低〜中次元の滑らかまたは中程度に 滑らか ブラックボックス
- 勾配 / Jacobianが利用できない
- 一般不等式制約
- 評価が比較的安価
- 局所 可行 候補が欲しい

## Python

```python
import numpy as np
from scipy.optimize import minimize


def objective(x: np.ndarray) -> float:
    return float((x[0] - 1.0) ** 2 + (x[1] - 2.0) ** 2)


def inside_disk(x: np.ndarray) -> float:
    return float(1.0 - x[0] ** 2 - x[1] ** 2)


def above_line(x: np.ndarray) -> float:
    return float(x[0] + x[1] - 0.5)


result = minimize(
    objective,
    x0=np.array([0.2, 0.4]),
    method="COBYLA",
    constraints=[
        {"type": "ineq", "fun": inside_disk},
        {"type": "ineq", "fun": above_line},
    ],
    options={"rhobeg": 0.5, "tol": 1e-7, "maxiter": 3_000},
)

violation = max(0.0, -inside_disk(result.x), -above_line(result.x))
print(result.success, result.x, result.fun, violation, result.message)
```

SciPy版の上下限対応と`catol`の意味は、利用版の公式文書で確認します。
`rhobeg`と`tol`が指定する半径も確認します。

## 診断値

### Trust-領域 radius

- `rhobeg`: 初期探索尺度
- final radius / `tol`: 終了時の局所モデル 尺度
- 大きすぎる: 局所線形モデルが悪い
- 小さすぎる: 初期点近傍から抜けにくい

変数を無次元化し、制約値の尺度も揃えます。

### 最初に見る診断値

- 目的関数 / 可行点の最良目的値
- 最大制約違反
- 信頼領域の半径
- 目的関数評価数
- 可行 評価 割合
- モデル 配置
- 失敗した / 非有限値 評価数
- 停止理由

COBYLAは微分を使う KKT 残差を直接返さない場合があるため、可行性と局所摂動による改善余地を別に確認します。

## 失敗・切替の兆候

- 厳密な 等式制約が重要 → 等式制約を扱える別の制約法を検討する
- 強い雑音で線形モデルが不安定 → 繰り返し評価や雑音を考慮する手法を比較する
- 高次元 → モデルの評価数と配置を確認し、別の微分不要法を検討する
- 1評価が極端に高価 → 低評価予算向けの手法や代理モデルを比較する
- 不連続な 可行性 → COBYLAの連続局所モデルを前提にしない
- 大域最適解や証明が必要 → 局所 手法の保証範囲を超えるため、別のソルバーを検討する
- 可行領域が極端に細い → 初期点、尺度合わせ、制約の表現を見直す

::: warning
COBYLAが制約違反を小さくしたことと、連続モデルの大域最適性は別です。異なる初期点と尺度で再確認します。
:::

## 次に読む

- [制約付きの微分なし問題](#/formulations/PA014)：値だけで一般制約を扱う形
- [COBYQA](#/learn/cobyqa)：局所二次近似
- [MADS](#/learn/mads)：格子と近傍調査
