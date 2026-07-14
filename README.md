# 最適化コンパス / Optimization Compass

> 最適化を「選ぶ・理解する・使う」ための、データ駆動のOptimization Atlas。

Optimization Compassは、「最適化したい。でも、何をどう解けばいい？」という問いを、構造化された問題・手法・実装・根拠データから整理するオープンソースプロジェクトです。

単一のアルゴリズムランキングを返すのではなく、次を同じknowledge baseから提供します。

- 問題条件を整理する診断
- 最適化全体を俯瞰する複数のMap
- 手法・概念・実装を学ぶ教材
- アルゴリズムの動きを理解する可視化
- 実問題から逆引きするProblem Gallery
- 推薦理由と情報源を辿るevidence trail
- データの不足と偏りを確認するCoverage audit

**公開Atlas:** https://mryk814.github.io/optimization-compass/

## 3つの入口

Optimization Compassは、異なる目的を一つの画面へ混ぜず、3つの体験として整理します。

| やりたいこと | 入口 | 主な流れ |
|---|---|---|
| 問題を解きたい | Diagnose | 条件整理 → 代替解法 → 候補手法 → 実装 → 注意事項 |
| 最適化を理解したい | Map / Learn / Theater | 全体像 → 概念 → 手法 → 比較・可視化 |
| データを使いたい | Sources / Coverage / Data | 構造化データ → 根拠 → 欠落 → Download / API |

体験は分かれていますが、表示内容のauthorityは同じcanonical databaseです。

## 現在のデータセット

現在の公開データセットは **v0.3.1** です。

| 項目 | 件数 |
|---|---:|
| Tables | 42 |
| Rows | 8,144 |
| Methods | 98 |
| Problem archetypes | 56 |
| Implementations | 64 |
| Sources | 95 |
| Example cases | 28 |
| Decision rules | 78 |
| Evidence links | 4,193 |
| Canonical visualization scenarios | 16 |

配布形式:

- SQLite
- JSON / JSONL
- CSV ZIP
- Excel
- SQL schema
- release manifest / report
- GitHub Pages向けversioned site data

データは [`data/`](data/) から取得できます。

## いま利用できる機能

### Diagnose — 問題条件から候補を探す

質問に答えると、次の順で結果を返します。

1. 汎用最適化より先に確認すべき代替解法
2. 問題に適合する手法候補
3. 条件付き候補
4. 前提と衝突する手法
5. 代表的な実装・ソルバー
6. 発火した決定ルールとsource ID

推薦本体はLLMではなく、SQLiteの質問・決定規則・適合関係を使う決定的なrule engineです。

### Map — 最適化の全体像と現在地を見る

問題の変数、目的関数、制約、利用可能な情報などを、スタート地点から段階的に展開します。

