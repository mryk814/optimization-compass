---
content_id: concept.evaluation-cost
kind: concept
canonical_entity_type: feature
canonical_entity_id: F_EVALUATION_COST
title_ja: 評価費と予算
title_en: Evaluation Cost and Budget
summary: 評価費と予算は、目的関数を何回・どの並列度・どの信頼度で測れるかを表し、探索よりも先に最適化の実行可能な戦略を決めます。
source_ids: [S035, S059, S075]
related_ids: [family.expensive-black-box, bayesian-optimization, random-search, hyperband-asha]
status: published
last_reviewed: 2026-07-18
---

評価費と予算は、目的関数を何回・どの並列度・どの信頼度で測れるかを表し、探索よりも先に最適化の実行可能な戦略を決めます。

## 評価費は1回のwall-clock時間だけでは決まらない

simulationを1回実行する時間は、評価費の一部です。
実験試料を作る費用、GPU queueの待ち時間、失敗trialの後始末も、探索に使える予算を減らします。
担当者が結果を確認できる回数も、使える予算を制約します。
同じ10分の評価でも、100台で並列に回せる計算と、装置を占有して逐次にしか測れない実験では、適した探索の形が異なります。

したがって、次の予算を混ぜずに記録します。

| 予算 | 例 | 手法選択への影響 |
| --- | --- | --- |
| 評価回数 | 実験50回、simulation 1,000回 | surrogateを学習する余地、baselineの強さ |
| 逐次時間 | 装置1日、締切まで6時間 | 次の点を待って選ぶ価値 |
| 並列枠 | GPU 8枚、試験片4本 | batch / asynchronous探索、idle時間 |
| fidelity | epoch、mesh、試料量 | early stoppingやmulti-fidelityが使えるか |
| 再評価枠 | 同一点を何回測るか | noise推定、外れ値確認、比較の公平性 |
| 失敗枠 | timeout、破損、infeasible | retry・停止・欠測の扱い |

`cheap`や`very_expensive`は、普遍的な秒数を表す分類ではありません。
評価回数、並列性、必要精度、実験の不可逆性に対する相対的な分類です。

## 評価回数と並列度で候補手法が変わる

数十〜数百回しか評価できず、1回ごとの結果を待てるなら、観測履歴と不確実性から次の点を選ぶ[Bayesian Optimization](#/learn/bayesian-optimization)が候補になります。
これは「必ず最少回数で最適解へ着く」ことを意味しません。
surrogateの仮定、initial design、noise、acquisition最適化が合わなければ、単純な[Random Search](#/learn/random-search)より悪くなることもあります。

評価が安価で大量並列に実行できる場合は、探索の複雑な逐次判断より、広く独立に試すbaselineが強いことがあります。
途中の低コスト評価が最終性能をある程度予測するなら、[Hyperband / ASHA](#/learn/hyperband-asha)のようにresourceを段階配分する設計も検討できます。
ただし、途中指標と最終指標の順位相関が弱いと、良い候補を早く落とします。

## budgetには停止規則も含める

手法比較や実運用では、評価回数だけでなく停止規則を先に決めます。
たとえば「80 trial、4 worker、wall-clock 6時間、failed trialは記録して再試行しない、同一点の再評価は最大2回」のように書きます。
後から一方の手法だけに追加budgetを与えると、性能差と予算差を分けられません。

```python
experiment_budget = {
    "max_evaluations": 80,
    "wall_clock_minutes": 360,
    "parallel_workers": 4,
    "replicates_per_selected_point": 2,
    "failure_policy": "record-and-stop",
    "stopping_rule": "first-reached-limit",
}

assert experiment_budget["max_evaluations"] > 0
assert experiment_budget["parallel_workers"] > 0
```

このようなcontract（契約）があると、best-so-farだけでなく、評価開始・完了時刻、idle時間、失敗率、実際に使ったbudgetを並べて読めます。

## 高価な評価で混同しやすい失敗

- 初期designを省くと、surrogateや局所探索が偏った場所から始まる
- noiseがあるのに再評価枠をゼロにすると、偶然の良い値を改善と誤認しやすい
- batchを大きくしすぎると、同じ情報を得る前に似た候補を消費する
- timeoutや実験失敗を黙って悪い目的値へ置換すると、失敗領域と低性能領域を区別できない
- fidelityを下げた結果だけで最終品質を判断すると、早期停止のbiasを見落とす

::: warning
評価費が高いことだけで、Bayesian Optimizationを第一選択にはできません。
変数のdomain、条件付き空間、noise、並列度、失敗の意味、利用できるfidelityを一緒に見ます。
:::

## 次に読む

高価なblack-box全体の条件付き選択は、[高価なblack-box・HPOの選び分け](#/learn/family.expensive-black-box)で確認できます。
評価不能・失敗を含む可行性の扱いは、[制約class](#/learn/concept.constraint-class)へ進みます。
