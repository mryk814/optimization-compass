# Nested and equilibrium Theater の読み方

Issue #140 では、bilevel optimization、equilibrium-constrained optimization、complementarity、hybrid systems を同じ「複雑な最適化」として扱わず、観測する構造を分ける。

この設計メモは、新しい canonical ID や renderer を追加する前に、現在の VisualizationScenario 契約で表現できる範囲を固定する。

## 現在の Theater に置く読み方

Theater の入口では、目的値だけでなく、run の学習目的、primary observables、停止条件、適用範囲の限界を同じ文脈で表示する。

| 構造 | まず分けて読む値 | 取り違えてはならないもの |
| --- | --- | --- |
| nested solve | outer progress、inner residual、solve tolerance | 外側の1回の更新と、内側 solve の収束を同じ iteration と数えること |
| equilibrium / complementarity | objective、residual、constraint violation、smoothing parameter | exact complementarity と penalty / smoothing による近似 |
| hybrid / mode | mode sequence、switching event、active mode、chattering | prescribed mode schedule と mode discovery |

現在の公開 scenario は、これらの構造固有の観測量をまだ一つの新しい schema に統合していない。

したがって、既存のカードは scenario が宣言した `lesson.primary_observables` を表示し、未宣言の inner accuracy、complementarity gap、mode sequence を推測して補わない。

## 既存契約との対応

新しい scenario を設計するときは、まず既存のフィールドで学習内容を表せるか確認する。

- `lesson.learning_objective` は、何を理解する run かを一文で示す。
- `lesson.primary_observables` と `secondary_observables` は、図と text alternative が追う値を分ける。
- `lesson.success_signals` と `failure_signals` は、受理された更新と、残差増大や mode chattering などの現象を区別する。
- `experiment.stopping` は、outer iteration、inner tolerance、residual threshold などの停止条件を保持する。
- `lesson.limitations_ja` は、exact solve、truncated / unrolled solve、relaxation、fixed mode schedule のどこまでを示すかを限定する。

これらのフィールドだけでは、inner solve の計算費用や mode discovery の探索空間を十分に表せない場合がある。

その場合は、数値を一つの目的値履歴へ押し込まず、contract 拡張を別 Issue として設計する。

## 最初の旗艦 Case に必要な境界

最初の nested / equilibrium / hybrid Case は、小さい固定例で次の境界を表示する。

1. inner solve が exact、truncated、unrolled のどれか。
2. bilevel の解釈が optimistic か pessimistic か。
3. 微分している対象が solver の反復か、解写像か。
4. complementarity が exact か、penalty / smoothing / relaxation か。
5. mode schedule が prescribed か、候補から discovery するか。
6. stationarity、feasibility、constraint qualification のどれを保証し、どれを保証しないか。

固定例の教育的な収束結果は、一般の bilevel、MPEC、接触問題、hybrid system の性能保証にならない。

## 出典

- [The Standard Pessimistic Bilevel Problem](https://epubs.siam.org/doi/abs/10.1137/18M119759X?download=true&journalCode=sjope8)
- [A class of smoothing methods for mathematical programs with complementarity constraints](https://www.sciencedirect.com/science/article/pii/S0096300306007016)
- [Optimal mode-switching for hybrid systems with varying initial states](https://www.sciencedirect.com/science/article/abs/pii/S1751570X07001513)
