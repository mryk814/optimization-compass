---
content_id: sgd
kind: method
method_id: M_SGD
title_ja: 確率的勾配降下法
title_en: Stochastic Gradient Descent
summary: 全dataではなく、一様にsampleしたmini-batchの勾配でparameterを更新します。各stepはfull-data勾配の不偏推定ですが、samplingによるvarianceを持つ一次法です。
source_ids: [S047, S048, S049]
prerequisites: [method.gradient-descent]
related_ids: [momentum-sgd, adam, family.stochastic-ml]
status: published
last_reviewed: 2026-07-26
---

全dataではなく、一様にsampleしたmini-batchの勾配でparameterを更新します。各stepはfull-data勾配の不偏推定ですが、samplingによるvarianceを持つ一次法です。

## 30秒でつかむ

SGDは、全dataの勾配を毎回計算する代わりに、mini-batchの勾配で安価な更新を多数回行います。
その分、各更新にはsampling noiseが入り、1 stepの改善と学習全体の傾向を分けて読む必要があります。

- 見ているもの: train loss、validation loss、gradient estimate、seed間のばらつき
- 動かしているもの: parameter、mini-batch、learning rate、batch size
- 前進の判断: validation指標が改善し、複数seedで結果が安定すること
- 恐れていること: divergence、overfitting、gradient noise、seed依存

同じrunでも、mini-batchだけを見たlossとfull-data lossでは線の形が変わります。
次の固定線形回帰では、橙のstepが揺れながら青緑のfull-data optimumへ近づきます。

![32 sample、2 parameterの固定線形回帰をbatch size 4、learning rate 0.3で8 epoch実行したSGD結果。上段ではparameter pathがfull-data lossの等高線を小刻みに横切る。下段では橙のmini-batch lossが大きく揺れ、青緑のfull-data lossにも63回中5回の上昇stepがある一方、run全体では2.241から0.0016へ下がる。](./media/sgd-mini-batch-execution.svg "固定LCG shuffleとpure Python SGDから生成した実行結果です。full-data optimumは診断用の参照であり、更新には渡していません。validation、汎化性能、neural network、framework実装、SGD一般の性能は示しません。")

1 stepの上下だけでは、run全体の進行を判定できません。
mini-batch loss、full-dataのtrain loss、未使用dataのvalidation指標は別々に追います。

## 何を不偏推定しているか

full-batch勾配降下法は、全$N$点の勾配平均

$$
\nabla f(x_k) = \frac{1}{N}\sum_{i=1}^{N} \nabla f_i(x_k)
$$

を1 stepごとに計算します。SGDはdatasetから一様にsamplingしたmini-batch $B_k$（$|B_k|=b \ll N$）だけで

$$
g_k = \frac{1}{b}\sum_{i \in B_k} \nabla f_i(x_k)
$$

を計算し、$x_{k+1} = x_k - \eta_k g_k$ で更新します。
samplingが一様なら、$g_k$は$\nabla f(x_k)$の不偏推定です。
ただし分散を持つため、各stepの方向にはnoiseが乗ります。
1 stepで読むsample数は、full-batchの$N$から$b$へ減ります。

## learning rateとbatch sizeが決めるもの

learning rate $\eta_k$ とbatch size $b$ は、更新方向のvarianceと1 stepのcostを変えます。
$\eta_k$を大きくすると速く進む場合がありますが、勾配noiseによる振動や発散も強くなります。
小さくすると更新は安定しやすい一方、同じepoch数での進みが遅くなります。

learning rate scheduleは、反復数やvalidation指標に応じて$\eta_k$を変えます。
batch sizeを大きくするとgradient estimateのvarianceは下がりますが、1 stepで読むsample数が増えます。

## 収束の見方がdeterministicな最適化と違う点

SGDのgradient normやtrain lossは、mini-batch noiseにより単調には下がりません。
実務ではtrain lossとvalidation lossを分けて追います。
validation lossの停滞や悪化は、early stoppingを検討する材料です。

同じhyperparameterでも、seedやdata orderにより最終parameterとvalidation指標が変わります。
単一runだけで手法を判断せず、複数seedでvarianceを確認します。

## 向いている条件

- 巨大なsample数またはdatasetがmemoryに収まらない
- online / streamingでdataが逐次到着する
- convex ERM（経験risk最小化）や大規模neural networkのbaseline
- GPU等で1 stepのcostを抑えられる
- 真の最適性証明より実用的な汎化性能を優先する

小規模で高精度な凸問題を厳密なgapまで解きたい場合は、full-batchの[勾配降下法](#/learn/method.gradient-descent)や二次法のほうが診断しやすい場合があります。

## Python

```python
import numpy as np


def make_dataset(
    rng: np.random.Generator, n_samples: int, n_features: int
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    x = rng.normal(size=(n_samples, n_features))
    true_w = rng.normal(size=n_features)
    noise = 0.1 * rng.normal(size=n_samples)
    y = x @ true_w + noise
    return x, y, true_w


def sgd_step(
    x_batch: np.ndarray, y_batch: np.ndarray, w: np.ndarray, learning_rate: float
) -> np.ndarray:
    residual = x_batch @ w - y_batch
    grad = x_batch.T @ residual / x_batch.shape[0]
    return w - learning_rate * grad


rng = np.random.default_rng(0)
x, y, true_w = make_dataset(rng, n_samples=2_000, n_features=5)
w = np.zeros(x.shape[1])
learning_rate = 0.05
batch_size = 32

for epoch in range(20):
    order = rng.permutation(x.shape[0])
    for start in range(0, x.shape[0], batch_size):
        idx = order[start : start + batch_size]
        w = sgd_step(x[idx], y[idx], w, learning_rate)

print(w, true_w, np.linalg.norm(w - true_w))
```

`w`が`true_w`へ近づく過程は、mini-batchのsamplingとlearning rateに依存します。
実務のoptimizerは、momentumやparameterごとのscalingも持ちます。

利用versionの挙動は[Optax](https://optax.readthedocs.io/en/latest/)、[torch.optim](https://docs.pytorch.org/docs/stable/optim.html)、[Keras optimizers](https://www.tensorflow.org/api_docs/python/tf/keras/optimizers)の公式referenceで確認します。

## 最初に見る診断値

- train_loss
- validation_loss
- gradient_norm（mini-batchによる推定値）
- learning_rate
- seed_variance（複数seedでの結果のばらつき）

## 失敗・切替の兆候

- divergence（lossが増大し続ける） → learning rate、batch size、gradient clippingを確認する
- plateau（train_lossが長期間改善しない） → learning-rate schedule、batch size、初期化を見直す
- overfitting（train_lossは下がるがvalidation_lossが悪化する） → early stoppingとregularizationを確認する
- bad_learning_rate（大きすぎて発散、または小さすぎて停滞する） → learning rateを調整し、同じbudgetで比較する
- saddle点付近で更新が長時間停滞する → Momentum SGDや別のoptimizerを検討する
- gradient explosionやseed間でのvalidation指標のばらつきが大きい → clipping、normalization、複数seed評価を行う

::: note
これらの兆候が出た場合、まずlearning rate scheduleとbatch sizeを見直します。単純な反復回数の増加は解決策にならないことが多いです。
:::

velocityを蓄積する更新は[Momentum SGD](#/learn/momentum-sgd)で確認できます。
勾配の1次・2次momentを使うadaptive scalingは[Adam](#/learn/adam)です。
[確率勾配・機械学習optimizerの選び分け](#/learn/family.stochastic-ml)では、mini-batch系optimizerを条件から比較できます。
