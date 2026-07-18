---
content_id: concept.chance-risk-contract
kind: concept
canonical_entity_type: feature
canonical_entity_id: F_CONSTRAINT_CHANCE
title_ja: Chance constraint・CVaR・robustness
title_en: Chance Constraints, CVaR, and Robustness
summary: Chance constraintは、制約違反の確率を指定して不確実な制約を扱う枠組みで、CVaR・robust・stochastic・DROとの違いを目的・制約・保証範囲で整理します。
source_ids: [S054, S055, S056]
prerequisites: [concept.uncertainty-models, concept.constraint-class]
related_ids: [concept.simplex, family.stochastic-ml, lp-qp-conic]
status: published
last_reviewed: 2026-07-19
---

Chance constraintは、制約違反の確率を指定して不確実な制約を扱う枠組みで、CVaR・robust・stochastic・DROとの違いを目的・制約・保証範囲で整理します。

## 30秒でつかむ

不確実な最適化では、「悪い結果をどこまで許すか」を目的と制約に分けて記録します。

| 語彙 | 主に置く場所 | 問い | 依存する前提 |
| --- | --- | --- | --- |
| stochastic | 目的・制約 | 分布やscenarioの平均的な結果をどう扱うか | 分布・生成規則・sample |
| robust | 制約・目的 | 指定したuncertainty setのどの値でも守るか | setの範囲・形・根拠 |
| chance constraint | 制約 | 違反確率を目標以下にできるか | 分布・確率水準・推定 |
| CVaR | 目的・場合によっては制約 | 悪い側のtailをどれだけ抑えるか | lossの向き・tail水準・sample |
| distributionally robust optimization (DRO) | 目的・制約 | 許容した分布集合の中で結果を抑えられるか | ambiguity set・距離・半径 |

「stochastic」は一つのsolver名ではありません。確率分布や有限scenarioを使う問題の表現です。`robust`は不確実性をsetで囲む考え方であり、`chance constraint`は確率を制約の判定へ入れる考え方です。CVaRはtail riskの測り方で、これらと同じ分類軸ではありません。

## chance constraintは制約違反の確率を指定する

不確実な値を`ξ`、制約関数を`g(x, ξ)`とすると、代表的なchance constraintは次の形です。

$$
\Pr\{g(x,\xi)\leq 0\}\geq 1-\alpha.
$$

`α`は許容する違反確率です。ここで指定しているのは、明示した分布と確率モデルのもとでの制約充足です。`α=0.05`と書いただけで、未知の分布や将来の全データに対する安全保証になるわけではありません。

実装やCaseでは、少なくとも次を一緒に残します。

- 何が揺らぐか。parameter、observation noise、process disturbanceの区別
- `ξ`の分布、推定方法、独立性や定常性の仮定
- `α`の値と、確率を評価する単位
- 分布を推定したsampleと、性能を確認するheld-out sampleの分割
- violationの定義、tolerance、未観測条件への外挿範囲

有限scenarioのうち何件で制約を満たしたかを数えるだけなら、まずはempirical scenario satisfactionです。scenarioの生成規則と評価データが別に固定されていない限り、それを確率保証と呼びません。

## CVaRは悪い側のtailを目的へ入れる

損失`L(x, ξ)`を小さくしたいとき、平均だけでなく悪い側のtailを重く見るためにCVaR（Conditional Value at Risk）を使う場合があります。CVaRは、指定したquantileより悪い損失の平均を表すtail-riskの指標です。

chance constraintが「制約違反の頻度をどこまで許すか」を問うのに対して、CVaRは「悪い損失が起きたとき、その大きさをどれだけ抑えるか」を問います。そのため、CVaRを目的関数へ加えても、制約違反確率を直接`1-α`以下にしたことにはなりません。反対に、chance constraintを置いても、違反したときの損失額やtailの厚さは制御しません。

目的と制約の両方へ不確実性を入れるなら、次のように別々に記録します。

| 記録する場所 | 例 | 読み方 |
| --- | --- | --- |
| 目的 | 期待損失 + CVaRの重み付き和 | 平均性能とtail riskの交換を読む |
| 制約 | chance constraint | 違反の頻度に上限を置く |
| 両方 | CVaR objective + robust constraint | tailの大きさとset内の最悪可行性を別々に読む |

