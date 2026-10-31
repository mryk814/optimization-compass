# OC-EVOL-021: 実装への橋とbrief出口

状態: 未投稿のIssue下書き / M1 / P1 / 相対規模: medium

## 目的

代表実装と入出力・status・版・未確定を持ち帰れるようにする。

## 成果物

modeling/solver/evaluator/orchestrationの対応とJSON brief。

## 接続先

- `src/optimization_compass/agent_service.py`
- `site/src/features/diagnose/`

既存作業: 同種の既存Issue/PRを着手時に検索。

依存: OC-EVOL-004, OC-EVOL-008

## 受入条件

- [ ] AI内蔵を必須にしない
- [ ] unknownを保存
- [ ] ライセンス/保守は確認日を残す
- [ ] 実行は別許可

## 検証と権限

既存AGENTS/validation registryへ従い、変更面に合うテストを実行する。台帳/数値の検査と、人の学習評価を別にする。新schema、外部送信、課金、実実験、公開、mergeは別承認。未実行の試験を成功と記載しない。

## 非目標

- 本票だけでmainへ無断mergeしない
- 企画IDをそのままcanonical IDへ挿入しない
- 新しい独立した推薦/品質正本を作らない

## 出典

E03, E10, E13, R11。URL・確認日・限界は `../SOURCES.md`。
