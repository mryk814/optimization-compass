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
last_reviewed: 2026-09-30
---

全dataではなく、一様にsampleしたmini-batchの勾配でparameterを更新します。各stepはfull-data勾配の不偏推定ですが、samplingによるvarianceを持つ一次法です。

## 30秒でつかむ

全校生徒の平均身長を知りたいとき、全員を測る代わりに、毎回数人だけを測って平均を見積もるとします。
一回の見積もりは外れますが、多数回繰り返せば、全員を測った結果に近づきます。
SGDは、この考えで勾配を見積もります。全データの勾配を毎回計算する代わりに、ミニバッチ（mini-batch）の勾配で、安価な更新を多数回行います。

- **見るもの**: ミニバッチの勾配、学習用の損失（train loss）、検証用の損失（validation loss）
- **動かすもの**: パラメータ、ミニバッチの選び方、学習率（learning rate）、バッチの大きさ
- **前進の判断**: 検証指標が改善し、複数のseedで結果が安定すること

各更新には抽出のばらつき（sampling noise）が入ります。一回の更新の良し悪しと、学習全体の傾向は、分けて読みます。

## 一手の意味

全データを使う勾配降下法は、全 $N$ 点の勾配の平均を、一歩ごとに計算します。

$$
\nabla f(x_k) = \frac{1}{N}\sum_{i=1}^{N} \nabla f_i(x_k)
$$

SGDは、データから一様に抽出したミニバッチ $B_k$（$|B_k|=b \ll N$）だけで、勾配を見積もります。

$$
g_k = \frac{1}{b}\sum_{i \in B_k} \nabla f_i(x_k)
$$

この $g_k$ を使って、$x_{k+1} = x_k - \eta_k g_k$ と更新します。$\eta_k$ は学習率です。
この式は「一部のデータで見積もった下り坂の向きへ、学習率の分だけ進む」と読みます。

抽出が一様なら、$g_k$ は $\nabla f(x_k)$ の不偏推定です。
つまり、平均すると全データの勾配に一致します。ただし分散を持つので、各更新の向きにはnoiseが乗ります。
一歩で読むデータ数は、全データの $N$ 個から $b$ 個へ減ります。

### 学習率とバッチの大きさが決めるもの

学習率 $\eta_k$ とバッチの大きさ $b$ は、更新の向きの分散と、一歩のcostを変えます。
$\eta_k$ を大きくすると、速く進む場合があります。勾配のnoiseによる振動や発散も強くなります。
小さくすると、更新は安定しやすい一方、同じエポック（epoch）数での進みが遅くなります。

学習率のスケジュール（learning rate schedule）は、反復の数や検証指標に応じて $\eta_k$ を変えます。
バッチを大きくすると、勾配の推定の分散は下がります。一歩で読むデータ数は増えます。

## 小さな例

6点のデータ $(x_i,y_i)$ に、直線 $y=wx$ を当てはめます。決めるのは傾き $w$ だけです。
データは $y=2x$ に小さな乱数を足した形です。

| 点 $i$ | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---:|---:|---:|---:|---:|---:|
| $x_i$ | 1 | 2 | 3 | 4 | 5 | 6 |
| $y_i$ | 2.1 | 3.9 | 6.6 | 8.1 | 9.5 | 12.4 |

損失は $L(w)=\tfrac{1}{2N}\sum_i(wx_i-y_i)^2$ です。全データで最小にする傾きは $w^*\approx 2.022$ で、そのときの損失は約 $0.063$ です。
$w=0$ から始め、学習率は $0.02$、バッチの大きさは2とします。エポックごとに点を並べ替え、2点ずつ取ります。並べ替えの乱数の seed は 0 に固定しました。

各点の勾配は $(wx_i-y_i)\,x_i$ で、ミニバッチ勾配はそのミニバッチの2点の平均です。

| 更新 | ミニバッチ | 更新前の $w$ | ミニバッチ勾配 | 全データの勾配 | 更新後の $w$ | 更新後の損失 $L(w)$ |
|---:|---|---:|---:|---:|---:|---:|
| 1 | 点4と点3 | 0 | $-26.10$ | $-30.67$ | 0.522 | 17.125 |
| 2 | 点6と点5 | 0.522 | $-45.03$ | $-22.75$ | 1.423 | 2.788 |
| 3 | 点1と点2 | 1.423 | $-1.39$ | $-9.09$ | 1.450 | 2.540 |

