# OC-EVOL-008: 高価な評価の利用者journey

状態: 未投稿のIssue下書き / M1 / P1 / 相対規模: medium

## 目的

評価費、失敗型、ノイズ、安全初期集合のunknownを整理する。

## 成果物

研究者向けの評価契約とbrief出口。

## 接続先

- `data/seeds/site_gallery.json`
- `data/seeds/learning_paths.json`
- `src/optimization_compass/failure_modes.py`

既存作業: 同種の既存Issue/PRを着手時に検索。

依存: OC-EVOL-004

## 受入条件

- [ ] timeoutと違反を分ける
- [ ] 安全条件を補完しない
- [ ] 予算の単位を明示
- [ ] 外部実験を実行しない

## 検証と権限

既存AGENTS/validation registryへ従い、変更面に合うテストを実行する。台帳/数値の検査と、人の学習評価を別にする。新schema、外部送信、課金、実実験、公開、mergeは別承認。未実行の試験を成功と記載しない。

## 非目標

- 本票だけでmainへ無断mergeしない
- 企画IDをそのままcanonical IDへ挿入しない
- 新しい独立した推薦/品質正本を作らない

## 出典

E12, E38, R11。URL・確認日・限界は `../SOURCES.md`。
