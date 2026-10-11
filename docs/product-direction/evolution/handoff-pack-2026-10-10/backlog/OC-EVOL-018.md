# OC-EVOL-018: BOの安全・失敗・多忠実度拡充

状態: 未投稿のIssue下書き / M1 / P1 / 相対規模: medium

## 目的

通常制約BO、SafeOpt、失敗観測、fidelityの違いを整理する。

## 成果物

個別条件/除外、失敗taxonomy、判断例。

## 接続先

- `content/methods/`
- `src/optimization_compass/failure_modes.py`

既存作業: 同種の既存Issue/PRを着手時に検索。

依存: OC-EVOL-008

## 受入条件

- [ ] 安全初期集合を確認
- [ ] 失敗を大罰点へ自動代入しない
- [ ] 高忠実度の順位を仮定しない
- [ ] 原典の仮定と保証範囲を記載

## 検証と権限

既存AGENTS/validation registryへ従い、変更面に合うテストを実行する。台帳/数値の検査と、人の学習評価を別にする。新schema、外部送信、課金、実実験、公開、mergeは別承認。未実行の試験を成功と記載しない。

## 非目標

- 本票だけでmainへ無断mergeしない
- 企画IDをそのままcanonical IDへ挿入しない
- 新しい独立した推薦/品質正本を作らない

## 出典

E12, E38。URL・確認日・限界は `../SOURCES.md`。
