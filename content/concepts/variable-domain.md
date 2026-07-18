---
content_id: concept.variable-domain
kind: concept
canonical_entity_type: feature
canonical_entity_id: F_VARIABLE_DOMAIN
title_ja: 変数のdomain
title_en: Variable Domain
summary: 変数のdomainは、最適化で何を動かせるかを決め、使える定式化・solver・保証の範囲を最初に絞る分類です。
source_ids: [S054, S055, S056]
related_ids: [family.smooth-local, family.discrete-structure, family.manifold]
status: published
last_reviewed: 2026-07-18
---

変数のdomainは、最適化で何を動かせるかを決め、使える定式化・solver・保証の範囲を最初に絞る分類です。

## まず「何を選ぶか」を言葉にする

最適化でいう変数は、Pythonの`float`や`int`の型だけではありません。設計長さなら連続値、製品を採用するかならbinary、訪問順ならpermutation、制御入力の時系列ならtrajectoryが変数です。solver選択の前に、**解として返したい対象がどの集合に属するか**を明示します。

同じ実装でも、表現を変えると別の問題になります。たとえば「3種類から1つを選ぶ」は、整数`0, 1, 2`として連続最適化器へ渡すより、categorical choiceまたはone-hot binaryとして制約を伴う離散問題として表す方が、選択の意味を保ちやすくなります。

| domain | 典型例 | 最初に確認すること |
| --- | --- | --- |
| continuous | 寸法、濃度、温度 | bounds、scale、微分の有無 |
| integer / binary | 台数、採否、on/off | 線形緩和の強さ、論理制約、許容gap |
| categorical / ordinal | 材料種、モデル種、段階 | 順序や距離を仮定してよいか |
| permutation / graph / set | 順路、接続、選抜 | 専用のgraph・matching・routing構造がないか |
| simplex / matrix / manifold | 配合比、共分散、回転 | 集合を保つprojection・parameterization・retractionがあるか |
| trajectory / function | 制御列、温度profile | 時間離散化、dynamics、連続時間での妥当性 |

## domainはsolver名より先に効く

連続変数で滑らかな目的と勾配があるなら、[滑らかな局所最適化](#/learn/family.smooth-local)のような勾配法を検討できます。一方、binaryや整数を連続変数として解いて丸めるだけでは、丸め後の解が制約を満たすとは限らず、最適性gapの解釈も失われます。離散性が本質なら、[離散・組合せ最適化](#/learn/family.discrete-structure)の定式化から考えます。

domainが特殊な集合である場合も同様です。確率の比率は単に非負な実数の並びではなく、合計1のsimplexです。回転行列や低ランク行列は、成分ごとのboundsだけでは本来の集合を保てません。制約へpenaltyを足す方法もありますが、projection、変数変換、または[manifold最適化](#/learn/family.manifold)のように集合を直接扱う方法と比べて、conditionや実行可能性を確認します。

## 連続緩和は便利だが、元の問題ではない

整数・binary問題を連続緩和して解くと、下界、初期解、感度解析、branch-and-boundの部分問題として役立つことがあります。ただし、緩和解の`x = 0.37`は「0か1を選ぶ」という元の意思決定そのものではありません。丸めや整数化の後には、目的値・制約違反・最適性証明を改めて評価します。

同じ注意はtrajectoryにもあります。時間を粗く離散化した制約を満たしても、連続時間の途中で安全制約を満たす保証には直結しません。必要ならmesh refinement、区間内検証、または連続時間の制約を扱う定式化を追加します。

::: warning
「変数が数値で表せる」ことと、「連続最適化として扱ってよい」ことは別です。カテゴリ、順列、論理、行列構造を安易に連続値へ符号化すると、solverが動いても解の意味を壊すことがあります。
:::

## 診断するときの最小チェック

解法を比較する前に、次を記録しておくと切替理由を追えます。

- 各変数のdomain、単位、bounds、許容精度
- 整数・カテゴリの符号化と、無効な組合せを除く制約
- 連続緩和を使う場合は、丸め・repair後に再評価した可行性と目的値
- trajectoryなら、時間刻み、制御の保持方法、区間内制約の確認方法
- 特殊集合なら、projection・parameterization・retractionのどれで集合を保つか

次に、目的の形が滑らかか、制約が何か、1回の評価にどれだけの予算を使えるかを並べます。domainだけで万能なsolverは決まりませんが、domainと矛盾する選択は早い段階で除外できます。

## 次に読む

制約の表し方と可行性の読み方は[制約class](#/learn/concept.constraint-class)、評価回数が限られるときの予算設計は[評価費と予算](#/learn/concept.evaluation-cost)を確認してください。
