---
content_id: mma
kind: method
method_id: M_MMA
title_ja: MMA
title_en: Method of Moving Asymptotes
summary: MMAは、非線形最適化を変数ごとの凸な近似問題へ分解し、moving asymptotesで更新幅を制御する逐次近似手法です。
source_ids: [S100]
prerequisites: [topology-optimization, concept.constraint-class]
related_ids: [optimality-criteria-topology, simp-topology]
visualization_ids: [topology-optimization-field-evolution]
comparison_ids: [COMPARE_TOPOLOGY_OC_MMA]
aliases: [/learn/mma]
status: published
last_reviewed: 2026-07-18
---

MMAは、非線形最適化を変数ごとの凸な近似問題へ分解し、moving asymptotesで更新幅を制御する逐次近似手法です。

## 更新問題を近似して解く

元の目的関数や制約をそのまま一度に解くのではなく、現在点の周辺で近似問題を作ります。
各変数の近似には上下の漸近線があり、反復の履歴に応じて次の更新範囲が変わります。

トポロジー最適化では、密度fieldの各要素が大量の設計変数になります。
MMAはこのような変数数の多い制約付き問題を、感度情報を使う逐次更新として扱います。

## OCとの違い

OCはminimum-complianceと体積率の構造に強く結びついた更新則です。
MMAは近似問題を毎回組み立てるため、追加の制約や異なる目的へ拡張しやすい一方、漸近線や近似の設定を持ちます。

同じ問題で比べるときは、MMAが一般に優れていると決めつけません。
固定したgenerator、予算、初期密度、制約、filterを揃え、fieldの変化と停止状態を一緒に見ます。

## 診断値

`compliance`と`volume_fraction`に加え、近似問題の更新幅、move limit、gray fraction、checkerboard scoreを保存します。
近似問題が元の問題をどの程度表しているかは、iterationごとの値で確認します。

## 失敗・切替の兆候

更新が振動する、体積率は守るが荷重経路が安定しない、近似問題の設定に結果が強く依存する場合は、asymptoteとmove limitを点検します。
構造が単純なminimum-complianceに戻るなら、OCとの比較を残して選び分けます。

## 次に読む

[OCとMMAの比較](#/compare/COMPARE_TOPOLOGY_OC_MMA)で同じdensity fieldを読み、[SIMP密度法](#/learn/simp-topology)で感度がどこから来るかを確認します。
