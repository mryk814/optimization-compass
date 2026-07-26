---
content_id: spatial-branch-and-bound
kind: method
method_id: M_SPATIAL_BRANCH_BOUND
title_ja: 空間branch-and-bound
title_en: Spatial Branch and Bound
summary: 非凸MINLPで連続変数の区間も分岐し、各領域の凸緩和から下界を作ります。下界と実行可能解のgapを閉じながら、大域最適性を確かめる厳密探索法です。
source_ids: [S021, S024, S025]
prerequisites: []
related_ids: [branch-and-bound, outer-approximation-minlp, family.discrete-structure]
status: published
last_reviewed: 2026-07-26
---

非凸MINLPで連続変数の区間も分岐し、各領域の凸緩和から下界を作ります。下界と実行可能解のgapを閉じながら、大域最適性を確かめる厳密探索法です。

## 何を分岐しているか

[整数B&B](#/learn/branch-and-bound)は、整数変数の値を固定または分割してnodeを作ります。
空間branch-and-boundは、非凸な非線形項を含む連続変数の**区間**でも分岐します。

たとえば非凸項 $xy$（双線形項）があるとします。
$x$の区間$[x_L, x_U]$を、$[x_L, m]$と$[m, x_U]$へ分けます。
二つの部分区間は、別々のnodeとして評価されます。

## 各領域で下界をどう作るか

分岐で得られた各区間では、非凸な非線形項をconvex relaxationへ置き換えて下界を計算します。
代表例はMcCormick包絡です。
双線形項 $xy$ を区間$[x_L,x_U]\times[y_L,y_U]$上で線形不等式の組により挟みます。

$$
w \ge x_Ly + xy_L - x_Ly_L,\qquad w \ge x_Uy + xy_U - x_Uy_U
$$

このような不等式で$w\approx xy$を緩和します。
region上のLPまたは凸QPを解くと、元の非凸問題に対する下界が得られます。
区間が狭くなるほど緩和はきつくなり、下界と実行可能解（incumbent）のgapが縮みます。

## bound gapで大域性を判断する

整数B&Bでは、整数割当が尽きれば探索が完了します。
空間branch-and-boundが扱う連続区間は、どこまでも細分できます。
有限回で探索が尽きるとは限りません。

大域最適性は「区間をすべて分けた」ことではなく、次のbound gapで判断します。

$$
\text{global bound} \le \text{incumbent} \le \text{global bound} + \text{gap tolerance}
$$

**bound gapが許容範囲に収まったこと**が、指定したtoleranceでの大域最適性certificateになります。
ただし、緩い緩和は下界を悪化させます。
区間を狭めれば緩和の質は上がりますが、木のnode数が増えます。

次の図は、後半のPython例と同じ固定多項式を実行した結果です。
赤い区間は、区間下界がincumbent以上になったため捨てられました。

![固定1変数多項式をinterval arithmetic lower boundで空間branch-and-boundした結果。目的関数ではx=1のincumbentが得られ、停止時の区間partitionではboundで捨てた区間と未確定のopen区間を分けている。70 nodeの処理でglobal lower boundが-4から-1.010まで上がり、incumbent -1との差が0.0095になった。](./media/spatial-branch-bound-execution.svg "pure Pythonで生成した固定1変数教材です。妥当なinterval lower boundによる枝刈りとgapの推移を示します。McCormick relaxation、多変数MINLP、solver一般の性能やgap 0の厳密解は示しません。")

緑のopen区間が残っていても、最良の下界とincumbentの差は0.01未満です。
「すべての区間を消す」のではなく、「残った区間でも0.01以上は改善できない」と読めます。

## 木が爆発する限界

McCormick包絡などの緩和は、変数次元や非凸項が増えると緩くなりやすい性質があります。
下界がincumbentへ近づかなければ、区間を枝刈りできません。
分岐が続き、木のnode数が急増する場合があります。

実務では[SCIP](https://www.scipopt.org/doc/html/)、[Gurobi](https://docs.gurobi.com/projects/optimizer/en/current/)、[CPLEX](https://www.ibm.com/docs/en/icos)などのsolverを利用できます。
各solverは変数選択と区間分割を行い、cutやpresolveも組み合わせます。

## 向いている条件

- 非凸MINLPで大域最適性の証明（gap付きのcertificate）が必要な場合
- 非線形項がMcCormick包絡などの凸緩和で扱える構造を持つ場合
- 変数次元や非凸項の数が、solverが現実的な時間で扱える範囲に収まる場合
- black-boxではなく、緩和に使える関数の代数的な形が分かっている場合

noiseを含むblack-box評価しかできない問題や、緩和のしようがない極端な非凸性を持つ問題では、gapを閉じるまでの木が非現実的に大きくなることがあります。その場合はheuristicや[Outer Approximation](#/learn/outer-approximation-minlp)（対象がconvex MINLPの場合）を検討します。

## Python

次は図を生成した1変数の教育用ループです。
区間演算（interval arithmetic）で**必ず目的関数以下になる下界**を作り、gapが0.01以下になるまでbest-bound searchを続けます。

```python
def nonconvex_objective(x: float) -> float:
    return float(x**2 * (1.0 + 0.5 * (x - 1.0) ** 2) - 2.0 * x)


def square_interval(lower: float, upper: float) -> tuple[float, float]:
    minimum = 0.0 if lower <= 0.0 <= upper else min(lower**2, upper**2)
    return minimum, max(lower**2, upper**2)


def interval_lower_bound(lower: float, upper: float) -> float:
    x_squared = square_interval(lower, upper)
    shifted_squared = square_interval(lower - 1.0, upper - 1.0)
    product_lower = x_squared[0] * shifted_squared[0]
    return x_squared[0] + 0.5 * product_lower - 2.0 * upper


def spatial_branch_and_bound(
    gap_tolerance: float = 0.01, max_nodes: int = 256
) -> tuple[float, float, float, int]:
    pending = [(interval_lower_bound(0.0, 2.0), 0.0, 2.0)]
    best_x, incumbent = 0.0, nonconvex_objective(0.0)
    nodes_explored = 0

    while pending and nodes_explored < max_nodes:
        pending.sort()
        bound, lower, upper = pending.pop(0)
        if bound >= incumbent:
            continue
        if incumbent - bound <= gap_tolerance:
            pending.append((bound, lower, upper))
            break

        midpoint = 0.5 * (lower + upper)
        for candidate in (lower, midpoint, upper):
            value = nonconvex_objective(candidate)
            if value < incumbent:
                best_x, incumbent = candidate, value

        for child in ((lower, midpoint), (midpoint, upper)):
            child_bound = interval_lower_bound(*child)
            if child_bound < incumbent:
                pending.append((child_bound, *child))
        nodes_explored += 1

    global_bound = min((bound for bound, _, _ in pending), default=incumbent)
    return best_x, incumbent, global_bound, nodes_explored


print(spatial_branch_and_bound())
# (1.0, -1.0, -1.0095138549804688, 70)
```

この下界は、$x^2$と$(x-1)^2$が非負であることを使った区間演算です。
probe値ではないため、枝刈りの根拠にできます。
ただし変数の依存関係を重複して評価するため、McCormick包絡などより緩くなる場合があります。

実務で凸緩和solverを使う場合は、[SCIP](https://www.scipopt.org/doc/html/)や[Gurobi](https://docs.gurobi.com/projects/optimizer/en/current/)の公式文書で対応する非線形項とrelaxation設定を確認します。

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

整数変数だけを分岐する基本形は[Branch-and-Bound](#/learn/branch-and-bound)で確認できます。
convex MINLPで整数と連続を分ける方式は[MINLPのOuter Approximation](#/learn/outer-approximation-minlp)です。
[離散・組合せ最適化の選び分け](#/learn/family.discrete-structure)では、問題構造から候補を比較できます。
