---
content_id: pbt
kind: method
method_id: M_PBT
title_ja: Population Based Training
title_en: Population-Based Training
summary: 並走するworkerの途中成績を比較し、良いworkerの学習状態を継承してhyperparameterを変える継続学習型HPOです。
source_ids: [S038, S069]
prerequisites: []
related_ids: [hyperband-asha, random-search, family.expensive-black-box]
status: published
last_reviewed: 2026-07-24
---

並走するworkerの途中成績を比較し、良いworkerの学習状態を継承してhyperparameterを変える継続学習型HPOです。

## 30秒でつかむ

PBTは、固定したconfigurationを一つずつ完走させる方法ではありません。
**学習途中のworkerを比較し、良い系譜を継承しながらhyperparameter scheduleを変えます。**

- 見ているもの: validation metric、worker state、hyperparameter、lineage
- 動かしているもの: weight、optimizer state、hyperparameterの摂動
- 前進の判断: 同じtotal training budgetで、良い系譜が残り続けるか
- 別に確認するもの: worker間のresource利用率、exploit / explore頻度、再現性
- 恐れていること: population collapse、誤った継承、系譜の欠落、noiseへの過反応

最終workerのhyperparameterだけでは、結果を再現する情報になりません。

## まず確認すること

| 項目 | 確認内容 |
|---|---|
| worker | 同じarchitectureでweightを継承できるか |
| metric | 一定間隔でvalidationできるか |
| interval | exploit / exploreの頻度が学習速度に合うか |
| budget | populationと学習時間を同じ条件で比較できるか |
| lineage | source、継承時点、摂動後の値を保存できるか |

## 何を並走させているか

PBTは複数のworkerを同時に学習させます。
各workerは、自分のweightとhyperparameterを持ちます。
一定のstepやepochごとにvalidation metricを測り、worker間の途中成績を比較します。

random searchやHyperbandでは、1つのworkerが固定のhyperparameterで学習を続けます。
PBTは途中経過を比較し、学習状態をworker間で受け渡します。

## exploitとexploreが何をしているか

1回の更新loopでは、何を保ち、何を変えたかを順番に追います。

1. **学習**: 各workerを同じintervalだけ進める
2. **評価**: validation metricで途中成績を比較する
3. **exploit**: 下位workerへ上位workerのweightと、必要ならoptimizer stateをコピーする
4. **explore・記録**: hyperparameterを摂動または再sampleし、継承元と変更値を残す

このloopを繰り返すと、1つのworkerの系譜（lineage）が途中で枝分かれします。
学習の前半と後半で、異なるhyperparameterを経験する場合もあります。
PBTが探索する対象は、固定のhyperparameter setではありません。
学習の進行に応じて値を変える**hyperparameter schedule**です。

## 通常のHPOと結果の解釈が違う点

random searchやHyperbandは、trialごとに固定のhyperparameter setを割り当てます。
そこで比べるのは「このconfigurationがどれだけ良いか」です。

PBTで最後に残る成績は、継承と摂動を経た系譜全体の結果です。
したがって「良いhyperparameter set」ではなく、「良いscheduleを持つ系譜」を見つけたと解釈します。

最終hyperparameterだけでは、この結果を再現できません。
いつ、どのworkerから、どの状態を継承したかも必要です。
population全体について、exploit元／explore後の値／評価時点のmetricを記録します。

## 向いている条件

- 長時間の学習で、learning rateやregularizationなどのhyperparameterを学習の進行に応じて変化させる価値がある
- populationを同時に走らせるだけの並列resourceがある
- validation metricを一定間隔で安価に計算できる
- workerの間でweightを転用できる（同一architecture）

## 避ける／切り替える条件

- 評価や学習が安価で、大量trialを単純に並列実行できる → [Random Search](#/learn/random-search)や[Hyperband / ASHA](#/learn/hyperband-asha)で十分な場合
- populationを同時に走らせる並列resourceがない
- 固定configの比較として単純な再現性・監査性を優先したい
- weightの継承が意味を持たない設定（architecture自体を探索するなど）

## Python

次の例では、学習器を単純なscore関数に置き換えます。
下位workerが上位workerを継承し、learning rateを摂動する1回の更新を確認します。

```python
from dataclasses import dataclass, replace
import random


@dataclass(frozen=True)
class Worker:
    worker_id: int
    weight: float
    learning_rate: float


def validation_score(worker: Worker) -> float:
    return -((worker.weight - 1.0) ** 2) - 0.1 * worker.learning_rate


rng = random.Random(7)
population = [
    Worker(worker_id=index, weight=rng.uniform(-1.0, 2.0), learning_rate=0.1)
    for index in range(4)
]
ranked = sorted(population, key=validation_score, reverse=True)
source = ranked[0]
target = ranked[-1]

# exploit: 上位workerの状態を継承する
# explore: 継承したhyperparameterを少し変える
replacement = replace(
    source,
    worker_id=target.worker_id,
    learning_rate=source.learning_rate * rng.choice([0.8, 1.2]),
)
population[target.worker_id] = replacement

print([(worker.worker_id, validation_score(worker)) for worker in population])
```

実務では、この操作を学習intervalごとに繰り返します。
weight／optimizer state／系譜はcheckpointへ保存します。
実装時は[Ray TuneのPBT guide](https://docs.ray.io/en/latest/tune/examples/pbt_guide.html)で、利用versionのAPIとcheckpoint挙動を確認します。

## 診断値

- best-so-far（系譜全体での最良validation metric）
- population内のhyperparameter分散（多様性が早期に失われていないか）
- exploit発生頻度と、exploit元・exploit先の系譜記録
- explore後のhyperparameterが実際に成績を改善したか
- worker間のidle time・resource利用率

## 失敗・切替の兆候

- populationが早期に同じhyperparameterへ収束し、多様性を失う（population collapse）
- exploitが頻発しすぎて学習が不安定になる
- explore時の摂動が大きすぎてweightの継承価値を壊す
- validation metricがnoiseに支配され、誤ったworkerをexploitしてしまう
- 系譜の記録が不完全で、最終結果を再現できない

## 次に読む

途中成績で候補を打ち切りbudgetを再配分する考え方は[Hyperband / ASHA](#/learn/hyperband-asha)、何も仮定しないbaselineは[Random Search](#/learn/random-search)で確認できます。高価なblack-box評価全体の選び分けは[高価なblack-box・HPOの選び分け](#/learn/family.expensive-black-box)にまとめています。
