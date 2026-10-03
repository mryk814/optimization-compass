---
content_id: dijkstra-astar
kind: method
method_id: M_DIJKSTRA_ASTAR
title_ja: Dijkstra法とA*探索
title_en: Dijkstra's Algorithm and A* Search
summary: 非負の重みを持つ有向・無向グラフで、確定済みの距離と過大評価しない見積り（admissible heuristic）を使い、最短路を厳密に求める探索法です。
source_ids: [S054]
prerequisites: [dynamic-programming]
related_ids: [dynamic-programming, cp-sat]
aliases: [/learn/dijkstra-astar]
status: published
last_reviewed: 2026-09-30
---

非負の重みを持つ有向・無向グラフで、確定済みの距離と過大評価しない見積り（admissible heuristic）を使い、最短路を厳密に求める探索法です。

## 30秒でつかむ

池に石を投げると、波紋が石のまわりに広がります。
Dijkstra法は、始点から近い順に、波紋のように探索の範囲を広げます。
A*探索は、ゴールの方向へ、波紋を偏らせて広げます。

- **見るもの**: 各探索点の暫定距離 $g(n)$。A*では、ゴールまでの残りコストの見積り $h(n)$ も
- **動かすもの**: 優先度付きキュー。優先度が最も小さい探索点を一つ取り出して確定し、隣の辺を緩める（relax）
- **前進の判断**: ゴールを取り出した時点で、ゴールまでの最短距離が確定する

ゴールに初めて届いた時点では、まだ確定しません。取り出すまで、より短い経路が見つかる可能性が残っています。

## 一手の意味

一手は、キューから優先度が最小の探索点を一つ取り出して確定し、そこから伸びる辺で隣の探索点の暫定距離を更新する操作です。

Dijkstra法は、始点からの暫定距離 $g(n)$ が最小の探索点を取り出します。
その探索点から伸びる辺を緩め、ゴールへ届くまで確定した領域を広げます。
辺のコストが非負なら、キューから取り出して確定した距離は、後から改善されません。

辺を緩めるとは、次の比較です。取り出した探索点 $u$ から辺 $(u,v)$ で $v$ へ行くとき、いまの暫定距離より短ければ更新します。

$$
g(v)\leftarrow \min\bigl(g(v),\; g(u)+w(u,v)\bigr)
$$

A*探索は、現在までのコストと、ゴールまでの残りコストの見積りを足した優先度で探索点を選びます。

$$
f(n)=g(n)+h(n)
$$

- $g(n)$: 始点から現在の探索点までに支払ったコスト
- $h(n)$: 現在の探索点からゴールまでに必要な残りコストの見積り

$h(n)=0$ なら、Dijkstra法と同じ優先度です。
$h$ が真の残りコストを過大評価しないなら（admissible）、A*も最適性を維持できます。
さらに、どの辺 $(u,v)$ でも $h(u)\le w(u,v)+h(v)$ が成り立つなら（consistent）、確定済みの探索点の再展開を抑えやすくなります。

## 小さな例

始点 S からゴール G までの最短路を、次の小さなグラフで求めます。数字は辺の重みで、辺は両向きに通れます。

| 辺 | S-A | S-C | S-B | C-G | B-G |
|---|---:|---:|---:|---:|---:|
| 重み | 1 | 2 | 4 | 6 | 3 |

A*で使う見積り $h$ は、ゴールまでの残りコストのおおよその値で、次の表のとおりとします。

| 探索点 | S | A | C | B | G |
|---|---:|---:|---:|---:|---:|
| 見積り $h$ | 6 | 7 | 5 | 3 | 0 |

どの辺でも $h(u)\le w(u,v)+h(v)$ が成り立つ（consistent）ことを確かめてあります。

### Dijkstra法

暫定距離 $g$ が小さい順に探索点を取り出します。

| 順 | 取り出す探索点 | $g$ | 辺を緩めた結果 |
|---:|---|---:|---|
| 1 | S | 0 | A=1、C=2、B=4 を記録 |
| 2 | A | 1 | 先に進む辺なし（Aの隣はSだけで、確定済み） |
| 3 | C | 2 | G=2+6=8 を記録 |
| 4 | B | 4 | G=4+3=7 に更新（8より短い） |
| 5 | G | 7 | ゴールを取り出した。最短距離は7 |

順3でGに届いていますが、その時点の距離8は暫定です。順4で、Bを経由する距離7が見つかりました。ゴールを取り出すまで待つ理由が、ここにあります。
最短路は S→B→G で、コストは 7 です。取り出した探索点は 5 個でした。

### A*探索

優先度 $f=g+h$ が小さい順に取り出します。

