# Japanese UI Copy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace internal answer codes and opaque result labels in the browser UI with Japanese labels that retain the English concept name in parentheses.

**Architecture:** Keep canonical answer IDs in form values and API payloads. Add a single explicit Japanese presentation map inside the existing browser UI template, use `beginner_wording` for question text when available, and adjust only visible helper/result labels in `web.py`.

**Tech Stack:** Python 3.12, FastAPI, embedded HTML/JavaScript, pytest, uv.

## Global Constraints

- API の回答値、SQLite の canonical ID、推薦エンジンの判定ロジックは変更しない。
- CLI の JSON 出力やデータセットのスキーマ変更は今回の対象外。
- 選択肢の `value` には既存の canonical ID をそのまま使う。
- 全選択肢を明示的な表示名マップで管理し、snake_case の機械的変換には依存しない。
- 表示名が未登録の場合は canonical ID をそのまま表示し、回答送信は継続できる。
- 旧 UI と新 UI を並存させる分岐や、別バージョンの API は作らない。

---

### Task 1: Add regression coverage for the browser copy contract

**Files:**
- Modify: `tests/test_api.py`
- Read: `src/optimization_compass/web.py`

**Interfaces:**
- Consumes: `optimization_compass.web.HTML`, the existing static browser template.
- Produces: tests that fail until the Japanese display map and visible copy are present without changing the canonical form value expression.

- [ ] **Step 1: Add the failing test**

Append these assertions to `tests/test_api.py`:

```python
def test_browser_copy_preserves_canonical_values() -> None:
    from optimization_compass.web import HTML

    assert "連続値（continuous）" in HTML
    assert "0/1の二値（binary）" in HTML
    assert "この質問で確認すること：" in HTML
    assert "一致した判断ルール" in HTML
    assert "主な実装例" in HTML
    assert "適用された判断ルール" in HTML
    assert 'value="${esc(a)}"' in HTML
```

- [ ] **Step 2: Run the focused test and confirm it fails**

Run:

```powershell
uv run pytest tests/test_api.py::test_browser_copy_preserves_canonical_values -q
```

Expected: FAIL because the current template displays raw answer IDs and still contains the old result labels.

---

### Task 2: Implement Japanese display labels without changing API values

**Files:**
- Modify: `src/optimization_compass/web.py`
- Test: `tests/test_api.py::test_browser_copy_preserves_canonical_values`

**Interfaces:**
- Consumes: each question's `allowed_answers`, `beginner_wording`, `question`, and `why_asked` fields.
- Produces: the same form submission payload as before, with Japanese-only presentation changes.

- [ ] **Step 1: Add the explicit display map**

Add this JavaScript constant before `load()` in `src/optimization_compass/web.py`:

```javascript
const ANSWER_LABELS_JA = Object.freeze({
  continuous: '連続値（continuous）', integer: '整数値（integer）',
  binary: '0/1の二値（binary）', categorical: 'カテゴリ値（categorical）',
  mixed: '混合型（mixed）', structured_or_unknown: '構造化・複雑な型（structured or unknown）',
  explicit_algebraic: '数式で表せる（explicit algebraic）',
  residual_vector: '残差ベクトルで表せる（residual vector）',
  automatic_differentiation_graph: '自動微分グラフで表せる（automatic differentiation graph）',
  simulation_only: 'シミュレーションのみ（simulation only）',
  experiment_only: '実験で評価する（experiment only）', unknown: 'わからない（unknown）',
  linear: '線形（linear）', quadratic: '二次（quadratic）',
  sum_of_squares: '二乗和（sum of squares）', general_nonlinear: '一般の非線形（general nonlinear）',
  multiobjective: '多目的（multiobjective）',
  equation_or_feasibility: '方程式・実行可能性問題（equation or feasibility）',
  none: '制約なし（none）', bounds: '上下限制約（bounds）', nonlinear: '非線形制約（nonlinear）',
  logical_or_combinatorial: '論理・組合せ制約（logical or combinatorial）',
  conic_or_psd: '錐・半正定値制約（conic or PSD）',
  dynamics_or_manifold: '力学系・多様体制約（dynamics or manifold）',
  implicit_or_failure: '暗黙的・失敗する可能性あり（implicit or failure）',
  analytic_gradient: '解析的な勾配（analytic gradient）', autodiff: '自動微分（autodiff）',
  jacobian_or_hvp: 'Jacobian・HVP（Jacobian or HVP）',
  numerical_difference_only: '数値差分のみ（numerical difference only）',
  stochastic_gradient: '確率的勾配（stochastic gradient）',
  unreliable_or_none: '信頼できない・利用不可（unreliable or none）',
  not_differentiable: '微分できない（not differentiable）',
  milliseconds_or_less: 'ミリ秒以下（milliseconds or less）', seconds: '秒（seconds）',
  minutes: '分（minutes）', hours_or_more: '時間以上（hours or more）',
  deterministic_reliable: '決定的で信頼できる（deterministic reliable）',
  small_noise: '小さなノイズ（small noise）', large_noise: '大きなノイズ（large noise）',
  random_seeded: '乱数によるがseed固定可能（random seeded）',
  occasional_failure: 'ときどき失敗する（occasional failure）',
  frequent_failure: '頻繁に失敗する（frequent failure）',
  timeout_possible: 'タイムアウトの可能性あり（timeout possible）',
  under_10: '10未満（under 10）', 10_to_100: '10〜100', 100_to_10000: '100〜10,000',
  over_10000: '10,000超（over 10,000）',
  huge_sparse_or_distributed: '巨大・疎・分散型（huge sparse or distributed）',
  local_is_fine: '局所解で十分（local is fine）',
  global_candidate_desired: '大域解の候補がほしい（global candidate desired）',
  multiple_distinct_solutions: '異なる解を複数探したい（multiple distinct solutions）',
  no_certificate_needed: '証明は不要（no certificate needed）',
  gap_desired: '最適性gapがほしい（gap desired）',
  global_proof_required: '大域最適性の証明が必要（global proof required）',
  feasible_solution_first: 'まず実行可能解がほしい（feasible solution first）',
  approximation_guarantee: '近似保証がほしい（approximation guarantee）',
  none_known: '特になし（none known）', least_squares: '最小二乗（least squares）',
  lp_qp_conic: 'LP・QP・錐最適化（LP/QP/conic）',
  graph_flow_path_matching: 'グラフ・フロー・経路・マッチング（graph/flow/path/matching）',
  scheduling_routing: 'スケジューリング・経路計画（scheduling/routing）',
  prox_separable: '近接可能・分離可能（prox/separable）',
  optimal_control: '最適制御（optimal control）', manifold: '多様体（manifold）',
  stochastic_or_robust: '確率的・ロバスト（stochastic or robust）', other: 'その他（other）',
  one_off: '一度だけ（one-off）', repeated_similar: '似た問題を繰り返す（repeated similar）',
  online_or_realtime: 'オンライン・リアルタイム（online or realtime）',
  parallel_evaluations: '評価を並列化できる（parallel evaluations）',
  distributed: '分散実行できる（distributed）', gpu_available: 'GPUを使える（GPU available）',
  warm_start_available: 'warm startを使える（warm start available）'
});
```

