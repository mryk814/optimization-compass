---
content_id: simulated-annealing
kind: method
method_id: M_SIMULATED_ANNEALING
title_ja: Simulated Annealing
title_en: Simulated Annealing
summary: 温度parameterに応じて悪化する移動も確率的に受理し、局所解からの脱出を狙う確率的大域探索heuristicです。
source_ids: [S009, S007, S008]
prerequisites: []
related_ids: [dual-annealing, basin-hopping, family.global-search]
status: published
last_reviewed: 2026-07-26
---

温度parameterに応じて悪化する移動も確率的に受理し、局所解からの脱出を狙う確率的大域探索heuristicです。

## 何を確率的に受理しているか

通常の局所法は改善する移動だけを採用します。
Simulated Annealingは、現在点 $x$ から候補点 $x'$ を作った後、目的値が悪化しても一定確率で採用します。
よく使われる受理確率はMetropolis型です。

$$
P(\text{accept}) = \min\left(1, \exp\left(-\frac{f(x') - f(x)}{T}\right)\right)
$$

$f(x') \le f(x)$ なら確率1で採用します。
悪化する場合でも、差 $f(x') - f(x)$ が小さいほど、また温度 $T$ が高いほど採用されやすくなります。
$T$ を反復とともに下げる規則をcooling scheduleと呼びます。

## 温度が挙動をどう変えるか

温度が高いと、悪化移動を受理して広い領域のbasinへ移れます。
温度が低いと、改善移動を中心に受理する局所法へ近づきます。

ここで、探索中の`current`と、これまでの最良値`best-so-far`を分けて見ます。
次の固定実行では、橙の`current`が上昇しても、青緑の`best-so-far`は悪化しません。

![1次元Rastrigin関数を初期点3.5から固定seedで400反復探索したSimulated Annealingの実行結果。上段は受理した状態が複数のbasinを横断する様子を示す。下段では橙の現在値が何度も上昇する一方、青緑の最良値は32.25から0.00076へ単調に改善する。受理65回のうち32回は悪化移動で、最初の100反復に18回、最後の100反復には1回だけ現れる。](./media/simulated-annealing-execution.svg "固定1次元Rastrigin、seed 7、初期温度5.0、幾何冷却0.985のpure Python実行です。別seed、高次元、別schedule、Simulated Annealing一般の性能や大域最適性は示しません。")

このrunでは、受理した65 moveのうち32 moveが悪化でした。
そのうち18 moveは最初の100反復、1 moveだけが最後の100反復に現れます。
温度が下がるにつれて、探索から絞り込みへ重心が移った結果です。

> 固定した1次元Rastrigin、seed 7の教材実行です。
> 最良目的値は`32.25 → 0.00076`ですが、最適性証明ではありません。
> 別seed、高次元、別scheduleで同じ結果になることも保証しません。

cooling scheduleが速すぎると、他のbasinへ移る前に探索が固まります。
遅すぎると、評価予算を使い切っても探索が絞れません。
温度の下げ方とrestart（re-annealing）の有無は、実装ごとに記録すべきparameterです。

## 保証の弱さ

Simulated Annealingはheuristicであり、有限回の実行で大域最適性を証明する手法ではありません。
理論上は無限回・十分遅い冷却で大域最適へ収束するという結果がありますが、実務の有限budgetにはそのまま適用できません。
bounded低次元で決定的な網羅性を持たせたい場合は、[SHGO](#/learn/shgo)や[DIRECT](#/learn/direct-global)のような領域分割型が別の選択肢になります。

SciPyには古典的なSimulated Annealingの直接実装はなく、後継として[`scipy.optimize.dual_annealing`](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.dual_annealing.html)が提供されています。
`dual_annealing`はvisiting distributionと局所探索を組み合わせた発展形です。

## 向いている条件

- 低〜中次元のbounded連続問題
- 目的関数が多峰で複数のbasinが存在する
- 評価予算に余裕があり、確率的探索を許容できる
- 局所法だけでは初期点依存が強すぎる

## 避ける／切り替える条件

- 高次元かつ一評価が高価で構造的な手がかりがない
- 局所解で十分であり、大域探索のcostが見合わない
- 大域最適性の証明が必須な用途
- 再現可能な単一runの結果が求められる（seed依存が大きいため）

## Python

```python
import math
import random


def rastrigin(x: float) -> float:
    return 10.0 + x * x - 10.0 * math.cos(2.0 * math.pi * x)


def anneal(
    x0: float = 3.5,
    n_iter: int = 400,
    t0: float = 5.0,
    cooling_rate: float = 0.985,
    step_scale: float = 0.5,
    seed: int = 7,
) -> tuple[float, float, list[tuple[int, float, float, float, bool]]]:
    rng = random.Random(seed)
    x = x0
    f_x = rastrigin(x)
    best_x = x
    best_f = f_x
    temperature = t0
    history = [(0, f_x, best_f, temperature, False)]

    for iteration in range(1, n_iter + 1):
        step = rng.gauss(0.0, step_scale)
        candidate = min(5.12, max(-5.12, x + step))
        f_candidate = rastrigin(candidate)
        delta = f_candidate - f_x
        accepted = delta <= 0.0 or rng.random() < math.exp(-delta / temperature)
        accepted_worsening = accepted and delta > 0.0
        if accepted:
            x, f_x = candidate, f_candidate
            if f_x < best_f:
                best_x, best_f = x, f_x
        history.append((iteration, f_x, best_f, temperature, accepted_worsening))
        temperature *= cooling_rate

    return best_x, best_f, history


best_x, best_f, history = anneal()
accepted_worse = sum(row[4] for row in history)
print(f"best_x={best_x:.6f}, best_f={best_f:.6f}")
print(f"accepted worsening moves={accepted_worse}")
```

```text
best_x=-0.001963, best_f=0.000765
accepted worsening moves=32
```

`history`の`current objective`と`best-so-far`を別々にplotしてください。
`cooling_rate`や`step_scale`を変えると、受理回数と改善curveが変わります。

## 診断値

- best-so-far objective
- diversity（探索している点群の散らばり）
- coverage（探索領域のどこまで到達したか）
- local refinement success（低温段階で改善が続いているか）

## 失敗・切替の兆候

- 評価予算を消費してもincumbentがほとんど改善しない
- 探索点群の多様性が早期に失われ、同じbasin付近に留まる
- 悪化移動の受理率がほぼ0または1のまま変化しない
- 異なるseedで得られる解が大きくばらつく

::: warning
「Simulated Annealingを実行した」だけでは結果の再現条件として不十分です。
初期点とseedを記録します。
cooling scheduleとstep sizeも残してください。
:::

## 次に読む

- 発展したvisiting distributionとlocal search: [Dual Annealing](#/learn/dual-annealing)
- ランダム摂動と局所法の交互実行: [Basin Hopping](#/learn/basin-hopping)
- 大域探索全体の選び分け: [大域探索・多峰性問題の選び分け](#/learn/family.global-search)
