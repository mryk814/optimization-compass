# 定式化の辞書と学ぶ道筋を育てる

定式化の辞書（`/formulations`）と学ぶ道筋（`/paths`）は、学習者向けの背骨です。
設計判断は [ADR 0017](adr/0017-formulation-atlas-and-learning-paths.md) にあります。この文書は手順書です。

## 育て方の全体像

```text
骨格（全57型・最初から公開）        肉付け（1本ずつ）              順路（問いでつなぐ）
data/seeds/formulation_atlas.json → content/concepts/<型>.md   → data/seeds/learning_paths.json
  標準形・読み下し・手がかり・関係      動く図を中心にした解説          ステップ＝問い＋ページ
            └──────────── export-site-data が全部を検証し、辞書・コンパス・道筋を生成 ────┘
```

次に何を書くかは、推測ではなく参照数で決めます。

```bash
uv run optimization-compass export-site-data --output site/public/data
uv run python scripts/formulation_backlog.py --limit 10
```

道筋のステップ・公開事例・関係から多く参照されているのに記事がない型が、上位に出ます。

## レシピ A — 定式化の記事を書く

1. `scripts/formulation_backlog.py` の上位から1つ選び、`site/public/data/formulation-atlas.json` で、その型の標準形・関係・手法の候補を読みます。
2. `content/concepts/<kebab-name>.md` を作ります。frontmatter は次の形です。

   ```yaml
   ---
   content_id: concept.<kebab-name>
   kind: concept
   canonical_entity_type: problem
   canonical_entity_id: PA0xx
   title_ja: 日本語名（略称）
   title_en: English Name
   summary: カードと検索に出る1〜2文。本文の書き出しとは別に書く。
   prerequisites: [concept.xxx]
   related_ids: [method-content-id]
   source_ids: [S054, S055]
   status: published
   last_reviewed: YYYY-MM-DD
   ---
   ```

3. 本文は [`docs/writing-articles.md`](writing-articles.md) に沿って書きます。節の並びは決まっていません。定式化の記事では、読者が自分の課題をこの形だと見分けられ、小さな例を解け、合わないときの行き先が分かることを目指します。標準形と性質のカード、定式化のコンパス（関係の一覧）、ソルバーの一覧はページの枠が出すので、本文で一覧にし直しません。
4. 例の数値とコードは、実際に実行して確かめます。プロジェクト本体に数値計算ライブラリを足さず、一時環境で動かします。

   ```bash
   uv run --no-project --with scipy --with numpy python example.py
   ```

5. 動く図は、既存の explorable を再利用するか、[`docs/explorables.md`](explorables.md) の手順で追加します。
6. export して、辞書・定式化ページ・道筋の表示を確かめます。

## レシピ B — 形どうしの関係を足す

`data/seeds/formulation_atlas.json` の `relations` に1行足します。

```json
{"from": "PA005", "to": "PA033", "type": "special_case_of", "note_ja": "残差が線形なら…になります。"}
```

- `special_case_of`: from は to の特別な場合（from ⊂ to）。コンパスでは from の北に to が出ます。
- `relaxes_to`: from の条件を外すと to になる。to の最適値が from の界になる場合に使います。
- `reformulates_to`: 条件付きで from を to の形に書き直せる。条件を `note_ja` に必ず書きます。
- `contrasts_with`: 似て見えるが性質が違う。向きは持ちません。
- 推移的に導ける関係（LP ⊂ SDP など）は書きません。コンパスが混みます。
- 循環、未知のID、重複は export で失敗します。

## レシピ C — 道筋を作る・直す

`data/seeds/learning_paths.json` にステップを並べます。

- ステップの `question_ja` は、そのページを読むと答えられる問いを1文で書きます。見出しの言い換えではなく、読者が抱く疑問の形にします（「〜はなぜ〜か。」）。
- 記事の `prerequisites` が道筋の後ろにあると失敗します。前提を先に置くか、記事の前提を見直します。
- 骨格しかない型もステップにできます。その型が backlog の上位に上がります。
- 1本の道筋は7〜12ステップを目安にし、終えたときにできることを `goal_ja` に書きます。初めての読者の入口になる道筋（例: `what-is-optimization`）は、一度で歩き切れるよう4〜5ステップに絞ってかまいません。
- ステップには、任意で `stumbles` を付けられます。読者がそのステップでつまずいたときの戻り先です。
  - 各項目には `trouble_ja`（つまずきを読者の言葉で書いた1文。「〜が分からない。」の形）と、戻り先の `target_type`・`target_id` を書きます。
  - 戻り先は、公開済みの記事か定式化だけです。そのステップ自身は指せません。
  - 画面では、ステップのページの下に「つまずいたら戻る」として出ます。戻った先のページには、元のステップへ帰るリンクが出ます。
  - 用語や前提の記事へ戻すことを優先し、「次を読めば分かる」ような先送りの戻り先にはしません。
- 道筋のページには、最初の定式化のステップへの近道（「順を飛ばして式から読む」）が自動で出ます。式を先に見たい読者のためです。最初のステップがその定式化そのものなら、代わりに定式化の辞書へのリンクが出ます。

## 検証

書いている途中は、生成物を作り直さずに記事ファイルだけを検査できます（複数人が並行して書いても衝突しません）。

```bash
uv run python scripts/check_article.py content/concepts/<file>.md
```

仕上げに全体を検証します。

```bash
uv run optimization-compass export-site-data --output site/public/data
uv run optimization-compass validate content
uv run python -m pytest tests/test_formulation_atlas.py
npm --prefix site test -- --run src/contracts/formulation-atlas.test.ts
```
