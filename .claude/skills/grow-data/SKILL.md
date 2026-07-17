---
name: grow-data
description: Decide what Optimization Compass knowledge to grow next (データを育てる・次に何を追加するか). Finds coverage / content-density / concept / Gallery / comparison gaps from generated reports, then routes to the matching authoring skill.
---

# データ育成のtriage（何を、どの導線で育てるか）

「データを増やしたい・育てたいが、どこから手を付けるか」を決めるためのスキルです。
ギャップを観測してから、変更種類ごとの導線（skill）へルーティングします。

## Step 1 — ギャップを観測する

生成物は読み取り専用ですが、**ギャップの観測には積極的に使います**。

```bash
# 学習coverageの優先slice（rank順の「次にやるべき領域」）
sed -n '/## Priority slices/,/## Integrity issues/p' site/public/data/coverage.md

# method記事の密度floor（summary>=35字 / body>=1200字 / TOC>=4 / Python>=1）
uv run python scripts/method_content_density_report.py --output /tmp/density.md && cat /tmp/density.md

# 量の現状（README生成factsと突き合わせる）
ls content/methods | wc -l   # method記事数
ls content/concepts | wc -l  # concept記事数（歴史的に最も薄い領域）
python3 -c "import json; print(len(json.load(open('data/seeds/site_gallery.json'))['cases']), 'gallery cases')"
python3 -c "import json; print(len(json.load(open('data/seeds/site_comparisons.json'))['comparisons']), 'comparisons')"
```

補助的な観測:

- `content/**/*.md` で `status: draft` のまま止まっている記事（`grep -rl 'status: draft' content/`）
- Gallery caseの `comparison_ids: []` / `visualization_ids: []`（既存artifactへの未接続）
- `docs/product-direction/` と GitHub issues #122/#123（journey completeness が現在の優先方針）

## Step 2 — 育成対象を1つに絞る

Roadmapの方針は「新しい基盤の数より、**完全に辿れるProblem journey**を増やす」です。
迷ったら次の優先順で選びます。

1. coverage priority sliceの上位に紐づく、既存entityの**未接続リンク**（case↔comparison↔visualization↔content）
2. 密度floor未達、または `draft` のmethod/concept記事の充実
3. 既存entityだけで書けるGallery case（構造化データ貢献の推奨入口）
4. 既存trace/rendererを再利用するcomparison
5. 新しいproblem instance（JSON+Pythonのペア作業）
6. 新しいmethod/implementation/source（migrationが必要。安易に踏み込まない）

## Step 3 — 導線へルーティングする

| 育てたいもの | 使うskill | 検証tier |
|---|---|---|
| method/concept記事の追加・充実 | `add-content-article` | A（関係が変わればstage追加） |
| Gallery case | `add-gallery-case` | B |
| 比較（comparison） | `add-comparison` | B |
| 実行可能なproblem instance | `add-problem-instance` | B |
| 新しいmethod/implementation/source | skillなし。`docs/adding-knowledge.md` §11 と `.agents/skills/optimization-compass-maintenance/SKILL.md` Recipe F（高リスク・maintainerフロー） | B〜C |

検証tierは `make tier-a` / `make tier-b` / `make tier-c` で一発実行できます。

## 全導線に共通の不変条件（要約）

- 生成物（`knowledge.sqlite`, `DATASET_VERSION`, `site/public/data/**`, `data/optimization_method_selection_database_v*`）を手で直さない。
- 新しいIDを作る前に、既存entity・alias・近縁重複を必ず検索する。
- 事実の追加には一次sourceを付ける。Qiita / Zennはsource不可。
- `unknown` / `not_applicable` / `unsupported` を混同しない。
- 1 PR = 1つのレビュー関心事。content・canonical data・生成releaseを混ぜない。

完全版は `/AGENTS.md` と `.agents/skills/optimization-compass-maintenance/SKILL.md` を参照。
