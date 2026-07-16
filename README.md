# 最適化コンパス / Optimization Compass

> 現実の問いを、定式化・候補・除外理由・可視化・根拠へつなぐOptimization Atlas。

Optimization Compassは、「最適化したい。でも、何をどう解けばいい？」という問いを、
構造化された問題・手法・実装・根拠データから整理するオープンソースプロジェクトです。
単一の万能rankingではなく、**何を試すか、なぜ除外するか、何を確認するか**を示します。

**公開Atlas:** https://mryk814.github.io/optimization-compass/

## まず試す

- **条件がまだ曖昧:** [Diagnose](https://mryk814.github.io/optimization-compass/#/diagnose)
- **実例から考えたい:** [Problem Gallery](https://mryk814.github.io/optimization-compass/#/gallery)

一つのCaseから、次の流れを辿れます。

```text
現実の問い
  → decision variables / objective / constraints
  → 汎用最適化より先に確認する代替解法
  → candidate / conditional / excluded methods
  → representative implementation
  → Theater / Compare
  → failure・limitation・switch signal
  → source / evidence
```

Map、教材、可視化、比較は独立した目的地ではなく、問題を理解して判断するための道具として
同じcanonical knowledge baseから生成します。

## 現在のデータセット

<!-- BEGIN GENERATED DATASET FACTS -->
現在の公開データセットは **0.11.0** （2026-07-16 release）です。

| 項目 | 件数 |
|---|---:|
| Tables | 59 |
| Rows | 8,957 |
| Methods | 99 |
| Problem archetypes | 56 |
| Implementations | 64 |
| Sources | 96 |
| Example cases | 28 |
| Decision rules | 78 |
| Evidence links | 4,193 |

このブロックはrelease authorityと生成reportから生成します。手作業で件数を変更しません。
<!-- END GENERATED DATASET FACTS -->

ここでいうdataset versionは、知識データ配布全体のrelease identityです。site manifestや各JSONの
contract versionはデータ形状を独立に識別するもので、別のアプリreleaseではありません。

配布形式はSQLite、JSON / JSONL、CSV ZIP、Excel、SQL schema、release manifest / reportです。
最新版は [`data/`](data/) にあります。

## 入口

| 目的 | 入口 |
|---|---|
| 問題条件を整理する | [Diagnose](https://mryk814.github.io/optimization-compass/#/diagnose) |
| 実問題から逆引きする | [Gallery](https://mryk814.github.io/optimization-compass/#/gallery) |
| 問題構造を俯瞰する | [Map](https://mryk814.github.io/optimization-compass/#/map) |
| 手法・概念を学ぶ | [Learn](https://mryk814.github.io/optimization-compass/#/learn) |
| アルゴリズムの動きを見る | [Theater](https://mryk814.github.io/optimization-compass/#/theater) |
| 条件を揃えて比較する | [Compare](https://mryk814.github.io/optimization-compass/#/compare) |
| Case・手法・根拠を横断検索する | [Search](https://mryk814.github.io/optimization-compass/#/search) |
| 根拠と欠落を確認する | [Sources](https://mryk814.github.io/optimization-compass/#/sources) / [Coverage](https://mryk814.github.io/optimization-compass/#/coverage) |

## 設計原則

- **problem-first** — 手法名より、解きたい問いと定式化から始める
- **alternative-first** — 求根、最小二乗、線形方程式、グラフ法、DPなどを先に検討する
- **exclusion wins** — 前提違反があれば、他の支持より除外を優先する
- **unknown is data** — 不明を勝手にyes / noへ補完しない
- **method != implementation** — 理論手法とライブラリ/APIを分離する
- **traceable** — 推薦理由をruleとsourceまで追跡可能にする
- **deterministic** — 同じ入力・同じデータ版から同じ結果を生成する
- **comparison needs context** — 初期値、budget、停止条件、oracle、parameter policyを明示する
- **no universal ranking** — 文脈のない総合scoreを手法選択の根拠にしない

## Authority

```text
編集可能な入力
  ├─ SQL migration / validated seed
  ├─ Markdown content
  ├─ Python registry / generator
  └─ TypeScript renderer
           │
           ▼
決定的なstaged build
           │
           ├─ released SQLite
           ├─ distribution files
           ├─ site data / search / Coverage
           └─ Trace / visualization artifacts
```

released SQLiteはruntime authorityですが、直接編集しません。生成物ではなく、監査可能な入力を修正します。
詳細は [`docs/metadata-responsibilities.md`](docs/metadata-responsibilities.md) と
[`AGENTS.md`](AGENTS.md) を参照してください。

## Quick start

### Optimization Atlas

```bash
cd site
npm ci
npm run dev
```

### REST API / CLI

```bash
uv sync --all-extras
uv run optimization-compass serve
uv run optimization-compass questions
uv run optimization-compass recommend examples/binary_linear.json
```

## Validation

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest
uv run optimization-compass verify-data
uv run python scripts/verify_content.py
uv run python scripts/verify_licensing.py
uv run python scripts/rebuild_dataset.py --stage
uv run python scripts/sync_readme_facts.py --check
npm --prefix site run parity
npm --prefix site test -- --run
npm --prefix site run build
```

## Contributing

小さな文章修正や既存entityを使ったCase追加から始められます。

1. [`AGENTS.md`](AGENTS.md) — authority、禁止される直接編集、検証tier
2. [`docs/adding-knowledge.md`](docs/adding-knowledge.md) — 変更種類ごとのrecipe
3. [`CONTRIBUTING.md`](CONTRIBUTING.md) — source、license、DCO sign-off

公式documentation、公式repository、原論文、標準規格を優先します。Qiita / Zennは根拠として使用しません。

## Roadmap

現在は、新しい基盤の数よりも**完全に辿れるProblem journey**を増やすことを優先しています。

- [Problem-first product direction](docs/product-direction/problem-first-atlas.md)
- [代表Case journey](https://github.com/mryk814/optimization-compass/issues/122)
- [journey completeness](https://github.com/mryk814/optimization-compass/issues/123)
- [README release facts](https://github.com/mryk814/optimization-compass/issues/149)
- [Problem-first Home](https://github.com/mryk814/optimization-compass/issues/150)
- [Failure / exclusion discovery](https://github.com/mryk814/optimization-compass/issues/151)

## License

- code・build tooling: [MIT](LICENSE)
- canonical/distributed structured data: [CC BY 4.0](DATA_LICENSE)
- educational content・generated diagrams・Trace・screenshots: [CC BY 4.0](CONTENT_LICENSE)

第三者sourceは元の権利条件に従います。詳細は [`NOTICE`](NOTICE)、
[`docs/licensing.md`](docs/licensing.md)、[`THIRD_PARTY_SOURCE_AUDIT.md`](THIRD_PARTY_SOURCE_AUDIT.md) を参照してください。

Optimization Compassは、候補選定、学習、前提整理を支援します。最適性、安全性、法令適合、
商用license、数値安定性を保証しません。重要な意思決定では実問題での検証と専門家reviewを行ってください。
