---
name: add-formulation
description: Grow the formulation dictionary and learning paths (定式化の辞書・学ぶ道筋を育てる) — write a formulation article with the 8-section skeleton, add a formulation relation or standard form, or add/reorder a learning path. Validated via optimization-compass validate content.
---

# 定式化の辞書と学ぶ道筋を育てる（薄いwrapper）

規則の正はこのスキルではなく次の3つです。編集前に必ず読むこと:

1. `docs/formulation-atlas.md` — レシピ A（記事）/ B（関係）/ C（道筋）と検証コマンド
2. `docs/adr/0017-formulation-atlas-and-learning-paths.md` — authority の境界と関係の意味
3. `.agents/skills/article-style/SKILL.md` — 本文の文体

## 手順

1. 何を書くかを決める: `uv run optimization-compass export-site-data --output site/public/data` のあと
   `uv run python scripts/formulation_backlog.py --limit 10` の上位から1つ選ぶ。
2. `site/public/data/formulation-atlas.json` で、その型の標準形・関係・手法の候補・事例を読む。
3. レシピ A の8節で `content/concepts/<name>.md` を書く。数値例とコードは一時環境で実行して確かめる
   （`uv run --no-project --with scipy --with numpy python <file>`）。プロジェクトの依存は増やさない。
4. 記事で気づいた関係の抜け・誤りは `data/seeds/formulation_atlas.json` を直す（レシピ B）。
5. 道筋に入れるべきなら `data/seeds/learning_paths.json` にステップと問いを足す（レシピ C）。
6. 書いている途中は `uv run python scripts/check_article.py content/concepts/<name>.md` で型・リンク・根拠ID・文体を確かめる（生成物を使わないので並行作業でも安全）。
7. 仕上げに export し、`uv run optimization-compass validate content` と
   `uv run python -m pytest tests/test_formulation_atlas.py tests/test_content_quality.py` を通す。
8. 記事を足したら `uv run python scripts/content_quality_report.py` でレポートを再生成する
   （コミット済みレポートとの差分でテストが落ちるため）。

## Stop条件

- 対象の問題型が DB に無い、または既存の型と重複しそう → 新しい型は migration が必要（maintenance skill Recipe F）。
- 標準形や関係の根拠となる source が DB の `sources` に無い → 記事を `draft` にして止まる。
