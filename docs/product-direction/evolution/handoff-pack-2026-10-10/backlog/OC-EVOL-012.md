# OC-EVOL-012: BOの視界制限・予測・評価費

状態: 未投稿のIssue下書き / M2 / P1 / 相対規模: medium

## 目的

真の関数を見る学習者視点と、観測だけを使うoptimizer視点を明示する。

## 成果物

BO_ORACLE台本、観測/情報境界、比較予算。

## 接続先

- `site/src/features/explorable/BayesOptAcquisition.tsx`
- `site/src/features/explorable/math/`

既存作業: 同種の既存Issue/PRを着手時に検索。

依存: OC-EVOL-008, OC-EVOL-010

## 受入条件

- [ ] 未観測truthをoptimizerへ渡さない
- [ ] 同じseed/観測で再現
- [ ] 費用とiterationを区別
- [ ] 安全保証の有無を明示

## 検証と権限

既存AGENTS/validation registryへ従い、変更面に合うテストを実行する。台帳/数値の検査と、人の学習評価を別にする。新schema、外部送信、課金、実実験、公開、mergeは別承認。未実行の試験を成功と記載しない。

## 非目標

- 本票だけでmainへ無断mergeしない
- 企画IDをそのままcanonical IDへ挿入しない
- 新しい独立した推薦/品質正本を作らない

## 出典

E12, E20, E38。URL・確認日・限界は `../SOURCES.md`。
