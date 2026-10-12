# OC-EVOL-017: 不確実性・多段階の辞書スライス

状態: 未投稿のIssue下書き / M1 / P1 / 相対規模: medium

## 目的

stochastic/robust/chance/DROと多段階の区別を作る。

## 成果物

情報構造付きの在庫/貯水toyとpolicy説明。

## 接続先

- `content/concepts/`
- `data/seeds/formulation_atlas.json`

既存作業: 同種の既存Issue/PRを着手時に検索。

依存: OC-EVOL-004

## 受入条件

- [ ] 未来情報を先行行動へ漏らさない
- [ ] 分布/集合/リスク仮定を別項目
- [ ] SDDP成立条件を原典で確認
- [ ] 一回の最適解とpolicyを区別

## 検証と権限

既存AGENTS/validation registryへ従い、変更面に合うテストを実行する。台帳/数値の検査と、人の学習評価を別にする。新schema、外部送信、課金、実実験、公開、mergeは別承認。未実行の試験を成功と記載しない。

## 非目標

- 本票だけでmainへ無断mergeしない
- 企画IDをそのままcanonical IDへ挿入しない
- 新しい独立した推薦/品質正本を作らない

## 出典

E09, E10。URL・確認日・限界は `../SOURCES.md`。
