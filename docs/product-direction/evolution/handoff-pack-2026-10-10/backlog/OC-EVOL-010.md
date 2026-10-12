# OC-EVOL-010: 共有scene・observable・媒体契約の差分

状態: 未投稿のIssue下書き / M1 / P1 / 相対規模: medium

## 目的

既存ADR/実装から不足するseek・共有状態・freshnessのみ追加する。

## 成果物

model/view/beats/observableの差分契約と代表fixture。

## 接続先

- `src/optimization_compass/resources/explorables.json`
- `site/src/features/explorable/math/`
- `site/src/features/explorable/`
- `site/scripts/record-scene.mjs`

既存作業: 同種の既存Issue/PRを着手時に検索。

依存: OC-EVOL-001

## 受入条件

- [ ] 第二の数値モデルを作らない
- [ ] 提案と実装済みを分ける
- [ ] 動画の値は同じobservableを使用
- [ ] 旧sceneを壊さない

## 検証と権限

既存AGENTS/validation registryへ従い、変更面に合うテストを実行する。台帳/数値の検査と、人の学習評価を別にする。新schema、外部送信、課金、実実験、公開、mergeは別承認。未実行の試験を成功と記載しない。

## 非目標

- 本票だけでmainへ無断mergeしない
- 企画IDをそのままcanonical IDへ挿入しない
- 新しい独立した推薦/品質正本を作らない

## 出典

R05。URL・確認日・限界は `../SOURCES.md`。
