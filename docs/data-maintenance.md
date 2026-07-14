# Data Maintenance

## Release gate

- `uv run python scripts/rebuild_dataset.py --stage` が2回の同一tree hashで完了する
- SQLite DDLを作成できる
- 全行を投入できる
- `PRAGMA foreign_key_check` が0件
- 主キー重複が0件
- evidence targetが解決できる
- stored statusを信用せずliveに再計算した `CHK001`–`CHK019` にfailがない
- database-only検証では `CHK020=not_run` とし、全distribution/manifest/version/hashを実際に
  読み戻した `verify_release_tree` だけがartifact consistencyを成立させる
- JSON / JSONL / CSV directory / deterministic ZIP / XLSX / SQLiteが列・主キー・行・NULL・値まで一致する
- manifest schema/version/release dateをpath解決前に検証し、JSON/JSONL header、SQLite
  version history、report、versioned filename、hash、runtime copy、`DATASET_VERSION`が一致する

## Staged rebuild

```bash
uv run python scripts/rebuild_dataset.py --stage
```

このコマンドは公開済みv0.2.0のversion/hashを確認して一時ディレクトリだけに構築します。
atlas metadata migration/seedは監査可能な入力ですが、runtime authorityはreleased SQLiteです。
Task 11Aではpublish modeを呼び出さず、公開distributionとruntime copyを変更しません。
新versionを構築するときは `build_staged_release(..., target_version=..., release_date=...)`
がversion history/model revisionを含む全artifactを同じidentityで生成します。publish gateはdata
directory、runtime DB、`DATASET_VERSION`を先に全てstage/backupし、途中の置換失敗時は3対象を
まとめて元へ戻します。
通常の公開済みbase検証は `verify_database(..., require_atlas=False)`、staged release gateは
`require_atlas=True` とし、Atlas tableが全て欠落してもbase datasetへ誤判定しません。

authorityの境界と明示状態の意味は [metadata-responsibilities.md](metadata-responsibilities.md)
を参照してください。

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
