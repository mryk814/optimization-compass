# Optimization Compass

最適化の定式化・手法・実装・根拠をつなぐ、版つきのデータ駆動 Optimization Atlas。

人が使う情報（起動、検証）は [`README.md`](README.md)、変更の種類ごとの手順は [`docs/adding-knowledge.md`](docs/adding-knowledge.md) にある。記事を書くときは [`docs/teaching-article-playbook.md`](docs/teaching-article-playbook.md)（リポジトリを読めない AI には [`docs/prompts/teaching-article.md`](docs/prompts/teaching-article.md)）と [`docs/article-style.md`](docs/article-style.md) に従う。

## 読者に届けるもの

どの変更も、次の3つのどれかを読者にとって良くするためにする。ページ・行・文字を増やしただけで、どれも良くならない変更は前進ではない。

1. **引ける** — 定式化ごとの `/formulations/<PROBLEM_ID>` に、標準形、読み下し、見分ける手がかり、定式化どうしの位置（より一般・より特殊・緩和や書き換え・似ているだけ）、候補の手法がある。
2. **進める** — `/paths/<path_id>` が定式化と記事を問いの順に並べる。各ステップの上に「この項の問い」、下に「次の問い」を出す。
3. **当てはめる** — Diagnose と Gallery が、同じ知識を読者自身の問題に当てる。

構造は「骨格 → 記事 → 投影」。骨格（リリースした DB と `data/seeds/formulation_atlas.json`）が最初からすべての entity を見せ、記事（`content/**/*.md`）を1本ずつ足し、画面は両方から生成する。方針は [`docs/product-direction/learning-atlas.md`](docs/product-direction/learning-atlas.md) と [ADR 0017](docs/adr/0017-formulation-atlas-and-learning-paths.md)。

- 次に書く記事は勘で選ばず、`uv run python scripts/formulation_backlog.py` で選ぶ。
- 記事を変える前後に `uv run python scripts/article_quality.py show <article>` で基準の満たし方を見て、レビューしたら `record` で台帳に残す（[`docs/article-quality.md`](docs/article-quality.md)）。台帳は、記事の編集や基準の追加で古くなったレビューを見つけるためにある。

## どこを直すか

| 変えたいもの | 正本 |
|---|---|
| stable ID、構造化した関係、対応範囲、根拠、正典の知識 | SQL migration と検証済みの seed・catalog（ここからリリース用の SQLite を作る） |
| 手法・概念の解説文 | `content/**/*.md` の frontmatter と本文 |
| 定式化の記事 | `content/concepts/*.md`（`canonical_entity_type: problem`）。[`docs/formulation-atlas.md`](docs/formulation-atlas.md) のレシピ A |
| 定式化の族、標準形、読み下し、手がかり、定式化どうしの関係 | `data/seeds/formulation_atlas.json`（同レシピ B） |
| 学習経路 | `data/seeds/learning_paths.json`（同レシピ C） |
| 編集範囲（Coverage の分母） | `data/seeds/editorial_scope.json`（[`docs/editorial-scope.md`](docs/editorial-scope.md)） |
| Gallery の事例 | `data/seeds/site_gallery.json` |
| 比較の定義 | `data/seeds/site_comparisons.json` |
| 問題の定義とインスタンス | `src/optimization_compass/resources/problem-suite.json`（変えるとリリースが要る。下の「リリース」） |
| 問題の実行時の振る舞い | `src/optimization_compass/problem_registry.py` |
| 動く図（explorable） | `src/optimization_compass/resources/explorables.json` と `site/src/features/explorable/`（[`docs/explorables.md`](docs/explorables.md)） |
| 問題・手法・判断・探索の図 | `site/src/visual-system/` の部品を使う（[`docs/visual-system.md`](docs/visual-system.md)） |
| 表示・可視化のメタデータ | `data/seeds/` の seed と `src/optimization_compass/` の Python の契約 |

## 生成物を直接編集しない

リリースした SQLite が実行時の正本だが、直接は編集しない。見た目の結果を直すために次を手で書き換えず、正本を直して再生成する。

