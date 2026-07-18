---
content_id: sgd
kind: method
method_id: M_SGD
title_ja: 確率的勾配降下法
title_en: Stochastic Gradient Descent
summary: 全dataではなくmini-batchから計算した勾配を真の勾配の不偏推定として使い、parameterを反復更新する一次法です。
source_ids: [S047, S048, S049]
prerequisites: [method.gradient-descent]
related_ids: [momentum-sgd, adam, family.stochastic-ml]
status: published
last_reviewed: 2026-07-18
---

全dataではなくmini-batchから計算した勾配を真の勾配の不偏推定として使い、parameterを反復更新する一次法です。

## 30秒でつかむ

SGDは、全dataの勾配を毎回計算する代わりに、mini-batchの勾配で安価な更新を多数回行います。
その分、各更新にはsampling noiseが入り、1 stepの改善と学習全体の傾向を分けて読む必要があります。

- 見ているもの: train loss、validation loss、gradient estimate、seed間のばらつき
- 動かしているもの: parameter、mini-batch、learning rate、batch size
- 前進の判断: validation指標が改善し、複数seedで結果が安定すること
- 恐れていること: divergence、overfitting、gradient noise、seed依存

## 何を不偏推定しているか

full-batch勾配降下法は、全$N$点の勾配平均

$$
\nabla f(x_k) = \frac{1}{N}\sum_{i=1}^{N} \nabla f_i(x_k)
$$

を1 stepごとに計算します。SGDはdatasetから一様にsamplingしたmini-batch $B_k$（$|B_k|=b \ll N$）だけで

$$
g_k = \frac{1}{b}\sum_{i \in B_k} \nabla f_i(x_k)
$$

を計算し、$x_{k+1} = x_k - \eta_k g_k$ で更新します。samplingが一様なら $g_k$ は $\nabla f(x_k)$ の不偏推定ですが、分散を持ちます。1 stepあたりのcostは$b$に比例して下がる一方、各stepの方向にnoiseが乗ります。

## learning rateとbatch sizeが決めるもの

learning rate $\eta_k$ とbatch size $b$ は、更新方向のvarianceと1 stepの安さのtrade-offを操作するhyperparameterです。$\eta_k$ を大きくすると収束は速くなり得ますが、勾配のnoiseがそのまま更新に乗って発散しやすくなります。逆に小さいと安定しますが、epoch数に対する進みが遅くなります。多くの実装ではlearning rate scheduleとして反復や検証指標に応じて$\eta_k$を減衰させ、batch sizeを大きくすると1 stepのvarianceは下がるものの1 stepあたりのcostが増えます。

## 収束の見方がdeterministicな最適化と違う点

deterministicな最適化はgradient normの単調な減少で進捗を確認できますが、SGDの1 stepはmini-batchのnoiseを含むため、gradient normやtrain lossは単調に下がりません。実務ではtrain lossとvalidation lossを分けて追い、validation lossの停滞や悪化をearly stoppingの判定に使います。また同じhyperparameterでもseedやdata orderの違いで最終的なparameterやvalidation指標が変わるため、単一の実行結果だけで手法を判断せず、複数seedでのvarianceを確認します。

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

`w`が`true_w`へ近づくかは、mini-batchのsamplingとlearning rateに依存します。実務のoptimizerが持つmomentumやper-coordinate scalingなどの機能は、利用framework（[Optax](https://optax.readthedocs.io/en/latest/)、[torch.optim](https://docs.pytorch.org/docs/stable/optim.html)、[Keras optimizers](https://www.tensorflow.org/api_docs/python/tf/keras/optimizers)）の公式referenceで利用versionに対応する説明を確認します。

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

velocityを蓄積して振動を抑える考え方は[Momentum SGD](#/learn/momentum-sgd)、勾配の1次・2次momentを使うadaptive scalingは[Adam](#/learn/adam)、mini-batch系optimizer全体の選び分けは[確率勾配・機械学習optimizerの選び分け](#/learn/family.stochastic-ml)で確認できます。
