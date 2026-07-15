---
content_id: genetic-algorithm
kind: method
method_id: M_GENETIC_ALGORITHM
title_ja: 遺伝的アルゴリズム
title_en: Genetic Algorithm
summary: 個体の表現、selection、crossover、mutationを組み合わせ、離散・混合・black-box空間から良い候補を探索するpopulation法です。
source_ids: [S033, S040, S054]
prerequisites: [concept.derivative-free]
related_ids: [cma-es, differential-evolution, particle-swarm]
aliases: [/learn/genetic-algorithm]
status: published
last_reviewed: 2026-07-15
---

個体の表現、selection、crossover、mutationを組み合わせ、離散・混合・black-box空間から良い候補を探索するpopulation法です。

## 「GA」は一つの固定algorithmではない

性能を決める主要要素は、

- genotype / phenotypeの表現
- 初期population
- fitnessと制約違反の扱い
- parent selection
- crossover
- mutation
- elitism
- diversity維持

です。同じ「遺伝的アルゴリズム」という名前でも、表現とoperatorが違えば別の探索器と考えた方が安全です。

## 表現が最重要

たとえばscheduleを単純なbit列にすると、多くの個体が実行不能になる場合があります。次の選択肢を比較します。

- 常に可行となるencoding
- repair operator
- penalty
- feasibility-first selection
- decoderでphenotypeへ変換

operatorが問題構造を壊さないことが、汎用parameter調整より重要な場合があります。

## Python: 小さなbinary選択

```python
import random

VALUES = [8, 5, 6, 4, 7, 3]
WEIGHTS = [4, 3, 5, 2, 6, 1]
CAPACITY = 12
POPULATION_SIZE = 30
MUTATION_RATE = 0.05
random.seed(4)


def score(bits: list[int]) -> float:
    total_weight = sum(w * bit for w, bit in zip(WEIGHTS, bits, strict=True))
    total_value = sum(v * bit for v, bit in zip(VALUES, bits, strict=True))
    return float(total_value if total_weight <= CAPACITY else total_value - 20 * (total_weight - CAPACITY))


def mutate(bits: list[int]) -> list[int]:
    return [1 - bit if random.random() < MUTATION_RATE else bit for bit in bits]


population = [
    [random.randint(0, 1) for _ in VALUES]
    for _ in range(POPULATION_SIZE)
]

for _ in range(150):
    ranked = sorted(population, key=score, reverse=True)
    next_population = ranked[:4]
    while len(next_population) < POPULATION_SIZE:
        parent_a, parent_b = random.sample(ranked[:15], 2)
        cut = random.randrange(1, len(VALUES))
        child = parent_a[:cut] + parent_b[cut:]
        next_population.append(mutate(child))
    population = next_population

best = max(population, key=score)
print(best, score(best))
```

この例は教育用です。実務では、penaltyに依存した「高得点だがinfeasible」な解を最終出力しないよう、可行性を別に検証します。

## 診断値

- best / median fitness
- feasible fraction
- unique individual数
- genotype diversity
- elite占有率
- mutationによる改善率
- seed間の分散
- evaluation budget

## 向いている条件

- 離散・カテゴリ・混合変数を自然にencodingできる
- differentiabilityを期待できない
- evaluationを並列化できる
- 近傍が複雑で複数basinを探索したい
- 最適性証明より良い候補集合が重要

## 失敗・避ける条件

- premature convergenceでpopulationが同一化
- crossoverが可行構造を破壊
- penalty scaleがobjectiveを圧倒、または弱すぎる
- 評価が高価すぎてpopulationを維持できない
- 専用DP、flow、matching、CP-SATで強い構造を使える
- 単一seed・単一parameter設定だけで優劣を断定

::: note
GAを使う前に、問題固有の近傍探索、dynamic programming、constraint programmingで構造を直接使えないか確認します。
:::
