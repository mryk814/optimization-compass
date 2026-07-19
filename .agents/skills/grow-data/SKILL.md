---
name: grow-data
description: Decide what Optimization Compass knowledge to grow next (データを育てる・次に何を追加するか). Observes coverage / content-density / seed gaps, then routes to the matching authoring skill and validate task.
---

# データ育成のtriage（何を、どの導線で育てるか）

「次に何を育てるか」を観測してから、変更種類ごとの導線へルーティングする薄いスキルです。
規則の本体はこのスキルには置きません。必ず先に読むこと:

1. `/AGENTS.md`
2. `.agents/skills/optimization-compass-maintenance/SKILL.md`（作業手順・不変条件の正）

## Step 1 — ギャップを観測する（生成物は読むだけ）

ファイルはReadツールで読みます（プラットフォーム依存のシェル加工をしない）:

- `site/public/data/coverage.md` の「Priority slices」節 — rank順の「次にやるべき領域」
- method記事の密度floor: `uv run python scripts/method_content_density_report.py --output <一時ファイルパス>`
  を実行し、出力レポートを読む（デフォルト出力先はリポジトリ内なので必ず`--output`で退避する）
- `content/methods/` と `content/concepts/` のファイル数と `status: draft` の記事
- `data/seeds/site_gallery.json` の `cases` 配列、`data/seeds/site_comparisons.json` の
  `comparisons` 配列（件数と、`comparison_ids: []` / `visualization_ids: []` の未接続case）
- `docs/product-direction/` と Issues #122 / #123（journey completenessが現在の優先方針）

## Step 2 — 育成対象を1つに絞る

Roadmapの方針は「新しい基盤の数より、完全に辿れるProblem journeyを増やす」。迷ったら:

1. coverage priority slice上位に紐づく既存entityの未接続リンク
2. 密度floor未達・`draft` 記事の充実
3. 既存entityだけで書けるGallery case
4. 既存trace/rendererを再利用するcomparison
5. 新しいproblem instance
6. 新しいmethod/implementation/source（migration必須の高リスク。安易に踏み込まない）

## Step 3 — 導線へルーティングする

| 育てたいもの | skill | 反復チェック | PRゲート |
|---|---|---|---|
| method/concept記事 | `add-content-article` | `uv run optimization-compass validate content` | `validate tier-a` |
| Gallery case | `add-gallery-case` | `validate gallery` | `validate tier-b` |
| comparison | `add-comparison` | `validate comparison` | `validate tier-b` |
| problem instance | `add-problem-instance` | `validate problem` | `validate tier-c` |
| method/implementation/source追加 | skillなし — maintenance skill Recipe F + `docs/adding-knowledge.md` §11 | — | `validate tier-b`〜`tier-c` |

`uv run optimization-compass validate <task> --list` で各タスクの実行内容を確認できます。
タスク構成の正は `src/optimization_compass/validation_tasks.py` です。
