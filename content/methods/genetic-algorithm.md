---
content_id: genetic-algorithm
kind: method
method_id: M_GENETIC_ALGORITHM
title_ja: 遺伝的アルゴリズム
title_en: Genetic Algorithm
summary: 個体の表現と選択・交叉・突然変異を組み合わせる集団法です。離散・混合・ブラックボックス空間から良い候補を探索します。
source_ids: [S033, S040, S054]
prerequisites: [concept.derivative-free]
related_ids: [cma-es, differential-evolution, particle-swarm]
aliases: [/learn/genetic-algorithm]
status: published
last_reviewed: 2026-09-30
---

個体の表現と選択・交叉・突然変異を組み合わせる集団法です。離散・混合・ブラックボックス空間から良い候補を探索します。

## 30秒でつかむ

良い献立をいくつか残し、その組合せを入れ替えたり一品だけ変えたりして、新しい献立を試します。遺伝的アルゴリズムも候補の表現と作り方を設計します。

- 見るもの: 候補の目的値と可行性
- 動かすもの: 次に試す候補と探索の状態
- 前進の判断: 固定した評価予算で良い候補が残ること

## 一手の意味

一世代では親を選び、交叉と突然変異から子を作ります。その後で残す個体を選びます。

$$
P_{k+1}=\operatorname{select}\!\left(P_k\cup\operatorname{mutate}(\operatorname{cross}(P_k))\right)
$$

$P_k$ は個体の集団です。この式は操作の順序を表し、固定された唯一の実装を指定するものではありません。

### 「GA」は一つの固定アルゴリズムではない

性能を決める主要要素は、

- 遺伝子型と表現型の表現
- 初期集団
- 適応度と制約違反の扱い
- 親の選択
- 交叉
- 突然変異
- エリート保存
- 多様性維持

です。同じ「遺伝的アルゴリズム」という名前でも、表現と操作が違えば別の探索器と考えた方が安全です。

### 表現が最重要

たとえば予定を単純なビット列にすると、多くの個体が実行不能になる場合があります。次の選択肢を比較します。

- 常に可行となる符号化
- 修復操作
- 罰則
- 可行性を優先する選択
- 復号器で表現型へ変換

操作が問題構造を壊さないことが、汎用パラメータ調整より重要な場合があります。

## 小さな例

Python節のナップサック例は、6品目から容量12以内の品目を選びます。
先頭から3世代の最良得点を記録して、集団が更新される様子を確かめます。

| 世代 | 最良個体のビット列 | 最良得点 |
|---|---|---:|
| 1 | 1,0,1,1,0,1 | 21 |
| 2 | 1,0,1,1,0,1 | 21 |
| 3 | 1,0,1,1,0,1 | 21 |

この個体の重さは12で、容量を満たします。

最良得点が止まっていても、集団内の他の候補は変化し得ます。
得点と可行性を別々に確かめます。

## 向く条件・避ける条件

### 向いている条件

- 離散・カテゴリ・混合変数を自然に符号化できる
- 微分可能性を期待できない
- 評価を並列化できる
- 近傍が複雑で複数谷を探索したい
- 最適性証明より良い候補集合が重要

### 避ける／切り替える条件

- 早期収束で集団が同一化
- 交叉が可行構造を破壊
- 罰則の尺度が目的を圧倒、または弱すぎる
- 評価が高価すぎて集団を維持できない
- 専用DP、フロー、マッチング、CP-SATで強い構造を使える
- 一つの乱数種・単一パラメータ設定だけで優劣を断定

::: note
GAを使う前に、問題固有の近傍探索や動的計画法を確認します。制約プログラミングで構造を直接使えないかも確認します。
:::

## Python

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

この例は教育用です。実務では、罰則に依存した「高得点だが実行不能」な解を最終出力しないよう、可行性を別に検証します。

## 診断値

- 最良 / 中央値適応度
- 可行な候補の割合
- 異なる個体数
- 遺伝子型の多様性
- エリート占有率
- 突然変異による改善率
- 乱数種間の分散
- 評価予算

## 失敗・切替の兆候

- 集団が同じ個体ばかりになる → 早期収束を疑い、表現と突然変異率を見直します。
- 高得点なのに制約違反が残る → 罰則の設計を確認し、最終候補の可行性を別に検査します。
- 評価予算で集団を維持できない → [Bayesian Optimization](#/learn/bayesian-optimization)も比較します。

## 次に読む

- [関連する手法の記事](#/learn/cma-es)：一手の意味と選び分けを比べます。

- [この手法を使う問題の定式化](#/formulations/PA032)：決定変数と目的を確認します。
