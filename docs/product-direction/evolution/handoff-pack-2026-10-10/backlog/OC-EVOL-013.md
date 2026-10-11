# OC-EVOL-013: 輸送の対応と正則化を体験

状態: 未投稿のIssue下書き / M2 / P1 / 相対規模: medium

## 目的

2x2輸送から、質量保存・正則化・別分野の対応を説明する。

## 成果物

TRANSPORT_MORPH台本、最小fixture、対応表。

## 接続先

- `site/src/features/explorable/math/（新図候補）`
- `content/concepts/（既存との照合後）`

既存作業: 同種の既存Issue/PRを着手時に検索。

依存: OC-EVOL-009, OC-EVOL-010

## 受入条件

- [ ] 行/列質量0.5を保存
- [ ] 正則化解と元の最適輸送を区別
- [ ] ラベル変換で数学を変えない
- [ ] 非均衡へ拡張する場合は別契約

## 検証と権限

既存AGENTS/validation registryへ従い、変更面に合うテストを実行する。台帳/数値の検査と、人の学習評価を別にする。新schema、外部送信、課金、実実験、公開、mergeは別承認。未実行の試験を成功と記載しない。

## 非目標

- 本票だけでmainへ無断mergeしない
- 企画IDをそのままcanonical IDへ挿入しない
- 新しい独立した推薦/品質正本を作らない

## 出典

E11。URL・確認日・限界は `../SOURCES.md`。
