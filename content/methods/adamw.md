---
content_id: adamw
kind: method
method_id: M_ADAMW
title_ja: AdamW
title_en: AdamW
summary: Adamの適応的な更新（adaptive update）と重み減衰（weight decay）を分離し、勾配（gradient）による更新とパラメータを縮める正則化（regularization）を別の操作として扱う学習optimizerです。
source_ids: [S047, S048, S049]
related_ids: [family.stochastic-ml, adam, momentum-sgd]
status: published
last_reviewed: 2026-07-16
---

Adamの適応的な更新（adaptive update）と重み減衰（weight decay）を分離し、勾配（gradient）による更新とパラメータを縮める正則化（regularization）を別の操作として扱う学習optimizerです。

## 30秒でつかむ

この手法の気持ちは、勾配に応じた一歩とパラメータを縮める操作を分け、学習の進み方と正則化を別々に整えることです。

座標ごとの適応的なstepを使いながら、パラメータを小さく保つ操作を勾配へ混ぜ込まず、正則化として独立に調整します。

- 見ているもの: 確率勾配（stochastic gradient）、一次モーメントと二次モーメント、learning rate
- 動かしているもの: parameter、moment state、weight decay
- 前進の判断: trainingだけでなくvalidation metricの改善
- 恐れていること: learning-rateとdecayの混同、過学習、optimizer state memory

AdamWは「Adamより常に良い」という順位ではありません。training recipeの中でregularizationをどう定義するかを明確にする選択です。

## 仕組み

Adamのmoment推定からadaptiveなgradient stepを作り、そのstepとは別にparameterを縮めます。概念的には次の二つを分けます。

1. gradient情報による更新
2. weight decayによるparameter縮小

実際の式、bias correction、epsilon、parameter groupはframework実装で確認します。特に「L2 penaltyをlossへ加える」ことと「decoupled weight decay」は同じ操作ではありません。

## まず確認すること

| 項目 | 確認内容 |
|---|---|
| objective | mini-batch gradientを利用する学習問題か |
| regularization | weight decayをparameter縮小として扱いたいか |
| parameter groups | biasやnormalization parameterへdecayを適用するか |
| schedule | learning rateとdecayをどう時間変化させるか |
| memory | 一次・二次momentを保持できるか |
| evaluation | validation metricとearly stoppingがあるか |

小規模なdeterministic凸問題や高精度解が必要な問題では、L-BFGSや専用solverも比較します。

## 向く条件・避ける条件

- **向く**: neural networkなど高次元stochastic training
- **向く**: sparseまたは座標ごとにscaleの違うgradient
- **向く**: Adam系を使いつつweight decayを明示したい
- **向く**: frameworkのparameter groupで適用範囲を管理できる
- **避ける**: optimizer state memoryが厳しい
- **避ける**: validationなしでtraining lossだけを最小化する
- **避ける**: decay対象を理解せず全parameterへ同じ設定を適用
- **切り替える**: 厳密な最適性gapや大域certificateが必要


## Python

次の例は、`torch.optim.AdamW`を使って一回の更新を行う最小例です。

```python
import torch

model = torch.nn.Linear(4, 1)
optimizer = torch.optim.AdamW(
    model.parameters(),
    lr=1e-3,
    weight_decay=1e-2,
)

inputs = torch.randn(16, 4)
targets = torch.randn(16, 1)

optimizer.zero_grad()
predictions = model(inputs)
loss = torch.nn.functional.mse_loss(predictions, targets)
loss.backward()
optimizer.step()

print(float(loss.detach()))
```

実務ではseed、data split、schedule、parameter group、framework versionを記録します。

## 診断値

- training / validation loss
- primary validation metric
- learning rateとweight decay
- update normとparameter norm
- gradient clipping率
- seed間のばらつき
- peak memoryとthroughput

training lossだけ下がりvalidationが悪化する場合、optimizerの停止条件とmodel generalizationを分けて考えます。

## うまくいったサインと切替サイン

- trainingは改善しvalidationが悪化 → decay、data、early stoppingを見直す
- parameter normが急減 → decayが強すぎる可能性
- optimizer stateがmemoryを圧迫 → SGD系やstate shardingを検討
- 初期改善後にplateau → schedule、SGD+momentum、L-BFGSを比較
- NaNや発散 → learning rate、mixed precision、gradient scalingを確認

## コラム: optimizerだけを比較しない

AdamWの結果はlearning-rate schedule、warmup、batch size、normalization、data augmentation、gradient clippingと組み合わさって決まります。optimizer名だけを変えた比較と、各optimizer向けにrecipeを調整した比較を区別します。

## 次に読む

[確率勾配・機械学習optimizerの選び分け](#/learn/family.stochastic-ml)でSGD、Momentum、Adamとの条件付き優先度を確認してください。
