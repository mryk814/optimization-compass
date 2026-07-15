---
content_id: adam
kind: method
method_id: M_ADAM
title_ja: Adam
title_en: Adam
summary: 勾配の一次momentと二次momentを座標ごとに推定し、bias correction付きの適応stepでparameterを更新する確率的一次法です。
source_ids: [S047, S048, S049, S070]
prerequisites: [method.gradient-descent]
related_ids: [momentum-sgd, method.gradient-descent, bfgs]
comparison_ids: [COMPARE_GRADIENT_FAMILY]
aliases: [/learn/adam]
comparison_aliases: [COMPARE_GRADIENT_FAMILY|/compare/gradient-quadratic]
status: published
last_reviewed: 2026-07-15
---

勾配の一次momentと二次momentを座標ごとに推定し、bias correction付きの適応stepでparameterを更新する確率的一次法です。

## 更新状態

時刻 $t$ のgradientを $g_t$ とすると、Adamは概ね

$$
m_t=\beta_1m_{t-1}+(1-\beta_1)g_t
$$

$$
v_t=\beta_2v_{t-1}+(1-\beta_2)g_t^2
$$

を更新します。初期値0によるbiasを補正した $\hat m_t,\hat v_t$ を使い、

$$
x_{t+1}=x_t-\eta\frac{\hat m_t}{\sqrt{\hat v_t}+\epsilon}
$$

と進みます。

$m_t$は方向の平滑化、$v_t$は座標ごとのgradient scaleを表します。

## 「自動でlearning rateを決める」わけではない

Adamは座標ごとのstepを正規化しますが、global learning rate $\eta$、schedule、$\beta_1$、$\beta_2$、$\epsilon$は依然として重要です。さらに、

- coupled L2 penalty
- decoupled weight decay
- AMSGrad
- clipping
- mixed precision

などのvariantで挙動が変わります。

## Python

```python
import numpy as np


def gradient(x: np.ndarray) -> np.ndarray:
    return np.array([2.0 * (x[0] - 1.0), 80.0 * (x[1] + 2.0)])


x = np.array([4.0, 3.0])
first = np.zeros_like(x)
second = np.zeros_like(x)
learning_rate = 0.08
beta1 = 0.9
beta2 = 0.999
epsilon = 1e-8

for step in range(1, 3_001):
    g = gradient(x)
    first = beta1 * first + (1.0 - beta1) * g
    second = beta2 * second + (1.0 - beta2) * (g * g)
    first_hat = first / (1.0 - beta1**step)
    second_hat = second / (1.0 - beta2**step)
    update = learning_rate * first_hat / (np.sqrt(second_hat) + epsilon)
    x = x - update
    if np.linalg.norm(g) < 1e-8 and np.linalg.norm(update) < 1e-8:
        break

print(x, np.linalg.norm(gradient(x)))
```

これはdeterministic quadraticの教育例です。mini-batch noise、weight decay、scheduleを含むframework実装とは条件が異なります。

## 見るべき診断値

- objective / validation metric
- gradient norm
- update norm
- effective step $\eta/(\sqrt{\hat v} + \epsilon)$
- first / second moment norm
- parameter norm
- gradient clipping率
- learning-rate schedule
- seed間のばらつき

training lossだけ下がりvalidationが悪化する場合、optimizerの停止条件とmodel generalizationを分けて考えます。

## 向いている条件

- stochastic gradientを使う大規模学習
- 座標ごとのgradient scaleが違う
- sparseまたはnonstationaryなgradient
- 初期の実用的なbaselineを早く作りたい
- exactな局所最適化よりtraining budgetが支配的

## Momentum SGDとの比較

- Adamは座標ごとの二次momentでscaleを変える
- Momentumは一つのvelocityを蓄積する
- Adamの初期改善が速くても、最終generalizationが常に優れるとは限らない
- weight decay実装の違いを揃える

同じepoch数ではなく、batch order、update count、schedule、regularization、seedを揃えます。

## 失敗・切替の兆候

- learning rateが大きくlossが不安定
- second momentが大きくなりstepが極小化
- epsilonが低精度計算で支配的
- weight decayをL2 penaltyと混同
- validation metricが停滞しtraining lossだけ改善
- gradient clippingが常時発動
- optimizer stateをrestoreせずresume

::: warning
Adamの適応stepは、最適性certificateや大域保証ではありません。終了時のstatusはbudget、gradient、validation、再現性を含めて報告します。
:::
