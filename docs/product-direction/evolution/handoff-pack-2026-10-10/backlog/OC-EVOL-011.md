# OC-EVOL-011: 主単体法を証明・感度・動画へ拡張

状態: 未投稿のIssue下書き / M2 / P1 / 相対規模: medium

## 目的

PR298を再利用し、一手→双対証明→感度範囲へつなぐ。

## 成果物

storyboards/LP_PORTRAIT.mdの実装と数値fixture。

## 接続先

- `site/src/features/explorable/`
- `content/methods/primal-simplex.md`

既存作業: PR297, PR298

依存: OC-EVOL-007, OC-EVOL-010

## 受入条件

- [ ] 最適値24、双対5/7と6/7に一致
- [ ] 在庫感度の有効範囲を表示
- [ ] PR297/298を重複実装しない
- [ ] 文章だけでも証明が読める

## 検証と権限

既存AGENTS/validation registryへ従い、変更面に合うテストを実行する。台帳/数値の検査と、人の学習評価を別にする。新schema、外部送信、課金、実実験、公開、mergeは別承認。未実行の試験を成功と記載しない。

## 非目標

- 本票だけでmainへ無断mergeしない
- 企画IDをそのままcanonical IDへ挿入しない
- 新しい独立した推薦/品質正本を作らない

## 出典

R07, R06, R05。URL・確認日・限界は `../SOURCES.md`。
