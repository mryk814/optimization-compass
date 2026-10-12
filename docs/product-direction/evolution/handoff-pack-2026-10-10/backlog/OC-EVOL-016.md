# OC-EVOL-016: 分解と列・制約生成の辞書スライス

状態: 未投稿のIssue下書き / M1 / P1 / 相対規模: medium

## 目的

Benders、列生成、Dantzig–Wolfe等の関係を一つの小例で示す。

## 成果物

主問題/部分問題/追加情報の図と検算。

## 接続先

- `content/methods/`
- `data/seeds/site_gallery.json`

既存作業: 同種の既存Issue/PRを着手時に検索。

依存: OC-EVOL-004

## 受入条件

- [ ] 最小化/最大化の向きを明記
- [ ] cutとcolumnを区別
- [ ] 整数/凸recourse条件を説明
- [ ] 分解が常に速いとしない

## 検証と権限

既存AGENTS/validation registryへ従い、変更面に合うテストを実行する。台帳/数値の検査と、人の学習評価を別にする。新schema、外部送信、課金、実実験、公開、mergeは別承認。未実行の試験を成功と記載しない。

## 非目標

- 本票だけでmainへ無断mergeしない
- 企画IDをそのままcanonical IDへ挿入しない
- 新しい独立した推薦/品質正本を作らない

## 出典

E07, E08。URL・確認日・限界は `../SOURCES.md`。
