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
last_reviewed: 2026-07-24
---

現在の勾配だけでなく過去の更新を速度として蓄積し、同じ方向の移動を強めて谷を横切る振動を抑える一次法です。

## 30秒でつかむ

Momentumは、毎回の勾配をそのまま使わず、過去の更新を速度として残します。
細長い谷で急な方向へ往復する成分を弱め、緩い方向へ進む成分を積み上げる設計です。

- 見ているもの: objective、gradient、velocity、update
- 動かしているもの: parameter、速度状態、learning rate
- 前進の判断: best-so-farとgradient normが安定し、velocityが過大にならないこと
- 恐れていること: overshoot、発散、古いvelocity、mini-batch noise

## 何を状態として持つか

代表的なheavy-ball型では、速度 $v_k$ とparameter $x_k$ を

$$
v_{k+1}=\beta v_k+\nabla f(x_k)
$$

$$
x_{k+1}=x_k-\eta v_{k+1}
$$

で更新します。実装によって勾配へ $(1-\beta)$ を掛けるか、Nesterov look-aheadを使うか、dampeningを入れるかが異なります。

- $\eta$: learning rate
- $\beta$: momentum coefficient
- $v_k$: 過去の勾配を含む更新状態

## なぜzig-zagを抑えられるか

細長い谷では、急な方向の勾配符号が反復ごとに入れ替わり、緩い方向の符号は比較的一貫します。Momentumは符号が交互に変わる成分を相殺し、同じ方向の成分を蓄積します。

一方で、蓄積された速度はminimumを通り過ぎても残るため、learning rateや$\beta$が大きすぎるとovershootや発散を起こします。

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

この更新式は教育用です。frameworkごとのMomentum / Nesterov定義、weight decay、gradient averagingを公式documentationで確認します。

## 最初に見る診断値

- objectiveとbest-so-far
- gradient norm
- velocity norm
- update norm
- learning rate
- gradientとvelocityの角度
- oscillation / overshoot
- mini-batch間のgradient variance
- evaluationまたはtraining-step budget

velocity normが大きいままobjectiveが悪化する場合、単に反復を増やしません。
learning rate／$\beta$／scalingを見直します。

## 向いている条件

- smoothな大規模problem
- stochastic gradientを繰り返し利用する
- gradient descentが細長い谷で振動する
- per-coordinate adaptive scalingより単純な状態を使いたい
- training loopとscheduleを管理できる

## 比較で揃えること

[Gradient family comparison](#/compare/gradient-quadratic)では、同じ初期点・gradient budget・停止条件で比較します。
machine learningではさらに、

- data order / mini-batch
- seed
- learning-rate schedule
- weight decay
- gradient clipping
- epochではなくupdate count

を揃えます。

## 失敗・切替の兆候

- minimum周辺で振動が減らない → learning rate、$\beta$、scalingを見直す
- velocityが蓄積して発散 → learning rateまたは$\beta$を下げ、gradient clippingを確認する
- learning-rate decay後も古いvelocityが支配 → velocityの扱いとscheduleを確認する
- parameter scaleが極端に違う → scalingまたはadaptive methodを比較する
- sparse / nonstationary gradientで状態が古くなる → momentum係数と更新scheduleを見直す
- Adam等との比較でscheduleやregularizationが異なる → 同じbudget、schedule、regularizationで比較する

## 蓄積したvelocityが発散するとき

[Momentumのfailure Trace](#/theater/learning/SCENARIO_MOMENTUM_QUADRATIC_DIVERGENCE)では、high learning rateと固定momentumでobjectiveと終了statusを追えます。
[勾配降下法・Adamとの感度Compare](#/compare/COMPARE_GRADIENT_DIVERGENCE)は、同じ目的・初期点・40回のoracle evaluation budgetを使います。

各手法には発散を説明する固定presetを使っています。
良いparameterを探索する比較でも、手法の一般性能rankingでもありません。

::: warning
Momentumは局所探索の軌跡を改善しますが、非凸問題の大域最適性を証明しません。初期値とseedによる結果差を残します。
:::
