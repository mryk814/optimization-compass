# OC-EVOL-019: 問題構造80候補の正準対応

状態: 未投稿のIssue下書き / M1 / P1 / 相対規模: medium

## 目的

problem/profile/隣接問題を混ぜずにscopeを既存辞書へ写す。

## 成果物

標準形・読み下し・識別cue・近隣の対応。

## 接続先

- `data/seeds/formulation_atlas.json`
- `src/optimization_compass/problem_instances.py`

既存作業: 同種の既存Issue/PRを着手時に検索。

依存: OC-EVOL-004

## 受入条件

- [ ] 全80を新problem行にしない
- [ ] 既存57型の対応を保持
- [ ] profileの独立軸を保持
- [ ] 根拠のない定型文を埋めない

## 検証と権限

既存AGENTS/validation registryへ従い、変更面に合うテストを実行する。台帳/数値の検査と、人の学習評価を別にする。新schema、外部送信、課金、実実験、公開、mergeは別承認。未実行の試験を成功と記載しない。

## 非目標

- 本票だけでmainへ無断mergeしない
- 企画IDをそのままcanonical IDへ挿入しない
- 新しい独立した推薦/品質正本を作らない

## 出典

E01, R02。URL・確認日・限界は `../SOURCES.md`。
