---
content_id: family.composite-convex
kind: method
method_id: MF_COMPOSITE_CONVEX
title_ja: 非滑らか・複合凸最適化の選び分け
title_en: Choosing a Composite Convex Optimizer
summary: 滑らかな損失とL1正則化・制約・分離構造を組み合わせるとき、近接法、FISTA、Coordinate Descent、ADMMなどを選び分ける入口です。
source_ids: [S055, S061, S066, S067]
related_ids: [proximal-gradient, fista, coordinate-descent, subgradient, mirror-descent, admm]
status: published
last_reviewed: 2026-07-16
---

滑らかな損失とL1正則化・制約・分離構造を組み合わせるとき、近接法、FISTA、Coordinate Descent、ADMMなどを選び分ける入口です。

## 30秒でつかむ

このfamilyの気持ちは、**全部を一つの難しい関数として扱わず、滑らかな部分、非滑らかな正則化、単純な制約、分離可能な部分へ分け、それぞれに合う操作を交互に使うこと**です。

- 見ているもの: gradient、proximal mapping、primal/dual residual、objective gap
- 動かすもの: 現在点、補助変数、dual変数、座標、momentum
- 前進の判断: objective・fixed-point residual・primal/dual residualの低下
- 主な弱点: step size、proxの難しさ、残差balance、多数反復

非滑らかな項があるからといって、すぐsubgradient法を選ぶ必要はありません。proxや座標更新を計算できるなら、より強い構造を使えます。

## まず確認すること

| 確認項目 | 選択への影響 |
|---|---|
| 分解形 | `smooth + nonsmooth`、separable、consensusのどれか |
| prox・projection | 閉形式または安価に計算できるか |
| convexity | 大域gapや収束率を解釈できるか |
| sparsity | 座標更新や疎解の利点があるか |
| 分散性 | 複数block・machineへ分ける必要があるか |
| 必要精度 | 粗い解か、高精度なprimal-dual残差か |

一般NLPへそのまま渡す前に、L1、box、simplex、norm、indicator functionなどが既知のprox・projectionを持つか確認します。

## 条件付きの選び分け

| 役割 | 手法 | 優先しやすい条件 | 切り替えを考える条件 |
|---|---|---|---|
| 基本の分離更新 | [Proximal Gradient](#/learn/proximal-gradient) | smooth loss + 安価なprox、凸複合問題 | step sizeが保守的で遅い、proxが高価 |
| 加速されたprox | [FISTA](#/learn/fista) | 凸問題で目的gapを早く下げたい | 振動が強い、restartが頻繁 |
| 変数ごとの更新 | [Coordinate Descent](#/learn/coordinate-descent) | 座標更新が安価、疎な高次元問題 | feature相関が強く一座標ずつでは遅い |
| 最小限の構造 | [Subgradient](#/learn/subgradient) | proxが使えず、粗い凸解でよい | step scheduleに敏感、改善が非常に遅い |
| 問題幾何を使う | [Mirror Descent](#/learn/mirror-descent) | simplex、確率分布、online convex optimization | mirror mapが問題に合わない |
| 分離・consensus | [ADMM](#/learn/admm) | block分解、distributed、prox部分問題が解きやすい | primal/dual residualが不均衡、部分問題が重い |
| 非滑らかmodelを蓄積 | [Bundle method](#/methods/M_BUNDLE) | subgradientより安定した凸非滑らか解法が必要 | bundle管理・部分問題が支配的 |

同じiteration数で比較しません。gradient、prox、通信、部分問題のcostが手法ごとに違います。

## うまくいったサインと切替サイン

追うべき値:

- objective valueとbest-so-far
- gradient mapping / fixed-point residual
- primal / dual residual
- sparsity patternの安定
- step sizeとbacktracking回数
- ADMM penalty parameter
- prox time、通信time、座標sweep数

切替サイン:

- subgradientが長時間ほぼ改善しない → prox、bundle、smooth approximationを検討
- FISTAが振動する → adaptive restartまたはproximal gradientへ
- coordinate descentが相関変数で停滞 → block更新やquasi-Newtonへ
- ADMMの一方の残差だけ大きい → penalty調整・scalingを見直す
- prox計算が本体より高価 → 定式化または別splittingを検討
- 非凸項が入った → 凸保証をそのまま適用しない

## 小さな比較の型

operation costを分けて記録します。

```python
comparison = {
    "problem_instance": "same-composite-objective",
    "gradient_budget": 1_000,
    "prox_budget": 1_000,
    "communication_budget": None,
    "objective_tolerance": 1e-6,
    "methods": ["proximal-gradient", "FISTA", "ADMM"],
    "metrics": ["objective_gap", "fixed_point_residual", "wall_time"],
}

assert comparison["gradient_budget"] == comparison["prox_budget"]
```

## コラム: proxは何をしているか

proximal operatorは、非滑らかな項を単に微分する代わりに、現在点から離れすぎない範囲でその項を含む小問題を解きます。L1正則化のsoft-thresholdingは代表例です。

「proxが存在する」ことと「実装上安価に計算できる」ことは別です。大規模な内部solveが必要なら、分解した意味が薄れる場合があります。

## 次に読む

滑らかで非滑らかな項がなければ[滑らかな局所最適化](#/learn/family.smooth-local)、一般非線形制約が本質なら[制約付きNLP](#/learn/family.constrained-nlp)へ進みます。