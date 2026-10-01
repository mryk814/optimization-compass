---
content_id: mirror-descent
kind: method
method_id: M_MIRROR_DESCENT
title_ja: Mirror Descent
title_en: Mirror Descent
summary: ユークリッド距離ではなく、問題に合うBregman幾何（Bregman geometry）を使う一次法です。単体（simplex）と確率分布、非一様なscale上で劣勾配stepを行います。
source_ids: [S055, S066]
prerequisites: [concept.convexity, subgradient]
related_ids: [subgradient, proximal-gradient, multi-objective]
aliases: [/learn/mirror-descent]
status: published
last_reviewed: 2026-09-30
---

ユークリッド距離ではなく、問題に合うBregman幾何（Bregman geometry）を使う一次法です。単体（simplex）と確率分布、非一様なscale上で劣勾配stepを行います。

## 30秒でつかむ

予算の配分比率を調整する場面を想像してください。比率は正で、合計は100%です。
比率に足し算で手を入れると、ある項目がマイナスになったり、合計が100%を超えたりします。「何%増やすか」というかけ算で手を入れれば、比率は正のままです。
Mirror Descentは、ユークリッド射影（Euclidean projection）が問題の構造に合わないとき、領域に合わせた距離の測り方で一手を作ります。

- **見るもの**: 劣勾配、領域、Bregman距離で測った一手、制約の状態
- **動かすもの**: 変数（primal）、双対空間での一手、mirror map
- **前進の判断**: 目的関数値、後悔（regret）、双対ギャップが改善し、領域の制約を保つこと

距離の測り方を替えると、同じ劣勾配から、別の更新が生まれます。

## 一手の意味

通常の射影劣勾配法は、ユークリッド距離で射影します。次の式は、劣勾配の反対へ進んでから、領域 $C$ の中でいちばん近い点へ戻るという意味です。

$$
x_{k+1}=\Pi_C(x_k-\eta g_k)
$$

Mirror Descentは、強凸なmirror map $\psi$ から、Bregmanダイバージェンス（Bregman divergence）を作ります。これが「距離」の代わりになります。

$$
D_\psi(x,y)=\psi(x)-\psi(y)-\nabla\psi(y)^T(x-y)
$$

そして、次の問題を解いて更新します。

$$
x_{k+1}=\arg\min_{x\in C}\left\{\eta g_k^Tx+D_\psi(x,x_k)\right\}
$$

式は「線形化した目的 $g_k^Tx$ を下げつつ、現在点からの距離 $D_\psi$ が大きくなりすぎないようにする」と言っています。
$\psi$ が $\frac12\lVert x\rVert_2^2$ なら、$D_\psi$ はユークリッド距離の二乗の半分で、射影劣勾配法に戻ります。

領域の形に合わせてmirror mapを選ぶと、更新が自然になります。

- ユークリッドの二乗ノルム: 射影勾配法に戻る
- 負のエントロピー: 確率の単体
- 対数バリア系: 正の象限、領域の内部の幾何
- 行列のエントロピー: 半正定値の構造
- 問題ごとの、座標ごとに分かれた写像: 座標ごとに尺度が違う場合

mirror mapが変われば、双対空間での一手も、主変数へ戻す方法も変わります。

### 単体上の更新

単体は、$x_i\ge0$ かつ $\sum_i x_i=1$ の領域です。ここで負のエントロピー $\psi(x)=\sum_i x_i\log x_i$ をmirror mapに使うと、更新が閉じた形になります。

$$
x_{k+1,i}=\frac{x_{k,i}\exp(-\eta g_{k,i})}{\sum_j x_{k,j}\exp(-\eta g_{k,j})}
$$

各成分に $\exp(-\eta g_i)$ を掛けて、合計が1になるように割ります。指数化勾配（exponentiated gradient）型の更新です。
掛ける数は常に正なので、成分は正のまま保たれ、合計は割り算で1に戻ります。射影は要りません。

## 小さな例