初期の損失は $31.07$ でした。

更新1では、ミニバッチ勾配は全データの勾配に近く、向きも同じです。
更新2では、ミニバッチが $x$ の大きい点5と点6でした。勾配が全データの約2倍に出て、$w$ が大きく進みます。
更新3では、$x$ の小さい点1と点2で、勾配がほとんど出ません。$w$ はほぼ動きません。

ミニバッチ勾配は、毎回の更新で全データの勾配からずれています。
それでも、$w=0$ で2点のミニバッチ15通りの勾配を平均すると、ちょうど全データの勾配 $-30.67$ に一致します。これが不偏推定の意味です。
6回の更新（2エポック）の後で、$w=1.863$、損失は $0.255$ になります。最適な傾き $2.022$ に近づいています。
この数値は seed 固定の一例で、別の seed では、ミニバッチの並びも途中の値も変わります。

### 図で見る

もう少し大きな例です。32点・2パラメータの線形回帰を、8エポック実行しています。

橙のミニバッチ損失は大きく揺れます。青緑の全データ損失も、更新によっては上がります。

![32 sample、2 parameterの固定線形回帰をbatch size 4、learning rate 0.3で8 epoch実行したSGD結果。上段ではparameter pathがfull-data lossの等高線を小刻みに横切る。下段では橙のmini-batch lossが大きく揺れ、青緑のfull-data lossにも63回中5回の上昇stepがある一方、run全体では2.241から0.0016へ下がる。](./media/sgd-mini-batch-execution.svg "固定LCG shuffleとpure Python SGDから生成した実行結果です。full-data optimumは診断用の参照であり、更新には渡していません。validation、汎化性能、neural network、framework実装、SGD一般の性能は示しません。")

1回の更新の上下だけでは、run全体の進行を判定できません。
ミニバッチの損失と、全データの学習損失は別です。未使用データの検証指標も、別々に追います。

## 向く条件・避ける条件

向く条件です。

- データ数が巨大、またはデータがメモリに収まらない
- オンライン・ストリーミングで、データが逐次到着する
- 凸な経験リスク最小化（ERM）や、大規模なneural networkのbaseline
- GPUなどで、一歩のcostを抑えられる
- 真の最適性の証明より、実用的な汎化性能を優先する

避ける、または切り替える条件です。

