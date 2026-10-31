# OC-EVOL-027: 任意の小計算をするブラウザ実験室

状態: 未投稿のIssue下書き / M3 / P3 / 相対規模: large

## 目的

固定toyを越える必要が確認された場合にWorker計算を試す。

## 成果物

小問題・中断・上限・遅延ロードのPoC。

## 接続先

- `site/src/（optional lab、設計後）`

既存作業: 同種の既存Issue/PRを着手時に検索。

依存: OC-EVOL-021, OC-EVOL-024

## 受入条件

- [ ] 通常の本文に必須読込を追加しない
- [ ] 中断とメモリ上限
- [ ] 必要package/WASMを確認
- [ ] SharedArrayBuffer要件を実配信で検証

## 検証と権限

既存AGENTS/validation registryへ従い、変更面に合うテストを実行する。台帳/数値の検査と、人の学習評価を別にする。新schema、外部送信、課金、実実験、公開、mergeは別承認。未実行の試験を成功と記載しない。

## 非目標

- 本票だけでmainへ無断mergeしない
- 企画IDをそのままcanonical IDへ挿入しない
- 新しい独立した推薦/品質正本を作らない

## 出典

E33, E34, E35, E36。URL・確認日・限界は `../SOURCES.md`。
