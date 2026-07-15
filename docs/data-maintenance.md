# Data Maintenance

## Release gate

- `uv run python scripts/rebuild_dataset.py --stage` が2回の同一tree hashで完了する
- SQLite DDLを作成できる
- 全行を投入できる
- `PRAGMA foreign_key_check` が0件
- 主キー重複が0件
- evidence targetが解決できる
- stored statusを信用せずliveに再計算した `CHK001`–`CHK019`、coverage closureの
  `CHK021`、claim/context closureの `CHK022`–`CHK023`、failure relation closureの
  `CHK024`、terminology alias closureの`CHK025`にfailがない

Atomic predicateを変更するときは、`005_atomic_predicates.sql` と
`data/seeds/atomic_predicates.json` を同じ変更で更新します。`complete` coverageと
rule-target retirementは、legacy rule条件からpolicy exclusionを再現できる場合だけ許可されます。
- database-only検証では `CHK020=not_run` とし、全distribution/manifest/version/hashを実際に
  読み戻した `verify_release_tree` だけがartifact consistencyを成立させる
- JSON / JSONL / CSV directory / deterministic ZIP / XLSX / SQLiteが列・主キー・行・NULL・値まで一致する
- manifest schema/version/release dateをpath解決前に検証し、JSON/JSONL header、SQLite
  version history、report、versioned filename、hash、runtime copy、`DATASET_VERSION`が一致する
- manifestのcode/data/content license宣言と同梱noticeが一致し、CSV ZIP内の
  `LICENSES/` entryを読み戻せる

## Staged rebuild

```bash
uv run python scripts/rebuild_dataset.py --stage
```

target versionとrelease dateは `src/optimization_compass/resources/release-authority.json` だけで変更します。CLI引数、UI、
validatorへversionを重複記載しません。次で2回検証済みtreeを保持できます。

```bash
uv run python scripts/rebuild_dataset.py --stage --output .release-stage
```

このコマンドは公開済みv0.2.0のversion/hashを確認してstaging領域だけに構築します。
atlas metadata migration/seedは監査可能な入力ですが、runtime authorityはreleased SQLiteです。
新versionを構築するときは `build_staged_release(..., target_version=..., release_date=...)`
がversion history/model revisionを含む全artifactを同じidentityで生成します。publish gateはdata
directory、runtime DB、`DATASET_VERSION`、site dataを先に全てstage/backupし、途中の置換失敗時は
4対象をまとめて元へ戻します。

```bash
uv run python scripts/rebuild_dataset.py --publish --staged-directory .release-stage
```

publish後はversioned release identityと `site/public/data/release.json` がbyte単位で一致し、
SQLite / JSON / JSONL / CSV / ZIP / XLSX / report / runtime DB / site JSONが同じdataset versionを
持つことを確認します。
通常の公開済みbase検証は `verify_database(..., require_atlas=False)`、staged release gateは
`require_atlas=True` とし、Atlas tableが全て欠落してもbase datasetへ誤判定しません。

authorityの境界と明示状態の意味は [metadata-responsibilities.md](metadata-responsibilities.md)
を参照してください。

## Git tag and GitHub Release

repository内のatomic publishと全検証完了後にのみ `dataset-v<version>` tagをmainの検証済みcommitへ
付けます。GitHub Releaseにはversioned SQLite、JSON、JSONL、CSV ZIP、XLSX、schema、report、
manifest、release identityを添付し、manifestのSHA-256をchecksum authorityとして扱います。

公開前の権利・配布・Pages確認は
[public-release-checklist.md](public-release-checklist.md) を使用してください。

## Volatile fields

次は更新頻度が高いため、リリース前に公式情報を再確認します。

- `implementations.last_release`
- `implementations.maintenance_status`
- `implementations.license`
- 公式ドキュメントURL
- 商用モデル・無料利用条件

## Golden cases

推薦変更は、最低限次の類型でsnapshotを確認します。

- 0-1線形制約
- expensive black-box
- smooth unconstrained continuous
- non-differentiable
- noisy high-dimensional
- least squares
- global certificate required
