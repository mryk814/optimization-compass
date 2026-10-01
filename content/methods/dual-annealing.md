---
content_id: dual-annealing
kind: method
method_id: M_SIMULATED_ANNEALING
title_ja: Dual Annealing
title_en: Dual Annealing
summary: 温度付きの確率的飛び移りで有界非凸空間を探索し、再加熱と局所探索を組み合わせて複数谷から良い候補を探します。
source_ids: [S009, S018]
prerequisites: [concept.derivative-free]
related_ids: [shgo, direct-global, differential-evolution]
aliases: [/learn/dual-annealing]
status: published
last_reviewed: 2026-09-30
---

温度付きの確率的飛び移りで有界非凸空間を探索し、再加熱と局所探索を組み合わせて複数谷から良い候補を探します。

Dual Annealingは、canonicalな手法`M_SIMULATED_ANNEALING`の一変種です。
Python例はSciPy実装`I_SCIPY_DUAL_ANNEALING`に固有のAPIです。
焼きなまし法一般の保証と、実装固有の設定を分けて読みます。

## 30秒でつかむ

熱いうちは遠くまで歩き、冷えると周辺を念入りに調べる感覚です。

- **見るもの**：現在の目的値、最良値、温度
- **動かすもの**：探索点と局所探索の開始点
- **前進の判断**：最良値の改善と、異なる谷へ到達できること

高い温度では悪化する一歩も一定確率で受け入れ、局所 谷から抜けます。
温度を下げるにつれて探索を局所化します。

Dual Annealingは一般化された 焼きなまし法の移動先を選ぶ分布と受理規則を使います。
必要に応じて局所ソルバーも組み合わせます。

まず、基礎になるSimulated Annealingの受理機構を固定実行で見ます。
橙の`current`は悪化しても、青緑の`best-so-far`は手放しません。

![1次元Rastrigin関数を初期点3.5から固定seedで400反復探索したSimulated Annealingの実行結果。上段は受理した状態が複数のbasinを横断する様子を示す。下段では橙の現在値が何度も上昇する一方、青緑の最良値は32.25から0.00076へ単調に改善する。受理65回のうち32回は悪化移動で、最初の100反復に18回、最後の100反復には1回だけ現れる。](./media/simulated-annealing-execution.svg "固定1次元Rastrigin、seed 7、初期温度5.0、幾何冷却0.985のpure Python実行です。Dual Annealing固有のvisiting distributionとlocal searchは含みません。別seed、高次元、別schedule、手法一般の性能や大域最適性も示しません。")

この実行では、受理した65 移動のうち32 移動が悪化でした。
最初の100反復では18回、最後の100反復では1回だけです。
温度低下に伴う「探索から絞り込みへ」の移行が見えます。

> この図は古典的なな受理機構を切り出した1次元教材です。
> SciPyの`dual_annealing`実行結果ではなく、移動先を選ぶ分布と局所探索も含みません。
> Dual Annealingの結果を比較するときは、以下の追加要因を分けて記録します。

## 一手の意味

候補の提案と受理判定で、現在の状態を更新します。
受理した点だけを現在点へ渡し、最良値は独立に保存します。

$$
x_{k+1}=
\begin{cases}
y_k & \text{受理した場合},\\
x_k & \text{棄却した場合}.
\end{cases}
$$

温度と分布の設定が、候補を作る範囲と悪化の受理を変えます。

### Local 探索の有無

`no_local_search=False`では、最終結果や評価回数に局所ソルバーが含まれます。

比較時は、

- 焼きなまし 評価
- 局所探索 評価
- `local solver`と許容誤差
- 局所探索開始条件

を分けます。局所的な絞り込みを含むDual Annealingと、含まない集団法を同じ反復数で比較しません。

### Temperatureと分布

- 初期 温度: 初期飛び移り 尺度
- 移動先の分布の パラメータ: 裾の長い 飛び移りの性質
- 受理パラメータ: 悪化一歩の受容
- 再加熱の 温度 比: 再加熱のタイミング

各`parameter`は相互作用し、問題 尺度や上下限へ依存します。

## 小さな例

Python例と同じ2変数Rastrigin関数を、上下限 $[-5.12,5.12]$ と乱数seed 7で実行しました。
最初の3回の改善をコールバックで記録しています。
これは全反復ではなく、新しい最良点が見つかった順です。

| 改善記録 | 点 | 目的値 | 発見した段階 |
|---|---|---:|---|
| 1 | $(1.0674,-1.9676)$ | 6.1001 | 確率的探索 |
| 2 | $(0.9950,-1.9899)$ | 4.9748 | 局所探索 |
| 3 | $(-0.9371,-0.9780)$ | 2.7014 | 確率的探索 |

2回目は局所探索で谷の底を詰めています。
その後、別の谷の候補がさらに良い値を返しました。
4000評価で止まった実行の目的値は約 $1.07\times10^{-14}$ でした。
この停止は、予算終了によるもので、大域最適性の証明ではありません。

## 向く条件・避ける条件

### 向いている条件

- 有界 連続 非凸 問題
- 複数の谷
- `gradient`を要求しない
- `local solver`と混成化したい
- 中程度の 次元
- 確率的 探索を許容

### 避ける／切り替える条件

- 1評価が極端に高価
- 高い 次元
- 雑音で受理が乱れる
- 上下限が広すぎる
- `general constraint`が中心
- 再現性にseedを記録しない
- 最適性 証明が必要

## Python

```python
import numpy as np
from scipy.optimize import dual_annealing


def rastrigin(x: np.ndarray) -> float:
    return float(10.0 * len(x) + np.sum(x * x - 10.0 * np.cos(2.0 * np.pi * x)))


result = dual_annealing(
    rastrigin,
    bounds=[(-5.12, 5.12), (-5.12, 5.12)],
    maxfun=4_000,
    seed=7,
    no_local_search=False,
)

print(result.success, result.x, result.fun, result.nfev, result.message)
```

SciPy 版により乱数引数や設定名が変わる可能性があるため、利用版の公式文書を確認します。

## 診断値

- これまでの最良値 目的関数
- 現在値 状態 目的関数
- 受理 / 棄却 移動数
- 温度
- 再加熱 数
- 目的関数評価数
- 局所探索 呼び出し数
- 境界到達率
- seed間の結果分散
- 停止理由

`current state`が悪化してもこれまでの最良値は保持します。
確率的探索では現在値と現在の採用点を分けます。

::: warning
冷却スケジュールが終了したことは大域最適性の証明ではありません。複数seed、同じ評価予算、局所探索有無を揃えて候補品質を評価します。
:::

## 失敗・切替の兆候

- 悪化移動ばかりで最良値が変わらない → 温度と上下限の尺度を確認します。
- 複数の乱数seedで結果が大きく揺れる → 同じ評価予算で結果の分布を比べます。
- 一般制約の違反を処理できない → [制約付きの微分なし法](#/learn/cobyla)と比較します。
- 1評価が高価で候補数を確保できない → [Bayesian Optimization](#/learn/bayesian-optimization)を検討します。

## 次に読む

- [微分なし大域探索](#/formulations/PA013)：有限予算で候補を探す問題
- [DIRECT](#/learn/direct-global)：決定的な領域分割
- [Basin Hopping](#/learn/basin-hopping)：局所求解後の谷を渡る方法
