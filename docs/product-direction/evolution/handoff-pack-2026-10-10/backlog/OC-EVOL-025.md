# OC-EVOL-025: 動画制作3方式の比較PoC

状態: 未投稿のIssue下書き / M2 / P1 / 相対規模: medium

## 目的

既存recorder、Remotion、HyperFramesを同じsceneで比較する。

## 成果物

数値一致・字幕・修正工数・render/サイズ・license記録。

## 接続先

- `site/scripts/record-scene.mjs`
- `隔離したPoCディレクトリ（新設は承認後）`

既存作業: 同種の既存Issue/PRを着手時に検索。

依存: OC-EVOL-011

## 受入条件

- [ ] 計算正本は一つ
- [ ] 採用版LICENSE/発効条件を確認
- [ ] 有料サービスを無断接続しない
- [ ] 改善が小さければ現行方式を採る

## 検証と権限

既存AGENTS/validation registryへ従い、変更面に合うテストを実行する。台帳/数値の検査と、人の学習評価を別にする。新schema、外部送信、課金、実実験、公開、mergeは別承認。未実行の試験を成功と記載しない。

## 非目標

- 本票だけでmainへ無断mergeしない
- 企画IDをそのままcanonical IDへ挿入しない
- 新しい独立した推薦/品質正本を作らない

## 出典

E23, E24, E25, E26, E27。URL・確認日・限界は `../SOURCES.md`。
