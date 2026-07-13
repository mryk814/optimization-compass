# Data Maintenance

## Release gate

- SQLite DDLを作成できる
- 全行を投入できる
- `PRAGMA foreign_key_check` が0件
- 主キー重複が0件
- evidence targetが解決できる
- `release_checks.status = fail` が0件

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
