---
content_id: network-simplex
kind: method
method_id: M_NETWORK_SIMPLEX
title_ja: Network Simplex法
title_en: Network Simplex
summary: 最小費用流のnetwork構造を使い、basisを全域木として扱うことで一般のsimplex法より高速に解く専用法です。
source_ids: [S054]
prerequisites: []
related_ids: [primal-simplex, dijkstra-astar, family.discrete-structure]
status: published
last_reviewed: 2026-07-26
---

最小費用流のnetwork構造を使い、basisを全域木として扱うことで一般のsimplex法より高速に解く専用法です。

## 何を解いているか

最小費用流問題では、各nodeでflowの保存則を満たします。
そのうえで容量制約の範囲内にflowを流し、edgeごとの単位費用の合計を最小化します。
これは線形計画問題として定式化でき、[Primal simplex法](#/learn/primal-simplex)でも解けます。
ただし、node-arc接続行列の多くの成分は0です。
非零成分も$+1$と$-1$だけという特殊な構造を持ちます。
Network Simplex法は、basisを一般の行列ではなくgraph上の全域木として扱います。
この構造を使い、汎用simplex法より軽い更新で同じ最適解を求めます。

## Basisが全域木に対応する理由

線形計画のsimplex法では、basisは基底変数に対応する列の集合です。
最小費用流では、実行可能なbasisがnetworkの全域木（spanning tree）に対応します。
木の外にあるnon-basic edgeは、flowを0または容量上限に固定します。
残るnode数$-1$本のbasic edgeを決めれば、flow保存則からnetwork全体のflowが定まります。

1回のbasis変換（pivot操作）は、graph上で次のように見えます。

1. 被約費用から、改善方向へ入れるnon-basic edgeを選ぶ
2. そのedgeを木へ加え、ただ1つできるcycleに沿ってflowを動かす
3. 容量の上限または下限へ最初に達するedgeを木から外す

上段の太線4本が、5 nodeを結ぶ初期treeです。
橙の`A → Z`を加えるとcycleが1つだけでき、flowを1単位動かせます。

![供給node AとBから需要node X、Y、Zへ9単位を輸送する固定最小費用流。上段の初期treeはA-Xに3、A-Yに1、B-Yに1、B-Zに4を流し、総費用は20。被約費用がマイナス2のA-Zを加え、cycleに1単位を流す。下段ではA-Yが0になってtreeを離れ、A-Zが1、B-Yが2、B-Zが3となり、全nodeの需給を保ったまま総費用が18へ下がる。](./media/network-simplex-pivot-execution.svg "2供給×3需要の固定輸送問題で、Network Simplexのentering edge、cycle、leaving edgeを1回のpivotとして読む実行結果")

cycle上で増やすedgeと減らすedgeを交互にたどります。
この例では`A → Y`が最初に0へ達するため、treeから外れます。
全nodeの需給は変えず、総費用だけが`20 → 18`へ下がります。

> 固定した2供給×3需要の整数flow教材です。
> `A → Z`の被約費用は`-2`、cycleへ流す量は1です。
> degeneracy、容量上限、負費用cycleは含みません。
> 大規模networkやNetwork Simplex実装一般の性能も示していません。

被約費用は、edge costと両端のnode potentialから計算できます。
したがって、一般のsimplex法が使う行列演算をgraph上の更新へ置き換えられます。

## 整数性という構造の恩恵

最小費用流問題のnode-arc接続行列はtotally unimodularです。
edgeの容量とnodeの需給量が整数なら、最適basic feasible solutionも整数になります。
整数解を得るためだけに、分枝限定法を加える必要はありません。
[Hungarian algorithm](#/learn/hungarian-algorithm)のような他のnetwork専用法にも、同じ構造由来の整数性が現れます。

この保証はnetwork構造に由来します。
複数edgeにまたがる論理条件やresource制約などのside constraintsを足すと、totally unimodularとは限りません。
その場合、線形緩和から整数解が得られる保証も失われます。

## 向いている条件

- 問題が最小費用流として定式化でき、node-arc接続行列がnetwork構造を保っている
- flow保存則と容量制約以外のside constraintsがない、または後で分離できる
- 整数容量・整数需給量に対して整数最適解が必要
- 大規模なnetworkで汎用simplex法より高速な専用solverを使いたい

## 避ける／切り替える条件

side constraintsでnode-arc接続行列のnetwork構造が崩れると、専用法の前提が成り立ちません。
この場合は、一般のLPへ戻ることを検討します。
離散変数を含むなら、MILPやCP-SATが候補です。
[Primal simplex法](#/learn/primal-simplex)など、LP・QP・錐最適化solverとの役割を分けて選びます。

## Python

```python
costs = {
    ("A", "X"): 2.0, ("A", "Y"): 5.0, ("A", "Z"): 4.0,
    ("B", "X"): 3.0, ("B", "Y"): 1.0, ("B", "Z"): 2.0,
}
flows = {
    ("A", "X"): 3.0, ("A", "Y"): 1.0, ("A", "Z"): 0.0,
    ("B", "X"): 0.0, ("B", "Y"): 1.0, ("B", "Z"): 4.0,
}
potentials = {"A": 0.0, "B": -4.0, "X": -2.0, "Y": -5.0, "Z": -6.0}
entering = ("A", "Z")
reduced_cost = (
    costs[entering] - potentials[entering[0]] + potentials[entering[1]]
)
cycle = (
    (("A", "Z"), 1.0),
    (("B", "Z"), -1.0),
    (("B", "Y"), 1.0),
    (("A", "Y"), -1.0),
)
theta = min(flows[arc] for arc, direction in cycle if direction < 0.0)

before = sum(flows[arc] * cost for arc, cost in costs.items())
for arc, direction in cycle:
    flows[arc] += direction * theta
after = sum(flows[arc] * cost for arc, cost in costs.items())

print(reduced_cost, theta)
print(flows)
print(before, after)
```

出力では`A → Z`の被約費用が`-2`、cycleへ流す量が1になります。
`A → Y`は0へ達し、総費用は20から18へ下がります。

このコードは、固定した実行可能treeから1回だけpivotする教育用の例です。
大規模な実務問題では、node-arc構造を直接使うNetwork Simplex実装を検討します。
対応範囲は、公式の[NEOS Guide: Optimization Problem Types](https://neos-guide.org/guide/types/)と利用versionのsolverドキュメントで確認します。

## 診断値

network構造を保てているかと、basis更新が最適性条件へ近づいているかを確認します。

- states（basisに対応する全域木の構造）
- edges（networkのedge数と容量制約の有無）
- labels（node potentialの値）
- memory（全域木構造と補助配列が使うmemory量）
- feasibility（需給量の総和が0で、全nodeの需要を満たせるか）
- optimality condition（すべてのnon-basic edgeで被約費用の符号条件が満たされているか）

## 失敗・切替の兆候

- side constraintsの追加でnode-arc接続行列がnetwork構造を保てなくなっている
- 需給量や容量が整数でなく、整数解を前提とした後段処理と食い違う
- 需給量の総和が0でない、または容量不足で全nodeの需要を満たせない
- 無限容量の負費用cycleがあり、目的値を下げ続けられる
- 問題規模に対してnode数・edge数が巨大で、汎用LPとして解くと遅い

## 次に読む

同じ「node-arc構造を専用法で使う」という考え方は[Primal simplex法](#/learn/primal-simplex)や[Dijkstra法とA*](#/learn/dijkstra-astar)にも共通します。離散・組合せ最適化全体の選び分けは[離散・組合せ最適化の選び分け](#/learn/family.discrete-structure)を参照してください。
