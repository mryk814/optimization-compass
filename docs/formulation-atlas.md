# 定式化の辞書と学ぶ道筋を育てる

定式化の辞書（`/formulations`）と学ぶ道筋（`/paths`）は、学習者向けの背骨です。
設計判断は [ADR 0017](adr/0017-formulation-atlas-and-learning-paths.md) にあります。この文書は手順書です。

## 育て方の全体像

```text
骨格（全57型・最初から公開）        肉付け（1本ずつ）              順路（問いでつなぐ）
data/seeds/formulation_atlas.json → content/concepts/<型>.md   → data/seeds/learning_paths.json
  標準形・読み下し・手がかり・関係      8節の型に沿った解説            ステップ＝問い＋ページ
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
   summary: 本文の最初の段落と完全に同じ文。
   prerequisites: [concept.xxx]
   related_ids: [method-content-id]
   source_ids: [S054, S055]
   status: published
   last_reviewed: YYYY-MM-DD
   ---
   ```

3. 本文は次の8節をこの順で書きます。欠けや順序違いは export で失敗します。

   | 節 | 書くこと |
   |---|---|
   | 30秒でつかむ | 身近な場面1つと、決めるもの／良くしたいもの／守ることの3行 |
   | 標準形を読む | 式の前に意味を1文。記号表。solverごとの形の違い |
   | 小さな例 | 手で検算できる数値例。答えの位置や双対値などの「読み取り」 |
   | 見分け方 | この形を疑う言葉と、別の形へ行くべき兆候（リンク付き） |
   | 近い定式化 | seed の関係のうち学習上重要なものを、条件付きで説明 |
   | 解き方の系統 | 方法の系統ごとに進み方と保証。実行して同じ数値が出るコード |
   | つまずきやすい点 | 実際に起きる誤りと、その確かめ方 |
   | 次に読む | 2〜4本。道筋上の次の問いを優先 |

4. 例の数値とコードは、実際に実行して確かめます。プロジェクト本体に数値計算ライブラリを足さず、一時環境で動かします。

   ```bash
   uv run --no-project --with scipy --with numpy python example.py
   ```

5. 動く図が理解の核なら、既存の explorable を再利用するか、[`docs/explorables.md`](explorables.md) の手順で追加します（1記事1つ）。
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
- 1本の道筋は7〜12ステップを目安にし、終えたときにできることを `goal_ja` に書きます。

## 検証

書いている途中は、生成物を作り直さずに記事ファイルだけを検査できます（複数人が並行して書いても衝突しません）。

```bash
uv run python scripts/check_article.py content/concepts/<file>.md
```

仕上げに全体を検証します。

```bash
uv run optimization-compass export-site-data --output site/public/data
uv run optimization-compass validate content
uv run python -m pytest tests/test_formulation_atlas.py tests/test_content_quality.py
npm --prefix site test -- --run src/contracts/formulation-atlas.test.ts
```
