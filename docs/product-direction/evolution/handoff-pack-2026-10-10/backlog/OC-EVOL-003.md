# OC-EVOL-003: Coverageへ分母と品質軸を統合

状態: 未投稿のIssue下書き / M1 / P0 / 相対規模: medium

## 目的

存在、レビュー、教材、体験、転移を別の集合として集計する。

## 成果物

生成されるcoverage snapshotと種類別の分子/分母、未照合、stale、対象外。

## 接続先

- `src/optimization_compass/coverage.py`
- `site/src/features/coverage/`
- `data/seeds/article_quality_ledger.json（PR297再確認）`

既存作業: PR297, PR298

依存: OC-EVOL-002

## 受入条件

- [ ] 分母追加と完成追加を別表示
- [ ] 別名を二重計上しない
- [ ] PR297のレビュー状態を再利用
- [ ] 集計値を手編集できない

## 検証と権限

既存AGENTS/validation registryへ従い、変更面に合うテストを実行する。台帳/数値の検査と、人の学習評価を別にする。新schema、外部送信、課金、実実験、公開、mergeは別承認。未実行の試験を成功と記載しない。

## 非目標

- 本票だけでmainへ無断mergeしない
- 企画IDをそのままcanonical IDへ挿入しない
- 新しい独立した推薦/品質正本を作らない

## 出典

R03, R06。URL・確認日・限界は `../SOURCES.md`。
