---
content_id: family.smooth-local
kind: method
method_id: MF_SMOOTH_LOCAL
title_ja: 滑らかな局所最適化の選び分け
title_en: Choosing a Smooth Local Optimizer
summary: 勾配や曲率を使える連続問題で、Gradient Descent、BFGS、Newton系を条件に応じて選び分けるための入口です。
source_ids: [S002, S056, S057]
related_ids: [method.gradient-descent, bfgs, lbfgsb, newton-method, trust-region-newton-cg]
status: published
last_reviewed: 2026-07-16
---

勾配や曲率を使える連続問題で、Gradient Descent、BFGS、Newton系を条件に応じて選び分けるための入口です。

## 30秒でつかむ

このfamilyの気持ちは、**現在地の近くで目的関数がどちらへ下がり、どの程度曲がっているかを使って、無駄の少ない一歩を作ること**です。

- 見ているもの: 目的関数値、勾配、必要ならHessianまたはHessian-vector積
- 動かすもの: 現在点と探索方向
- 前進の判断: 目的値の低下、勾配ノルムの低下、局所modelと実際の改善の一致
- 主な弱点: 初期値依存、微分の誤り、変数scale、非凸問題の局所解

「二階法が常に上位」という順位ではありません。1stepの賢さと、memory・線形代数・微分計算の重さを交換しています。

## まず確認すること

| 確認項目 | 選択への影響 |
|---|---|
| 勾配を正確に得られるか | 得られないなら、このfamilyを第一候補にしない |
| 変数数とmemory | dense BFGSやHessianを保持できるか |
| Hessian-vector積 | Newton-CGやtrust-regionを大規模化できるか |
| bounds | L-BFGS-Bやprojected methodが必要か |
| 非凸性 | 局所停留点で十分か、負の曲率を扱いたいか |
| 必要精度 | 粗い改善か、高精度なstationarityか |

勾配を自動微分で得られても、正しいとは限りません。有限差分との方向微分check、単位、batch平均、regularizationを確認します。

## 条件付きの選び分け

| 役割 | 手法 | 優先しやすい条件 | 切り替えを考える条件 |
|---|---|---|---|
| 分かりやすい基準点 | [Gradient Descent](#/learn/method.gradient-descent) | 更新則を理解したい、巨大問題で単純stepが必要 | learning rate調整だけで進まず評価回数が増える |
| 中小規模の標準候補 | [BFGS](#/learn/bfgs) | 滑らか、勾配が信頼できる、dense近似を保持可能 | memoryが支配的、line search failureが続く |
| 高次元・bounds | [L-BFGS-B](#/learn/lbfgsb) | 変数が多い、上下限がある | 一般非線形制約が本質、曲率近似が不安定 |
| 二階情報を直接利用 | [Newton法](#/learn/newton-method) | Hessianが得られ、良い近傍で高精度化したい | Hessianが不定・特異、線形系が重い |
| 二階法を安全に大規模化 | [Trust-region Newton-CG](#/learn/trust-region-newton-cg) | HVPがあり、modelを信用する範囲を制御したい | trust radiusが縮み続ける、HVPが不正 |
| 低memory方向更新 | [Nonlinear CG](#/methods/M_NLCG) | 大規模無制約で勾配はあるがmemoryを抑えたい | restartが頻発し、方向の質が保てない |

これは一般性能rankingではありません。同じproblem instance、初期点、gradient oracle、tolerance、budgetで比較します。

## うまくいったサインと切替サイン

うまく進んでいるときは、目的値だけでなく次も改善します。

- 勾配ノルムが一貫して小さくなる
- line searchの試行回数が極端に増えない
- step normが停止許容値へ近づく
- trust-regionではactual / predicted reduction比が安定する
- 異なる初期値でも同程度の解へ到達する

切替サイン:

- gradient checkが一致しない → 微分・単位・データ処理を直す
- line search failureが続く → scaling、trust-region、別のglobalizationを検討
- memoryが支配的 → BFGSからL-BFGSやNLCGへ
- 局所解が初期値ごとに変わる → multi-startやglobal-search familyへ
- bounds以外の制約違反が残る → constrained NLP familyへ

## 小さな比較の型

実装比較ではiteration数だけを揃えません。少なくとも評価回数と停止条件を記録します。

```python
experiment = {
    "problem_instance": "same-smooth-objective",
    "initial_point": [1.0, -1.0],
    "gradient_source": "automatic-differentiation-checked",
    "objective_evaluation_budget": 500,
    "gradient_evaluation_budget": 500,
    "gradient_tolerance": 1e-6,
    "methods": ["BFGS", "L-BFGS-B", "trust-ncg"],
}

assert experiment["objective_evaluation_budget"] > 0
```

## コラム: 速い収束とは何か

Newton系の「速い」は、通常は**解の十分近くでの局所収束率**を指します。初期点が遠い、Hessianが不定、line searchやtrust-regionが候補stepを拒否する状況では、その速さはそのまま現れません。

また、非凸問題で勾配が小さいことは大域最適性の証明ではありません。局所最小、鞍点、平坦領域を区別するには、曲率、複数初期値、problem固有の構造を追加で確認します。

## 次に読む

一般制約がある場合は[制約付きNLPの選び分け](#/learn/family.constrained-nlp)、勾配が信用できない場合は[局所Derivative-freeの選び分け](#/learn/family.local-dfo)へ進みます。