Mapは「唯一の正しい巨大分類図」ではありません。目的別のViewをcanonical dataから生成する方針です。現在はProblem Structure Viewを公開しており、oracle・保証・mechanism・implementationなどの追加Viewを[ロードマップ](#roadmap)で進めます。

### Learn / Method pages — 手法と概念を学ぶ

教材はMarkdownからbuild-timeに安全なHTMLへ変換されます。

対応内容:

- 数式
- Python code
- 表・リスト・callout
- 目次
- 関連手法・可視化・比較
- sourceとlast reviewed

Method pageは、説明・実装・Trace・比較・ケース・根拠をまとめたcanonical hubです。

### Method Theater / Compare Lab — 動きと違いを理解する

現在の代表的な可視化:

- **Nelder–Mead** — simplexの反射・膨張・収縮・縮小
- **Gradient Descent / Momentum / Adam** — 同一条件の軌跡と目的値比較
- **Branch-and-Bound** — 探索木、incumbent、bound、gap、枝刈り
- **Bayesian Optimization** — 観測、surrogate、uncertainty、acquisition、次の評価点

可視化は手法ごとの動画を手作りするのではなく、次をversioned dataとして管理します。

```text
Problem definition
  └─ Problem instance
       └─ Visualization scenario
            ├─ Method run(s)
            ├─ Initial condition / parameters / seed
            ├─ Budget / stopping condition
            ├─ Educational purpose / limitations
            └─ Renderable artifact
```

実行可能な例はPython generatorからTraceを生成します。GIF、動画、PNGはTraceやscenarioから作る派生成果物であり、source of truthではありません。

### Problem Gallery — 実問題から逆引きする

現実の問いを、次の形へ分解して表示します。

- decision variables
- objective
- constraints
- problem features
- candidate / excluded methods
- representative implementation
- minimal Python example
- practical cautions
- Map / Diagnose / Visualizationへの導線

### Sources — 根拠を確認する

推薦、教材、可視化、ケースからsource pageへ辿れます。

Source pageでは、公式URL、publisher、source type、last verified、関連entityを確認できます。定期source-health workflowは、リンク切れとstale metadata候補を報告します。

### Coverage — 何が学べて、何が不足しているかを見る

Coverageはページ数のランキングではありません。

次の2層を監査します。

1. method / problem / feature familyがMap、推薦、教材、可視化、比較、Gallery、実装、sourceへ接続されているか
2. 明示された学習目的に対し、必要なscenario・artifact・renderer・routeが存在するか

Coverage status:

- `available`
- `partial`
- `missing`
- `not_applicable`

現在のCoverageには、canonical scenario / comparisonと生成artifact間の既知の参照ズレも表示されています。解消作業は [#44](https://github.com/mryk814/optimization-compass/issues/44) で追跡します。

## 設計原則

- **alternative-first** — 求根、最小二乗、線形方程式、グラフ法、DPなどを先に検討する
- **exclusion wins** — 前提違反があれば、他の支持より除外を優先する
- **unknown is data** — 不明を勝手にyes/noへ補完しない
- **method != implementation** — 理論手法とライブラリ/APIを分離する
- **traceable** — 推薦理由をruleとsourceまで追跡可能にする
- **deterministic** — 同じ入力・同じデータ版から同じ結果を生成する
- **data-first views** — View固有の知識をUIへハードコードしない
- **comparison needs context** — 初期値、budget、停止条件、oracle、parameter policyを明示する
- **no universal ranking** — 文脈のない総合スコアを手法選択の根拠にしない

## Architecture

```text
Canonical SQLite knowledge base
  ├─ methods / problem archetypes / features
  ├─ implementations / sources / evidence
  ├─ decision questions / rules
  ├─ view presets / visualization metadata
  └─ coverage expectations
          │
          ├─ Python deterministic recommendation engine
          ├─ ViewSpec / entity links / static site export
          ├─ executable objective & algorithm registry
          └─ release / validation pipeline

Markdown content ───────────────┐
Python-generated Trace JSON ────┼─> Optimization Atlas (React / GitHub Pages)
Versioned renderer payloads ────┘
```

Authorityの境界:

| Authority | Owns |
|---|---|
| Canonical SQLite | stable IDs、分類、関係、support scope、source relation |
| Markdown | 人間向け説明、数式、code、教材構成 |
| Python registry | 実行可能なobjective、algorithm、deterministic Trace生成 |
| Generated site data | ViewSpec、entity links、indexes、resolved scenario envelopes |
| Trace / renderer payload | 実行snapshotと可視化固有の観測値 |
| TypeScript renderer registry | renderer familyとUI componentの対応 |

詳細は [`docs/metadata-responsibilities.md`](docs/metadata-responsibilities.md) と [`docs/adr/`](docs/adr/) を参照してください。

## Quick start

### Optimization Atlas

Node.js 24を使用します。

```bash
cd site
npm ci
npm run dev
```

ローカルURL:

```text
http://127.0.0.1:5173/optimization-compass/
```

Production build:

```bash
cd site
npm run typecheck
npm test -- --run
npm run build
npm run test:e2e
```

### REST API / CLI

Python 3.12以上を使用します。

```bash
uv sync --all-extras
uv run optimization-compass serve
```

- API landing: `http://127.0.0.1:8000/`
- OpenAPI: `http://127.0.0.1:8000/docs`

CLI examples:

```bash
uv run optimization-compass questions
uv run optimization-compass recommend examples/binary_linear.json
uv run optimization-compass recommend examples/expensive_blackbox.json
uv run optimization-compass verify-data
```

API example:

```bash
curl -X POST http://127.0.0.1:8000/v1/recommendations \
  -H 'content-type: application/json' \
  -d @examples/binary_linear.json
```

## Repository structure

```text
content/                         # method / concept educational Markdown
data/                            # versioned dataset distributions and migrations
site/                            # React / TypeScript Optimization Atlas
src/optimization_compass/
  api.py                         # FastAPI
  cli.py                         # Typer CLI
  db.py                          # SQLite read-only repository
  engine.py                      # deterministic recommendation engine
  site_export.py                 # versioned static data export
  traces/                        # Trace contracts and generators
  resources/
    knowledge.sqlite             # runtime canonical database
docs/                            # ADRs, contracts, maintenance and release docs
scripts/                         # validation, export and release tooling
tests/                           # Python tests and fixtures
```

## Validation and release discipline

Python:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest --cov=optimization_compass --cov-report=term-missing
uv run optimization-compass verify-data
uv run python scripts/verify_content.py
uv run python scripts/verify_licensing.py
uv run python scripts/rebuild_dataset.py --stage
```

Site:

```bash
cd site
npm ci
npm run typecheck
npm test -- --run
npm run parity
npm run build
npm run test:e2e
```

GitHub Pagesは、Python、data、content、licensing、parity、site tests、browser E2Eを同一commitで通過した単一artifactだけをdeployします。

公開データはimmutable releaseとして扱います。新しいreleaseは、SQLite、JSON、JSONL、CSV、Excel、manifest、runtime DB、site dataを同一identityでatomicに生成します。

## Roadmap

次のフェーズは、新しい基盤を増やすことより、**DBにある知識をより多く、読みやすく、複数のViewへ公開すること**を重視します。

全体Epic: [#43 Deepen the Atlas](https://github.com/mryk814/optimization-compass/issues/43)

| Priority | Issue | Goal |
|---|---|---|
| P0 | [#44](https://github.com/mryk814/optimization-compass/issues/44) | scenario / comparison / Coverageのcanonical参照を統一する |
| P0 | [#45](https://github.com/mryk814/optimization-compass/issues/45) | Map・教材・可視化の文字、説明、目的地表示を改善する |
| P1 | [#46](https://github.com/mryk814/optimization-compass/issues/46) | oracle・保証・mechanism・implementationなど複数Viewを生成する |
| P1 | [#47](https://github.com/mryk814/optimization-compass/issues/47) | 教材を12件以上、Galleryを10件以上へ拡張する |
| P2 | [#48](https://github.com/mryk814/optimization-compass/issues/48) | method assumptionsをmachine-evaluable predicatesへ正規化する |
| P2 | [#49](https://github.com/mryk814/optimization-compass/issues/49) | versioned implementation claimsとbenchmark contextを追加する |
| P2 | [#50](https://github.com/mryk814/optimization-compass/issues/50) | constrained / multi-objective可視化を追加する |

### Current data priorities

- Coverage integrity errorを0件にする
- DBにある28 casesをGalleryへ段階的に昇格する
- 98 methodsから代表教材を選び、説明・実装・sourceを接続する
- implementation release metadataのunknownを一次情報で減らす
- method assumptionsを複数Viewと推薦で再利用できる形へ正規化する
- benchmarkや比較にはcontextを必須化する

## Contributing

変更は、推薦ロジック、canonical data、教材、可視化、UIを可能な範囲で分けてレビューしてください。

Data PRには最低限、次が必要です。

1. 変更対象ID
2. 変更前と変更後
3. 公式ドキュメント、公式repository、原論文などの一次情報
4. 推薦・View・教材への影響
5. validation結果

Qiita / Zennは根拠として使用しません。

詳細は [`CONTRIBUTING.md`](CONTRIBUTING.md) を参照してください。

## License

権利範囲を分けて公開しています。

- Python / TypeScript / CSS / HTML / build code: [MIT](LICENSE)
- canonical database and structured distributions: [CC BY 4.0](DATA_LICENSE)
- educational content, generated diagrams, Trace JSON and screenshots: [CC BY 4.0](CONTENT_LICENSE)

第三者の論文、ドキュメント、商標、引用、リンク先コンテンツは元の権利条件に従い、本repositoryのライセンスでは再許諾されません。詳細は [`NOTICE`](NOTICE) と [`docs/licensing.md`](docs/licensing.md) を参照してください。

## Disclaimer

Optimization Compassは、候補選定、学習、前提整理を支援するものです。最適性、安全性、法令適合、商用ライセンス、数値安定性を保証しません。重要な意思決定では、実問題での検証と専門家レビューを行ってください。
