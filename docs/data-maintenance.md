# Data Maintenance

## Release gate

- `uv run python scripts/rebuild_dataset.py --stage` が2回の同一tree hashで完了する
- SQLite DDLを作成できる
- 全行を投入できる
- `PRAGMA foreign_key_check` が0件
- 主キー重複が0件
- evidence targetが解決できる
- stored statusを信用せずliveに再計算した `CHK001`–`CHK020` にfailがない
- JSON / JSONL / CSV directory / deterministic ZIP / XLSX / SQLiteが列・主キー・行・NULL・値まで一致する
- manifestのversion、versioned filename、hash、runtime copy、`DATASET_VERSION`が一致する

## Staged rebuild

```bash
uv run python scripts/rebuild_dataset.py --stage
```

このコマンドは公開済みv0.2.0のversion/hashを確認して一時ディレクトリだけに構築します。
atlas metadata migration/seedは監査可能な入力ですが、runtime authorityはreleased SQLiteです。
Task 11Aではpublish modeを呼び出さず、公開distributionとruntime copyを変更しません。

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