- [ ] **Step 2: Render display labels while preserving canonical IDs**

Replace the current question rendering with this helper and call:

```javascript
function renderQuestion(q) {
  const questionText = q.beginner_wording || q.question;
  return `<fieldset class="question"><h3>${q.sequence}. ${esc(questionText)}</h3><p><b>この質問で確認すること：</b> ${esc(q.why_asked)}</p>${q.allowed_answers.map(a => `<label><input type="${q.answer_type==='multi_choice'?'checkbox':'radio'}" name="${esc(q.question_id)}" value="${esc(a)}"> ${esc(ANSWER_LABELS_JA[a] ?? a)}</label>`).join('')}</fieldset>`;
}

qEl.innerHTML = questions.map(renderQuestion).join('');
```

The `value="${esc(a)}"` expression must remain unchanged so the API continues to receive canonical IDs.

- [ ] **Step 3: Replace visible result labels**

Apply these exact replacements in the result template:

```text
支持規則       -> 一致した判断ルール
代表実装       -> 主な実装例
docs           -> 公式docs
追加確認       -> 追加で確認したいこと
発火した規則   -> 適用された判断ルール
```

Do not change result JSON fields, recommendation section meanings, or canonical IDs.

- [ ] **Step 4: Run the focused regression test**

Run:

```powershell
uv run pytest tests/test_api.py::test_browser_copy_preserves_canonical_values -q
```

Expected: PASS.

---

### Task 3: Run the full verification and inspect the live UI

**Files:**
- Read: `docs/superpowers/specs/2026-07-13-japanese-ui-copy-design.md`
- Verify: `src/optimization_compass/web.py`, `tests/test_api.py`, `tests/test_engine.py`

**Interfaces:**
- Consumes: the completed Japanese display map and unchanged recommendation API.
- Produces: test evidence that the UI copy changed without changing recommendation behavior or dataset integrity.

- [ ] **Step 1: Run the complete Python test suite**

Run:

```powershell
uv run pytest
```

Expected: exit code 0 and zero failures.

- [ ] **Step 2: Run static checks**

Run:

```powershell
uv run ruff check .
uv run ruff format --check .
uv run mypy src
```

Expected: each command exits 0.

- [ ] **Step 3: Verify the dataset**

Run:

```powershell
uv run optimization-compass verify-data
```

Expected: `ok: true`, `foreign_key_violations: 0`, and `failed_release_checks: 0`.

- [ ] **Step 4: Inspect the live browser UI**

With the existing server at `http://127.0.0.1:8001/`, confirm:

1. Question options show Japanese labels with English concepts in parentheses.
2. The form still submits and returns a recommendation.
3. Result headings use the new Japanese labels.
4. No raw answer code is shown as the only visible label for the mapped options.

- [ ] **Step 5: Confirm repository state**

Run:

```powershell
git -c safe.directory=C:/Users/ootan/projects/optimization-compass diff --check
git -c safe.directory=C:/Users/ootan/projects/optimization-compass status --short
```

Expected: no whitespace errors; only the intended UI/test files are modified before the implementation commit.

