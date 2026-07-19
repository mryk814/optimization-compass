---
content_id: concept.evaluation-cost
kind: concept
canonical_entity_type: feature
canonical_entity_id: F_EVALUATION_COST
title_ja: 評価費と予算
title_en: Evaluation Cost and Budget
summary: 評価費と予算は、目的関数を何回・どの並列度・どのfidelityで測れるかを記録し、評価ledgerから探索と比較の公平性を決めます。
source_ids: [S035, S038, S059, S069, S075]
related_ids: [family.expensive-black-box, bayesian-optimization, random-search, hyperband-asha]
status: published
last_reviewed: 2026-07-19
---

評価費と予算は、目的関数を何回・どの並列度・どのfidelityで測れるかを記録し、評価ledgerから探索と比較の公平性を決めます。

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

## まず評価ledgerを作る

高価なsimulationでは、最終的なbest-so-farだけを残すと、どの評価に予算を使ったかが消えます。1回の呼び出しを1行として、少なくとも次を記録します。

| 項目 | 記録するもの | 読み方 |
| --- | --- | --- |
| `call_id` | simulator callの一意な番号 | 再試行や重複評価を追う |
| `x` / configuration | 設計変数またはtrialの設定 | 同じ候補の再評価を区別する |
| `fidelity` | low / high、epoch、meshなど | どの精度の観測かを区別する |
| `cost` | そのcallが消費した相対費または実費 | 予算の累計を計算する |
| `status` | `ok`、`failed`、`censored`、`timeout` など | 値がない理由を残す |
| `observed_value` | 成功時の観測値。失敗時は`null` | 目的値と状態を混ぜない |

`started_at`、`finished_at`、worker、seedを追加できる場合は、wall-clockと並列性も追跡できます。重要なのは、失敗したcallもledgerから消さないことです。評価をやり直したなら、新しい`call_id`を割り当てます。

```python
ledger = [
    {"call_id": 1, "x": 0.5, "fidelity": "low", "cost": 1.0,
     "status": "ok", "observed_value": 0.31},
    {"call_id": 2, "x": 0.5, "fidelity": "high", "cost": 12.0,
     "status": "ok", "observed_value": 0.28},
    {"call_id": 3, "x": 2.7, "fidelity": "low", "cost": 1.0,
     "status": "failed", "observed_value": None},
]

spent = sum(row["cost"] for row in ledger)
successful = [row for row in ledger if row["status"] == "ok"]
```

`best-so-far`は通常、成功した同一fidelityの観測を対象に計算します。low fidelityで得た値をhigh fidelityの最終品質へそのまま混ぜると、探索の進展と評価精度の差が分からなくなります。

## fidelityが違えば、同じ評価とは限らない

low fidelityは安価な近似、high fidelityはより高価で精度の高い評価です。ただし、low fidelityの順位がhigh fidelityと一致する保証はありません。安い評価を増やすことは、high fidelityを1回増やすことと同じではないのです。

固定した教材でこの違いを追うなら、設計変数を$x\in[-3,3]$、fidelityを$\ell\in\{L,H\}$、costを$c_L=1$、$c_H=12$とします。high fidelity相当の予算は、次のように換算できます。

$$
C_H=\sum_k \frac{c_{\ell_k}}{c_H}.
$$

たとえばlowを12回使っても、highを1回使った費用に相当するだけです。low fidelityの観測はsurrogateの学習や候補の絞り込みに役立つ場合がありますが、最終候補の品質をhigh fidelityで確認した記録は別に残します。[Bayesian Optimization](#/learn/bayesian-optimization)は履歴と不確実性から次の評価点を選ぶ候補であり、[Hyperband / ASHA](#/learn/hyperband-asha)は中間resourceから継続・停止を判断するresource allocationです。両者を使う場合も、fidelityの意味と費用を同じledgerへ書きます。

## 失敗とcensoredを目的値に置き換えない

simulationがcrashした、timeoutした、計測上限に達して値が確定しなかった。この3つは、低い目的値が観測されたこととは違います。

- `failed`: 計算や実験が完了せず、値を得られなかった
- `censored`: 上限・観測窓・停止条件のため、値がある範囲までしか分からない
- `timeout`: 時間上限に達した。`failed`と同じ扱いにするかは、事前に決める

いずれも少なくともstatusと消費costを記録し、`observed_value`を`null`にします。失敗を目的値へ一律に大きな罰則として代入すると、失敗領域と本当に悪い領域を区別できません。feasibility model、censoring model、retry policyを使うなら、その採用条件と再試行分のcostを比較条件に明記します。

この区別は、失敗率を隠さないためだけのものではありません。失敗が特定の領域に偏っているなら、探索空間、制約、simulationの前処理、あるいはfidelity policyのどこかを見直す必要があります。

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

このようなcontract（契約）があると、best-so-farだけでなく、評価開始・完了時刻、idle時間、失敗率、実際に使ったbudgetを並べて読めます。fidelityを複数使う場合は、trial数とは別にhigh-fidelity-equivalent costも報告します。

## 比較は同じ予算の物差しで読む

multi-fidelityの比較でiteration数だけを揃えると、low fidelityを多く使った手法とhigh fidelityを多く使った手法を公平に比べられません。少なくとも次を固定します。

| 比較軸 | 揃える内容 |
| --- | --- |
| 初期条件 | initial design、bounds、seed、同一点の再評価規則 |
| 評価予算 | total cost、high-fidelity-equivalent cost、wall-clock上限 |
| 実行条件 | 並列worker数、batch / asynchronousの方針、停止規則 |
| fidelity | 各fidelityの定義、cost、切替条件、最終確認のfidelity |
| 失敗処理 | `failed` / `censored` / `timeout`の記録、retry、modelへの入力方法 |
| 指標 | 成功したhigh fidelityのbest-so-far、成功率、status別件数 |

「同じ80 trial」だけでは不十分です。ある手法が12回のlow fidelityで候補を絞り、別の手法が1回のhigh fidelityに相当する費用を使っているなら、その差をcost軸に戻して表示します。single runの勝敗を一般的なrankingへ拡張せず、固定条件と未確認の前提を添えて読みます。

[high-fidelity-equivalent costを揃えたCompare](#/compare/COMPARE_BO_MULTIFIDELITY_COST)では、初期design、noise、low/high cost、parallel workers=1、固定tuning、失敗をnullで記録してcostを課しretryしないpolicyを固定します。変更するのはfidelity配分だけです。[low-fidelity biasのfailure Theater](#/theater/bayesian-optimization/SCENARIO_BO_1D_LOW_FIDELITY_BIAS)では、同じ2候補を両fidelityで確認すると順位が反転します。前者は公平な物差し、後者はdiscrepancyを見逃したfailure signalであり、どちらも一般的な手法順位ではありません。

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

high/low fidelityの固定例を実際の候補選択へつなぐには、[低／高 fidelityシミュレータのGalleryケース](#/gallery/multi-fidelity-simulator)を確認してください。高価なblack-box全体の条件付き選択は、[高価なblack-box・HPOの選び分け](#/learn/family.expensive-black-box)で確認できます。評価不能・失敗を含む可行性の扱いは、[制約class](#/learn/concept.constraint-class)へ進みます。
