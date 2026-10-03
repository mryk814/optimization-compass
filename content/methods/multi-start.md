---
content_id: multi-start
kind: method
method_id: M_MULTISTART
title_ja: Multi-start局所最適化
title_en: Multi-start Local Optimization
summary: 複数の初期点から局所法を独立に実行し、最良の解を採用する最も単純な大域化戦略です。
source_ids: [S056, S007, S008]
prerequisites: []
related_ids: [basin-hopping, bfgs, family.global-search]
status: published
last_reviewed: 2026-09-30
---

複数の初期点から局所法を独立に実行し、最良の解を採用する最も単純な大域化戦略です。

## 30秒でつかむ

山を下る出発地点をいくつか変え、到着した谷の中から低いものを選ぶ感覚です。

- **見るもの**：各初期点から到達した局所解と目的値
- **動かすもの**：初期点と局所求解の回数
- **前進の判断**：最良値の改善と、異なる谷への到達

Multi-startは、探索領域から複数の初期点 $x_0^{(1)}, \dots, x_0^{(k)}$ を選び、それぞれから同じ局所法（BFGSなど）を独立に実行します。得られた局所解 $x^{*(1)}, \dots, x^{*(k)}$ のうち目的値が最良のものを採用します。

各実行は互いに依存しないため、局所法そのものの収束理論をそのまま利用できます。Multi-startが追加しているのは「初期点をどう選ぶか」と「複数結果からどう選ぶか」だけです。

## 一手の意味

第 $j$ の初期点を局所求解 $L$ に渡し、これまでの最良値を更新します。

$$
x^{*(j)}=L(x_0^{(j)}),\qquad
b_j=\min\{b_{j-1},f(x^{*(j)})\}.
$$

制約付き問題では、可行な候補を比較する条件も必要です。

### 初期点をどう選ぶか

初期点標本化方法によって領域の網羅のされ方が変わります。

- 一様標本化: 上下限内から独立に一様分布で選ぶ。実装が単純で並列化しやすい
- ラテン超方格による標本化: 各次元を層別してから組み合わせ、少ない点数でも領域全体をより均等に覆う
- 既知の候補点: 過去の実行結果や定義域知識から初期点を追加する

初期点の数を増やすほど多くの谷に到達しやすくなりますが、局所法の実行回数もその分だけ増えます。

### 並列性と重複評価

各実行が独立であることは、multi-startを並列計算と相性の良い戦略にします。一方で、複数の初期点が同じ谷へ収束すると、その分の局所法実行は重複した情報しか得られません。

- 前提: 局所法が十分に速く、多数回の実行が評価予算内で収まる
- 無駄: 同じ谷へ複数回到達すると、その実行は新しい情報を追加しない
- 診断的価値: 「同じ解に何回到達したか」を数えると、領域内の局所解の数や到達しやすさをおおまかに把握できる

一評価あたりが非常に高価な問題では、局所法の実行回数そのものが制約になり、multi-startの初期点数を絞る必要があります。有界低次元で領域分割による網羅性を求めるなら、[SHGO](#/learn/shgo)や[DIRECT](#/learn/direct-global)も候補です。

## 小さな例

Python例の2変数Rastrigin関数を、乱数種7で実行しました。
25初期点のうち、最初の3本の局所求解です。

| 求解 | 初期点 | 到達点 | 目的値 |
|---|---|---|---:|
| 1本目 | $(1.2810,4.0675)$ | $(0.9950,3.9798)$ | 16.9142 |
| 2本目 | $(2.8230,-2.8139)$ | $(2.9849,-2.9849)$ | 17.9092 |
| 3本目 | $(-2.0463,3.8252)$ | $(-1.9899,3.9798)$ | 19.8991 |

3本目までの最良値は1本目の16.9142です。
独立の局所求解を増やしても、毎回最良値が改善するわけではありません。
25本では23個の異なる到達点が得られ、重複は2本でした。
最良値は約0.9950で、この予算では原点の目的値0へ届きませんでした。

## 向く条件・避ける条件

### 向いている条件

- 局所法（BFGSなど）が1回の実行として十分に速い
- 目的関数が多峰で、初期点依存が強く出る
- 並列実行の環境があり、複数回の局所法実行を並べられる
- 大域最適性の証明よりも、実用的に良い候補を複数見つけたい

### 避ける／切り替える条件

- 1回の局所法実行自体が高価で、多数回の実行が予算を超える
- 単峰性が既知で、単一の初期点で十分な問題
- 大域最適性の証明が必須な用途
- 初期点数を増やしても新しい谷への到達が増えない（重複ばかりになる）

## Python

```python
import numpy as np
from scipy.optimize import minimize


def rastrigin(x: np.ndarray) -> float:
    return float(10.0 * len(x) + np.sum(x**2 - 10.0 * np.cos(2.0 * np.pi * x)))


rng = np.random.default_rng(7)
n_starts = 25
bounds = (-5.12, 5.12)

best_x: np.ndarray | None = None
best_f = np.inf
seen_solutions: list[np.ndarray] = []
duplicate_count = 0

for _ in range(n_starts):
    x0 = rng.uniform(bounds[0], bounds[1], size=2)
    result = minimize(rastrigin, x0=x0, method="BFGS")

    is_duplicate = any(
        np.linalg.norm(result.x - prior) < 1e-3 for prior in seen_solutions
    )
    if is_duplicate:
        duplicate_count += 1
    else:
        seen_solutions.append(result.x)

    if result.fun < best_f:
        best_x, best_f = result.x, result.fun

print(best_x, best_f)
print("distinct solutions:", len(seen_solutions), "duplicates:", duplicate_count)
```

`distinct solutions`が初期点数より大幅に少なければ、同じ谷へ繰り返し到達していることを意味します。局所法自体の設定は[BFGS](#/learn/bfgs)の記事も参照してください。

## 診断値

- これまでの最良値目的関数
- 多様性（到達した局所解同士の散らばり）
- 網羅率（初期点標本化全体で探索領域をどこまで覆ったか）
- 局所求解の成功（各局所法実行が収束条件を満たしたか）

## 失敗・切替の兆候

- 初期点数を増やしても新しい谷への到達が増えず、重複ばかりが増える
- 評価予算を消費してもこれまでの最良値がほとんど改善しない
- 一部の初期点で局所法自体が収束条件を満たさない
- 高次元化により初期点標本化密度が急速に不足する

## 次に読む

[微分なし大域探索](#/formulations/PA013)で、局所解を集める戦略の限界を確認します。

複数の候補点からの局所探索という考え方をランダムな飛び移りへ発展させたものは[Basin Hopping](#/learn/basin-hopping)、大域探索全体の選び分けは[大域探索・多峰性問題の選び分け](#/learn/family.global-search)で確認できます。