- 小規模で、高精度な凸問題を厳密なgapまで解きたい → 全データを使う[勾配降下法](#/learn/method.gradient-descent)や二次法のほうが診断しやすい場合がある
- 更新が鞍点（saddle point）の付近で長く停滞する → [Momentum SGD](#/learn/momentum-sgd)や別のoptimizerを検討する
- 座標ごとの勾配の尺度が大きく違う → 座標ごとに尺度を調整する[Adam](#/learn/adam)を比べる

定式化の側から見ると、凸な損失の大規模な平均なら[大規模な確率的ERM（PA041）](#/formulations/PA041)、neural networkなら[neural networkの学習（PA040）](#/formulations/PA040)が対応します。

## Python

次の例は、5次元の線形回帰を、ミニバッチSGDで学習します。

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
# [ 0.49136525 -1.33846503 -1.1063983  -0.45277381  1.67811457]
# [ 0.48940762 -1.33654639 -1.11383088 -0.45295171  1.6798241 ] 0.008106219896085993
```

`w` が `true_w` へ近づく過程は、ミニバッチの抽出と学習率に依存します。
実務のoptimizerは、momentumや、パラメータごとの尺度の調整も持ちます。

「小さな例」は、次のコードで再現できます。

```python
import numpy as np

x = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
y = np.array([2.1, 3.9, 6.6, 8.1, 9.5, 12.4])
learning_rate = 0.02
rng = np.random.default_rng(0)
w = 0.0

for epoch in range(2):
    order = rng.permutation(len(x))
    for start in range(0, len(x), 2):
        idx = order[start : start + 2]
        g_batch = np.mean((w * x[idx] - y[idx]) * x[idx])
        g_full = np.mean((w * x - y) * x)
        w_before, w = w, w - learning_rate * g_batch
        loss = 0.5 * np.mean((w * x - y) ** 2)
        print(idx + 1, round(w_before, 3), round(g_batch, 2), round(g_full, 2), round(w, 3), round(loss, 3))
# [4 3] 0.0 -26.1 -30.67 0.522 17.125
# [6 5] 0.522 -45.03 -22.75 1.423 2.788
# [1 2] 1.423 -1.39 -9.09 1.45 2.54
# [5 6] 1.45 -16.71 -8.67 1.785 0.49
# [2 3] 1.785 -2.2 -3.6 1.829 0.346
# [1 4] 1.829 -1.71 -2.93 1.863 0.255
```

利用するversionの挙動は、公式referenceで確認します。[Optax](https://optax.readthedocs.io/en/latest/)、[torch.optim](https://docs.pytorch.org/docs/stable/optim.html)、[Keras optimizers](https://www.tensorflow.org/api_docs/python/tf/keras/optimizers)があります。

## 診断値

SGDの勾配の大きさや学習損失は、ミニバッチのnoiseで、単調には下がりません。
一回の値でなく、傾向と、複数のseedでのばらつきを見ます。

| 診断値 | 見方 | 判断 |
|---|---|---|
| train_loss | 学習用データでの損失 | 下がり続けるなら継続。長期間動かなければ、学習率のスケジュールや初期化を見直す |
| validation_loss | 未使用データでの損失 | 停滞や悪化は、早期終了（early stopping）を検討する材料 |
| gradient_norm | ミニバッチによる推定値 | 大きく暴れるなら、clippingや学習率を確認する |
| learning_rate | 現在の学習率 | 損失の振動や停滞と合わせて読む |
| seed_variance | 複数のseedでの結果のばらつき | 大きければ、単一のrunで手法を判断しない |

同じhyperparameterでも、seedやデータの順序により、最終的なパラメータと検証指標が変わります。
単一のrunだけで手法を判断せず、複数のseedでvarianceを確認します。

## 失敗・切替の兆候

| 症状 | 考えられる原因 | 対処・切替先 |
|---|---|---|
| 損失が増大し続ける（divergence） | 学習率が大きすぎる | 学習率、バッチの大きさ、勾配のclippingを確認する |
| train_lossが長期間改善しない（plateau） | 学習率が合わない、または初期化が悪い | 学習率のスケジュール、バッチの大きさ、初期化を見直す |
| train_lossは下がるがvalidation_lossが悪化する（overfitting） | 学習データに過剰に適合した | 早期終了と正則化を確認する |
| 学習率が大きすぎて発散、または小さすぎて停滞する（bad_learning_rate） | 学習率が問題の尺度に合っていない | 学習率を調整し、同じ予算で比べる |
| 鞍点の付近で、更新が長時間停滞する | 勾配が小さい領域に入った | [Momentum SGD](#/learn/momentum-sgd)や別のoptimizerを検討する |
| 勾配爆発（gradient explosion）や、seed間で検証指標のばらつきが大きい | 勾配の尺度が不安定、またはseedへの依存が強い | clipping、正規化（normalization）、複数seedでの評価を行う |

::: note
これらの兆候が出たときは、まず学習率のスケジュールとバッチの大きさを見直します。単純な反復回数の増加は、解決策にならないことが多いです。
:::

## 次に読む

- [大規模な確率的ERM（PA041）](#/formulations/PA041)：凸な損失の巨大な平均を、一部のデータで近似しながら最小にする型
- [neural networkの学習（PA040）](#/formulations/PA040)：非凸な損失を、確率的勾配で最小にする型
- [Momentum SGD](#/learn/momentum-sgd)と[Adam](#/learn/adam)：velocityの蓄積と、座標ごとの尺度の調整
- [確率勾配・機械学習optimizerの選び分け](#/learn/family.stochastic-ml)：ミニバッチ系optimizerを条件から比べる
