---
name: add-content-article
description: Add or improve a method/concept article (method記事・concept記事の追加・修正・充実) in content/**/*.md for an existing canonical entity, meeting the density floor, then validate with tier A.
---

# method / concept 記事を追加・充実させる

既存のcanonical entity（`M_*` method、concept）に対して `content/**/*.md` を追加・改善する導線です。
**新しいmethod IDやsource IDを作る作業ではありません**（それはmigrationが必要な高リスク作業。
`docs/adding-knowledge.md` §11 へ）。

## Step 1 — 前提を確認する

```bash
# 対象entityがcanonicalに存在するか（記事が無い ≠ entityが無い）
python3 - <<'EOF'
import sqlite3
db = sqlite3.connect("src/optimization_compass/resources/knowledge.sqlite")  # 読み取りのみ
for row in db.execute("SELECT method_id, name_ja FROM methods WHERE method_id LIKE ? OR name_ja LIKE ?",
                      ("%KEYWORD%", "%キーワード%")):
    print(row)
EOF

# 既存記事・aliasの重複確認
grep -rn "method_id: M_XXX" content/
```

引用するsource IDが `site/public/data/sources.json` に存在することも確認します。
使いたいsourceが無い場合は**stop**（source追加はcanonical data作業）。

## Step 2 — 最も近い既存記事をコピーして書く

新規ファイルは `content/methods/<content-id>.md` または `content/concepts/<content-id>.md`。
frontmatterの形は最も近い既存記事に合わせます。代表形:

```yaml
---
content_id: example-method
kind: method            # または concept
method_id: M_EXAMPLE    # conceptの場合は不要なことがある。近い既存例に従う
title_ja: 例示手法
title_en: Example Method
summary: 最初の本文段落と完全に一致する短い説明です。
source_ids: [S001]
prerequisites: []
related_ids: []
status: draft           # 関係・sourceが不完全なうちはdraft
last_reviewed: 2026-07-17
---
```

### 本文の要件

- 直感 → 仕組み → 前提・保証の範囲 → 診断・switch signal → 限界、の順で説明する。
- 変数型・利用可能な情報（勾配など）・制約・評価コストを明示する。
- method理論とimplementation固有の挙動を分離する。library defaultを一般推奨にしない。
- 既存のcase / visualization / comparison / family guidanceへ`related_ids`等でリンクする。

### 密度floor（published methodの品質下限）

- summary ≥ 35字
- 本文 ≥ 1,200字
- 見出し（TOC）≥ 4
- 構文的に有効なPythonブロック ≥ 1

```bash
uv run python scripts/method_content_density_report.py --output /tmp/density.md
grep <content-id> /tmp/density.md
```

## Step 3 — 検証する

```bash
make tier-a
```

`related_ids` 追加などで生成index・関係が変わる場合はstaged buildも:

```bash
uv run python scripts/rebuild_dataset.py --stage
npm --prefix site run build
```

## Stop条件

- entityがcanonicalに存在しない → 記事だけ先行させない。canonical追加はRecipe F。
- 適切な一次sourceが見つからない → 推測で書かず、draftのまま欠落を明記するか中止。
- 記事を書く過程でcanonical構造データの誤りを見つけた → 記事修正と分けてescalate。

## PRに書くこと

変更category（content）、対象content_id / method_id、根拠source、
検証コマンドと結果、`status`（draft/published）の判断理由。DCO sign-off必須。
