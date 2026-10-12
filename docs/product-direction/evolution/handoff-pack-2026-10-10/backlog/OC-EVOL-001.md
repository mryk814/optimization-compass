# OC-EVOL-001: 基準監査と既存作業の照合

状態: 未投稿のIssue下書き / M0 / P0 / 相対規模: small

## 目的

実装先HEAD、未コミット差分、PR297/298、canonical件数とscope候補の照合状態を確定する。

## 成果物

観測と推測を区別したbaseline JSONと、重複作業の統合メモ。

## 接続先

- `AGENTS.md`
- `data/seeds/`
- `src/optimization_compass/resources/`
- `tools/audit_repository.py（本パック内）`

既存作業: PR297, PR298

依存: なし

## 受入条件

- [ ] DB/生成物のhashが監査前後で同じ
- [ ] 一致候補と意味レビュー済みを別状態にする
- [ ] unmatchedを未収録確定にしない
- [ ] コード/公開に変更を行わない

## 検証と権限

既存AGENTS/validation registryへ従い、変更面に合うテストを実行する。台帳/数値の検査と、人の学習評価を別にする。新schema、外部送信、課金、実実験、公開、mergeは別承認。未実行の試験を成功と記載しない。

## 非目標

- 本票だけでmainへ無断mergeしない
- 企画IDをそのままcanonical IDへ挿入しない
- 新しい独立した推薦/品質正本を作らない

## 出典

R08, R14, R06, R07。URL・確認日・限界は `../SOURCES.md`。
