# OC-EVOL-020: 判断規則候補のレビューと回帰例

状態: 未投稿のIssue下書き / M1 / P1 / 相対規模: large

## 目的

24候補を既存規則に照合し、必要な差分のみ追加する。

## 成果物

規則差分、unknown/矛盾/除外テスト。

## 接続先

- `src/optimization_compass/engine.py`
- `src/optimization_compass/predicates.py`
- `tests/fixtures/recommendation_cases.json`

既存作業: 同種の既存Issue/PRを着手時に検索。

依存: OC-EVOL-004

## 受入条件

- [ ] exclusion winsを維持
- [ ] Python/TS parityを検証
- [ ] source IDsを保持
- [ ] 見た目だけの強い推奨をしない

## 検証と権限

既存AGENTS/validation registryへ従い、変更面に合うテストを実行する。台帳/数値の検査と、人の学習評価を別にする。新schema、外部送信、課金、実実験、公開、mergeは別承認。未実行の試験を成功と記載しない。

## 非目標

- 本票だけでmainへ無断mergeしない
- 企画IDをそのままcanonical IDへ挿入しない
- 新しい独立した推薦/品質正本を作らない

## 出典

R09, E01, E03, E38。URL・確認日・限界は `../SOURCES.md`。
