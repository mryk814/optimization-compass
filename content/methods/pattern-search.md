---
content_id: pattern-search
kind: method
method_id: M_PATTERN_SEARCH
title_ja: Pattern Search
title_en: Pattern Search
summary: 現在点の周囲へpattern方向のpoll点を配置し、改善の有無に応じてstep sizeを拡大・縮小する微分不要局所探索法です。
source_ids: [S018, S056, S060]
prerequisites: [concept.derivative-free]
related_ids: [powell, mads, method.nelder-mead]
aliases: [/learn/pattern-search]
status: published
last_reviewed: 2026-07-15
---

現在点の周囲へpattern方向のpoll点を配置し、改善の有無に応じてstep sizeを拡大・縮小する微分不要局所探索法です。

## Pollの考え方

現在点 $x_k$、step size $\Delta_k$、方向集合 $D_k$ に対し、

$$
x_k+\Delta_k d,\quad d\in D_k
$$

を評価します。改善点があればincumbentを更新し、なければ$\Delta_k$を縮小します。

coordinate directions $\{\pm e_i\}$ は単純なpatternですが、positive spanning setを使う理論的変種や、search stepを加える実装もあります。

## Python: coordinate pattern

```python
import numpy as np


def objective(x: np.ndarray) -> float:
    return float((1.0 - x[0]) ** 2 + 20.0 * (x[1] - x[0] ** 2) ** 2)


x = np.array([-1.2, 1.0])
step = 0.5
minimum_step = 1e-6
directions = np.vstack((np.eye(2), -np.eye(2)))

while step > minimum_step:
    candidates = [x + step * direction for direction in directions]
    values = [objective(candidate) for candidate in candidates]
    best_index = int(np.argmin(values))
    if values[best_index] < objective(x):
        x = candidates[best_index]
        step = min(step * 1.2, 1.0)
    else:
        step *= 0.5

print(x, objective(x), step)
```

これは教育用のopportunistic coordinate searchです。正式なpattern-search / generalized pattern-searchの方向条件や停止理論をすべて実装してはいません。

## Complete pollとopportunistic poll

- complete poll: 全候補を評価して最良点を選ぶ
- opportunistic: 最初の改善で残りを省略

opportunisticは評価数を減らせますが、方向順序に依存します。並列評価ではcomplete pollが自然な場合があります。

## 診断値

- incumbent objective
- step / mesh size
- successful / unsuccessful poll数
- poll direction別の成功率
- evaluation count
- parallel batch size
- bounds hit率
- constraint violation
- stopping reason

stepが小さいだけでglobal optimumは保証されません。noise floorより小さなstepを続けても改善判定が不安定になります。

## 向いている条件

- 低〜中次元のblack-box
- derivativeがない、信用できない
- 軽い非滑らかさ
- poll点を並列評価できる
- 局所stationarityの目安が欲しい

## 避ける／切り替える条件

- 高次元でpoll点数が予算を圧迫
- 評価が極端に高価
- noiseで改善判定が揺れる
- variable scaleが悪い
- black-box constraintを単純penaltyだけで扱う
- discrete / categorical domainを無理に連続方向へ埋め込む

[MADS](#/learn/mads)はpoll方向とmeshをより一般化し、black-box constraintを扱う実装もあります。

::: warning
同じ「pattern search」でもsearch step、poll set、opportunism、mesh update、constraint handlingが異なります。implementationとoptionを明記します。
:::