| 生成物 | 再生成 |
|---|---|
| `src/optimization_compass/resources/knowledge.sqlite`、`src/optimization_compass/resources/DATASET_VERSION`、`data/optimization_method_selection_database_v*` | `uv run python scripts/rebuild_dataset.py --stage`（公開済みの成果物は変えない）。置き換えるのはリリースの publish だけ |
| `site/public/data/**` | 既存 entity の記事を公開するなら `uv run optimization-compass ready content <content-id>`、それ以外は `uv run optimization-compass export-site-data --output site/public/data` |
| `docs/content-quality-report.md`、`docs/method-content-density-report.md` | `uv run python scripts/content_quality_report.py`、`uv run python scripts/method_content_density_report.py` |
| README の「現在のデータセット」 | `uv run python scripts/sync_readme_facts.py` |
| Trace、media、検索・retrieval、Coverage、manifest、release の生成物 | それぞれの生成手順（[`docs/adding-knowledge.md`](docs/adding-knowledge.md)） |

- 生成した JSON は手でマージしない。他の PR と衝突したら、main を取り込んでブランチの最新の状態から作り直す。
- 再生成で、変更と関係のない生成物の差分が大量に出たら、コミットせずに原因を調べる。ビルドは決定的なので、それ自体が異常のしるし。
- リリース用の生成物がコミットに入るのは、生成手順が作ったリリースのコミットだけ。

## 不変条件（Core invariants）

- stable ID を黙って別の意味に使い回さない。
- `method`（理論上の手法）と `implementation`（ライブラリ・API）を分ける。
- `unknown`、`not_applicable`、`unsupported` は、別々の明示的な状態として保つ。
- 事実として足す知識は、出典・根拠までたどれるようにする。出典は公式ドキュメント、公式リポジトリ、原論文、標準・仕様を優先する。Qiita と Zenn は出典にしない。
- ライブラリの既定値を、どこでも通じる推奨や順位として示さない。
- 比較では、固定した要因、変えた要因、予算、同期、指標、公平性、注意点、順位づけしてよいかを書く。
- 離散化して解いた結果から、連続モデルでの保証を条件なしに導かない。
- PDE 制約のデータでは、決定変数、導かれる状態、残差制約、評価の失敗、ソルバーのコストを区別できるように保つ。
- 公開する解説文は日本語で書く。英語は、正式な用語、固有名、API、出典の題名、コード、式、識別子に残す。
- 正典の関係からルートを生成できるときは、UI のコードに entity ごとの対応表を足さない。
- すべての問題型（problem archetype）は formulation atlas にちょうど1回ずつ現れる。`special_case_of` と `relaxes_to` は循環を作らない。どの関係も、成り立つ条件を `note_ja` に書く。
- 定式化・手法・族の記事は、決まった節の骨組み（`src/optimization_compass/content_skeletons.py`）に従う。例の数値は見積もらず計算する。骨組みより前に書いた記事は `data/seeds/content_skeleton_pending.json` にあり、この一覧は減る一方にする。
- 学習経路のステップは、それぞれ答える問いを持ち、自分の前提より前に来ない。
- 推薦の出力を変えるときは、その変化を示す回帰ケースを足す。

## 先にメンテナーに相談すること

次は公開済みデータセットの版・引用・互換性に関わり、あとから戻しにくい。決める前に相談する。

- 新しい stable ID の名前空間や、スキーマの欄が要りそうなとき。
- release の版上げや migration の順序。
- 新しい renderer や artifact contract の版。

## リリース

- 公開（GitHub Pages への deploy、dataset の publish、release catalog の更新）は、普段の記事や seed の編集に混ぜない。Pages に deploy するのは手動の `.github/workflows/pages-deploy.yml`（workflow_dispatch）だけ。
- `src/optimization_compass/resources/problem-suite.json` の変更はリリースの境界を越える。release authority を更新し、staged の SQLite とサイトを作って publish し、`CITATION.cff` と dataset card を作り直す。普段の site export は、seed と runtime の SQLite の食い違いをわざと拒む。
- release catalog に過去の版が入っているので、staging のテストには未公開の版を使う。公開済みの版を使うと、identity の検証で（正しく）落ちる。
- まだ公開していない staged release のサイト出力には、前の版までの catalog が入る。新しい版が current として載るのは、外部の bundle と catalog を更新した後。

## その他

- コミットには DCO の sign-off（`git commit -s`）を付ける（[`CONTRIBUTING.md`](CONTRIBUTING.md)）。
- ブラウザーのテストで原因を調べるときは、`CI=1` と他と重ならない `PLAYWRIGHT_PORT` を付けて1 worker で動かす。多 worker では、ルートの失敗が資源不足やタイムアウトに埋もれる。
