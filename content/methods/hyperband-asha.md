---
content_id: hyperband-asha
kind: method
method_id: M_HYPERBAND_ASHA
title_ja: Hyperband / ASHA
title_en: Hyperband and ASHA
summary: 多数のtrialを小さなresourceで始め、中間成績が悪いtrialを早期終了して有望なtrialへbudgetを移すmulti-fidelity探索です。
source_ids: [S034, S038, S069]
related_ids: [family.expensive-black-box, tpe, bayesian-optimization]
status: published
last_reviewed: 2026-07-18
---

多数のtrialを小さなresourceで始め、中間成績が悪いtrialを早期終了して有望なtrialへbudgetを移すmulti-fidelity探索です。

## 30秒でつかむ

この手法の気持ちは、**すべての候補を最後まで育てるのではなく、少し試した時点で見込みの薄い候補を止め、その分の時間や計算資源を有望な候補へ回したい**というものです。

- 見ているもの: intermediate metric、消費resource、trial status
- 動かしているもの: trialの継続・停止とresource allocation
- 前進の判断: 限られた総resourceで良い最終trialを残せるか
- 別に確認するもの: sampler、pruner、総resource budget、worker utilization
- 恐れていること: 初期成績と最終成績の不一致、遅咲きtrialの誤prune

ASHAはasynchronousにpromotion / stoppingを進め、worker待ちを減らす実装strategyです。samplerとprunerは別の役割として記録します。

## まず確認すること

| 項目 | 確認内容 |
|---|---|
| resource | epoch、sample数、simulation精度など段階的に増やせるか |
| intermediate metric | 最終性能をある程度予測するか |
| checkpoint | trialを継続・再開できるか |
| workers | asynchronous実行に価値があるか |
| fairness | trialごとのresourceを比較できるか |
| noise | 早い段階の揺れで良いtrialを落とさないか |

途中metricが最終目的とほぼ無関係なら、早期停止は探索を速くするどころかsystematic biasを作ります。

## 仕組み

Successive Halvingでは、多数のconfigurationへ小resourceを与え、上位の一部だけを次のresource段階へ進めます。Hyperbandは初期trial数と最大resourceの異なる複数bracketを組み合わせます。

ASHAではtrial完了を待って同期せず、結果が届いた時点で継続可否を判断します。これにより異なる実行時間のtrialが混在する環境でworkerを使いやすくなります。

## 向く条件・避ける条件

向きやすい条件:

- training epochやsample数を段階的に増やせる
- intermediate metricと最終metricに相関がある
- 多数workerでtrialを並列実行する
- 一trialを最後まで回すcostが高い

避ける条件:

- 中間結果を観測できないatomicな実験
- 遅れて急改善するtrialが多い
- checkpoint / resumeができず再計算costが大きい
- 最終性能の僅かな差に厳密certificateが必要

## 診断値

見る値:

- resource段階ごとのtrial数
- pruned / completed trial比率
- intermediateとfinal rankingの相関
- worker utilization
- checkpoint overhead
- best final metricと総resource
- seed / bracket間のばらつき

中間metric、最終metric、pruned判定、総resourceは別々に記録します。
pruned trialが少ないことだけでは、resource allocationが良いとは判断できません。

## うまくいったサインと切替サイン

- pruned trialが後から良いと判明 → pruningを弱める、grace periodを増やす
- worker idleが多い → asynchronous schedulingを確認
- checkpoint overheadが支配的 → resource粒度を粗くする
- intermediate metricが不安定 → smoothing、複数評価、別metricを検討
- search-space提案が弱い → TPEやBO samplerと組み合わせる

## Python

```python
import optuna


def objective(trial: optuna.Trial) -> float:
    rate = trial.suggest_float("rate", 1e-4, 1e-1, log=True)
    score = 10.0
    for step in range(20):
        score = score * (1.0 - min(rate * 5.0, 0.5)) + 0.01 * step
        trial.report(score, step)
        if trial.should_prune():
            raise optuna.TrialPruned()
    return score


pruner = optuna.pruners.HyperbandPruner(min_resource=1, max_resource=20, reduction_factor=3)
study = optuna.create_study(direction="minimize", pruner=pruner)
study.optimize(objective, n_trials=30)
print(len(study.trials), study.best_value)
```

この例の中間metricは説明用です。実データではprune判断と最終metricの関係を検証します。

## コラム: optimizerではなくresource allocator

Hyperband / ASHAはparameterをどう提案するかと、trialへどれだけresourceを与えるかを分けて考えます。Random、TPE、BOなどのsamplerと組み合わせられます。

[高価なblack-box・HPOの選び分け](#/learn/family.expensive-black-box)でTPEやGP-BOと役割を分けて確認してください。
