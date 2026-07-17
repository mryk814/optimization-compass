---
name: add-gallery-case
description: Add a Gallery case (Galleryケース・実例・事例の追加) to data/seeds/site_gallery.json using only existing canonical IDs, then validate with tier B. The recommended first structured-data contribution.
---

# Gallery caseを追加する

実問題の事例を `data/seeds/site_gallery.json` へ追加する導線です。
**既存のcanonical IDだけを使います**。新しいmethod/problem/source IDが必要になったら、
それはこの導線ではなくcanonical data作業（`docs/adding-knowledge.md` §11）です。

## Step 1 — 使うIDを先に全部解決する

追加前に、以下がすべて既存であることを確認します（`site/public/data/*.json` を読むのが早い）:

- `problem_archetype_id`（`problems.json`）
- すべての `feature_id` とその値、Diagnose `question_id` と回答（`recommendation/`配下）
- candidate / conditional / excluded の各method ID
- `implementation_ids`、`source_ids`
- 使うなら `visualization_ids`、`comparison_ids`

```bash
python3 -c "
import json
g = json.load(open('data/seeds/site_gallery.json'))
print('existing case_ids:', [c['case_id'] for c in g['cases']])
"
```

## Step 2 — 最も近い既存caseをコピーして書き換える

`data/seeds/site_gallery.json` 内で問題構造が最も近いcaseをコピーし、
**コピーした全IDを1つずつ再評価して置き換えます**（プロースだけ変えてIDを流用しない）。

主要フィールド: `case_id`, `title_ja/en`, `domain`, `problem_archetype_id`,
`feature_values`, `question_answers`, `candidate/conditional/excluded_methods`,
`implementation_ids`, `visualization_ids`, `comparison_ids`, `source_ids`,
`difficulty`, `status`, `last_reviewed`, `question`, `decision_variables`,
`objective`, `constraints`, `map_node_id`, `python_example`,
`practical_notes`, `limitations`。

### 意味的な必須要件

- candidate / conditional / excluded のmethod集合は**重複禁止**。
- conditional・excludedには**具体的な理由**を必ず書く（「合わない」だけは不可）。
- `map_node_id` はcaseの `question_answers` から導出可能であること
  （例: `answer:Q01:binary`）。
- `python_example` は非空で `compile()` が通る最小例。
- `limitations` で「この固定教材caseが保証しないこと」を明示する。
  `practical_notes`（実務適用時の確認事項）はlimitationsの代替にならない。
- 固定した教材runの結果が実問題の性能を保証すると示唆しない。
- canonical `EC...` caseを昇格する場合はDBのexample-case関係と一致させ、
  Diagnose回答を完備する。

## Step 3 — 検証する

```bash
make tier-b
```

反復中は焦点を絞った先行チェックが速い:

```bash
uv run python scripts/verify_content.py
uv run optimization-compass verify-data
uv run pytest tests/test_site_export.py
```

GalleryのUIはデータから生成されます。**site側コードは触りません**。

## Stop条件

- 必要なmethod/implementation/source IDが存在しない。
- 問題構造に合うproblem archetypeが無い。
- `map_node_id` に対応するDiagnose質問・回答が無い。

いずれも「不足しているcanonical entityは何か」を報告して止まる（勝手にIDを作らない）。

## PRに書くこと

追加した `case_id`、参照した全canonical ID、根拠source、
journey/Coverage/routeへの影響、検証コマンドと結果。DCO sign-off必須。
