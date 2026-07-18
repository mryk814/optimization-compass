---
content_id: spsa
kind: method
method_id: M_SPSA
title_ja: SPSA（同時摂動確率近似）
title_en: Simultaneous Perturbation Stochastic Approximation
summary: 全座標を個別に差分評価せず、ランダムな一方向の正負2評価から高次元勾配を確率的に推定する局所法です。
source_ids: [S018, S056]
related_ids: [family.local-dfo, method.gradient-descent]
status: published
last_reviewed: 2026-07-18
---

全座標を個別に差分評価せず、ランダムな一方向の正負2評価から高次元勾配を確率的に推定する局所法です。

## 30秒でつかむ

この手法の気持ちは、**変数が何千個あっても各座標を一つずつ揺らさず、全部を同時に少し揺らした二つの評価から、だいたいの下り方向を知りたい**というものです。

- 見ているもの: 正負に摂動した2点の関数値
- 動かしているもの: 現在点、ランダム摂動、gain sequence
- 前進の判断: noisyなbest-so-farと平均的な改善
- 恐れていること: 推定variance、step scheduleの不適合、制約違反

一回の勾配推定に必要な評価数が次元へ直接比例しにくい点が強みですが、推定方向は強く揺れます。

## まず確認すること

| 項目 | 確認内容 |
|---|---|
| dimension | 座標差分が高価になるほど大きいか |
| noise | 同一点でも値が揺れるか、平均化できるか |
| budget | 多数の小stepを繰り返せるか |
| bounds | 摂動点と更新点をどう実行可能に保つか |
| scale | 座標ごとの単位差が摂動を壊さないか |

正確な自動微分を使えるなら、まずstochastic gradientや一階法を比較します。低次元なら通常の有限差分の方が診断しやすい場合があります。

## 仕組み

ランダムvector $\Delta_k$を作り、二つの値を評価します。

$$
y_+ = f(x_k+c_k\Delta_k),\qquad y_- = f(x_k-c_k\Delta_k)
$$

各成分の勾配推定は概ね次です。

$$
\hat g_{k,i}=\frac{y_+-y_-}{2c_k\Delta_{k,i}}
$$

その後、$x_{k+1}=x_k-a_k\hat g_k$で更新します。$a_k$と$c_k$のschedule、摂動分布、再評価回数が挙動を決めます。

## 向く条件・避ける条件

向きやすい条件:

- 高次元で関数値だけ得られる
- 評価noiseがあり、座標差分を大量に取れない
- 1回の勾配推定あたりの評価数を抑えたい
- 粗い局所改善を多数stepで積み上げられる

避ける条件:

- 評価回数が数十回しかない高価実験
- 離散・カテゴリ変数が中心
- 厳密なstationarityや大域certificateが必要
- bounds外の評価が危険でprojectionも意味を壊す

## うまくいったサインと切替サイン

見る値:

- best-so-farと移動平均objective
- 推定gradient norm
- update norm
- 正負評価差
- 同じ点の再評価variance
- boundsへのclip率
- seed間の結果分布

切替サイン:

- update方向が毎回反転しbestが改善しない → gain scheduleと平均化を見直す
- 正負評価差がnoise以下 → 摂動幅を調整する
- boundsへ頻繁にclip → parameterizationやprojectionを見直す
- 少数評価しか使えない → Bayesian Optimizationへ
- gradient oracleを追加できる → stochastic gradient methodへ

## Python

```python
import numpy as np

rng = np.random.default_rng(7)


def objective(x: np.ndarray) -> float:
    noise = 0.01 * rng.normal()
    return float(np.sum((x - 1.0) ** 2) + noise)


x = np.zeros(20)
for iteration in range(1, 101):
    delta = rng.choice(np.array([-1.0, 1.0]), size=x.shape)
    a_k = 0.1 / (iteration ** 0.602)
    c_k = 0.1 / (iteration ** 0.101)
    y_plus = objective(x + c_k * delta)
    y_minus = objective(x - c_k * delta)
    gradient_estimate = (y_plus - y_minus) / (2.0 * c_k * delta)
    x = x - a_k * gradient_estimate

print(x[:3], objective(x))
```

## コラム: 2評価で勾配が正確になるわけではない

SPSAは評価数を抑える代わりにvarianceを受け入れます。単一stepの方向を精密に解釈するより、複数step・複数seed・移動平均で傾向を見ます。

[局所Derivative-free最適化の選び分け](#/learn/family.local-dfo)でMADSやNelder–Meadとの次元・budget・制約対応の違いを確認してください。
