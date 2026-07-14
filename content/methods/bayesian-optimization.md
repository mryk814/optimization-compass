---
content_id: bayesian-optimization
kind: method
method_id: M_BAYESIAN_OPT_GP
title_ja: ベイズ最適化
title_en: Bayesian Optimization
summary: 少ない評価回数で有望な点を選ぶため、代理モデルと獲得関数を使う逐次最適化です。
source_ids: [S034, S035]
prerequisites: []
related_ids: []
visualization_ids: []
comparison_ids: []
aliases: [/learn/bayesian-optimization]
visualization_aliases: []
comparison_aliases: []
status: published
last_reviewed: 2026-07-15
---

少ない評価回数で有望な点を選ぶため、代理モデルと獲得関数を使う逐次最適化です。

## 何を繰り返しているか

1. いくつかの点で高価な目的関数を評価する。
2. 観測結果から、目的関数の予測と不確実性を表す代理モデルを更新する。
3. 獲得関数を使い、次に評価する点を選ぶ。
4. 評価予算または停止条件まで繰り返す。

代理モデルの平均は目的関数そのものではありません。不確実性が大きい場所を調べる**探索**と、良い値が期待できる場所を調べる**活用**のバランスを取ります。

## 画面の読み方

| 表示 | 読み取ること |
|---|---|
| observed points | 実際に評価した入力と結果 |
| surrogate mean | 現在の代理モデルが予測する平均 |
| uncertainty | まだ分かっていない範囲 |
| acquisition | 次の評価点を選ぶための基準 |
| incumbent | 現時点で最良の観測値 |

> [!WARNING]
> 獲得関数の最大点は、目的関数の最適点だと確定した場所ではありません。次に情報を得る価値が高い候補です。

## 向いている状況

- 1回の実験やsimulationが高価
- 評価回数に厳しい上限がある
- 勾配を直接利用できない
- hyperparameterや設計変数を少ない試行で改善したい

高次元、強いカテゴリ構造、頻繁な評価失敗、非定常な目的関数では、kernel、encoding、failure handling、search spaceの設計を別に確認します。

## 比較するときの注意

Random Searchなどと比較する場合は、少なくとも次を揃えます。

- initial design
- random seed
- objective evaluation budget
- noise handling
- search bounds
- stopping condition

単一のtrajectoryだけで一般的な優劣を判断せず、複数seedと問題instanceで確認します。
