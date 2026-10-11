# OC-EVOL-005: 条件付き関係の意味契約

状態: 未投稿のIssue下書き / M1 / P1 / 相対規模: medium

## 目的

包含、等価変形、緩和、共通部品、学習順、応用を区別する。

## 成果物

既存schemaとの差分ADR案と最小関係サンプル。

## 接続先

- `data/seeds/formulation_atlas.json`
- `src/optimization_compass/formulation_atlas.py`
- `src/optimization_compass/entity_links.py`

既存作業: 同種の既存Issue/PRを着手時に検索。

依存: OC-EVOL-004

## 受入条件

- [ ] 等価と緩和を区別
- [ ] 保証の方向と前提が必須
- [ ] 学習順と数理的包含を混ぜない
- [ ] 新namespaceを設計レビュー

## 検証と権限

既存AGENTS/validation registryへ従い、変更面に合うテストを実行する。台帳/数値の検査と、人の学習評価を別にする。新schema、外部送信、課金、実実験、公開、mergeは別承認。未実行の試験を成功と記載しない。

## 非目標

- 本票だけでmainへ無断mergeしない
- 企画IDをそのままcanonical IDへ挿入しない
- 新しい独立した推薦/品質正本を作らない

## 出典

E01, E07, R09。URL・確認日・限界は `../SOURCES.md`。
