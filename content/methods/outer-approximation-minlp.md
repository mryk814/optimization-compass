---
content_id: outer-approximation-minlp
kind: method
method_id: M_OUTER_APPROX_MINLP
title_ja: MINLPのOuter Approximation
title_en: Outer Approximation for MINLP
summary: 整数変数を扱う主問題と、整数を固定した連続NLPを交互に解き、凸な非線形情報を切除平面として主問題へ戻す厳密探索法です。
source_ids: [S021, S024, S028, S056]
related_ids: [branch-and-cut, constrained-continuous]
status: published
last_reviewed: 2026-09-30
---

整数変数を扱う主問題と、整数を固定した連続NLPを交互に解き、凸な非線形情報を切除平面として主問題へ戻す厳密探索法です。

## 30秒でつかむ

整数候補の担当者と連続量の担当者が、候補と線形のメモを交互に受け渡します。

整数の組合せを選ぶ問題と、その候補で連続変数を詰める問題へ分けます。
連続側で得た接線の情報を、切除平面として整数側へ返します。

- 見ているもの: MILPの主問題の界、NLP部分問題の可行解、勾配、切除平面
- 動かしているもの: 整数候補、連続解、線形化した切除平面、最良可行解
- 前進の判断: 主問題の界と最良の実行可能解のギャップが縮むか
- 別に確認するもの: MILPとNLPそれぞれの計算費用、大域ギャップ、停止理由
- 恐れていること: 非凸連続部分、弱い切除平面、NLPの求解失敗、不適切なBig-M

有限反復の証明を期待できるのは、連続部分の凸性など必要な前提が満たされ、ソルバーが正しく処理する場合です。

## 一手の意味

凸関数の接線は、元の関数全体の下界になります。

$$
f(x)\ge f(x_k)+\nabla f(x_k)^T(x-x_k)
$$

目的の補助変数や凸な制約へこの線形化を加え、主問題の緩和を強めます。

### 仕組み

基本サイクルは次です。

1. 線形化した切除平面を含むMILPの主問題から整数候補を得る
2. その整数を固定して連続NLPを解く
3. 可行なら最良可行解を更新する
4. NLPの勾配から目的値・制約の線形化した切除平面を作る
5. 主問題へ切除平面を加え、界と最良可行解のギャップが閉じるまで繰り返す

NLPが実行不可能な場合には実行可能性を調べる部分問題や候補の再訪を防ぐ切除平面など、実装ごとの処理が必要です。

## 小さな例

$y\in\{0,1,2\}$、$x=y$ のもとで $(x-1.2)^2+0.1y$ を最小化します。
連続目的を $f(x)=(x-1.2)^2$ とし、補助変数 $\theta$ へ接線による下界を追加します。
初期接線は $x=1.2$ の $\theta\ge0$ です。

| 反復 | 主問題が選ぶ $y$ | 主問題の下界 | 候補の目的値 | 最良可行値 |
|---|---:|---:|---:|---:|
| 1 | 0 | 0.00 | 1.44 | 1.44 |
| 2 | 1 | 0.10 | 0.14 | 0.14 |
| 3 | 1 | 0.14 | 0.14 | 0.14 |

$x=0$ の接線を返すと、次は $y=1$ を選びます。
$x=1$ の接線を加えると下界と可行値が一致します。
小さな整数候補を全列挙した主問題で、MILP探索木を再現する例ではありません。

## 向く条件・避ける条件

### まず確認すること

| 項目 | 確認内容 |
|---|---|
| 変数 | 整数・二値変数と連続変数が混在するか |
| 凸性 | 整数を固定したNLPが凸か |
| 微分 | 目的関数と制約の勾配を得られるか |
| 定式化 | 指示変数、Big-M、上下限が妥当か |
| 実行可能性 | 整数候補ごとのNLPが実行不可能になりうるか |
| 保証 | 大域ギャップや証明が必要か |

非凸MINLPでは通常のOuter Approximationの切除平面が大域的に有効とは限りません。
空間分枝限定法など別の大域的な手法が必要です。

