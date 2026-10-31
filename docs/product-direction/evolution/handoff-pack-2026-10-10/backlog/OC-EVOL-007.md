# OC-EVOL-007: 初学者の辞書→一手→次の問い

状態: 未投稿のIssue下書き / M1 / P1 / 相対規模: medium

## 目的

用語を知らない読者が目的・変数・制約を区別して進める入口を作る。

## 成果物

PERSONA_01/02の動線と転移課題。

## 接続先

- `data/seeds/learning_paths.json`
- `site/src/features/content/`
- `site/src/App.tsx`

既存作業: PR297, PR298

依存: OC-EVOL-004

## 受入条件

- [ ] 診断を強制しない
- [ ] 式へ直行する導線も残す
- [ ] つまずきごとに戻れる
- [ ] 次の問いが明示される

## 検証と権限

既存AGENTS/validation registryへ従い、変更面に合うテストを実行する。台帳/数値の検査と、人の学習評価を別にする。新schema、外部送信、課金、実実験、公開、mergeは別承認。未実行の試験を成功と記載しない。

## 非目標

- 本票だけでmainへ無断mergeしない
- 企画IDをそのままcanonical IDへ挿入しない
- 新しい独立した推薦/品質正本を作らない

## 出典

R02, R04, R07。URL・確認日・限界は `../SOURCES.md`。
