---
content_id: smac
kind: method
method_id: M_SMAC_RF
title_ja: SMAC（random forest surrogate）
title_en: SMAC with Random Forest Surrogate
summary: Gaussian processの代わりにrandom forestをsurrogateに使い、categorical・条件付きparameterを含むsearch spaceを扱いやすくしたsequential model-based optimizationです。
source_ids: [S037, S059, S075]
prerequisites: []
related_ids: [bayesian-optimization, tpe, random-search, family.expensive-black-box]
aliases: [/learn/smac]
status: published
last_reviewed: 2026-07-17
---

Gaussian processの代わりにrandom forestをsurrogateに使い、categorical・条件付きparameterを含むsearch spaceを扱いやすくしたsequential model-based optimizationです。

## 何をsurrogateにしているか

[Bayesian Optimization](#/learn/bayesian-optimization)は多くの場合Gaussian processをsurrogateに使いますが、SMAC（Sequential Model-based Algorithm Configuration）はrandom forestをsurrogateとして使います。観測済みのparameterと評価値の組をrunhistoryとして蓄積し、random forestをそのrunhistoryで学習します。

random forestは各木の予測のばらつきから不確実性の目安を得られるため、Gaussian processと同様に予測平均と不確実性の両方をacquisitionへ渡せます。決定的な違いは、random forestが連続変数だけでなくcategorical変数や、あるparameterが別のparameterの値によってのみ意味を持つ条件付きparameterを、木構造の分岐として自然に扱える点です。

## GP-BOとの使い分け

search spaceの形が、GP-BOとrandom forest surrogateのどちらを検討するかの主な手がかりです。

- 連続変数中心で次元が低〜中程度なら、kernelによる距離の定義が自然なGaussian process系のBayesian Optimizationが選択肢になります。
- categorical変数や条件付きparameterが多く混在するalgorithm configurationやhyperparameter optimizationでは、木構造で分岐を表現できるrandom forest系（SMAC）が選択肢になります。

どちらも「良い手法」という一般順位ではなく、search spaceの表現しやすさで選び分けます。

## runhistoryとincumbentが持つ役割

SMACは評価した点とその結果をrunhistoryとして保存し続けます。runhistoryはsurrogateの学習dataであると同時に、途中経過を再現・再開するための記録でもあります。

これまでの評価の中で最良の設定はincumbentと呼ばれます。incumbentはsurrogateの予測ではなく、実際に評価された観測値に基づく候補です。次に評価する候補はacquisitionによってsurrogateから選ばれますが、探索の過程でincumbentが更新されるたびに、以降の探索はその時点のbest-so-farを基準に進みます。

## 向いている条件

- categorical・整数・条件付きparameterが混在するalgorithm configuration
- 評価コストが高く、runhistoryを再利用する価値がある
- 連続変数だけの低次元search spaceに限定されない
- 失敗trialやtimeoutを記録・活用したい

連続変数中心の低次元search spaceで、kernelによる不確実性をそのまま解釈したい場合は[Gaussian-process BO](#/learn/bayesian-optimization)を検討します。評価が安価で大量に並列実行できる場合は[Random Search](#/learn/random-search)や[TPE](#/learn/tpe)との比較も有効です。

## Python

次はSMAC3で1変数のconfiguration spaceを作り、deterministicな目的関数を限られたtrial数で最小化する最小例です。

```python
from ConfigSpace import Configuration, ConfigurationSpace, Float
from smac import HyperparameterOptimizationFacade, Scenario

space = ConfigurationSpace(
    space={"x": Float("x", bounds=(-5.0, 5.0), default=0.0)}
)


def objective(config: Configuration, seed: int = 0) -> float:
    del seed
    return float((config["x"] - 1.5) ** 2)


scenario = Scenario(space, deterministic=True, n_trials=20)
smac = HyperparameterOptimizationFacade(scenario, objective, overwrite=True)
incumbent = smac.optimize()

print(dict(incumbent), objective(incumbent))
```

実装は[SMAC3](https://automl.github.io/SMAC3/latest/)の公式documentationを参照し、search spaceの定義方法、facade（scenarioの種類）、runhistoryの保存形式は利用versionに対応する説明で確認します。

## 診断値

- best_so_far（incumbentの評価値）
- surrogate_error（random forestの予測誤差）
- calibration（不確実性の較正）
- acquisition_value
- failed_trials数

## 失敗・切替の兆候

- surrogateのcross-validation誤差が大きく改善しない
- 不確実性の較正が悪く、acquisitionが同じ領域ばかり提案する
- 条件付きparameterの表現が誤っており、無効な組み合わせが提案され続ける
- 評価が安価すぎてsurrogate構築のoverheadが見合わない
- runhistoryが少なすぎてrandom forestの分散推定が不安定

連続低次元でGaussian processによる不確実性を直接扱いたい場合は[Bayesian Optimization](#/learn/bayesian-optimization)、条件付き空間で密度比を使う別のsurrogateは[TPE](#/learn/tpe)、何も仮定しないbaselineは[Random Search](#/learn/random-search)、高価なblack-box探索全体の選び分けは[高価なblack-box・HPOの選び分け](#/learn/family.expensive-black-box)で確認できます。
