---
content_id: pbt
kind: method
method_id: M_PBT
title_ja: Population Based Training
title_en: Population-Based Training
summary: 学習を止めずに、並走するworker集団の途中成績を見て、弱いworkerが強いworkerのweightをコピーし、hyperparameterを摂動するhyperparameter optimization手法です。
source_ids: [S038, S069]
prerequisites: []
related_ids: [hyperband-asha, random-search, family.expensive-black-box]
status: published
last_reviewed: 2026-07-17
---

学習を止めずに、並走するworker集団の途中成績を見て、弱いworkerが強いworkerのweightをコピーし、hyperparameterを摂動するhyperparameter optimization手法です。

## 何を並走させているか

PBTは複数のworkerを同時に学習させます。各workerは自分のweightとhyperparameterを持ち、一定間隔（stepやepoch）ごとにvalidation metricで成績を評価されます。random searchやHyperbandのように、1つのworkerが最初から最後まで固定のhyperparameterで学習を続けるわけではありません。populationとして並走させ、途中経過を互いに比較しながら学習を進めます。

## exploitとexploreが何をしているか

評価のたびに、成績が悪いworkerは次の2つの操作を受けます。

- **exploit**: 成績が良いworkerのweight（および必要ならoptimizer state）をコピーする
- **explore**: コピーしたhyperparameterに摂動を加える、またはsearch spaceから再sampleする

学習を中断せずにこの継承と摂動を繰り返すため、1つのworkerの系譜（lineage）は、学習の前半と後半で異なるhyperparameterを経験します。つまりPBTが探索しているのは、固定のhyperparameter setではなく、学習の進行に応じてhyperparameterを変化させる**schedule**です。

## 通常のHPOと結果の解釈が違う点

random searchやHyperbandは、1つのtrialに1つの固定hyperparameter setを割り当て、「このconfigurationがどれだけ良いか」を比較します。PBTの結果はこれとは性質が異なります。最終的に残ったworkerの成績は、ある1つのhyperparameter setの成績ではなく、途中で何度も継承・摂動を経た系譜全体が生んだ結果です。そのため「良いhyperparameterが見つかった」と言うより、「良いhyperparameter scheduleを持つ系譜が見つかった」と解釈するほうが正確です。

この違いは再現性にも影響します。最終hyperparameterだけを記録しても、そこに至った系譜（いつ、誰から、どのweightとhyperparameterを継承したか）を再現できなければ、同じ結果を再現できません。実務ではpopulation全体の履歴（exploit元、explore後の値、評価時点のmetric）を記録します。

## 向いている条件

- 長時間の学習で、learning rateやregularizationなどのhyperparameterを学習の進行に応じて変化させる価値がある
- populationを同時に走らせるだけの並列resourceがある
- validation metricを一定間隔で安価に計算できる
- workerの間でweightを転用できる（同一architecture）

避ける／切り替える条件:

- 評価や学習が安価で、大量trialを単純に並列実行できる → [Random Search](#/learn/random-search)や[Hyperband / ASHA](#/learn/hyperband-asha)で十分な場合
- populationを同時に走らせる並列resourceがない
- 固定configの比較として単純な再現性・監査性を優先したい
- weightの継承が意味を持たない設定（architecture自体を探索するなど）

## Python

次は学習器そのものを単純なscore関数に置き換え、下位workerが上位workerの状態を継承してlearning rateを摂動する1回分のexploit / exploreを再現します。

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

実務ではこの操作を学習intervalごとに繰り返し、weight、optimizer state、系譜をcheckpointへ保存します。実装は[Ray Tune](https://docs.ray.io/en/latest/tune/index.html)のPopulationBasedTrainingの公式referenceで、利用versionに対応するAPIとcheckpoint挙動を確認します。

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

途中成績で候補を打ち切りbudgetを再配分する考え方は[Hyperband / ASHA](#/learn/hyperband-asha)、何も仮定しないbaselineは[Random Search](#/learn/random-search)で確認できます。高価なblack-box評価全体の選び分けは[高価なblack-box・HPOの選び分け](#/learn/family.expensive-black-box)にまとめています。
