# ADR 0017: 定式化を学習の背骨にし、道筋で順序を与える

- Status: accepted
- Date: 2026-09-30
- Related: ADR 0002, ADR 0010, ADR 0013, [`docs/product-direction/learning-atlas.md`](../product-direction/learning-atlas.md)

## Context

Optimization Compass は、手法・実装・根拠・推薦規則・可視化の基盤を厚く持っています。
それでも「最適化を理解したい人」が使い続ける理由が弱い状態でした。原因は次の3つです。

1. **学習者の単位である「定式化」にページがない。** DBには57の問題型（`problem_archetypes`）があるのに、URLがなく、標準形の数式もなく、説明は `線形計画。変数=continuous、目的=linear、制約=linear。` のような機械的な要約でした。学習者が「二次錐計画って何？」と引く場所がありません。
2. **順序がない。** Learn は128件のカードの平らな一覧で、どこから読み、読んだ後に何へ進むかが示されません。`learning_edges`（53本）は各ページの脇に関係として出るだけです。
3. **入口が「自分の問題を持っている人」前提。** Home の主行動は診断と事例で、理解を深めたい人の主行動がありませんでした。

## Decision

### 1. 定式化の辞書（formulation atlas）

すべての問題型に `/formulations/<PROBLEM_ID>` のページを与え、学習の背骨にします。

| 何を | どこに書くか | authority |
|---|---|---|
| 問題型のID・名前・記述子・手法の適合度・代替解法 | released SQLite | 既存のまま（変更しない） |
| 系統（family）、標準形（LaTeX）、読み下し、見分けの手がかり、形どうしの関係 | `data/seeds/formulation_atlas.json` | 新しい authored seed |
| 解説本文 | `content/concepts/*.md`（`canonical_entity_type: problem`、`canonical_entity_id: PAxxx`） | 既存の content 契約 |
| 公開データ | `site/public/data/formulation-atlas.json`（contract 1.0.0） | 生成物 |

- seed は **全問題型を必ず1回ずつ** 含みます。記事がなくても、標準形・読み下し・関係・手法の候補を持つ「骨格ページ」が最初から公開されます。辞書の網羅性は骨格が保証し、記事は後から肉付けします。
- 関係は4種類に限ります: `special_case_of`（特別な場合）、`relaxes_to`（緩和）、`reformulates_to`（書き換え）、`contrasts_with`（似て非なる）。`special_case_of` と `relaxes_to` は循環を禁止します。各関係は、成り立つ条件を1文の `note_ja` で必ず述べます。
- 画面では関係を「定式化のコンパス」として示します。北＝より一般の形、南＝より特別な形、東＝緩和・書き換えの行き先、西＝ここへ来る元の形です。
- 問題型の entity link の canonical URL を `/formulations/<id>` にします。問題型を説明する記事の `/learn/<content_id>` は、手法記事と同じく alias として定式化ページへ redirect します。
- 系統には `lens` を持たせ、「式の形で分ける型（form）」「評価の事情で分ける型（oracle）」「使う場面で分ける型（application）」を区別します。black-box や HPO は式の形ではなく事情の分類であることを、学習者に隠しません。

### 2. 定式化記事の型

定式化記事は文字数ではなく、次の8節をこの順で持つことを公開条件にします（`content_quality.formulation_skeleton_gaps`）。

`30秒でつかむ → 標準形を読む → 小さな例 → 見分け方 → 近い定式化 → 解き方の系統 → つまずきやすい点 → 次に読む`

「小さな例」は、手で確かめられる数値と、実行して同じ数値が出るコードを持ちます。

### 3. 学ぶ道筋（learning paths）

`data/seeds/learning_paths.json` に、定式化と記事を「問い」でつないだ順路を書きます。

- 各ステップは `formulation` か `content` を指し、そのステップが答える **問い（`question_ja`）** を必ず持ちます。見出しではなく問いが、読者を次へ引っ張る単位です。
- 記事の `prerequisites` が同じ道筋の後ろにあれば、export が失敗します。
- 骨格しかない定式化もステップにできます（「解説は準備中」と表示）。道筋が、次に書くべき記事を示します。
- 公開データは `site/public/data/learning-paths.json`（contract 1.0.0）。進み具合は閲覧者のブラウザの `localStorage` にだけ置き、なくても動きます。
- ステップのページには、どのページでも共通に、上部に「道筋の位置と、この項の問い」、下部に「次の問い」カードを出します。各ページは道筋の存在を知る必要がありません（ルートの一致で判定）。

### 4. 入口

- Home は「学ぶ（道筋・辞書）」と「解く（診断・事例）」の2つの入口を並べます。
- 主ナビゲーションは `道筋・辞書・手法・診断・事例` の短い名詞にし、375px でもすべて見えるようにします。

## Consequences

- 新しい問題型を DB に追加すると、formulation seed を更新するまで export が失敗します。辞書の欠けを作らないための意図した摩擦です。
- 問題型の記事を1本書くと、その型の定式化ページ・道筋・entity link・検索がすべて更新されます。
- `SiteManifest` は 1.5.0 になり、`formulation_atlas` と `learning_paths` を持ちます。
- 次に書くべき記事は `scripts/formulation_backlog.py` が、道筋・事例・関係からの参照数で順位付けします。

## Rejected alternatives

- **関係を記事の frontmatter に書く**: 関係が記事のない型にも必要で、両端の記事に重複して書くことになるため採りません。
- **関係を `learning_edges` へ migration で追加する**: release 境界の変更になり、教育上の構造を試しながら育てる速度が出ません。関係の意味が安定したら、`learning_edges` への昇格を別途検討します。
- **全型の記事が揃うまで辞書を公開しない**: 骨格だけでも標準形・関係・候補手法で引く価値があり、欠けが見えること自体が次の執筆を促します。