| 順 | 取り出す探索点 | $g$ | $f=g+h$ | 辺を緩めた結果 |
|---:|---|---:|---:|---|
| 1 | S | 0 | 6 | A: $f=1+7=8$、C: $f=2+5=7$、B: $f=4+3=7$ を記録 |
| 2 | B | 4 | 7 | G: $g=7$、$f=7$ を記録 |
| 3 | G | 7 | 7 | ゴールを取り出した。最短距離は7 |

順2では、CとBの優先度が $f=7$ で同点です。同点のときは $h$ が小さい方（B）を先に取り出します。
順3でも、Cとゴールが $f=7$ で同点です。ゴールは $h=0$ なので先に取り出され、Cは展開されずに終わります。

同じ最短距離 7 が、取り出した探索点 3個で求まりました。A（優先度8）は取り出されず、C（優先度7）は同点の処理で後回しになりました。どちらも展開されずに、ゴールが確定しています。
見積りが真の残りコスト以下（admissible）でなければ、この省略は最適な経路を落とすことがあります。

### 格子で見る

次の固定した格子では、どちらもコスト24の最短路を返します。違うのは、ゴールに着くまでに展開したセルの範囲です。

![17列11行の固定格子をDijkstra法とManhattan距離の見積り付きA*探索で解いた実行結果。上段のDijkstra法は始点から全方向へ広がり168格子要素を展開する。下段のA*は目標方向へ探索を絞り92格子要素を展開する。障害物を避ける経路は異なるが、どちらの最短経路費用も24である。](./media/dijkstra-astar-grid-execution.svg "固定した単位費用の 4近傍格子のPythonだけで実行した結果です。A*の展開数はDijkstra法より45%少なくなりますが、別グラフ、重み、tie-break、ヒューリスティクス一般の削減率や実行時間は示しません。")

淡い橙が展開済みのセル、青緑が返された最短路です。
A*は168セルから92セルへ、展開の範囲を減らしました。
これは、この格子とManhattan距離の見積りで得た固定の結果です。

> 両者の最短コストは同じ24です。
> 経路そのものは複数あるため、返された経路の形が同じである必要はありません。
> 展開数の45%削減は一般性能順位付けではありません。

## 向く条件・避ける条件

使う前に、次を確認します。

- 辺の重みは非負か
- コストの単位は揃い、経路上で加算できるか
- 探索点と辺は、問題の`state`と遷移を表しているか
- `side constraint`は、`path state`へ含まれているか

