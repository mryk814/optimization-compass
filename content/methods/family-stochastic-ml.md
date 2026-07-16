---
content_id: family.stochastic-ml
kind: method
method_id: MF_STOCHASTIC_ML
title_ja: 確率勾配・機械学習optimizerの選び分け
title_en: Choosing a Stochastic ML Optimizer
summary: mini-batch勾配を使う大規模学習で、SGD、Momentum、Adam、AdamWとfull-batch法を選び分ける入口です。
source_ids: [S047, S048, S049, S070]
related_ids: [method.gradient-descent, momentum-sgd, adam, bfgs]
status: published
last_reviewed: 2026-07-16
---

mini-batch勾配を使う大規模学習で、SGD、Momentum、Adam、AdamWとfull-batch法を選び分ける入口です。

## 30秒でつかむ

このfamilyの気持ちは、**全データで正確な勾配を毎回計算せず、mini-batchから得る揺れる方向を何度も積み重ねて、学習目的を改善すること**です。

- 見ているもの: mini-batch gradient、training loss、validation metric、learning rate
- 動かすもの: parameter、momentum、一次・二次moment、weight decay
- 前進の判断: validation改善、loss低下、gradientやupdateの安定
- 主な弱点: learning-rate依存、seed variance、overfitting、plateau、gradient explosion

optimizerのtraining lossが最も低いことと、未知データで最も良いことは別です。validationと運用metricを停止判断へ含めます。

## まず確認すること

| 確認項目 | 選択への影響 |
|---|---|
| dataset / model規模 | full-batchが可能か、mini-batchが必要か |
| gradient sparsity | 座標ごとのadaptive stepが有効か |
| batch noise | momentumやaveragingで安定化できるか |
| hardware | GPU、distributed、mixed precisionを使うか |
| regularization | weight decay、dropout、data augmentationとの関係 |
| training budget | epoch、step、wall time、energyのどれを制約にするか |
| generalization | training objective以外のvalidation指標があるか |

小規模で高精度な凸問題なら、stochastic optimizerよりL-BFGSや専用solverが適する場合があります。

## 条件付きの選び分け

| 役割 | 手法 | 優先しやすい条件 | 切り替えを考える条件 |
|---|---|---|---|
| 基準となる単純更新 | SGD | tuningに時間を使える、generalizationを重視、十分なtraining budget | 振動が強い、収束が遅すぎる |
| 方向を蓄積 | [Momentum SGD](#/learn/momentum-sgd) | 細長い谷、mini-batch noise、SGDの振動を抑えたい | momentumが大きくovershootする |
| adaptiveな標準候補 | [Adam](#/learn/adam) | sparse/noisy gradient、初期の立ち上がりを速くしたい | validationがSGD系より悪い、stepが不安定 |
| weight decayを分離 | [AdamW](#/methods/M_ADAMW) | weight decayをregularizationとして明示したい | decayとlearning-rate scheduleの調整が曖昧 |
| full-batch曲率利用 | [BFGS](#/learn/bfgs) / L-BFGS | 小〜中規模、deterministic loss、full gradientが安価 | data全体のgradientが重い、online更新が必要 |
| 座標更新 | [Coordinate Descent](#/learn/coordinate-descent) | convex・sparse・座標subproblemが安価 | deep modelの一般trainingには自然でない |

AdamとSGDのどちらが「上」かではなく、初期改善、最終validation、wall time、memory、tuning budgetで判断します。

## うまくいったサインと切替サイン

追うべき値:

- training lossとvalidation loss
- primary business / scientific metric
- learning rateとupdate norm
- gradient normまたはgradient clipping率
- epoch / step / wall time
- seed間のばらつき
- data throughputとhardware utilization
- early stopping時点

切替サイン:

- lossが発散・NaN → learning rate、normalization、mixed precision、gradient clippingを確認
- trainingは改善しvalidationが悪化 → optimizerよりregularizationと停止時点を見直す
- Adamが早くplateau → schedule変更、SGD+momentumへの切替を比較
- SGDの振動が大きい → momentum、batch size、preconditioningを検討
- optimizer stateがmemoryを圧迫 → SGD、低memory法、parameter shardingを検討
- seed差が大きい → 複数runで中央値・分散を報告

## 小さな比較の型

同じepoch数だけでなく、data accessとwall timeも揃えます。

```python
training_contract = {
    "dataset_split_version": "v1",
    "initial_weights_seed": 123,
    "data_order_seeds": [1, 2, 3],
    "batch_size": 128,
    "maximum_epochs": 100,
    "early_stopping_metric": "validation_loss",
    "methods": ["SGD-momentum", "Adam", "AdamW"],
    "reported_metrics": ["validation_loss", "wall_time", "peak_memory"],
}

assert training_contract["maximum_epochs"] > 0
```

## コラム: optimizerとtraining recipe

実際の結果はoptimizer名だけで決まりません。learning-rate schedule、warmup、batch size、normalization、weight decay、gradient clipping、data augmentation、mixed precisionが一つのtraining recipeを作ります。

比較では、optimizerだけ変更したのか、recipe全体を各手法向けに調整したのかを明記します。公平性は「parameterを全部同じにすること」ではなく、調整方針とbudgetを事前に決めることです。

## 次に読む

deterministicな滑らか問題なら[滑らかな局所最適化](#/learn/family.smooth-local)、trial自体が高価なhyperparameter探索なら[高価なblack-box・HPO](#/learn/family.expensive-black-box)へ進みます。