単体上で、損失 $\frac12\lVert p-t\rVert^2$ を最小にします。目標は $t=(0.65,\ 0.25,\ 0.10)$ で、最小点はこの $t$ 自身、値は $0$ です。
勾配は $p-t$ です。初期点は一様な $p_0=(1/3,\,1/3,\,1/3)$、一手の係数は $\eta=0.8$ とします。

| 反復 $k$ | $p_k$ | 損失 |
|---:|---|---:|
| 0 | $(0.3333,\ 0.3333,\ 0.3333)$ | 0.0808 |
| 1 | $(0.4219,\ 0.3064,\ 0.2717)$ | 0.0423 |
| 2 | $(0.4887,\ 0.2827,\ 0.2286)$ | 0.0218 |
| 3 | $(0.5359,\ 0.2654,\ 0.1988)$ | 0.0115 |

最初の一手を手で追います。勾配は $g_0=(-0.3167,\ 0.0833,\ 0.2333)$ です。
$\exp(-0.8g_0)$ は $(1.288,\ 0.936,\ 0.830)$ で、これを $p_0$ の各成分に掛けると、合計は $1.018$ になります。合計で割ると $p_1=(0.4219,\ 0.3064,\ 0.2717)$ です。
勾配が負の成分は大きく、正の成分は小さくなります。三つの成分は正のままで、合計は1です。

最初の数回は、損失がほぼ半分ずつ減ります。更新166回で、勾配のノルムが $10^{-9}$ を下回ります。

### ユークリッドの一手が領域をはみ出すとき

同じ初期点から、$\eta=3$ の一手を比べます。この損失では、ユークリッド勾配法の安定な範囲が $\eta<2$ です。$\eta=3$ は、ユークリッド側に不利な設定です。優劣を比べる実験ではありません。更新が領域をはみ出すかどうかを見る例です。

| 一手 | 結果 |
|---|---|
| ユークリッドの一手そのもの | $(1.283,\ 0.083,\ -0.367)$ |
| 単体へ射影したあと | $(1,\ 0,\ 0)$ |
| 指数化勾配の一手 | $(0.670,\ 0.202,\ 0.129)$ |

ユークリッドの一手は、第3成分がマイナスになり、単体の外に出ます。射影すると、頂点 $(1,\,0,\,0)$ に張り付いてしまいます。
指数化勾配の一手は、単体の内部に留まります。

この損失は滑らかで、ユークリッド距離で測ってもよく振る舞います。$\eta=0.8$ なら、ユークリッドの射影勾配法のほうが速く目標に着きます。
Mirror Descentは、領域に合った距離を使う手法です。どちらの距離が合うかは、領域と、劣勾配の大きさの偏り方で決まります。

## 向く条件・避ける条件

Mirror Descentは、領域の形と距離の測り方を合わせたいときの手法です。
先に、問題の領域と、その領域で安価に書けるmirror mapを確認します。

向く条件です。

