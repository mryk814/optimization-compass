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
last_reviewed: 2026-07-16
---

温度parameterに応じて悪化する移動も確率的に受理し、局所解からの脱出を狙う確率的大域探索heuristicです。

## 何を確率的に受理しているか

通常の局所法は改善する移動だけを採用します。Simulated Annealingは、現在点 $x$ から候補点 $x'$ を作った後、目的値が悪化しても一定確率で採用します。よく使われる受理確率はMetropolis型です。

$$
P(\text{accept}) = \min\left(1, \exp\left(-\frac{f(x') - f(x)}{T}\right)\right)
$$

$f(x') \le f(x)$ なら確率1で採用します。悪化する場合でも、差 $f(x') - f(x)$ が小さいほど、また温度 $T$ が高いほど採用されやすくなります。$T$ を反復とともに下げる規則をcooling scheduleと呼びます。

## 温度が挙動をどう変えるか

温度が高いときは悪化移動をほぼ自由に受理するため、探索はrandom walkに近づき、広い領域のbasinへ移動できます。温度が低いときは改善移動しか事実上受理せず、局所法に近い挙動になります。

- 高温段階: 多様なbasinへの到達を優先し、incumbentの改善は保証しない
- 低温段階: 見つけたbasin内を絞り込み、局所的な精緻化を行う
- cooling scheduleが速すぎる: 局所解へ早期収束し、他のbasinを見逃す
- cooling scheduleが遅すぎる: 評価予算を使い切っても収束しない

温度の下げ方（線形、幾何、対数など）とrestart（re-annealing）の有無は実装ごとに異なるparameterです。

## 保証の弱さ

Simulated Annealingはheuristicであり、有限回の実行で大域最適性を証明する手法ではありません。理論上は無限回・十分遅い冷却で大域最適へ収束するという結果がありますが、実務で使う有限budgetの設定にはそのまま適用できません。bounded低次元で決定的な網羅性を持たせたい場合は、[SHGO](#/learn/shgo)や[DIRECT](#/learn/direct-global)のような領域分割型の手法が別の選択肢になります。

SciPyには古典的なSimulated Annealingの直接実装はなく、後継として[`scipy.optimize.dual_annealing`](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.dual_annealing.html)が提供されています。dual_annealingはvisiting distributionと局所探索を組み合わせた発展形で、詳細は[Dual Annealing](#/learn/dual-annealing)を確認してください。

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
import numpy as np


def rastrigin(x: np.ndarray) -> float:
    return float(10.0 * len(x) + np.sum(x**2 - 10.0 * np.cos(2.0 * np.pi * x)))


def anneal(
    x0: np.ndarray,
    n_iter: int = 2_000,
    t0: float = 5.0,
    cooling_rate: float = 0.995,
    step_scale: float = 0.5,
    seed: int = 7,
) -> tuple[np.ndarray, float]:
    rng = np.random.default_rng(seed)
    x = x0.copy()
    f_x = rastrigin(x)
    best_x, best_f = x.copy(), f_x
    temperature = t0

    for _ in range(n_iter):
        candidate = x + rng.normal(scale=step_scale, size=x.shape)
        f_candidate = rastrigin(candidate)
        delta = f_candidate - f_x
        if delta <= 0.0 or rng.random() < np.exp(-delta / temperature):
            x, f_x = candidate, f_candidate
            if f_x < best_f:
                best_x, best_f = x.copy(), f_x
        temperature *= cooling_rate

    return best_x, best_f


best_x, best_f = anneal(np.array([3.5, -4.0]))
print(best_x, best_f)
```

`temperature`が下がるにつれ悪化移動の受理率がほぼ0へ近づく点を確認してください。`cooling_rate`や`step_scale`を変えると、best-so-farの改善curveが大きく変わります。

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
「Simulated Annealingを実行した」だけでは結果の再現条件として不十分です。初期点、cooling schedule、step size、seedを一緒に記録します。
:::

より発展したvisiting distributionとlocal searchの組み合わせは[Dual Annealing](#/learn/dual-annealing)、ランダム摂動と局所法を交互に行う近い戦略は[Basin Hopping](#/learn/basin-hopping)、大域探索全体の選び分けは[大域探索・多峰性問題の選び分け](#/learn/family.global-search)で確認できます。
