# OC-EVOL-006: 俯瞰図と条件レンズ

状態: 未投稿のIssue下書き / M1 / P1 / 相対規模: medium

## 目的

全体棚、近傍、条件レンズ、未収録を使い分ける。

## 成果物

小図/一覧を持つ関係UI。

## 接続先

- `site/src/visual-system/`
- `site/src/features/map/`
- `site/src/contracts/`

既存作業: 同種の既存Issue/PRを着手時に検索。

依存: OC-EVOL-005

## 受入条件

- [ ] 辺の意味が読める
- [ ] 位置を意味的距離と誤解させない
- [ ] キーボードで同じ情報へ到達
- [ ] 既存canonical routeと戻るを維持

## 検証と権限

既存AGENTS/validation registryへ従い、変更面に合うテストを実行する。台帳/数値の検査と、人の学習評価を別にする。新schema、外部送信、課金、実実験、公開、mergeは別承認。未実行の試験を成功と記載しない。

## 非目標

- 本票だけでmainへ無断mergeしない
- 企画IDをそのままcanonical IDへ挿入しない
- 新しい独立した推薦/品質正本を作らない

## 出典

R02, E32。URL・確認日・限界は `../SOURCES.md`。
