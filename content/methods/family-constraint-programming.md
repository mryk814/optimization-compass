---
content_id: family.constraint-programming
kind: method
method_id: MF_CONSTRAINT_PROGRAMMING
title_ja: 制約プログラミング・SATの選び分け
title_en: Choosing a Constraint Programming or SAT Approach
summary: domain propagation、learning、searchを用いて論理・組合せ制約の可行性と最適化を扱う手法群の入口です。
source_ids: [S022, S053]
related_ids: [cp-sat, cp-search, cdcl-sat, family.discrete-structure]
status: published
last_reviewed: 2026-07-16
---

domain propagation、learning、searchを用いて論理・組合せ制約の可行性と最適化を扱う手法群の入口です。

## 30秒でつかむ

このfamilyの気持ちは、**変数が取り得る値の範囲（domain）を制約から論理的に削り、削り切れなかった部分だけ分岐して探すこと**です。

- 見ているもの: 各変数のdomain、制約の伝播結果、衝突（conflict）
- 動かすもの: domainの縮小と、分岐による探索木の分割
- 前進の判断: domainが縮む、conflictの原因が学習節として再利用できる、実行可能解が見つかる
- 主な弱点: 伝播が弱い制約表現では爆発しやすい、連続・滑らかな構造の利用は弱い

「CP-SATが常に最良」という順位ではありません。可否・組合せ構造・論理制約が主役の問題で、伝播の強さと探索・学習の仕組みが噛み合うかを条件で判断します。

## まず確認すること

| 確認項目 | 選択への影響 |
|---|---|
| 変数のdomain | 有限domainか、Boolean/整数へ意味のあるencodingができるか |
| 制約の種類 | 論理・global constraintが中心か、線形整数構造が強いか |
| 最適化か充足か | 目的関数の有無、bound反復で十分な規模か |
| 証明の必要性 | feasibility/infeasibilityの証明そのものが成果物か |
| 整数化の妥当性 | 実数精度を整数・Booleanのscaleへ落として意味が保たれるか |

論理・scheduling・resource制約が中心ならこのfamilyを第一候補にしますが、整数線形構造（線形目的関数と線形不等式）が強い問題は、MILP系のBranch-and-Cutのような手法とも比較する価値があります。

## 条件付きの選び分け

| 役割 | 手法 | 優先しやすい条件 | 切り替えを考える条件 |
|---|---|---|---|
| 伝播・学習・探索を統合した既定候補 | [CP-SAT](#/learn/cp-sat) | 論理・scheduling・assignment制約が中心で、最適化と証明の両方が欲しい | 整数線形構造が強く、専用MILP solverの方が緩和が強い |
| domain縮小の仕組みを学ぶ入口 | [制約プログラミング探索](#/learn/cp-search) | global constraintで問題を書きたい、propagationと分岐の関係を理解したい | 大規模化して自作の伝播では収束しない |
| Boolean充足可能性そのものが焦点 | [CDCL SAT](#/learn/cdcl-sat) | 論理制約中心で、可否そのものやUNSAT証明が目的 | 最適化そのものが目的で、目的関数を直接扱いたい |
| 整数線形構造が強い場合の代替 | Branch and Cut | 線形目的関数と線形不等式が中心で、強い連続緩和が使える | 論理・scheduling制約が支配的でLP緩和が弱い |

これは一般性能rankingではありません。同じmodel、time limit、hardware、seed、worker数で比較します。

## うまくいったサインと切替サイン

うまく進んでいるときは、探索が進むほど手がかりが増えます。

- domainが分岐のたびに目に見えて縮む
- conflict/branchあたりのpropagationが多く、探索木が浅い
- 学習節（CDCL/CP-SATの内部）が同種の衝突を再発させない
- best boundとincumbentのgapが縮む

切替サイン:

- conflict/node数が増え続けて収束しない → 伝播・分岐戦略・model表現を見直す
- domainが縮まらない → global constraintの選び方やencodingを見直す
- 整数scaleが過大 → 単位・離散化を見直す、またはMILP系へ切り替える
- 本質的に連続・滑らかな構造が支配的 → NLP/QP系のfamilyへ

## 小さな比較の型

比較ではsolution qualityだけでなく、time limit・seed・worker数を揃えます。

```python
experiment = {
    "problem_instance": "same-finite-domain-model",
    "domain_representation": "boolean-or-integer",
    "time_limit_seconds": 60,
    "random_seed": 7,
    "worker_count": 1,
    "methods": ["cp-sat", "cp-search", "cdcl-sat"],
}

assert experiment["time_limit_seconds"] > 0
```

## コラム: 可否判定と最適化はどう繋がるか

SATやCPの探索は、もともと「制約をすべて満たせるか」という可否判定として発展しました。最適化は、見つけた解より良い値を要求するbound制約を追加してSAT/CPを繰り返し呼ぶことで扱えます。CP-SATのような実装は、この反復とlinear relaxationやcutを内部で統合しており、単純な繰り返し呼び出しより効率的です。MaxSATのように、制約の一部を重み付きで緩めて最適化そのものを目的関数化する拡張もあります。

## 次に読む

離散最適化全体でgraphや動的計画法との比較を知りたい場合は[離散・組合せ最適化の選び分け](#/learn/family.discrete-structure)へ進みます。
