---
content_id: method.nelder-mead
kind: method
method_id: M_NELDER_MEAD
title_ja: Nelder–Mead単体法
title_en: Nelder–Mead
summary: 勾配を使わず、単体を変形しながら局所探索します。
related_ids: [concept.derivative-free]
visualization_ids: [nelder-mead-quadratic]
comparison_ids: [COMPARE_GRADIENT_FAMILY]
aliases: [/learn/method.nelder-mead]
visualization_aliases: [nelder-mead-quadratic|/theater/nelder-mead]
comparison_aliases: [COMPARE_GRADIENT_FAMILY|/compare/gradient-quadratic]
source_ids: [S001, S002]
status: published
last_reviewed: 2026-07-14
---

## 直感

単体を変形して、目的関数の低い方向を探します。

## 注意

局所探索であり、高次元・制約付き・多峰性では万能ではありません。
