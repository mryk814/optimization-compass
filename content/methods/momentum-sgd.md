---
content_id: momentum-sgd
kind: method
method_id: M_MOMENTUM_SGD
title_ja: Momentum SGD
title_en: Momentum Stochastic Gradient Descent
summary: 現在の勾配だけでなく過去の更新を速度として蓄積し、同じ方向の移動を強めて谷を横切る振動を抑える一次法です。
source_ids: [S048, S049, S056]
prerequisites: [method.gradient-descent]
related_ids: [method.gradient-descent, adam, bfgs]
visualization_ids: [momentum-quadratic-divergence]
comparison_ids: [COMPARE_GRADIENT_FAMILY, COMPARE_GRADIENT_DIVERGENCE]
aliases: [/learn/momentum-sgd]
comparison_aliases: [COMPARE_GRADIENT_FAMILY|/compare/gradient-quadratic]
status: published
last_reviewed: 2026-09-30
---

現在の勾配だけでなく過去の更新を速度として蓄積し、同じ方向の移動を強めて谷を横切る振動を抑える一次法です。

## 30秒でつかむ

坂を下る台車は、傾きが変わってもそれまでの勢いをすぐには失いません。Momentumも過去の勾配を速度に残して進みます。

Momentumは、毎回の勾配をそのまま使わず、過去の更新を速度として残します。
細長い谷で急な方向へ往復する成分を弱め、緩い方向へ進む成分を積み上げる設計です。

- 見るもの: 目的、勾配、速度、更新
- 動かすもの: パラメータ、速度状態、学習率
- 前進の判断: これまでの最良値と勾配ノルムが安定し、速度が過大にならないこと

## 一手の意味

### 何を状態として持つか

代表的なheavy-ball型では、速度 $v_k$ とパラメータ $x_k$ を

$$
v_{k+1}=\beta v_k+\nabla f(x_k)
$$

$$
x_{k+1}=x_k-\eta v_{k+1}
$$

で更新します。実装によって勾配へ $(1-\beta)$ を掛けるか、Nesterov 先読みを使うか、減衰を入れるかが異なります。

- $\eta$: 学習率
- $\beta$: モーメンタム係数
- $v_k$: 過去の勾配を含む更新状態

### なぜジグザグを抑えられるか

細長い谷では、急な方向の勾配符号が反復ごとに入れ替わり、緩い方向の符号は比較的一貫します。Momentumは符号が交互に変わる成分を相殺し、同じ方向の成分を蓄積します。

一方で、蓄積された速度は最小点を通り過ぎても残るため、学習率や$\beta$が大きすぎると行き過ぎや発散を起こします。

## 小さな例

$f(x)=(x-1)^2$ を $x_0=2$、$v_0=0$ から解きます。
学習率 $\eta=0.1$、係数 $\beta=0.5$ を使い、一手の意味の式を3回実行しました。

| 更新 | 速度 $v$ | 更新後の $x$ | $f(x)$ |
|---|---:|---:|---:|
| 1 | 2.000 | 1.800 | 0.640000 |
| 2 | 2.600 | 1.540 | 0.291600 |
| 3 | 2.380 | 1.302 | 0.091204 |

2回目は勾配が小さくなっても、前の速度が残るため移動量が増えます。
速度の蓄積を確かめる例であり、どの係数でも安定するという意味ではありません。

## 向く条件・避ける条件

### 向いている条件

- 滑らかなな大規模問題
- 確率勾配を繰り返し利用する
- 勾配降下法が細長い谷で振動する
- 座標ごとの適応的尺度調整より単純な状態を使いたい
- 学習繰返しと予定を管理できる

## Python

```python
import numpy as np


def objective(x: np.ndarray) -> float:
    return float((x[0] - 1.0) ** 2 + 40.0 * (x[1] + 2.0) ** 2)


def gradient(x: np.ndarray) -> np.ndarray:
    return np.array([2.0 * (x[0] - 1.0), 80.0 * (x[1] + 2.0)])


x = np.array([4.0, 3.0])
velocity = np.zeros_like(x)
learning_rate = 0.02
momentum = 0.85

for _ in range(2_000):
    g = gradient(x)
    velocity = momentum * velocity + g
    candidate = x - learning_rate * velocity
    if not np.isfinite(objective(candidate)):
        raise FloatingPointError("non-finite objective")
    x = candidate
    if np.linalg.norm(g) < 1e-8 and np.linalg.norm(velocity) < 1e-8:
        break

print(x, objective(x), np.linalg.norm(gradient(x)))
```

この更新式は教育用です。フレームワークごとのMomentum / Nesterov定義、重み減衰、勾配の平均化を公式文書で確認します。

## 診断値

### 最初に見る診断値

- 目的とこれまでの最良値
- 勾配ノルム
- 速度ノルム
- 更新量のノルム
- 学習率
- 勾配と速度の角度
- 振動 / 行き過ぎ
- ミニバッチ間の勾配の分散
- 評価または学習更新の予算

速度ノルムが大きいまま目的が悪化する場合、単に反復を増やしません。
学習率／$\beta$／尺度調整を見直します。

- 恐れていること: 行き過ぎ、発散、古い速度、ミニバッチ雑音

## 失敗・切替の兆候

- 最小点周辺で振動が減らない → 学習率、$\beta$、尺度調整を見直す
- 速度が蓄積して発散 → 学習率または$\beta$を下げ、勾配のクリッピングを確認する
- 学習率減衰後も古い速度が支配 → 速度の扱いと予定を確認する
- パラメータ尺度が極端に違う → 尺度調整または適応的手法を比較する
- 疎な / 非定常な勾配で状態が古くなる → モーメンタム係数と更新予定を見直す
- Adam等との比較で予定や正則化が異なる → 同じ予算、予定、正則化で比較する

### 実行結果を先に見る

![同じ細長い二次目的、初期点、40回の評価予算で実行したGradient Descent、Momentum、Adamの軌跡。Momentumは谷を横切る往復を残しながら、蓄積した速度で進む。](./media/gradient-family-execution.svg "固定Python生成プログラムの実行結果です。橙のMomentum軌跡では、谷を横切る振動と進行方向への蓄積を同時に読めます。この一例は一般的な性能の順位付けではありません。")

橙の線が谷を何度も横切る形を見ます。速度を持つことは振動を即座に消すのではなく、符号が入れ替わる更新を反復の中でならす設計です。

### 比較で揃えること

[勾配法の比較](#/compare/gradient-quadratic)では、同じ初期点・勾配予算・停止条件で比較します。
機械学習ではさらに、

- データの順序 / ミニバッチ
- 乱数種
- 学習率の予定
- 重み減衰
- 勾配のクリッピング
- エポックではなく更新回数

を揃えます。

### 蓄積した速度が発散するとき

[Momentumの失敗時の計算履歴](#/theater/learning/SCENARIO_MOMENTUM_QUADRATIC_DIVERGENCE)では、高い学習率と固定モーメンタムで目的と終了状態を追えます。
[勾配降下法・Adamとの感度比較](#/compare/COMPARE_GRADIENT_DIVERGENCE)は、同じ目的・初期点・40回の取得手段評価予算を使います。

各手法には発散を説明する固定設定を使っています。
良いパラメータを探索する比較でも、手法の一般性能順位でもありません。

::: warning
Momentumは局所探索の軌跡を改善しますが、非凸問題の大域最適性を証明しません。初期値と乱数種による結果差を残します。
:::

## 次に読む

- [関連する手法の記事](#/learn/method.gradient-descent)：一手の意味と選び分けを比べます。

- [この手法を使う問題の定式化](#/formulations/PA040)：決定変数と目的を確認します。
