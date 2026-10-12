# OC-EVOL-022: persona意図別の入口と戻り道

状態: 未投稿のIssue下書き / M1 / P1 / 相対規模: medium

## 目的

10仮説の入口/詰まり/出口を少数の利用目的導線へまとめる。

## 成果物

intent切替・直接検索・戻る・出口のUX。

## 接続先

- `site/src/App.tsx`
- `data/seeds/learning_paths.json`

既存作業: 同種の既存Issue/PRを着手時に検索。

依存: OC-EVOL-007, OC-EVOL-008, OC-EVOL-009

## 受入条件

- [ ] persona固定選択を強制しない
- [ ] 専門家の短い経路を残す
- [ ] モバイルでも目的が読める
- [ ] ユーザー研究未検証と明示

## 検証と権限

既存AGENTS/validation registryへ従い、変更面に合うテストを実行する。台帳/数値の検査と、人の学習評価を別にする。新schema、外部送信、課金、実実験、公開、mergeは別承認。未実行の試験を成功と記載しない。

## 非目標

- 本票だけでmainへ無断mergeしない
- 企画IDをそのままcanonical IDへ挿入しない
- 新しい独立した推薦/品質正本を作らない

## 出典

R02, R04。URL・確認日・限界は `../SOURCES.md`。
