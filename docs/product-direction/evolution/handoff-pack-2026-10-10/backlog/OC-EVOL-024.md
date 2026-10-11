# OC-EVOL-024: アクセシビリティと軽量な代替

状態: 未投稿のIssue下書き / M2 / P1 / 相対規模: medium

## 目的

操作図・3D・動画を利用できない場合も同じ知識へ到達可能にする。

## 成果物

keyboard・focus・reduced-motion・字幕・文章/表の検証。

## 接続先

- `site/src/features/explorable/`
- `site/e2e/`

既存作業: 同種の既存Issue/PRを着手時に検索。

依存: OC-EVOL-010

## 受入条件

- [ ] 色のみで意味を伝えない
- [ ] 動画視聴を進行条件にしない
- [ ] 320/375pxと拡大で操作を確認
- [ ] AAA項目をAA義務と誤記しない

## 検証と権限

既存AGENTS/validation registryへ従い、変更面に合うテストを実行する。台帳/数値の検査と、人の学習評価を別にする。新schema、外部送信、課金、実実験、公開、mergeは別承認。未実行の試験を成功と記載しない。

## 非目標

- 本票だけでmainへ無断mergeしない
- 企画IDをそのままcanonical IDへ挿入しない
- 新しい独立した推薦/品質正本を作らない

## 出典

E37, R05。URL・確認日・限界は `../SOURCES.md`。
