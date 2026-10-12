# OC-EVOL-028: ローカルcompanionの境界実験

状態: 未投稿のIssue下書き / M3 / P3 / 相対規模: large

## 目的

私有データ/native solver需要を検証し、allowlist runnerを設計する。

## 成果物

評価契約、権限、result manifest、timeout、失敗型。

## 接続先

- `独立companion設計（未実装）`

既存作業: 同種の既存Issue/PRを着手時に検索。

依存: OC-EVOL-021

## 受入条件

- [ ] 任意shellを公開しない
- [ ] 知識DBと利用者データを分離
- [ ] 外部評価は承認が必要
- [ ] 安全性/最適性/モデル妥当性を区別

## 検証と権限

既存AGENTS/validation registryへ従い、変更面に合うテストを実行する。台帳/数値の検査と、人の学習評価を別にする。新schema、外部送信、課金、実実験、公開、mergeは別承認。未実行の試験を成功と記載しない。

## 非目標

- 本票だけでmainへ無断mergeしない
- 企画IDをそのままcanonical IDへ挿入しない
- 新しい独立した推薦/品質正本を作らない

## 出典

R11, E03。URL・確認日・限界は `../SOURCES.md`。