CVaRの値を比較するときは、lossの向き、tail水準、sample数、scenarioの重み、最適化に使ったsampleと評価用sampleを固定します。値が小さいことだけで、異なる分布や異なるtail水準の結果を順位付けしません。

## robust・stochastic・DROを同じ軸で混ぜない

| formulation | 揺らぎの表現 | 代表的な主張 | 外側へ言えないこと |
| --- | --- | --- | --- |
| robust optimization | uncertainty set `U` | `U`の中の全ての値で制約を守る | `U`の外側の値への保証 |
| stochastic programming | distributionまたはscenario | 指定した分布・scenarioで期待値や制約を評価する | 分布外・未観測データでの同じ結果 |
| chance-constrained optimization | distributionと許容確率 | 指定した確率モデルで違反確率を抑える | 分布推定の誤差やmodel misspecificationを無視した保証 |
| DRO | 分布の集合（ambiguity set） | 許容した分布集合の中でworst-caseを抑える | ambiguity setの外側の分布 |

robust optimizationのsetは、parameterが取りうる範囲を表します。DROのambiguity setは、確率分布そのものの候補集合を表します。どちらも「不確実なものを集合で扱う」と説明できますが、集合の要素がparameterなのか分布なのかを省略しません。

stochastic programmingでscenarioを増やすと、計算問題の表現は細かくなります。しかし、sample sizeが増えたことだけでout-of-sample性能や確率保証が自動的に得られるわけではありません。scenarioの生成、重み、seed、評価用データを固定して、in-sampleとheld-outを分けます。

## simplex配分での読み方

ポートフォリオや資源配分では、配分`x`をsimplex上に置き、scenarioごとの損失`L_s(x)`を評価する形がよく現れます。

$$
x_i\geq 0,\qquad \sum_i x_i=1.
$$

このsimplex制約は、配分のdomainを定めます。不確実性の扱いは別に、たとえば次のように追加します。

- stochastic: `L_s(x)`の期待損失を目的にする
- CVaR: 大きい`L_s(x)`のtailを目的に加える
- chance constraint: 予算超過などの制約をscenarioで許容確率までに抑える
- robust: 定めた損失・需要のsetの全てで制約を守る
- DRO: scenario分布の候補集合に対するworst-caseを抑える

同じ配分変数を使っても、目的・制約・保証範囲が変われば別の問題です。nominalな共分散riskの結果を、そのままCVaR、chance constraint、robust、DROの結果として表示しません。

## 仕様に残す最小contract

不確実性を含む問題では、次の項目を空欄にしません。

```python
uncertainty_contract = {
    "source": "parameter | observation_noise | process_disturbance",
    "model": "distribution | scenarios | uncertainty_set | ambiguity_set",
    "objective_risk": "expectation | variance | worst_case | cvar | not_applicable",
    "constraint_treatment": "nominal | robust | chance | scenario",
    "confidence_or_tail": "explicit_value_and_definition",
    "training_evaluation_split": "fixed_description",
    "guarantee_scope": "supported_claim_and_assumptions",
}
```

`unknown`は、まだ調べていない前提を`nominal`や`not_applicable`へ変換する値ではありません。分布、set、tail水準、評価データのどれが未確定かをそのまま残し、追加で必要な観測やsourceを記録します。

::: warning
scenario上の可行性、chance constraintの確率計算、robust set内の可行性、DROのambiguity set内のworst-caseは、それぞれ保証の範囲が違います。表示する結果には、対象となったscenario・分布・setと、評価時のtoleranceを添えます。
:::

## 次に読む

[不確実性モデル・リスク・保証範囲](#/learn/concept.uncertainty-models)で、uncertainty sourceとguarantee scopeの分解を確認してください。配分変数のdomainは[Simplex・確率ベクトル](#/learn/concept.simplex)、一般の可行性判定は[制約class](#/learn/concept.constraint-class)で確認できます。確率的gradientのnoiseと確率制約は別の話なので、optimizerの選択は[確率勾配・機械学習optimizerの選び分け](#/learn/family.stochastic-ml)へ分けて進みます。
