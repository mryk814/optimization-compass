---
content_id: bundle-method
kind: method
method_id: M_BUNDLE
title_ja: Bundle法
title_en: Bundle Method
summary: 非滑らか凸関数で過去の劣勾配を捨てずcutの束として蓄え、単一の劣勾配stepより安定した局所modelを作る方法です。
source_ids: [S055, S056]
related_ids: [family.composite-convex, subgradient, proximal-gradient]
status: published
last_reviewed: 2026-07-16
---

非滑らか凸関数で過去の劣勾配を捨てずcutの束として蓄え、単一の劣勾配stepより安定した局所modelを作る方法です。

## 30秒でつかむ

この手法の気持ちは、**折れ曲がった関数で今の劣勾配だけを信じるのではなく、これまで観測した支持平面を束ねて、次に進むための下側modelを育てたい**というものです。

- 見ているもの: 関数値、劣勾配、cut、model gap
- 動かしているもの: bundle、中心点、trial point
- 前進の判断: serious stepで中心点を改善できるか
- 恐れていること: cutの増大、弱いmodel、部分問題の重さ

劣勾配法が一回ごとに方向を使い捨てるのに対し、Bundle法は過去情報を局所modelへ残します。

## まず確認すること

| 項目 | 確認内容 |
|---|---|
| convexity | 凸非滑らか問題として扱えるか |
| oracle | 関数値と劣勾配を返せるか |
| prox structure | より単純な近接作用素を使えないか |
| dimension | bundle subproblemを解ける規模か |
| precision | 粗い解か、安定したgap診断が必要か |

L1正則化などproxが安価なら、Proximal GradientやFISTAを先に考える方が単純です。

## 仕組み

観測点 $x_i$ と劣勾配 $g_i$から、凸性に基づくcutを作ります。

$$
f(x) \geq f(x_i) + g_i^T(x-x_i)
$$

複数cutの最大値でpiecewise-linear modelを作り、中心点から離れすぎない安定化項と合わせてtrial pointを選びます。trialが十分改善すればserious step、改善が弱くても有用なcutならnull stepとしてbundleだけ更新します。

## 向く条件・避ける条件

向きやすい条件:

- 凸だが非滑らかな目的関数
- 関数値と劣勾配oracleがある
- 単純なsubgradient法より安定した進行が必要
- dual decompositionなどcutに意味がある

避ける条件:

- 非凸でcutがglobal lower modelにならない
- proxを閉形式で計算できる単純構造
- bundle部分問題が元問題並みに重い
- 離散変数や強いnoiseを未model化

## うまくいったサインと切替サイン

見る値:

- serious / null step比率
- model gap
- bundle size
- center objective
- stabilization parameter
- cutのactive数

切替サイン:

- null stepばかり続く → model、stabilization、oracleを確認
- bundleが増えmemoryを圧迫 → aggregationやcut deletionを検討
- proxが実は安価 → Proximal Gradientへ
- 非凸性が重要 → convex guaranteeを外し別methodへ
- 劣勾配noiseが大きい → samplingやrobust oracleを検討

## Python

```python
from dataclasses import dataclass

import numpy as np


@dataclass
class Cut:
    point: np.ndarray
    value: float
    subgradient: np.ndarray


def model_value(cuts: list[Cut], candidate: np.ndarray) -> float:
    return max(
        cut.value + float(cut.subgradient @ (candidate - cut.point))
        for cut in cuts
    )


cuts = [
    Cut(np.array([1.0, 0.0]), 1.0, np.array([1.0, -1.0])),
    Cut(np.array([0.0, 1.0]), 0.8, np.array([-0.5, 1.0])),
]
trial = np.array([0.5, 0.5])
print(model_value(cuts, trial))
```

この例はcut modelだけを示す教育用断片です。実装には安定化付きsubproblem、serious-step判定、cut管理が必要です。

## コラム: null stepは失敗ではない

trial pointが中心点を更新しなくても、新しいcutがmodelを改善するなら情報は増えています。これがBundle法の特徴です。ただしnull stepが続きすぎる場合は進行していない可能性があります。

[非滑らか・複合凸最適化の選び分け](#/learn/family.composite-convex)でSubgradient、Proximal Gradient、ADMMとの前提差を確認してください。