# OC-EVOL-004: 同一性と粒度の対応ルール

状態: 未投稿のIssue下書き / M1 / P1 / 相対規模: medium

## 目的

family・method・variant・primitive・implementationの境界を既存語彙へ写す。

## 成果物

対応表と既存複合項目の分割/alias方針。

## 接続先

- `data/seeds/`
- `src/optimization_compass/entity_links.py`

既存作業: 同種の既存Issue/PRを着手時に検索。

依存: OC-EVOL-002

## 受入条件

- [ ] 旧IDを別概念へ転用しない
- [ ] 既存URLを維持
- [ ] 曖昧な多対多対応を明示
- [ ] 全変更に移行例を付す

## 検証と権限

既存AGENTS/validation registryへ従い、変更面に合うテストを実行する。台帳/数値の検査と、人の学習評価を別にする。新schema、外部送信、課金、実実験、公開、mergeは別承認。未実行の試験を成功と記載しない。

## 非目標

- 本票だけでmainへ無断mergeしない
- 企画IDをそのままcanonical IDへ挿入しない
- 新しい独立した推薦/品質正本を作らない

## 出典

R09, R12。URL・確認日・限界は `../SOURCES.md`。
