---
content_id: branch-and-bound
kind: method
method_id: M_BRANCH_BOUND
title_ja: Branch-and-Bound（分枝限定法）
title_en: Branch and Bound
summary: 上下界を使って、改善できない離散探索の枝をまとめて除外する。
source_ids: [S021, S022, S079]
prerequisites: []
related_ids: []
visualization_ids: [binary-knapsack-bnb-complete, binary-knapsack-bnb-budget]
comparison_ids: []
aliases: [/learn/branch-and-bound]
visualization_aliases: []
status: published
last_reviewed: 2026-07-15
---

上下界を使って、改善できない離散探索の枝をまとめて除外する。

Branch-and-Boundは、整数・0-1変数の候補を枝分かれさせながら、実行可能解の値（incumbent）と未探索部分のboundを比較して探索範囲を減らします。

## naive enumerationとの違い

naive enumerationはすべての割当を調べます。Branch-and-Boundは、制約違反のsubtreeと、boundがincumbentを改善できないsubtreeを丸ごと探索しません。枝を調べなかった理由が証明として残る点が重要です。

## best feasible・global bound・gap

- best feasible valueは、現時点で見つかった実行可能解の値です。
- global boundは、未探索部分が到達しうる最良値の限界です。
- gapが0になり、未処理nodeがなくなれば最適性を証明できます。時間切れやnode予算で停止した場合、best feasibleは候補解ですが最適性は未証明です。

## MIPとCP-SATを同一視しない

MIPのBranch-and-Cutは連続緩和、cut、presolveなどを組み合わせます。CP-SATはSAT/CP由来の伝播・学習などを統合します。どちらも探索木やboundを見せられますが、内部機構やboundの意味を同一視できません。この教材は4変数knapsackの教育用Branch-and-Boundで、実solverの性能比較ではありません。
