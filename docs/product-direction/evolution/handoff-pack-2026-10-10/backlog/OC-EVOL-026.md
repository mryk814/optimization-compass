# OC-EVOL-026: 媒体鮮度・出典・再生成

状態: 未投稿のIssue下書き / M2 / P1 / 相対規模: medium

## 目的

モデル・view・台本・音声の入力変更を検出し、派生物の再生成を管理する。

## 成果物

media manifestとstale/再生成/rollback手順。

## 接続先

- `src/optimization_compass/derived_media.py`
- `src/optimization_compass/resources/`
- `site/scripts/record-scene.mjs`

既存作業: 同種の既存Issue/PRを着手時に検索。

依存: OC-EVOL-025

## 受入条件

- [ ] OS/GPU跨ぎのbyte一致を保証しない
- [ ] 入力hashと数値一致を検査
- [ ] 古い音声/字幕を検出
- [ ] 自動公開の変更は別承認

## 検証と権限

既存AGENTS/validation registryへ従い、変更面に合うテストを実行する。台帳/数値の検査と、人の学習評価を別にする。新schema、外部送信、課金、実実験、公開、mergeは別承認。未実行の試験を成功と記載しない。

## 非目標

- 本票だけでmainへ無断mergeしない
- 企画IDをそのままcanonical IDへ挿入しない
- 新しい独立した推薦/品質正本を作らない

## 出典

R05, R10。URL・確認日・限界は `../SOURCES.md`。
