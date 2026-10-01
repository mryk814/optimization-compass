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
last_reviewed: 2026-09-30
---

温度parameterに応じて悪化する移動も確率的に受理し、局所解からの脱出を狙う確率的大域探索heuristicです。

## 30秒でつかむ

霧の中の山地を、高度計だけを頼りに、いちばん低い谷を目指して歩くとします。
下り坂しか選ばなければ、最初に見つけた窪みで動けなくなります。
そこで、体力に余裕のある序盤は、上り坂も確率的に受け入れます。疲れてきた終盤は、下り坂だけを選ぶようにします。この「体力」に当たるのが温度です。

- **見るもの**: 現在点と候補点の目的関数値の差、そのときの温度
- **動かすもの**: 現在点と温度。候補点は乱数で作る
- **前進の判断**: 現在の値でなく、これまでの最良値（best-so-far）が改善すること

温度が高いうちは広く歩き回り、下がるにつれて一つの谷へ絞り込みます。

## 一手の意味

通常の局所法は、改善する移動だけを採用します。
Simulated Annealingは、現在点 $x$ から候補点 $x'$ を作ります。目的関数値が悪化しても、一定の確率で採用します。
よく使われる受理確率は、Metropolis型です。

$$
P(\text{accept}) = \min\left(1, \exp\left(-\frac{f(x') - f(x)}{T}\right)\right)
$$

$f(x') \le f(x)$ なら確率1で採用します。
悪化する場合の採用されやすさは、差と温度で決まります。差 $f(x') - f(x)$ が小さいほど、温度 $T$ が高いほど、採用されやすくなります。
$T$ を反復とともに下げる規則を、冷却スケジュール（cooling schedule）と呼びます。

一回の反復は、次の順です。

1. 現在点の近くに、乱数で候補点を作る
2. 候補点の目的関数値を評価し、差を計算する
3. 受理確率を計算し、一様乱数と比べて採用か棄却かを決める
4. 温度を下げる

## 小さな例

1次元のRastrigin関数 $f(x)=10+x^2-10\cos(2\pi x)$ を、区間 $[-5.12,\,5.12]$ で最小化します。最小点は $x=0$ で、値は $0$ です。整数の位置ごとに局所解があります。
初期点は $x=3.5$（$f=32.25$）、初期温度は $T_0=5.0$ で、反復ごとに $0.985$ 倍へ冷やします。
候補点は、現在点に標準偏差 $0.5$ の正規乱数を足して作り、範囲の外は端へ切り詰めます。
乱数の seed は 7 に固定しました。最初の5反復です。

| 反復 | 温度 $T$ | 現在点（値） | 候補点（値） | 差 $\Delta$ | 受理確率 | 引いた乱数 | 結果 |
|---:|---:|---|---|---:|---:|---:|---|
| 1 | 5.000 | 3.500（32.25） | 3.372（28.31） | $-3.94$ | 1 | | 受理（改善） |
| 2 | 4.925 | 3.372（28.31） | 3.628（30.11） | $+1.80$ | 0.694 | 0.651 | 受理（悪化を受理） |
| 3 | 4.851 | 3.628（30.11） | 4.184（23.49） | $-6.62$ | 1 | | 受理（改善） |
| 4 | 4.778 | 4.184（23.49） | 4.457（39.49） | $+16.00$ | 0.035 | 0.366 | 棄却 |
| 5 | 4.707 | 4.184（23.49） | 4.740（33.09） | $+9.59$ | 0.130 | 0.037 | 受理（悪化を受理） |

反復2では、悪化幅 $1.80$ が小さく温度も高いので、受理確率は $0.694$ です。引いた乱数 $0.651$ がそれを下回り、悪化を受理しました。
反復4では、悪化幅が $16.00$ と大きく、受理確率は $0.035$ です。乱数 $0.366$ はそれを上回り、棄却しました。
反復5では、受理確率は $0.130$ と低めです。それでも乱数が $0.037$ と小さく、大きな悪化を受理しています。

この5反復で、現在点は $3.5$ から $4.74$ へ動き、最小点 $x=0$ からは遠ざかっています。最良値は $32.25$ から $23.49$ へ下がりました。
現在点の値と最良値は別物です。悪化を受理しても、最良値は悪化しません。
この数値は seed 固定の一例で、別の seed では変わります。

### 400反復の全体像

橙の現在値が何度も上昇しても、青緑の最良値は悪化しません。

![1次元Rastrigin関数を初期点3.5から固定seedで400反復探索したSimulated Annealingの実行結果。上段は受理した状態が複数のbasinを横断する様子を示す。下段では橙の現在値が何度も上昇する一方、青緑の最良値は32.25から0.00076へ単調に改善する。受理65回のうち32回は悪化移動で、最初の100反復に18回、最後の100反復には1回だけ現れる。](./media/simulated-annealing-execution.svg "固定1次元Rastrigin、seed 7、初期温度5.0、幾何冷却0.985のpure Python実行です。別seed、高次元、別schedule、Simulated Annealing一般の性能や大域最適性は示しません。")

このrunでは、受理した65回の移動のうち、32回が悪化でした。
そのうち18回は最初の100反復、1回だけが最後の100反復に現れます。
温度が下がるにつれて、探索から絞り込みへ重心が移った結果です。

> 固定した1次元Rastrigin、seed 7の教材実行です。
> 最良目的値は`32.25 → 0.00076`ですが、最適性証明ではありません。
> 別seed、高次元、別scheduleで同じ結果になることも保証しません。

## 向く条件・避ける条件

向く条件です。

- 低〜中次元の、上下限つき連続問題
- 目的関数が多峰で、複数の谷（basin）がある
- 評価予算に余裕があり、確率的な探索を許容できる
- 局所法だけでは、初期点への依存が強すぎる

避ける、または切り替える条件です。

- 高次元で一回の評価が高価、かつ構造的な手がかりがない → [高次元のblack-box最適化（PA015）](#/formulations/PA015)や、[高価な低次元評価（PA014）](#/formulations/PA014)を確認する
- 局所解で十分で、大域探索のcostが見合わない → 局所法へ
- 大域最適性の証明が必須な用途 → 領域分割型の[SHGO](#/learn/shgo)や[DIRECT](#/learn/direct-global)
- 再現できる単一のrunの結果が求められる（seedへの依存が大きいため） → 複数のseedで比べる

## Python

次の例は、上の1次元Rastriginを、標準ライブラリだけで焼きなましします。

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

`history` の現在値（current objective）と最良値（best-so-far）を、別々にplotしてください。
`cooling_rate` や `step_scale` を変えると、受理回数と改善の曲線が変わります。

SciPyには、古典的なSimulated Annealingの直接の実装はありません。後継として[`scipy.optimize.dual_annealing`](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.dual_annealing.html)があります。
`dual_annealing` は、visiting distributionと局所探索を組み合わせた発展形です。

## 診断値

| 診断値 | 見方 | 判断 |
|---|---|---|
| 最良値（best-so-far） | 評価数に対する改善 | 改善が止まったら、冷却か候補の作り方を見直す |
| 悪化した移動の受理率 | 悪化を受理した割合 | 0や1のまま変わらないなら、温度の設定が合っていない |
| 多様性（diversity） | 探索している点群の散らばり | 早期に失われたら、同じ谷に留まっている |
| 到達範囲（coverage） | 探索領域のどこまで到達したか | 狭いなら、初期温度か候補の幅を大きくする |
| 局所的な仕上げの成否（local refinement success） | 低温の段階で改善が続いているか | 続かないなら、冷却が速すぎる可能性がある |

冷却が速すぎると、ほかの谷へ移る前に探索が固まります。
遅すぎると、評価予算を使い切っても探索が絞れません。
温度の下げ方と、やり直し（re-annealing）の有無は、実装ごとに記録すべきparameterです。

## 失敗・切替の兆候

| 症状 | 考えられる原因 | 対処・切替先 |
|---|---|---|
| 評価予算を使っても、最良値がほとんど改善しない | 冷却が遅すぎる、または候補の幅が合わない | 冷却と候補の幅を見直す |
| 探索点の多様性が早期に失われ、同じ谷の付近に留まる | 冷却が速すぎる | 初期温度と冷却率を見直す。[Dual Annealing](#/learn/dual-annealing)や[Basin Hopping](#/learn/basin-hopping)を比べる |
| 悪化した移動の受理率が、ほぼ0または1のまま変わらない | 温度の尺度が目的関数の差に合っていない | 初期温度を、目的関数値の差に合わせて調整する |
| 異なるseedで得られる解が、大きくばらつく | 有限の予算では、探索が谷に依存する | 複数のseedで比べる。予算を増やす |

::: warning
「Simulated Annealingを実行した」だけでは、結果の再現条件として不十分です。
初期点とseedを記録します。
冷却スケジュールと候補の幅（step size）も残してください。
:::

## コラム: 保証の弱さ

Simulated Annealingはheuristicであり、有限回の実行で大域最適性を証明する手法ではありません。
理論上は、無限回・十分遅い冷却で大域最適へ収束するという結果があります。しかし、実務の有限の予算にはそのまま適用できません。
boundedな低次元で、決定的な網羅性を持たせたい場合は、[SHGO](#/learn/shgo)や[DIRECT](#/learn/direct-global)のような領域分割型が別の選択肢になります。

## 次に読む

- [高次元のblack-box最適化（PA015）](#/formulations/PA015)：勾配なしで多くの変数を決めるとき、何が難しくなるか
- [Dual Annealing](#/learn/dual-annealing)：発展したvisiting distributionと局所探索
- [Basin Hopping](#/learn/basin-hopping)：ランダムな摂動と局所法の交互実行
- [大域探索・多峰性問題の選び分け](#/learn/family.global-search)：条件から手法を比べる
