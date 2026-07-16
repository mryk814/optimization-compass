---
content_id: family.global-search
kind: method
method_id: MF_GLOBAL_SEARCH
title_ja: 大域探索・多峰性問題の選び分け
title_en: Choosing a Global Search Strategy
summary: bounds内に複数の谷や良い候補があるとき、multi-start、領域分割、annealing、population探索を選び分ける入口です。
source_ids: [S006, S007, S008, S009, S058, S072, S073, S074]
related_ids: [direct-global, shgo, dual-annealing, differential-evolution, cma-es, genetic-algorithm, particle-swarm]
status: published
last_reviewed: 2026-07-16
---

bounds内に複数の谷や良い候補があるとき、multi-start、領域分割、annealing、population探索を選び分ける入口です。

## 30秒でつかむ

このfamilyの気持ちは、**一つの初期点から素直に下るだけでは見逃す谷があるので、探索領域を分ける、飛び移る、複数候補を同時に育てることで広く探すこと**です。

- 見ているもの: best-so-far、領域coverage、population diversity、局所探索の成功
- 動かすもの: start点、矩形、温度、population、探索分布
- 前進の判断: 新しいbasinの発見とincumbent改善
- 主な弱点: 評価budget、次元の呪い、有限時間での証明不足

「global」という名前があっても、有限budgetで大域最適性を証明するとは限りません。deterministic、stochastic、理論保証、実装上の停止条件を分けて読みます。

## まず確認すること

| 確認項目 | 選択への影響 |
|---|---|
| bounds | 探索領域が有限か、十分狭く設定できるか |
| 次元 | 領域分割やpopulation評価が現実的か |
| 1評価の費用 | 数百〜数万評価を許容できるか |
| 並列性 | populationやmulti-startを同時評価できるか |
| 目的関数の性質 | smooth、discontinuous、noisy、multimodal |
| 必要な保証 | 良い候補か、lower boundを伴う証明か |

構造を使える凸問題、graph問題、MILPをblack-box global searchへ隠さないでください。専用構造を使う方が強い保証と診断を得られます。

## 条件付きの選び分け

| 役割 | 手法 | 優先しやすい条件 | 切り替えを考える条件 |
|---|---|---|---|
| 複数局所探索の基準 | [Multi-start](#/methods/M_MULTI_START) | 局所法が安価で、basin差を初期点で確認したい | start数だけ増え、coverageが偏る |
| 局所法と確率的ジャンプ | [Basin Hopping](#/methods/M_BASIN_HOPPING) | 低次元、局所最適化が有効、basin間移動を試したい | 局所solveがbudgetを支配する |
| 決定論的な領域分割 | [DIRECT](#/learn/direct-global) | 低次元bounded、Lipschitz定数を明示したくない | rectangle数が急増、高次元 |
| topologyを使う候補生成 | [SHGO](#/learn/shgo) | 低次元、比較的滑らか、決定論的候補が欲しい | sampling complexが大きくなりすぎる |
| 温度で悪化stepも許す | [Dual Annealing](#/learn/dual-annealing) | 多峰性、連続bounds、stochastic探索を許容 | coolingやseedで結果が不安定 |
| 差分でpopulationを更新 | [Differential Evolution](#/learn/differential-evolution) | 並列評価可能、非滑らか・多峰性 | 一評価が高価、dimension×populationが重い |
| 分布の形を学ぶ | [CMA-ES](#/learn/cma-es) | 連続、変数相関が強い、moderate dimension | 極端な高次元、非常に少ないbudget |
| 柔軟なencoding | [Genetic Algorithm](#/learn/genetic-algorithm) | 離散・混合encodingや独自operatorが必要 | encodingが意味を壊し、parameter調整が支配的 |

有限budgetで証明が必要なら、convex global optimization、spatial branch-and-bound、問題固有boundを持つ手法を別に検討します。

## うまくいったサインと切替サイン

追うべき値:

- best-so-farと改善間隔
- objective evaluation数
- population diversityまたは領域coverage
- basinごとの到達頻度
- 複数seedの分布
- feasible fraction
- local refinement成功率

切替サイン:

- diversityが早期に消える → restart、mutation、別population法
- bestが改善しないままbudgetを消費 → search bounds、構造、surrogateを見直す
- 同じbasinばかり再訪 → initializationとcoverage strategyを変更
- 評価が高価すぎる → Bayesian Optimizationやmulti-fidelityへ
- 低次元で決定論的再現性が欲しい → DIRECTやSHGOを検討
- 局所解で十分と分かった → smooth localまたはlocal DFOへ戻す

## 小さな比較の型

stochastic手法は単一seedで比較しません。

```python
benchmark = {
    "problem_instance": "same-bounded-multimodal-problem",
    "bounds": [(-5.0, 5.0), (-5.0, 5.0)],
    "objective_evaluation_budget": 2_000,
    "seeds": [1, 2, 3, 4, 5],
    "methods": ["DIRECT", "dual-annealing", "differential-evolution"],
    "reported_metrics": ["best_so_far", "success_rate", "evaluation_count"],
}

assert len(benchmark["seeds"]) > 1
```

## コラム: 大域性には複数の意味がある

大域探索という言葉は、少なくとも次を区別します。

1. 複数basinを探すheuristic
2. budgetを増やすと広く探索する漸近的性質
3. lower boundとupper boundを詰めるcertificate
4. 特定仮定下での理論保証

画面上で広く点が動いていることは、3番の証明ではありません。Optimization Compassでは、global candidateとglobal certificateを別の到達点として扱います。

## 次に読む

評価が非常に高価なら[高価なblack-box探索の選び分け](#/learn/family.expensive-black-box)、局所改善へ絞るなら[滑らかな局所最適化](#/learn/family.smooth-local)または[局所Derivative-free](#/learn/family.local-dfo)へ進みます。