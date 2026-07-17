---
name: add-problem-instance
description: Add an executable problem definition/instance (問題インスタンス・ベンチマーク問題の追加) as a coordinated problem-suite.json + problem_registry.py pair, validated via optimization-compass validate problem / tier-c.
---

# 実行可能なproblem instanceを追加する（薄いwrapper）

規則の正はこのスキルではなく次の2つです。編集前に必ず読むこと:

1. `.agents/skills/optimization-compass-maintenance/SKILL.md` — Recipe E
2. `docs/adding-knowledge.md` §10

problem instanceは2つのauthorityのペア作業です。片方だけの変更は不完全です:

- metadata: `src/optimization_compass/resources/problem-suite.json`
- 評価器: `src/optimization_compass/problem_registry.py`
  （instanceの `registry_key` とregistryのキー集合は完全一致が要求される）

## 手順

1. 既存definitionのinstance追加で済むか、新definitionが要るかを既存定義をReadして判断する。
2. mathematical familyが最も近い既存instanceをJSONとPythonの両方でReadし、
   その形に合わせて書く。referenceの根拠sourceが無ければ**stop**。
3. `tests/test_problem_instances.py` の既存パターンに合わせてfocusedテストを追加する。
4. 検証する:

   ```
   uv run optimization-compass validate problem
   ```

   **PRゲートは `uv run optimization-compass validate tier-c`**
   （AGENTS.mdのTier C: executable problemはTier C。E2Eはscenario/journeyへ影響が
   ない場合は適用外なので、その場合は `validate tier-b` を実行し、適用外の理由をPRに明記する）。

## Stop条件・PR記載事項

maintenance skillの「Stop conditions」と `docs/knowledge-change-checklist.md` の
「Problem, scenario, and visualization」節に従う。DCO sign-off必須。
