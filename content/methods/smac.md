---
content_id: smac
kind: method
method_id: M_SMAC_RF
title_ja: SMAC（random forest surrogate）
title_en: SMAC with Random Forest Surrogate
summary: SMACは、ガウス過程（Gaussian process）の代わりにランダムフォレスト（random forest）を予測用のsurrogateとして使う、逐次モデルベース最適化（sequential model-based optimization）です。カテゴリ変数（categorical）や条件付きparameterを含むsearch spaceを扱いやすい点に特徴があります。
source_ids: [S037, S059, S075]
prerequisites: []
related_ids: [bayesian-optimization, tpe, random-search, family.expensive-black-box]
aliases: [/learn/smac]
status: published
last_reviewed: 2026-07-18
---

SMACは、ガウス過程（Gaussian process）の代わりにランダムフォレスト（random forest）を予測用のsurrogateとして使う、逐次モデルベース最適化（sequential model-based optimization）です。カテゴリ変数（categorical）や条件付きparameterを含むsearch spaceを扱いやすい点に特徴があります。

## 何をsurrogateに使うか

[Bayesian Optimization](#/learn/bayesian-optimization)では、多くの場合、ガウス過程（Gaussian process）をsurrogateに使います。
SMAC（Sequential Model-based Algorithm Configuration）は、random forestをsurrogateとして使います。
評価したparameterと評価値の組は、runhistoryとして蓄積されます。
SMACはこの記録を使ってrandom forestを学習します。

random forestでは、各木の予測のばらつきから不確実性の目安を得られます。
そのため、Gaussian processと同じように、予測平均と不確実性を獲得関数（acquisition）に渡せます。
違いは、連続変数だけでなく、カテゴリ変数や条件付きparameterも木構造の分岐として扱いやすいことです。

## GP-BOとの使い分け

search spaceの形が、GP-BOとrandom forest surrogateのどちらを検討するかの手がかりになります。

- 連続変数が中心で次元が低〜中程度なら、kernelで距離を定義しやすいGaussian process系のBayesian Optimizationが候補になります。
- カテゴリ変数や条件付きparameterが多いalgorithm configurationやhyperparameter optimizationでは、木構造で分岐を表せるrandom forest系（SMAC）が候補になります。

優劣の一般順位ではありません。
search spaceをどちらが表現しやすいかで選び分けます。

## runhistoryとincumbentが持つ役割

SMACは、評価した点とその結果をrunhistoryに保存し続けます。
runhistoryはsurrogateの学習データ（data）であると同時に、途中経過を再現・再開するための記録でもあります。

これまでに評価した設定のうち、最も評価値がよいものをincumbentと呼びます。
incumbentはsurrogateの予測ではなく、実際の観測値から選ばれた候補です。
次に評価する候補は、acquisitionがsurrogateから選びます。
探索が進んでincumbentが更新されると、その後は更新されたbest-so-farを基準に進みます。

## 向いている条件

- カテゴリ変数（categorical）、整数、条件付きparameterが混在するalgorithm configuration
- 評価コストが高く、runhistoryを再利用する価値がある
- 連続変数だけの低次元search spaceに限られない
- 失敗したtrialやtimeoutを記録・活用したい

連続変数が中心の低次元search spaceで、kernelによる不確実性を直接解釈したい場合は[Gaussian-process BO](#/learn/bayesian-optimization)を検討します。
評価が安価で大量に並列実行できる場合は、[Random Search](#/learn/random-search)や[TPE](#/learn/tpe)との比較も有効です。

## Python

次はSMAC3で1変数のconfiguration spaceを作り、決定的な目的関数（deterministic objective function）を限られたtrial数で最小化する最小例です。

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

実装については、[SMAC3](https://automl.github.io/SMAC3/latest/)の公式documentationを参照してください。
search spaceの定義方法、facade（scenarioの種類）、runhistoryの保存形式は、利用するversionに対応する説明で確認します。

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

連続変数中心の低次元でGaussian processによる不確実性を直接扱いたい場合は、[Bayesian Optimization](#/learn/bayesian-optimization)を検討します。
条件付き空間で密度比を使う別のsurrogateは[TPE](#/learn/tpe)、何も仮定しないbaselineは[Random Search](#/learn/random-search)です。
高価なblack-box探索全体の選び分けは、[高価なblack-box・HPOの選び分け](#/learn/family.expensive-black-box)で確認できます。
