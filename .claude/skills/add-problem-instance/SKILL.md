---
name: add-problem-instance
description: Add an executable problem definition/instance (問題インスタンス・ベンチマーク問題の追加) as a coordinated pair — problem-suite.json metadata plus problem_registry.py evaluator — then validate with tier B.
---

# 実行可能なproblem instanceを追加する

problem instanceは**2つの authority のペア作業**です。片方だけの変更は不完全です。

1. metadata: `src/optimization_compass/resources/problem-suite.json`
2. 実行可能な評価器: `src/optimization_compass/problem_registry.py`

instanceの `registry_key` とPython registryのキー集合は**完全一致**が要求されます。

## Step 1 — 既存定義を確認する

- 追加したい問題が既存definitionのinstance追加で済むか、新definitionが要るか。
- 最も近い既存instance（同じmathematical family・domain）をJSONとPython両方で読む。

## Step 2 — metadataを書く（problem-suite.json）

definition/instanceが持つもの: ID、mathematical family、変数domain、目的の方向、
利用可能なoracle（objective / gradient / …）、制約class、次元とパラメータ、
初期化候補とseed方針、known-reference状態、表示range・数式・単位・limitations、
source IDと `last_reviewed`。

### 規律

- 表示用の数式expressionは説明的な文字列。**コードとして評価させない**。
- referenceは exact / best-known / approximate / unknown / not meaningful を明示する。
- 教材用の隠しreference情報と、optimizerに見える情報を分離する。

## Step 3 — 評価器を書く（problem_registry.py）

- instanceの `registry_key` に対応するregistry entryを**ちょうど1つ**追加する。
- 評価前に次元・パラメータ型をvalidateする。
- 制約と infeasible時の結果ポリシーを明示する。
- 多目的と明示されたdefinition以外で目的ベクトルを返さない。
- 近い既存evaluatorのコードスタイル（vectorization、型注釈）に合わせる。

## Step 4 — テストを書く

`tests/test_problem_instances.py` 等の既存パターンに合わせ、
評価値・gradient・次元validation・infeasible挙動のfocusedテストを追加します。
生の件数assertは、それ自体がrelease契約でない限り書きません。

## Step 5 — 検証する

```bash
make tier-b
```

反復中の先行チェック:

```bash
uv run ruff check . && uv run mypy src
uv run pytest tests/test_problem_instances.py tests/test_engine.py
```

新しいvisualization scenarioまで作る場合はtier C（`make tier-c`）。

## Stop条件

- 新しいmathematical familyやoracle種別など、既存contractに無い概念が必要。
- 連続/離散のfeasibility意味論が曖昧なまま埋められない。
- referenceの根拠となる一次sourceが無い。

## PRに書くこと

definition/instance ID、`registry_key`、oracle・制約・referenceの宣言内容、
根拠source、テスト内容、検証コマンドと結果。DCO sign-off必須。
