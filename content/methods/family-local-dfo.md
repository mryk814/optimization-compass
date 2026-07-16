---
content_id: family.local-dfo
kind: method
method_id: MF_DFO_LOCAL
title_ja: 局所Derivative-free最適化の選び分け
title_en: Choosing a Local Derivative-Free Optimizer
summary: 勾配を使えない低〜中次元の連続問題で、Nelder–Mead、Powell、Pattern Search、COBYLA、MADSを選び分ける入口です。
source_ids: [S002, S018, S031, S060, S063]
related_ids: [method.nelder-mead, powell, pattern-search, cobyla, mads]
status: published
last_reviewed: 2026-07-16
---

勾配を使えない低〜中次元の連続問題で、Nelder–Mead、Powell、Pattern Search、COBYLA、MADSを選び分ける入口です。

## 30秒でつかむ

このfamilyの気持ちは、**傾きが分からなくても、少し違う点を実際に試し、良かった方向・形・meshを次の探索へ引き継ぐこと**です。

- 見ているもの: 関数値、候補点の比較、探索geometry、必要なら制約違反
- 動かすもの: 単体、方向集合、poll点、mesh、局所model
- 前進の判断: 評価値の改善と探索半径・meshの縮小
- 主な弱点: 評価回数、高次元、noise floor、弱い停止診断

「微分不要」は「情報不要」ではありません。bounds、変数scale、評価budget、失敗した評価の扱いが結果を大きく変えます。

## まず確認すること

| 確認項目 | 選択への影響 |
|---|---|
| 次元 | 次元が増えるほど候補評価が重くなる |
| 1評価の費用 | 数十〜数千回の評価が許されるか |
| bounds・一般制約 | 無制約、単純bounds、black-box制約のどれか |
| noise | 小さな改善を信頼できるか、再評価が必要か |
| 不連続・失敗 | simulation failureをどの値として扱うか |
| 求める保証 | 良い局所候補か、stationarityの理論が必要か |

評価が非常に高価で回数が数十回に限られるなら、局所DFOよりBayesian Optimizationやsurrogate法を先に検討します。

## 条件付きの選び分け

| 役割 | 手法 | 優先しやすい条件 | 切り替えを考える条件 |
|---|---|---|---|
| 最も素朴な低次元候補 | [Nelder–Mead](#/learn/method.nelder-mead) | 非常に低次元、無制約または単純bounds、評価が比較的安価 | simplex退化、shrink反復、高次元 |
| 方向を再利用 | [Powell法](#/learn/powell) | 座標・方向ごとの探索が効く、滑らかだが勾配なし | line searchが不安定、方向集合が問題に合わない |
| 規則的な近傍探索 | [Pattern Search](#/learn/pattern-search) | bounds内で分かりやすいpollを試したい | mesh縮小だけ続き改善しない |
| 微分なしの一般制約 | [COBYLA](#/learn/cobyla) | 低次元、非線形制約を局所線形近似で扱いたい | constraint violationが停滞、scaleが悪い |
| black-box制約と理論 | [MADS](#/learn/mads) | 評価失敗・black-box制約、mesh stationarityを重視 | poll数がbudgetを圧迫、高次元 |
| 同時摂動で高次元へ | [SPSA](#/methods/M_SPSA) | noiseあり、高次元、座標差分が高価 | gain sequenceが不安定、varianceが大きすぎる |

同じ「関数値だけで動く」手法でも、探索状態と制約の扱いは大きく違います。

## うまくいったサインと切替サイン

追うべき値:

- best-so-far objective
- evaluation count
- simplex diameter / mesh size / poll size
- successful stepの割合
- repeated or duplicate points
- constraint violation
- 再評価した点のvariance
- 異なる初期点・初期geometryでの解

切替サイン:

- geometryだけ縮みbestが改善しない → scaling、restart、別familyを検討
- noise floor以下の差を追う → 再評価、robust比較、停止条件を変更
- 高次元でpoll数が支配的 → SPSA、surrogate、構造を使う手法へ
- 一般制約の違反が減らない → COBYLA/MADS、または滑らかならconstrained NLPへ
- 初期点ごとに別basinへ入る → global-search familyへ

## 小さな比較の型

DFO比較ではiterationよりobjective evaluation数が重要です。

```python
experiment = {
    "problem_instance": "same-black-box-instance",
    "bounds": [(-2.0, 2.0), (-1.0, 3.0)],
    "initial_point": [-1.2, 1.0],
    "objective_evaluation_budget": 400,
    "noise_repeats": 1,
    "methods": ["Nelder-Mead", "Powell", "MADS"],
}

assert experiment["objective_evaluation_budget"] >= 1
```

## コラム: 小さくなったことと解けたこと

単体、mesh、探索半径が小さくなるのは、局所探索が細かくなったことを示します。しかし、良いbasinにいることや大域最適性を証明するものではありません。

停止時には、geometryだけでなくbest objective、制約違反、複数start、残りbudgetを併記します。手法固有のstationarity保証がある場合も、その前提と実装の停止判定を区別します。

## 次に読む

評価が高価なら[高価なblack-box探索の選び分け](#/learn/family.expensive-black-box)、複数basinを広く探すなら[大域探索の選び分け](#/learn/family.global-search)へ進みます。