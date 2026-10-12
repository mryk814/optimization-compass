# OC-EVOL-014: 射影と線形oracleの辞書スライス

状態: 未投稿のIssue下書き / M1 / P1 / 相対規模: medium

## 目的

Frank–Wolfeと射影・近接の区別を既存収録へ追加/拡充する。

## 成果物

個別記事、条件付き関係、簡単な単体上の例。

## 接続先

- `content/methods/`
- `data/seeds/formulation_atlas.json`

既存作業: 同種の既存Issue/PRを着手時に検索。

依存: OC-EVOL-004

## 受入条件

- [ ] 既存項目と照合
- [ ] 凸性とoracle条件を記載
- [ ] 一手と失敗条件を検算
- [ ] 性能の普遍順位を作らない

## 検証と権限

既存AGENTS/validation registryへ従い、変更面に合うテストを実行する。台帳/数値の検査と、人の学習評価を別にする。新schema、外部送信、課金、実実験、公開、mergeは別承認。未実行の試験を成功と記載しない。

## 非目標

- 本票だけでmainへ無断mergeしない
- 企画IDをそのままcanonical IDへ挿入しない
- 新しい独立した推薦/品質正本を作らない

## 出典

E05, E04。URL・確認日・限界は `../SOURCES.md`。
