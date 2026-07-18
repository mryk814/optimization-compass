---
content_id: spatial-branch-and-bound
kind: method
method_id: M_SPATIAL_BRANCH_BOUND
title_ja: 空間branch-and-bound
title_en: Spatial Branch and Bound
summary: 非凸MINLPの大域最適化のため、整数変数だけでなく連続変数の区間でも分岐し、各領域で凸緩和から下界を作りながら木を刈り込む厳密探索法です。
source_ids: [S021, S024, S025]
prerequisites: []
related_ids: [branch-and-bound, outer-approximation-minlp, family.discrete-structure]
status: published
last_reviewed: 2026-07-18
---

非凸MINLPの大域最適化のため、整数変数だけでなく連続変数の区間でも分岐し、各領域で凸緩和から下界を作りながら木を刈り込む厳密探索法です。

## 何を分岐しているか

[整数B&B](#/learn/branch-and-bound)は、整数変数の値を固定・分割することでnodeを作ります。空間branch-and-boundはこれに加えて、非凸な非線形項を含む連続変数の**区間**でも分岐します。たとえば非凸項 $xy$（双線形項）を含む問題では、$x$の区間を$[x_L, x_U]$から$[x_L, m]$と$[m, x_U]$に分割し、それぞれの部分区間で問題を扱います。分岐対象が「整数の値」ではなく「連続変数の存在範囲」であることが、空間branch-and-boundという名前の由来です。

## 各領域で下界をどう作るか

分岐で得られた各区間では、非凸な非線形項をconvex relaxationに置き換えて下界を計算します。代表的な考え方がMcCormick包絡で、双線形項 $xy$ を区間$[x_L,x_U]\times[y_L,y_U]$上で凸・凹な線形不等式の組で挟み、線形または凸な緩和問題に置き換えます。

$$
w \ge x_Ly + xy_L - x_Ly_L,\qquad w \ge x_Uy + xy_U - x_Uy_U
$$

のような不等式で$w\approx xy$を近似すると、region上の緩和問題（LPまたは凸QP）を解くだけで、元の非凸問題の下界が得られます。区間が狭いほどこの緩和はきつくなり、下界と実行可能解（incumbent）の差（gap）が小さくなります。

## bound gapで大域性を判断する

整数B&Bは離散変数の値を固定していくため、最終的に整数割当が尽きれば探索が完了します。空間branch-and-boundは連続区間を扱うため、区間をどこまでも細分でき、有限回で探索が尽きるとは限りません。

そこで、大域最適性は「探索を終えた」ことではなく、次のbound gapで判断します。

$$
\text{global bound} \le \text{incumbent} \le \text{global bound} + \text{gap tolerance}
$$

**bound gapが許容範囲に収まったこと**が、大域最適性の証明になります。緩和が緩いと下界が悪化します。緩和をきつくすると計算costが増えます。区間を狭めるほど緩和の質は上がりますが、木のnode数も増えます。

## 木が爆発する限界

McCormick包絡などの緩和は、変数次元が増えるほど、また非凸性が強い（非線形項が多い、非単調な関数を含む）ほど緩みやすくなります。緩和が緩いと、ある区間の下界がincumbentを超えられず枝刈りできません。さらに細かく分岐する必要が生まれ、次元数や非凸項の数に対して木が指数的に増える場合があります。

実務では、[SCIP](https://www.scipopt.org/doc/html/)のようなオープンソースsolverや、[Gurobi](https://docs.gurobi.com/projects/optimizer/en/current/)、[CPLEX](https://www.ibm.com/docs/en/icos)などの商用solverが、変数選択・区間分割の戦略、cut、presolveを組み合わせて木の増大を抑えています。

## 向いている条件

- 非凸MINLPで大域最適性の証明（gap付きのcertificate）が必要な場合
- 非線形項がMcCormick包絡などの凸緩和で扱える構造を持つ場合
- 変数次元や非凸項の数が、solverが現実的な時間で扱える範囲に収まる場合
- black-boxではなく、緩和に使える関数の代数的な形が分かっている場合

noiseを含むblack-box評価しかできない問題や、緩和のしようがない極端な非凸性を持つ問題では、gapを閉じるまでの木が非現実的に大きくなることがあります。その場合はheuristicや[Outer Approximation](#/learn/outer-approximation-minlp)（対象がconvex MINLPの場合）を検討します。

## Python

次は1変数の非凸関数に対する区間分割branch-and-boundの教育用ループです。各区間の下界を「区間端点での関数値の最小値」という単純な近似で代用しています。実際のMcCormick包絡のような凸下界ではありませんが、「区間を分割し、下界でincumbentを超えられない区間を刈る」という骨格を示します。

```python
from dataclasses import dataclass


def nonconvex_objective(x: float) -> float:
    return float(x**2 * (1.0 + 0.5 * (x - 1.0) ** 2) - 2.0 * x)


def interval_lower_bound(lower: float, upper: float, n_probe: int = 5) -> float:
    # 区間内をprobeして最小値を下界の代用とする教育用の簡略化。
    # 実務ではMcCormick包絡など凸緩和で真の下界を作る。
    step = (upper - lower) / (n_probe - 1) if n_probe > 1 else 0.0
    values = [nonconvex_objective(lower + i * step) for i in range(n_probe)]
    return min(values)


@dataclass
class Region:
    lower: float
    upper: float


def spatial_branch_and_bound(
    domain: Region, tol: float = 1e-3, max_nodes: int = 200
) -> tuple[float, float]:
    pending = [domain]
    best_value = nonconvex_objective(domain.lower)
    nodes_explored = 0

    while pending and nodes_explored < max_nodes:
        region = pending.pop()
        nodes_explored += 1
        bound = interval_lower_bound(region.lower, region.upper)

        if bound >= best_value - tol:
            continue  # この区間はincumbentを改善できないため枝刈り

        midpoint = 0.5 * (region.lower + region.upper)
        best_value = min(
            best_value, nonconvex_objective(region.lower), nonconvex_objective(region.upper)
        )

        if region.upper - region.lower > tol:
            pending.append(Region(region.lower, midpoint))
            pending.append(Region(midpoint, region.upper))

    return best_value, nodes_explored


best, nodes = spatial_branch_and_bound(Region(-2.0, 2.0))
print(best, nodes)
```

`interval_lower_bound`は真の凸緩和ではなくprobeによる近似であり、大域最適性の証明にはなりません。実務でMcCormick包絡や凸緩和solverを組み込む場合は、[SCIP](https://www.scipopt.org/doc/html/)や[Gurobi](https://docs.gurobi.com/projects/optimizer/en/current/)などの公式ドキュメントで対応する非線形項の種類とrelaxationの設定を確認します。

## 診断値

- incumbent / global bound / relative and absolute gap
- node数、open node数
- root relaxationのgap
- 区間の最小幅（分岐の細かさ）
- prune理由別のnode数
- memory
- termination reason（gap達成、time limit、node limit）

## 失敗・切替の兆候

- 緩和が緩くroot bound gapが大きい
- 木のnode数が次元・非凸項の増加に対して急増する
- 長時間incumbentが得られない
- 区間分割が特定の変数だけで進み他の非凸項の緩和が改善しない
- black-boxや不連続な評価をそのまま緩和しようとしている

## 次に読む

整数変数のみを分岐する基本形は[Branch-and-Bound](#/learn/branch-and-bound)、convex MINLPで整数と連続を分離して解く方式は[MINLPのOuter Approximation](#/learn/outer-approximation-minlp)、離散・組合せ最適化全体の選び分けは[離散・組合せ最適化の選び分け](#/learn/family.discrete-structure)で確認できます。