- 凸最適化である
- 確率、単体、正の変数を扱う（[単体上の最適化](#/formulations/PA036)）
- オンライン学習や、後悔（regret）の最小化である
- ユークリッドでない幾何が自然である
- 疎で高次元の領域である
- 別の幾何で、射影を安価に書ける

避ける、または切り替える条件です。

- mirrorの射影が、元の問題より難しい
- 非凸の問題に、凸の保証を当てはめようとしている
- ユークリッド幾何で十分なのに、複雑にしている → [劣勾配法](#/learn/subgradient)や射影勾配法で足りる
- 近接作用素が使える構造である → [近接勾配法](#/learn/proximal-gradient)と比べる（[非滑らかな凸複合の最小化](#/formulations/PA010)）

## Python

次の例は、単体上で負のエントロピーを使う指数化勾配型の更新です。上の小さな例を再現します。
比較のために、ユークリッドの一手を単体へ射影する関数も置きます。

```python
import numpy as np

target = np.array([0.65, 0.25, 0.10])


def loss(p: np.ndarray) -> float:
    return float(0.5 * np.sum((p - target) ** 2))


def loss_gradient(p: np.ndarray) -> np.ndarray:
    return p - target


def exponentiated_gradient_step(p: np.ndarray, g: np.ndarray, eta: float) -> np.ndarray:
    """負のエントロピーを mirror map に使った更新: p_i ∝ p_i exp(-eta g_i)。"""
    log_weight = np.log(p) - eta * g
    log_weight -= np.max(log_weight)          # overflow を避ける
    weight = np.exp(log_weight)
    return weight / weight.sum()


def euclidean_step_with_projection(p: np.ndarray, g: np.ndarray, eta: float) -> np.ndarray:
    """比較用: ユークリッドの一手を、単体へ射影する。"""
    v = p - eta * g
    u = np.sort(v)[::-1]
    cumulative = np.cumsum(u) - 1.0
    k = np.nonzero(u * np.arange(1, v.size + 1) > cumulative)[0][-1]
    return np.maximum(v - cumulative[k] / (k + 1), 0.0)


p = np.full(3, 1.0 / 3.0)
for k in range(4):
    print(k, np.round(p, 4), round(loss(p), 4))
    p = exponentiated_gradient_step(p, loss_gradient(p), eta=0.8)
# 0 [0.3333 0.3333 0.3333] 0.0808
# 1 [0.4219 0.3064 0.2717] 0.0423
# 2 [0.4887 0.2827 0.2286] 0.0218
# 3 [0.5359 0.2654 0.1988] 0.0115

start = np.full(3, 1.0 / 3.0)
g = loss_gradient(start)
print(np.round(start - 3.0 * g, 3))                                  # ユークリッドの一手そのもの
# [ 1.283  0.083 -0.367]
print(np.round(euclidean_step_with_projection(start, g, 3.0), 3))   # 射影後
# [1. 0. 0.]
print(np.round(exponentiated_gradient_step(start, g, 3.0), 3))      # 指数化勾配の一手
# [0.67  0.202 0.129]

p = np.full(3, 1.0 / 3.0)
for k in range(1, 501):
    g = loss_gradient(p)
    if np.linalg.norm(g) < 1e-9:
        break
    p = exponentiated_gradient_step(p, g, 0.8)
print(k, p, p.sum())
# 167 [0.65 0.25 0.1 ] 1.0
```

出力の最後の `167` は、停止の判定に達した回で、更新は166回です。更新後も、成分は正で、合計は1です。
成分が0の場合の対数と桁あふれと正則化の扱いは、実装で確認します。
`log_weight` から最大値を引くのは、指数を取る前に値を揃え、桁あふれを避けるためです。合計を割る操作の前後で、結果は変わりません。

## 診断値

ユークリッドのノルムだけで一手を評価すると、選んだ幾何の意味を取り逃がす場合があります。

- 目的関数値、後悔、双対ギャップ
- Bregman距離で測った一手の大きさ
- 劣勾配のノルムと、その双対ノルム
- 最小の成分と、境界への近さ
- 制約違反
- エントロピーやスパース性
- 移動平均（running average）
- 一手の係数の予定表（step schedule）

## 失敗・切替の兆候

- mirror mapが領域の境界で数値的に不安定になる → 成分が0に近づくと、対数や指数が桁あふれする → 最小の成分に下限を置くか、正則化を足す
- 一手の予定表と双対ノルムを無視している → 一手の大きさが幾何に合っていない → 双対ノルムで劣勾配の大きさを測り直す
- 確率が0の成分を対数へ入れている → 対数が定義されない → 更新の前に、成分が正であることを保つ

::: note
Mirror Descentは、特定の一つの更新式ではありません。mirror map、ノルム、一手の予定表を含む族（family）です。比較では、幾何まで明記します。
:::

## 次に読む

- [劣勾配法](#/learn/subgradient)：非滑らかな凸問題の基本形。ユークリッド幾何での一手
- [近接勾配法](#/learn/proximal-gradient)：近接作用素を使える構造での一手
- [単体上の最適化](#/formulations/PA036)：この手法が解く問題の標準形の一つ