### 向く条件・避ける条件

向きやすい条件:

- 凸MINLP
- 整数を固定したNLPを安定して解ける
- 勾配を利用できる
- MILPの主問題へ強い切除平面を追加できる
- 実行可能解と大域ギャップの両方が必要

避ける条件:

- 一般非凸MINLPを凸とみなす
- ブラックボックス・ノイズを含む非線形評価
- 上下限がなくBig-Mが極端に大きい
- NLP部分問題が頻繁に失敗する

## Python

小さな例の計算を再現する、実行可能な教育用コードです。

```python
cuts = [(1.2, 0.0)]
incumbent = float("inf")
for iteration in range(1, 4):
    candidates = []
    for y in range(3):
        theta = max(0.0, max(
            value + 2.0 * (point - 1.2) * (y - point)
            for point, value in cuts
        ))
        candidates.append((theta + 0.1 * y, y))
    master_bound, y = min(candidates)
    nlp_value = (y - 1.2) ** 2 + 0.1 * y  # 等式 x=y で連続解は一意
    incumbent = min(incumbent, nlp_value)
    cuts.append((float(y), (y - 1.2) ** 2))
    print(iteration, y, master_bound, nlp_value, incumbent)
    if incumbent - master_bound <= 1e-10:
        break
```

```text
from dataclasses import dataclass


@dataclass
class SubproblemResult:
    feasible: bool
    objective: float
    point: tuple[float, ...]


def outer_approximation(max_iterations: int = 20) -> SubproblemResult | None:
    cuts: list[object] = []
    incumbent: SubproblemResult | None = None

    for _ in range(max_iterations):
        integer_candidate = solve_milp_master(cuts)
        subproblem = solve_fixed_integer_nlp(integer_candidate)

        if subproblem.feasible:
            if incumbent is None or subproblem.objective < incumbent.objective:
                incumbent = subproblem
            cuts.extend(linearize_at(subproblem.point))
        else:
            cuts.append(build_feasibility_cut(integer_candidate))

        if master_gap_is_closed(incumbent):
            break

    return incumbent
```

このコードはアルゴリズムの責務を示す教育用骨格です。
`solve_milp_master`などは利用ソルバーに合わせて実装します。

## 診断値

見る値:

- 最良可行解と主問題の界
- 最適性ギャップ
- 主問題の反復数
- NLP 成功 / 実行不可能数
- 切除平面追加数と切除平面の違反
- 同じ整数候補の再訪
- MILPの節点数とNLPの評価費用

最良可行解と主問題の界を保存します。
最適性ギャップと部分問題の状態も別々に保存します。
どれか一つが改善しても、大域最適性の証明が成立したとは限りません。

## 失敗・切替の兆候

- 切除平面を増やしても界が動かない → 定式化と線形化を見直す
- NLPの求解失敗が多い → 初期点、尺度調整、実行可能性処理を確認
- 非凸性で切除平面が無効 → 空間分枝限定法へ
- 整数候補を何度も再訪 → 候補の再訪を防ぐ切除平面や主問題の許容誤差を確認
- 早い可行解だけ必要 → ヒューリスティックや制限時間を設ける方針を検討

### コラム: 分解と大域性

整数と連続を分けたから自動的に簡単になるわけではありません。
主問題の緩和とNLPの条件数が、部分問題の難しさに影響します。
切除平面の強さと整数候補の数も、全体の計算費用を決めます。

MILP側の探索は[Branch-and-Cut](#/learn/branch-and-cut)、連続部分問題は[制約付き連続最適化](#/learn/constrained-continuous)を参照し、両者の状態を別々に保存してください。

## 次に読む

[Branch-and-Cut](#/learn/branch-and-cut)で主問題の探索を確認します。
[制約付き連続最適化](#/learn/constrained-continuous)で連続部分問題を確認します。

- 問題の形を確認する: [混合整数非線形計画](#/formulations/PA025)
