---
content_id: concept.uncertainty-models
kind: concept
canonical_entity_type: feature
canonical_entity_id: F_GUARANTEE_UNCERTAINTY
title_ja: 不確実性モデル・リスク・保証範囲
title_en: Uncertainty Models, Risk, and Guarantee Scope
summary: 不確実性を、何が揺らぐか・どうモデル化するか・目的と制約のどこへ反映するか・どこまで保証するかに分けて読むための語彙です。
source_ids: [S054, S055, S056]
prerequisites: [concept.constraint-class, concept.simplex]
related_ids: [family.stochastic-ml, family.expensive-black-box, lp-qp-conic]
status: published
last_reviewed: 2026-07-19
---

不確実性を、何が揺らぐか・どうモデル化するか・目的と制約のどこへ反映するか・どこまで保証するかに分けて読むための語彙です。

## 30秒でつかむ

「不確実な最適化」という一語だけでは、少なくとも次の4つが混ざります。

| 先に分けるもの | 問うていること | 代表的な記録 |
| --- | --- | --- |
| 不確実性のsource | 何が揺らぐのか | parameter、観測、process disturbance |
| uncertainty model | 揺らぎを何として表すか | point、set、distribution、scenario |
| risk treatment | 悪い結果を目的へどう反映するか | expectation、variance、worst case、tail risk |
| guarantee scope | どの条件で何を言えるか | nominal、robust、probabilistic、empirical |

この分解をしないまま「robustだから安全」「scenarioで満たしたから確率保証がある」と読まないことが、この語彙の出発点です。

## まず、何が不確実かを分ける

### 不確実なparameter

材料定数、需要、将来価格など、モデルへ入れる値そのものが分からない場合です。真の値が固定されていても、推定できていないことがあります。これは、観測を増やせば減る知識不足（epistemic uncertainty）として扱う場合がありますが、必ずこの二分法だけで整理できるとは限りません。

### observation noise

同じ条件を測り直しても値が揺れる、あるいは測定過程が真の状態を正確に返さない場合です。データを増やして平均を安定させることと、将来の観測が揺れないことは同じではありません。ノイズを目的関数の値へ入れたのか、制約判定へ入れたのかも残します。

### process disturbance

制御や運用の途中で外乱が入り、決定後の状態が変わる場合です。設計時点のparameter uncertaintyだけでなく、実行中のdisturbanceとfeedback・再計画の有無を記録します。

これらは同じ問題に同時に現れます。たとえば、需要の推定誤差はparameter uncertainty、注文の到着時のばらつきはobservation noise、配送中の遅延はprocess disturbanceとして別々に検証する必要があります。

## 次に、揺らぎの表現を選ぶ

### nominal model

代表値を1つ置いて、通常の最適化問題を解きます。計算と説明は簡単ですが、代表値以外での可行性や性能は別の検証です。nominal feasibilityは、robust feasibilityや確率的な制約充足を意味しません。

### uncertainty set

未知量が入る範囲を集合 $U$ として、集合の中の値に対する条件を検討します。robust formulationでは「この集合のどの値を採っても制約を守る」のように、集合全体に対する可行性を問います。集合の形・幅・根拠を変えると保守性も変わるため、uncertainty setは単なるsolver parameterではありません。

### distribution

未知量の確率分布を仮定し、期待値や確率を目的・制約へ入れます。確率モデルの選択、推定、calibration、独立性や定常性の仮定を明示します。分布を仮定した結果は、その仮定から外れたデータに対する無条件の保証ではありません。

### empirical scenarios

観測または生成した有限個のscenarioを並べ、各scenarioでの目的・制約値を比較します。これはscenario集合上の結果を確認する方法であり、未観測のout-of-sampleや真の分布に対する保証とは別です。scenario数、生成規則、seed、学習用と評価用の分割を固定して記録します。

### ambiguity set

分布そのものを1つに固定せず、妥当と考える分布の集合を扱う考え方です。distributionally robust optimization（DRO）を使う場合は、どの分布集合を許したか、半径や距離の意味、データからの構成方法を明記します。これは uncertainty setでparameterを囲むことと同じではありません。

## riskは目的と制約で別に扱う

同じ「riskを抑える」でも、目的関数と制約では問いが違います。

| 場所 | 問い | 記録するもの |
| --- | --- | --- |
| objective | 平均的な性能と悪い結果のどちらを重く見るか | expectation、variance、worst-case、tail-riskの定義と係数 |
| constraint | 危険な結果をどの頻度・範囲まで許すか | violationの定義、target、confidence、判定単位 |

varianceを小さくする目的を置いても、制約違反の確率を直接制御したことにはなりません。逆に、chance constraintを置いても、制約違反が起きないことを保証するわけではありません。CVaRなどtail riskを使う場合も、lossの向き、tailの定義、quantile、confidence level、sampleでの評価方法を同じ契約へ書きます。

## guarantee scopeを4段階で読む

1. **Nominal**: 代表値・基準データでの結果。基準から外れた場合の主張は含まない。
2. **Robust**: 明示したuncertainty setの中での最悪条件に対する結果。setの外側までは言えない。
3. **Probabilistic**: 明示した分布と確率水準のもとでの主張。分布仮定と推定誤差を別に検証する。
4. **Empirical scenario**: 手元の有限scenarioで観測した結果。out-of-sample性能や確率保証は、別の評価設計が必要。

「制約を満たした」という一文には、どの時点で、どのscenario・set・分布で、何を計算し、どのtoleranceで判定したかを添えます。離散化したscenarioや固定sampleでの可行性を、連続系・将来データ・分布外の安全保証へ拡張しません。

## Case journeyへつなぐ

現在の[ポートフォリオ配分Case](#/gallery/portfolio-allocation)は、4資産のsimplex制約と共分散riskを読むnominalな教材です。過去データの推定誤差や将来分布の変化を扱うrobust・stochastic・chance-constrained・DROのcomplete journeyではありません。Caseの制約、目的、実装を読んだあと、次のsliceでは固定scenarioとheld-out scenarioを分けたTheater/Compareを接続します。

この境界を明記することで、単一の配分結果を「将来損失の保証」と誤読せずに済みます。complete journeyへ進めるには、少なくとも次を同じCase identityへ接続します。

- uncertainty sourceとmodel assumption
- objective riskとconstraint riskの定義
- 固定した教育用scenarioとout-of-sample評価
- sample size、confidence target、seed、停止条件
- candidate・conditional・excluded methodの理由と、実装が報告する診断値

## 仕様に残す最小contract

不確実性を含むCaseでは、次の項目を空欄にしません。

```python
uncertainty_contract = {
    "source": "uncertain_parameter | observation_noise | process_disturbance",
    "model": "nominal | set | distribution | scenarios | ambiguity_set",
    "objective_risk": "explicit_definition_or_not_applicable",
    "constraint_treatment": "nominal | robust | chance | scenario",
    "training_evaluation_split": "fixed_description",
    "guarantee_scope": "what_is_supported_and_under_which_assumptions",
}
```

`unknown`は、まだ調べていないことを`nominal`や`not_applicable`へ変換するための値ではありません。未確定の前提を残したまま、どの追加観測・追加scenario・追加sourceが必要かを記録します。

## 次に読む

[制約class](#/learn/concept.constraint-class)で可行性の判定単位を確認し、[Simplex・確率ベクトル](#/learn/concept.simplex)で配分Caseの変数領域を確認します。確率的な更新noiseとtraining validationの区別は[確率勾配・機械学習optimizerの選び分け](#/learn/family.stochastic-ml)へ進みます。