単純な最短路（[最短路問題](#/formulations/PA029)）は、MIPへ変換しても解けます。
専用の方法はグラフの構造を直接利用するので、保証と診断値を対応づけやすくなります。

ただし、次の`side constraint`が増えると、専用の構造が崩れる場合があります。

- 複数の資源の容量
- 時間窓
- 経路全体に依存する論理条件
- 集荷と配達（pickup and delivery）
- 複数車両の相互作用
- 負の辺や、閉路に関する条件

この場合は、`state`を拡張したDPや、資源制約付き最短路（資源制約付き最短路）を検討します。[CP-SAT](#/learn/cp-sat)やMIPも候補です。

## Python

小さな例を、Dijkstra法（$h=0$）とA*探索で解きます。表の取り出し順が、出力に対応します。

```python
import heapq

graph = {  # 辺の重み（無向）
    "S": {"A": 1, "C": 2, "B": 4},
    "A": {"S": 1},
    "C": {"S": 2, "G": 6},
    "B": {"S": 4, "G": 3},
    "G": {"C": 6, "B": 3},
}
estimate = {"S": 6, "A": 7, "C": 5, "B": 3, "G": 0}  # goal までの残りコストの見積り h
# 一貫性（consistency）の確認: h(u) <= w(u, v) + h(v)
assert all(estimate[u] <= w + estimate[v] for u in graph for v, w in graph[u].items())


def search(h, start="S", goal="G"):
    distance = {start: 0}
    queue = [(h[start], h[start], start)]  # (優先度 f, 同点のときの h, node)
    closed = []
    while queue:
        priority, _, node = heapq.heappop(queue)
        if node in closed:
            continue
        closed.append(node)
        print(f"  取り出す {node}: g={distance[node]}, f={priority}")
        if node == goal:
            break
        for neighbor, weight in graph[node].items():
            candidate = distance[node] + weight
            if candidate < distance.get(neighbor, float("inf")):
                distance[neighbor] = candidate
                heapq.heappush(queue, (candidate + h[neighbor], h[neighbor], neighbor))
    return distance[goal], closed


print("Dijkstra法（h = 0）")
print(search({node: 0 for node in graph}))
print("A*探索")
print(search(estimate))
```

```text
Dijkstra法（h = 0）
  取り出す S: g=0, f=0
  取り出す A: g=1, f=1
  取り出す C: g=2, f=2
  取り出す B: g=4, f=4
  取り出す G: g=7, f=7
(7, ['S', 'A', 'C', 'B', 'G'])
A*探索
  取り出す S: g=0, f=6
  取り出す B: g=4, f=7
  取り出す G: g=7, f=7
(7, ['S', 'B', 'G'])
```

### 格子の実行

図と同じ格子を解きます。`use_heuristic=False` がDijkstra法、`True` がManhattan距離の見積り付きA*です。

```python
import heapq

WIDTH, HEIGHT = 17, 11
START = (1, 5)
GOAL = (15, 5)
OBSTACLES = (
    {(6, y) for y in range(1, 10) if y != 2}
    | {(11, y) for y in range(1, 10) if y != 8}
)


def shortest_path(
    *,
    use_heuristic: bool,
) -> tuple[int, tuple[tuple[int, int], ...], tuple[tuple[int, int], ...]]:
    def heuristic(node: tuple[int, int]) -> int:
        if not use_heuristic:
            return 0
        return abs(GOAL[0] - node[0]) + abs(GOAL[1] - node[1])

    distance = {START: 0}
    predecessor = {}
    queue = [(heuristic(START), heuristic(START), START)]
    closed = set()
    expanded = []

    while queue:
        _, _, node = heapq.heappop(queue)
        if node in closed:
            continue
        closed.add(node)
        expanded.append(node)
        if node == GOAL:
            break

        for dx, dy in ((1, 0), (0, 1), (-1, 0), (0, -1)):
            neighbor = (node[0] + dx, node[1] + dy)
            inside = 0 <= neighbor[0] < WIDTH and 0 <= neighbor[1] < HEIGHT
            if not inside or neighbor in OBSTACLES:
                continue
            candidate = distance[node] + 1
            if candidate >= distance.get(neighbor, WIDTH * HEIGHT + 1):
                continue
            distance[neighbor] = candidate
            predecessor[neighbor] = node
            priority = candidate + heuristic(neighbor)
            heapq.heappush(queue, (priority, heuristic(neighbor), neighbor))

    path = [GOAL]
    while path[-1] != START:
        path.append(predecessor[path[-1]])
    path.reverse()
    return distance[GOAL], tuple(path), tuple(expanded)


for name, use_heuristic in (("Dijkstra", False), ("A*", True)):
    cost, path, expanded = shortest_path(use_heuristic=use_heuristic)
    print(f"{name}: cost={cost}, expanded={len(expanded)}, path nodes={len(path)}")
```

```text
Dijkstra: cost=24, expanded=168, path nodes=25
A*: cost=24, expanded=92, path nodes=25
```

図と出力は、この同じ条件と同点の処理（tie-break）で生成しています。

## 診断値

- 展開した探索点数
- 緩めた辺の数
- 優先度付きキューの大きさ
- 再展開した探索点数（A*）
- 見積りの誤差と一貫性（見積りの誤差と一貫性）
- メモリ
- ゴールのコストと下界

判断の目安は次のとおりです。
展開数がDijkstra法とほとんど変わらないなら、見積りが弱いと考えます。
再展開が多いなら、見積りが一貫していない可能性があります。

::: warning
地図上の直線距離は、常に安全な見積りとは限りません。
割引や瞬間移動の辺で、実際のコストが地理的な距離より小さくなる場合は、過大評価しないこと（admissibility）を確認します。
:::

## 失敗・切替の兆候

| 症状 | 考えられる原因 | 対処 |
|---|---|---|
| 状態が爆発してメモリが増える | `state`にため込む情報が多い | `state`の設計を見直す。支配関係で刈る。[動的計画法](#/learn/dynamic-programming)の考え方を使う |
| Dijkstra法と同程度に展開する | 見積りが弱い | より強い（ただし過大評価しない）見積りを探す |
| 最適でない経路を返す | 見積りが過大評価している | 見積りが真の残りコスト以下かを確かめる |
| 経路が制約を破っている | `side constraint`を`node state`に入れ忘れた | `state`を拡張する。[CP-SAT](#/learn/cp-sat)やMIPを検討する |
| 負の辺があって結果がおかしい | 負の辺にはDijkstra法が使えない | 負の辺を扱える別の最短路法を使う |
| 経路のコストが加法的でない | 単純な辺の和に落とせない | `state`を拡張するか、別の定式化にする |

## 次に読む

- [最短路問題](#/formulations/PA029)：小さな例の問題を定式化から読み直す
- [動的計画法](#/learn/dynamic-programming)：`state`を拡張して履歴を扱う
- [CP-SAT](#/learn/cp-sat)：論理制約やスケジューリングを含む場合
