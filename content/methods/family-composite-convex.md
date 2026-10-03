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

この手法群の気持ちは、**全部を一つの難しい関数として扱わず、滑らかな部分、非滑らかな正則化、単純な制約、分離可能な部分へ分け、それぞれに合う操作を交互に使うこと**です。

- 見ているもの: 勾配、近接写像、主残差・双対残差、目的値ギャップ
- 動かすもの: 現在点、補助変数、双対の変数、座標、慣性項
- 前進の判断: 目的値・不動点残差・主残差・双対残差の低下
- 主な弱点: 歩幅、近接演算の難しさ、残差均衡、多数反復

非滑らかな項があるからといって、すぐ劣勾配法を選ぶ必要はありません。近接演算や座標更新を計算できるなら、より強い構造を使えます。

## まず確認すること

| 確認項目 | 選択への影響 |
|---|---|
| 分解形 | `smooth + nonsmooth`、分離可能、変数の一致のどれか |
| 近接演算・射影 | 閉形式または安価に計算できるか |
| 凸性 | 大域ギャップや収束率を解釈できるか |
| 疎性 | 座標更新や疎解の利点があるか |
| 分散性 | 複数ブロック・計算機へ分ける必要があるか |
| 必要精度 | 粗い解か、高精度な主双対残差か |

一般NLPへそのまま渡す前に、L1、箱型制約、単体、ノルム、指示関数などが既知の近接演算・射影を持つか確認します。

## 条件付きの選び分け

| 役割 | 手法 | 優先しやすい条件 | 切り替えを考える条件 |
|---|---|---|---|
| 基本の分離更新 | [Proximal Gradient](#/learn/proximal-gradient) | 滑らかな損失 + 安価な近接演算、凸複合問題 | 歩幅が保守的で遅い、近接演算が高価 |
| 加速された近接演算 | [FISTA](#/learn/fista) | 凸問題で目的ギャップを早く下げたい | 振動が強い、再始動が頻繁 |
| 変数ごとの更新 | [Coordinate Descent](#/learn/coordinate-descent) | 座標更新が安価、疎な高次元問題 | 特徴相関が強く一座標ずつでは遅い |
| 最小限の構造 | [Subgradient](#/learn/subgradient) | 近接演算が使えず、粗い凸解でよい | 歩幅の変更規則に敏感、改善が非常に遅い |
| 問題幾何を使う | [Mirror Descent](#/learn/mirror-descent) | 単体、確率分布、逐次的な凸最適化 | 鏡写像が問題に合わない |
| 分離・変数の一致 | [ADMM](#/learn/admm) | ブロック分解、分散計算、近接演算部分問題が解きやすい | 主残差・双対残差が不均衡、部分問題が重い |
| 非滑らかモデルを蓄積 | [Bundle method](#/methods/M_BUNDLE) | 劣勾配より安定した凸非滑らか解法が必要 | 束の管理・部分問題が支配的 |

同じ反復数で比較しません。勾配、近接演算、通信、部分問題の費用が手法ごとに違います。

## うまくいったサインと切替サイン

追うべき値:

- 目的関数値とそれまでの最良値
- 勾配写像 / 不動点残差
- 主残差・双対残差
- 疎性パターンの安定
- 歩幅と後戻り回数
- ADMM ペナルティパラメータ
- 近接演算時間、通信時間、座標一巡数

切替サイン:

- 劣勾配が長時間ほぼ改善しない → 近接演算、bundle、滑らかな近似を検討
- FISTAが振動する → 適応的な再始動または近接勾配法へ
- 座標降下法が相関変数で停滞 → ブロック更新や準Newton法へ
- ADMMの一方の残差だけ大きい → ペナルティ調整・尺度の調整を見直す
- 近接演算計算が本体より高価 → 定式化または別分割を検討
- 非凸項が入った → 凸保証をそのまま適用しない

## 小さな比較の型

各操作の費用を分けて記録します。

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

## コラム: 近接演算は何をしているか

近接操作は、非滑らかな項を単に微分する代わりに、現在点から離れすぎない範囲でその項を含む小問題を解きます。L1正則化のsoft-thresholdingは代表例です。

「近接演算が存在する」ことと「実装上安価に計算できる」ことは別です。大規模な内部求解が必要なら、分解した意味が薄れる場合があります。

## 次に読む

滑らかで非滑らかな項がなければ[滑らかな局所最適化](#/learn/family.smooth-local)、一般非線形制約が本質なら[制約付きNLP](#/learn/family.constrained-nlp)へ進みます。
